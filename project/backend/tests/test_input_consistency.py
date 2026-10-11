import copy
import json
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.schemas.models import Property
from app.services.input_consistency import conflicting_inputs


def payload():
    row = json.loads((Path(__file__).resolve().parents[1] / 'data/curated_demo_properties.json').read_text())[4]
    return {k: v for k, v in row.items() if k not in ('dataset_kind', 'dataset_source')}


@pytest.mark.parametrize('patch,field', [
    ({'heat_pump_installed': True}, 'heating_system'),
    ({'physical_inputs': {'space_heating_demand_kwh': 100000}}, 'space_heating_demand_kwh'),
    ({'solar_installed': False, 'physical_inputs': {'solar_generation_kwh': 1000}}, 'solar_installed'),
    ({'smart_thermostat_installed': True, 'smart_controls': 'none'}, 'smart_controls'),
])
def test_conflicting_evidence_never_produces_scenario_numbers(patch, field):
    value = payload()
    patch = copy.deepcopy(patch)
    value['property']['physical_inputs'].update(patch.pop('physical_inputs', {}))
    value['property'].update(patch)
    response = TestClient(app).post('/scenarios/simulate', json={**value, 'retrofits': ['loft_insulation']})
    assert response.status_code == 503
    result = response.json()
    assert result['status'] == 'unavailable'
    assert field in result['reason']
    assert result['energy'] is None
    assert result['valuation']['value_change_range_gbp'] is None


def test_consistency_tolerance_and_missing_are_not_zero():
    value = payload()['property']
    property = Property.model_validate(value)
    assert conflicting_inputs(property) == []
    property.physical_inputs.gas_space_heating_kwh = None
    assert conflicting_inputs(property) == []
    property.physical_inputs.gas_space_heating_kwh = 0
    assert 'space_heating' in ' '.join(conflicting_inputs(property))


def test_assessment_surfaces_conflict_without_losing_metered_carbon():
    value = payload()
    value['property']['heat_pump_installed'] = True
    result = TestClient(app).post('/assessments/full', json=value).json()
    assert any('heating_system' in warning for warning in result['assessment']['warnings'])
    assert result['baseline_carbon']['status'] == 'available'


def test_explicit_energy_impact_endpoint_cannot_bypass_conflict_guard():
    from app.main import get_repository
    from app.db.repository import JsonPropertyRepository
    repository = JsonPropertyRepository(Path(__file__).resolve().parents[1] / 'data/curated_demo_properties.json')
    app.dependency_overrides[get_repository] = lambda: repository
    value = payload()
    value['property']['heat_pump_installed'] = True
    try:
        response = TestClient(app).post('/properties/DEMO-P00005/valuation/impact', json={
            'scenario_property': value['property'], 'scenario_annual_energy': value['annual_energy']})
        assert response.status_code == 200
        result = response.json()
        assert result['status'] == 'unavailable'
        assert 'Conflicting' in result['reason']
        assert result['uplift_range'] is None
    finally:
        app.dependency_overrides.pop(get_repository, None)
