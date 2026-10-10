import csv
from pathlib import Path
import pytest
from app.db.repository import CsvPropertyRepository

ROOT = Path(__file__).resolve().parents[2]


def test_csv_dataset_loads_and_sums():
    repo = CsvPropertyRepository(ROOT / 'Data/csv/properties.csv', ROOT / 'Data/csv/energy_usage.csv')
    assert len(repo.list_properties()) == 100
    first = repo.load_property('P00001')
    assert first.annual_energy.electricity_kwh == 2997.41
    assert first.annual_energy.gas_kwh == 27040.56
    assert first.annual_energy.electricity_months_covered == 12
    assert first.dataset_kind == 'synthetic'
    pump = repo.load_property('P00003')
    assert pump.annual_energy.gas_kwh == 0
    assert pump.property.heating_system is None
    assert pump.property.renewable_contribution is None
    assert pump.benchmark is None


def write_energy(tmp_path, rows):
    path = tmp_path / 'energy.csv'
    with path.open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    return path


@pytest.fixture
def energy_rows():
    with (ROOT / 'Data/csv/energy_usage.csv').open(newline='') as stream:
        return list(csv.DictReader(stream))


def test_missing_fuel_is_not_zero(tmp_path, energy_rows):
    energy_rows[0]['gas_kwh'] = ''
    repo = CsvPropertyRepository(ROOT / 'Data/csv/properties.csv', write_energy(tmp_path, energy_rows))
    energy = repo.load_property('P00001').annual_energy
    assert energy.gas_kwh is None
    assert energy.gas_months_covered == 11
    assert energy.electricity_kwh == 2997.41


def test_duplicate_month_is_rejected(tmp_path, energy_rows):
    energy_rows.append(energy_rows[0].copy())
    with pytest.raises(ValueError, match='Duplicate energy month'):
        CsvPropertyRepository(ROOT / 'Data/csv/properties.csv', write_energy(tmp_path, energy_rows))


def test_orphan_energy_is_rejected(tmp_path, energy_rows):
    energy_rows[0]['property_id'] = 'UNKNOWN'
    with pytest.raises(ValueError, match='Unknown energy property'):
        CsvPropertyRepository(ROOT / 'Data/csv/properties.csv', write_energy(tmp_path, energy_rows))
