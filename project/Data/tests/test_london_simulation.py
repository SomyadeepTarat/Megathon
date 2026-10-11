import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'Data/scripts'))
from expand_dataset import audit, read_csv, write_csv
from simulate_london import REFERENCE, assign, base_property, calibrate, simulate


@pytest.fixture(scope='module')
def cohort():
    refs = json.loads(REFERENCE.read_text())
    params = calibrate(refs, size=500)
    fields, original = read_csv(ROOT / 'Data/csv/properties.csv')
    meter_fields, meters = read_csv(ROOT / 'Data/csv/energy_usage.csv')
    props, energy, metadata = simulate(original, meters, fields, 150, refs, params)
    return refs, params, fields, meter_fields, original, meters, props, energy, metadata


def test_unchanged_contract_physics_and_stable_prefix(cohort):
    refs, params, fields, meter_fields, original, meters, props, energy, metadata = cohort
    assert props[:100] == original and energy[:1200] == meters
    assert all(list(p) == fields for p in props)
    assert all(list(m) == meter_fields for m in energy)
    assert audit(props, energy)['errors'] == []
    smaller = simulate(original, meters, fields, 130, refs, params)
    assert smaller[0] == props[:130] and smaller[1] == energy[:1560]
    assert all(p['region'] == 'Greater London' for p in props[100:])
    assert all(p[k] == '' for p in props[100:] for k in ['heat_pump_compatible', 'roof_suitable_for_solar', 'roof_suitable_for_loft', 'controls_compatible'])


def test_reference_scope_and_price_dispersion(cohort):
    refs, params, *_ = cohort
    assert len(refs['borough_type_prices_gbp']) == 33
    assert refs['london_type_prices_gbp']['Flat'] == 424013
    assert sum(refs['epc_existing_2025']['rating_counts'].values()) == refs['epc_existing_2025']['certificate_count']
    assert params['residual_log_price_sigma'] == .18
    assert 'PILOT' in params['pilot_namespace']
    assert refs['need_london_2024']['gas']['median_kwh'] > 10000
    assert base_property('P100001', refs) == base_property('P100001', refs)


def test_fresh_customer_reservation_excludes_exposed_ids(cohort):
    *_, props, _, metadata = cohort
    legacy_ids = {p['property_id'] for p in props[:100]}
    assert not legacy_ids & {r['property_id'] for r in metadata}
    _, v2 = read_csv(ROOT / 'Data/reports/kew_synthetic_v2/split_manifest.csv')
    assert not {r['property_id'] for r in v2} & {r['property_id'] for r in metadata}
    assert all(r['split'] == assign(props[i+100]['customer_id']) for i, r in enumerate(metadata))
    assert assign('C100001') == assign('C100001')


def test_backend_and_ml_contract(cohort, tmp_path):
    import pandas as pd
    from app.db.repository import CsvPropertyRepository
    from app.core.scoring import calculate_score
    from ml.valuation import validate_snapshot
    _, _, fields, meter_fields, _, _, props, energy, _ = cohort
    write_csv(tmp_path / 'properties.csv', fields, props)
    write_csv(tmp_path / 'energy_usage.csv', meter_fields, energy)
    repo = CsvPropertyRepository(tmp_path / 'properties.csv', tmp_path / 'energy_usage.csv')
    assert len(repo.list_properties()) == 150
    assert all(calculate_score(p).status == 'available' for p in repo.list_properties())
    assert len(validate_snapshot(pd.read_csv(tmp_path / 'properties.csv'))) == 150


def test_final_evaluation_guard_does_not_access_data(tmp_path):
    from evaluate_london import evaluate
    (tmp_path / 'FINAL_EVALUATION.json').write_text('{}')
    with pytest.raises(ValueError, match='already recorded'):
        evaluate(tmp_path, final=True)
