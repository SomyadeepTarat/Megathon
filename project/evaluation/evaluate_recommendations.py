"""Evaluate independently reviewed feasibility labels, including conditional status."""
import argparse
import json
from pathlib import Path
from sklearn.metrics import classification_report
from evaluation.reference_policy import reference_scope


def evaluate(rows):
    scope = reference_scope(rows, "independently_reviewed", "reference")
    labels = ["eligible", "rejected", "conditional"]
    if any(r["expected"] not in labels or r["predicted"] not in labels for r in rows):
        raise ValueError("Use eligible, rejected or conditional labels")
    return {"rows": len(rows), **scope, "metrics": classification_report(
        [r["expected"] for r in rows], [r["predicted"] for r in rows],
        labels=labels, output_dict=True, zero_division=0)}


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--input", type=Path, required=True, help="JSON array of reviewed prediction/label pairs")
    a = p.parse_args()
    print(json.dumps(evaluate(json.loads(a.input.read_text())), indent=2))
