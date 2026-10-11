from app.schemas.models import ScenarioRequest
from app.schemas.engines import RecommendationResponse, RecommendationOption
from app.services.orchestrator import run_scenario
from carbon_engine.retrofit_catalogue import RETROFIT_CATALOGUE, SEQUENTIAL_ORDER


def recommend(request, retrofit, carbon, valuation, *, excluded_retrofits=(), excluded_packages=()):
    ranked, other = [], []
    policy = ('High requires feasible eligibility, positive modeled objective benefit, and observed annual-energy plus '
              'physical-input provenance. Medium means benefit is calculable from synthetic/estimated inputs or eligibility '
              'is conditional. Low means explicit incompatibility/already-present or no positive objective benefit. '
              'Ranking position alone never sets suitability.')
    for measure in RETROFIT_CATALOGUE:
        if measure in excluded_retrofits or any(set(package) == {measure} for package in excluded_packages):
            continue
        data = request.model_dump(mode='json', exclude={'scenario_id'})
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
        calculable_for_objective = (
            request.objective == 'energy_reduction' and result.energy is not None and result.energy.improvement_percentage is not None or
            request.objective == 'carbon_reduction' and result.energy is not None and result.carbon.status == 'available' or
            request.objective == 'shortest_payback' and result.simple_payback_years is not None
        )
        if feasibility.status == 'infeasible' or (calculable_for_objective and not benefit):
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
        if feasibility.status != 'feasible':
            ranking_reason = feasibility.reason
        elif result.energy is None:
            ranking_reason = result.reason or 'Energy simulation is unavailable.'
        elif not calculable_for_objective:
            ranking_reason = ('Percentage improvement is unavailable because baseline purchased energy is zero.' if request.objective == 'energy_reduction' else
                              result.carbon.reason if request.objective == 'carbon_reduction' else result.payback_reason)
        elif not benefit:
            ranking_reason = 'No positive calculated benefit for the selected objective; excluded from recommendations.'
        else:
            ranking_reason = ('Ranked by calculated purchased-energy reduction of ' + f'{result.energy.improvement_percentage:.2f}%.' if request.objective == 'energy_reduction' else
                              'Ranked by calculated annual carbon reduction.' if request.objective == 'carbon_reduction' else 'Ranked by calculated shortest positive simple payback.')
        option = RecommendationOption(retrofit=measure, feasibility=feasibility, scenario=result,
                                      suitability=suitability, suitability_reason=suitability_reason,
                                      ranking_reason=ranking_reason,
                                      estimated_cost_gbp=result.installation_cost_gbp)
        if calculable_for_objective and benefit and option.feasibility.status == 'feasible':
            ranked.append(option)
        else:
            other.append(option)
    if request.objective == 'shortest_payback':
        ranked.sort(key=lambda option: (option.scenario.simple_payback_years, option.retrofit))
    elif request.objective == 'carbon_reduction':
        ranked.sort(key=lambda option: (-option.scenario.carbon.reduction_kg_co2e, option.retrofit))
    else:
        ranked.sort(key=lambda option: (-option.scenario.energy.improvement_percentage, option.retrofit))
    for priority, option in enumerate(ranked, 1):
        option.priority = priority
    return RecommendationResponse(property_id=request.property.property_id,
        objective=request.objective,
        installation_order=[measure for measure in SEQUENTIAL_ORDER if any(option.retrofit == measure for option in ranked)],
        status='partial' if ranked and other else 'available' if ranked else 'unavailable',
        recommendations=ranked, other_options=other,
        methodology='Individual feasible options simulated against the same baseline; energy ranking uses 100 * (baseline purchased electricity + gas - after purchased electricity - gas) / baseline purchased energy. Other explicit objectives use carbon reduction or shortest positive payback. Suitability policy: ' + policy,
        warnings=['This ranks individual measures, not budget-optimized packages.',
                  'Installation order is separate from benefit rank: demand reduction before heat-pump sizing/installation, then solar. Confirm dependencies with an installer; combined outcomes require package simulation, not addition of individual savings.'] +
                 (['Conditional, incompatible, unavailable and non-beneficial options remain in other_options with reasons.'] if other else []))
