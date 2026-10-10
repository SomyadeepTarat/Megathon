import type { Assessment, AssessmentRequest, PropertyRecord, PropertySummary, Scenario, Retrofit, Objective, AdvisorResult, Recommendation } from './types';

const notice = 'Illustrative demo data only. No backend is connected; edits do not calculate new performance.';
const ids: Retrofit[] = ['loft_insulation', 'heat_pump', 'solar_panels', 'double_glazing', 'smart_thermostat'];
const names = ['Loft insulation', 'Heat pump', 'Solar panels', 'Double glazing', 'Smart thermostat'];
const costs = [1200, 9500, 6500, 4800, 250];
const records: PropertyRecord[] = ['Greater London', 'South East', 'West Midlands', 'North West', 'Wales', 'South West'].map((region, i) => ({
  property: { property_id: `DEMO-00${i + 1}`, property_type: ['detached', 'semi_detached', 'terraced', 'flat', 'detached', 'terraced'][i], region, floor_area_m2: 110, property_age_years: 45, bedrooms: 3, energy_rating: 'D', insulation: 'poor', heating_system: 'modern_gas_boiler', glazing: 'double', renewable_contribution: 'none', smart_controls: 'none', roof_suitable_for_loft: true, roof_suitable_for_solar: null, heat_pump_compatible: true, controls_compatible: true, current_property_value_gbp: null, market_index: null, provenance: {} },
  annual_energy: { electricity_kwh: 3200, gas_kwh: 14500, quality: 'synthetic', method: 'Annual energy totals', electricity_months_covered: 12, gas_months_covered: 12, warnings: [] },
  benchmark: null, dataset_kind: 'synthetic', dataset_source: 'Frontend demonstration only',
}));
function assessment(id: string, after = false): Assessment {
  return { property_id: id, score: { status: 'available', score: after ? 76 : 52, classification: after ? 'Good' : 'Needs improvement', components: after ? [] : [
    ['energy_consumption', 0.3, 60, 18], ['epc_rating', 0.2, 50, 10], ['insulation', 0.15, 40, 6], ['heating_system', 0.15, 60, 9], ['windows', 0.1, 60, 6], ['renewables', 0.05, 0, 0], ['smart_controls', 0.05, 60, 3],
  ].map(([name, weight, subscore, contribution]) => ({ name: String(name), weight: Number(weight), subscore: Number(subscore), contribution: Number(contribution), evidence: { source: 'Property assessment' } })), missing_fields: [], methodology_version: 'frontend-demo' }, poor_home: !after, intensity_kwh_m2_year: after ? 109 : 161, issues: after ? [] : [{ code: 'insulation', severity: 'medium', message: 'Improve loft insulation to reduce heat loss.', evidence: { source: 'Property details' } }], warnings: [] };
}
function scenario(input: AssessmentRequest, selected: Retrofit[]): Scenario {
  // One fixed sample package. Never sum impacts or calculate estimates in the UI.
  const supported = selected.length === 2 && selected.includes('loft_insulation') && selected.includes('smart_thermostat');
  return { property_id: input.property.property_id, scenario_id: 'DEMO-SCENARIO', status: supported ? 'partial' : 'unavailable', reason: supported ? 'Loft insulation and smart thermostat package.' : 'A comparison is not available for this package yet. Try loft insulation and smart thermostat.', baseline_assessment: assessment(input.property.property_id), after_assessment: supported ? assessment(input.property.property_id, true) : null, updated_property: supported ? { ...input.property, insulation: 'good', smart_controls: 'present' } : null,
    feasibility: { status: 'conditional', items: selected.map(retrofit => ({ retrofit, status: 'conditional', reason: 'Illustrative only; eligibility has not been assessed.' })), reason: notice },
    energy: supported ? { baseline: { electricity_kwh: 3200, gas_kwh: 14500 }, after: { electricity_kwh: 3100, gas_kwh: 8900 }, electricity_savings_kwh: 100, gas_savings_kwh: 5600, net_savings_kwh: 5700, improvement_percentage: 32.2 } : null,
    carbon: { status: supported ? 'available' : 'unavailable', reduction_kg_co2e: supported ? 1050 : null, reason: notice, factors: [] }, valuation: { status: 'unavailable', reason: 'A property valuation is not available.', baseline_value_gbp: null, after_value_gbp: null, value_change_gbp: null, value_change_range_gbp: null, warnings: [] }, installation_cost_gbp: supported ? 1450 : null, applied_retrofits: supported ? selected : [], assumptions: ['Installation costs and outcomes depend on property suitability.'], warnings: [], annual_bill_savings_gbp: supported ? 420 : null, simple_payback_years: supported ? 3.5 : null };
}
export const demo = {
  health: async () => ({ status: 'demo', capabilities: {} }),
  properties: async (): Promise<PropertySummary[]> => records.map(r => ({ property_id: r.property.property_id, property_type: r.property.property_type, region: r.property.region, dataset_kind: r.dataset_kind, dataset_source: r.dataset_source })),
  property: async (id: string): Promise<PropertyRecord> => structuredClone(records.find(r => r.property.property_id === id) ?? records[0]),
  assessment: async (id: string) => assessment(id),
  assess: async (input: AssessmentRequest) => assessment(input.property.property_id),
  simulate: async (input: AssessmentRequest, selected: Retrofit[], _budget: number | null, _objective: Objective) => scenario(input, selected),
  recommendations: async (_input: AssessmentRequest, _budget: number | null, _objective: Objective): Promise<Recommendation[]> => ids.map((retrofit, i) => ({ retrofit, feasibility: { status: 'conditional', reason: 'Suitability requires confirmation' }, suitability: 'Requires assessment', priority: i + 1, estimated_cost_gbp: costs[i], energy: null, carbon: null, reason: `${names[i]} can improve comfort and energy performance. Suitability requires an assessment.`, assumptions: ['Confirm suitability with a qualified installer.'] })),
  advisor: async (_id: string, message: string, selection?: { intent: string; retrofits: Retrofit[]; budget_gbp: number | null; objective: Objective }, _context?: AssessmentRequest): Promise<AdvisorResult> => ({ status: 'success', explanation: /budget|£|best/i.test(message) ? 'Loft insulation and smart controls are useful starting points to explore. Compare their installation costs with your budget.' : /what if|heat pump|simulate/i.test(message) ? 'Heat pumps can reduce gas use while increasing electricity demand. Property suitability and insulation matter. Explore the planner to review your options.' : 'The assessment highlights loft insulation as an opportunity. Better insulation helps retain warmth and can improve comfort. Review the score components to understand each contribution.', mode: 'demo', fallback_reason: null, tool_calls: [], result: null, intent: { intent: selection?.intent ?? 'explain_score', retrofits: selection?.retrofits ?? [], budget_gbp: selection?.budget_gbp ?? null, objective: selection?.objective ?? 'carbon_reduction' } }),
};
