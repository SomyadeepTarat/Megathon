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
import pandas as pd

from ml.valuation import train, validate_snapshot

ROOT = Path(__file__).resolve().parents[1]
NUMERIC = ["floor_area_m2", "bedrooms", "age"]


def run(data, output):
    data, output = data.resolve(), output.resolve()
    properties_path, energy_path = data / "csv/properties.csv", data / "csv/energy_usage.csv"
    p = pd.read_csv(properties_path, dtype={"property_id": str, "customer_id": str})
    e = pd.read_csv(energy_path, dtype={"property_id": str})
    output.mkdir(parents=True, exist_ok=True)
    validate_snapshot(p)
    if e.isna().any().any():
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

    # Same artifact contract and leakage controls as production training.
    provenance = json.loads((ROOT / 'ml/snapshot_provenance.json').read_text())
    provenance['data_sha256'] = hashlib.sha256(properties_path.read_bytes()).hexdigest()
    artifact, report, predictions, manifest = train(p, provenance, target_kind='snapshot')
    predictions.to_csv(output / 'held_out_snapshot_predictions.csv', index=False)
    manifest.to_csv(output / 'snapshot_split_manifest.csv', index=False)
    joblib.dump(artifact, output / 'snapshot_model.joblib')
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
        "pending": ["Official benchmark validation (current supplied references are synthetic)",
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
