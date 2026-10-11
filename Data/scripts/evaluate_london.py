"""Development diagnostics and independent conformal calibration, no production model changes.

Default never scores the fresh test partition. --final evaluates it once after
freezing the selection, model and calibration choices; do not tune from that result.
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.model_selection import GroupKFold

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from ml.valuation import CATEGORICAL, NUMERIC, conformal_radius, metrics, pipeline, validate_snapshot
from expand_dataset import ROOT, read_csv, sha, write_json

VERSION = 'kew_london_v3'
FEATURES = NUMERIC[:-1] + CATEGORICAL
TARGET = 'current_value_estimate_gbp'


def grouped_errors(frame, prediction):
    result = {}
    groups = {
        'region': frame.region, 'property_type': frame.property_type,
        'size_band': pd.cut(frame.floor_area, [0, 55, 90, 140, float('inf')], right=False).astype(str),
        'price_band': pd.cut(frame[TARGET], [0, 300000, 500000, 750000, 1000000, float('inf')], right=False).astype(str),
    }
    for name, labels in groups.items():
        result[name] = {str(label): dict(count=int((labels == label).sum()),
                                       **metrics(frame.loc[labels == label, TARGET], prediction[np.asarray(labels == label)]))
                        for label in sorted(set(labels))}
    return result


def coverage(frame, prediction, radius, proportional=False):
    widths = radius * np.maximum(50000, prediction) if proportional else np.full(len(frame), radius)
    covered = np.abs(frame[TARGET].to_numpy() - prediction) <= widths
    return {'nominal_coverage': .9, 'actual_coverage': float(np.mean(covered)),
            'count': len(frame), 'mean_interval_width_gbp': float(np.mean(2 * widths)),
            'by_property_type': {k: {'count': int((frame.property_type == k).sum()),
                                     'coverage': float(np.mean(covered[np.asarray(frame.property_type == k)]))}
                                 for k in sorted(set(frame.property_type))}}


def evaluate(data, final=False):
    if final and (data / 'FINAL_EVALUATION.json').exists():
        raise ValueError('Final evaluation already recorded. Do not repeatedly evaluate/tune on this holdout.')
    props = validate_snapshot(pd.read_csv(data / 'properties.csv'))
    manifest = pd.read_csv(data / 'split_manifest.csv')
    if not manifest.property_id.is_unique or set(props.property_id) != set(manifest.property_id):
        raise ValueError('Split manifest must match every property exactly once')
    df = props.merge(manifest, on=['property_id', 'customer_id'], validate='one_to_one')
    if df.groupby('customer_id').split.nunique().max() != 1:
        raise ValueError('Customer leakage')
    fit = df[df.split == 'fit'].reset_index(drop=True)
    selection = df[df.split == 'selection'].reset_index(drop=True)
    calibration = df[df.split == 'calibration'].reset_index(drop=True)
    candidates, diagnostics = {}, {}
    for kind in ['ridge', 'hist_gradient_boosting']:
        model = pipeline(kind, False, NUMERIC[:-1]).fit(fit[FEATURES], fit[TARGET])
        pred = model.predict(selection[FEATURES])
        diagnostics[kind] = {'metrics': metrics(selection[TARGET], pred),
                             'errors': grouped_errors(selection, pred)}
        candidates[kind] = model
    choice = 'hist_gradient_boosting' if diagnostics['hist_gradient_boosting']['metrics']['mae_gbp'] < .98 * diagnostics['ridge']['metrics']['mae_gbp'] else 'ridge'
    # Learning curves use only grouped fit folds and never consume calibration/test.
    curves = []
    for count in [100, 250, 500, len(fit)]:
        if count > len(fit):
            continue
        subset = fit.iloc[:count]
        folds = []
        for train, validation in GroupKFold(n_splits=5).split(subset, groups=subset.customer_id):
            model = clone(candidates[choice]).fit(subset.iloc[train][FEATURES], subset.iloc[train][TARGET])
            folds.append(metrics(subset.iloc[validation][TARGET], model.predict(subset.iloc[validation][FEATURES]))['mae_gbp'])
        curves.append({'fit_rows': count, 'mean_grouped_cv_mae_gbp': float(np.mean(folds)),
                       'std_fold_mae_gbp': float(np.std(folds)), 'folds': 5})
    development = pd.concat([fit, selection])
    model = clone(candidates[choice]).fit(development[FEATURES], development[TARGET])
    cal_pred = model.predict(calibration[FEATURES])
    residuals = np.abs(calibration[TARGET].to_numpy() - cal_pred)
    absolute_radius = conformal_radius(residuals, .1)
    relative_radius = conformal_radius(residuals / np.maximum(50000, cal_pred), .1)
    report = {'status': 'synthetic evaluation; not market accuracy or causal retrofit evidence',
              'features': FEATURES, 'new_ml_inputs': [], 'selected_model': choice,
              'selection_rule': 'Existing candidates and 2% MAE improvement rule; selection partition only',
              'selection_diagnostics': diagnostics, 'learning_curves_fit_only': curves,
              'calibration': {'count': len(calibration), 'alpha': .1,
                              'absolute_radius_gbp': absolute_radius, 'relative_radius': relative_radius,
                              'interval_policy': 'Predeclared price-proportional scale max(predicted price, GBP 50,000); no test-driven interval selection.'},
              'splits': df.split.value_counts().to_dict(), 'test_status': 'reserved; not evaluated',
              'calibration_assumption': 'Fresh customer groups from the same frozen synthetic generator are exchangeable; coverage is marginal, not guaranteed per type.'}
    # Record unseen categories without inspecting held-out targets/predictions.
    report['selection_unseen_categories'] = {k: sorted(set(selection[k]) - set(fit[k])) for k in CATEGORICAL}
    frozen = {'selected_model': choice, 'features': FEATURES, 'absolute_radius': absolute_radius,
              'relative_radius': relative_radius, 'source_sha256': {'properties.csv': sha(data / 'properties.csv'),
                                                                  'split_manifest.csv': sha(data / 'split_manifest.csv'),
                                                                  'evaluator.py': sha(Path(__file__))}}
    report['frozen_configuration_sha256'] = hashlib.sha256(json.dumps(frozen, sort_keys=True).encode()).hexdigest()
    if final:
        marker = data / 'FINAL_EVALUATION.json'
        if marker.exists():
            raise ValueError('Final evaluation already recorded. Do not repeatedly evaluate/tune on this holdout.')
        test = df[df.split == 'test'].reset_index(drop=True)
        pred = model.predict(test[FEATURES])
        report['test_status'] = 'evaluated once after freezing model and intervals; now exposed, do not tune'
        report['fresh_test'] = {'metrics': metrics(test[TARGET], pred),
                                'relative_intervals': coverage(test, pred, relative_radius, True),
                                'absolute_intervals_comparator': coverage(test, pred, absolute_radius),
                                'errors': grouped_errors(test, pred)}
        write_json(marker, {'configuration': frozen, 'configuration_sha256': report['frozen_configuration_sha256'],
                            'test_status': report['test_status']})
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data', type=Path, default=ROOT / 'generated' / VERSION)
    parser.add_argument('--final', action='store_true')
    args = parser.parse_args()
    report = evaluate(args.data, args.final)
    name = 'final_evaluation.json' if args.final else 'development_diagnostics.json'
    write_json(ROOT / 'reports' / VERSION / name, report)
    print(json.dumps({'selected_model': report['selected_model'], 'test_status': report['test_status'],
                      'report': str(ROOT / 'reports' / VERSION / name)}, indent=2))


if __name__ == '__main__':
    main()
