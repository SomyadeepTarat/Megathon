"""Public-reference London simulation with the existing CSV/ML contract."""
import argparse
import bisect
import hashlib
import json
import math
import random
import shutil
import sys
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean, median

from expand_dataset import ROOT, SCHEMA, audit, diagnostics, fixtures, physical_row, read_csv, sha, write_csv, write_json
from generate_energy_usage import annual_components, generate, validate

VERSION = 'kew_london_v3'
REFERENCE = ROOT / 'manifests/london_reference_v1.json'
SEED = 20261011
KINDS = ['Detached', 'Semi-detached', 'Terraced', 'Flat']
AREA_MEANS = {'Detached': 128, 'Semi-detached': 101, 'Terraced': 86, 'Flat': 63}


def rng_for(identifier, channel):
    return random.Random(int(hashlib.sha256(f'{SEED}:{channel}:{identifier}'.encode()).hexdigest(), 16))


def base_property(identifier, refs):
    rng = rng_for(identifier, 'physical')
    bands = refs['age_bands']
    low, high, _ = rng.choices(bands, weights=[b[2] for b in bands])[0]
    age = 2026 - rng.randint(low, high)
    counts = refs['housing_mix_counts']
    flat_share = counts['Flat'] / sum(counts.values())
    recent = low == 2003
    flat_prob = refs['post_2002_flat_share'] if recent else (flat_share - .12 * refs['post_2002_flat_share']) / .88
    kind = 'Flat' if rng.random() < flat_prob else rng.choices(KINDS[:3], weights=[counts[k] for k in KINDS[:3]])[0]
    # Conditional sizes and dispersion are disclosed assumptions, not EPC microdata.
    sigma = .30
    area = round(max(25, min(350, AREA_MEANS[kind] * math.exp(rng.gauss(-.5 * sigma**2, sigma)))), 1)
    bedrooms = rng.choices([1, 2], [.8, .2])[0] if area < 55 else rng.choices([2, 3], [.8, .2])[0] if area < 90 else rng.choices([3, 4], [.75, .25])[0] if area < 140 else rng.choices([4, 5, 6], [.65, .3, .05])[0]
    fabric = rng.choices(['Poor', 'Average', 'Good'], [.01, .04, .95] if age <= 26 else [.3, .5, .2] if age <= 81 else [.5, .35, .15])[0]
    glazing = rng.choices(['Single', 'Double', 'Triple'], [.005, .845, .15] if age <= 26 else [.08, .87, .05] if age < 60 else [.25, .72, .03])[0]
    electric = rng.random() < .06  # inherited assumption; not estimated from London EPC statistics
    heating = rng.choices(['Heat pump', 'Electric resistance'], [.4, .6])[0] if electric else rng.choices(['Old gas boiler', 'Modern gas boiler'], [.02, .98] if age <= 26 else [.2, .8] if age < 60 else [.45, .55])[0]
    solar = rng.random() < {'Detached': .18, 'Semi-detached': .12, 'Terraced': .08, 'Flat': .02}[kind]
    controls = rng.random() < (.85 if heating == 'Heat pump' else .5 if age <= 26 else .3)
    latent = 50 + {'Poor': -12, 'Average': 8, 'Good': 20}[fabric] + {'Single': -10, 'Double': 5, 'Triple': 10}[glazing] + {'Old gas boiler': -8, 'Modern gas boiler': 3, 'Heat pump': 12, 'Electric resistance': -5}[heating] + 8 * solar + 4 * controls + (5 if age <= 26 else 0) + rng.gauss(0, 5)
    row = dict(property_id=identifier, customer_id=identifier.replace('P', 'C', 1), property_type=kind,
               age=str(age), floor_area_m2=str(area), bedrooms=str(bedrooms), energy_rating='D',
               heating=heating, insulation=fabric, glazing=glazing, solar=str(solar).lower(),
               smart_controls=str(controls).lower(), region='Greater London', current_value_estimate_gbp='1',
               data_status='synthetic', generation_seed=str(SEED))
    # Separate RNG prevents changing fabric/EPC from changing price noise/location.
    pricing = rng_for(identifier, 'price')
    boroughs = sorted(b for b, values in refs['borough_type_prices_gbp'].items() if kind in values)
    borough = pricing.choice(boroughs)  # equal borough weights: explicitly not a stock distribution
    anchor = refs['borough_type_prices_gbp'][borough][kind]
    sigma_price = .18  # retain original residual dispersion, never shrink to improve MAE
    price = anchor * (area / AREA_MEANS[kind])**.55 * (1 + .02 * (bedrooms - 3)) * (1.04 if age <= 10 else 1) * math.exp(pricing.gauss(-.5 * sigma_price**2, sigma_price))
    return row, latent, price, borough


