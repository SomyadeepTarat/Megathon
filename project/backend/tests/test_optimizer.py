import json
from pathlib import Path

from app.schemas.models import ScenarioRequest
from app.services.adapters import ExistingValuationAdapter
from app.services.optimization import optimize_packages
from app.services.p4_adapter import P4CarbonAdapter, P4RetrofitAdapter


def request_fixture(**updates):
    data = json.loads((Path(__file__).resolve().parents[2] / 'docs/assessment-example.json').read_text())
    data['property'].update(property_id='OPTIMIZER1', solar_installed=False,
        heat_pump_installed=False, heat_pump_compatible=True, controls_compatible=True,
        roof_suitable_for_solar=True, roof_suitable_for_loft=True,
        loft_insulation_installed=False,
        physical_inputs={'thermal_demand_kwh': 8000, 'thermal_demand_scope': 'space_heating',
            'space_heating_demand_kwh': 8000, 'hot_water_demand_kwh': 0,
            'boiler_efficiency': .8, 'scop': 4,
            'proposed_solar_generation_kwh': 1000,
            'proposed_solar_self_consumed_kwh': 500,
            'provenance': {'status': 'TEST ONLY'}})
    data['emission_factors'] = {fuel: {'fuel': fuel, 'kg_co2e_per_kwh': factor,
        'source': 'TEST FIXTURE ONLY', 'source_year': 2026,
        'accounting_boundary': 'test boundary', 'version': 'test-only-v1'}
        for fuel, factor in [('electricity', .2), ('gas', .18)]}
    data.update(retrofits=[], objective='energy_reduction', budget_gbp=2000)
    data.update(updates)
    return ScenarioRequest.model_validate(data)


def engines():
    return P4RetrofitAdapter(), P4CarbonAdapter(), ExistingValuationAdapter()


def test_optimizer_evaluates_all_subsets_and_obeys_inclusive_budget():
    names = ['loft_insulation', 'heat_pump', 'solar_panels', 'double_glazing', 'smart_thermostat']
    costs = {name: {'amount_gbp': 1000, 'source': 'TEST ONLY', 'date': '2026-10-10'} for name in names}
    retrofit, carbon, valuation = engines()
    result = optimize_packages(request_fixture(retrofit_costs=costs), retrofit, carbon, valuation)
    assert result.status == 'available'
    assert len(result.package_decisions) == 32
    assert any(row['status'] == 'eligible' and row['cost_gbp'] == 2000 for row in result.package_decisions)
    assert any(row['status'] == 'rejected' and row['cost_gbp'] == 3000 for row in result.package_decisions)
    assert 'heat_pump' in result.ranked_packages[0].applied_retrofits
    assert result.ranked_packages[0].installation_cost_gbp <= 2000


def test_optimizer_marks_unknown_prices_unavailable_instead_of_free():
    retrofit, carbon, valuation = engines()
    result = optimize_packages(request_fixture(retrofit_costs={
        'heat_pump': {'amount_gbp': 1000, 'source': 'TEST ONLY', 'date': '2026-10-10'}}),
        retrofit, carbon, valuation)
    assert len(result.package_decisions) == 32
    assert any(row['status'] == 'unavailable' and 'cost missing' in row['reason']
               for row in result.package_decisions)


def test_payback_requires_both_tariffs_and_positive_savings():
    names = ['loft_insulation', 'heat_pump', 'solar_panels', 'double_glazing', 'smart_thermostat']
    costs = {name: {'amount_gbp': 1000, 'source': 'TEST ONLY', 'date': '2026-10-10'} for name in names}
    retrofit, carbon, valuation = engines()
    no_tariff = optimize_packages(request_fixture(objective='shortest_payback', retrofit_costs=costs),
                                  retrofit, carbon, valuation)
    assert no_tariff.status == 'unavailable'
    with_tariff = optimize_packages(request_fixture(objective='shortest_payback', retrofit_costs=costs,
        electricity_tariff_gbp_per_kwh=.2, gas_tariff_gbp_per_kwh=.1), retrofit, carbon, valuation)
    assert with_tariff.status == 'available'
    assert with_tariff.ranked_packages[0].simple_payback_years is not None


def test_tradeoffs_use_same_budget_and_preserve_objective():
    names = ['loft_insulation', 'heat_pump', 'solar_panels', 'double_glazing', 'smart_thermostat']
    costs = {name: {'amount_gbp': 1000, 'source': 'TEST ONLY', 'date': '2026-10-10'} for name in names}
    retrofit, carbon, valuation = engines()
    result = optimize_packages(request_fixture(retrofit_costs=costs, objective='carbon_reduction',
        electricity_tariff_gbp_per_kwh=.3, gas_tariff_gbp_per_kwh=.06), retrofit, carbon, valuation)
    context = result.best_scenario.optimization_context
    assert context.objective == 'carbon_reduction'
    assert all(row.installation_cost_gbp <= context.budget_gbp for row in context.alternatives)
    assert {row.objective for row in context.alternatives} == {'carbon_reduction', 'energy_reduction', 'shortest_payback'}
    selected = next(row for row in context.alternatives if row.objective == context.objective)
    assert selected.retrofits == result.best_scenario.applied_retrofits
    assert context.installation_order[-1] in ('heat_pump', 'solar_panels')
