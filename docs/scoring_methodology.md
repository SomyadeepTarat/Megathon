# Scoring methodology v1

Weights: EPC 0.25, purchased-energy intensity 0.20, insulation 0.15, heating 0.15, windows 0.10, renewable contribution 0.10, controls 0.05. Each subscore ranges from 0 to 100.

Mappings taken from the PRD's proposed team assumptions:

- EPC A/B/C/D/E/F/G: 100/85/70/55/40/20/0.
- Insulation poor/average/good: 20/60/100.
- Heating old gas/modern gas/direct electric/air-source heat pump/ground-source heat pump: 20/50/60/90/100.
- Glazing single/double/triple: 20/75/100.
- Renewable none/limited/substantial: 0/50/100.
- Controls none/basic/advanced: 0/50/100.

The heating mapping is a simplified team sustainability proxy, not a universal efficiency ranking. Renewable contribution is explicitly supplied; the backend does not infer it from a solar boolean. A documented physical mapping from generation to these categories is future energy-engine work.

Intensity = (annual grid imports + annual gas) / floor area, in kWh/m2/year. Relative intensity r = intensity / documented applicable benchmark. Consumption subscore = clip(100 - 50*(r - 0.5), 0, 100). Benchmark source and methodology are required. No invented default benchmark is provided. Benchmarks must match property type and region if region-specific.

Weighted contributions are computed without preliminary rounding. Final reporting uses nearest-integer half-up rounding; classification uses this reported integer. Categories: 80–100 highly efficient, 65–79 good, 50–64 moderate, 30–49 poor, 0–29 very poor. Poor-home flag is score < 50.

Missing required scoring data makes the full score unavailable; known components remain visible. Weights are never redistributed. Missing fuel differs from observed zero. Annualization is not implemented here: P3 must provide annual values, coverage, quality, and method. Observed annual fuel values require twelve months of coverage. Estimated values are explicitly warned about.

A retrofit must not overwrite the recorded EPC rating without a separately supported and labeled EPC estimation method. All numbers are calculated in Python; there is no LLM dependency.

Issue detection identifies above-benchmark intensity, poor insulation, old gas heating, single glazing, no renewables, and no smart controls. Severity is a team-defined explanatory ordering. Above-benchmark is a comparison, not a claim of a universal high-consumption threshold. Missing values do not generate condition-based accusations.
