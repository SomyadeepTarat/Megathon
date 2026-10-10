'use client';
import { useEffect, useRef, useState } from 'react';
import './opening-intro.css';
type AutumnScene = { render: (seconds: number) => void; resize: () => void; dispose: () => void };
export function OpeningIntro() {
  const [finished, setFinished] = useState(false);
  const logo = useRef<HTMLDivElement>(null);
  const canvas = useRef<HTMLCanvasElement>(null);
  useEffect(() => {
    const media = window.matchMedia('(prefers-reduced-motion: reduce)');
    if (media.matches) { setFinished(true); return; }
    let active = true, frame = 0, scene: AutumnScene | undefined;
    let flight: Animation | undefined, textFade: Animation | undefined;
    const element = logo.current!;
    const target = Array.from(document.querySelectorAll<HTMLElement>('.kew-journey-brand, .brand')).find(node => {
      const r = node.getBoundingClientRect(); return r.width > 0 && r.left >= 0 && r.top >= 0 && r.top < innerHeight;
    });
    const symbol = target?.querySelector<HTMLElement>('.brand-mark') ?? target?.querySelector<SVGSVGElement>('svg');
    const wordmark = target?.querySelector<HTMLElement>('.intro-wordmark');
    const originalSymbolVisibility = symbol?.style.visibility ?? '';
    const originalTextVisibility = wordmark?.style.visibility ?? '';
    if (symbol) {
      const copy = symbol.cloneNode(true) as HTMLElement;
      copy.style.visibility = 'visible';
      element.replaceChildren(copy);
      symbol.style.visibility = 'hidden';
    }
    if (wordmark) wordmark.style.visibility = 'hidden';
    const restore = () => {
      if (symbol) symbol.style.visibility = originalSymbolVisibility;
      if (wordmark) wordmark.style.visibility = originalTextVisibility;
    };
    const resize = () => { scene?.resize(); };
    const run = async () => {
      try {
        const modulePath = '/kew-journey/autumn.js';
        const module = await import(/* webpackIgnore: true */ modulePath) as { createAutumnScene: (canvas: HTMLCanvasElement, destination: () => DOMRect, logoSvg?: SVGSVGElement) => AutumnScene };
        if (!active) return;
        const logoSvg = symbol instanceof SVGSVGElement ? symbol : symbol?.querySelector<SVGSVGElement>('svg');
        scene = module.createAutumnScene(canvas.current!, () => logoSvg?.getBoundingClientRect() ?? symbol?.getBoundingClientRect() ?? new DOMRect(24,24,28,28), logoSvg ?? undefined);
      } catch { /* The logo sequence still works when WebGL is unavailable. */ }
      if (!active) return;
      const start = performance.now();
      const tick = (now: number) => {
        if (!active) return;
        scene?.render((now - start) / 1000);
        if (now - start < 3700) frame = requestAnimationFrame(tick);
      };
      frame = requestAnimationFrame(tick);
      const destination = symbol?.getBoundingClientRect();
      element.style.left = `${destination?.left ?? 24}px`;
      element.style.top = `${destination?.top ?? 24}px`;
      flight = element.animate([
        { opacity: 0, offset: 0 },
        { opacity: 0, offset: 3150 / 3350 },
        { opacity: 1, offset: 1 },
      ], { duration: 3350, easing: 'linear', fill: 'forwards' });
      try { await flight.finished; } catch { return; }
      if (!active) return;
      restore(); element.style.display = 'none';
      if (wordmark) textFade = wordmark.animate([{ opacity: 0 }, { opacity: 1 }], { duration: 450, easing: 'ease-out' });
      if (textFade) { try { await textFade.finished; } catch {} }
      if (active) { scene?.dispose(); scene = undefined; setFinished(true); }
    };
    void run();
    const reduce = () => { if (media.matches) { active = false; restore(); flight?.cancel(); textFade?.cancel(); cancelAnimationFrame(frame); scene?.dispose(); scene = undefined; setFinished(true); } };
    window.addEventListener('resize', resize);
    media.addEventListener('change', reduce);
    return () => { active = false; restore(); flight?.cancel(); textFade?.cancel(); cancelAnimationFrame(frame); scene?.dispose(); element.replaceChildren(); window.removeEventListener('resize', resize); media.removeEventListener('change', reduce); };
  }, []);
  if (finished) return null;
  return <div className="opening-intro" aria-hidden="true"><div className="opening-backdrop" /><canvas ref={canvas} className="opening-autumn-canvas" /><div className="opening-logo" ref={logo} /></div>;
}
