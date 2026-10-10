"""Synthetic SOFTWARE TEST data; invented prices are never market evidence."""
import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd


def fixture(n=600, seed=42):
    rng = np.random.default_rng(seed)
    area = rng.uniform(45, 220, n)
    regions = rng.choice(["Fixture North", "Fixture South", "Fixture Central"], n)
    rating = rng.choice(list("ABCDEFG"), n)
    types = rng.choice(["Detached", "Semi-detached", "Flat", "Terraced"], n)
    market = rng.uniform(.9, 1.1, n)
    age = rng.integers(1, 130, n)
    # Intentionally invented, documented relationship to exercise regression only.
    price = (area * 2200 + np.where(regions == "Fixture South", 80000, 0)
             + np.where(types == "Detached", 30000, 0)
             + np.array(["GFEDCBA".index(r) * 4000 for r in rating])
             - age * 150) * market + rng.normal(0, 18000, n)
    return pd.DataFrame(dict(property_id=[f"FIX{i:05}" for i in range(n)],
                             customer_id=[f"C{i // 2:05}" for i in range(n)],
                             sale_date=[f"2024-{i % 12 + 1:02}-01" for i in range(n)],
                             sale_price=np.maximum(20000, price), floor_area=area,
                             bedrooms=np.clip(np.floor(area / 40), 1, 5), age=age,
                             market_index=market, region=regions, property_type=types,
                             energy_rating=rating))


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--output", type=Path, default=Path("ml/fixtures"))
    args = p.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    fixture().to_csv(args.output / "synthetic_sales.csv", index=False)
    provenance = {"kind": "synthetic", "source": "ml.make_fixture, seed 42; invented price equation",
                  "license": "Project-generated test fixture; no external data",
                  "energy_evidence": {"reviewed": False, "reference": None}}
    (args.output / "provenance.json").write_text(json.dumps(provenance, indent=2))


if __name__ == "__main__":
    main()
