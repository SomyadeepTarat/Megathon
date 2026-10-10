import json
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from app.main import app, repository


@pytest.fixture
def client():
    saved = dict(repository.overrides)
    with TestClient(app) as value:
        yield value
    repository.overrides = saved


@pytest.fixture
def complete_input():
    value = json.loads((Path(__file__).resolve().parents[2] / 'docs/assessment-example.json').read_text())
    value['property'].update(property_id='INTEGRATION1', solar_installed=False, heat_pump_installed=False,
        heat_pump_compatible=True, controls_compatible=True, roof_suitable_for_solar=True,
        roof_suitable_for_loft=True, loft_insulation_installed=False,
        physical_inputs={'thermal_demand_kwh': 8000, 'thermal_demand_scope': 'space_heating',
                         'space_heating_demand_kwh': 8000, 'hot_water_demand_kwh': 0,
                         'boiler_efficiency': .8, 'scop': 4,
                         'proposed_heat_pump_type': 'air_source_heat_pump',
                         'proposed_solar_generation_kwh': 1000, 'proposed_solar_self_consumed_kwh': 500,
                         'provenance': {'thermal_demand_kwh': 'TEST ONLY', 'boiler_efficiency': 'TEST ONLY',
                                        'scop': 'TEST ONLY', 'proposed_heat_pump_type': 'TEST ONLY',
                                        'proposed_solar_generation_kwh': 'TEST ONLY', 'proposed_solar_self_consumed_kwh': 'TEST ONLY'}})
    value['emission_factors'] = {fuel: {'fuel': fuel, 'kg_co2e_per_kwh': factor,
        'source': 'TEST FIXTURE ONLY', 'source_year': 2026, 'accounting_boundary': 'test boundary',
        'version': 'test-only-v1'} for fuel, factor in [('electricity', .2), ('gas', .18)]}
    return value


def test_real_p4_route_returns_signed_fuels_and_partial_results(client, complete_input):
    complete_input['retrofits'] = ['heat_pump']
    response = client.post('/scenarios/simulate', json=complete_input)
    assert response.status_code == 200
    result = response.json()
    assert result['status'] == 'partial'
    assert result['energy']['electricity_savings_kwh'] == -2000
    assert result['energy']['gas_savings_kwh'] == 10000
    assert result['carbon']['reduction_kg_co2e'] == 1400
    assert result['carbon_savings_by_fuel_kg_co2e'] == {'electricity': -400, 'gas': 1800}
    assert result['updated_property']['heat_pump_installed'] is True
    assert result['updated_property']['heating_system'] == 'air_source_heat_pump'
    assert result['updated_property']['energy_rating'] == 'E'
    assert result['baseline_carbon']['total_kg_co2e'] == 3120
    assert result['after_carbon']['total_kg_co2e'] == 1720
    assert result['after_carbon']['electricity_kg_co2e'] == 1360
    assert result['after_carbon']['gas_kg_co2e'] == 360
    assert result['installation_cost_gbp'] is None
    assert result['valuation']['status'] == 'unavailable'
    assert 'EPC' in result['valuation']['reason']


def test_registered_snapshot_drives_real_advisor(client, complete_input):
    response = client.post('/properties', json=complete_input)
    assert response.status_code == 201
    chat = client.post('/advisor/chat', json={'property_id': 'INTEGRATION1', 'message': 'Install heat pump'})
    assert chat.status_code == 200
    result = chat.json()
    assert result['status'] == 'partial'
    assert result['tool_calls'] == ['feasibility', 'simulate']
    assert '-2000.0 kWh/year' in result['explanation']
    assert result['result']['carbon']['reduction_kg_co2e'] == 1400
    assert result['result']['valuation']['status'] == 'unavailable'


@pytest.mark.parametrize('measure,field', [('heat_pump', 'heat_pump_compatible'), ('smart_thermostat', 'controls_compatible')])
def test_real_adapter_blocks_incompatibility(client, complete_input, measure, field):
    complete_input['property'][field] = False
    complete_input['retrofits'] = [measure]
    result = client.post('/scenarios/simulate', json=complete_input)
    assert result.status_code == 409
    assert result.json()['feasibility']['items'][0]['status'] == 'infeasible'
    assert result.json()['energy'] is None


