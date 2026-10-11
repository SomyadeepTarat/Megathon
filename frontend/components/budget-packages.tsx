'use client';

import type { OptimizationResult } from '@/lib/types';
import { label, money, number } from '@/lib/format';
import { Badge } from './ui';

const priorities = {
  carbon_reduction: 'Most carbon reduction',
  energy_reduction: 'Most energy savings',
  shortest_payback: 'Shortest payback',
};

export function BudgetPackages({ result, budget, busy, onCompare }: {
  result: OptimizationResult; budget: number; busy: boolean; onCompare: () => void;
}) {
  const best = result.best_scenario;
  if (!best) return null;
  const options = best.optimization_context?.alternatives ?? [];
  return <section className="panel budget-results" aria-label="Budget-optimized package recommendations" aria-live="polite">
    <div className="section-heading"><div><h2>Your budget, put to work</h2><p>Best packages within {money(budget)}, using confirmed feasibility and documented costs.</p></div><Badge>{result.package_decisions.length} combinations checked</Badge></div>
    <p>{best.optimization_context?.explanation || result.methodology}</p>
    <div className="budget-package-grid">{options.map((option) => {
      const chosen = option.objective === result.objective;
      const remaining = budget - option.installation_cost_gbp;
      return <article className={`budget-package-card ${chosen ? 'chosen' : ''}`} key={option.objective}>
        <Badge tone={chosen ? '' : 'amber'}>{chosen ? 'Best for your priority' : 'Alternative priority'}</Badge>
        <h3>{priorities[option.objective]}</h3>
        <p className="budget-package-name">{option.retrofits.length ? option.retrofits.map(label).join(' + ') : 'Keep your current setup'}</p>
        <span className="mini-label">Confirmed feasible in this assessment</span>
        <dl>
          <div><dt>Installation cost</dt><dd>{money(option.installation_cost_gbp)}</dd></div>
          <div><dt>Budget remaining</dt><dd>{money(remaining)}</dd></div>
          <div><dt>Annual bill savings</dt><dd>{money(option.annual_bill_savings_gbp)}</dd></div>
          <div><dt>Carbon reduction</dt><dd>{number(option.carbon_reduction_kg_co2e, 'kg CO₂e/year')}</dd></div>
          <div><dt>Energy savings</dt><dd>{number(option.net_energy_savings_kwh, 'kWh/year')}</dd></div>
          <div><dt>Simple payback</dt><dd>{number(option.simple_payback_years, 'years', 1)}</dd></div>
        </dl>
        {chosen && <button className="button primary" disabled={busy} onClick={onCompare}>View this package in detail</button>}
      </article>;
    })}</div>
    <p className="budget-result-note">Packages are simulated together; standalone savings are not added up. A different priority may choose the same package. Unspent budget is retained rather than spent on upgrades that do not improve the selected objective.</p>
    <details className="upgrade-assumptions"><summary>Assumptions and limitations</summary><ul>{[...best.assumptions, ...best.warnings].map((text, i) => <li key={i}>{text}</li>)}</ul><p>Suitability depends on the supplied evidence; confirm installation requirements with a qualified professional. Missing estimates remain unavailable.</p></details>
  </section>;
}
