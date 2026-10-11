import csv
from pathlib import Path

import pytest
from app.db.repository import CsvPropertyRepository


def test_london_repository_excludes_legacy_and_preserves_unknowns(tmp_path):
    root = Path(__file__).resolve().parents[2]
    import sys
    sys.path.insert(0, str(root / 'Data/scripts'))
    from expand_dataset import read_csv, write_csv
    from simulate_london import simulate, calibrate, REFERENCE, assign
    import json
    fields, original = read_csv(root / 'Data/csv/properties.csv')
    energy_fields, meters = read_csv(root / 'Data/csv/energy_usage.csv')
    refs = json.loads(REFERENCE.read_text())
    props, energy, _ = simulate(original, meters, fields, 110, refs, calibrate(refs, size=100))
    output = tmp_path / 'Data/generated/kew_london_v3'
    write_csv(output / 'properties.csv', fields, props)
    write_csv(output / 'energy_usage.csv', energy_fields, energy)
    manifest = [dict(property_id=p['property_id'], customer_id=p['customer_id'], split='legacy_diagnostic' if i < 100 else assign(p['customer_id'])) for i, p in enumerate(props)]
    write_csv(output / 'split_manifest.csv', ['property_id', 'customer_id', 'split'], manifest)
    repo = CsvPropertyRepository.from_london(tmp_path)
    assert len(repo.list_properties()) == 10
    assert all(r.property.region == 'Greater London' and r.property.heat_pump_compatible is None and not r.retrofit_costs for r in repo.list_properties())
    assert 'kew_london_v3' in repo.list_properties()[0].dataset_source
    with pytest.raises(KeyError):
        repo.load_property('P00001')
    manifest[-1]['property_id'] = 'WRONG'
    write_csv(output / 'split_manifest.csv', ['property_id', 'customer_id', 'split'], manifest)
    with pytest.raises(ValueError, match='manifest'):
        CsvPropertyRepository.from_london(tmp_path)
