'use client';

import type { OptimizationResult, Objective } from '@/lib/types';
import { label, money, number } from '@/lib/format';
import { baselineOnlyOptimization, groupedPackages, uniqueText } from '@/lib/planner';
import { Badge } from './ui';

const priorities = {
  carbon_reduction: 'Most carbon reduction',
  energy_reduction: 'Most energy savings',
  shortest_payback: 'Shortest payback',
};

export function BudgetPackages({ result, budget, busy, onCompare }: {
  result: OptimizationResult; budget: number; busy: boolean; onCompare: (objective: Objective) => void;
}) {
  const best = result.best_scenario;
  if (!best) return null;
  if (baselineOnlyOptimization(result)) {
    const reasons = uniqueText(result.package_decisions.flatMap(row =>
      row && typeof row === 'object' && 'reason' in row && typeof row.reason === 'string' ? [row.reason] : []));
    return <section className="panel budget-results" aria-label="Budget optimization needs more information" aria-live="polite">
      <h2>No upgrade package could be confirmed</h2>
      <p>No upgrade package passed the input, feasibility and {money(budget)} budget checks. The unchanged home is the comparison baseline; this does not establish that keeping it unchanged is the best investment.</p>
      <p>Review the reasons below. Add documented costs and any missing eligibility or energy evidence in Assessment, or adjust your budget.</p>
      <details><summary>Why packages were excluded · {result.package_decisions.length} combinations checked</summary><ul>{reasons.map(reason => <li key={reason}>{reason}</li>)}</ul></details>
    </section>;
  }
  const options = groupedPackages(best.optimization_context?.alternatives ?? [], result.objective);
  return <section className="panel budget-results" aria-label="Budget-optimized package recommendations" aria-live="polite">
    <div className="section-heading"><div><h2>Your budget, put to work</h2><p>Best packages within {money(budget)}, using confirmed feasibility and documented costs.</p></div><Badge>{result.package_decisions.length} combinations checked</Badge></div>
    <p>We compared feasible packages within your budget. The highlighted package best meets your selected priority.</p><details className="upgrade-assumptions"><summary>Why this package wins</summary><p>{best.optimization_context?.explanation || result.methodology}</p></details>
    <div className="budget-package-grid">{options.map(({option, objectives, chosen}) => {
      const remaining = budget - option.installation_cost_gbp;
      return <article className={`budget-package-card ${chosen ? 'chosen' : ''}`} key={option.objective}>
        <Badge tone={chosen ? '' : 'amber'}>{chosen ? 'Best for your priority' : 'Alternative priority'}</Badge>
        <h3>{chosen ? priorities[result.objective] : priorities[option.objective]}</h3><p className="winning-objectives">Best for: {objectives.map(value => priorities[value].toLowerCase()).join(' · ')}</p>
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
        <button className={`button ${chosen ? "primary" : "secondary"}`} disabled={busy} onClick={() => onCompare(option.objective)}>{chosen ? "View this package in detail" : "Compare this alternative"}</button>
      </article>;
    })}</div>
    <p className="budget-result-note">Packages are simulated together; standalone savings are not added up. A different priority may choose the same package. Unspent budget is retained rather than spent on upgrades that do not improve the selected objective.</p>
    <details className="upgrade-assumptions"><summary>Assumptions and limitations</summary><ul>{uniqueText([...best.assumptions, ...best.warnings]).map((text, i) => <li key={i}>{text}</li>)}</ul><p>Suitability depends on the supplied evidence; confirm installation requirements with a qualified professional. Missing estimates remain unavailable.</p></details>
  </section>;
}
