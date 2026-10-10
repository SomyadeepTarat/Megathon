"""PRD integration: predict_value_impact(baseline, scenario).

scenario is the complete UPDATED property, not a list of retrofit IDs.
"""
from __future__ import annotations

import os
import pickle
import sys
from pathlib import Path

import numpy as np
import pandas as pd

# Support the documented backend launch from its own directory as well as repo root.
PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
from ml.valuation import CATEGORICAL, ENERGY, NUMERIC, load_artifact

DEFAULT_MODEL = Path(__file__).resolve().parents[3] / "ml/models/valuation.joblib"


def unavailable(reason):
    return {"status": "unavailable", "reason": reason}


def normalize(state):
    if hasattr(state, "model_dump"):
        state = state.model_dump(mode="json")
    row = dict(state)
    if row.get("floor_area") is None:
        row["floor_area"] = row.get("floor_area_m2")
    if row.get("age") is None:
        row["age"] = row.get("property_age_years")
    return row


def feature_row(state, artifact):
    state = normalize(state)
    row = {}
    for col in artifact["features"]:
        value = state.get(col)
        if value is None:
            raise ValueError(f"Missing valuation input: {col}")
        if col in artifact["numeric_bounds"]:
            try:
                value = float(value)
            except (TypeError, ValueError):
                raise ValueError(f"Invalid numeric input: {col}") from None
            lo, hi = artifact["numeric_bounds"][col]
            if not np.isfinite(value) or not lo <= value <= hi:
                raise ValueError(f"Outside training support: {col}")
            if col == "bedrooms" and value % 1:
                raise ValueError("Bedrooms must be integral")
        else:
            # API enums use semi_detached; CSV uses Semi-detached.
            canonical = lambda x: str(x).strip().lower().replace("_", "-")
            choices = [x for x in artifact["categories"][col] if canonical(x) == canonical(value)]
            if len(choices) != 1:
                raise ValueError(f"Unseen category: {col}")
            value = choices[0]
        row[col] = value
    return row


def predict_property_value(property_data, model_path=None, *, allow_illustrative=False):
    """Baseline inference independent of EPC uplift support; no current-price anchoring."""
    snapshot = DEFAULT_MODEL.with_name("snapshot.joblib")
    path = Path(model_path or os.environ.get("VALUATION_BASELINE_MODEL_PATH") or
                (snapshot if snapshot.exists() else DEFAULT_MODEL))
    if not path.is_file():
        return unavailable("No calibrated baseline valuation model available")
    try:
        artifact = load_artifact(path)
        synthetic = artifact["provenance"]["kind"] == "synthetic"
        if synthetic and not allow_illustrative:
            return unavailable("Synthetic training data cannot support a real-world valuation")
        row = feature_row(property_data, artifact)
        value = float(artifact["model"].predict(pd.DataFrame([row]))[0])
        radius = artifact["radius"]
        if not np.isfinite(value) or value <= 0 or not np.isfinite(radius) or radius < 0:
            return unavailable("Model produced an invalid baseline valuation")
    except (ValueError, OSError, EOFError, KeyError, TypeError, AttributeError, ImportError, pickle.UnpicklingError) as error:
        return unavailable(str(error) if isinstance(error, ValueError) else "Valuation artifact is invalid or incompatible")
    return {"status": "illustrative" if synthetic else "indicative", "value_gbp": value,
            "range_gbp": [max(0, value-radius), value+radius], "confidence_level": 1-artifact["alpha"],
            "target_kind": artifact.get("target_kind", "sales"),
            "method": "Grouped regression with separate split-conformal residual calibration",
            "warnings": (["Synthetic baseline-estimate model; not an observed-market valuation."] if synthetic else []) +
                        ["Marginal interval coverage requires exchangeability; not a guaranteed sale price.",
                         "Baseline valuation does not establish a causal retrofit premium."]}


def predict_value_impact(baseline, scenario, model_path=None, *, allow_illustrative=False):
    baseline, scenario = normalize(baseline), normalize(scenario)
    path = Path(model_path or os.environ.get("VALUATION_MODEL_PATH", DEFAULT_MODEL))
    if not path.is_file():
        return unavailable("No calibrated valuation model available")
    try:
        artifact = load_artifact(path)
    except (ValueError, OSError, EOFError, KeyError, TypeError, AttributeError, ImportError, pickle.UnpicklingError):
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
    for col in ["floor_area", "bedrooms", "age", "market_index", *CATEGORICAL]:
        if baseline.get(col) != scenario.get(col):
            return unavailable(f"Unrelated characteristic changed: {col}")
    if baseline.get("property_id") != scenario.get("property_id"):
        return unavailable("Baseline and scenario refer to different properties")
    try:
        rows = [feature_row(state, artifact) for state in [baseline, scenario]]
    except ValueError as error:
        return unavailable(str(error))
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
