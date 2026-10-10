'use client';
import { useState } from 'react';
import { Leaf, Trophy } from 'lucide-react';
import { label, money, number } from '@/lib/format';
import { bestOutput, valueImpact, type ComparePriority, type OutputSnapshot } from '@/lib/results';
import type { Assessment } from '@/lib/types';

export function OutputSummary({ output, assessment }: { output?: OutputSnapshot; assessment: Assessment | null }) {
  const score = output ? output.afterScore : assessment?.score.score;
  const classification = output ? output.afterClass : assessment?.score.classification;
  return <section className="output-summary" aria-label="Expected outputs"><span className="mini-label"><Leaf size={14} /> Your home at a glance</span><h3>{output ? 'Your retrofit result' : 'Your current home'}</h3><p>{output ? 'Calculated outputs from your latest completed package.' : 'Run an assessment, then explore an improvement package.'}</p>{output && <span className={`badge ${output.status === 'partial' ? 'amber' : ''}`}>{label(output.status)} estimate</span>}<dl>
    <div><dt>Green Home Score</dt><dd className="output-score">{number(score)}{score != null && <small> / 100</small>}</dd></div>
    <div><dt>Efficiency classification</dt><dd>{classification || 'Unavailable'}</dd></div>
    <div><dt>{output ? 'Modelled improvements' : 'Recommended improvements'}</dt><dd>{output ? output.upgrades.map(label).join(' + ') || 'No upgrades applied' : 'Check recommendations in the planner'}</dd></div>
    <div><dt>Potential annual energy savings</dt><dd>{number(output?.energySavings, 'kWh/year')}<small>Electricity: {number(output?.electricitySavings, 'kWh/year')}<br />Gas: {number(output?.gasSavings, 'kWh/year')}</small></dd></div>
    <div><dt>Potential annual carbon reduction</dt><dd>{number(output?.carbonReduction == null ? null : output.carbonReduction / 1000, 't CO₂e/year', 2)}</dd></div>
    <div><dt>Potential property-value impact</dt><dd>{output ? valueImpact(output) : 'Run a retrofit scenario'}{output?.valueRange && <small>{output.valueRange.map(money).join(' to ')} · {output.valueStatus === 'illustrative' ? 'Synthetic illustration' : 'Indicative range'}</small>}</dd></div>
  </dl><p className="output-footnote">Score: weighted assessment · Energy: retrofit calculation · Carbon: per-fuel factors · Value: valuation model. Missing outputs remain unavailable. A value estimate is not a guaranteed sale premium.</p></section>;
}

export function PackageComparison({ outputs }: { outputs: OutputSnapshot[] }) {
  const [priority, setPriority] = useState<ComparePriority>('score');
  const best = bestOutput(outputs, priority), current = outputs.at(-1);
  const descriptions = { score: 'Highest available score', energy: 'Most net energy saved', carbon: 'Most carbon reduced', cost: 'Lowest installation cost' };
  if (!current) return <section className="panel"><h2>Your packages, side by side</h2><p>Run a package in the planner or Ask Kew to see its calculated outputs here. Run another package to compare options for the same home.</p></section>;
  const rows: { name: string; baseline: string; value: (o: OutputSnapshot) => string }[] = [
    { name: 'Green Home Score / 100', baseline: number(current.beforeScore), value: (o) => number(o.afterScore) },
    { name: 'Efficiency classification', baseline: current.beforeClass || 'Unavailable', value: (o) => o.afterClass || 'Unavailable' },
    { name: 'Purchased electricity · kWh/year', baseline: number(current.beforeElectricity), value: (o) => number(o.afterElectricity) },
    { name: 'Purchased gas · kWh/year', baseline: number(current.beforeGas), value: (o) => number(o.afterGas) },
    { name: 'Electricity savings · kWh/year', baseline: 'Reference', value: (o) => number(o.electricitySavings) },
    { name: 'Gas savings · kWh/year', baseline: 'Reference', value: (o) => number(o.gasSavings) },
    { name: 'Net energy savings · kWh/year', baseline: 'Reference', value: (o) => number(o.energySavings) },
    { name: 'Purchased-energy reduction · %', baseline: 'Reference', value: (o) => number(o.improvement, '', 1) },
    { name: 'Carbon reduction · t CO₂e/year', baseline: 'Reference', value: (o) => number(o.carbonReduction == null ? null : o.carbonReduction / 1000, '', 2) },
    { name: 'Installation cost', baseline: 'No proposed works', value: (o) => money(o.cost) },
    { name: 'Annual bill savings', baseline: 'Reference', value: (o) => money(o.billSavings) },
    { name: 'Simple payback · years', baseline: 'Not applicable', value: (o) => number(o.payback, '', 1) },
    { name: 'Property-value impact · range', baseline: 'Reference', value: valueImpact },
    { name: 'Property-value change · £ range', baseline: 'Reference', value: (o) => o.valueRange ? o.valueRange.map(money).join(' to ') : 'Unavailable' },
  ];
  return <section className="panel package-comparison"><div className="section-heading"><div><h2>Find the package that fits you</h2><p>Compare your current home with up to six packages from this session.</p></div><label className="field"><span>Compare by</span><select value={priority} onChange={(e) => setPriority(e.target.value as ComparePriority)}><option value="score">Green Home Score</option><option value="energy">Net energy savings</option><option value="carbon">Carbon reduction</option><option value="cost">Installation cost</option></select></label></div><p className="comparison-guidance">{descriptions[priority]} is highlighted among available estimates. Partial results may be missing other outputs; review feasibility and assumptions before deciding. Negative savings mean an increase in consumption.</p><div className="package-table-scroll" tabIndex={0} aria-label="Scrollable package comparison"><table><caption>Current home and calculated retrofit packages for {current.propertyId}</caption><thead><tr><th scope="col">Output</th><th scope="col">Current home<small>Baseline assessment</small></th>{outputs.map((o, i) => <th scope="col" key={o.id} className={best.includes(o.id) ? 'best-package' : ''}><span>Package {i + 1}{i === outputs.length - 1 ? ' · latest' : ''}</span><small>{o.upgrades.map(label).join(' + ') || 'No upgrades'}</small><span className={`badge ${o.status === 'partial' ? 'amber' : ''}`}>{label(o.status)}</span>{o.valueStatus === 'illustrative' && <small>Synthetic value illustration</small>}{best.includes(o.id) && <span className="best-label"><Trophy size={13} />{descriptions[priority]}</span>}</th>)}</tr></thead><tbody>{rows.map((row) => <tr key={row.name}><th scope="row">{row.name}</th><td>{row.baseline}</td>{outputs.map((o) => <td className={best.includes(o.id) ? 'best-package' : ''} key={o.id}>{row.value(o)}</td>)}</tr>)}</tbody></table></div>{outputs.map((output, i) => <details className="package-evidence" key={output.id}><summary>Package {i + 1}: assumptions and feasibility</summary>{output.notes.length ? <ul>{Array.from(new Set(output.notes)).map((note) => <li key={note}>{note}</li>)}</ul> : <p>No additional evidence was supplied.</p>}</details>)}<p className="output-footnote">Every package uses the same home details and baseline. Changing property details clears this comparison; results are kept only for this page session.</p></section>;
}
