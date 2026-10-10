export function number(value: number | null | undefined, unit = '', decimals = 0): string {
  return value === null || value === undefined || !Number.isFinite(value) ? 'Unavailable' : `${new Intl.NumberFormat('en-GB', { maximumFractionDigits: decimals }).format(value)}${unit ? ` ${unit}` : ''}`;
}
export function money(value: number | null | undefined): string {
  return value === null || value === undefined || !Number.isFinite(value) ? 'Unavailable' : new Intl.NumberFormat('en-GB', { style: 'currency', currency: 'GBP', maximumFractionDigits: 0 }).format(value);
}
export function label(value: string | null | undefined): string {
  return value ? value.replaceAll('_', ' ').replace(/^./, (c) => c.toUpperCase()) : 'Not provided';
}
export function numericInput(value: string): number | null { return value.trim() === '' ? null : Number(value); }
