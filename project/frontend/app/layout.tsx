import type { Metadata } from 'next';
import { Workspace } from '@/components/workspace';
import { OpeningIntro } from '@/components/opening-intro';
import './globals.css';
export const metadata: Metadata = { title: 'Kew', description: 'Assess your home and compare retrofit options, energy use, carbon and costs.' };
export default function Layout({ children }: Readonly<{ children: React.ReactNode }>) {
  // Extensions can add crxlauncher attributes before React hydrates this element.
  return <html lang="en-GB" suppressHydrationWarning><body><OpeningIntro /><Workspace>{children}</Workspace></body></html>;
}
