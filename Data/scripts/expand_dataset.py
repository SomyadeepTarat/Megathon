"""Versioned synthetic expansion. No dependencies, schema changes or observed joins.

Run from the project root: python Data/scripts/expand_dataset.py --total 2000
"""
import argparse
import csv
import hashlib
import json
import math
import shutil
from collections import Counter, defaultdict
from pathlib import Path
from statistics import median

from generate_properties import BASE_FIELDS, generate_base
from generate_energy_usage import SEED, YEAR, generate, validate

ROOT = Path(__file__).resolve().parents[1]
VERSION = 'kew_synthetic_v2'
SCHEMA = ROOT / 'manifests' / 'kew_schema_v1.json'
SYSTEMS = {'Old gas boiler': 'old_gas_boiler', 'Modern gas boiler': 'modern_gas_boiler',
           'Heat pump': 'air_source_heat_pump', 'Electric resistance': 'electric_resistance'}
COMPATIBILITY = ['roof_suitable_for_loft', 'roof_suitable_for_solar',
                 'heat_pump_compatible', 'controls_compatible']


def read_csv(path):
    with Path(path).open(newline='', encoding='utf-8-sig') as stream:
        reader = csv.DictReader(stream)
        rows = list(reader)
        if any(None in row or any(v is None for v in row.values()) for row in rows):
            raise ValueError(f'Malformed CSV row in {path}')
        return reader.fieldnames, rows


