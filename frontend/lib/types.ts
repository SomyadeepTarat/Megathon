export type Retrofit = 'loft_insulation' | 'heat_pump' | 'solar_panels' | 'double_glazing' | 'smart_thermostat';
export type Objective = 'carbon_reduction' | 'energy_reduction' | 'shortest_payback';
export interface PhysicalInputs {
  space_heating_demand_kwh?: number | null; hot_water_demand_kwh?: number | null; hot_water_cop?: number | null; proposed_solar_generation_kwh?: number | null; proposed_solar_self_consumed_kwh?: number | null; proposed_solar_self_consumption_fraction?: number | null; electric_resistance_efficiency?: number | null;
  thermal_demand_kwh?: number | null; heating_energy_kwh?: number | null; boiler_efficiency?: number | null; heating_efficiency?: number | null; scop?: number | null; solar_generation_kwh?: number | null; solar_self_consumed_kwh?: number | null; solar_self_consumption_fraction?: number | null; proposed_heat_pump_type?: 'air_source_heat_pump' | 'ground_source_heat_pump' | null; provenance: Record<string, string>;
}
export interface DocumentedFactor { fuel: 'electricity' | 'gas'; kg_co2e_per_kwh: number; source: string; source_year: number; accounting_boundary: string; version: string }
export interface Property {
  property_id: string; property_type: string; region: string; floor_area_m2: number;
  property_age_years: number | null; bedrooms: number | null; energy_rating: string | null;
  insulation: string | null; heating_system: string | null; glazing: string | null;
  renewable_contribution: string | null; smart_controls: string | null;
  roof_suitable_for_loft: boolean | null; roof_suitable_for_solar: boolean | null;
  heat_pump_compatible: boolean | null; controls_compatible: boolean | null;
  current_property_value_gbp: number | null; market_index: number | null;
  physical_inputs?: PhysicalInputs; solar_installed?: boolean | null; heat_pump_installed?: boolean | null; loft_insulation_installed?: boolean | null;
  provenance: Record<string, string>;
}
export interface AnnualEnergy {
  electricity_kwh: number | null; gas_kwh: number | null;
  quality: 'observed' | 'estimated' | 'synthetic' | 'missing'; method: string;
  electricity_months_covered: number; gas_months_covered: number; warnings: string[];
}
export interface Benchmark { property_type: string; intensity_kwh_m2_year: number; source: string; methodology: string; region?: string | null }
export interface AssessmentRequest { retrofit_costs?: Partial<Record<Retrofit, { amount_gbp: number; source: string; date: string }>>; electricity_tariff_gbp_per_kwh?: number | null; gas_tariff_gbp_per_kwh?: number | null; property: Property; annual_energy: AnnualEnergy; benchmark: Benchmark | null; emission_factors?: { electricity: DocumentedFactor; gas: DocumentedFactor } | null }
export interface PropertyRecord extends AssessmentRequest { dataset_kind: 'synthetic' | 'observed' | 'estimated' | 'imported'; dataset_source: string }
export interface PropertySummary { property_id: string; property_type: string; region: string; dataset_kind: 'synthetic' | 'observed' | 'estimated' | 'imported'; dataset_source: string }
export interface Component { name: string; subscore: number | null; weight: number; contribution: number | null; evidence: Record<string, string | number | null> }
export interface Assessment {
  property_id: string; score: { status: string; score: number | null; classification: string | null; components: Component[]; missing_fields: string[]; methodology_version: string };
  baseline_carbon?: { status: string; total_kg_co2e: number | null; reason?: string | null };
  poor_home: boolean | null; intensity_kwh_m2_year: number | null;
  issues: { code: string; severity: string; message: string; evidence: Record<string, unknown> }[]; warnings: string[];
}
export interface EnergyImpact {
  baseline: { electricity_kwh: number; gas_kwh: number }; after: { electricity_kwh: number; gas_kwh: number };
  electricity_savings_kwh: number; gas_savings_kwh: number; net_savings_kwh: number; improvement_percentage: number | null;
}
export interface Scenario {
  property_id: string; scenario_id: string; status: 'success' | 'partial' | 'rejected' | 'unavailable'; reason: string | null;
  baseline_assessment: Assessment; after_assessment: Assessment | null; updated_property: Property | null;
  feasibility: { status: string; items: { retrofit: Retrofit; status: string; reason: string }[]; reason: string | null };
  energy: EnergyImpact | null;
  carbon: { status: string; reduction_kg_co2e: number | null; reason: string | null; factors: { source: string; source_year: number; accounting_boundary: string }[] };
  valuation: { status: string; reason: string | null; baseline_value_gbp: number | null; after_value_gbp: number | null; value_change_gbp: number | null; value_change_range_gbp: [number, number] | null; warnings: string[] };
  optimization_context?: OptimizationContext | null;
  installation_cost_gbp: number | null; applied_retrofits: Retrofit[]; assumptions: string[]; warnings: string[];
  annual_bill_savings_gbp?: number | null; simple_payback_years?: number | null;
}
export interface Recommendation { retrofit: Retrofit; feasibility: { status: string; reason: string }; suitability?: 'High' | 'Medium' | 'Low'; suitability_reason?: string; recommended: boolean; priority: number | null; annual_bill_savings_gbp?: number | null; simple_payback_years?: number | null; estimated_cost_gbp: number | null; energy: EnergyImpact | null; carbon: Scenario['carbon'] | null; reason: string; assumptions: string[] }
export interface AdvisorResult { clarification_kind?: 'package' | 'budget' | null; status: string; explanation: string; mode: string; fallback_reason: string | null; tool_calls: string[]; result: Record<string, unknown> | null; intent: { intent: string; retrofits: Retrofit[]; budget_gbp: number | null; objective: Objective } }
export interface PortfolioRow { property_id: string; property_type: string; region: string; score: number | null; intensity: number | null; improvement: number | null; carbon: number | null; classification: string | null; error?: string; dataset_kind: string }

export interface RecommendationResponse { property_id: string; scenario_id: string | null; revision: number | null; objective: Objective; installation_order: Retrofit[]; status: string; recommendations: { retrofit: Retrofit; feasibility: { status: string; reason: string }; scenario: Scenario; suitability: 'High' | 'Medium' | 'Low'; suitability_reason: string; ranking_reason?: string | null; priority: number | null; estimated_cost_gbp: number | null }[]; other_options: RecommendationResponse['recommendations']; methodology: string; warnings: string[] }

export interface BaselineValuation { property_id: string; status: 'unavailable' | 'illustrative' | 'indicative'; reason: string | null; value_gbp: number | null; range_gbp: [number, number] | null; confidence_level: number | null; target_kind: 'sales' | 'snapshot' | null; method: string | null; warnings: string[] }

export interface OptimizationResult { status: string; reason: string | null; best_scenario: Scenario | null; ranked_packages: unknown[]; package_decisions: unknown[]; objective: Objective; methodology: string }

export interface PackageTradeoff { objective: Objective; retrofits: Retrofit[]; installation_cost_gbp: number; carbon_reduction_kg_co2e: number | null; net_energy_savings_kwh: number; annual_bill_savings_gbp: number | null; simple_payback_years: number | null }
export interface OptimizationContext { objective: Objective; budget_gbp: number; explanation: string; alternatives: PackageTradeoff[]; installation_order: Retrofit[] }
