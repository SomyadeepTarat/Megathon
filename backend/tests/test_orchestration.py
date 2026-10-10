from copy import deepcopy
import json
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from app.main import app, get_retrofit_engine, get_carbon_engine, get_valuation_engine
from app.schemas.models import ScenarioRequest, Heating
from app.schemas.engines import (FeasibilityResult, FeasibilityItem, SimulationResult, FuelState,
                                CarbonResult, EmissionFactor, ValuationResult, EnergyImpact)
from app.services.adapters import PendingCarbonEngine, ExistingValuationAdapter
from app.services.orchestrator import run_scenario, EngineContractError


@pytest.fixture
def request_data():
    row = json.loads((Path(__file__).resolve().parents[1] / 'data/demo_properties.json').read_text())[0]
    row.pop('dataset_kind')
    row.pop('dataset_source')
    row['benchmark'] = {'property_type': 'detached', 'intensity_kwh_m2_year': 140,
                        'source': 'TEST ONLY', 'methodology': 'Synthetic test fixture'}
    row['retrofits'] = ['heat_pump']
    row['budget_gbp'] = 10000
    return row


class TestRetrofitAdapter:
    __test__ = False
    version = 'test-only-v1'
    def __init__(self, status='feasible', after=None, cost=7000):
        self.status, self.after, self.cost = status, after, cost
        self.called = False

    def check_feasibility(self, request):
        return FeasibilityResult(status='available', items=[FeasibilityItem(
            retrofit=item, status=self.status, reason='Test reference') for item in request.retrofits])

    def simulate_retrofits(self, request):
        self.called = True
        updated = request.property.model_copy(deep=True)
        if 'heat_pump' in request.retrofits:
            updated.heating_system = Heating.AIR_HEAT_PUMP
        return SimulationResult(updated_property=updated,
            after=self.after or FuelState(electricity_kwh=6000, gas_kwh=3000),
            applied_retrofits=request.retrofits, installation_cost_gbp=self.cost,
            methodology_version=self.version, assumptions=['Test-only fuel values'])


class TestValuationAdapter:
    __test__ = False
    def predict_value_impact(self, baseline, scenario):
        return ValuationResult(status='unavailable', reason='Test: no calibrated model')


class TestCarbonAdapter:
    __test__ = False
    def calculate_carbon(self, energy):
        factors = [EmissionFactor(fuel=fuel, kg_co2e_per_kwh=value, source='TEST ONLY',
                    source_year=2026, accounting_boundary='Synthetic test boundary')
                   for fuel, value in [('electricity', .2), ('gas', .3)]]
        return CarbonResult(status='available', factors=factors,
            reduction_kg_co2e=energy.electricity_savings_kwh*.2 + energy.gas_savings_kwh*.3)


def test_heat_pump_integration(request_data):
    original = deepcopy(request_data)
    result = run_scenario(ScenarioRequest.model_validate(request_data), TestRetrofitAdapter(),
                          TestCarbonAdapter(), TestValuationAdapter())
    assert result.status == 'partial'
    assert result.energy.electricity_savings_kwh == -1200
    assert result.energy.gas_savings_kwh == 9000
    assert result.energy.net_savings_kwh == 7800
    assert result.carbon.reduction_kg_co2e == 2460
    assert result.updated_property.heating_system == 'air_source_heat_pump'
    assert result.updated_property.energy_rating == 'E'
    heating = next(x for x in result.after_assessment.score.components if x.name == 'heating_system')
    assert heating.subscore == 90
    assert request_data == original
    assert result.valuation.status == 'unavailable'


@pytest.mark.parametrize('status', ['conditional', 'infeasible'])
def test_rejected_packages_are_not_simulated(request_data, status):
    engine = TestRetrofitAdapter(status=status)
    result = run_scenario(ScenarioRequest.model_validate(request_data), engine,
                          TestCarbonAdapter(), TestValuationAdapter())
    assert result.status == 'rejected'
    assert result.energy is None
    assert not engine.called


def test_missing_energy_prevents_simulation(request_data):
    request_data['annual_energy']['gas_kwh'] = None
    engine = TestRetrofitAdapter()
    result = run_scenario(ScenarioRequest.model_validate(request_data), engine,
                          TestCarbonAdapter(), TestValuationAdapter())
    assert result.status == 'unavailable'
    assert not engine.called


def test_budget_rejection_has_no_applied_outputs(request_data):
    request_data['budget_gbp'] = 100
    result = run_scenario(ScenarioRequest.model_validate(request_data), TestRetrofitAdapter(),
                          TestCarbonAdapter(), TestValuationAdapter())
    assert result.status == 'rejected'
    assert result.energy is None
    assert result.applied_retrofits == []


def test_zero_baseline(request_data):
    request_data['annual_energy'].update(electricity_kwh=0, gas_kwh=0)
    engine = TestRetrofitAdapter(after=FuelState(electricity_kwh=0, gas_kwh=0))
    result = run_scenario(ScenarioRequest.model_validate(request_data), engine,
                          PendingCarbonEngine(), TestValuationAdapter())
    assert result.energy.improvement_percentage is None
    assert result.carbon.status == 'unavailable'


