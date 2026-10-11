'use client';
import { useEffect, useRef, useState } from 'react';
import './opening-intro.css';
type AutumnScene = { render: (seconds: number, handoff?: number) => boolean; resize: () => void; dispose: () => void };
export function OpeningIntro() {
  const [finished, setFinished] = useState(false);
  const logo = useRef<HTMLDivElement>(null);
  const canvas = useRef<HTMLCanvasElement>(null);
  useEffect(() => {
    // Wait for the restored Overview/introduction layout before measuring its logo.
    // Otherwise reload can capture the outgoing introduction's brand position.
    let cleanup: (() => void) | undefined;
    const setup = requestAnimationFrame(() => {
    const media = window.matchMedia('(prefers-reduced-motion: reduce)');
    if (media.matches) { setFinished(true); return; }
    let active = true, frame = 0, scene: AutumnScene | undefined;
    let textFade: Animation | undefined;
    const element = logo.current!;
    element.parentElement?.classList.remove('has-arrived');
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
      element.parentElement?.classList.add('has-arrived');
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
      const destination = symbol?.getBoundingClientRect();
      element.style.left = `${destination?.left ?? 24}px`;
      element.style.top = `${destination?.top ?? 24}px`;
      const start = performance.now();
      // Rendered arrival and logo opacity share one animation clock. A delayed
      // frame cannot reveal the logo before the travelling leaf is in place.
      await new Promise<void>((resolve) => {
        let arrivedAt: number | undefined;
        const tick = (now: number) => {
          if (!active) { resolve(); return; }
          const destination = symbol?.getBoundingClientRect();
          element.style.left = `${destination?.left ?? 24}px`;
          element.style.top = `${destination?.top ?? 24}px`;
          const seconds = (now - start) / 1000;
          const blend = arrivedAt === undefined ? 0 : Math.min(1, (now - arrivedAt) / 200);
          const arrived = scene ? scene.render(seconds, blend) : seconds >= 3.15;
          if (arrived && arrivedAt === undefined) arrivedAt = now;
          element.style.opacity = String(blend);
          if (blend < 1) frame = requestAnimationFrame(tick);
          else resolve();
        };
        frame = requestAnimationFrame(tick);
      });
      if (!active) return;
      restore(); element.style.display = 'none';
      if (wordmark) textFade = wordmark.animate([{ opacity: 0 }, { opacity: 1 }], { duration: 450, easing: 'ease-out' });
      if (textFade) { try { await textFade.finished; } catch {} }
      if (active) { scene?.dispose(); scene = undefined; setFinished(true); }
    };
    void run();
    const reduce = () => { if (media.matches) { active = false; restore(); textFade?.cancel(); cancelAnimationFrame(frame); scene?.dispose(); scene = undefined; setFinished(true); } };
    window.addEventListener('resize', resize);
    media.addEventListener('change', reduce);
    cleanup = () => { active = false; restore(); textFade?.cancel(); cancelAnimationFrame(frame); scene?.dispose(); element.replaceChildren(); window.removeEventListener('resize', resize); media.removeEventListener('change', reduce); };
    });
    return () => { cancelAnimationFrame(setup); cleanup?.(); };
  }, []);
  if (finished) return null;
  return <div className="opening-intro" aria-hidden="true"><div className="opening-backdrop" /><canvas ref={canvas} className="opening-autumn-canvas" /><div className="opening-logo" ref={logo} /></div>;
}
