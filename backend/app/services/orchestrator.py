from app.services.valuation_inputs import impact_input_reason
import math
from uuid import uuid4
from app.core.efficiency import assess
from app.schemas.models import AssessmentRequest, AnnualEnergy, ScenarioRequest
from app.schemas.engines import (ScenarioResponse, FuelState, EnergyImpact, CarbonResult,
                                ValuationResult)
from app.services.p4_adapter import CalculationUnavailable
from app.services.contracts import RetrofitEngine, CarbonEngine, ValuationEngine


class EngineContractError(RuntimeError):
    pass


def run_scenario(request: ScenarioRequest, retrofit: RetrofitEngine,
                 carbon: CarbonEngine, valuation: ValuationEngine) -> ScenarioResponse:

    original = request.model_copy(deep=True)
    baseline = assess(original)
    response = ScenarioResponse(
        scenario_id=str(uuid4()), property_id=original.property.property_id,
        status='unavailable', baseline_assessment=baseline,
        feasibility=retrofit.check_feasibility(original.model_copy(deep=True)),
        carbon=CarbonResult(status='unavailable', reason='No completed scenario.'),
        valuation=ValuationResult(status='unavailable', reason='No completed scenario.'),
        versions={'score': baseline.score.methodology_version, 'retrofit': retrofit.version},
    )
    feasibility = response.feasibility
    if feasibility.status == 'unavailable':
        response.reason = feasibility.reason
        return response
    if {x.retrofit for x in feasibility.items} != set(original.retrofits):
        raise EngineContractError('Feasibility must cover exactly the requested measures')
    blocked = [item for item in feasibility.items if item.status != 'feasible']
    if blocked:
        response.status = 'rejected'
        response.reason = 'Package contains infeasible or conditional measures; resolve conditions before simulation.'
        return response
    energy = original.annual_energy
    if energy.electricity_kwh is None or energy.gas_kwh is None:
        response.reason = 'Both baseline fuel values are required for simulation.'
        return response
    try:
        result = retrofit.simulate_retrofits(original.model_copy(deep=True))
    except CalculationUnavailable as exc:
        response.reason = str(exc)
        return response
    if len(result.applied_retrofits) != len(set(result.applied_retrofits)) or set(result.applied_retrofits) != set(original.retrofits):
        raise EngineContractError('Simulation must apply exactly the requested measures')

    for field in ['property_id', 'property_type', 'region', 'floor_area_m2',
                  'property_age_years', 'bedrooms', 'market_index', 'energy_rating',
                  'current_property_value_gbp']:
        if getattr(result.updated_property, field) != getattr(original.property, field):
            raise EngineContractError(f'Simulation changed protected baseline field: {field}')
    if original.budget_gbp is not None and result.installation_cost_gbp is None:
        response.reason = 'Budget validation requires documented installation costs.'
        return response
    if original.budget_gbp is not None and result.installation_cost_gbp > original.budget_gbp:
        response.status = 'rejected'
        response.reason = 'Selected package exceeds the requested budget.'
        return response
    before = FuelState(electricity_kwh=energy.electricity_kwh, gas_kwh=energy.gas_kwh)
    e = before.electricity_kwh - result.after.electricity_kwh
    g = before.gas_kwh - result.after.gas_kwh
    total = before.electricity_kwh + before.gas_kwh
    impact = EnergyImpact(baseline=before, after=result.after,
                          electricity_savings_kwh=e, gas_savings_kwh=g, net_savings_kwh=e+g,
                          improvement_percentage=100*(e+g)/total if total else None)
    response.energy = impact
    response.updated_property = result.updated_property
    response.after_assessment = assess(AssessmentRequest(
        property=result.updated_property,
        annual_energy=AnnualEnergy(**result.after.model_dump(), quality='estimated',
                                   method=result.methodology_version,
                                   electricity_months_covered=12, gas_months_covered=12,
                                   warnings=result.warnings),
        benchmark=original.benchmark))
    carbon_result = carbon.calculate_carbon(impact.model_copy(deep=True))
    if carbon_result.status == 'available':
        factors = {f.fuel: f.kg_co2e_per_kwh for f in carbon_result.factors}
        expected = e*factors['electricity'] + g*factors['gas']
        if not math.isclose(carbon_result.reduction_kg_co2e, expected, abs_tol=1e-7, rel_tol=1e-9):
            raise EngineContractError('Carbon result disagrees with fuel changes and factors')
    response.carbon = carbon_result
    input_reason = impact_input_reason(original.property, result.updated_property)
    if input_reason:
        response.valuation = ValuationResult(status='unavailable', reason=input_reason)
    elif original.property.model_dump() != result.updated_property.model_dump() and original.property.energy_rating == result.updated_property.energy_rating:
        response.valuation = ValuationResult(status='unavailable', reason='No supported projected EPC estimate; the existing valuation model uses recorded EPC as its energy feature.')
    else:
        response.valuation = valuation.predict_value_impact(original.property.model_copy(deep=True),
                                                           result.updated_property.model_copy(deep=True))
    if hasattr(carbon, 'baseline'):
        response.baseline_carbon = carbon.baseline(original)
        if response.baseline_carbon.get('status') == 'available' and carbon_result.status == 'available':
            factors = {factor.fuel: factor.kg_co2e_per_kwh for factor in carbon_result.factors}
            after_e = impact.after.electricity_kwh * factors['electricity']
            after_g = impact.after.gas_kwh * factors['gas']
            response.after_carbon = {
                'status': 'available', 'electricity_kg_co2e': after_e,
                'gas_kg_co2e': after_g, 'total_kg_co2e': after_e + after_g,
                'factors': [factor.model_dump(mode='json') for factor in carbon_result.factors],
            }
            response.carbon_savings_by_fuel_kg_co2e = {
                'electricity': e * factors['electricity'],
                'gas': g * factors['gas'],
            }
    response.installation_cost_gbp = result.installation_cost_gbp
    response.annual_bill_savings_gbp = result.annual_bill_savings_gbp
    response.bill_savings_reason = result.bill_savings_reason
    response.simple_payback_years = result.simple_payback_years
    response.payback_reason = result.payback_reason
    response.applied_retrofits = result.applied_retrofits
    response.assumptions = result.assumptions
    response.warnings = list(baseline.warnings) + result.warnings
    response.versions['simulation'] = result.methodology_version
    response.status = 'success' if (response.after_assessment.score.status == 'available'
                                  and response.carbon.status == 'available'
                                  and response.valuation.status == 'indicative') else 'partial'
    return response
