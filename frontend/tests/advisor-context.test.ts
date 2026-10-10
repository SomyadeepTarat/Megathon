import { test } from 'node:test';
import assert from 'node:assert/strict';
import { actionContext, needsPackageSelection } from '../lib/advisor-context.ts';
import type { AdvisorResult } from '../lib/types.ts';
const blocked = { status: 'infeasible', intent: { intent: 'simulate_retrofit', retrofits: ['heat_pump'], budget_gbp: null, objective: 'carbon_reduction' } } as AdvisorResult;
test('blocked scenario survives follow-up context and clarification messages', () => {
  assert.deepEqual(actionContext([{ result: blocked }, { result: { ...blocked, intent: { ...blocked.intent, intent: 'clarify', retrofits: [] } } }]), blocked.intent);
  const baseline = { ...blocked, status: 'success', intent: { ...blocked.intent, intent: 'explain', retrofits: [] } };
  assert.equal(actionContext([{ result: blocked }, { result: baseline }])?.intent, 'explain');
});
test('budget clarification never opens the retrofit selector', () => {
  assert.equal(needsPackageSelection({ ...blocked, status: 'clarification_required', clarification_kind: 'budget' }), false);
  assert.equal(needsPackageSelection({ ...blocked, status: 'clarification_required', clarification_kind: 'package' }), true);
  assert.equal(needsPackageSelection(blocked), false);
});
