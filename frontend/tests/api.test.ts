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
  globalThis.fetch = async () => Response.json({ property_id: 'EDIT-1', scenario_id: 'R1', recommendations: [], other_options: [{ retrofit: 'solar_panels', feasibility: { status: 'conditional', reason: 'Roof unknown' }, scenario: { installation_cost_gbp: null, energy: null, carbon: null, reason: 'Needs confirmation', assumptions: [], warnings: [] } }], methodology: 'Individual screening', warnings: ['Optimizer pending'] });
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
    property_id: 'EDIT-1', scenario_id: 'R1',
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

test('advisor stream handles split network chunks and delivers real progress', async () => {
  const progress: string[] = [];
  const encoder = new TextEncoder();
  globalThis.fetch = async () => new Response(new ReadableStream({ start(controller) {
    for (const chunk of ['event: pro', 'gress\ndata: {"message":"Checking feasibility"}\n\n',
      'event: result\ndata: {"status":"success","explanation":"Verified answer"}\n\n']) {
      controller.enqueue(encoder.encode(chunk));
    }
    controller.close();
  } }));
  const answer = await api.advisorStream('P1', 'install solar', (message) => progress.push(message));
  assert.deepEqual(progress, ['Checking feasibility']);
  assert.equal(answer.explanation, 'Verified answer');
});

test('advisor stream never treats an interrupted connection as an answer', async () => {
  globalThis.fetch = async () => new Response(new ReadableStream({ start(controller) { controller.close(); } }));
  await assert.rejects(api.advisorStream('P1', 'Explain', () => {}), /ended before an answer/);
});

test('recommendations render the property/scenario list retrieved from storage in its saved order', async () => {
  const calls: string[] = [];
  const scenario = { installation_cost_gbp: null, energy: { electricity_savings_kwh: -2000, gas_savings_kwh: 10000 }, carbon: { status: 'unavailable', reason: 'No factors' }, assumptions: ['Physical calculation'], warnings: [], reason: null };
  globalThis.fetch = async (url, init) => {
    calls.push(String(url));
    if (init?.method === 'POST') return Response.json({ property_id: 'EDIT-1', scenario_id: 'session /1', recommendations: [] });
    return Response.json({ property_id: 'EDIT-1', scenario_id: 'session /1', revision: 2, installation_order: ['loft_insulation', 'heat_pump'], recommendations: [
      { retrofit: 'heat_pump', priority: 1, feasibility: { status: 'feasible', reason: 'Compatible' }, suitability: 'Medium', suitability_reason: 'Synthetic inputs', scenario },
      { retrofit: 'loft_insulation', priority: 2, feasibility: { status: 'feasible', reason: 'Suitable roof' }, suitability: 'Medium', suitability_reason: 'Synthetic inputs', scenario },
    ], other_options: [], methodology: 'Percentage reduction', warnings: [] });
  };
  const result = await api.recommendations(input, null, 'energy_reduction');
  assert.deepEqual(calls, ['/api/backend/retrofits/recommend', '/api/backend/properties/EDIT-1/recommendations?scenario_id=session%20%2F1']);
  assert.deepEqual(result.items.map((row) => row.retrofit), ['heat_pump', 'loft_insulation']);
  assert.equal(result.items[0].energy?.electricity_savings_kwh, -2000);
  assert.equal(result.items[0].carbon?.status, 'unavailable');
  assert.ok(result.warnings.some((text) => text.includes('loft insulation → heat pump')));
});

test('stored recommendation response cannot leak another property into the planner', async () => {
  globalThis.fetch = async (_url, init) => Response.json({ property_id: init?.method === 'POST' ? 'EDIT-1' : 'OTHER', scenario_id: 'R1' });
  await assert.rejects(api.recommendations(input, null, 'energy_reduction'), /differ from the requested property/);
});
