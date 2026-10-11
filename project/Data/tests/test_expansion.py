"""Contract, physical integrity, missingness and leakage regression tests."""
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'Data/scripts'))
from expand_dataset import audit, diagnostics, expand, fixtures, read_csv, splits, write_csv
from generate_properties import BASE_FIELDS, generate_base


@pytest.fixture(scope='module')
def expanded():
    fields, source = read_csv(ROOT / 'Data/csv/properties.csv')
    meter_fields, meters = read_csv(ROOT / 'Data/csv/energy_usage.csv')
    props, energy = expand(source, meters, fields, 230)
    return fields, meter_fields, source, meters, props, energy


def test_schema_source_preservation_and_reproducibility(expanded):
    fields, meter_fields, source, meters, props, energy = expanded
    locked = json.loads((ROOT / 'Data/manifests/kew_schema_v1.json').read_text())
    assert fields == locked['properties'] and meter_fields == locked['energy_usage']
    assert all(list(p) == fields for p in props)
    assert all(list(r) == meter_fields for r in energy)
    assert props[:100] == source and energy[:1200] == meters
    assert (props, energy) == expand(source, meters, fields, 230)
    assert props[:150] == expand(source, meters, fields, 150)[0]
    assert energy[:1800] == expand(source, meters, fields, 150)[1]
    demos = [{k: p[k] for k in BASE_FIELDS} for p in source[:10]]
    legacy = generate_base(demos)
    assert all(str(p[k]) == old[k] for p, old in zip(legacy, source) for k in BASE_FIELDS)


def test_physical_audit_detects_corruption(expanded):
    _, _, _, _, props, energy = expanded
    assert audit(props, energy)['errors'] == []
    bad = [dict(p) for p in props]
    bad[0]['heating_system'] = 'electric_resistance'
    assert any('heating subtype conflict' in x for x in audit(bad, energy)['errors'])
    bad_meters = [dict(r) for r in energy]
    bad_meters[0]['electricity_kwh'] = '99999'
    assert any('grid/PV balance' in x for x in audit(props, bad_meters)['errors'])
    assert audit(props, energy + [energy[0]])['joins']['duplicate_month_keys'] == 1


def test_stable_customer_splits_preserve_holdout(expanded):
    _, _, _, _, props, _ = expanded
    path = ROOT / 'ml/reports/current_snapshot/split_manifest.csv'
    assigned = splits(props, path)
    _, prior = read_csv(path)
    assert assigned[:100] == prior
    assert splits(props[:150], path) == assigned[:150]
    same_customer = dict(props[-1], property_id='ANOTHER_HOME')
    extended = splits(props + [same_customer], path)
    assert extended[-1]['split'] == extended[-2]['split']
    assert not set(r['property_id'] for r in assigned if r['split'] == 'test') & set(r['property_id'] for r in assigned if r['split'] != 'test')


def test_missing_is_distinct_from_zero_and_edges_are_isolated(expanded):
    fields, meter_fields, _, _, props, energy = expanded
    edge_p, edge_e, manifest = fixtures(props, energy)
    assert len(edge_p) == 60 and all(list(p) == fields for p in edge_p)
    assert all(list(r) == meter_fields for r in edge_e)
    assert not {p['property_id'] for p in edge_p} & {p['property_id'] for p in props}
    derived = {r['property_id']: r for r in diagnostics(edge_p, edge_e)}
    for r in manifest:
        intensity = derived[r['property_id']]['purchased_energy_intensity_kwh_m2_year']
        if r['case'] in ('missing_month', 'missing_reading', 'unknown_floor_area'):
            assert intensity is None
        if r['case'] == 'zero_all_consumption':
            assert intensity == 0
    assert all(p[k] == '' for p in props[100:] for k in ['roof_suitable_for_loft', 'roof_suitable_for_solar', 'heat_pump_compatible', 'controls_compatible'])


def test_backend_and_existing_ml_accept_same_contract(expanded, tmp_path):
    import pandas as pd
    from app.db.repository import CsvPropertyRepository
    from ml.valuation import validate_snapshot
    fields, meter_fields, _, _, props, energy = expanded
    p_path, e_path = tmp_path / 'properties.csv', tmp_path / 'energy_usage.csv'
    write_csv(p_path, fields, props)
    write_csv(e_path, meter_fields, energy)
    repository = CsvPropertyRepository(p_path, e_path)
    assert len(repository.list_properties()) == 230
    record = repository.load_property('P00101')
    assert record.property.roof_suitable_for_solar is None
    assert record.annual_energy.electricity_months_covered == 12
    validated = validate_snapshot(pd.read_csv(p_path))
    assert len(validated) == 230


def test_duplicate_source_is_rejected(expanded):
    fields, _, source, meters, _, _ = expanded
    with pytest.raises(ValueError, match='Ambiguous source IDs'):
        expand(source + [source[0]], meters, fields, 230)