def scaled_readings(base, raw, heat_scale, appliance_scale):
    rows = []
    gas = 'gas boiler' in base['heating']
    pump = base['heating'] == 'Heat pump'
    boiler = .72 if base['heating'] == 'Old gas boiler' else .90
    for prior in raw:
        r = dict(prior)
        old_heat, water = float(r['space_heating_demand_kwh']), float(r['hot_water_demand_kwh'])
        old_electric_heat = 0 if gas else old_heat / (3 if pump else 1)
        electric_water = 0 if gas else water / (2.5 if pump else 1)
        appliance = float(r['electricity_demand_kwh']) - old_electric_heat - electric_water
        heat = old_heat * heat_scale
        demand = appliance * appliance_scale + (0 if gas else heat / (3 if pump else 1)) + electric_water
        generation = float(r['solar_generation_kwh'])
        own = min(demand, generation * .45)
        values = {'space_heating_demand_kwh': heat, 'electricity_demand_kwh': demand,
                  'solar_self_consumed_kwh': own, 'solar_export_kwh': generation - own}
        r.update({k: f'{v:.6f}' for k, v in values.items()})
        r.update(electricity_kwh=f'{demand-own:.2f}', gas_kwh=f'{(heat+water)/boiler if gas else 0:.2f}',
                 reading_source='simulate_london.py v3; London NEED-2024 anchored synthetic scenario, not observed')
        rows.append(r)
    return rows


def calibrate(refs, size=3000):
    """External-reference pilot; never read any development/calibration/test labels."""
    pilot = [base_property(f'PILOT{i:05d}', refs) for i in range(size)]
    grouped = defaultdict(list)
    for r in generate([p[0] for p in pilot]):
        grouped[r['property_id']].append(r)
    gas_homes = []
    for p, _, _, _ in pilot:
        if 'gas boiler' in p['heating']:
            readings = grouped[p['property_id']]
            gas_homes.append((sum(float(r['space_heating_demand_kwh']) for r in readings),
                              sum(float(r['hot_water_demand_kwh']) for r in readings),
                              .72 if p['heating'] == 'Old gas boiler' else .90))
    target = refs['need_london_2024']['gas']['median_kwh']
    lo, hi = .1, 5.0
    for _ in range(35):
        mid = (lo + hi) / 2
        if median((heat * mid + water) / eff for heat, water, eff in gas_homes) < target:
            lo = mid
        else:
            hi = mid
    heat_scale = (lo + hi) / 2
    target_e = refs['need_london_2024']['electricity']['median_kwh']
    # Precompute seasonal components, then solve only an intercept multiplier.
    electric = []
    for p, _, _, _ in pilot:
        gas = 'gas boiler' in p['heating']; pump = p['heating'] == 'Heat pump'
        months = []
        for r in grouped[p['property_id']]:
            heat, water = float(r['space_heating_demand_kwh']), float(r['hot_water_demand_kwh'])
            old_thermal = 0 if gas else heat / (3 if pump else 1) + water / (2.5 if pump else 1)
            thermal = 0 if gas else heat * heat_scale / (3 if pump else 1) + water / (2.5 if pump else 1)
            months.append((float(r['electricity_demand_kwh']) - old_thermal, thermal, .45 * float(r['solar_generation_kwh'])))
        electric.append(months)
    lo, hi = .1, 5.0
    for _ in range(35):
        mid = (lo + hi) / 2
        if median(sum(max(0, app * mid + thermal - pv) for app, thermal, pv in months) for months in electric) < target_e:
            lo = mid
        else:
            hi = mid
    rating_counts = refs['epc_existing_2025']['rating_counts']
    scores = sorted(p[1] for p in pilot)
    total = sum(rating_counts.values()); accumulated = 0; cutoffs = []
    for rating in 'GFEDCB':
        accumulated += rating_counts[rating]
        cutoffs.append(scores[min(size-1, round(size * accumulated / total))])
    return {'pilot_count': size, 'pilot_namespace': 'PILOT only; disjoint from all labelled evaluation rows',
            'heat_scale': heat_scale, 'appliance_scale': (lo + hi) / 2,
            'epc_score_cutoffs_ascending': cutoffs,
            'price_intercepts_by_type': {k: refs['london_type_prices_gbp'][k] / mean(p[2] for p in pilot if p[0]['property_type'] == k) for k in KINDS},
            'residual_log_price_sigma': .18, 'frozen_from': 'public aggregates + independently seeded pilot; no valuation error/holdout feedback'}


