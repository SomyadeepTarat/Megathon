"""Exhaustive, deterministic budget-constrained retrofit package search."""
from __future__ import annotations

from itertools import combinations

from carbon_engine.retrofit_catalogue import RETROFIT_CATALOGUE, SEQUENTIAL_ORDER
from app.schemas.engines import OptimizationResult, SimulationResult, OptimizationContext, PackageTradeoff
from app.schemas.models import ScenarioRequest
from app.services.orchestrator import run_scenario


def optimize_packages(request: ScenarioRequest, retrofit, carbon, valuation) -> OptimizationResult:
    """Enumerate all 32 subsets; only documented, feasible, affordable results rank."""
    objective = request.objective
    method = ("Enumerate all retrofit subsets against the same baseline; require known feasibility and "
              "documented per-measure costs within the budget; rank by the selected objective with "
              "cost and retrofit IDs as deterministic tie-breakers. No weighted score is used.")
    if request.budget_gbp is None:
        return OptimizationResult(status="unavailable", reason="A budget is required for constrained optimization.",
                                  objective=objective, methodology=method)
    measures = tuple(RETROFIT_CATALOGUE)
    decisions = []
    scored = []
    comparable = []
    for count in range(len(measures) + 1):
        for package in combinations(measures, count):
            label = list(package)
            if package:
                costs_missing = [m for m in package if m not in request.retrofit_costs]
                if costs_missing:
                    decisions.append({"retrofits": label, "status": "unavailable",
                                      "reason": "Documented installation cost missing for: " + ", ".join(costs_missing)})
                    continue
            cost = sum(request.retrofit_costs[m].amount_gbp for m in package)
            if cost > request.budget_gbp:
                decisions.append({"retrofits": label, "status": "rejected", "cost_gbp": cost,
                                  "reason": f"Package cost £{cost:g} exceeds budget £{request.budget_gbp:g}."})
                continue
            payload = request.model_dump(mode="python")
            payload["retrofits"] = label
            candidate = ScenarioRequest.model_validate(payload)
            result = run_scenario(candidate, retrofit, carbon, valuation)
            feasibility = {item.retrofit: item.status for item in result.feasibility.items}
            if result.status == "rejected":
                decisions.append({"retrofits": label, "status": "conditional" if "conditional" in feasibility.values() else "rejected",
                                  "cost_gbp": cost, "reason": result.reason,
                                  "feasibility": {item.retrofit: {"status": item.status, "reason": item.reason} for item in result.feasibility.items}})
                continue
            if result.energy is None:
                decisions.append({"retrofits": label, "status": "unavailable", "cost_gbp": cost,
                                  "reason": result.reason or "Fuel simulation unavailable."})
                continue
            comparable.append(result)
            if objective == "carbon_reduction":
                if result.carbon.status != "available":
                    decisions.append({"retrofits": label, "status": "unavailable", "cost_gbp": cost,
                                      "reason": result.carbon.reason or "Documented carbon factors are required."})
                    continue
                metric = result.carbon.reduction_kg_co2e
            elif objective == "energy_reduction":
                metric = result.energy.net_savings_kwh
            else:
                if result.simple_payback_years is None:
                    decisions.append({"retrofits": label, "status": "unavailable", "cost_gbp": cost,
                                      "reason": result.payback_reason or "Payback inputs are unavailable."})
                    continue
                metric = result.simple_payback_years
            decisions.append({"retrofits": label, "status": "eligible", "cost_gbp": cost,
                              "objective_value": metric, "reason": "Feasible, calculable, and within the supplied budget."})
            scored.append((metric, cost, label, result))
    if objective == "shortest_payback":
        scored.sort(key=lambda row: (row[0], row[1], row[2]))
    else:
        scored.sort(key=lambda row: (-row[0], row[1], row[2]))
    ranked = [SimulationResult(
        updated_property=row.updated_property,
        after=row.energy.after,
        applied_retrofits=row.applied_retrofits,
        installation_cost_gbp=row.installation_cost_gbp,
        methodology_version=row.versions.get("simulation", "p4-carbon-package-adapter-v1"),
        assumptions=row.assumptions, warnings=row.warnings,
        annual_bill_savings_gbp=row.annual_bill_savings_gbp,
        bill_savings_reason=row.bill_savings_reason,
        simple_payback_years=row.simple_payback_years,
        payback_reason=row.payback_reason,
    ) for _, _, _, row in scored]
    if not ranked:
        reason = "No package has enough documented inputs to satisfy the selected objective and budget."
        return OptimizationResult(status="unavailable", reason=reason, ranked_packages=[],
                                  package_decisions=decisions, objective=objective, methodology=method)
    best = scored[0][3]
    alternatives = []
    for choice in ('carbon_reduction', 'energy_reduction', 'shortest_payback'):
        eligible = [row for row in comparable if
                    (row.carbon.status == 'available' if choice == 'carbon_reduction' else
                     row.simple_payback_years is not None if choice == 'shortest_payback' else True)]
        if not eligible:
            continue
        def key(row):
            value = (row.carbon.reduction_kg_co2e if choice == 'carbon_reduction' else
                     row.energy.net_savings_kwh if choice == 'energy_reduction' else row.simple_payback_years)
            return (value if choice == 'shortest_payback' else -value,
                    row.installation_cost_gbp, row.applied_retrofits)
        winner = min(eligible, key=key)
        alternatives.append(PackageTradeoff(objective=choice, retrofits=winner.applied_retrofits,
            installation_cost_gbp=winner.installation_cost_gbp,
            carbon_reduction_kg_co2e=winner.carbon.reduction_kg_co2e,
            net_energy_savings_kwh=winner.energy.net_savings_kwh,
            annual_bill_savings_gbp=winner.annual_bill_savings_gbp,
            simple_payback_years=winner.simple_payback_years))
    descriptions = {'carbon_reduction': 'the greatest annual operational carbon reduction',
                    'energy_reduction': 'the greatest annual purchased-energy reduction',
                    'shortest_payback': 'the shortest simple payback among packages with positive bill savings'}
    explanation = ('This package provides ' + descriptions[objective] +
        ' among feasible, calculable packages within your budget. Ties prefer lower installation cost, then retrofit IDs. '
        'Carbon, energy and financial objectives can select different packages; compare the alternatives below. '
        'Simple payback excludes maintenance, financing, tariff changes and property-value impact.')
    best.optimization_context = OptimizationContext(objective=objective, budget_gbp=request.budget_gbp,
        explanation=explanation, alternatives=alternatives,
        installation_order=[measure for measure in SEQUENTIAL_ORDER if measure in best.applied_retrofits])
    return OptimizationResult(status="available", ranked_packages=ranked, best_scenario=best, package_decisions=decisions,
                              objective=objective, methodology=method)
