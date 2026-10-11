"""Evaluate a saved artifact on a genuinely new dataset (do not reuse training rows)."""
import argparse
import json
import numpy as np
import pandas as pd
from ml.valuation import load_artifact, metrics, validate_data, validate_snapshot


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--model", required=True)
    p.add_argument("--data", required=True)
    p.add_argument("--manifest", required=True, help="Training split manifest for overlap audit")
    a = p.parse_args()
    artifact = load_artifact(a.model)
    snapshot = artifact.get('target_kind') == 'snapshot'
    df = validate_snapshot(pd.read_csv(a.data)) if snapshot else validate_data(pd.read_csv(a.data))
    manifest = pd.read_csv(a.manifest, dtype=str)
    if "customer_id" in manifest and "customer_id" not in df:
        raise ValueError("Customer IDs required to audit overlap against customer-grouped training")
    for col in ["property_id", "customer_id"]:
        if col in manifest and col in df and set(df[col].astype(str)) & set(manifest[col]):
            raise ValueError(f"External evaluation overlaps development/calibration/test {col}s")
    pred = artifact["model"].predict(df[artifact["features"]])
    target = 'current_value_estimate_gbp' if snapshot else 'sale_price'
    result = metrics(df[target], pred)
    result.update(rows=len(df), target_kind=artifact.get('target_kind', 'sales'),
                  interval_coverage=float(np.mean(abs(df[target] - pred) <= artifact["radius"])))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
