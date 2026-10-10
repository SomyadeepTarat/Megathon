'use client';

import { useEffect, useRef, useState } from 'react';
import { ArrowDown, ArrowUpRight, Leaf, Sun, Wind, Layers } from 'lucide-react';
import './home-journey.css';

type JourneyScene = { resize: (width: number, height: number) => void; render: (progress: number) => void; dispose: (releaseContext?: boolean) => void };
const smooth = (a: number, b: number, value: number) => {
  const t = Math.max(0, Math.min(1, (value - a) / (b - a)));
  return t * t * (3 - 2 * t);
};

export function HomeJourney() {
  const root = useRef<HTMLElement>(null);
  const canvas = useRef<HTMLCanvasElement>(null);
  const [mode, setMode] = useState<'loading' | 'ready' | 'static'>('loading');

  useEffect(() => {
    const section = root.current!;
    const surface = canvas.current!;
    const stage = section.querySelector<HTMLElement>('.kew-journey-stage')!;
    const media = window.matchMedia('(prefers-reduced-motion: reduce)');
    let scene: JourneyScene | undefined;
    let disposed = false, visible = false, loading = false, failed = false;
    let frame = 0, actual = 0, target = 0, last = 0;
    let generation = 0;
    const fade = (selector: string, value: number) => {
      const element = section.querySelector<HTMLElement>(selector)!;
      element.style.opacity = String(value);
      element.style.visibility = value < .01 ? 'hidden' : 'visible';
    };
    const paint = (p: number) => {
      scene?.render(p);
      fade('.kew-city-copy', 1 - smooth(.16, .32, p));
      fade('.kew-eco-copy', smooth(.35, .47, p) * (1 - smooth(.76, .84, p)));
      fade('.kew-land-copy', smooth(.82, .9, p));
      fade('.kew-solar', smooth(.48, .56, p) * (1 - smooth(.79, .87, p)));
      fade('.kew-insulation', smooth(.57, .65, p) * (1 - smooth(.79, .87, p)));
      fade('.kew-pump', smooth(.65, .73, p) * (1 - smooth(.79, .87, p)));
      fade('.kew-scroll-cue', 1 - smooth(.08, .18, p));
      surface.style.opacity = String(1 - smooth(.93, 1, p));
    };
    const stop = () => { cancelAnimationFrame(frame); frame = 0; last = 0; };
    const tick = (now: number) => {
      frame = 0;
      if (!visible || document.hidden || !scene || media.matches) return;
      const dt = last ? Math.min((now - last) / 1000, .08) : 1 / 60;
      last = now;
      actual += (target - actual) * (1 - Math.exp(-dt * 9));
      if (Math.abs(target - actual) < .0005) actual = target;
      paint(actual);
      // No perpetual loop: only render until the scroll position settles.
      if (actual !== target) frame = requestAnimationFrame(tick);
      else last = 0;
    };
    const schedule = () => {
      if (!frame && visible && !document.hidden && scene && !media.matches) frame = requestAnimationFrame(tick);
    };
    const scroll = () => {
      const bounds = section.getBoundingClientRect();
      target = Math.max(0, Math.min(1, -bounds.top / Math.max(1, bounds.height - stage.clientHeight)));
      schedule();
    };
    const resize = () => { scene?.resize(stage.clientWidth, stage.clientHeight); scroll(); };
    const initialize = async () => {
      if (disposed || scene || loading || failed || media.matches || !visible || document.hidden) return;
      loading = true;
      const token = ++generation;
      try {
        // The supplied local vendor modules stay out of the server bundle.
        const modulePath = '/kew-journey/scene.js';
        const module = await import(/* webpackIgnore: true */ modulePath) as { createJourneyScene: (canvas: HTMLCanvasElement) => JourneyScene };
        if (disposed || token !== generation || media.matches || !visible || document.hidden) return;
        scene = module.createJourneyScene(surface);
        setMode('ready');
        resize();
        actual = target;
        paint(actual);
      } catch {
        if (!disposed) { failed = true; scene?.dispose(); scene = undefined; setMode('static'); }
      } finally {
        loading = false;
        if (!disposed && token !== generation) void initialize();
      }
    };
    const motion = () => {
      generation++;
      stop();
      if (media.matches) {
        scene?.dispose(); scene = undefined;
        setMode('static');
      } else {
        setMode(failed ? 'static' : 'loading');
        void initialize();
      }
    };
    const visibility = () => {
      if (document.hidden) stop();
      else { scroll(); void initialize(); }
    };
    const contextLost = (event: Event) => {
      if (disposed || media.matches || !scene) return;
      event.preventDefault();
      stop(); failed = true;
      scene?.dispose(); scene = undefined;
      setMode('static');
    };
    const observer = new IntersectionObserver(([entry]) => {
      visible = entry.isIntersecting;
      if (visible) { scroll(); void initialize(); }
      else stop();
    });
    observer.observe(section);
    const sizeObserver = new ResizeObserver(resize);
    sizeObserver.observe(stage);
    window.addEventListener('scroll', scroll, { passive: true });
    document.addEventListener('visibilitychange', visibility);
    media.addEventListener('change', motion);
    surface.addEventListener('webglcontextlost', contextLost);
    if (media.matches) setMode('static');
    return () => {
      disposed = true; generation++;
      stop(); observer.disconnect(); sizeObserver.disconnect();
      window.removeEventListener('scroll', scroll);
      document.removeEventListener('visibilitychange', visibility);
      media.removeEventListener('change', motion);
      surface.removeEventListener('webglcontextlost', contextLost);
      scene?.dispose(true);
    };
  }, []);

  const skip = () => {
    const workspace = document.getElementById('kew-workspace');
    workspace?.scrollIntoView({ behavior: 'auto', block: 'start' });
    document.getElementById('main')?.focus({ preventScroll: true });
  };

  return <section ref={root} id="kew-journey" className={`kew-journey ${mode === 'static' ? 'is-static' : ''}`} aria-label="An illustrated journey from London to your home">
    <div className="kew-journey-stage">
      <canvas ref={canvas} aria-hidden="true" />
      <div className="kew-journey-wash" />
      <header className="kew-journey-header"><span className="kew-journey-brand"><Leaf size={28} /> Kew <small>A greener way home.</small></span><button onClick={skip}>Skip to Overview <ArrowUpRight size={16} /></button></header>
      <div className="kew-journey-copy kew-city-copy"><span className="eyebrow">A different perspective</span><h1>Every city.<br />Every street.<br /><em>Every home.</em></h1><p>A greener future begins<br />closer than you think.</p></div>
      <div className="kew-journey-copy kew-eco-copy"><span className="eyebrow">Small changes. Better homes.</span><h2>See the<br /><em>possibilities.</em></h2><p>From the roof above you<br />to the energy that warms you.</p></div>
      <div className="kew-journey-copy kew-land-copy"><span className="eyebrow">Your home, understood</span><h2>A little more<br /><em>clarity.</em></h2><p>Your Kew Overview is just below.</p><button className="button primary" onClick={skip}>Explore your home <ArrowDown size={16} /></button></div>
      <div className="kew-journey-callouts" aria-hidden="true">
        <div className="kew-callout kew-solar"><Sun size={23} /><div><strong>Solar panels</strong><span>Explore electricity from the sun.</span></div></div>
        <div className="kew-callout kew-insulation"><Layers size={23} /><div><strong>Insulation</strong><span>Help keep warmth inside the home.</span></div></div>
        <div className="kew-callout kew-pump"><Wind size={23} /><div><strong>Heat pump</strong><span>Move heat from outside to inside.</span></div></div>
      </div>
      <p className="sr-only">The illustrated city descends to a home. Solar panels can generate electricity; insulation can retain warmth; a heat pump can transfer heat from outdoors. These are illustrations, not recommendations or calculated savings.</p>
      {mode === 'loading' && <span className="kew-journey-status" role="status">Drawing a greener perspective…</span>}
      {mode === 'static' && <div className="kew-journey-fallback"><img src="/home.svg" alt="An illustrated home with solar panels and a garden" /><p>Solar panels · Insulation · Heat pump</p><p>Explore the possibilities for your home in Overview.</p><button className="button primary" onClick={skip}>Continue to Overview <ArrowDown size={16} /></button></div>}
      <div className="kew-journey-note">London · An illustrated journey<small>Illustrative possibilities, not recommendations or calculated savings.</small></div>
      <span className="kew-scroll-cue"><ArrowDown size={17} /> Scroll to find your way home</span>
    </div>
  </section>;
}

export function ReplayJourney() {
  return <button className="kew-replay" onClick={() => {
    const journey = document.getElementById('kew-journey');
    journey?.scrollIntoView({ behavior: 'auto', block: 'start' });
    journey?.querySelector<HTMLButtonElement>('button')?.focus({ preventScroll: true });
  }}>↖ Replay introduction</button>;
}
