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
    parser.add_argument("--split-manifest", type=Path, help="Exact property/customer fit/selection/calibration/test assignments")
    parser.add_argument("--exclude-split", help="Explicit diagnostic-only partition to exclude from training/evaluation")
    parser.add_argument("--interval-policy", choices=["absolute", "price_proportional"], default="absolute")
    args = parser.parse_args()
    provenance = json.loads(args.provenance.read_text())
    provenance["data_sha256"] = hashlib.sha256(args.data.read_bytes()).hexdigest()
    supplied_splits = pd.read_csv(args.split_manifest, dtype=str) if args.split_manifest else None
    frame = pd.read_csv(args.data)
    if args.exclude_split:
        if supplied_splits is None or args.exclude_split in {"fit", "selection", "calibration", "test"}:
            raise ValueError("Exclude only an explicit diagnostic partition in a supplied manifest")
        excluded = supplied_splits.loc[supplied_splits.split == args.exclude_split, "property_id"]
        if excluded.empty or not set(excluded).issubset(set(frame.property_id)):
            raise ValueError("Diagnostic partition must exist and match supplied property IDs")
        provenance["excluded_partition"] = {"name": args.exclude_split, "properties": len(excluded)}
        frame = frame[~frame.property_id.isin(excluded)].reset_index(drop=True)
        supplied_splits = supplied_splits[~supplied_splits.property_id.isin(excluded)]
    if args.split_manifest:
        provenance["split_manifest_sha256"] = hashlib.sha256(args.split_manifest.read_bytes()).hexdigest()
    artifact, report, predictions, manifest = train(frame, provenance, args.seed,
        target_kind=args.target_kind, split_manifest=supplied_splits, interval_policy=args.interval_policy)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.reports.mkdir(parents=True, exist_ok=True)
    joblib.dump(artifact, args.output)
    (args.reports / "valuation_metrics.json").write_text(json.dumps(report, indent=2))
    predictions.to_csv(args.reports / "held_out_predictions.csv", index=False)
    manifest.to_csv(args.reports / "split_manifest.csv", index=False)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
