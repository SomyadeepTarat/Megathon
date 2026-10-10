'use client';
import { AlertCircle, ArrowRight, ChevronRight, Info, LoaderCircle } from 'lucide-react';
import Link from 'next/link';
import type { ReactNode } from 'react';
import { useWorkspace } from './workspace';
import { number } from '@/lib/format';

export function Eyebrow({ children }: { children: ReactNode }) { return <div className="eyebrow"><span />{children}</div>; }
export function PageHeading({ eyebrow, title, description, action }: { eyebrow: string; title: string; description: string; action?: ReactNode }) { return <div className="page-heading"><div><Eyebrow>{eyebrow}</Eyebrow><h1>{title}</h1><p>{description}</p></div>{action}</div>; }
export function Notice({ children, tone = 'neutral' }: { children: ReactNode; tone?: 'neutral' | 'warning' | 'error' }) { return <div className={`notice ${tone}`} role={tone === 'error' ? 'alert' : 'status'}>{tone === 'neutral' ? <Info size={17} /> : <AlertCircle size={17} />}<div>{children}</div></div>; }
export function Badge({ children, tone = '' }: { children: ReactNode; tone?: string }) { return <span className={`badge ${tone}`}>{children}</span>; }
export function Busy({ text = 'Loading your home…' }: { text?: string }) { return <div className="busy" role="status"><LoaderCircle className="spin" size={20} />{text}</div>; }
export function Empty({ title, children, action }: { title: string; children: ReactNode; action?: ReactNode }) { return <div className="empty-state"><span className="empty-icon"><Info size={23} /></span><h3>{title}</h3><p>{children}</p>{action}</div>; }
export function NeedProperty() { return <Empty title="Let’s start with your home." action={<Link href="/assessment" className="button primary">Select a property <ArrowRight size={16} /></Link>}>Select a property or enter your own details to create a considered retrofit plan.</Empty>; }
export function PropertySelect() { const { properties, record, selectProperty, newProperty, loading } = useWorkspace(); return <div className="property-select"><label htmlFor="home-select">Your property</label><div><select id="home-select" value={record?.property.property_id || ''} onChange={(e) => { if (e.target.value) void selectProperty(e.target.value); }} disabled={loading}><option value="">Select a property</option>{record && !properties.some((p) => p.property_id === record.property.property_id) && <option value={record.property.property_id}>Your entered property</option>}{properties.map((p) => <option key={p.property_id} value={p.property_id}>{p.property_id} · {p.region} · {p.property_type.replaceAll('_', ' ')}</option>)}</select><button className="button secondary" onClick={newProperty}>Enter my own home <ChevronRight size={15} /></button></div></div>; }
export function Metric({ title, value, unit, note }: { title: string; value: number | null | undefined; unit?: string; note?: string }) { return <div className="metric"><span>{title}</span><strong className={value == null ? 'unavailable' : ''}>{number(value, '', 1)}{value != null && unit && <small>{unit}</small>}</strong>{note && <p>{note}</p>}</div>; }
