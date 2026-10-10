"""PRD integration: predict_value_impact(baseline, scenario).

scenario is the complete UPDATED property, not a list of retrofit IDs.
"""
from __future__ import annotations

import os
from pathlib import Path

import numpy as np
import pandas as pd

from ml.valuation import CATEGORICAL, ENERGY, NUMERIC, load_artifact

DEFAULT_MODEL = Path(__file__).resolve().parents[3] / "ml/models/valuation.joblib"


def unavailable(reason):
    return {"status": "unavailable", "reason": reason}


def predict_value_impact(baseline, scenario, model_path=None, *, allow_illustrative=False):
    path = Path(model_path or os.environ.get("VALUATION_MODEL_PATH", DEFAULT_MODEL))
    if not path.is_file():
        return unavailable("No calibrated valuation model available")
    try:
        artifact = load_artifact(path)
    except (ValueError, OSError, EOFError, KeyError):
        return unavailable("Valuation artifact is invalid or incompatible")
    synthetic = artifact["provenance"]["kind"] == "synthetic"
    if synthetic and not allow_illustrative:
        return unavailable("Synthetic training data cannot support real-world value uplift")
    if not synthetic and not artifact["energy_supported"]:
        return unavailable("No reviewed evidence supporting an energy-efficiency valuation relationship")
    features = artifact["features"]
    if ENERGY not in features:
        return unavailable("Model has no supported energy-efficiency feature")
    # Reject changes unrelated to retrofits rather than silently crediting them.
    for col in NUMERIC + CATEGORICAL:
        if baseline.get(col) != scenario.get(col):
            return unavailable(f"Unrelated characteristic changed: {col}")
    if baseline.get("property_id") != scenario.get("property_id"):
        return unavailable("Baseline and scenario refer to different properties")
    rows = []
    for state in [baseline, scenario]:
        row = {}
        for col in features:
            value = state.get(col)
            if value is None:
                return unavailable(f"Missing valuation input: {col}")
            if col in NUMERIC:
                try:
                    value = float(value)
                except (TypeError, ValueError):
                    return unavailable(f"Invalid numeric input: {col}")
                lo, hi = artifact["numeric_bounds"][col]
                if not np.isfinite(value) or not lo <= value <= hi:
                    return unavailable(f"Outside training support: {col}")
            elif value not in artifact["categories"][col]:
                return unavailable(f"Unseen category: {col}")
            row[col] = value
        rows.append(row)
    predictions = artifact["model"].predict(pd.DataFrame(rows))
    if not np.isfinite(predictions).all() or (predictions <= 0).any():
        return unavailable("Model produced an invalid property value")
    before, after = map(float, predictions)
    delta = after - before
    q = artifact["radius"]
    # Exact equality of supported features means an exact zero MODEL contrast.
    width = 0 if rows[0] == rows[1] else 2 * artifact["pair_radius"]
    return {
        "status": "illustrative" if synthetic else "indicative",
        "baseline_value_gbp": before, "after_value_gbp": after,
        "baseline_range_gbp": [max(0, before - q), before + q],
        "after_range_gbp": [max(0, after - q), after + q],
        "value_change_gbp": delta, "value_change_range_gbp": [delta - width, delta + width],
        "confidence_level": 1 - artifact["alpha"],
        "method": "Split conformal absolute residuals; contrast uses two alpha/2 marginal bands",
        "warnings": ["Observational model contrast; not a causal retrofit premium.",
                     "Contrast coverage is unvalidated; exchangeability may fail for retrofit scenarios.",
                     "Physical upgrades without a supported updated EPC do not change the model estimate."],
    }
