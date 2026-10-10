"""Errors against independently prepared per-fuel reference estimates."""
import argparse
import json
from pathlib import Path
import numpy as np
from evaluation.reference_policy import reference_scope


def evaluate(rows):
    scope = reference_scope(rows, "independently_prepared", "reference_source")
    result = {}
    for fuel in ["electricity_kwh", "gas_kwh"]:
        expected = np.array([r["expected_after"][fuel] for r in rows], dtype=float)
        predicted = np.array([r["predicted_after"][fuel] for r in rows], dtype=float)
        if not np.isfinite(expected).all() or not np.isfinite(predicted).all() or (expected < 0).any() or (predicted < 0).any():
            raise ValueError("Reference and predicted fuel values must be finite and nonnegative")
        nonzero = expected != 0
        result[fuel] = {"mae_kwh": float(np.mean(abs(expected - predicted))),
                        "mape_percent": float(100 * np.mean(abs((expected[nonzero] - predicted[nonzero]) / expected[nonzero]))) if nonzero.any() else None,
                        "percentage_error_rows": int(nonzero.sum()), "zero_reference_rows": int((~nonzero).sum())}
    return {"rows": len(rows), "per_fuel": result, **scope}


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--input", type=Path, required=True)
    a = p.parse_args()
    print(json.dumps(evaluate(json.loads(a.input.read_text())), indent=2))
