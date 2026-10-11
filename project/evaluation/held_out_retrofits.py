"""Seeded held-out properties vs a separately coded PRD arithmetic/rule oracle.

Never imports the production energy engine for reference labels. Both share
assumptions; this is broad implementation agreement, not measured accuracy.
"""
import argparse
import copy
import itertools
import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np
from fastapi.testclient import TestClient
from evaluation.evaluate_energy import evaluate as energy_metrics
from evaluation.evaluate_recommendations import evaluate as feasibility_metrics

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'backend'))
from app.main import app

MEASURES = ('loft_insulation', 'heat_pump', 'solar_panels', 'double_glazing', 'smart_thermostat')
LABEL_SOURCE = 'prd.md sections 8–9; independent closed-form oracle in evaluation.held_out_retrofits'
METHOD = 'Sequential space multipliers .85*.90*.925; water unchanged; per-system thermal conversion; preserved appliance/nonheating gas; bounded PV imports; explicit installation/compatibility rules.'


def generate_cases(n=24, seed=917):
    rng = np.random.default_rng(seed)
    base = json.loads((ROOT/'backend/data/curated_demo_properties.json').read_text())[0]
    for i in range(n):
        row = copy.deepcopy(base)
        row.pop('dataset_kind'); row.pop('dataset_source')
        prop = row['property']
        system = ('old_gas_boiler', 'modern_gas_boiler', 'air_source_heat_pump', 'electric_resistance')[i % 4]
        space, water = rng.uniform(2000, 22000), rng.uniform(0, 3000)
        eta, scop, water_cop = rng.uniform(.65, .95), rng.uniform(2, 4.5), rng.uniform(2, 3)
        appliances, other_gas = rng.uniform(500, 4500), rng.uniform(0, 500)
        existing_pv = i % 6 == 0
        generation, consumption = (1500, 400) if existing_pv else (0, 0)
        physical = {'space_heating_demand_kwh': space, 'hot_water_demand_kwh': water,
            'boiler_efficiency': eta, 'scop': scop, 'hot_water_cop': water_cop,
            'electric_resistance_efficiency': 1, 'base_appliance_electricity_kwh': appliances,
            'solar_generation_kwh': generation, 'solar_self_consumed_kwh': consumption,
            'proposed_solar_generation_kwh': 2000, 'proposed_solar_self_consumed_kwh': 800,
            'proposed_heat_pump_type': 'air_source_heat_pump',
            'provenance': {'status': 'synthetic', 'source': LABEL_SOURCE}}
        electric_heat = space/scop + water/water_cop if system == 'air_source_heat_pump' else space+water if system == 'electric_resistance' else 0
        gas_heat = (space+water)/eta if system.endswith('gas_boiler') else 0
        prop.update(property_id=f'HELDOUT-{seed}-{i:03}',
            property_type=('detached', 'semi_detached', 'flat', 'terraced', 'bungalow')[i % 5],
            region=('Greater London', 'South East', 'North West')[i % 3],
            floor_area_m2=float(rng.uniform(50, 220)), physical_inputs=physical,
            heating_system=system, heat_pump_installed=system == 'air_source_heat_pump',
            insulation='good' if i % 7 == 0 else 'poor', glazing='double' if i % 5 == 0 else 'single',
            smart_controls='advanced' if i % 8 == 0 else 'none',
            smart_thermostat_installed=i % 8 == 0, loft_insulation_installed=False,
            solar_installed=existing_pv, renewable_contribution='limited' if existing_pv else 'none',
            roof_suitable_for_loft=(True, None, False)[i % 3],
            roof_suitable_for_solar=(True, False, None)[i % 3],
            heat_pump_compatible=(True, None, False)[(i//3) % 3],
            controls_compatible=(True, False, None)[(i//3) % 3])
        prop['provenance'] = {'record': 'synthetic', 'source': LABEL_SOURCE,
                              'customer_id': f'HELDOUT-C-{seed}-{i:03}'}
        row['benchmark'] = None
        physical['annual_electricity_demand_kwh'] = appliances + electric_heat
        row['annual_energy'].update(electricity_kwh=appliances+electric_heat-consumption,
            gas_kwh=gas_heat+other_gas, quality='synthetic', method='Independent synthetic held-out thermal-component generator')
        # Holdout quotes/tariffs are assumptions, not external market prices.
        row['retrofit_costs'] = {m: {'amount_gbp': c, 'source': 'Synthetic held-out quote', 'date': '2026-10-11'}
            for m, c in zip(MEASURES, [1800, 8500, 4500, 7000, 300])}
        row.update(electricity_tariff_gbp_per_kwh=.25, gas_tariff_gbp_per_kwh=.065)
        yield row


def feasibility_reference(prop, measure):
    present = {'loft_insulation': prop['loft_insulation_installed'] or prop['insulation'] == 'good',
        'heat_pump': prop['heat_pump_installed'], 'solar_panels': prop['solar_installed'],
        'double_glazing': prop['glazing'] in ('double', 'triple'),
        'smart_thermostat': prop['smart_controls'] == 'advanced'}[measure]
    if present:
        return 'infeasible'
    field = {'loft_insulation': 'roof_suitable_for_loft', 'heat_pump': 'heat_pump_compatible',
             'solar_panels': 'roof_suitable_for_solar', 'smart_thermostat': 'controls_compatible'}.get(measure)
    if field and prop[field] is not True:
        return 'infeasible' if prop[field] is False else 'conditional'
    return 'feasible'


def reference(row, measures):
    prop, energy = row['property'], row['annual_energy']
    phys, system = prop['physical_inputs'], prop['heating_system']
    space, water = phys['space_heating_demand_kwh'], phys['hot_water_demand_kwh']
    after_space = space * np.prod([fraction for m, fraction in
        [('loft_insulation', .85), ('double_glazing', .90), ('smart_thermostat', .925)] if m in measures])
    gas_system = system.endswith('gas_boiler')
    old_e_heat = (space/phys['scop'] + water/phys['hot_water_cop'] if system == 'air_source_heat_pump' else
                  space+water if system == 'electric_resistance' else 0)
    old_g_heat = (space+water)/phys['boiler_efficiency'] if gas_system else 0
    new_pump = 'heat_pump' in measures or system == 'air_source_heat_pump'
    e_heat = after_space/phys['scop'] + water/phys['hot_water_cop'] if new_pump else after_space+water if system == 'electric_resistance' else 0
    g_heat = (after_space+water)/phys['boiler_efficiency'] if gas_system and not new_pump else 0
    demand = energy['electricity_kwh'] + phys['solar_self_consumed_kwh'] - old_e_heat + e_heat
    solar = min(demand, 800) if 'solar_panels' in measures else min(demand, phys['solar_self_consumed_kwh'])
    e, g = max(0, demand-solar), energy['gas_kwh']-old_g_heat+g_heat
    e_save, g_save = energy['electricity_kwh']-e, energy['gas_kwh']-g
    cost = sum(row['retrofit_costs'][m]['amount_gbp'] for m in measures)
    bill = e_save*.25 + g_save*.065
    return {'electricity_kwh': e, 'gas_kwh': g, 'net': e_save+g_save,
        'carbon': e_save*.13096 + g_save*.18231, 'cost': cost, 'bill': bill,
        'payback': cost/bill if bill > 0 else None}


def run(output=ROOT/'evaluation/results/held_out_retrofits'):
    output = Path(output); output.mkdir(parents=True, exist_ok=True)
    rows = list(generate_cases())
    energies, feasibilities, rankings, optimizations = [], [], [], []
    map_labels = {'feasible': 'eligible', 'infeasible': 'rejected', 'conditional': 'conditional'}
    with TestClient(app) as client:
        for row in rows:
            prop = row['property']; identifier = prop['property_id']
            states = {m: feasibility_reference(prop, m) for m in MEASURES}
            expected_packages = []
            for count in range(6):
                for package in itertools.combinations(MEASURES, count):
                    response = client.post('/scenarios/simulate', json={**row, 'retrofits': list(package)})
                    result = response.json()
                    if any(states[m] != 'feasible' for m in package):
                        assert response.status_code == 409 and result['energy'] is None, result
                        continue
                    assert response.status_code == 200 and result['energy'] is not None, result
                    expected = reference(row, package)
                    actual = result['energy']['after']
                    energies.append({'case_id': identifier+':'+','.join(package), 'reference_kind': 'documented_rule',
                        'reference_source': LABEL_SOURCE, 'label_methodology': METHOD,
                        'expected_after': {f: expected[f] for f in ('electricity_kwh', 'gas_kwh')},
                        'predicted_after': actual, 'expected_carbon': expected['carbon'],
                        'predicted_carbon': result['carbon']['reduction_kg_co2e']})
                    expected_packages.append((list(package), expected))
            for objective, field in [('carbon_reduction', 'carbon'), ('energy_reduction', 'net'), ('shortest_payback', 'payback')]:
                response = client.post('/retrofits/recommend', json={**row, 'objective': objective, 'budget_gbp': 15000})
                assert response.status_code == 200, response.text
                result = response.json()
                if objective == 'carbon_reduction':
                    for item in result['recommendations']+result['other_options']:
                        feasibilities.append({'property_id': identifier, 'retrofit': item['retrofit'],
                            'expected': map_labels[states[item['retrofit']]], 'predicted': map_labels[item['feasibility']['status']],
                            'reference_kind': 'documented_rule', 'reference': LABEL_SOURCE, 'label_methodology': METHOD})
                individual = [(p, ref) for p, ref in expected_packages if len(p) == 1 and ref[field] is not None]
                individual.sort(key=lambda pair: (pair[1][field] if field == 'payback' else -pair[1][field], pair[0][0]))
                expected_order = [p[0] for p, _ in individual]
                actual_order = [item['retrofit'] for item in result['recommendations']]
                rankings.append({'property_id': identifier, 'objective': objective,
                    'expected': expected_order, 'predicted': actual_order, 'exact_match': expected_order == actual_order})
                expected = [(p, ref) for p, ref in expected_packages if ref['cost'] <= 15000 and ref[field] is not None]
                expected.sort(key=lambda pair: (pair[1][field] if field == 'payback' else -pair[1][field], pair[1]['cost'], pair[0]))
                response = client.post('/retrofits/optimize', json={**row, 'objective': objective, 'budget_gbp': 15000})
                assert response.status_code == 200, response.text
                actual = response.json()['best_scenario']
                want = expected[0][0] if expected else None
                got = actual['applied_retrofits'] if actual else None
                optimizations.append({'property_id': identifier, 'objective': objective,
                    'expected': want, 'predicted': got, 'exact_match': want == got})
    report = {'scope': 'held-out synthetic property agreement against separately implemented documented rules',
        'seed': 917, 'properties': len(rows), 'energy': energy_metrics(energies),
        'carbon_mae_kg_co2e': float(np.mean([abs(r['expected_carbon']-r['predicted_carbon']) for r in energies])),
        'feasibility': feasibility_metrics(feasibilities),
        'ranking_cases': len(rankings), 'ranking_exact_match_fraction': float(np.mean([r['exact_match'] for r in rankings])),
        'ranking_nonempty_cases': sum(bool(r['expected']) for r in rankings),
        'fixed_catalogue_order_exact_match_fraction': float(np.mean([
            sorted(r['expected'], key=MEASURES.index) == r['expected'] for r in rankings])),
        'feasibility_majority_baseline_accuracy': max(Counter(r['expected'] for r in feasibilities).values()) / len(feasibilities),
        'optimizer_cases': len(optimizations), 'optimizer_exact_match_fraction': float(np.mean([r['exact_match'] for r in optimizations])),
        'coverage': ['five property types', 'three regions', 'gas/heat-pump/resistance heating', 'existing PV',
            'already-installed measures', 'unknown/false eligibility', 'all 32 packages', 'three objectives', 'signed fuel changes'],
        'limitations': ['Shared PRD assumptions; zero numerical error is implementation agreement, not measured savings accuracy.',
                       'These properties are never used to fit or calibrate valuation models.',
                       'Human explanation quality and observed-market validity are separate evidence.']}
    for name, content in [('cases', rows), ('energy_predictions', energies), ('feasibility_predictions', feasibilities),
                          ('ranking_predictions', rankings), ('optimizer_predictions', optimizations), ('metrics', report)]:
        (output/f'{name}.json').write_text(json.dumps(content, indent=2)+'\n')
    numerical_ok = all(report['energy']['per_fuel'][f]['mae_kwh'] < 1e-7 for f in ('electricity_kwh', 'gas_kwh'))
    assert numerical_ok and report['carbon_mae_kg_co2e'] < 1e-7, report
    assert all(r['expected'] == r['predicted'] for r in feasibilities), report
    assert report['ranking_exact_match_fraction'] == report['optimizer_exact_match_fraction'] == 1, report
    print(json.dumps(report, indent=2))
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('--output', type=Path, default=ROOT/'evaluation/results/held_out_retrofits')
    run(parser.parse_args().output)
