import { test } from 'node:test';
import assert from 'node:assert/strict';
import { advisorOutput, bestOutput, valueImpact, type OutputSnapshot } from '../lib/results.ts';
import type { AdvisorResult } from '../lib/types.ts';

const response = (patch: Record<string, unknown> = {}): AdvisorResult => ({ status: 'partial', explanation: 'Computed test result', mode: 'fallback', fallback_reason: null, intent: { intent: 'simulate_retrofit', retrofits: ['heat_pump'], budget_gbp: null, objective: 'carbon_reduction' }, tool_calls: ['simulate'], result: {
  scenario_id: 'one', property_id: 'P1', status: 'partial', applied_retrofits: ['heat_pump'],
  score: { baseline: 38, after: 68, classification: 'Poor', after_classification: 'Good' },
  energy: { electricity_savings_kwh: -1200, gas_savings_kwh: 5000, net_savings_kwh: 3800 },
  carbon: { status: 'unavailable', reduction_kg_co2e: 500 },
  valuation: { status: 'indicative', baseline_value_gbp: 200000, value_change_range_gbp: [4000, 10000] }, ...patch,
} });

test('advisor comparison preserves backend classification and signed fuel changes', () => {
  const output = advisorOutput(response())!;
  assert.equal(output.afterClass, 'Good');
  assert.equal(output.electricitySavings, -1200);
  assert.equal(output.energySavings, 3800);
  assert.equal(output.carbonReduction, null);
  assert.equal(output.afterGas, null);
  assert.equal(valueImpact(output), '+2.0% to +5.0%');
});
test('failed calls and assessment-only replies cannot become completed comparisons', () => {
  assert.equal(advisorOutput({ ...response(), status: 'rejected' }), null);
  assert.equal(advisorOutput({ ...response(), tool_calls: ['assessment'] }), null);
  assert.equal(advisorOutput(response({ scenario_id: null })), null);
});
test('unavailable valuations and missing denominators never imply a premium', () => {
  const unavailable = advisorOutput(response({ valuation: { status: 'unavailable', value_change_range_gbp: [1, 5] } }))!;
  assert.equal(unavailable.valueRange, null);
  const missing = advisorOutput(response({ valuation: { status: 'indicative', baseline_value_gbp: 0, value_change_range_gbp: [1, 5] } }))!;
  assert.equal(valueImpact(missing), 'Percentage unavailable; see the £ range');
});
test('best package depends on priority, excludes unknowns and preserves ties and zero', () => {
  const base = advisorOutput(response())!;
  const outputs: OutputSnapshot[] = [{ ...base, id: 'a', afterScore: 70, cost: 0 }, { ...base, id: 'b', afterScore: 80, cost: 5000 }, { ...base, id: 'c', afterScore: null, cost: null }];
  assert.deepEqual(bestOutput(outputs, 'score'), ['b']);
  assert.deepEqual(bestOutput(outputs, 'cost'), ['a']);
  assert.deepEqual(bestOutput(outputs, 'carbon'), []);
  assert.deepEqual(bestOutput(outputs, 'energy'), ['a', 'b', 'c']);
});
