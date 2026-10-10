import type { AdvisorResult } from './types.ts';

export const pendingPreview = {
  notice: 'Dummy preview — fixed sample values for unfinished features, not calculated for this property.',
  annual_bill_savings_gbp: 420,
  simple_payback_years: 3.5,
  value_change_gbp: 12000,
  value_change_range_gbp: [7000, 18000] as [number, number],
  improvement_percentage: 25,
  carbon_reduction_kg_co2e: 900,
};

export function budgetPreview(budget: number | null): AdvisorResult {
  return {
    status: 'unavailable', mode: 'deterministic', fallback_reason: 'Budget optimizer integration pending.',
    explanation: `${pendingPreview.notice} A sample planner package is loft insulation plus a smart thermostat. Your entered budget is £${budget ?? 0}. This package has not been optimized or checked against that budget.`,
    tool_calls: [], result: { preview: true, sample_package: ['loft_insulation', 'smart_thermostat'] },
    intent: { intent: 'optimize_budget', retrofits: [], budget_gbp: budget, objective: 'carbon_reduction' },
  };
}
