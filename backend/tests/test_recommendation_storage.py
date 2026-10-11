"""Ranking and stored frontend contracts exercised through mounted routes."""
import sqlite3

import pytest
from fastapi.testclient import TestClient

from app.main import app, get_repository
from app.db.repository import EditableRepository, JsonPropertyRepository
from pathlib import Path
from test_runtime_integration import complete_input  # shared physical/factor fixture


@pytest.fixture
def storage(tmp_path):
    source = JsonPropertyRepository(Path('backend/data/demo_properties.json'))
    return EditableRepository(source, tmp_path / 'recommendations.db')


@pytest.fixture
def client(storage):
    app.dependency_overrides[get_repository] = lambda: storage
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.pop(get_repository, None)


def test_default_percentage_ranking_and_stored_route_order(client, complete_input, storage):
    posted = client.post('/retrofits/recommend', json=complete_input)
    assert posted.status_code == 200
    result = posted.json()
    assert result['objective'] == 'energy_reduction'
    options = result['recommendations']
    assert [row['retrofit'] for row in options] == ['heat_pump', 'loft_insulation', 'double_glazing', 'smart_thermostat', 'solar_panels']
    percentages = [row['scenario']['energy']['improvement_percentage'] for row in options]
    assert percentages == sorted(percentages, reverse=True)
    assert [row['priority'] for row in options] == [1, 2, 3, 4, 5]
    assert options[0]['scenario']['energy']['electricity_savings_kwh'] == -2000
    assert options[0]['scenario']['energy']['gas_savings_kwh'] == 10000
    assert options[0]['suitability'] == 'Medium'  # rank alone cannot establish High
    assert result['installation_order'].index('loft_insulation') < result['installation_order'].index('heat_pump')
    path = f"/properties/INTEGRATION1/recommendations?scenario_id={result['scenario_id']}"
    assert client.get(path).json() == result
    assert client.get('/properties/INTEGRATION1/recommendations').json() == result
    restarted = EditableRepository(storage.source, storage.database_path)
    assert restarted.load_recommendations('INTEGRATION1', result['scenario_id']).model_dump(mode='json') == result


def test_conditional_incompatible_existing_and_missing_inputs_stay_unranked(client, complete_input):
    complete_input['property'].update(heat_pump_compatible=False, roof_suitable_for_loft=None, solar_installed=True)
    complete_input['property']['physical_inputs']['space_heating_demand_kwh'] = None
    complete_input['property']['physical_inputs']['thermal_demand_kwh'] = None
    result = client.post('/retrofits/recommend', json=complete_input).json()
    assert result['recommendations'] == []
    other = {row['retrofit']: row for row in result['other_options']}
    assert other['heat_pump']['feasibility']['status'] == 'infeasible'
    assert other['loft_insulation']['feasibility']['status'] == 'conditional'
    assert other['solar_panels']['feasibility']['status'] == 'infeasible'
    assert other['double_glazing']['scenario']['energy'] is None
    assert other['double_glazing']['scenario']['reason']
    assert all(row['priority'] is None for row in other.values())


def test_carbon_unavailable_does_not_imply_zero_benefit(client, complete_input, monkeypatch):
    monkeypatch.setenv('GREENPRINT_EMISSION_FACTORS_FILE', '')
    complete_input.update(emission_factors=None, objective='carbon_reduction')
    result = client.post('/retrofits/recommend', json=complete_input).json()
    assert result['recommendations'] == []
    assert all(row['scenario']['carbon']['reduction_kg_co2e'] is None for row in result['other_options'])
    assert all(row['suitability'] == 'Medium' for row in result['other_options'])
    complete_input['objective'] = 'energy_reduction'
    assert len(client.post('/retrofits/recommend', json=complete_input).json()['recommendations']) == 5


def test_zero_baseline_percentage_is_unavailable(client, complete_input):
    complete_input['annual_energy'].update(electricity_kwh=0, gas_kwh=0)
    physical = complete_input['property']['physical_inputs']
    physical.update(space_heating_demand_kwh=0, thermal_demand_kwh=0)
    result = client.post('/retrofits/recommend', json=complete_input).json()
    assert result['recommendations'] == []
    assert all(row['scenario']['energy']['improvement_percentage'] is None for row in result['other_options'])


