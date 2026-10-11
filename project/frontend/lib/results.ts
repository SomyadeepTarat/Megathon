import type { AdvisorResult, Scenario } from './types.ts';

export interface OutputSnapshot {
  notes: string[]; id: string; propertyId: string; status: string; upgrades: string[];
  beforeScore: number | null; afterScore: number | null; beforeClass: string | null; afterClass: string | null;
  beforeElectricity: number | null; afterElectricity: number | null; beforeGas: number | null; afterGas: number | null;
  electricitySavings: number | null; gasSavings: number | null; energySavings: number | null; improvement: number | null;
  carbonReduction: number | null; cost: number | null; billSavings: number | null; payback: number | null;
  valueStatus: string; valueReason: string | null; baselineValue: number | null; valueRange: [number, number] | null;
}
const finite = (value: unknown): number | null => typeof value === 'number' && Number.isFinite(value) ? value : null;
const object = (value: unknown): Record<string, unknown> => value !== null && typeof value === 'object' ? value as Record<string, unknown> : {};
const string = (value: unknown): string | null => typeof value === 'string' ? value : null;
function range(value: unknown): [number, number] | null {
  return Array.isArray(value) && value.length === 2 && finite(value[0]) !== null && finite(value[1]) !== null ? [value[0], value[1]] : null;
}
export function scenarioOutput(value: Scenario): OutputSnapshot {
  return {
    notes: [...value.assumptions, ...value.warnings, ...value.feasibility.items.map((item) => `${item.retrofit}: ${item.status} — ${item.reason}`)], id: value.scenario_id, propertyId: value.property_id, status: value.status, upgrades: value.applied_retrofits,
    beforeScore: finite(value.baseline_assessment.score.score), afterScore: finite(value.after_assessment?.score.score),
    beforeClass: value.baseline_assessment.score.classification, afterClass: value.after_assessment?.score.classification ?? null,
    beforeElectricity: finite(value.energy?.baseline.electricity_kwh), afterElectricity: finite(value.energy?.after.electricity_kwh),
    beforeGas: finite(value.energy?.baseline.gas_kwh), afterGas: finite(value.energy?.after.gas_kwh),
    electricitySavings: finite(value.energy?.electricity_savings_kwh), gasSavings: finite(value.energy?.gas_savings_kwh),
    energySavings: finite(value.energy?.net_savings_kwh), improvement: finite(value.energy?.improvement_percentage),
    carbonReduction: value.carbon.status === 'available' ? finite(value.carbon.reduction_kg_co2e) : null,
    cost: finite(value.installation_cost_gbp), billSavings: finite(value.annual_bill_savings_gbp), payback: finite(value.simple_payback_years),
    valueStatus: value.valuation.status, valueReason: value.valuation.reason, baselineValue: finite(value.valuation.baseline_value_gbp),
    valueRange: value.valuation.status === 'unavailable' ? null : range(value.valuation.value_change_range_gbp),
  };
}
export function advisorOutput(value: AdvisorResult): OutputSnapshot | null {
  if (!value.tool_calls.some((call) => ['simulate', 'optimize'].includes(call)) || !['success', 'partial'].includes(value.status)) return null;
  const data = object(value.result), score = object(data.score), energy = object(data.energy), carbon = object(data.carbon), valuation = object(data.valuation);
  const id = string(data.scenario_id), propertyId = string(data.property_id);
  if (!id || !propertyId || !['success', 'partial'].includes(String(data.status))) return null;
  return {
    notes: [...(Array.isArray(data.assumptions) ? data.assumptions : []), ...(Array.isArray(data.warnings) ? data.warnings : []), ...(Array.isArray(object(data.feasibility).items) ? (object(data.feasibility).items as unknown[]).map((item) => { const row = object(item); return `${string(row.retrofit) || 'Upgrade'}: ${string(row.status) || 'Unknown'} — ${string(row.reason) || ''}`; }) : [])].filter((v): v is string => typeof v === 'string'),
    id, propertyId, status: String(data.status), upgrades: Array.isArray(data.applied_retrofits) ? data.applied_retrofits.filter((v): v is string => typeof v === 'string') : [],
    beforeScore: finite(score.baseline), afterScore: finite(score.after), beforeClass: string(score.classification), afterClass: string(score.after_classification),
    beforeElectricity: finite(energy.baseline_electricity_kwh), afterElectricity: finite(energy.after_electricity_kwh),
    beforeGas: finite(energy.baseline_gas_kwh), afterGas: finite(energy.after_gas_kwh),
    electricitySavings: finite(energy.electricity_savings_kwh), gasSavings: finite(energy.gas_savings_kwh), energySavings: finite(energy.net_savings_kwh), improvement: finite(energy.improvement_percentage),
    carbonReduction: carbon.status === 'available' ? finite(carbon.reduction_kg_co2e) : null,
    cost: finite(data.installation_cost_gbp), billSavings: finite(data.annual_bill_savings_gbp), payback: finite(data.simple_payback_years),
    valueStatus: string(valuation.status) ?? 'unavailable', valueReason: string(valuation.reason), baselineValue: finite(valuation.baseline_value_gbp),
    valueRange: valuation.status === 'unavailable' ? null : range(valuation.value_change_range_gbp),
  };
}
export function valueImpact(output: OutputSnapshot): string {
  if (!output.valueRange) return 'Unavailable';
  if (output.baselineValue === null || output.baselineValue <= 0) return 'Percentage unavailable; see the £ range';
  const percent = (value: number) => `${value > 0 ? '+' : ''}${(100 * value / output.baselineValue!).toFixed(1)}%`;
  return `${percent(output.valueRange[0])} to ${percent(output.valueRange[1])}`;
}
export type ComparePriority = 'score' | 'energy' | 'carbon' | 'cost';
export function bestOutput(outputs: OutputSnapshot[], priority: ComparePriority): string[] {
  const field = { score: 'afterScore', energy: 'energySavings', carbon: 'carbonReduction', cost: 'cost' } as const;
  const candidates = outputs.filter((o) => ['success', 'partial'].includes(o.status) && o[field[priority]] !== null);
  if (!candidates.length) return [];
  const best = (priority === 'cost' ? Math.min : Math.max)(...candidates.map((o) => o[field[priority]]!));
  return candidates.filter((o) => o[field[priority]] === best).map((o) => o.id);
}
