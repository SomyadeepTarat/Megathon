import copy
import csv
import json
import subprocess
import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from app.main import app, repository
from app.db.repository import JsonPropertyRepository, EditableRepository
from app.schemas.models import ScenarioRequest, AnnualEnergy
from app.services.p4_adapter import configured_factors, P4RetrofitAdapter

ROOT = Path(__file__).resolve().parents[2]


def demo():
    return JsonPropertyRepository(ROOT / 'backend/data/curated_demo_properties.json').list_properties()[0]


def test_sqlite_roundtrip_preserves_costs_tariffs_and_unknowns(tmp_path):
    path = tmp_path / 'properties.db'
    base = JsonPropertyRepository(ROOT / 'backend/data/curated_demo_properties.json')
    first = EditableRepository(base, path)
    record = demo()
    record.property.property_id = 'PERSISTED'
    record.property.market_index = None
    first.save_property(record)
    reopened = EditableRepository(base, path)
    assert reopened.load_property('PERSISTED').model_dump() == record.model_dump()


def test_official_factors_are_bundled_and_versioned(monkeypatch):
    monkeypatch.delenv('GREENPRINT_EMISSION_FACTORS_FILE', raising=False)
    factors = configured_factors()
    assert factors.electricity.kg_co2e_per_kwh == .13096
    assert factors.gas.kg_co2e_per_kwh == .18231
    assert 'gross calorific' in factors.gas.accounting_boundary
    assert '2026-07-31' in factors.electricity.version


def test_chained_simulations_preserve_physical_state():
    record = demo()
    payload = record.model_dump(exclude={'dataset_kind', 'dataset_source'})
    adapter = P4RetrofitAdapter()
    together = adapter.simulate_retrofits(ScenarioRequest(**payload, retrofits=['loft_insulation', 'smart_thermostat']))
    first = adapter.simulate_retrofits(ScenarioRequest(**payload, retrofits=['smart_thermostat']))
    payload['property'] = first.updated_property
    payload['annual_energy'] = AnnualEnergy(**first.after.model_dump(), quality='estimated', method='Chained scenario', electricity_months_covered=12, gas_months_covered=12)
    second = adapter.simulate_retrofits(ScenarioRequest(**payload, retrofits=['loft_insulation']))
    assert second.after.gas_kwh == pytest.approx(together.after.gas_kwh)
    assert second.after.electricity_kwh == pytest.approx(together.after.electricity_kwh)


def test_budget_advisor_uses_actual_optimizer_and_simulation():
    saved = dict(repository.overrides)
    try:
        record = demo()
        repository.save_property(record)
        with TestClient(app) as client:
            result = client.post('/advisor/chat', json={'property_id': record.property.property_id,
                'message': 'Find a package for my budget', 'scenario': {'intent': 'optimize_budget', 'retrofits': [], 'budget_gbp': 7000, 'objective': 'energy_reduction'}})
        assert result.status_code == 200
        answer = result.json()
        assert answer['status'] in ('success', 'partial')
        assert answer['tool_calls'] == ['optimize']
        assert answer['result']['feasibility']['all_feasible'] is True
        assert answer['result']['installation_cost_gbp'] <= 7000
        assert answer['result']['energy']['net_savings_kwh'] > 0
        assert len(answer['result']['package_decisions']) == 32
    finally:
        repository.overrides = saved


def test_data_generators_reproduce_exact_files_from_other_directory(tmp_path):
    for script, args, source in [
        ('generate_properties.py', ['--output', str(tmp_path / 'properties.csv')], 'properties.csv'),
        ('generate_energy_usage.py', ['--output', str(tmp_path / 'energy_usage.csv')], 'energy_usage.csv')]:
        result = subprocess.run([sys.executable, str(ROOT / 'Data/scripts' / script), *args], cwd=tmp_path, capture_output=True, text=True)
        assert result.returncode == 0, result.stderr
        assert (tmp_path / source).read_bytes() == (ROOT / 'Data/csv' / source).read_bytes()
