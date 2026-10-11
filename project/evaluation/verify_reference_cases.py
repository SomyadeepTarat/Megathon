"""Hand-calculated synthetic arithmetic references, not measured retrofit accuracy.

Expected fuel totals are fixed independently of calls to the production engine.
Both calculations share the PRD's assumptions: agreement verifies implementation,
not the physical validity of those assumptions.
"""
import copy
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'backend'))
from fastapi.testclient import TestClient
from app.main import app

CASES = [
    ('unchanged', [], 2000, 12000),
    ('loft', ['loft_insulation'], 2000, 10500),
    ('glazing', ['double_glazing'], 2000, 11000),
    ('controls', ['smart_thermostat'], 2000, 11250),
    ('solar', ['solar_panels'], 1500, 12000),
    ('heat_pump', ['heat_pump'], 4640, 0),
    ('loft_controls', ['loft_insulation', 'smart_thermostat'], 2000, 9862.5),
    ('solar_heat_pump', ['solar_panels', 'heat_pump'], 4140, 0),
    ('all_five', ['loft_insulation', 'double_glazing', 'smart_thermostat', 'heat_pump', 'solar_panels'], 3555.25, 0),
]


def payload():
    record = json.loads((ROOT / 'backend/data/curated_demo_properties.json').read_text())[0]
    for field in ('dataset_kind', 'dataset_source'):
        record.pop(field)
    record['property'].update(heating_system='modern_gas_boiler', insulation='poor', glazing='single',
        solar_installed=False, heat_pump_installed=False, loft_insulation_installed=False,
        smart_thermostat_installed=False, smart_controls='none', renewable_contribution='none')
    record['property']['physical_inputs'] = {
        'space_heating_demand_kwh': 8000, 'hot_water_demand_kwh': 1600,
        'base_appliance_electricity_kwh': 2000, 'boiler_efficiency': .8,
        'scop': 4, 'hot_water_cop': 2.5, 'proposed_heat_pump_type': 'air_source_heat_pump',
        'proposed_solar_generation_kwh': 1000, 'proposed_solar_self_consumed_kwh': 500,
        'provenance': {'reference': 'Explicit synthetic analytical inputs; not measurements'}}
    record['annual_energy'].update(electricity_kwh=2000, gas_kwh=12000, quality='synthetic',
        method='Analytical reference: 2000 appliance electricity; (8000 space + 1600 water)/0.8 gas')
    return record


def run():
    rows = []
    base = payload()
    with TestClient(app) as client:
        for name, measures, expected_e, expected_g in CASES:
            response = client.post('/scenarios/simulate', json={**base, 'retrofits': measures})
            assert response.status_code == 200, response.text
            result = response.json()
            actual = result['energy']['after']
            for fuel, expected in [('electricity_kwh', expected_e), ('gas_kwh', expected_g)]:
                assert math.isclose(actual[fuel], expected, abs_tol=1e-8), (name, fuel, actual, expected)
            rows.append({'case_id': name, 'retrofits': measures,
                'expected_after': {'electricity_kwh': expected_e, 'gas_kwh': expected_g}, 'actual_after': actual})
        zero = copy.deepcopy(base)
        zero['annual_energy'].update(electricity_kwh=0, gas_kwh=0)
        zero['property']['physical_inputs'].update(space_heating_demand_kwh=0, hot_water_demand_kwh=0, base_appliance_electricity_kwh=0)
        result = client.post('/scenarios/simulate', json={**zero, 'retrofits': []}).json()
        assert result['energy']['improvement_percentage'] is None
        rows.append({'case_id': 'zero_baseline', 'result': result['energy']})
        missing = copy.deepcopy(base)
        missing['annual_energy'].update(gas_kwh=None, gas_months_covered=0)
        response = client.post('/scenarios/simulate', json={**missing, 'retrofits': ['heat_pump']})
        assert response.status_code == 503 and response.json()['energy'] is None, response.text
        rows.append({'case_id': 'missing_fuel', 'status': response.status_code, 'reason': response.json()['reason']})
        unsuitable = copy.deepcopy(base)
        unsuitable['property']['heat_pump_compatible'] = False
        response = client.post('/scenarios/simulate', json={**unsuitable, 'retrofits': ['heat_pump']})
        assert response.status_code == 409 and response.json()['energy'] is None, response.text
        rows.append({'case_id': 'infeasible_heat_pump', 'status': response.status_code, 'reason': response.json()['reason']})
    report = {'status': 'passed', 'cases': rows,
        'reference_basis': 'Fixed hand-calculated synthetic examples: gas=(space+water)/0.8; heat-pump electricity=space/4+water/2.5+2000; solar subtracts 500; sequential space reductions .85, .90, .925.',
        'per_fuel_mae_kwh': {fuel: sum(abs(r['actual_after'][fuel] - r['expected_after'][fuel]) for r in rows[:9]) / 9
                             for fuel in ('electricity_kwh', 'gas_kwh')},
        'limitations': 'Implementation agreement under shared assumptions; not independent real-world predictive validation.'}
    output = ROOT / 'evaluation/results/current_pipeline/reference_verification.json'
    output.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'status': report['status'], 'cases': len(rows), 'per_fuel_mae_kwh': report['per_fuel_mae_kwh'], 'limitations': report['limitations']}, indent=2))
    return report


if __name__ == '__main__':
    run()