def test_revision_identity_and_property_isolation(client, complete_input, storage):
    complete_input['scenario_id'] = 'planner-session'
    first = client.post('/retrofits/recommend', json=complete_input).json()
    complete_input['property']['controls_compatible'] = False
    second = client.post('/retrofits/recommend', json=complete_input).json()
    assert (first['revision'], second['revision']) == (1, 2)
    assert first['scenario_id'] == second['scenario_id']
    assert 'smart_thermostat' in [row['retrofit'] for row in first['recommendations']]
    assert 'smart_thermostat' not in [row['retrofit'] for row in second['recommendations']]
    assert client.get('/properties/OTHER/recommendations?scenario_id=planner-session').status_code == 404
    complete_input['property']['property_id'] = 'OTHER'
    third = client.post('/retrofits/recommend', json=complete_input).json()
    assert third['revision'] == 1
    assert client.get('/properties/INTEGRATION1/recommendations?scenario_id=planner-session').json() == second
    with sqlite3.connect(storage.database_path) as connection:
        assert connection.execute('SELECT COUNT(*) FROM recommendation_snapshots').fetchone()[0] == 2


def test_identical_inputs_upsert_and_changed_inputs_create_new_context(client, complete_input):
    first = client.post('/retrofits/recommend', json=complete_input).json()
    second = client.post('/retrofits/recommend', json=complete_input).json()
    assert second['scenario_id'] == first['scenario_id']
    assert second['revision'] == 2
    complete_input['objective'] = 'carbon_reduction'
    third = client.post('/retrofits/recommend', json=complete_input).json()
    assert third['scenario_id'] != first['scenario_id']
    assert third['revision'] == 1


def test_package_interactions_are_recalculated_not_added(client, complete_input):
    ranked = client.post('/retrofits/recommend', json=complete_input).json()
    options = {row['retrofit']: row for row in ranked['recommendations']}
    individual = sum(options[m]['scenario']['energy']['net_savings_kwh'] for m in ['loft_insulation', 'heat_pump'])
    package = client.post('/scenarios/simulate', json={**complete_input, 'retrofits': ['heat_pump', 'loft_insulation']}).json()
    assert package['energy']['after']['electricity_kwh'] == 6500
    assert package['energy']['after']['gas_kwh'] == 2000
    assert package['energy']['net_savings_kwh'] == 8300
    assert package['energy']['net_savings_kwh'] != individual


def test_budget_without_documented_costs_never_establishes_affordability(client, complete_input):
    result = client.post('/retrofits/recommend', json={**complete_input, 'budget_gbp': 1000}).json()
    assert result['recommendations'] == []
    assert all('cost' in row['scenario']['reason'].lower() for row in result['other_options'])


def test_optimizer_default_contract_is_preserved(client, complete_input):
    result = client.post('/retrofits/optimize', json=complete_input).json()
    assert result['objective'] == 'carbon_reduction'


def test_negative_carbon_benefit_is_preserved_but_not_recommended(client, complete_input):
    complete_input['objective'] = 'carbon_reduction'
    complete_input['emission_factors']['electricity']['kg_co2e_per_kwh'] = .99
    complete_input['emission_factors']['gas']['kg_co2e_per_kwh'] = .01
    result = client.post('/retrofits/recommend', json=complete_input).json()
    assert 'heat_pump' not in [row['retrofit'] for row in result['recommendations']]
    heat = next(row for row in result['other_options'] if row['retrofit'] == 'heat_pump')
    assert heat['scenario']['carbon']['reduction_kg_co2e'] == -1880
    assert heat['priority'] is None
    assert heat['suitability'] == 'Low'
    assert 'No positive' in heat['ranking_reason']
    reductions = [row['scenario']['carbon']['reduction_kg_co2e'] for row in result['recommendations']]
    assert reductions == sorted(reductions, reverse=True)
