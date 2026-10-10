"""Initial evaluation of synthetic property snapshots, not observed sales.

Run from the repo root: python -m evaluation.evaluate_initial_dataset
No team-owned datasets or engines are modified.
"""
import argparse
import hashlib
import importlib.util
import json
import sys
from collections import Counter
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import median_absolute_error
from sklearn.model_selection import GroupShuffleSplit
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from ml.valuation import conformal_radius, metrics

ROOT = Path(__file__).resolve().parents[1]
NUMERIC = ["floor_area_m2", "bedrooms", "age"]
CATEGORIES = ["region", "property_type", "energy_rating"]


def build(kind, energy=True):
    categories = CATEGORIES if energy else CATEGORIES[:-1]
    prep = ColumnTransformer([("numeric", StandardScaler(), NUMERIC),
                              ("categories", OneHotEncoder(handle_unknown="ignore", sparse_output=False), categories)])
    model = Ridge(alpha=10) if kind == "ridge" else HistGradientBoostingRegressor(
        max_iter=120, max_leaf_nodes=15, l2_regularization=10, random_state=42, early_stopping=False)
    return make_pipeline(prep, model)


def errors(y, pred):
    result = metrics(y, pred)
    result["median_absolute_error_gbp"] = float(median_absolute_error(y, pred))
    result["mape_percent"] = float(np.mean(abs((np.asarray(y) - pred) / np.asarray(y))) * 100)
    return result


