'use client';

import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { createContext, useContext, useEffect, useRef, useState, type ReactNode } from 'react';
import { ArrowUpRight, ChartNoAxesColumnIncreasing, ChevronRight, CircleHelp, House, Leaf, Menu, MessageCircle, RefreshCw, SlidersHorizontal, Trees, X } from 'lucide-react';
import { api } from '@/lib/api';
import type { Assessment, AssessmentRequest, PropertyRecord, PropertySummary, Scenario } from '@/lib/types';
import { label } from '@/lib/format';
import { Advisor } from './advisor';
import { HomeJourney, ReplayJourney } from './home-journey';

interface State {
  properties: PropertySummary[]; record: PropertyRecord | null; assessment: Assessment | null; scenario: Scenario | null;
  loading: boolean; error: string | null; dirty: boolean; service: 'checking' | 'online' | 'offline';
  selectProperty: (id: string) => Promise<void>; newProperty: () => void;
  edit: (record: PropertyRecord) => void; runAssessment: () => Promise<void>;
  setScenario: (scenario: Scenario | null) => void; openAdvisor: () => void; refresh: () => void;
}
const Context = createContext<State | null>(null);
export function useWorkspace() { const value = useContext(Context); if (!value) throw new Error('Workspace missing'); return value; }
export function inputOf(record: PropertyRecord): AssessmentRequest { return { property: record.property, annual_energy: record.annual_energy, benchmark: record.benchmark, emission_factors: record.emission_factors, retrofit_costs: record.retrofit_costs, electricity_tariff_gbp_per_kwh: record.electricity_tariff_gbp_per_kwh, gas_tariff_gbp_per_kwh: record.gas_tariff_gbp_per_kwh }; }
export function blankProperty(): PropertyRecord {
  return { property: { property_id: `HOME-${Date.now()}`, property_type: 'detached', region: '', floor_area_m2: 0, property_age_years: null, bedrooms: null, energy_rating: null, insulation: null, heating_system: null, glazing: null, renewable_contribution: null, smart_controls: null, roof_suitable_for_loft: null, roof_suitable_for_solar: null, heat_pump_compatible: null, controls_compatible: null, current_property_value_gbp: null, market_index: null, provenance: {} }, annual_energy: { electricity_kwh: null, gas_kwh: null, quality: 'missing', method: 'User-provided annual totals; no readings supplied yet', electricity_months_covered: 0, gas_months_covered: 0, warnings: [] }, benchmark: null, dataset_kind: 'observed', dataset_source: 'User-provided property details; energy quality is declared separately' };
}
const navigation = [{ href: '/', name: 'Overview', icon: House }, { href: '/assessment', name: 'Assessment', icon: ChartNoAxesColumnIncreasing }, { href: '/planner', name: 'Retrofit planner', icon: SlidersHorizontal }, { href: '/portfolio', name: 'Portfolio', icon: Trees }];

