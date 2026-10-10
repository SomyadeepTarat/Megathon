# Backend teammate handoff

## Canonical contracts

`backend/app/schemas/models.py` contains property, annual energy, benchmark, assessment, and scenario inputs. `backend/app/schemas/engines.py` contains feasibility, fuel state, simulation, energy impact, carbon, valuation, recommendation, optimization, and repository output models. OpenAPI `/openapi.json` is the frontend route contract.

All fields use the declared units. Missing consumption is null, not zero. Enum strings must not change without coordination. Engines return validated model objects, not free-form dictionaries. Models forbid unknown fields.

## P3: data

Implement `PropertyRepository` from `backend/app/services/contracts.py`: `list_properties()` and `load_property(id)` return `PropertyRecord` objects, with data provenance, annual energy coverage, and applicable benchmark. Unknown IDs raise KeyError. Replace `get_repository()` in `app/main.py` when integrating. Current JSON repository copies records to avoid shared mutation. Its three homes are explicitly synthetic handwritten fixtures, not a training dataset.

Annualization is still P3's work. Preserve missing months and provide method/quality. Observed annual values require full-year coverage. Benchmarks require documented methodology, source, type, and optional region matching. Do not adopt test fixture benchmarks as real references.

## P4: retrofit and carbon

Implement `RetrofitEngine` with `version`, `check_feasibility(ScenarioRequest)` and `simulate_retrofits(ScenarioRequest)`. Feasibility must cover exactly the requested measures, each with feasible/conditional/infeasible and reason. Packages with conditional or infeasible measures are blocked before simulation. No partial measure application is currently supported.

SimulationResult requires updated Property, purchased grid electricity/gas after the package, applied measures, nonnegative installation cost, methodology version, assumptions, and warnings. Supply the complete updated physical state. Preserve property identity, location, size, age, bedrooms, market index, current market-value baseline, and recorded EPC. A separate explicitly supported estimated-EPC contract can be designed later.

The orchestrator computes signed savings from returned fuel states. It checks applied measures and budgets and refuses inconsistent carbon outputs. It protects the baseline by passing independent deep copies to adapters. Package interactions and physical validity remain your engine's responsibility. No heating-demand model or retrofit constants are fabricated by P1.

Implement `CarbonEngine.calculate_carbon(EnergyImpact)`: return CarbonResult with both documented EmissionFactors, units kgCO2e/kWh, year, source and boundary. Missing factors return unavailable with reason. The orchestrator verifies signed per-fuel arithmetic; it does not verify the external source's correctness. Keep boundaries compatible between fuels.

Replace `get_retrofit_engine()` and `get_carbon_engine()` in `app/main.py` with real implementations. FastAPI dependency overrides are used only in tests. Recommendation/optimization models are defined but their routes are pending P4 integration; objective in ScenarioRequest does not optimize the submitted package.

## P5: valuation

Existing `backend/app/services/valuation_service.py` is preserved. `ExistingValuationAdapter` maps floor_area_m2 to floor_area and property_age_years to age, and passes bedrooms, market_index, region, property_type and recorded energy_rating. Categories must match the trained dataset; unknown categories return unavailable. Market index is optional for scoring but required if the valuation model uses it. We do not infer it.

The adapter calls the existing function with allow_illustrative=False. Missing models or unsupported evidence remain unavailable. Physical improvements alone do not establish a new EPC. P5's observed relationship is indicative, not causal. Valuation model/preprocessing versions should be added to the service response during later integration.

## P2: frontend

GET /properties -> GET /properties/{id} -> POST /assessments supports an edited property. Detail responses include dataset_kind/source; strip those repository-only fields when creating AssessmentRequest or ScenarioRequest. POST /scenarios/simulate accepts full snapshot, selected measures, optional budget and objective. Treat 409 and 503 as typed domain outcomes; display reasons rather than a generic network error. HTTP 200 partial means energy may exist while score/carbon/value is unavailable. Render status per module.

LLM/advisor and unified dashboard routes remain pending. Intent extraction must validate against ScenarioRequest. Numerical results must be recomputed before explanation.

## Error and status policy

- 422: invalid request schema.
- 404: unknown stored property.
- 409 rejected: infeasible, conditional, or over-budget selected package.
- 503 unavailable: engine not integrated or required fuel data missing.
- 200 partial: simulation completed but one or more estimates unavailable.
- 200 success: complete supported results.
- 500: unexpected engine failure or inconsistent engine output; no fabricated fallback estimates.

Scenario IDs are generated per request; numerical results are repeatable for identical inputs and engine versions. Persistence, model metadata, authentication and deployment are separate future work.
