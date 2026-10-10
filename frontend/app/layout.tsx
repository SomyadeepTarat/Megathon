import type { Metadata } from 'next';
import { Workspace } from '@/components/workspace';
import { OpeningIntro } from '@/components/opening-intro';
import './globals.css';
export const metadata: Metadata = { title: 'Kew — A considered path to a greener home', description: 'Understand your home. Compare practical retrofits with transparent energy, carbon and cost estimates.' };
export default function Layout({ children }: Readonly<{ children: React.ReactNode }>) {
  // Extensions can add crxlauncher attributes before React hydrates this element.
  return <html lang="en-GB" suppressHydrationWarning><body><OpeningIntro /><Workspace>{children}</Workspace></body></html>;
}