def write_csv(path, fields, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', newline='', encoding='utf-8') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator='\n')
        writer.writeheader()
        writer.writerows(rows)


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n', encoding='utf-8')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def physical_row(base, template, readings, fields):
    row = {k: str(base[k]) if k in base else '' for k in fields}
    row.update({k: template[k] for k in fields if k.startswith('benchmark_')})
    def total(key):
        return sum(float(m[key]) for m in readings)
    heat, water = total('space_heating_demand_kwh'), total('hot_water_demand_kwh')
    demand, generation, own = (total(k) for k in
                              ('electricity_demand_kwh', 'solar_generation_kwh', 'solar_self_consumed_kwh'))
    heating = row['heating']
    efficiency = .72 if heating == 'Old gas boiler' else .90
    gas = 'gas boiler' in heating
    pump = heating == 'Heat pump'
    electric_heat = 0 if gas else heat / (3 if pump else 1)
    electric_water = 0 if gas else water / (2.5 if pump else 1)
    numbers = {
        'annual_space_heating_demand_kwh': heat, 'annual_hot_water_demand_kwh': water,
        'thermal_demand_kwh': heat + water, 'annual_electricity_demand_kwh': demand,
        'annual_solar_generation_kwh': generation, 'annual_solar_self_consumed_kwh': own,
        'annual_base_appliance_electricity_kwh': demand - electric_heat - electric_water,
        'annual_gas_space_heating_kwh': heat / efficiency if gas else 0,
        'annual_gas_hot_water_kwh': water / efficiency if gas else 0,
        'annual_electric_space_heating_kwh': electric_heat,
        'annual_electric_hot_water_kwh': electric_water,
    }
    row.update({k: f'{v:.6f}' for k, v in numbers.items()})
    share = own / demand if demand else 0
    row.update(heating_system=SYSTEMS[heating],
               heating_system_status='synthetic_assumption' if pump else 'derived_from_synthetic',
               renewable_share=f'{share:.9f}',
               renewable_contribution='none' if generation == 0 else 'substantial' if share >= .2 else 'limited',
               boiler_efficiency=f'{efficiency:.2f}' if gas else '',
               scop='3.0' if pump else '', hot_water_cop='2.5' if pump else '',
               electric_resistance_efficiency='1.0' if heating == 'Electric resistance' else '',
               solar_installed=row['solar'], thermal_demand_scope='space_heating_plus_hot_water',
               physical_inputs_status='synthetic_modelled', physical_inputs_year=str(YEAR),
               physical_inputs_generation_seed=str(SEED),
               physical_inputs_source='Data/scripts/expand_dataset.py v2; modelled, not measured; Data/relations/expanded_dataset.md')
    return row


def expand(original, original_energy, fields, total):
    if total < len(original):
        raise ValueError('Total must retain all original properties')
    ids = {p['property_id'] for p in original}
    customers = {p['customer_id'] for p in original}
    if len(ids) != len(original):
        raise ValueError('Ambiguous source IDs; refusing expansion')
    if any(not x.startswith('P') or not x[1:].isdigit() for x in ids):
        raise ValueError('Expected existing P + numeric IDs')
    next_id = max(int(x[1:]) for x in ids) + 1
    templates = {p['property_type']: p for p in original}
    demos = [{k: p[k] for k in BASE_FIELDS} for p in original[:10]]
    added = []
    batch = 0
    while len(added) < total - len(original):
        batch += 1
        # Reuse the existing conditional generator; each batch gets its own seed.
        for base in generate_base(demos, seed=SEED + batch)[10:]:
            if len(added) == total - len(original):
                break
            identifier = next_id + len(added)
            base.update(property_id=f'P{identifier:05d}', customer_id=f'C{identifier:05d}')
            if base['customer_id'] in customers:
                raise ValueError('Generated customer ID collides with source')
            added.append(base)
    energy = generate(added)
    grouped = defaultdict(list)
    for m in energy:
        m['reading_source'] = 'Data/scripts/expand_dataset.py v2; synthetic physical model; no observed meter record'
        grouped[m['property_id']].append(m)
    props = original + [physical_row(p, templates[p['property_type']], grouped[p['property_id']], fields) for p in added]
    return props, original_energy + energy


def audit(props, energy):
    groups = defaultdict(list)
    for r in energy:
        groups[r['property_id']].append(r)
    errors = []
    keys = [(r['property_id'], r['month']) for r in energy]
    identifiers = [p['property_id'] for p in props]
    if len(set(identifiers)) != len(props):
        errors.append('duplicate property IDs')
    if len(set(keys)) != len(keys):
        errors.append('duplicate property-month keys')
    unknown = sorted(set(groups) - set(identifiers))
    if unknown:
        errors.append('unmatched meter IDs')
    def close(a, b, tolerance=.08):
        return abs(float(a) - float(b)) <= tolerance
    for p in props:
        pid = p['property_id']
        readings = groups[pid]
        if {r['month'] for r in readings} != {f'{YEAR}-{m:02d}' for m in range(1, 13)}:
            errors.append(f'{pid}: incomplete calendar-year coverage')
        if p['heating_system'] != SYSTEMS.get(p['heating']):
            errors.append(f'{pid}: heating subtype conflict')
        if p['solar'] != p['solar_installed']:
            errors.append(f'{pid}: solar flag conflict')
        if any(p[k] not in ('true', 'false', '') for k in COMPATIBILITY):
            errors.append(f'{pid}: invalid compatibility flag')
        if p['data_status'] != 'synthetic' or p['physical_inputs_status'] != 'synthetic_modelled':
            errors.append(f'{pid}: missing synthetic disclosure')
        if any(not math.isfinite(float(v)) or float(v) < 0 for k, v in p.items()
               if (k.endswith('_kwh') or k in ('age', 'bedrooms', 'floor_area_m2', 'current_value_estimate_gbp')) and v):
            errors.append(f'{pid}: invalid numeric input')
        if float(p['floor_area_m2'] or 0) <= 0:
            errors.append(f'{pid}: invalid floor area')
        for r in readings:
            if any(not math.isfinite(float(v)) or float(v) < 0 for k, v in r.items() if k.endswith('_kwh') and v):
                errors.append(f'{pid}/{r["month"]}: invalid energy')
            if not close(float(r['electricity_kwh']) + float(r['solar_self_consumed_kwh']), r['electricity_demand_kwh'], .011):
                errors.append(f'{pid}/{r["month"]}: grid/PV balance')
            if not close(float(r['solar_export_kwh']) + float(r['solar_self_consumed_kwh']), r['solar_generation_kwh'], .00001):
                errors.append(f'{pid}/{r["month"]}: PV balance')
            if p['solar'] == 'false' and float(r['solar_generation_kwh']) != 0:
                errors.append(f'{pid}: PV without installation')
            heat, water = float(r['space_heating_demand_kwh']), float(r['hot_water_demand_kwh'])
            gas = 'gas boiler' in p['heating']
            expected_gas = (heat + water) / float(p['boiler_efficiency']) if gas else 0
            if not close(expected_gas, r['gas_kwh'], .011):
                errors.append(f'{pid}/{r["month"]}: fuel/thermal balance')
        mappings = {'annual_electricity_demand_kwh': 'electricity_demand_kwh',
                    'annual_solar_generation_kwh': 'solar_generation_kwh',
                    'annual_solar_self_consumed_kwh': 'solar_self_consumed_kwh',
                    'annual_space_heating_demand_kwh': 'space_heating_demand_kwh',
                    'annual_hot_water_demand_kwh': 'hot_water_demand_kwh'}
        for annual, monthly in mappings.items():
            if not close(p[annual], sum(float(r[monthly]) for r in readings), .00003):
                errors.append(f'{pid}: {annual} disagrees with meters')
        if not close(p['thermal_demand_kwh'], float(p['annual_space_heating_demand_kwh']) + float(p['annual_hot_water_demand_kwh']), .00001):
            errors.append(f'{pid}: thermal scope balance')
        components = ['annual_base_appliance_electricity_kwh', 'annual_electric_space_heating_kwh', 'annual_electric_hot_water_kwh']
        if not close(p['annual_electricity_demand_kwh'], sum(float(p[k]) for k in components), .00003):
            errors.append(f'{pid}: electrical components balance')
        if not close(float(p['annual_gas_space_heating_kwh']) + float(p['annual_gas_hot_water_kwh']),
                     sum(float(r['gas_kwh']) for r in readings)):
            errors.append(f'{pid}: gas components balance')
        heat, water = float(p['annual_space_heating_demand_kwh']), float(p['annual_hot_water_demand_kwh'])
        if 'gas boiler' in p['heating']:
            if not close(float(p['annual_gas_space_heating_kwh']) * float(p['boiler_efficiency']), heat, .00003) or not close(float(p['annual_gas_hot_water_kwh']) * float(p['boiler_efficiency']), water, .00003):
                errors.append(f'{pid}: boiler efficiency balance')
        else:
            heat_eff = float(p['scop']) if p['heating'] == 'Heat pump' else float(p['electric_resistance_efficiency'])
            water_eff = float(p['hot_water_cop']) if p['heating'] == 'Heat pump' else heat_eff
            if not close(float(p['annual_electric_space_heating_kwh']) * heat_eff, heat, .00003) or not close(float(p['annual_electric_hot_water_kwh']) * water_eff, water, .00003):
                errors.append(f'{pid}: electric efficiency balance')
        demand = float(p['annual_electricity_demand_kwh'])
        share = float(p['annual_solar_self_consumed_kwh']) / demand if demand else 0
        if not close(share, p['renewable_share'], .00000001):
            errors.append(f'{pid}: renewable share balance')
        expected = 'none' if float(p['annual_solar_generation_kwh']) == 0 else 'substantial' if share >= .2 else 'limited'
        if p['renewable_contribution'] != expected:
            errors.append(f'{pid}: renewable contribution conflict')
    categories = ['property_type', 'energy_rating', 'heating', 'insulation', 'glazing', 'region', 'data_status', 'physical_inputs_status']
    numeric = ['age', 'floor_area_m2', 'bedrooms', 'current_value_estimate_gbp', 'thermal_demand_kwh', 'annual_electricity_demand_kwh']
    return {
        'properties': len(props), 'monthly_readings': len(energy), 'property_columns': len(props[0]),
        'energy_columns': len(energy[0]), 'errors': sorted(set(errors)),
        'missing_cells': {k: sum(p[k] == '' for p in props) for k in props[0] if any(p[k] == '' for p in props)},
        'categories': {k: dict(sorted(Counter(p[k] for p in props).items())) for k in categories},
        'numeric_ranges': {k: {'min': min(float(p[k]) for p in props), 'max': max(float(p[k]) for p in props),
                              'median': median(float(p[k]) for p in props)} for k in numeric},
        'meter_missing_cells': {k: sum(r[k] == '' for r in energy) for k in energy[0] if any(r[k] == '' for r in energy)},
        'outlier_review': {'rule': 'Engineering QA flags only; no clipping or empirical market claim.',
                           'property_ids': [p['property_id'] for p in props if float(p['floor_area_m2']) < 25 or float(p['floor_area_m2']) > 300 or float(p['age']) > 200 or float(p['thermal_demand_kwh']) / float(p['floor_area_m2']) > 400]},
        'joins': {'key': 'property_id; monthly uniqueness is property_id + month',
                  'unmatched_meter_ids': unknown, 'properties_without_meters': sorted(set(identifiers) - set(groups)),
                  'duplicate_property_ids': len(identifiers) - len(set(identifiers)),
                  'duplicate_month_keys': len(keys) - len(set(keys)), 'observed_external_joins': 0},
        'period': {'energy_year': YEAR, 'property_snapshot_date': None, 'transaction_dates': None,
                   'alignment': 'Scenario assumes equipment unchanged during 2025; source age is approximately one year newer. No observed snapshot date.'},
        'limitations': ['All property and meter rows are synthetic; value labels are not observed sale prices.',
                       'Four compatibility fields are unknown, not false; blank performance fields are not applicable.',
                       'No UPRNs, EPC dates, transactions, tariffs, costs or surveyed eligibility available in this schema.',
                       'Inherited source rows reference missing Data/relations/P3_HANDOFF.md; retained without inventing evidence.',
                       '2026 emission factors with 2025 energy are a scenario assumption, not a historical 2025 emissions estimate.'],
    }


def splits(props, prior_path):
    _, prior = read_csv(prior_path)
    known = {}
    for r in prior:
        customer = r['customer_id']
        if customer in known and known[customer] != r['split']:
            raise ValueError('Prior split has customer leakage')
        known[customer] = r['split']
    result = []
    for p in props:
        customer = p['customer_id']
        bucket = int(hashlib.sha256(f'{VERSION}:{customer}'.encode()).hexdigest()[:16], 16) / 2**64
        split = known.get(customer) or ('fit' if bucket < .55 else 'selection' if bucket < .70 else 'calibration' if bucket < .85 else 'test')
        result.append(dict(property_id=p['property_id'], customer_id=customer, split=split))
    return result


def diagnostics(props, energy):
    grouped = defaultdict(list)
    for r in energy:
        grouped[r['property_id']].append(r)
    result = []
    for p in props:
        rows = grouped[p['property_id']]
        complete = (len(rows) == 12 and {r['month'] for r in rows} == {f'{YEAR}-{m:02d}' for m in range(1, 13)}
                    and all(r['reading_status'] != 'missing' and r['electricity_kwh'] and r['gas_kwh'] for r in rows))
        area = float(p['floor_area_m2']) if p['floor_area_m2'] else None
        age = int(p['age']) if p['age'] else None
        purchased = sum(float(r['electricity_kwh']) + float(r['gas_kwh']) for r in rows) if complete else None
        result.append({'property_id': p['property_id'], 'purchased_energy_intensity_kwh_m2_year': purchased / area if purchased is not None and area and area > 0 else None,
                       'log_floor_area': math.log(area) if area and area > 0 else None,
                       'floor_area_band': None if area is None else '<55' if area < 55 else '55-89' if area < 90 else '90-139' if area < 140 else '140+',
                       'age_band': None if age is None else '0-26' if age <= 26 else '27-59' if age < 60 else '60-81' if age <= 81 else '82+',
                       'energy_year': YEAR if complete else None, 'region': p['region'] or None})
    return result


def fixtures(props, energy):
    """60 isolated QA records, excluded from the expanded training files."""
    by_id = defaultdict(list)
    for m in energy:
        by_id[m['property_id']].append(m)
    p_out, e_out, manifest = [], [], []
    cases = ['missing_month', 'missing_reading', 'zero_gas_electric', 'zero_all_consumption',
             'conflicting_heating', 'conflicting_solar', 'infeasible_solar', 'infeasible_heat_pump',
             'unknown_floor_area', 'missing_thermal_inputs']
    for i in range(60):
        case = cases[i % len(cases)]
        template = next(p for p in props if p['heating'] == 'Electric resistance') if case == 'zero_gas_electric' else props[i % len(props)]
        p = dict(template, property_id=f'EDGE{i+1:03d}', customer_id=f'EDGE_C{i+1:03d}')
        rows = [dict(m, property_id=p['property_id']) for m in by_id[template['property_id']]]
        if case == 'missing_month':
            rows = rows[:-1]
        elif case == 'missing_reading':
            rows[0].update(electricity_kwh='', gas_kwh='', reading_status='missing')
        elif case == 'zero_all_consumption':
            for m in rows:
                m.update({k: '0.000000' for k in m if k.endswith('_kwh')})
            p.update({k: '0.000000' for k in p if k.endswith('_kwh')})
            p.update(solar='false', solar_installed='false', renewable_share='0', renewable_contribution='none')
        elif case == 'conflicting_heating':
            p['heating_system'] = 'electric_resistance' if 'gas boiler' in p['heating'] else 'modern_gas_boiler'
        elif case == 'conflicting_solar':
            p['solar_installed'] = 'false' if p['solar'] == 'true' else 'true'
        elif case == 'infeasible_solar':
            p['roof_suitable_for_solar'] = 'false'
        elif case == 'infeasible_heat_pump':
            p['heat_pump_compatible'] = 'false'
        elif case == 'unknown_floor_area':
            p['floor_area_m2'] = ''
        elif case == 'missing_thermal_inputs':
            p.update(thermal_demand_kwh='', annual_space_heating_demand_kwh='', annual_hot_water_demand_kwh='')
        p_out.append(p)
        e_out.extend(rows)
        manifest.append({'property_id': p['property_id'], 'case': case,
                         'expected': 'reject conflicting source or mark unavailable' if case.startswith(('conflicting', 'unknown')) else 'preserve missingness/zero and apply eligibility gating',
                         'status': 'synthetic QA fixture; excluded from splits/training'})
    return p_out, e_out, manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--total', type=int, default=2000)
    parser.add_argument('--output', type=Path, default=ROOT / 'generated' / VERSION)
    parser.add_argument('--handoff', action='store_true', help='Refresh small tracked reports, split manifest and samples')
    args = parser.parse_args()
    source, meters = ROOT / 'csv/properties.csv', ROOT / 'csv/energy_usage.csv'
    fields, original = read_csv(source)
    meter_fields, original_energy = read_csv(meters)
    schema = json.loads(SCHEMA.read_text())
    if fields != schema['properties'] or meter_fields != schema['energy_usage']:
        raise ValueError('Source schema differs from locked contract; no automatic migration')
    output = args.output.resolve()
    if any(output == p.resolve().parent for p in (source, meters)):
        raise ValueError('Expanded data must be versioned separately from source CSVs')
    source_report = audit(original, original_energy)
    if source_report['errors']:
        raise ValueError(source_report['errors'])
    props, energy = expand(original, original_energy, fields, args.total)
    validate(props, energy)
    report = audit(props, energy)
    if report['errors']:
        raise ValueError(report['errors'])
    assignments = splits(props, ROOT.parent / 'ml/reports/current_snapshot/split_manifest.csv')
    split_by_id = {r['property_id']: r['split'] for r in assignments}
    report['splits'] = {name: {'count': sum(r['split'] == name for r in assignments),
                              'categories': {k: sorted({p[k] for p in props if split_by_id[p['property_id']] == name}) for k in ['region', 'property_type', 'energy_rating', 'heating']}}
                        for name in ['fit', 'selection', 'calibration', 'test']}
    report['split_policy'] = 'Preserve current_snapshot assignments; hash new customer IDs: 55/15/15/15. Sidecar requires explicit ML adoption; existing train() is unchanged.'
    fit_categories = report['splits']['fit']['categories']
    report['unseen_vs_fit'] = {name: {k: sorted(set(values) - set(fit_categories[k]))
                                    for k, values in report['splits'][name]['categories'].items()}
                             for name in ['selection', 'calibration', 'test']}
    report['original_records_preserved'] = props[:len(original)] == original and energy[:len(original_energy)] == original_energy
    write_csv(output / 'properties.csv', fields, props)
    write_csv(output / 'energy_usage.csv', meter_fields, energy)
    write_csv(output / 'split_manifest.csv', ['property_id', 'customer_id', 'split'], assignments)
    write_json(output / 'derived_diagnostics.json', diagnostics(props, energy))
    write_json(output / 'source_audit.json', source_report)
    write_json(output / 'quality_report.json', report)
    edge_p, edge_e, edge_manifest = fixtures(props, energy)
    write_csv(output / 'edge_cases/properties.csv', fields, edge_p)
    write_csv(output / 'edge_cases/energy_usage.csv', meter_fields, edge_e)
    write_json(output / 'edge_cases/manifest.json', edge_manifest)
    chosen = props[:10] + props[len(original):len(original)+20]
    chosen_ids = {p['property_id'] for p in chosen}
    write_csv(output / 'sample/properties.csv', fields, chosen)
    write_csv(output / 'sample/energy_usage.csv', meter_fields, [m for m in energy if m['property_id'] in chosen_ids])
    sources = [source, meters, ROOT / 'csv/emission_factors_2026.csv', ROOT / 'csv/emission_factors_2026.provenance.json',
               ROOT.parent / 'ml/reports/current_snapshot/split_manifest.csv', SCHEMA,
               Path(__file__), ROOT / 'scripts/generate_properties.py', ROOT / 'scripts/generate_energy_usage.py']
    manifest = {'version': VERSION, 'total_properties': len(props), 'monthly_readings': len(energy),
                'status': 'synthetic', 'physical_seed': SEED, 'base_batch_seeds': '43 + zero-based batch index; 90 appended properties per batch',
                'schema_changed': False, 'new_ml_inputs': [], 'observed_enrichment': False,
                'source_sha256': {str(p.relative_to(ROOT.parent)).replace('\\', '/'): sha(p) for p in sources},
                'output_sha256': {str(p.relative_to(output)).replace('\\', '/'): sha(p) for p in sorted(output.rglob('*')) if p.is_file() and p.name != 'provenance.json'},
                'price_model': 'Inherited regional/type/size/bedroom/age anchors plus independent lognormal noise; no retrofit uplift or energy features.',
                'inference': 'Original inputs unchanged. No observed transaction/date enrichment or market/causal validity claim.',
                'field_provenance': {'original_rows': 'Source CSVs retained cell-for-cell; existing field provenance preserved.',
                                     'new_base_fields': 'generate_properties.generate_base; inherited assumptions, independently seeded batches.',
                                     'new_benchmark_fields': 'Existing fixed synthetic type-specific reference; not an official standard.',
                                     'new_physical_fields': 'generate_energy_usage physical model; 2025; seed 42 per stable property ID.',
                                     'new_compatibility_fields': 'Unavailable; blank, no survey evidence.'}}
    write_json(output / 'provenance.json', manifest)
    if args.handoff:
        reports = ROOT / 'reports' / VERSION
        sample = ROOT / 'samples' / VERSION
        reports.mkdir(parents=True, exist_ok=True)
        sample.mkdir(parents=True, exist_ok=True)
        for name in ['source_audit.json', 'quality_report.json', 'provenance.json', 'split_manifest.csv']:
            shutil.copyfile(output / name, reports / name)
        for name in ['properties.csv', 'energy_usage.csv']:
            shutil.copyfile(output / 'sample' / name, sample / name)
        edge_sample = edge_p[:10]
        edge_ids = {p['property_id'] for p in edge_sample}
        write_csv(sample / 'edge_cases/properties.csv', fields, edge_sample)
        write_csv(sample / 'edge_cases/energy_usage.csv', meter_fields, [m for m in edge_e if m['property_id'] in edge_ids])
        write_json(sample / 'edge_cases/manifest.json', edge_manifest[:10])
    print(json.dumps({'output': str(output), 'properties': len(props), 'monthly_readings': len(energy),
                      'schema_unchanged': True, 'audit_errors': report['errors'], 'original_records_preserved': report['original_records_preserved']}, indent=2))


if __name__ == '__main__':
    main()
