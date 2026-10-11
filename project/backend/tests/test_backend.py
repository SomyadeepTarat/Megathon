from copy import deepcopy
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.schemas.models import AssessmentRequest
from app.core.scoring import calculate_score, classify, WEIGHTS

client = TestClient(app)

@pytest.fixture
def payload():
    return {
        "property": {"property_id": "TEST1", "property_type": "detached", "region": "test",
                     "floor_area_m2": 120, "energy_rating": "E", "insulation": "poor",
                     "heating_system": "old_gas_boiler", "glazing": "single",
                     "renewable_contribution": "none", "smart_controls": "none"},
        "annual_energy": {"electricity_kwh": 4800, "gas_kwh": 12000,
                          "quality": "synthetic", "method": "test fixture",
                          "electricity_months_covered": 12, "gas_months_covered": 12},
        "benchmark": {"property_type": "detached", "intensity_kwh_m2_year": 140,
                      "source": "TEST ONLY: not a real reference", "methodology": "test fixture"},
    }


def test_score_arithmetic(payload):


    result = calculate_score(AssessmentRequest.model_validate(payload))
    assert result.score == 33
    assert result.classification == "Poor"
    assert len(result.components) == 7
    assert sum(c.contribution for c in result.components) == result.unrounded_score
    assert sum(WEIGHTS.values()) == 1


@pytest.mark.parametrize("score,category", [(0,"Very poor"),(29,"Very poor"),(30,"Poor"),
    (49,"Poor"),(50,"Moderate"),(64,"Moderate"),(65,"Good"),(79,"Good"),
    (80,"Highly efficient"),(100,"Highly efficient")])
def test_classification(score, category):
    assert classify(score) == category


@pytest.mark.parametrize("field,states", [
    ("energy_rating", ["G","F","E","D","C","B","A"]),
    ("insulation", ["poor","average","good"]),
    ("heating_system", ["old_gas_boiler","modern_gas_boiler","electric_resistance","air_source_heat_pump","ground_source_heat_pump"]),
    ("glazing", ["single","double","triple"]),
    ("renewable_contribution", ["none","limited","substantial"]),
    ("smart_controls", ["none","basic","advanced"]),
])
def test_mapping_monotonicity(payload, field, states):
    scores = []
    for state in states:
        payload["property"][field] = state
        scores.append(calculate_score(AssessmentRequest.model_validate(payload)).unrounded_score)
    assert scores == sorted(scores)


def test_intensity_monotonicity_and_area(payload):
    scores = []
    for energy in [0, 1000, 4800, 30000, 100000]:
        payload["annual_energy"]["electricity_kwh"] = energy
        scores.append(calculate_score(AssessmentRequest.model_validate(payload)).unrounded_score)
    assert scores == sorted(scores, reverse=True)
    first = deepcopy(payload)
    payload["property"]["floor_area_m2"] *= 2
    payload["annual_energy"]["electricity_kwh"] *= 2
    payload["annual_energy"]["gas_kwh"] *= 2
    assert calculate_score(AssessmentRequest.model_validate(first)).score == calculate_score(AssessmentRequest.model_validate(payload)).score


def test_half_up_final_rounding(payload):
    payload["property"]["heating_system"] = "modern_gas_boiler"
    payload["annual_energy"]["electricity_kwh"] = 3960

    payload["property"]["smart_controls"] = "basic"
    result = calculate_score(AssessmentRequest.model_validate(payload))
    assert result.unrounded_score == pytest.approx(40.5)
    assert result.score == 41


def test_missing_is_not_zero(payload):
    payload["annual_energy"]["gas_kwh"] = None
    result = client.post("/assessments", json=payload).json()
    assert result["score"]["status"] == "unavailable"
    assert result["score"]["score"] is None
    assert result["poor_home"] is None
    payload["annual_energy"]["gas_kwh"] = 0
    assert client.post("/assessments", json=payload).json()["score"]["status"] == "available"


def test_missing_benchmark(payload):
    payload.pop("benchmark")
    response = client.post("/assessments", json=payload)
    assert response.status_code == 200
    assert response.json()["score"]["missing_fields"] == ["benchmark"]


@pytest.mark.parametrize("section,field,value", [("property","floor_area_m2",0),
    ("annual_energy","gas_kwh",-1),("property","energy_rating","Z"),
    ("benchmark","property_type","flat"),("property","unexpected",True)])
def test_invalid_inputs(payload, section, field, value):
    payload[section][field] = value
    assert client.post("/assessments", json=payload).status_code == 422


def test_no_simulation_numbers(payload):
    payload["retrofits"] = ["heat_pump"]
    response = client.post("/scenarios/simulate", json=payload)
    assert response.status_code == 409
    assert response.json()["status"] == "rejected"
    assert response.json()["energy"] is None
    payload["retrofits"] = ["heat_pump", "heat_pump"]
    assert client.post("/scenarios/simulate", json=payload).status_code == 422


def test_repeated_assessment_preserves_input(payload):
    before = deepcopy(payload)
    first = client.post("/assessments", json=payload)
    second = client.post("/assessments", json=payload)
    assert first.status_code == 200
    assert first.json() == second.json()
    assert payload == before
    assert client.get("/health").json()["capabilities"]["scoring"] is True
