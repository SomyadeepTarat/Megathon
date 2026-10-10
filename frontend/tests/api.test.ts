import { test, afterEach } from 'node:test';
import assert from 'node:assert/strict';
import { api, ApiError } from '../lib/api.ts';
import type { AssessmentRequest } from '../lib/types.ts';
const originalFetch = globalThis.fetch;
afterEach(() => { globalThis.fetch = originalFetch; });
const input = { property: { property_id: 'EDIT-1', physical_inputs: { thermal_demand_kwh: 8000, provenance: {} } }, annual_energy: { electricity_kwh: 0, gas_kwh: null }, benchmark: null, emission_factors: null } as unknown as AssessmentRequest;
test('live assessment preserves physical inputs, zero and missing consumption', async () => {
  globalThis.fetch = async (url, init) => {
    assert.equal(url, '/api/backend/assessments');
    assert.deepEqual(JSON.parse(String(init?.body)), input);
    return Response.json({ property_id: 'EDIT-1', score: { score: null } });
  };
  assert.equal((await api.assess(input)).score.score, null);
});
test('structured unavailable scenarios reach the comparison screen', async () => {
  globalThis.fetch = async () => Response.json({ scenario_id: 'S1', status: 'unavailable', baseline_assessment: {}, reason: 'Missing thermal demand' }, { status: 503 });
  assert.equal((await api.simulate(input, ['heat_pump'], null, 'carbon_reduction')).reason, 'Missing thermal demand');
});
test('unstructured server errors never become scenario estimates', async () => {
  globalThis.fetch = async () => Response.json({ detail: 'Service unavailable' }, { status: 503 });
  await assert.rejects(api.simulate(input, [], null, 'carbon_reduction'), (error) => error instanceof ApiError && error.status === 503);
});
test('recommendations preserve conditional options and unknown costs', async () => {
  globalThis.fetch = async () => Response.json({ recommendations: [], other_options: [{ retrofit: 'solar_panels', feasibility: { status: 'conditional', reason: 'Roof unknown' }, scenario: { installation_cost_gbp: null, energy: null, carbon: null, reason: 'Needs confirmation', assumptions: [], warnings: [] } }], methodology: 'Individual screening', warnings: ['Optimizer pending'] });
  const result = await api.recommendations(input, null, 'carbon_reduction');
  assert.equal(result.items[0].estimated_cost_gbp, null);
  assert.equal(result.items[0].feasibility.status, 'conditional');
  assert.deepEqual(result.warnings, ['Individual screening', 'Optimizer pending']);
});
test('advisor registers edits before resolving property by ID', async () => {
  const calls: string[] = [];
  globalThis.fetch = async (url, init) => {
    calls.push(String(url));
    const body = JSON.parse(String(init?.body));
    if (calls.length === 1) assert.deepEqual(body, input);
    else assert.deepEqual(body, { property_id: 'EDIT-1', message: 'Explain my home' });
    return Response.json(calls.length === 1 ? input : { status: 'partial', intent: { intent: 'explain' }, explanation: 'Missing benchmark' });
  };
  await api.advisor('EDIT-1', 'Explain my home', undefined, input);
  assert.deepEqual(calls, ['/api/backend/properties', '/api/backend/advisor/chat']);
});
test('validation errors identify the failing field', async () => {
  globalThis.fetch = async () => Response.json({ detail: [{ loc: ['body', 'property', 'floor_area_m2'], msg: 'Must be greater than zero' }] }, { status: 422 });
  await assert.rejects(api.assess(input), /property.floor_area_m2: Must be greater than zero/);
});
test('unavailable optimizer explanation never becomes a fabricated preview', async () => {
  const answer = { status: 'unavailable', explanation: 'Documented costs missing.', intent: { intent: 'optimize_budget', budget_gbp: 5000 } };
  globalThis.fetch = async () => Response.json(answer);
  const result = await api.advisor('EDIT-1', 'Find a package');
  assert.deepEqual(result, answer);
});

test('optimizer requests actual package calculation and preserves null results', async () => {
  globalThis.fetch = async (url, init) => {
    assert.equal(url, '/api/backend/retrofits/optimize');
    assert.deepEqual(JSON.parse(String(init?.body)), { ...input, budget_gbp: 5000, objective: 'energy_reduction' });
    return Response.json({ status: 'unavailable', best_scenario: null, reason: 'No costs', ranked_packages: [] });
  };
  assert.equal((await api.optimize(input, 5000, 'energy_reduction')).best_scenario, null);
});

test('recommendation mapping preserves suitability, backend rank and unranked options', async () => {
  const scenario = { installation_cost_gbp: 1000, energy: null, carbon: null, reason: null, assumptions: [], warnings: [], annual_bill_savings_gbp: 100, simple_payback_years: 10 };
  globalThis.fetch = async () => Response.json({
    recommendations: [{ retrofit: 'heat_pump', priority: 2, suitability: 'Medium', suitability_reason: 'Synthetic screening estimate', feasibility: { status: 'feasible', reason: 'Compatible' }, scenario }],
    other_options: [{ retrofit: 'solar_panels', priority: null, suitability: 'Low', suitability_reason: 'Roof unsuitable', feasibility: { status: 'infeasible', reason: 'Roof unsuitable' }, scenario }], methodology: 'Ranked individual measures', warnings: []
  });
  const result = await api.recommendations(input, null, 'carbon_reduction');
  assert.equal(result.items[0].priority, 2);
  assert.equal(result.items[0].suitability, 'Medium');
  assert.equal(result.items[0].suitability_reason, 'Synthetic screening estimate');
  assert.equal(result.items[0].recommended, true);
  assert.equal(result.items[0].simple_payback_years, 10);
  assert.equal(result.items[1].priority, null);
  assert.equal(result.items[1].recommended, false);
});
