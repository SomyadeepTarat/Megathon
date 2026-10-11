"""Illustrative paired valuation benchmark, never observed-market evidence."""
from __future__ import annotations

import argparse
import hashlib
import json
import pickle
from functools import lru_cache
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import GroupShuffleSplit
from ml.valuation import pipeline, metrics, conformal_radius

ROOT = Path(__file__).resolve().parents[1]
MODEL = ROOT / 'ml/models/synthetic_impact.joblib'
NUMERIC = ['floor_area', 'bedrooms', 'age', 'energy_intensity']
CATEGORIES = ['region', 'property_type']
FEATURES = NUMERIC + CATEGORIES
ALPHA = .1


def generate(n=1800, seed=254):
    """Same region/type vocabulary as the app; new property IDs, disclosed labels."""
    source = pd.read_csv(ROOT / 'Data/csv/properties.csv')
    regions = sorted(source.region.unique())
    rates = {r: float((g.current_value_estimate_gbp / g.floor_area_m2).median())
             for r, g in source.groupby('region')}
    rng = np.random.default_rng(seed)
    frame = pd.DataFrame({
        'property_id': [f'IMPACT-{i:05}' for i in range(n)],
        'region': rng.choice(regions, n),
        'property_type': rng.choice(['detached', 'semi_detached', 'terraced', 'flat', 'bungalow'], n),
        'floor_area': rng.uniform(40, 350, n), 'bedrooms': rng.integers(0, 11, n),
        'age': rng.uniform(0, 200, n), 'energy_intensity': rng.uniform(0, 600, n)})
    # This coefficient is an invented scenario assumption, not a UK premium.
    coefficient = rng.uniform(100, 140, n)
    after_intensity = frame.energy_intensity.to_numpy() * rng.uniform(0, 1, n)
    type_offset = frame.property_type.map({'detached': 30000, 'semi_detached': 15000,
                                         'terraced': 5000, 'flat': 0, 'bungalow': 10000})
    base = frame.floor_area * frame.region.map(rates) + type_offset + frame.bedrooms * 5000 - frame.age * 100
    noise = rng.normal(0, 15000, n)
    frame['sale_price'] = base + coefficient * (300 - frame.energy_intensity) + noise
    frame['after_energy_intensity'] = after_intensity
    frame['value_change_reference_gbp'] = coefficient * (frame.energy_intensity - after_intensity)
    frame['after_sale_price'] = frame.sale_price + frame.value_change_reference_gbp
    return frame, rates


def fit_model(kind, rows, numeric=NUMERIC):
    model = pipeline(kind, energy=False, numeric=numeric)
    if kind == 'hist_gradient_boosting' and 'energy_intensity' in numeric:
        # Constrain the energy proxy; improving intensity must not reduce value.
        constraints = [-1 if col == 'energy_intensity' else 0 for col in numeric]
        constraints += [0] * sum(rows[col].nunique() for col in CATEGORIES)
        model.steps[-1][1].set_params(monotonic_cst=constraints)
    return model.fit(rows[numeric + CATEGORIES], rows.sale_price)


