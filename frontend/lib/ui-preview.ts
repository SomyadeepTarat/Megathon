import type { OutputSnapshot } from './results';

const base: OutputSnapshot = {
  id: 'ui-preview-1', propertyId: 'DUMMY-HOME', status: 'success', upgrades: ['loft_insulation'],
  beforeScore: 38, afterScore: 52, beforeClass: 'Poor', afterClass: 'Moderate',
  beforeElectricity: 4000, afterElectricity: 4000, beforeGas: 16000, afterGas: 13500,
  electricitySavings: 0, gasSavings: 2500, energySavings: 2500, improvement: 12.5,
  carbonReduction: 455, cost: 1500, billSavings: 150, payback: 10,
  valueStatus: 'illustrative', valueReason: 'Dummy UI preview only', baselineValue: 300000, valueRange: [3000, 6000],
  notes: ['Invented values for checking the interface only. No model or engine produced these figures.'],
};
export const previewOutputs: OutputSnapshot[] = [
  base,
  { ...base, id: 'ui-preview-2', upgrades: ['heat_pump'], afterScore: 68, afterClass: 'Good', afterElectricity: 10500, afterGas: 0, electricitySavings: -6500, gasSavings: 16000, energySavings: 9500, improvement: 47.5, carbonReduction: 2066, cost: 12500, billSavings: 400, payback: 31.25, valueRange: [6000, 12000] },
  { ...base, id: 'ui-preview-3', upgrades: ['loft_insulation', 'heat_pump', 'solar_panels'], afterScore: 82, afterClass: 'High', afterElectricity: 7000, afterGas: 0, electricitySavings: -3000, gasSavings: 16000, energySavings: 13000, improvement: 65, carbonReduction: 2524, cost: 20500, billSavings: 1050, payback: 19.5, valueRange: [9000, 15000] },
];