def assign(customer):
    bucket = int(hashlib.sha256(f'{VERSION}:reserve:{customer}'.encode()).hexdigest()[:16], 16) / 2**64
    return 'fit' if bucket < .4 else 'selection' if bucket < .6 else 'calibration' if bucket < .8 else 'test'


def simulate(original, original_energy, fields, total, refs, parameters):
    if total < len(original):
        raise ValueError('Total must retain original records')
    props, energy, metadata = list(original), list(original_energy), []
    templates = {p['property_type']: p for p in original}
    for i in range(total - len(original)):
        base, latent, price, borough = base_property(f'P{100001+i:06d}', refs)
        if any(p['property_id'] == base['property_id'] or p['customer_id'] == base['customer_id'] for p in original):
            raise ValueError('Fresh ID collides with source')
        base['energy_rating'] = 'GFEDCBA'[bisect.bisect_right(parameters['epc_score_cutoffs_ascending'], latent)]
        base['current_value_estimate_gbp'] = str(int(round(max(50000, price * parameters['price_intercepts_by_type'][base['property_type']]) / 1000) * 1000))
        readings = scaled_readings(base, generate([base]), parameters['heat_scale'], parameters['appliance_scale'])
        row = physical_row(base, templates[base['property_type']], readings, fields)
        row['physical_inputs_source'] = 'Data/scripts/simulate_london.py v3; public-reference simulation; Data/relations/london_simulation.md'
        reference = dict(base, floor_area_m2='100', age='54', bedrooms='3', insulation='Average',
                         glazing='Double', heating='Modern gas boiler', solar='false', smart_controls='false')
        ref_heat, ref_water, ref_appliance, _ = annual_components(reference, behavior=1)
        row['benchmark_intensity_kwh_m2_year'] = f'{((ref_heat * parameters["heat_scale"] + ref_water) / .9 + ref_appliance * parameters["appliance_scale"]) / 100:.6f}'
        row['benchmark_source'] = 'Synthetic London fixed reference v3; NEED-2024 anchored, not an official benchmark'
        row['benchmark_methodology'] = '100 m2, 3 assumed occupants, age 54, average insulation, double glazing, modern boiler .90, no PV/controls, London climate .95, behaviour 1; v3 pilot heat/appliance scales. PV substantial at self-consumed PV/demand >=20%; heat pumps assume air-source.'
        props.append(row); energy.extend(readings)
        metadata.append({'property_id': base['property_id'], 'latent_borough': borough,
                         'source_kind': 'synthetic latent location; not an observed property match',
                         'split': assign(base['customer_id'])})
    return props, energy, metadata


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--total', type=int, default=2000)
    parser.add_argument('--output', type=Path, default=ROOT / 'generated' / VERSION)
    parser.add_argument('--handoff', action='store_true')
    args = parser.parse_args()
    refs = json.loads(REFERENCE.read_text())
    fields, original = read_csv(ROOT / 'csv/properties.csv')
    meter_fields, original_energy = read_csv(ROOT / 'csv/energy_usage.csv')
    locked = json.loads(SCHEMA.read_text())
    if fields != locked['properties'] or meter_fields != locked['energy_usage']:
        raise ValueError('Schema drift; refusing automatic migration')
    if args.output.resolve() == (ROOT / 'csv').resolve():
        raise ValueError('Cannot overwrite original CSVs')
    parameters = calibrate(refs)
    props, energy, metadata = simulate(original, original_energy, fields, args.total, refs, parameters)
    validate(props, energy)
    report = audit(props, energy)
    if report['errors']:
        raise ValueError(report['errors'])
    output = args.output
    write_csv(output / 'properties.csv', fields, props)
    write_csv(output / 'energy_usage.csv', meter_fields, energy)
    assignments = [dict(property_id=p['property_id'], customer_id=p['customer_id'], split='legacy_diagnostic') for p in original]
    assignments.extend(dict(property_id=p['property_id'], customer_id=p['customer_id'], split=assign(p['customer_id'])) for p in props[len(original):])
    write_csv(output / 'split_manifest.csv', ['property_id', 'customer_id', 'split'], assignments)
    write_json(output / 'latent_provenance.json', metadata)
    write_json(output / 'parameters.json', parameters)
    write_json(output / 'derived_diagnostics.json', diagnostics(props, energy))
    grouped = defaultdict(list)
    for r in energy:
        grouped[r['property_id']].append(r)
    new = props[len(original):]
    report['reference_comparison'] = {'new_london_properties': len(new),
        'new_type_mix': dict(Counter(p['property_type'] for p in new)),
        'new_epc_mix': dict(Counter(p['energy_rating'] for p in new)),
        'new_mean_floor_area_m2': mean(float(p['floor_area_m2']) for p in new) if new else None,
        'epc_certificate_mean_area_m2': refs['epc_existing_2025']['floor_area_total_m2'] / refs['epc_existing_2025']['certificate_count'],
        'new_median_grid_kwh': median(sum(float(r['electricity_kwh']) for r in grouped[p['property_id']]) for p in new) if new else None,
        'new_gas_heated_median_kwh': median(sum(float(r['gas_kwh']) for r in grouped[p['property_id']]) for p in new if 'gas boiler' in p['heating']) if new else None,
        'reference_need': refs['need_london_2024'],
        'interpretation': 'Historical aggregates guide marginal simulation; joint distributions and current household/market realism are unvalidated.'}
    report['split_counts'] = dict(Counter(r['split'] for r in assignments))
    report['original_records_preserved'] = props[:len(original)] == original and energy[:len(original_energy)] == original_energy
    report['split_policy'] = 'Legacy 100 diagnostic only; independent fresh customer IDs with 40/20/20/20 hash assignment. Public pilot parameters frozen before model evaluation.'
    write_json(output / 'quality_report.json', report)
    edge_p, edge_e, edge_manifest = fixtures(props, energy)
    write_csv(output / 'edge_cases/properties.csv', fields, edge_p)
    write_csv(output / 'edge_cases/energy_usage.csv', meter_fields, edge_e)
    write_json(output / 'edge_cases/manifest.json', edge_manifest)
    chosen = original[:10] + new[:20]
    chosen_ids = {p['property_id'] for p in chosen}
    write_csv(output / 'sample/properties.csv', fields, chosen)
    write_csv(output / 'sample/energy_usage.csv', meter_fields, [r for r in energy if r['property_id'] in chosen_ids])
    sources = [REFERENCE, SCHEMA, Path(__file__), ROOT / 'scripts/expand_dataset.py', ROOT / 'scripts/generate_energy_usage.py',
               ROOT / 'csv/properties.csv', ROOT / 'csv/energy_usage.csv', ROOT / 'csv/emission_factors_2026.csv', ROOT / 'csv/emission_factors_2026.provenance.json']
    write_json(output / 'provenance.json', {'version': VERSION, 'python_runtime': sys.version.split()[0],
               'status': 'synthetic', 'schema_changed': False, 'new_ml_inputs': [],
               'source_sha256': {str(p.relative_to(ROOT.parent)).replace('\\', '/'): sha(p) for p in sources},
               'output_sha256': {str(p.relative_to(output)).replace('\\', '/'): sha(p) for p in sorted(output.rglob('*')) if p.is_file() and p.name != 'provenance.json'},
               'observed_property_joins': 0, 'source_reference': str(REFERENCE.relative_to(ROOT.parent)),
               'price': 'Public HPI type/borough anchors; independent location and unchanged .18 log noise; never EPC/retrofit uplift.',
               'unknown_eligibility': 'Four compatibility columns remain blank; no cost or tariff columns introduced.',
               'smartmeter': 'Catalogue reviewed; historical 2011-2014 household rows not downloaded. Existing seasonal model retained; not claimed to be empirically fitted.',
               'limitations': ['HPI aggregate averages are not correctly matched observed price labels.', 'EPC lodgements are biased and may repeat homes.',
                               'Census/EHS 2021, NEED 2024, EPC 2025 and HPI July 2026 are different populations/periods.',
                               'Uniform latent borough weights, conditional area distributions and equipment probabilities remain assumptions.']})
    if args.handoff:
        reports, samples = ROOT / 'reports' / VERSION, ROOT / 'samples' / VERSION
        reports.mkdir(parents=True, exist_ok=True); samples.mkdir(parents=True, exist_ok=True)
        for name in ['quality_report.json', 'parameters.json', 'provenance.json', 'split_manifest.csv']:
            shutil.copyfile(output / name, reports / name)
        for name in ['properties.csv', 'energy_usage.csv']:
            shutil.copyfile(output / 'sample' / name, samples / name)
    print(json.dumps({'properties': len(props), 'monthly_readings': len(energy), 'output': str(output),
                      'audit_errors': report['errors'], 'splits': report['split_counts']}, indent=2))


if __name__ == '__main__':
    main()
