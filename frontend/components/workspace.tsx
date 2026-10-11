'use client';

import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { createContext, useContext, useEffect, useLayoutEffect, useRef, useState, type ReactNode, type Dispatch, type SetStateAction } from 'react';
import { ArrowUpRight, ChartNoAxesColumnIncreasing, ChevronRight, CircleHelp, House, Leaf, Menu, MessageCircle, RefreshCw, SlidersHorizontal, Trees, X } from 'lucide-react';
import { api } from '@/lib/api';
import type { Assessment, AssessmentRequest, PropertyRecord, PropertySummary, Scenario } from '@/lib/types';
import { label } from '@/lib/format';
import { Advisor } from './advisor';
import { scenarioOutput, type OutputSnapshot } from '@/lib/results';
import { OutputSummary } from './results';
import { previewOutputs } from '@/lib/ui-preview';
import { HomeJourney, ReplayJourney } from './home-journey';

import type { PlannerDraft } from '@/lib/planner';

interface State {
  plannerDraft: PlannerDraft | null; setPlannerDraft: Dispatch<SetStateAction<PlannerDraft | null>>;
  properties: PropertySummary[]; record: PropertyRecord | null; assessment: Assessment | null; scenario: Scenario | null;
  loading: boolean; error: string | null; dirty: boolean; service: 'checking' | 'online' | 'offline';
  selectProperty: (id: string) => Promise<void>; newProperty: () => void;
  edit: (record: PropertyRecord) => void; runAssessment: () => Promise<void>;
  outputs: OutputSnapshot[]; addOutput: (output: OutputSnapshot) => void; setScenario: (scenario: Scenario | null) => void; openAdvisor: () => void; refresh: () => void;
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
  const [showIntroduction, setShowIntroduction] = useState(() => pathname === '/');
  const [resumeIntroduction, setResumeIntroduction] = useState(false);
  const [returningToIntroduction, setReturningToIntroduction] = useState(false);
  const overviewEnteredAt = useRef(0);
  const viewRestored = useRef(false);
  useLayoutEffect(() => {
    if (viewRestored.current) return;
    viewRestored.current = true;
    const navigation = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming | undefined;
    let savedView: string | null = null;
    try { savedView = sessionStorage.getItem('kew-home-view'); } catch {}
    if ((navigation?.type === 'reload' || navigation?.type === 'back_forward') && savedView === 'overview') {
      setShowIntroduction(false);
      overviewEnteredAt.current = performance.now();
    }
  }, []);
  useEffect(() => {
    if (pathname !== '/') return;
    try { sessionStorage.setItem('kew-home-view', showIntroduction ? 'introduction' : 'overview'); } catch {}
  }, [pathname, showIntroduction]);
  const introductionActive = pathname === '/' && showIntroduction;
  const openOverview = () => {
    overviewEnteredAt.current = performance.now();
    setShowIntroduction(false);
    setResumeIntroduction(false);
    setReturningToIntroduction(false);
    window.scrollTo({ top: 0, behavior: 'instant' });
  };
  useEffect(() => {
    if (pathname !== '/') {
      setShowIntroduction(false);
      setReturningToIntroduction(false);
    } else {
      overviewEnteredAt.current = performance.now();
    }
  }, [pathname]);
  const finishIntroduction = () => {
    overviewEnteredAt.current = performance.now();
    setReturningToIntroduction(false);
    setShowIntroduction(false);
    window.scrollTo({ top: 0, behavior: 'instant' });
    requestAnimationFrame(() => { window.scrollTo({ top: 0, behavior: 'instant' }); document.getElementById('main')?.focus({ preventScroll: true }); });
  };
  const replayIntroduction = () => { window.scrollTo({ top: 0, behavior: 'instant' }); setResumeIntroduction(false); setShowIntroduction(true); };
  useEffect(() => {
    document.documentElement.classList.toggle('kew-introduction-active', introductionActive);
    return () => document.documentElement.classList.remove('kew-introduction-active');
  }, [introductionActive]);
  useEffect(() => {
    if (pathname !== '/' || introductionActive) return;
    let touchY = 0, switching = false;
    let timer: ReturnType<typeof setTimeout> | undefined;
    const returnToJourney = (event: Event) => {
      const node = event.target instanceof Element ? event.target : null;
      if (window.scrollY > 1 || switching || performance.now() - overviewEnteredAt.current < 800 || node?.closest('input, textarea, select, [role="dialog"]')) return;
      if (event.cancelable) event.preventDefault();
      switching = true;
      setReturningToIntroduction(true);
      timer = setTimeout(() => {
        setResumeIntroduction(true);
        setShowIntroduction(true);
        setReturningToIntroduction(false);
      }, window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 0 : 250);
    };
    const wheel = (event: WheelEvent) => { if (event.deltaY < -3) returnToJourney(event); };
    const touchStart = (event: TouchEvent) => { touchY = event.touches[0]?.clientY ?? 0; };
    const touchMove = (event: TouchEvent) => { if ((event.touches[0]?.clientY ?? 0) - touchY > 35) returnToJourney(event); };
    const key = (event: KeyboardEvent) => { if (event.key === 'ArrowUp' || event.key === 'PageUp') returnToJourney(event); };
    window.addEventListener('wheel', wheel, { passive: false });
    window.addEventListener('touchstart', touchStart, { passive: true });
    window.addEventListener('touchmove', touchMove, { passive: false });
    window.addEventListener('keydown', key);
    return () => { clearTimeout(timer); window.removeEventListener('wheel', wheel); window.removeEventListener('touchstart', touchStart); window.removeEventListener('touchmove', touchMove); window.removeEventListener('keydown', key); };
  }, [pathname, introductionActive]);
  const [plannerDraft, setPlannerDraft] = useState<PlannerDraft | null>(null);
  const [properties, setProperties] = useState<PropertySummary[]>([]);
  const [record, setRecord] = useState<PropertyRecord | null>(null);
  const [assessment, setAssessment] = useState<Assessment | null>(null);
  const [scenario, updateScenario] = useState<Scenario | null>(null);
  const [outputs, setOutputs] = useState<OutputSnapshot[]>([]);
  const [uiPreview, setUiPreview] = useState(false);
  useEffect(() => { setUiPreview(process.env.NODE_ENV !== 'production' && new URLSearchParams(window.location.search).get('ui-preview') === '1'); }, []);
  const visibleOutputs = uiPreview ? previewOutputs : outputs;
  const [dirty, setDirty] = useState(false); const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null); const [service, setService] = useState<State['service']>('checking');
  const [advisor, setAdvisor] = useState(false); const [mobile, setMobile] = useState(false);
  const version = useRef(0);
  const outputVersion = version.current;
  function addOutput(output: OutputSnapshot) {
    if (outputVersion !== version.current || output.propertyId !== record?.property.property_id) return;
    setOutputs((rows) => [...rows.filter((row) => row.id !== output.id), output].slice(-6));
  }
  function setScenario(value: Scenario | null) {
    if (value && outputVersion !== version.current) return;
    updateScenario(value);
    if (value && ['success', 'partial'].includes(value.status)) addOutput(scenarioOutput(value));
  }
  async function refresh() {
    setService('checking');
    try { const [, rows] = await Promise.all([api.health(), api.properties()]); setProperties(rows); setService('online'); }
    catch { setService('offline'); }
  }
  useEffect(() => { void refresh(); }, []);
  useEffect(() => { setMobile(false); }, [pathname]);
  async function selectProperty(id: string) {
    const token = ++version.current; setPlannerDraft(null); setLoading(true); setError(null); setRecord(null); setAssessment(null); setScenario(null); setOutputs([]); setDirty(false);
    try { const value = await api.property(id); if (token === version.current) setRecord(value); }
    catch (e) { if (token === version.current) setError((e as Error).message); }
    finally { if (token === version.current) setLoading(false); }
  }
  function edit(value: PropertyRecord) { version.current++; setPlannerDraft(null); setLoading(false); setRecord(value); setDirty(true); setAssessment(null); setScenario(null); setOutputs([]); setError(null); }
  function newProperty() { version.current++; setPlannerDraft(null); setLoading(false); setRecord(blankProperty()); setAssessment(null); setScenario(null); setOutputs([]); setDirty(true); setError(null); router.push('/assessment'); }
  async function runAssessment() {
    if (!record) return;
    const token = ++version.current; setLoading(true); setError(null);
    try { const result = await api.assessFull(inputOf(record)); if (token === version.current) { setAssessment(result); setScenario(null); } }
    catch (e) { if (token === version.current) setError((e as Error).message); }
    finally { if (token === version.current) setLoading(false); }
  }
  const title = pathname === '/ranking' ? 'Property ranking' : pathname === '/compare' ? 'Scenario comparison' : navigation.find((item) => item.href === pathname)?.name || 'Workspace';
  const value: State = { plannerDraft, setPlannerDraft, properties, record, assessment, scenario, dirty, loading, error, service, selectProperty, newProperty, edit, runAssessment, outputs: visibleOutputs, addOutput, setScenario, openAdvisor: () => setAdvisor(true), refresh };
  return <Context.Provider value={value}>
    {introductionActive && <HomeJourney onComplete={finishIntroduction} resumeFromEnd={resumeIntroduction} />}
    <a href="#main" className="skip-link">Skip to content</a>
    <div id="kew-workspace" hidden={introductionActive} className={`app-shell ${returningToIntroduction ? 'is-returning-to-intro' : ''} ${pathname === '/' ? 'journey-workspace' : ''}`}>
      {mobile && <button className="nav-backdrop" aria-label="Close navigation" onClick={() => setMobile(false)} />}
      <aside id="workspace-navigation" className={`sidebar ${mobile ? 'is-open' : ''}`}>
        <Link href="/" onClick={openOverview} className="brand" aria-label="Kew home"><span className="brand-mark"><Leaf size={24} strokeWidth={1.6} /></span><span className="intro-wordmark">Kew</span></Link>
        <div className="nav-heading">Your workspace</div>
        <nav aria-label="Main navigation">{navigation.map(({ href, name, icon: Icon }) => <Link key={href} href={href} onClick={href === "/" ? openOverview : undefined} aria-current={pathname === href || (href === '/portfolio' && pathname === '/ranking') || (href === '/planner' && pathname === '/compare') ? 'page' : undefined} className={`nav-link ${pathname === href || (href === '/portfolio' && pathname === '/ranking') || (href === '/planner' && pathname === '/compare') ? 'active' : ''}`}><Icon size={19} strokeWidth={1.6} />{name}</Link>)}</nav>
        <div className="sidebar-bottom"><div className="sidebar-note"><span className="mini-label">A little clarity.</span><p>A better future starts<br />with understanding home.</p><Leaf size={28} strokeWidth={1} /></div><button className="nav-link help-link" onClick={() => setAdvisor(true)}><CircleHelp size={18} /> Ask Kew</button><div className="profile"><span className="avatar">YH</span><div>Your home workspace<small>Personal assessment</small></div></div></div>
      </aside>
      <div className="main-shell"><header className="topbar"><div className="breadcrumb"><button className="icon-button mobile-menu" onClick={() => setMobile(!mobile)} aria-label="Open navigation" aria-expanded={mobile} aria-controls="workspace-navigation"><Menu size={21} /></button><Link href="/" onClick={openOverview}>Kew</Link><ChevronRight size={14} /><span>{title}</span></div><div className="header-actions"><span className={`service-state ${service}`}><i />{service === 'online' ? 'Your workspace' : service === 'checking' ? 'Loading…' : 'Service unavailable'}</span><button className="icon-button" onClick={() => void refresh()} aria-label="Refresh properties"><RefreshCw size={18} /></button><span className="header-separator" /><button className="icon-button" aria-label="Open Kew advisor" onClick={() => setAdvisor(true)}><MessageCircle size={20} /></button></div></header>
        {service === 'offline' && <div className="connection-notice" role="status">The assessment service is offline. You can explore Kew and enter your details. <button onClick={() => void refresh()}>Reconnect <ArrowUpRight size={13} /></button></div>}
        <main id="main" tabIndex={-1} className="main-content">{uiPreview && <div className="notice warning" role="status"><div><strong>Dummy UI preview</strong><p>These figures are invented for design review. They are not model results and are not saved.</p><button className="button secondary" onClick={() => setAdvisor(true)}>Preview Ask Kew</button> <Link className="button secondary" href="/compare" onClick={() => { setUiPreview(false); setAdvisor(false); }}>Exit dummy preview</Link></div></div>}{pathname === '/' && <ReplayJourney onReplay={replayIntroduction} />}{children}</main>
        <footer className="footer"><span><Leaf size={13} /> Kew · A considered path to a greener home</span><span>Transparent estimates. Informed decisions.</span></footer>
      </div>
    </div>
    {!introductionActive && !advisor && <button className="advisor-launch" onClick={() => setAdvisor(true)}><span className="advisor-dot"><Leaf size={16} /></span>Ask Kew<ArrowUpRight size={15} /></button>}
    {advisor && <section className="advisor-panel" role="dialog" aria-modal="false" aria-label="Kew advisor"><header><div><span className="brand-mark"><Leaf size={18} /></span><div><strong>Ask Kew</strong><small>{uiPreview ? 'Dummy UI preview · invented figures' : 'Your home, explained.'}</small></div></div><button className="icon-button" onClick={() => setAdvisor(false)} aria-label="Close advisor"><X size={19} /></button></header><div className="advisor-body"><aside className="advisor-results"><OutputSummary output={visibleOutputs.at(-1)} assessment={assessment} /><Link href="/compare" className="button secondary" onClick={() => setAdvisor(false)}>Compare packages <ArrowUpRight size={14} /></Link></aside><div className="advisor-conversation"><Advisor key={JSON.stringify(record)} /></div></div></section>}
  </Context.Provider>;
}
