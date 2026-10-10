from app.schemas.models import ScenarioRequest
from app.schemas.engines import RecommendationResponse, RecommendationOption
from app.services.orchestrator import run_scenario
from carbon_engine.retrofit_catalogue import RETROFIT_CATALOGUE


def recommend(request, retrofit, carbon, valuation):
    ranked, other = [], []
    for measure in RETROFIT_CATALOGUE:
        data = request.model_dump(mode='json')
        data['retrofits'] = [measure]
        candidate = ScenarioRequest.model_validate(data)
        result = run_scenario(candidate, retrofit, carbon, valuation)
        option = RecommendationOption(retrofit=measure, feasibility=result.feasibility.items[0], scenario=result)
        if result.energy is not None and option.feasibility.status == 'feasible':
            ranked.append(option)
        else:
            other.append(option)
    if request.objective == 'shortest_payback':
        other.extend(ranked)
        ranked = []
    elif request.objective == 'carbon_reduction':
        ranked.sort(key=lambda option: (-(option.scenario.carbon.reduction_kg_co2e or 0), option.retrofit))
    else:
        ranked.sort(key=lambda option: (-option.scenario.energy.net_savings_kwh, option.retrofit))
    return RecommendationResponse(property_id=request.property.property_id,
        status='partial' if ranked and other else 'available' if ranked else 'unavailable',
        recommendations=ranked, other_options=other,
        methodology='Individual feasible options simulated by P4; interactions require a selected package simulation.',
        warnings=['This ranks individual measures, not budget-optimized packages.'] +
                 (['Shortest payback is unavailable without tariffs and documented costs.'] if request.objective == 'shortest_payback' else []))
