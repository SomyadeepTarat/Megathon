# Person 1 runtime integration

## Implemented

Runtime providers call P4RetrofitAdapter and P4CarbonAdapter instead of pending engines. The adapter invokes carbon_engine's actual feasibility and sequential simulation code. The P2 advisor router and partial-result adapter from latest main are preserved and connected to the same real providers.

Physical inputs are explicitly validated under property.physical_inputs: thermal_demand_kwh, heating_energy_kwh, boiler_efficiency, heating_efficiency, scop, solar generation, self-consumption, fraction, proposed heat-pump subtype and per-field provenance. Unknowns remain null. Raw P4 heating/solar fields are populated by the adapter. Solar self-consumption must have generation available and cannot exceed generation. Existing installed solar and heat pumps are explicit typed fields; CSV source flags are retained.

The adapter blocks known-incompatible heat pumps and smart controls and keeps unknown compatibility conditional before simulation. It uses the underlying engine for other eligibility rules. These integration guards do not change standalone P4 behavior; the P4 owner should also fix those checks in their own public functions.

P4 returns nested energy/emissions, which are converted into SimulationResult. Updated installed flags, heating subtype when supplied, double glazing, controls, and modeled thermal demand are returned. Loft installation alone does not establish whole-home insulation quality. Solar installation alone does not establish a scoring contribution category. Recorded EPC stays unchanged. Scenario valuation stays unavailable when no supported projected EPC exists; no uplift is guessed.

Costs are optional because P4 supplies no production cost catalogue. A request may supply retrofit_costs with amount_gbp, source and date per measure. Missing costs remain null. Budget-bearing requests cannot succeed without those costs. No payback/tariff values or package optimizer are fabricated.

## Routes

- POST /properties registers an edited or supplied snapshot for subsequent ID-based advisor requests. It is copied and stored in memory; restart discards edits. Source provenance must be supplied by callers; this is not persistent customer memory.
- POST /assessments/full exposes baseline score/components, annual energy, baseline emissions and baseline valuation status.
- POST /scenarios/simulate calls the real package simulation adapter; HTTP 200 can be partial when optional outputs are missing. 409 rejects conditional/infeasible or over-budget packages, 503 reports missing required data/factors/costs.
- POST /retrofits/recommend simulates and ranks individual positively feasible candidates. Conditional/unavailable options are shown separately. This is single-option screening, not a budget optimizer. Shortest payback remains unavailable.
- POST /properties/{id}/valuation/impact invokes the existing P5 service for baseline input; unsupported retrofit contrasts are unavailable. It never promises causal uplift. Requests use {} for the baseline.
- POST /advisor/chat supports registered property snapshots and explains verified partial energy/carbon while unavailable estimates stay explicit.
- GET /health reports connected providers and data requirements separately from process liveness. Artifact presence does not establish valuation support; the existing service checks provenance/evidence per request.

## Factors and provenance

Either provide emission_factors in AssessmentRequest/ScenarioRequest or set GREENPRINT_EMISSION_FACTORS_FILE to a versioned JSON file. Fields: fuel, kg_co2e_per_kwh, source, source_year, accounting_boundary, version. Electricity and gas must both be present. No production factor values are bundled; tests supply clearly labeled arithmetic fixtures only. The factor operator must choose compatible accounting boundaries and a reliable source. Physical-input provenance is preserved; unsourced values receive explicit warnings.

CSV ingestion now accepts declared synthetic/observed/estimated/imported property records and monthly readings. Energy quality follows the readings independently of property provenance. Complete-year totals are required; incomplete fuel stays null. The existing supplied CSV remains synthetic. The API does not transform it into observed evidence.

## Verification

Integration tests exercise actual mounted routes with the real contributed P4 engine and no dependency overrides. Explicit test-only inputs/factors establish signed heat-pump fuel savings, carbon arithmetic, updated state, baseline and partial results, advisor execution, missing data/factors, compatibility rejection, existing solar, solar-generation consistency, budget/cost behavior, recommendation and valuation endpoints, health readiness and unknown-property responses.

Default pytest includes carbon_engine/tests. These checks verify integration and arithmetic, not predictive accuracy. Existing standalone P4 test fixtures retain their original assumptions. Live Ollama behavior remains P2's opt-in provider check; default deterministic explanations stay functional.

## Remaining dependencies

P3: applicable documented benchmarks, heating subtype/renewable scoring data, physical measured/estimated inputs and production emissions factors. P4: official catalogue source evidence, costs, tariffs and budget package optimizer, plus standalone feasibility/solar fixes. P5: supported observed-data valuation artifacts and projected-EPC method if available. P2: frontend, provider configuration and optional live Ollama evaluation. No unsupported projected EPC is accepted as a trusted estimate.

Final local verification: 132 tests and 29 subtests passed on Python 3.14, with one upstream TestClient/httpx deprecation warning. Live HTTP checks are recorded in person1_http_check.json. New routes were exercised with actual configured providers; complete simulation tests use explicitly labeled test inputs/factors and no dependency overrides. Changes are local on feature/person1-runtime-integration and have not been pushed.