def test_noop_package(request_data):
    request_data['retrofits'] = []
    engine = TestRetrofitAdapter(after=FuelState(electricity_kwh=4800, gas_kwh=12000), cost=0)
    result = run_scenario(ScenarioRequest.model_validate(request_data), engine,
                          TestCarbonAdapter(), TestValuationAdapter())
    assert result.energy.net_savings_kwh == 0
    assert result.after_assessment.score.score == result.baseline_assessment.score.score


def test_contract_blocks_changed_epc(request_data):
    class InvalidEngine(TestRetrofitAdapter):
        def simulate_retrofits(self, request):
            result = super().simulate_retrofits(request)
            result.updated_property.energy_rating = 'A'
            return result
    with pytest.raises(EngineContractError, match='energy_rating'):
        run_scenario(ScenarioRequest.model_validate(request_data), InvalidEngine(),
                     TestCarbonAdapter(), TestValuationAdapter())


def test_incomplete_feasibility_rejected(request_data):
    class InvalidEngine(TestRetrofitAdapter):
        def check_feasibility(self, request):
            return FeasibilityResult(status='available', items=[])
    with pytest.raises(EngineContractError, match='cover exactly'):
        run_scenario(ScenarioRequest.model_validate(request_data), InvalidEngine(),
                     TestCarbonAdapter(), TestValuationAdapter())


def test_carbon_consistency(request_data):
    class InvalidCarbon(TestCarbonAdapter):
        def calculate_carbon(self, energy):
            result = super().calculate_carbon(energy)
            result.reduction_kg_co2e = 99
            return result
    with pytest.raises(EngineContractError, match='Carbon result'):
        run_scenario(ScenarioRequest.model_validate(request_data), TestRetrofitAdapter(),
                     InvalidCarbon(), TestValuationAdapter())


def test_mutating_adapter_cannot_change_baseline(request_data):
    class MutatingEngine(TestRetrofitAdapter):
        def check_feasibility(self, request):
            result = super().check_feasibility(request)
            request.property.energy_rating = 'A'
            request.annual_energy.gas_kwh = 0
            return result
    request = ScenarioRequest.model_validate(request_data)
    original = request.model_dump()
    result = run_scenario(request, MutatingEngine(), TestCarbonAdapter(), TestValuationAdapter())
    assert request.model_dump() == original
    assert result.baseline_assessment.score.score == 33
    assert result.energy.baseline.gas_kwh == 12000


def test_property_routes():
    client = TestClient(app)
    listing = client.get('/properties')
    assert listing.status_code == 200
    assert len(listing.json()) == 100
    assert all(row['dataset_kind'] == 'synthetic' for row in listing.json())
    detail = client.get('/properties/P00001').json()
    assert detail['benchmark'] is None
    assert detail['annual_energy']['quality'] == 'synthetic'
    assert client.get('/properties/P00001/assessment').json()['score']['status'] == 'unavailable'
    assert client.get('/properties/missing').status_code == 404
    assert client.get('/properties/missing/assessment').status_code == 404
    detail['property']['energy_rating'] = 'A'
    assert client.get('/properties/P00001').json()['property']['energy_rating'] == 'F'


def test_injected_route(request_data):
    app.dependency_overrides[get_retrofit_engine] = lambda: TestRetrofitAdapter()
    app.dependency_overrides[get_carbon_engine] = lambda: TestCarbonAdapter()
    app.dependency_overrides[get_valuation_engine] = lambda: TestValuationAdapter()
    try:
        client = TestClient(app)
        response = client.post('/scenarios/simulate', json=request_data)
        assert response.status_code == 200
        assert response.json()['energy']['electricity_savings_kwh'] == -1200
        app.dependency_overrides[get_retrofit_engine] = lambda: TestRetrofitAdapter(status='infeasible')
        assert client.post('/scenarios/simulate', json=request_data).status_code == 409
    finally:
        app.dependency_overrides.clear()


def test_valuation_field_translation(request_data):
    prop = ScenarioRequest.model_validate(request_data).property
    row = ExistingValuationAdapter.to_features(prop)
    assert row['floor_area'] == prop.floor_area_m2
    assert row['age'] == prop.property_age_years
    assert row['energy_rating'] == prop.energy_rating
    result = ExistingValuationAdapter().predict_value_impact(prop, prop)
    assert result.status == 'unavailable'


def test_output_contracts_reject_inconsistent_values():
    with pytest.raises(ValidationError):
        EnergyImpact(baseline=FuelState(electricity_kwh=10, gas_kwh=0),
                     after=FuelState(electricity_kwh=5, gas_kwh=0), electricity_savings_kwh=99,
                     gas_savings_kwh=0, net_savings_kwh=99, improvement_percentage=50)
    with pytest.raises(ValidationError):
        CarbonResult(status='available', reduction_kg_co2e=100)
    with pytest.raises(ValidationError):
        ValuationResult(status='unavailable', reason='Missing model', baseline_value_gbp=100)
