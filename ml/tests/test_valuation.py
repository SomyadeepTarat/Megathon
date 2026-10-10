import itertools
import joblib
import numpy as np
import pytest

from ml.make_fixture import fixture
from ml.valuation import conformal_radius, grouped_splits, train, validate_data
from backend.app.services.valuation_service import predict_value_impact


@pytest.fixture(scope="module")
def trained(tmp_path_factory):
    df = fixture()
    artifact, report, predictions, manifest = train(df, {"kind": "synthetic", "source": "test fixture", "license": "test"})
    path = tmp_path_factory.mktemp("model") / "valuation.joblib"
    joblib.dump(artifact, path)
    return df, artifact, report, predictions, manifest, path


def test_group_leakage_and_reproducibility():
    df = fixture()
    splits = grouped_splits(df)
    for a, b in itertools.combinations(splits, 2):
        assert not set(df.iloc[splits[a]].property_id) & set(df.iloc[splits[b]].property_id)
        assert not set(df.iloc[splits[a]].customer_id) & set(df.iloc[splits[b]].customer_id)
    assert sum(map(len, splits.values())) == len(df)
    for k, v in grouped_splits(df).items():
        np.testing.assert_array_equal(v, splits[k])


@pytest.mark.parametrize("column,value", [("sale_price", 0), ("floor_area", np.nan), ("bedrooms", 1.5), ("age", -1), ("energy_rating", "Z")])
def test_bad_data(column, value):
    df = fixture()
    df.loc[0, column] = value
    with pytest.raises(ValueError):
        validate_data(df)


def test_future_value_not_feature(trained):
    _, artifact, report, predictions, _, _ = trained
    assert "sale_price" not in artifact["features"]
    assert "current_value_estimate" not in artifact["features"]
    assert not report["group_overlap"]
    assert len(predictions) == report["counts"]["test"]["rows"]
    assert set(report["held_out_metrics"]) == {"ridge", "hist_gradient_boosting"}
    assert 0 <= report["interval_coverage"] <= 1


def test_conformal_corrected_rank():
    assert conformal_radius(np.arange(1, 20), .1) == 18
    with pytest.raises(ValueError):
        conformal_radius([1, 2], .05)


def supported_state(trained):
    df, artifact, _, _, _, _ = trained
    # Pick a row inside development numeric bounds.
    for _, row in df.iterrows():
        if all(lo <= row[c] <= hi for c, (lo, hi) in artifact["numeric_bounds"].items()):
            return row.to_dict()


def test_safe_default_and_same_state(trained):
    state = supported_state(trained)
    path = trained[-1]
    assert predict_value_impact(state, state, path)["status"] == "unavailable"
    result = predict_value_impact(state, state, path, allow_illustrative=True)
    assert result["status"] == "illustrative"
    assert result["value_change_range_gbp"] == [0, 0]


def test_scenario_validation(trained):
    state = supported_state(trained)
    path = trained[-1]
    for changed in [{**state, "floor_area": state["floor_area"] + 1}, {**state, "energy_rating": "X"}]:
        assert predict_value_impact(state, changed, path, allow_illustrative=True)["status"] == "unavailable"
    result = predict_value_impact(state, {**state, "energy_rating": "B" if state["energy_rating"] != "B" else "A"}, path, allow_illustrative=True)
    assert result["value_change_range_gbp"][0] <= result["value_change_gbp"] <= result["value_change_range_gbp"][1]
    assert predict_value_impact(state, state, "/tmp/missing-greenprint-model")["status"] == "unavailable"


def test_observed_requires_review(trained, tmp_path):
    artifact = dict(trained[1])
    artifact["provenance"] = {"kind": "observed"}
    artifact["energy_supported"] = False
    path = tmp_path / "observed.joblib"
    joblib.dump(artifact, path)
    state = supported_state(trained)
    assert predict_value_impact(state, state, path)["status"] == "unavailable"
