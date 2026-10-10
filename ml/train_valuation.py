"""Run with python -m ml.train_valuation --help."""
import argparse
import hashlib
import json
from pathlib import Path

import joblib
import pandas as pd

from ml.valuation import train


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--provenance", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("ml/models/valuation.joblib"))
    parser.add_argument("--reports", type=Path, default=Path("ml/reports"))
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--target-kind", choices=["sales", "snapshot"], default="sales")
    args = parser.parse_args()
    provenance = json.loads(args.provenance.read_text())
    provenance["data_sha256"] = hashlib.sha256(args.data.read_bytes()).hexdigest()
    artifact, report, predictions, manifest = train(pd.read_csv(args.data), provenance, args.seed, target_kind=args.target_kind)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.reports.mkdir(parents=True, exist_ok=True)
    joblib.dump(artifact, args.output)
    (args.reports / "valuation_metrics.json").write_text(json.dumps(report, indent=2))
    predictions.to_csv(args.reports / "held_out_predictions.csv", index=False)
    manifest.to_csv(args.reports / "split_manifest.csv", index=False)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