def test_solar_self_consumption_is_capped_to_generation_and_demand(client, complete_input):
    complete_input['property']['physical_inputs']['proposed_solar_generation_kwh'] = 10
    complete_input['property']['physical_inputs']['proposed_solar_self_consumed_kwh'] = 100
    complete_input['retrofits'] = ['solar_panels']
    result = client.post('/scenarios/simulate', json=complete_input)
    assert result.status_code == 200
    assert result.json()['energy']['after']['electricity_kwh'] == 4790
    assert any('capped' in warning for warning in result.json()['warnings'])


def test_existing_solar_is_not_recommended(client, complete_input):
    complete_input['property']['solar_installed'] = True
    complete_input['retrofits'] = ['solar_panels']
    assert client.post('/scenarios/simulate', json=complete_input).status_code == 409
    assert client.get('/properties/P00003').json()['property']['solar_installed'] is True


def test_smart_thermostat_state_does_not_invent_controls_category(client, complete_input):
    complete_input['retrofits'] = ['smart_thermostat']
    result = client.post('/scenarios/simulate', json=complete_input)
    assert result.status_code == 200
    updated = result.json()['updated_property']
    assert updated['smart_thermostat_installed'] is True
    assert updated['smart_controls'] == 'none'


def test_missing_factors_and_missing_physics_are_explicit(client, complete_input, monkeypatch):
    monkeypatch.delenv('GREENPRINT_EMISSION_FACTORS_FILE', raising=False)
    complete_input['retrofits'] = ['heat_pump']
    factors = complete_input.pop('emission_factors')
    response = client.post('/scenarios/simulate', json=complete_input)
    assert response.status_code == 200
    assert response.json()['energy'] is not None
    assert response.json()['carbon']['status'] == 'unavailable'
    assert 'factors' in response.json()['carbon']['reason']
    complete_input['emission_factors'] = factors
    complete_input['property']['physical_inputs'] = {}
    response = client.post('/scenarios/simulate', json=complete_input)
    assert response.status_code == 503
    assert 'heating demand' in response.json()['reason'].lower()


def test_cost_and_budget_validation(client, complete_input):
    complete_input.update(retrofits=['heat_pump'], budget_gbp=5000)
    response = client.post('/scenarios/simulate', json=complete_input)
    assert response.status_code == 503
    assert 'costs' in response.json()['reason']
    complete_input['retrofit_costs'] = {'heat_pump': {'amount_gbp': 7000, 'source': 'TEST ONLY', 'date': '2026-10-10'}}
    assert client.post('/scenarios/simulate', json=complete_input).status_code == 409
    complete_input['budget_gbp'] = 8000
    result = client.post('/scenarios/simulate', json=complete_input)
    assert result.status_code == 200
    assert result.json()['installation_cost_gbp'] == 7000
    complete_input['electricity_tariff_gbp_per_kwh'] = .2
    complete_input['gas_tariff_gbp_per_kwh'] = .1
    result = client.post('/scenarios/simulate', json=complete_input)
    assert result.status_code == 200
    assert result.json()['annual_bill_savings_gbp'] == 600
    assert result.json()['simple_payback_years'] == pytest.approx(7000 / 600)


def test_real_recommendation_and_valuation_routes(client, complete_input):
    complete_input['retrofits'] = []
    result = client.post('/retrofits/recommend', json=complete_input)
    assert result.status_code == 200
    assert any(row['retrofit'] == 'heat_pump' for row in result.json()['recommendations'])
    assert all(row['feasibility']['status'] == 'feasible' for row in result.json()['recommendations'])
    result = client.post('/properties/P00001/valuation/impact', json={})
    assert result.status_code == 200
    assert result.json()['status'] == 'unavailable'
    assert client.post('/properties/MISSING/valuation/impact', json={}).status_code == 404


