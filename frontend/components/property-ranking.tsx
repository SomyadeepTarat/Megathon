'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { api } from '@/lib/api';
import { label, money, number } from '@/lib/format';
import type { PortfolioRow } from '@/lib/types';
import { useWorkspace } from './workspace';
import { Busy, Empty, Notice, PageHeading } from './ui';

export function PropertyRanking() {
  const { selectProperty, properties } = useWorkspace();
  const router = useRouter();
  const [rows, setRows] = useState<PortfolioRow[]>([]);
  const [busy, setBusy] = useState(true);
  const [error, setError] = useState('');
  const [query, setQuery] = useState('');
  const [poorOnly, setPoorOnly] = useState(false);
  const [revision, setRevision] = useState(0);
  useEffect(() => {
    let active = true;
    setBusy(true); setError('');
    api.propertyRanking().then((result) => { if (active) setRows(result); }).catch((reason) => { if (active) { setRows([]); setError(reason.message); } }).finally(() => { if (active) setBusy(false); });
    return () => { active = false; };
  }, [revision, properties]);
  const displayed = rows.filter((row) => (!poorOnly || row.poor_home === true) && `${row.property_id} ${row.region} ${row.property_type}`.toLowerCase().includes(query.toLowerCase()));
  async function open(id: string) { await selectProperty(id); router.push('/assessment'); }
  return <>
    <PageHeading eyebrow="See the potential" title="Your properties, ranked." description="Compare estimated improvement potential and current recorded valuations across your homes." />
    <div className="portfolio-toolbar"><label className="search-field"><input aria-label="Search property ranking" placeholder="Search by property ID, region, or type" value={query} onChange={(event) => setQuery(event.target.value)} /></label><div><label className="ranking-filter"><input type="checkbox" checked={poorOnly} onChange={(event) => setPoorOnly(event.target.checked)} />Poor and very poor homes only</label><button className="button secondary" disabled={busy} onClick={() => setRevision((value) => value + 1)}>Refresh ranking</button></div></div>
    <Notice>Ranked by estimated reduction in annual purchased electricity plus gas: 100 × (baseline − after) / baseline. Packages include confirmed feasible improvements and account for interactions. Unknown eligibility, missing energy, or a zero baseline stays unranked. Equal potential shares a rank.</Notice>
    {error && <Notice tone="warning">{error}</Notice>}
    {busy ? <Busy text="Calculating property improvement potential…" /> : <div className="table-panel property-ranking-table"><table><caption>Properties ordered by estimated improvement potential; valuations are recorded baseline values, not guaranteed sale prices.</caption><thead><tr><th scope="col">Rank</th><th scope="col">Property</th><th scope="col">Current valuation</th><th scope="col">Green Home Score</th><th scope="col">Improvement potential</th><th scope="col">Electricity savings</th><th scope="col">Gas savings</th></tr></thead><tbody>{displayed.map((row) => <tr key={row.property_id}><td><strong>{row.rank == null ? 'Unranked' : `#${row.rank}`}</strong></td><th scope="row"><button className="property-table-link" onClick={() => void open(row.property_id)}>{row.property_id}</button><small>{row.region} · {label(row.property_type)}</small><small>{label(row.dataset_kind)} data</small><details><summary>Issues and proposed improvements</summary>{row.issues?.map((issue) => <p key={issue}>{issue}</p>)}<p>{row.feasible_retrofits?.length ? row.feasible_retrofits.map(label).join(', ') : 'No confirmed package available.'}</p>{row.reason && <p>{row.reason}</p>}</details></th><td>{money(row.current_property_value_gbp)}<small>Recorded current value</small></td><td>{number(row.score, '/100')}<small>{row.classification || 'Classification unavailable'}</small>{row.poor_home && <small>Needs improvement</small>}</td><td>{number(row.improvement, '%', 1)}{row.reason && <small>{row.reason}</small>}</td><td>{number(row.electricity_savings_kwh, 'kWh/year', 1)}</td><td>{number(row.gas_savings_kwh, 'kWh/year', 1)}</td></tr>)}</tbody></table>{!displayed.length && <Empty title="No properties to show.">Try another search or refresh the ranking.</Empty>}</div>}
    <p className="ranking-footnote">Savings are estimates. Negative fuel savings mean consumption increases. Synthetic data and valuations remain illustrative.</p>
  </>;
}
