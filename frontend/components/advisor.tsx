'use client';
import { useEffect, useRef, useState } from 'react';
import { ArrowUp, Leaf, LoaderCircle } from 'lucide-react';
import { api } from '@/lib/api';
import { needsPackageSelection } from '@/lib/advisor-context';
import { advisorOutput } from '@/lib/results';
import { label, number } from '@/lib/format';
import { inputOf, useWorkspace } from './workspace';
import type { AdvisorResult, Objective, Retrofit } from '@/lib/types';
interface Message { role: 'user' | 'assistant'; text: string; result?: AdvisorResult }
function ScenarioEvidence({ result }: { result: AdvisorResult }) {
  if (!result.tool_calls.some((call) => ['simulate', 'optimize'].includes(call)) || !['success', 'partial'].includes(result.status)) return null;
  const energy = result.result?.energy;
  if (!energy || typeof energy !== 'object') return null;
  const data = energy as Record<string, unknown>;
  return <div className="chat-scenario"><strong>Calculated scenario</strong>{(['electricity_savings_kwh', 'gas_savings_kwh', 'net_savings_kwh'] as const).map((key) => <div key={key}><span>{label(key.replace('_kwh', ''))}</span><b>{number(typeof data[key] === 'number' ? data[key] : null, 'kWh/year')}</b></div>)}</div>;
}
export function Advisor() {
  const { record, dirty, addOutput, setScenario } = useWorkspace();
  const [messages, setMessages] = useState<Message[]>([]); const [question, setQuestion] = useState('');
  const [progress, setProgress] = useState('Checking your home’s evidence…');
  const propertyId = record?.property.property_id;
  const currentProperty = useRef(propertyId); currentProperty.current = propertyId;
  useEffect(() => { setMessages([]); setConfirm(false); setPackageIds([]); }, [propertyId]);
  const [busy, setBusy] = useState(false); const [confirm, setConfirm] = useState(false);
  const [packageIds, setPackageIds] = useState<Retrofit[]>([]); const end = useRef<HTMLDivElement>(null);
  const ids: Retrofit[] = ['loft_insulation', 'heat_pump', 'solar_panels', 'double_glazing', 'smart_thermostat'];
  useEffect(() => { end.current?.scrollIntoView({ behavior: 'smooth', block: 'nearest' }); }, [messages, busy]);
  async function send(text: string, selected?: Retrofit[]) {
    if (!record || !text.trim() || busy) return;
    setMessages((value) => [...value, { role: 'user', text }]); setQuestion(''); setBusy(true); setConfirm(false);
    setProgress('Connecting to your home advisor…');
    try {
      const result = await api.advisorStream(record.property.property_id, text, setProgress, selected ? { intent: 'simulate_retrofit', retrofits: selected, budget_gbp: null, objective: 'carbon_reduction' as Objective } : undefined, dirty ? inputOf(record) : undefined);
      if (currentProperty.current !== record.property.property_id) return;
      const output = advisorOutput(result);
      if (output) { setScenario(null); addOutput(output); }
      setMessages((value) => [...value, { role: 'assistant', text: result.explanation, result }]);
      setConfirm(needsPackageSelection(result));
      if (result.clarification_kind === 'package') setPackageIds([]);
    } catch (e) { if (currentProperty.current !== record.property.property_id) return; setMessages((value) => [...value, { role: 'assistant', text: (e as Error).message }]); }
    finally { setBusy(false); }
  }
  return <><div className="advisor-messages"><div className="advisor-intro"><span><Leaf size={22} strokeWidth={1.5} /></span><h3>A little clarity for<br />your next step.</h3><p>Make sense of your home’s performance and explore your next steps.</p></div>{!record ? <p className="advisor-hint">Select or enter a property in Assessment to start.</p> : <><div className="context-pill">{record.property.property_id} · {dirty ? 'Your property details' : 'Your home'}</div>{messages.length === 0 && <div className="suggestions">{['Why is my score low?', 'What if I install a heat pump?', 'What if I have only £5,000?'].map((text) => <button key={text} onClick={() => void send(text)}>{text}<ArrowUp size={13} /></button>)}</div>}</>}{messages.map((message, i) => <div key={i} className={`chat-message ${message.role}`}><span>{message.role === 'user' ? 'You' : 'Kew'}</span><p>{message.text.split('\n\nEvidence and limitations\n')[0]}</p>{message.text.includes('\n\nEvidence and limitations\n') && <details><summary>Evidence and limitations</summary><p>{message.text.split('\n\nEvidence and limitations\n')[1]}</p></details>}{message.result && <small>{message.result.mode === 'grounded_llm' ? 'Local AI · verified evidence' : message.result.fallback_reason ? 'Verified evidence · offline fallback' : 'Verified backend response'}{message.result.status === 'partial' ? ' · Partial data' : ''}</small>}{message.result && <ScenarioEvidence result={message.result} />}</div>)}{confirm && <div className="package-confirm"><strong>Confirm your complete package</strong><p>Select only the upgrades you want to simulate.</p>{ids.map((id) => <label key={id}><input type="checkbox" checked={packageIds.includes(id)} onChange={() => setPackageIds((value) => value.includes(id) ? value.filter((r) => r !== id) : [...value, id])} />{label(id)}</label>)}<button className="button primary" onClick={() => void send('Simulate my confirmed retrofit package', packageIds)}>Simulate selected package</button></div>}{busy && <div className="busy"><LoaderCircle size={17} className="spin" />{progress}</div>}<div ref={end} /></div><form className="advisor-input" onSubmit={(e) => { e.preventDefault(); void send(question); }}><label className="sr-only" htmlFor="advisor-question">Ask Kew a question</label><input id="advisor-question" placeholder="Ask about your home…" value={question} onChange={(e) => setQuestion(e.target.value)} disabled={!record || busy} maxLength={4000} /><button aria-label="Send question" disabled={!record || busy || !question.trim()}><ArrowUp size={18} /></button></form></>;
}
