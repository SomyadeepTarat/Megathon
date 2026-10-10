"""Translate the real P1 contracts for the P2 advisor; never fabricate engine outputs."""
from __future__ import annotations

import asyncio

from app.core.efficiency import assess
from app.schemas.models import AssessmentRequest, ScenarioRequest
from app.services.orchestrator import run_scenario
from app.services.llm_service import EngineUnavailable, PropertyNotFound


def feasibility_view(value, requested):
    items = value.items
    complete = {item.retrofit for item in items} == set(requested)
    return {
        'status': value.status,
        'all_feasible': value.status == 'available' and complete and all(item.status == 'feasible' for item in items),
        'rejected_retrofits': [item.retrofit for item in items if item.status == 'infeasible'],
        'conditional_retrofits': [item.retrofit for item in items if item.status == 'conditional'],
        'items': [item.model_dump(mode='json') for item in items], 'reason': value.reason,
    }


def assessment_view(value):
    score = value.score.model_dump(mode='json')
    score['baseline'] = score.pop('score')
    return {
        'property_id': value.property_id,
        'status': 'success' if value.score.status == 'available' else 'partial',
        'score': score,
        'issues': [issue.message for issue in value.issues],
        'warnings': list(value.warnings),
    }


def scenario_view(value, requested):
    """Preserve partial estimates; this translates fields without recomputing numbers."""
    result = assessment_view(value.baseline_assessment)
    result.update(status=value.status, scenario_id=value.scenario_id, reason=value.reason,
                  feasibility=feasibility_view(value.feasibility, requested),
                  carbon=value.carbon.model_dump(mode='json'),
                  valuation=value.valuation.model_dump(mode='json'),
                  assumptions=list(value.assumptions), warnings=list(value.warnings),
                  installation_cost_gbp=value.installation_cost_gbp,
                  applied_retrofits=list(value.applied_retrofits), versions=value.versions)
    if value.after_assessment:
        result['score']['after'] = value.after_assessment.score.score
        result['score']['after_status'] = value.after_assessment.score.status
        result['score']['after_components'] = [c.model_dump(mode='json') for c in value.after_assessment.score.components]
    if value.energy:
        energy = value.energy
        result['energy'] = {
            'baseline_electricity_kwh': energy.baseline.electricity_kwh,
            'baseline_gas_kwh': energy.baseline.gas_kwh,
            'after_electricity_kwh': energy.after.electricity_kwh,
            'after_gas_kwh': energy.after.gas_kwh,
            'electricity_savings_kwh': energy.electricity_savings_kwh,
            'gas_savings_kwh': energy.gas_savings_kwh,
            'net_savings_kwh': energy.net_savings_kwh,
            'improvement_percentage': energy.improvement_percentage,
        }
    return result


class BackendAdvisorEngines:
    """Getters keep the advisor aligned with the application's configured dependencies."""
    def __init__(self, repository, retrofit, carbon, valuation):
        self.repository, self.retrofit, self.carbon, self.valuation = repository, retrofit, carbon, valuation

    def _record(self, property_id):
        try:
            return self.repository().load_property(property_id)
        except KeyError:
            raise PropertyNotFound() from None

    def _request(self, property_id, retrofits, budget=None, objective='carbon_reduction'):
        row = self._record(property_id)
        return ScenarioRequest(property=row.property, annual_energy=row.annual_energy,
                               benchmark=row.benchmark, retrofits=retrofits,
                               budget_gbp=budget, objective=objective)

    async def assessment(self, property_id):
        def execute():
            row = self._record(property_id)
            value = assess(AssessmentRequest(property=row.property, annual_energy=row.annual_energy,
                                             benchmark=row.benchmark))
            result = assessment_view(value)
            result['energy'] = {'baseline_electricity_kwh': row.annual_energy.electricity_kwh,
                                'baseline_gas_kwh': row.annual_energy.gas_kwh}
            result['sources'] = [f'Property dataset: {row.dataset_kind}; {row.dataset_source}',
                                 f'Annual energy: {row.annual_energy.quality}; {row.annual_energy.method}']
            if row.benchmark:
                result['sources'].append(row.benchmark.source)
            return result
        return await asyncio.to_thread(execute)

    async def feasibility(self, property_id, retrofits):
        def execute():
            value = self.retrofit().check_feasibility(self._request(property_id, retrofits))
            if value.status == 'unavailable':
                raise EngineUnavailable(value.reason)
            return feasibility_view(value, retrofits)
        return await asyncio.to_thread(execute)

    async def simulate(self, property_id, retrofits, budget_gbp, objective):
        def execute():
            request = self._request(property_id, retrofits, budget_gbp, objective)
            value = run_scenario(request, self.retrofit(), self.carbon(), self.valuation())
            result = scenario_view(value, retrofits)
            row = self._record(property_id)
            result['sources'] = [f'Property dataset: {row.dataset_kind}; {row.dataset_source}',
                                 f'Baseline energy: {row.annual_energy.quality}; {row.annual_energy.method}']
            result['sources'].extend(f'{factor.source} ({factor.source_year}); {factor.accounting_boundary}'
                                     for factor in value.carbon.factors)
            return result
        return await asyncio.to_thread(execute)

    async def optimize(self, property_id, budget_gbp, objective):
        # P1's OptimizationResult contains ranked simulation outputs but no full selected
        # ScenarioResponse. Until its objective/selection contract is wired, fail honestly.
        await asyncio.to_thread(self._record, property_id)
        raise EngineUnavailable('Budget optimization is not integrated with the application.')
