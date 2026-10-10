from app.schemas.models import ScenarioRequest
from app.schemas.engines import RecommendationResponse, RecommendationOption
from app.services.orchestrator import run_scenario
from carbon_engine.retrofit_catalogue import RETROFIT_CATALOGUE


def recommend(request, retrofit, carbon, valuation):
    ranked, other = [], []
    policy = ('High requires feasible eligibility, positive modeled objective benefit, and observed annual-energy plus '
              'physical-input provenance. Medium means benefit is calculable from synthetic/estimated inputs or eligibility '
              'is conditional. Low means explicit incompatibility/already-present or no positive objective benefit. '
              'Ranking position alone never sets suitability.')
    for measure in RETROFIT_CATALOGUE:
        data = request.model_dump(mode='json')
        data['retrofits'] = [measure]
        candidate = ScenarioRequest.model_validate(data)
        result = run_scenario(candidate, retrofit, carbon, valuation)
        feasibility = result.feasibility.items[0]
        benefit = (result.energy is not None and
                   (result.carbon.reduction_kg_co2e is not None and result.carbon.reduction_kg_co2e > 0 if request.objective == 'carbon_reduction' else
                    result.energy.net_savings_kwh > 0 if request.objective == 'energy_reduction' else
                    result.simple_payback_years is not None))
        physical = request.property.physical_inputs
        physical_observed = physical.provenance.get('status') == 'observed'
        observed = request.annual_energy.quality == 'observed' and physical_observed
        if feasibility.status == 'infeasible' or (result.energy is not None and not benefit):
            suitability = 'Low'
            suitability_reason = 'The measure is already present/incompatible or does not produce positive benefit for the selected objective.'
        elif feasibility.status == 'conditional':
            suitability = 'Medium'
            suitability_reason = 'Eligibility is conditional and requires confirmation before installation.'
        elif benefit and observed:
            suitability = 'High'
            suitability_reason = 'Eligibility is confirmed and positive modeled benefit uses observed annual-energy and physical-input provenance.'
        else:
            suitability = 'Medium'
            suitability_reason = 'The result is a screening estimate based on synthetic/estimated inputs or lacks objective evidence.'
        option = RecommendationOption(retrofit=measure, feasibility=feasibility, scenario=result,
                                      suitability=suitability, suitability_reason=suitability_reason,
                                      estimated_cost_gbp=result.installation_cost_gbp)
        calculable_for_objective = (
            request.objective == 'energy_reduction' and result.energy is not None or
            request.objective == 'carbon_reduction' and result.energy is not None and result.carbon.status == 'available' or
            request.objective == 'shortest_payback' and result.simple_payback_years is not None
        )
        if calculable_for_objective and option.feasibility.status == 'feasible':
            ranked.append(option)
        else:
            other.append(option)
    if request.objective == 'shortest_payback':
        ranked.sort(key=lambda option: (option.scenario.simple_payback_years, option.retrofit))
    elif request.objective == 'carbon_reduction':
        ranked.sort(key=lambda option: (-option.scenario.carbon.reduction_kg_co2e, option.retrofit))
    else:
        ranked.sort(key=lambda option: (-option.scenario.energy.net_savings_kwh, option.retrofit))
    for priority, option in enumerate(ranked, 1):
        option.priority = priority
    return RecommendationResponse(property_id=request.property.property_id,
        status='partial' if ranked and other else 'available' if ranked else 'unavailable',
        recommendations=ranked, other_options=other,
        methodology='Individual feasible options simulated by P4; interactions require a selected package simulation. Suitability policy: ' + policy,
        warnings=['This ranks individual measures, not budget-optimized packages.'] +
                 (['Options without all required objective inputs remain in other_options.'] if other else []))