def test_http_routes_have_no_duplicate_method_paths():
    from app.main import app
    routes = [(method, route.path) for route in app.routes
              for method in getattr(route, 'methods', [])]
    assert len(routes) == len(set(routes))


def test_health_reports_dependency_requirements(client):
    result = client.get('/health').json()
    assert result['readiness']['retrofit_engine']['connected'] is True
    assert result['readiness']['advisor']['mounted'] is True
    assert result['readiness']['budget_optimizer']['ready'] is True


def test_full_baseline_route(client, complete_input):
    response = client.post('/assessments/full', json=complete_input)
    assert response.status_code == 200
    assert response.json()['baseline_carbon']['total_kg_co2e'] == 3120
    assert response.json()['assessment']['score']['status'] == 'unavailable'
    assert response.json()['valuation']['status'] == 'unavailable'


def test_observed_csv_provenance_is_supported(tmp_path):
    import csv
    from app.db.repository import CsvPropertyRepository
    root = Path(__file__).resolve().parents[2]
    with (root / 'Data/csv/properties.csv').open() as stream:
        rows = list(csv.DictReader(stream))[:1]
    rows[0]['data_status'] = 'observed'
    prop_path = tmp_path / 'properties.csv'
    with prop_path.open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    with (root / 'Data/csv/energy_usage.csv').open() as stream:
        readings = [row for row in csv.DictReader(stream) if row['property_id'] == rows[0]['property_id']]
    for reading in readings:
        reading['reading_status'] = 'observed'
    energy_path = tmp_path / 'energy.csv'
    with energy_path.open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(readings[0]))
        writer.writeheader()
        writer.writerows(readings)
    record = CsvPropertyRepository(prop_path, energy_path).list_properties()[0]
    assert record.dataset_kind == 'observed'
    assert record.annual_energy.quality == 'observed'
    assert record.property.provenance['record'] == 'observed'


def test_unknown_glazing_is_conditional(client, complete_input):
    complete_input['property']['glazing'] = None
    complete_input['retrofits'] = ['double_glazing']
    response = client.post('/scenarios/simulate', json=complete_input)
    assert response.status_code == 409
    assert response.json()['feasibility']['items'][0]['status'] == 'conditional'


def test_property_route_preserves_dataset_physics_and_nulls(client):
    result = client.get('/properties/P00001')
    assert result.status_code == 200
    physical = result.json()['property']['physical_inputs']
    assert physical['space_heating_demand_kwh'] > 0
    assert physical['hot_water_demand_kwh'] > 0
    assert physical['boiler_efficiency'] == .72
    assert physical['scop'] is None
    assert result.json()['property']['heat_pump_compatible'] is None


def test_package_optimizer_enumerates_packages_and_respects_budget(client, complete_input):
    names = ['loft_insulation', 'heat_pump', 'solar_panels', 'double_glazing', 'smart_thermostat']
    costs = {measure: {'amount_gbp': 1000, 'source': 'TEST ONLY', 'date': '2026-10-10'} for measure in names}
    complete_input.update(retrofits=[], objective='energy_reduction', budget_gbp=2000, retrofit_costs=costs)
    response = client.post('/retrofits/optimize', json=complete_input)
    assert response.status_code == 200
    body = response.json()
    assert body['status'] == 'available'
    assert len(body['package_decisions']) == 32
    assert any(row['status'] == 'rejected' and row['cost_gbp'] > 2000 for row in body['package_decisions'])
    assert body['ranked_packages'][0]['after']['gas_kwh'] >= 0


def test_package_optimizer_does_not_treat_missing_cost_as_zero(client, complete_input):
    complete_input.update(retrofits=[], objective='energy_reduction', budget_gbp=5000,
                          retrofit_costs={'heat_pump': {'amount_gbp': 1000, 'source': 'TEST ONLY', 'date': '2026-10-10'}})
    response = client.post('/retrofits/optimize', json=complete_input)
    assert response.status_code == 200
    decisions = response.json()['package_decisions']
    assert any(row['status'] == 'unavailable' and 'Documented installation cost missing' in row['reason']
               for row in decisions)