def run(data, output):
    data, output = data.resolve(), output.resolve()
    properties_path, energy_path = data / "csv/properties.csv", data / "csv/energy_usage.csv"
    p = pd.read_csv(properties_path, dtype={"property_id": str, "customer_id": str})
    e = pd.read_csv(energy_path, dtype={"property_id": str})
    output.mkdir(parents=True, exist_ok=True)
    if p.isna().any().any() or e.isna().any().any():
        raise ValueError("Initial complete-dataset evaluation requires nonmissing fields")
    assert p.property_id.is_unique and not e.duplicated(["property_id", "month"]).any()
    assert set(p.property_id) == set(e.property_id)
    assert set(p.data_status) == {"synthetic"} and set(e.reading_status) == {"synthetic"}
    assert (p[NUMERIC + ["current_value_estimate_gbp"]] > 0).all().all()
    assert (e[["electricity_kwh", "gas_kwh"]] >= 0).all().all()
    for _, rows in e.groupby("property_id"):
        assert set(rows.month) == {f"2025-{i:02d}" for i in range(1, 13)}
    # Import P3's pure functions, avoiding its CLI's misplaced CSV paths.
    spec = importlib.util.spec_from_file_location("p3_energy_generator", data / "scripts/generate_energy_usage.py")
    generator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(generator)
    raw = pd.read_csv(properties_path, dtype=str).to_dict("records")
    regenerated = generator.generate(raw)
    generator.validate(raw, regenerated)
    expected = pd.DataFrame(regenerated)
    merged = e.merge(expected, on=["property_id", "month"], suffixes=("", "_regenerated"), validate="one_to_one")
    regeneration_errors = {}
    for fuel in ["electricity_kwh", "gas_kwh"]:
        regeneration_errors[fuel] = float(abs(merged[fuel] - merged[fuel + "_regenerated"].astype(float)).max())
        assert regeneration_errors[fuel] < 1e-8

    sys.path.insert(0, str(ROOT / "backend"))
    from app.db.repository import CsvPropertyRepository
    from app.core.scoring import calculate_score
    from app.core.efficiency import assess
    from app.schemas.models import AssessmentRequest
    repo = CsvPropertyRepository(properties_path, energy_path)
    assessments, rows = [], []
    for record in repo.list_properties():
        request = AssessmentRequest(property=record.property, annual_energy=record.annual_energy, benchmark=record.benchmark)
        assessment = assess(request).model_dump(mode="json")
        assessments.append(assessment)
        score = assessment["score"]
        assert score == calculate_score(request).model_dump(mode="json")
        row = {"property_id": record.property.property_id, "score_status": score["status"],
               "score": score["score"], "classification": score["classification"],
               "missing_fields": ";".join(score["missing_fields"]),
               "annual_electricity_kwh": record.annual_energy.electricity_kwh,
               "annual_gas_kwh": record.annual_energy.gas_kwh,
               "intensity_kwh_m2_year": assessment["intensity_kwh_m2_year"]}
        assert len(score["components"]) == 7 and abs(sum(c["weight"] for c in score["components"]) - 1) < 1e-12
        for c in score["components"]:
            row[c["name"] + "_subscore"] = c["subscore"]
            row[c["name"] + "_contribution"] = c["contribution"]
            if c["subscore"] is not None:
                assert 0 <= c["subscore"] <= 100
        rows.append(row)
    scores = pd.DataFrame(rows)
    scores.to_csv(output / "property_scores.csv", index=False)
    (output / "assessments.json").write_text(json.dumps(assessments, indent=2))

    # Snapshot-target experiment: do not relabel current estimates as sale prices.
    # 40/20/20/20 groups ensures >=19 calibration groups for alpha/2 bands.
    def split(indices, fraction, seed):
        a, b = next(GroupShuffleSplit(n_splits=1, test_size=fraction, random_state=seed).split(indices, groups=p.iloc[indices].customer_id))
        return indices[a], indices[b]
    rest, test_idx = split(np.arange(len(p)), .2, 42)
    rest, cal_idx = split(rest, .25, 43)
    fit_idx, select_idx = split(rest, 1/3, 44)
    splits = dict(fit=fit_idx, selection=select_idx, calibration=cal_idx, test=test_idx)
    group_sets = [set(p.iloc[v].customer_id) for v in splits.values()]
    assert all(not a & b for i, a in enumerate(group_sets) for b in group_sets[i+1:])
    features = NUMERIC + CATEGORIES
    target = "current_value_estimate_gbp"
    models, selection = {}, {}
    for kind in ["ridge", "hist_gradient_boosting"]:
        model = build(kind).fit(p.iloc[fit_idx][features], p.iloc[fit_idx][target])
        models[kind] = model
        selection[kind] = errors(p.iloc[select_idx][target], model.predict(p.iloc[select_idx][features]))
    selected = "hist_gradient_boosting" if selection["hist_gradient_boosting"]["mae_gbp"] < .98 * selection["ridge"]["mae_gbp"] else "ridge"
    no_epc = build(selected, False).fit(p.iloc[fit_idx][features], p.iloc[fit_idx][target])
    no_epc_mae = errors(p.iloc[select_idx][target], no_epc.predict(p.iloc[select_idx][features]))["mae_gbp"]
    development = np.concatenate([fit_idx, select_idx])
    for model in models.values():
        model.fit(p.iloc[development][features], p.iloc[development][target])
    model = models[selected]
    calibration = p.iloc[cal_idx].sample(frac=1, random_state=42).drop_duplicates("customer_id")
    residuals = abs(calibration[target].to_numpy() - model.predict(calibration[features]))
    radius = conformal_radius(residuals, .1)
    test = p.iloc[test_idx]
    pred = model.predict(test[features])
    report = {
        "dataset_kind": "synthetic", "target": target,
        "warning": "Illustrative snapshot regression only; not sale valuation or a causal EPC premium.",
        "selected_model": selected, "selection_metrics": selection,
        "held_out_metrics": {k: errors(test[target], m.predict(test[features])) for k, m in models.items()},
        "median_baseline": errors(test[target], np.full(len(test), p.iloc[development][target].median())),
        "epc_ablation_selection_mae_gbp": {"without_epc": no_epc_mae, "with_epc": selection[selected]["mae_gbp"]},
        "interval_nominal_coverage": .9, "interval_coverage": float(np.mean(abs(test[target] - pred) <= radius)),
        "interval_radius_gbp": radius, "mean_interval_width_gbp": float(np.mean(pred + radius - np.maximum(0, pred-radius))),
        "counts": {k: {"rows": len(v), "groups": p.iloc[v].customer_id.nunique()} for k, v in splits.items()},
        "group_overlap": False, "chronological_evaluation": "unavailable: no transactions or sale dates",
    }
    subgroups = {}
    for col in CATEGORIES:
        subgroups[col] = {}
        for label in sorted(test[col].unique()):
            mask = (test[col] == label).to_numpy()
            subgroups[col][label] = {"rows": int(mask.sum()), **errors(test.loc[mask, target], pred[mask]),
                                    "coverage": float(np.mean(abs(test.loc[mask, target].to_numpy()-pred[mask]) <= radius))}
    report["small_sample_subgroups_descriptive_only"] = subgroups
    predictions = test[["property_id", "customer_id", *features, target]].copy()
    predictions["prediction_gbp"] = pred
    predictions["lower_gbp"] = np.maximum(0, pred-radius)
    predictions["upper_gbp"] = pred+radius
    predictions.to_csv(output / "held_out_snapshot_predictions.csv", index=False)
    manifest = p[["property_id", "customer_id"]].copy()
    for name, indices in splits.items():
        manifest.loc[indices, "split"] = name
    manifest.to_csv(output / "snapshot_split_manifest.csv", index=False)
    joblib.dump({"experiment": "synthetic_snapshot_only", "model": model, "features": features,
                 "radius": radius, "report": report}, output / "snapshot_model.joblib")
    summary = {
        "inputs_sha256": {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest() for path in [properties_path, energy_path]},
        "data_quality": {"properties": len(p), "monthly_readings": len(e), "complete_years": len(scores),
                         "regeneration_max_absolute_error_kwh": regeneration_errors,
                         "generator_physical_checks": "passed; internal consistency only"},
        "scoring": {"available_full_scores": int(scores.score.notna().sum()),
                    "unavailable_full_scores": int(scores.score.isna().sum()),
                    "missing_field_counts": dict(Counter(field for a in assessments for field in a["score"]["missing_fields"])),
                    "component_available_counts": {c: int(scores[c+"_subscore"].notna().sum()) for c in [x["name"] for x in assessments[0]["score"]["components"]]},
                    "reproducibility": "passed for all properties"},
        "annual_energy": {"electricity_median_kwh": float(scores.annual_electricity_kwh.median()),
                          "gas_heated_median_kwh": float(scores.loc[scores.annual_gas_kwh > 0, "annual_gas_kwh"].median())},
        "valuation": report,
        "pending": ["Full scores: documented intensity benchmark; solar contribution; heat-pump subtype",
                    "Retrofit feasibility and scenario engine", "Carbon engine and documented factors",
                    "Recorded LLM responses and reviews", "Observed sales for real valuation"]}
    (output / "initial_metrics.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, default=ROOT / "Data")
    parser.add_argument("--output", type=Path, default=ROOT / "evaluation/results/initial_dataset")
    args = parser.parse_args()
    run(args.data, args.output)


if __name__ == "__main__":
    main()
