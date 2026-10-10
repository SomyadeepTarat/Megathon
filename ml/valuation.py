"""Grouped regression, untouched calibration, and conservative inference."""
from __future__ import annotations

import math
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import GroupShuffleSplit
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

NUMERIC = ["floor_area", "bedrooms", "age", "market_index"]
CATEGORICAL = ["region", "property_type"]
ENERGY = "energy_rating"


def validate_data(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    required = ["property_id", "sale_date", "sale_price", *NUMERIC, *CATEGORICAL]
    missing = sorted(set(required) - set(df.columns))
    if missing:
        raise ValueError(f"Missing columns: {missing}")
    for col in ["property_id", *CATEGORICAL]:
        if df[col].isna().any() or df[col].astype(str).str.strip().eq("").any():
            raise ValueError(f"Missing {col}")
        df[col] = df[col].astype(str).str.strip()
    for col in ["sale_price", *NUMERIC]:
        df[col] = pd.to_numeric(df[col], errors="raise")
        if not np.isfinite(df[col]).all():
            raise ValueError(f"Nonfinite or missing {col}")
    if (df[["sale_price", "floor_area", "market_index"]] <= 0).any().any():
        raise ValueError("Price, area and market index must be positive")
    if (df[["age", "bedrooms"]] < 0).any().any():
        raise ValueError("Age and bedrooms must be nonnegative")
    if (df.bedrooms % 1 != 0).any():
        raise ValueError("Bedrooms must be integral")
    df["sale_date"] = pd.to_datetime(df.sale_date, errors="raise")
    if df.sale_date.isna().any():
        raise ValueError("Missing sale date")
    if df.duplicated(["property_id", "sale_date"]).any():
        raise ValueError("Duplicate property/date transactions")
    if ENERGY in df:
        df[ENERGY] = df[ENERGY].astype("string").str.upper().str.strip()
        if df[ENERGY].isna().any() or not df[ENERGY].isin(list("ABCDEFG")).all():
            raise ValueError("EPC must be A–G; use energy_rating_at_sale, never a future EPC")
    if "customer_id" in df:
        if df.customer_id.isna().any():
            raise ValueError("Missing customer ID")
        df["customer_id"] = df.customer_id.astype(str).str.strip()
        if df.customer_id.eq("").any() or df.groupby("property_id").customer_id.nunique().max() > 1:
            raise ValueError("Each property must map to one nonempty customer group")
    return df.reset_index(drop=True)


def grouped_splits(df, seed=42):
    """70% development (55 fit +15 selection), 15 calibration, 15 test."""
    groups = df["customer_id"] if "customer_id" in df else df.property_id
    if groups.nunique() < 40:
        raise ValueError("At least 40 independent groups required for four-way evaluation")
    def partition(indices, fraction, offset):
        a, b = next(GroupShuffleSplit(n_splits=1, test_size=fraction, random_state=seed + offset)
                    .split(indices, groups=groups.iloc[indices]))
        return indices[a], indices[b]
    development, test = partition(np.arange(len(df)), .15, 0)
    development, calibration = partition(development, .15 / .85, 1)
    fit, selection = partition(development, .15 / .70, 2)
    return dict(fit=fit, selection=selection, calibration=calibration, test=test)


def pipeline(kind, energy=True):
    cats = CATEGORICAL + ([ENERGY] if energy else [])
    prep = ColumnTransformer([
        ("numeric", make_pipeline(SimpleImputer(strategy="median"), StandardScaler()), NUMERIC),
        ("category", OneHotEncoder(handle_unknown="ignore", sparse_output=False), cats),
    ])
    model = Ridge(alpha=10) if kind == "ridge" else HistGradientBoostingRegressor(
        max_iter=120, max_leaf_nodes=15, l2_regularization=10, random_state=42, early_stopping=False)
    return make_pipeline(prep, model)


def metrics(y, predictions):
    return {"mae_gbp": float(mean_absolute_error(y, predictions)),
            "rmse_gbp": float(np.sqrt(mean_squared_error(y, predictions))),
            "r2": float(r2_score(y, predictions)) if len(y) > 1 else None}


def conformal_radius(residuals, alpha):
    """Finite-sample corrected order statistic; never interpolate quantiles."""
    if not 0 < alpha < 1:
        raise ValueError("alpha must be between zero and one")
    rank = math.ceil((len(residuals) + 1) * (1 - alpha))
    if rank > len(residuals):
        raise ValueError("Too few calibration examples for requested coverage")
    return float(np.sort(residuals)[rank - 1])


def train(df, provenance, seed=42, alpha=.1):
    df = validate_data(df)
    if provenance.get("kind") not in {"observed", "synthetic"}:
        raise ValueError("Provenance kind must be observed or synthetic")
    if not provenance.get("source") or not provenance.get("license"):
        raise ValueError("Document source and license in provenance JSON")
    energy = ENERGY in df
    features = NUMERIC + CATEGORICAL + ([ENERGY] if energy else [])
    splits = grouped_splits(df, seed)
    fit, select, cal, test = (df.iloc[splits[k]] for k in ["fit", "selection", "calibration", "test"])
    candidates, selection_metrics = {}, {}
    for kind in ["ridge", "hist_gradient_boosting"]:
        model = pipeline(kind, energy).fit(fit[features], fit.sale_price)
        candidates[kind] = model
        selection_metrics[kind] = metrics(select.sale_price, model.predict(select[features]))
    # Require a material improvement; selection never touches calibration/test.
    selected = "hist_gradient_boosting" if selection_metrics["hist_gradient_boosting"]["mae_gbp"] < .98 * selection_metrics["ridge"]["mae_gbp"] else "ridge"
    dev = pd.concat([fit, select])
    for kind in candidates:
        candidates[kind].fit(dev[features], dev.sale_price)
    model = candidates[selected]
    energy_signal = None
    if energy:
        without_energy = pipeline(selected, False).fit(fit[NUMERIC + CATEGORICAL], fit.sale_price)
        without_mae = metrics(select.sale_price, without_energy.predict(select[NUMERIC + CATEGORICAL]))["mae_gbp"]
        with_mae = selection_metrics[selected]["mae_gbp"]
        energy_signal = {"without_epc_selection_mae_gbp": without_mae,
                         "with_epc_selection_mae_gbp": with_mae,
                         "relative_mae_improvement": (without_mae - with_mae) / without_mae if without_mae else 0}
    # One randomly sampled transaction per independent group avoids treating
    # repeated transactions/customers as independent conformal observations.
    group_col = "customer_id" if "customer_id" in df else "property_id"
    cal_independent = cal.sample(frac=1, random_state=seed).drop_duplicates(group_col)
    residuals = np.abs(cal_independent.sale_price.to_numpy() - model.predict(cal_independent[features]))
    radius = conformal_radius(residuals, alpha)
    pair_radius = conformal_radius(residuals, alpha / 2)
    pred = model.predict(test[features])
    report = {
        "selected_model": selected, "seed": seed, "alpha": alpha,
        "provenance": provenance, "selection_metrics": selection_metrics,
        "energy_signal_ablation": energy_signal,
        "held_out_metrics": {k: metrics(test.sale_price, m.predict(test[features])) for k, m in candidates.items()},
        "median_baseline": metrics(test.sale_price, np.full(len(test), dev.sale_price.median())),
        "interval_coverage": float(np.mean(np.abs(test.sale_price - pred) <= radius)),
        "mean_interval_width_gbp": float(np.mean(pred + radius - np.maximum(0, pred - radius))),
        "pair_marginal_coverage": float(np.mean(np.abs(test.sale_price - pred) <= pair_radius)),
        "counts": {k: {"rows": len(v), "properties": df.iloc[v].property_id.nunique(),
                       "groups": df.iloc[v]["customer_id" if "customer_id" in df else "property_id"].nunique()} for k, v in splits.items()},
        "calibration_independent_groups": len(cal_independent),
        "group_overlap": any(set(df.iloc[splits[a]][group_col]) & set(df.iloc[splits[b]][group_col])
                             for i, a in enumerate(splits) for b in list(splits)[i + 1:]),
        "time_evaluation": "not_run; random grouped split does not measure temporal generalization",
        "limitations": ["Observational associations are not causal retrofit effects.",
                        "Conformal coverage is marginal under exchangeability; scenario shifts can invalidate it.",
                        "Synthetic metrics verify implementation, not market accuracy.",
                        "Value-change intervals have no paired counterfactual coverage validation."],
    }
    # A reviewed evidence reference is required; EPC availability alone proves nothing.
    evidence = provenance.get("energy_evidence", {})
    supported = (energy and energy_signal["relative_mae_improvement"] > 0 and provenance["kind"] == "observed" and
                 evidence.get("reviewed") is True and bool(evidence.get("reference")))
    artifact = {"format_version": 1, "model": model, "features": features,
                "radius": radius, "pair_radius": pair_radius, "alpha": alpha,
                "provenance": provenance, "energy_supported": supported,
                "numeric_bounds": {c: [float(dev[c].min()), float(dev[c].max())] for c in NUMERIC},
                "categories": {c: sorted(dev[c].unique().tolist()) for c in CATEGORICAL + ([ENERGY] if energy else [])},
                "report": report}
    held_out = test[["property_id", "sale_date", "sale_price"]].copy()
    held_out["prediction_gbp"] = pred
    held_out["lower_gbp"] = np.maximum(0, pred - radius)
    held_out["upper_gbp"] = pred + radius
    manifest = df[["property_id"] + (["customer_id"] if "customer_id" in df else [])].copy()
    for name, indices in splits.items():
        manifest.loc[indices, "split"] = name
    return artifact, report, held_out, manifest


def load_artifact(path):
    # joblib uses pickle: load only artifacts produced by trusted local training.
    artifact = joblib.load(Path(path))
    if artifact.get("format_version") != 1:
        raise ValueError("Unsupported valuation artifact")
    return artifact
