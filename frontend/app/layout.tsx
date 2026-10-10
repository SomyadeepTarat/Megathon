import type { Metadata } from 'next';
import { Workspace } from '@/components/workspace';
import './globals.css';
export const metadata: Metadata = { title: 'Kew — A considered path to a greener home', description: 'Understand your home. Compare practical retrofits with transparent energy, carbon and cost estimates.' };
export default function Layout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en-GB"><body><Workspace>{children}</Workspace></body></html>;
}
