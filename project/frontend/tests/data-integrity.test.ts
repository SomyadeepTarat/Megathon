import { test } from 'node:test';
import assert from 'node:assert/strict';
import { number, money, numericInput } from '../lib/format.ts';
import { compareRows } from '../lib/portfolio.ts';
import type { PortfolioRow } from '../lib/types.ts';
test('unknown consumption stays null while explicit zero stays zero', () => { assert.equal(numericInput(''), null); assert.equal(numericInput('  '), null); assert.equal(numericInput('0'), 0); });
test('negative heat-pump savings are displayed with their sign', () => { assert.equal(number(-1200, 'kWh/year'), '-1,200 kWh/year'); });
test('unavailable values never display as a zero-valued estimate', () => { assert.equal(number(null), 'Unavailable'); assert.equal(money(undefined), 'Unavailable'); assert.equal(number(0), '0'); assert.equal(money(0), '£0'); });
test('missing portfolio estimates remain last in both sort directions', () => {
  const row = (id: string, score: number | null) => ({ property_id: id, score } as PortfolioRow);
  const values = [row('unknown', null), row('high', 70), row('zero', 0)];
  assert.deepEqual([...values].sort((a, b) => compareRows(a, b, 'score', 'asc')).map((r) => r.property_id), ['zero', 'high', 'unknown']);
  assert.deepEqual([...values].sort((a, b) => compareRows(a, b, 'score', 'desc')).map((r) => r.property_id), ['high', 'zero', 'unknown']);
});
