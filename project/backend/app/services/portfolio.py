"""Rank only calculable, confirmed complete retrofit packages; unknowns stay null."""
from app.core.efficiency import assess
from app.schemas.models import ScenarioRequest
from app.schemas.engines import PortfolioEntry
from app.services.orchestrator import run_scenario
from carbon_engine.retrofit_catalogue import RETROFIT_CATALOGUE


def rank_portfolio(repository, retrofit, carbon, valuation):
    rows = []
    for record in repository.list_properties():
        baseline = assess(record)
        request = ScenarioRequest(**record.model_dump(exclude={'dataset_kind', 'dataset_source'}),
                                  retrofits=list(RETROFIT_CATALOGUE))
        feasibility = retrofit.check_feasibility(request)
        reason = None
        scenario = None
        if feasibility.status != 'available' or any(item.status == 'conditional' for item in feasibility.items):
            reason = 'Complete feasible package is unknown; confirm eligibility before ranking potential.'
        else:
            request.retrofits = [item.retrofit for item in feasibility.items if item.status == 'feasible']
            from app.services.p4_adapter import P4CarbonAdapter
            provider = P4CarbonAdapter(record.emission_factors) if isinstance(carbon, P4CarbonAdapter) else carbon
            scenario = run_scenario(request, retrofit, provider, valuation)
            if scenario.energy is None or scenario.energy.improvement_percentage is None:
                reason = scenario.reason or 'Baseline energy is zero or unknown.'
        rows.append(PortfolioEntry(property_id=record.property.property_id, property_type=record.property.property_type,
            region=record.property.region, dataset_kind=record.dataset_kind,
            score=baseline.score.score, intensity=baseline.intensity_kwh_m2_year, classification=baseline.score.classification,
            improvement=scenario.energy.improvement_percentage if scenario and scenario.energy and reason is None else None,
            carbon=scenario.carbon.reduction_kg_co2e if scenario and scenario.carbon.status == 'available' else None,
            reason=reason, poor_home=baseline.poor_home,
            issues=[issue.message for issue in baseline.issues],
            current_property_value_gbp=record.property.current_property_value_gbp,
            electricity_savings_kwh=scenario.energy.electricity_savings_kwh if scenario and scenario.energy and reason is None else None,
            gas_savings_kwh=scenario.energy.gas_savings_kwh if scenario and scenario.energy and reason is None else None,
            feasible_retrofits=request.retrofits if scenario and reason is None else []))
    rows.sort(key=lambda row: (row.improvement is None, -(row.improvement or 0), row.property_id))
    previous = None
    rank = None
    for position, row in enumerate(rows, 1):
        if row.improvement is not None:
            if row.improvement != previous:
                rank = position
            row.rank = rank
            previous = row.improvement
    return rows
