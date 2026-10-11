"""Run the saved synthetic fixture model, with explicit illustrative opt-in."""
import json
import pandas as pd
from backend.app.services.valuation_service import predict_value_impact
from ml.valuation import load_artifact


def main():
    path = "ml/models/valuation.joblib"
    artifact = load_artifact(path)
    df = pd.read_csv("ml/fixtures/synthetic_sales.csv")
    for _, row in df.iterrows():
        if all(lo <= row[c] <= hi for c, (lo, hi) in artifact["numeric_bounds"].items()):
            baseline = row.to_dict()
            # Declared synthetic input required by the API guard, not a model
            # feature or an anchor derived from this row's sale-price target.
            baseline['current_property_value_gbp'] = 300000
            break
    else:
        raise ValueError("No fixture row inside training support")
    scenario = {**baseline, "energy_rating": "B" if baseline["energy_rating"] != "B" else "A"}
    # This is an invented updated EPC used only to demonstrate inference.
    print(json.dumps({"normal_mode": predict_value_impact(baseline, scenario, path),
                      "illustrative_demo": predict_value_impact(baseline, scenario, path, allow_illustrative=True)}, indent=2))


if __name__ == "__main__":
    main()