def train_demo(output=MODEL, reports=ROOT / 'ml/reports/synthetic_impact', seed=254):
    frame, rates = generate(seed=seed)
    indices = np.arange(len(frame))
    splits = {}
    for name, fraction, offset in [('test', .2, 0), ('calibration', .25, 1), ('selection', 1/3, 2)]:
        a, b = next(GroupShuffleSplit(n_splits=1, test_size=fraction, random_state=seed + offset)
                    .split(indices, groups=frame.iloc[indices].property_id))
        splits[name], indices = indices[b], indices[a]
    splits['fit'] = indices
    fit, selection = (frame.iloc[splits[k]] for k in ('fit', 'selection'))
    candidates = {kind: fit_model(kind, fit)
                  for kind in ('ridge', 'hist_gradient_boosting')}
    selection_metrics = {kind: metrics(selection.sale_price, model.predict(selection[FEATURES]))
                         for kind, model in candidates.items()}
    selected = ('hist_gradient_boosting' if selection_metrics['hist_gradient_boosting']['mae_gbp'] <
                .98 * selection_metrics['ridge']['mae_gbp'] else 'ridge')
    dev = frame.iloc[np.concatenate([splits['fit'], splits['selection']])]
    candidates = {kind: fit_model(kind, dev) for kind in candidates}
    model = candidates[selected]
    def contrast(rows, fitted=model):
        after = rows[FEATURES].copy()
        after['energy_intensity'] = rows.after_energy_intensity
        return fitted.predict(after) - fitted.predict(rows[FEATURES])
    cal, test = (frame.iloc[splits[k]] for k in ('calibration', 'test'))
    radius = conformal_radius(np.abs(cal.sale_price - model.predict(cal[FEATURES])), ALPHA)
    pair_radius = conformal_radius(np.abs(cal.value_change_reference_gbp - contrast(cal)), ALPHA)
    delta = contrast(test)
    before = model.predict(test[FEATURES])
    # Ablation on the untouched selection partition, not on calibration/test.
    no_energy = fit_model(selected, fit, NUMERIC[:-1])
    ablation = metrics(selection.sale_price, no_energy.predict(selection[NUMERIC[:-1] + CATEGORIES]))
    pred = test[['property_id', 'sale_price', 'value_change_reference_gbp']].copy()
    pred['prediction_gbp'] = before
    pred['lower_gbp'], pred['upper_gbp'] = np.maximum(0, before-radius), before+radius
    pred['value_change_prediction_gbp'] = delta
    pred['value_change_lower_gbp'], pred['value_change_upper_gbp'] = delta-pair_radius, delta+pair_radius
    report = {
        'scope': 'synthetic paired scenario agreement; not market accuracy or real causal evidence',
        'selected_model': selected, 'seed': seed, 'alpha': ALPHA,
        'selection_metrics': selection_metrics, 'without_energy_selection_metrics': ablation,
        'held_out_metrics': {k: metrics(test.sale_price, m.predict(test[FEATURES])) for k, m in candidates.items()},
        'median_baseline': metrics(test.sale_price, np.full(len(test), dev.sale_price.median())),
        'interval_coverage': float(np.mean(abs(test.sale_price-before) <= radius)),
        'mean_interval_width_gbp': float(np.mean(before+radius-np.maximum(0, before-radius))),
        'paired_uplift_mae_gbp': float(np.mean(abs(test.value_change_reference_gbp-delta))),
        'paired_uplift_interval_coverage': float(np.mean(abs(test.value_change_reference_gbp-delta) <= pair_radius)),
        'paired_uplift_mean_interval_width_gbp': 2 * pair_radius,
        'nonnegative_direction_fraction': float(np.mean(delta >= -1e-8)),
        'counts': {k: len(v) for k, v in splits.items()}, 'group_overlap': False,
        'limitations': ['Prices and paired responses are generated by a disclosed invented equation.',
                       'Coverage only applies to this synthetic scenario distribution under exchangeability.',
                       'Purchased-energy intensity is a screening proxy, affected by occupancy and behaviour.',
                       'No EPC is predicted or changed; no real retrofit premium is established.']}
    manifest = frame[['property_id']].copy()
    for name, rows in splits.items():
        manifest.loc[rows, 'split'] = name
    support = {'floor_area': [40, 350], 'bedrooms': [0, 10], 'age': [0, 200], 'energy_intensity': [0, 600]}
    provenance = {'kind': 'synthetic', 'source': 'ml.synthetic_impact.generate seed 254',
        'license': 'Project-generated synthetic data; no customer records',
        'region_rates_gbp_m2': rates,
        'label_rule': 'area*region_rate + type_offset + bedrooms*5000 - age*100 + coefficient*(300-intensity) + noise; coefficient~Uniform(100,140), noise~Normal(0,15000). Same noise/coefficient in paired scenario; only intensity changes.',
        'after_rule': 'baseline intensity * Uniform(0,1); independent property-group fit/selection/calibration/test; boosting constrained nonincreasing in intensity',
        'source_properties_sha256': hashlib.sha256((ROOT/'Data/csv/properties.csv').read_bytes()).hexdigest()}
    artifact = {'format_version': 'synthetic-impact-v1', 'model': model, 'features': FEATURES,
                'radius': radius, 'pair_radius': pair_radius, 'alpha': ALPHA, 'provenance': provenance,
                'numeric_bounds': support, 'categories': {c: sorted(frame[c].unique()) for c in CATEGORIES},
                'report': report}
    output, reports = Path(output), Path(reports)
    output.parent.mkdir(parents=True, exist_ok=True)
    reports.mkdir(parents=True, exist_ok=True)
    frame.to_csv(reports/'synthetic_sales_pairs.csv', index=False)
    provenance['data_sha256'] = hashlib.sha256((reports/'synthetic_sales_pairs.csv').read_bytes()).hexdigest()
    joblib.dump(artifact, output)
    pred.to_csv(reports/'held_out_predictions.csv', index=False)
    manifest.to_csv(reports/'split_manifest.csv', index=False)
    (reports/'provenance.json').write_text(json.dumps(provenance, indent=2)+'\n')
    (reports/'valuation_metrics.json').write_text(json.dumps(report, indent=2)+'\n')
    return report


