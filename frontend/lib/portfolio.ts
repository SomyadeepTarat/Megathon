import type { PortfolioRow } from './types.ts';
export function compareRows(a: PortfolioRow, b: PortfolioRow, field: keyof PortfolioRow, direction: 'asc' | 'desc') {
  const x = a[field], y = b[field];
  if (x == null && y == null) return 0;
  if (x == null) return 1;
  if (y == null) return -1;
  const difference = typeof x === 'number' && typeof y === 'number' ? x - y : String(x).localeCompare(String(y));
  return direction === 'asc' ? difference : -difference;
}
