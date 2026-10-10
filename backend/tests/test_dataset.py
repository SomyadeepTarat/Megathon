import csv
from pathlib import Path
import pytest
from app.db.repository import CsvPropertyRepository, load_property_energy_data

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
    assert pump.property.heating_system == 'air_source_heat_pump'
    assert pump.property.renewable_contribution in ('limited', 'substantial')
    assert pump.benchmark is not None
    assert any('synthetic reference benchmark' in warning for warning in pump.annual_energy.warnings)


def test_updated_dataset_produces_all_full_scores():
    from app.core.scoring import calculate_score
    repo = CsvPropertyRepository(ROOT / 'Data/csv/properties.csv', ROOT / 'Data/csv/energy_usage.csv')
    for record in repo.list_properties():
        score = calculate_score(record)
        assert score.status == 'available'
        assert len(score.components) == 7
        assert 0 <= score.score <= 100
        assert score.missing_fields == []


def test_combined_record_preserves_property_and_months_and_aggregates_energy():
    repo = CsvPropertyRepository.from_project_root(ROOT)
    result = repo.load_combined_record('P00003')

    typed_contract = set(repo.load_property('P00003').model_dump(mode='json'))
    assert set(result) == typed_contract | {'monthly_energy'}
    assert result['property']['property_id'] == 'P00003'
    assert result['property']['thermal_demand_kwh']
    assert result['property']['scop']
    assert result['benchmark'] is not None
    assert result['dataset_kind'] == 'synthetic'
    assert len(result['monthly_energy']) == 12
    assert all(row['property_id'] == 'P00003' for row in result['monthly_energy'])
    assert result['monthly_energy'][0]['month'] == '2025-01'

    for field in ('electricity_kwh', 'gas_kwh', 'electricity_demand_kwh',
                  'solar_generation_kwh', 'solar_self_consumed_kwh', 'solar_export_kwh',
                  'space_heating_demand_kwh', 'hot_water_demand_kwh'):
        assert result['annual_energy'][field] == pytest.approx(
            sum(float(row[field]) for row in result['monthly_energy']))
    assert result['annual_energy']['electricity_kwh'] != result['annual_energy']['electricity_demand_kwh']
    assert result['annual_energy']['solar_generation_kwh'] != result['annual_energy']['solar_self_consumed_kwh']
    assert 'reading_status' not in result['annual_energy']
    assert 'boiler_efficiency' not in result['annual_energy']


def test_p00001_retains_original_fields_and_nulls_without_allowlist():
    repo = CsvPropertyRepository.from_project_root(ROOT)
    result = repo.load_combined_record('P00001')
    with (ROOT / 'Data/csv/properties.csv').open(newline='') as stream:
        source = next(row for row in csv.DictReader(stream) if row['property_id'] == 'P00001')

    requested_fields = {
        'annual_space_heating_demand_kwh', 'annual_hot_water_demand_kwh',
        'thermal_demand_kwh', 'thermal_demand_scope',
        'annual_base_appliance_electricity_kwh', 'annual_gas_space_heating_kwh',
        'annual_gas_hot_water_kwh', 'annual_electric_space_heating_kwh',
        'annual_electric_hot_water_kwh', 'boiler_efficiency', 'scop',
        'hot_water_cop', 'electric_resistance_efficiency',
        'annual_electricity_demand_kwh', 'annual_solar_generation_kwh',
        'annual_solar_self_consumed_kwh', 'solar_installed',
        'roof_suitable_for_loft', 'roof_suitable_for_solar',
        'heat_pump_compatible', 'controls_compatible', 'physical_inputs_status',
        'physical_inputs_source', 'physical_inputs_year', 'physical_inputs_generation_seed',
    }
    assert requested_fields <= set(source)
    assert set(result['property']) == set(source)
    assert requested_fields <= set(result['property'])
    assert result['property']['physical_inputs_status'] == source['physical_inputs_status']
    assert result['property']['thermal_demand_kwh'] == source['thermal_demand_kwh']
    assert result['property']['scop'] is None
    assert result['property']['roof_suitable_for_loft'] is None
    assert result['property']['roof_suitable_for_solar'] is None
    assert result['property']['heat_pump_compatible'] is None
    assert result['property']['controls_compatible'] is None
    for field in requested_fields - {
        'scop', 'hot_water_cop', 'electric_resistance_efficiency',
        'roof_suitable_for_loft', 'roof_suitable_for_solar',
        'heat_pump_compatible', 'controls_compatible',
    }:
        assert result['property'][field] == source[field]
    assert result['annual_energy']['electricity_kwh'] == 2997.41
    assert result['annual_energy']['gas_kwh'] == 27040.56
    assert result['annual_energy']['quality'] == 'synthetic'
    assert result['annual_energy']['electricity_demand_kwh'] == pytest.approx(
        sum(float(row['electricity_demand_kwh']) for row in result['monthly_energy']))


def test_combined_record_loads_any_property_by_id():
    repo = CsvPropertyRepository.from_project_root()
    result = repo.load_combined_record('P00001')
    assert result['property']['property_id'] == 'P00001'
    assert all(row['property_id'] == 'P00001' for row in result['monthly_energy'])
    assert result['annual_energy']['electricity_kwh'] == pytest.approx(
        sum(float(row['electricity_kwh']) for row in result['monthly_energy']))


def test_public_loader_function_returns_combined_data():
    result = load_property_energy_data('P00001')
    assert result['property']['property_id'] == 'P00001'
    assert result['property']['thermal_demand_kwh'] == '19469.206660'
    assert result['annual_energy']['electricity_kwh'] == 2997.41
    assert result['annual_energy']['gas_kwh'] == 27040.56
    assert len(result['monthly_energy']) == 12


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
