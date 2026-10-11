import copy
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from app.main import app
from ml.synthetic_impact import train_demo

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope='module')
def model(tmp_path_factory):
    path = tmp_path_factory.mktemp('synthetic-impact')
    report = train_demo(path/'model.joblib', path/'reports')
    assert report['group_overlap'] is False
    assert report['nonnegative_direction_fraction'] == 1
    return path/'model.joblib', report


@pytest.fixture
def payload():
    row = json.loads((ROOT/'backend/data/curated_demo_properties.json').read_text())[0]
    row.pop('dataset_kind'); row.pop('dataset_source')
    return {**row, 'retrofits': ['heat_pump']}


def use_model(monkeypatch, path):
    from app.services import adapters
    from ml.synthetic_impact import predict_impact
    from app.schemas.engines import ValuationResult
    def predict(self, request, scenario, energy):
        if request.annual_energy.quality != 'synthetic':
            return ValuationResult(status='unavailable', reason='Observed input is not supported by the synthetic model.')
        return ValuationResult.model_validate(predict_impact(request.property, scenario, energy, path))
    monkeypatch.setattr(adapters.ExistingValuationAdapter, 'predict_scenario_impact', predict)


def test_integrated_impact_uses_energy_not_invented_epc(model, payload, monkeypatch):
    use_model(monkeypatch, model[0])
    with TestClient(app) as client:
        response = client.post('/scenarios/simulate', json=payload)
    assert response.status_code == 200
    result = response.json()
    value = result['valuation']
    assert value['status'] == 'illustrative'
    assert result['updated_property']['energy_rating'] == payload['property']['energy_rating']
    assert value['baseline_value_gbp'] == payload['property']['current_property_value_gbp']
    assert value['after_value_gbp'] - value['baseline_value_gbp'] == pytest.approx(value['value_change_gbp'])
    assert value['value_change_gbp'] >= 0
    assert value['uplift_range'][0] <= value['value_change_gbp'] <= value['uplift_range'][1]


@pytest.mark.parametrize('field', ['current_property_value_gbp', 'energy_rating', 'property_age_years', 'bedrooms'])
def test_missing_inputs_never_silently_impute(model, payload, monkeypatch, field):
    use_model(monkeypatch, model[0]); payload['property'][field] = None
    result = TestClient(app).post('/scenarios/simulate', json=payload).json()['valuation']
    assert result['status'] == 'unavailable'
    assert 'missing' in result['reason'].lower()
    assert all(result[key] is None for key in ('value_before', 'value_after', 'uplift_range'))


def test_unchanged_scenario_exact_zero(model, payload, monkeypatch):
    use_model(monkeypatch, model[0]); payload['retrofits'] = []
    result = TestClient(app).post('/scenarios/simulate', json=payload).json()['valuation']
    assert result['value_change_gbp'] == 0
    assert result['uplift_range'] == [0, 0]


def test_actual_adapter_blocks_observed_inputs(payload):
    payload['annual_energy']['quality'] = 'observed'
    result = TestClient(app).post('/scenarios/simulate', json=payload).json()['valuation']
    assert result['status'] == 'unavailable'
    assert 'projected EPC' in result['reason']


def test_missing_artifact_and_changed_location(model, payload):
    from ml.synthetic_impact import predict_impact
    from app.schemas.engines import EnergyImpact, FuelState
    prop = payload['property']
    fuel = FuelState(electricity_kwh=2000, gas_kwh=12000)
    energy = EnergyImpact(baseline=fuel, after=fuel, electricity_savings_kwh=0, gas_savings_kwh=0,
        net_savings_kwh=0, improvement_percentage=0)
    assert predict_impact(prop, prop, energy, '/missing/model.joblib')['status'] == 'unavailable'
    changed = copy.deepcopy(prop); changed['region'] = 'Another region'
    result = predict_impact(prop, changed, energy, model[0])
    assert result['status'] == 'unavailable' and 'region' in result['reason']


def test_test_groups_are_untouched_and_targets_not_features(model):
    import pandas as pd
    import joblib
    artifact = joblib.load(model[0])
    assert 'sale_price' not in artifact['features'] and 'baseline_value' not in artifact['features']
    manifest = pd.read_csv(model[0].parent/'reports/split_manifest.csv')
    assert manifest.property_id.is_unique and manifest.split.nunique() == 4
    assert model[1]['counts']['test'] == 360


def test_impact_endpoint_accepts_explicit_scenario_energy_and_rejects_missing_fuel(model, payload, monkeypatch):
    from app.main import get_repository
    from app.db.repository import JsonPropertyRepository
    use_model(monkeypatch, model[0])
    monkeypatch.setitem(app.dependency_overrides, get_repository,
        lambda: JsonPropertyRepository(ROOT/'backend/data/curated_demo_properties.json'))
    with TestClient(app) as client:
        scenario = client.post('/scenarios/simulate', json=payload).json()
        energy = {**payload['annual_energy'], **scenario['energy']['after'],
                  'quality': 'estimated', 'method': 'Actual backend simulation'}
        body = {'scenario_property': scenario['updated_property'], 'scenario_annual_energy': energy}
        route = '/properties/DEMO-P00001/valuation/impact'
        result = client.post(route, json=body)
        assert result.status_code == 200 and result.json()['status'] == 'illustrative'
        assert result.json()['value_change_gbp'] == pytest.approx(scenario['valuation']['value_change_gbp'])
        body['scenario_annual_energy']['gas_kwh'] = None
        result = client.post(route, json=body).json()
        assert result['status'] == 'unavailable' and result['uplift_range'] is None
