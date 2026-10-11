'use client';
import { useEffect, useState } from 'react';
import { api, ApiError } from '@/lib/api';
import { label } from '@/lib/format';
import { inputOf, useWorkspace } from './workspace';
import type { CustomerMemory, Objective, Retrofit } from '@/lib/types';

const measures: Retrofit[] = ['loft_insulation', 'heat_pump', 'solar_panels', 'double_glazing', 'smart_thermostat'];
const empty: CustomerMemory = {revision: 0, preferences: {budget_gbp: null, objective: 'carbon_reduction', excluded_retrofits: []}, completed_retrofits: [], feedback: {}, history: [], scope: ''};

export function CustomerMemoryPanel({refresh, onUse}: {refresh: number; onUse: () => void}) {
  const {record, dirty} = useWorkspace();
  const [memory, setMemory] = useState<CustomerMemory | null>(null);
  const [budget, setBudget] = useState(''); const [objective, setObjective] = useState<Objective>('carbon_reduction');
  const [excluded, setExcluded] = useState<Retrofit[]>([]); const [completed, setCompleted] = useState<Retrofit[]>([]);
  const [busy, setBusy] = useState(false); const [notice, setNotice] = useState('');
  const propertyId = record?.property.property_id;
  function apply(value: CustomerMemory) {
    setMemory(value); setBudget(value.preferences.budget_gbp === null ? '' : String(value.preferences.budget_gbp));
    setObjective(value.preferences.objective); setExcluded(value.preferences.excluded_retrofits); setCompleted(value.completed_retrofits);
  }
  useEffect(() => {
    let active = true;
    if (!propertyId) return;
    void api.memory(propertyId).then(value => { if(active) apply(value); }).catch(e => {
      if(!active) return;
      if(e instanceof ApiError && e.status === 404 && dirty) apply(empty);
      else setNotice((e as Error).message);
    });
    return () => {active = false;};
  }, [propertyId, refresh, dirty]);
  async function save(update: Parameters<typeof api.updateMemory>[1]) {
    if(!record || busy) return;
    setBusy(true); setNotice('');
    try {
      if(dirty) await api.register(inputOf(record));
      apply(await api.updateMemory(record.property.property_id, update));
      setNotice('Saved. These choices survive reloads; estimates will be recalculated.');
    } catch(e) {
      setNotice((e as Error).message);
      if(e instanceof ApiError && e.status === 409) apply(await api.memory(record.property.property_id));
    } finally {setBusy(false);}
  }
  if(!propertyId) return null;
  const packages = [...memory?.history || []].reverse().filter(row => row.recommended_package.length > 0)
    .filter((row,index,rows) => rows.findIndex(other => [...other.recommended_package].sort().join(',') === [...row.recommended_package].sort().join(',')) === index).slice(0,3);
  return <details className="customer-memory"><summary>What Kew remembers {memory && <small>· {memory.history.length} recent actions</small>}</summary>
    <p>Saved preferences for this customer. Completed work and package feedback belong to this home. They never replace assessment evidence.</p>
    <form onSubmit={e => {e.preventDefault(); if(memory) void save({revision: memory.revision, preferences: {budget_gbp: budget === '' ? null : Number(budget), objective, excluded_retrofits: excluded}, completed_retrofits: completed});}}>
      <label>Remembered maximum budget · GBP<input aria-label="Remembered maximum budget" type="number" min="0" max="1000000000" step="any" value={budget} onChange={e => setBudget(e.target.value)} /></label>
      <label>Remembered priority<select aria-label="Remembered priority" value={objective} onChange={e => setObjective(e.target.value as Objective)}><option value="carbon_reduction">Reduce carbon</option><option value="energy_reduction">Reduce purchased energy</option><option value="shortest_payback">Shortest payback</option></select></label>
      <fieldset><legend>Upgrades I do not want</legend>{measures.map(id => <label key={id}><input type="checkbox" checked={excluded.includes(id)} onChange={() => setExcluded(old => old.includes(id) ? old.filter(r => r !== id) : [...old,id])} />{label(id)}</label>)}</fieldset>
      <fieldset><legend>Work I confirm is completed at this home</legend><p>Proposed or accepted packages are not installed work. Update Assessment and its energy inputs after completing work.</p>{measures.map(id => <label key={id}><input type="checkbox" checked={completed.includes(id)} onChange={() => setCompleted(old => old.includes(id) ? old.filter(r => r !== id) : [...old,id])} />{label(id)}</label>)}</fieldset>
      <button className="button secondary" disabled={!memory || busy}>Save memory</button>
    </form>
    <button className="button secondary" type="button" disabled={!memory || busy} onClick={onUse}>Use my saved preferences</button>
    {packages.map(row => {const key = [...row.recommended_package].sort().join(',');return <div key={key}><strong>{row.recommended_package.map(label).join(' + ')}</strong><small> {memory?.feedback[key]?.response || 'No feedback yet'}</small>{(['accepted','rejected','deferred'] as const).map(response => <button className="button ghost" key={response} disabled={busy} onClick={() => {if(memory) void save({revision: memory.revision, feedback: {retrofits: row.recommended_package, response}});}}>{response === 'accepted' ? 'Interested' : response === 'rejected' ? 'Not for me' : 'Later'}</button>)}</div>;})}
    <p>“Not for me” or “Later” removes that exact package from future searches. “Interested” restores it; it does not mark work completed.</p>
    {memory && <button className="button ghost" disabled={busy} onClick={() => void save({revision: memory.revision, reset: true})}>Reset preferences and this home’s memory</button>}
    {notice && <p role="status">{notice}</p>}
  </details>;
}