export function Workspace({ children }: { children: ReactNode }) {
  const pathname = usePathname(); const router = useRouter();
  const [properties, setProperties] = useState<PropertySummary[]>([]);
  const [record, setRecord] = useState<PropertyRecord | null>(null);
  const [assessment, setAssessment] = useState<Assessment | null>(null);
  const [scenario, setScenario] = useState<Scenario | null>(null);
  const [dirty, setDirty] = useState(false); const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null); const [service, setService] = useState<State['service']>('checking');
  const [advisor, setAdvisor] = useState(false); const [mobile, setMobile] = useState(false);
  const version = useRef(0);
  async function refresh() {
    setService('checking');
    try { const [, rows] = await Promise.all([api.health(), api.properties()]); setProperties(rows); setService('online'); }
    catch { setService('offline'); }
  }
  useEffect(() => { void refresh(); }, []);
  useEffect(() => { setMobile(false); }, [pathname]);
  async function selectProperty(id: string) {
    const token = ++version.current; setLoading(true); setError(null); setRecord(null); setAssessment(null); setScenario(null); setDirty(false);
    try { const value = await api.property(id); if (token === version.current) setRecord(value); }
    catch (e) { if (token === version.current) setError((e as Error).message); }
    finally { if (token === version.current) setLoading(false); }
  }
  function edit(value: PropertyRecord) { version.current++; setLoading(false); setRecord(value); setDirty(true); setAssessment(null); setScenario(null); setError(null); }
  function newProperty() { version.current++; setLoading(false); setRecord(blankProperty()); setAssessment(null); setScenario(null); setDirty(true); setError(null); router.push('/assessment'); }
  async function runAssessment() {
    if (!record) return;
    const token = ++version.current; setLoading(true); setError(null);
    try { const result = await api.assessFull(inputOf(record)); if (token === version.current) { setAssessment(result); setScenario(null); } }
    catch (e) { if (token === version.current) setError((e as Error).message); }
    finally { if (token === version.current) setLoading(false); }
  }
  const title = pathname === '/compare' ? 'Scenario comparison' : navigation.find((item) => item.href === pathname)?.name || 'Workspace';
  const value: State = { properties, record, assessment, scenario, dirty, loading, error, service, selectProperty, newProperty, edit, runAssessment, setScenario, openAdvisor: () => setAdvisor(true), refresh };
  return <Context.Provider value={value}>
    {pathname === '/' && <HomeJourney />}
    <a href="#main" className="skip-link">Skip to content</a>
    <div id="kew-workspace" className={`app-shell ${pathname === '/' ? 'journey-workspace' : ''}`}>
      {mobile && <button className="nav-backdrop" aria-label="Close navigation" onClick={() => setMobile(false)} />}
      <aside id="workspace-navigation" className={`sidebar ${mobile ? 'is-open' : ''}`}>
        <Link href="/" className="brand" aria-label="Kew home"><span className="brand-mark"><Leaf size={24} strokeWidth={1.6} /></span><span>Kew<span className="brand-caption">A greener way home.</span></span></Link>
        <div className="nav-heading">Your workspace</div>
        <nav aria-label="Main navigation">{navigation.map(({ href, name, icon: Icon }) => <Link key={href} href={href} aria-current={pathname === href || (href === '/planner' && pathname === '/compare') ? 'page' : undefined} className={`nav-link ${pathname === href || (href === '/planner' && pathname === '/compare') ? 'active' : ''}`}><Icon size={19} strokeWidth={1.6} />{name}</Link>)}</nav>
        <div className="sidebar-bottom"><div className="sidebar-note"><span className="mini-label">A little clarity.</span><p>A better future starts<br />with understanding home.</p><Leaf size={28} strokeWidth={1} /></div><button className="nav-link help-link" onClick={() => setAdvisor(true)}><CircleHelp size={18} /> Ask Kew</button><div className="profile"><span className="avatar">YH</span><div>Your home workspace<small>Personal assessment</small></div></div></div>
      </aside>
      <div className="main-shell"><header className="topbar"><div className="breadcrumb"><button className="icon-button mobile-menu" onClick={() => setMobile(!mobile)} aria-label="Open navigation" aria-expanded={mobile} aria-controls="workspace-navigation"><Menu size={21} /></button><Link href="/">Kew</Link><ChevronRight size={14} /><span>{title}</span></div><div className="header-actions"><span className={`service-state ${service}`}><i />{service === 'online' ? 'Your workspace' : service === 'checking' ? 'Loading…' : 'Service unavailable'}</span><button className="icon-button" onClick={() => void refresh()} aria-label="Refresh properties"><RefreshCw size={18} /></button><span className="header-separator" /><button className="icon-button" aria-label="Open Kew advisor" onClick={() => setAdvisor(true)}><MessageCircle size={20} /></button></div></header>
        {service === 'offline' && <div className="connection-notice" role="status">The assessment service is offline. You can explore Kew and enter your details. <button onClick={() => void refresh()}>Reconnect <ArrowUpRight size={13} /></button></div>}
        <main id="main" tabIndex={-1} className="main-content">{pathname === '/' && <ReplayJourney />}{children}</main>
        <footer className="footer"><span><Leaf size={13} /> Kew · A considered path to a greener home</span><span>Transparent estimates. Informed decisions.</span></footer>
      </div>
    </div>
    {!advisor && <button className="advisor-launch" onClick={() => setAdvisor(true)}><span className="advisor-dot"><Leaf size={16} /></span>Ask Kew<ArrowUpRight size={15} /></button>}
    {advisor && <section className="advisor-panel" role="dialog" aria-modal="false" aria-label="Kew advisor"><header><div><span className="brand-mark"><Leaf size={18} /></span><div><strong>Ask Kew</strong><small>Your home, explained.</small></div></div><button className="icon-button" onClick={() => setAdvisor(false)} aria-label="Close advisor"><X size={19} /></button></header><Advisor key={JSON.stringify(record)} /></section>}
  </Context.Provider>;
}
