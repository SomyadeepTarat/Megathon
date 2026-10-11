import type { Objective, OptimizationResult, PackageTradeoff, Recommendation, Retrofit } from './types.ts';

export interface PlannerDraft {
  snapshot: string; selected: Retrofit[]; budget: string; objective: Objective;
  recommendations: Recommendation[]; recommendationsChecked: boolean; recommendationNote: string; optimization: OptimizationResult | null;
}
export function emptyPlan(snapshot: string): PlannerDraft {
  return {snapshot, selected: [], budget: '', objective: 'energy_reduction', recommendations: [], recommendationsChecked: false, recommendationNote: '', optimization: null};
}
export function groupedPackages(options: PackageTradeoff[], objective: Objective) {
  const groups = new Map<string, {option: PackageTradeoff; objectives: Objective[]; chosen: boolean}>();
  for (const option of options) {
    const key = [...option.retrofits].sort().join('|');
    const group = groups.get(key);
    if (group) { group.objectives.push(option.objective); if (option.objective === objective) {group.chosen = true; group.option = option;} }
    else groups.set(key, {option, objectives: [option.objective], chosen: option.objective === objective});
  }
  return [...groups.values()].sort((a,b) => Number(b.chosen) - Number(a.chosen));
}
export function orderedRecommendations(rows: Recommendation[]) {
  return [...rows].sort((a,b) => Number(b.recommended) - Number(a.recommended) || (a.priority ?? Infinity) - (b.priority ?? Infinity));
}
export function uniqueText(rows: string[]) { return [...new Set(rows.map(row => row.trim()).filter(Boolean))]; }

export function baselineOnlyOptimization(result: {best_scenario: {applied_retrofits: Retrofit[]} | null; ranked_packages: unknown[]}) {
  return !!result.best_scenario && result.best_scenario.applied_retrofits.length === 0 && result.ranked_packages.length === 1;
}