@lru_cache(maxsize=4)
def _load(path, mtime):
    artifact = joblib.load(path)
    if artifact.get('format_version') != 'synthetic-impact-v1' or artifact['provenance']['kind'] != 'synthetic':
        raise ValueError('Invalid synthetic impact artifact')
    return artifact


def predict_impact(baseline, scenario, energy, model_path=MODEL):
    from backend.app.services.valuation_inputs import impact_input_reason, normalize_property, missing
    def unavailable(reason):
        return {'status': 'unavailable', 'reason': reason, 'value_before': None, 'value_after': None, 'uplift_range': None}
    baseline, scenario = normalize_property(baseline), normalize_property(scenario)
    reason = impact_input_reason(baseline, scenario)
    if reason:
        return unavailable(reason)
    absent = sorted({key for state in (baseline, scenario) for key in ('age', 'bedrooms') if missing(state.get(key))})
    if absent:
        return unavailable('Insufficient property details provided (missing ' + ', '.join(absent) + '). Value impact cannot be estimated.')
    if baseline.get('provenance', {}).get('record') != 'synthetic':
        return unavailable('Illustrative impact requires an explicitly synthetic property record.')
    for key in ['property_id', 'floor_area', 'bedrooms', 'age', 'region', 'property_type', 'market_index', 'energy_rating', 'baseline_value']:
        if baseline.get(key) != scenario.get(key):
            return unavailable(f'Unrelated characteristic changed: {key}')
    try:
        path = Path(model_path)
        artifact = _load(str(path), path.stat().st_mtime_ns)
        rows = []
        for state, fuel in [(baseline, energy.baseline), (scenario, energy.after)]:
            row = {key: state.get(key) for key in FEATURES if key != 'energy_intensity'}
            row['energy_intensity'] = (fuel.electricity_kwh + fuel.gas_kwh) / float(state['floor_area'])
            for key, (low, high) in artifact['numeric_bounds'].items():
                value = float(row[key])
                if not np.isfinite(value) or not low <= value <= high:
                    raise ValueError(f'Missing or outside synthetic training support: {key}')
                if key == 'bedrooms' and value % 1:
                    raise ValueError('Bedrooms must be integral')
                row[key] = value
            for key, choices in artifact['categories'].items():
                if row[key] not in choices:
                    raise ValueError(f'Outside synthetic training support: {key}')
            rows.append(row)
        predictions = artifact['model'].predict(pd.DataFrame(rows))
        if not np.isfinite(predictions).all() or (predictions <= 0).any():
            raise ValueError('Invalid synthetic model prediction')
        delta = float(predictions[1] - predictions[0])
        before = float(baseline['baseline_value'])
        after = before + delta
        if after <= 0:
            raise ValueError('Anchored scenario value is not positive')
        width = 0 if rows[0] == rows[1] else artifact['pair_radius']
    except (OSError, ValueError, TypeError, KeyError, EOFError, ImportError, AttributeError, pickle.UnpicklingError) as exc:
        return unavailable(str(exc) if isinstance(exc, ValueError) else 'Synthetic impact artifact missing or incompatible; run python -m ml.synthetic_impact.')
    return {'status': 'illustrative', 'baseline_value_gbp': before, 'after_value_gbp': after,
        'value_before': before, 'value_after': after, 'value_change_gbp': delta,
        'uplift_range': [delta-width, delta+width], 'value_change_range_gbp': [delta-width, delta+width],
        'baseline_range_gbp': [before, before], 'after_range_gbp': [max(0, after-width), after+width],
        'confidence_level': 1-artifact['alpha'],
        'method': 'Synthetic regression contrast on simulated purchased-energy intensity, anchored to supplied current value; paired split-conformal calibration.',
        'warnings': (['Unused optional fields are missing: ' + ', '.join(sorted({key for state in (baseline, scenario)
            for key in ('market_index', 'insulation', 'heating_system', 'glazing', 'renewable_contribution', 'smart_controls')
            if missing(state.get(key))}))] if any(missing(state.get(key)) for state in (baseline, scenario)
            for key in ('market_index', 'insulation', 'heating_system', 'glazing', 'renewable_contribution', 'smart_controls')) else []) +
                    ['Synthetic demo estimate from an invented price relationship; not an observed-market valuation or guaranteed premium.',
                     'Current value is supplied as an anchor, not used as a model input; baseline range describes that fixed anchor.',
                     f"Nominal 90% contrast interval; held-out synthetic coverage {artifact['report']['paired_uplift_interval_coverage']:.1%}. Real-world coverage is unknown.",
                     'Recorded EPC, location, area, age, type and market conditions are held fixed.']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, default=MODEL)
    parser.add_argument('--reports', type=Path, default=ROOT/'ml/reports/synthetic_impact')
    args = parser.parse_args()
    print(json.dumps(train_demo(args.output, args.reports), indent=2))
