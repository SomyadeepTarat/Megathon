# Current pipeline verification — 11 October 2026

The implemented local prototype passes its automated checks and production HTTP smoke checks. This is **not** certification of observed-market valuation, real-world retrofit accuracy, browser usability, or the PRD's human explanation-quality targets. The supplied dataset is synthetic and those evidence gaps remain explicit.

## Verified requirements

| PRD requirement | Result and evidence |
|---|---|
| Local Next.js/FastAPI application | Production build, typecheck and all five application routes pass; local backend proxy passes. |
| Validated inputs and explicit missing data | Missing-critical valuation fields return `unavailable` with null values/range. Complete monthly coverage required; unknowns differ from zero. |
| Deterministic seven-component Green Home Score | All 100 supplied homes have complete scores. Required weights, component evidence, rounding and poor-home threshold are covered by tests. Synthetic benchmarks are labelled. |
| Five feasible retrofits and sequential energy changes | Confirmed eligibility required; hot water/appliances retained; heat-pump electricity increases stay signed; solar reduces imports. Existing solar and chained physical state have regression tests. |
| Sourced carbon factors | Corrected 2026 DESNZ extraction bundled with source row IDs, units, boundaries, workbook hash and licence. 100 baseline carbon calculations available. |
| Bills and payback | Documented costs and explicit tariffs required; missing inputs and nonpositive savings return reasons. |
| Exhaustive budget optimization | Ten curated homes × three objectives × 32 package decisions; accepted packages stay within £15,000 and confirmed feasibility. Seven homes permit shortest-payback estimates; three correctly return unavailable. |
| Portfolio potential | Complete confirmed-feasible packages, not one individually best measure. All ten curated demo potentials are calculable; unknown eligibility in ordinary data stays null. |
| Valuation baseline, model comparison and evaluation | Both training paths run. Snapshot Ridge beats HistGradientBoosting and is selected; grouped splits, independent calibration, metrics and support guards are tested. |
| Conservative value-impact fallback | Synthetic uplift disabled in production; insufficient information and unsupported updated EPC return unavailable. No invented premium. |
| Grounded advisor and fresh what-if calculations | Mounted production adapter and actual optimizer used. Explicit heat-pump, solar and combined package requests invoke feasibility then simulation. Deterministic fallback remains available. |
| Persistence and curated demo | SQLite round-trip preserves properties, physical inputs, nulls, cost sources and tariffs. Ten labelled synthetic variants prepared without modifying original CSVs. |

## Final executed checks

- `python -m pytest -q`: **210 passed, 34 subtests passed**, exit 0. Two nonblocking dependency/environment warnings: Starlette/httpx deprecation and loky physical-core detection.
- `python -m pip check`: no broken requirements, exit 0.
- `python -m compileall -q backend/app carbon_engine ml evaluation scripts Data/scripts`: exit 0.
- Frontend `npm run typecheck`, `npm test`, `npm run build`: exit 0; **12 frontend tests passed**.
- `npm ci`: successful; dependency audit reported zero vulnerabilities at installation time.
- Both data CLIs regenerate the enriched CSVs byte-for-byte from another working directory, covered by a regression test.
- Snapshot training, synthetic sales fixture generation/training and illustrative inference demo: exit 0.
- `evaluation.evaluate_initial_dataset`: exit 0; 100 homes, 1,200 readings, complete scores, exact fuel regeneration.
- `evaluation.verify_runtime --frontend-url http://127.0.0.1:3000`: exit 0; current production routes and frontend proxy checked.
- `evaluation.audit_full_pipeline --ollama --model qwen3:4b --timeout 20`: exit 0; **25 recorded responses**, 13 grounded-LLM responses and 12 deterministic conditional/clarification responses. Numeric whitelist audit found **0 unsupported numeric claims**. Human review count is zero; semantic quality targets remain unverified.
- No unmerged Git entries or whitespace errors. Existing merge work was preserved; changes were not committed or pushed.

Machine-readable evidence: [runtime verification](runtime_verification.json), [API audit](api_audit.json), [Ollama metrics](ollama_metrics.json), [actual responses awaiting review](ollama_responses.json), [dataset/model evaluation](../current_dataset/initial_metrics.json).

## Failures and exact fixes

| Discovered failure/deviation | Fix |
|---|---|
| Frontend fixed sample bill savings, payback, uplift and budget package appeared when calculations were unavailable | Removed the preview module and screen fallbacks; display actual results and null/reasons. |
| Planner and advisor budget flow did not use the contributed optimizer | Connected `/retrofits/optimize`; expose the actual best scenario and all package decisions; preserve edits, costs and tariffs in advisor registration. |
| Baseline carbon was not shown in the assessment | Connect frontend assessment to `/assessments/full` and display server-owned carbon. |
| No default documented fuel factors | Extract verified rows from corrected DESNZ workbook; CSV loader, provenance and explicit disable/configuration behavior. |
| Edited properties were lost on restart | Add validated SQLite snapshot persistence with atomic replacement and locking. |
| Portfolio UI attempted its own improvement calculation/incomplete ranking | Add typed server route that simulates the complete feasible package; frontend reads its results. |
| Existing solar distorted heating simulations; missing heat-pump COP caused a crash; chained scenarios reused stale component state | Reconstruct electricity demand from imports plus known self-consumption, retain bounded PV contribution with timing warning, derive conversion only from positive known demand/fuel, and propagate after-scenario physical inputs. |
| Basic programmable controls incorrectly blocked advanced smart controls | Distinguish basic and advanced controls; smart thermostat scenario applies the documented advanced category. |
| Data CLIs had wrong working-directory paths and discarded enriched fields | Resolve defaults against script location, preserve validated property enrichment and regenerate all 13 monthly columns. |
| Audit failed on newer FastAPI internal router objects and used an obsolete evaluation-only advisor | Read routes from OpenAPI; use mounted production advisor/adapters and separate current report directory. |
| Ollama clarified ordinary explanation questions and could explain baseline instead of a requested optimization | Add conservative explicit explanation/budget/combination grammar, clarify prompt examples, and reject baseline explanation for unresolved package optimization. Regression tests added. |
| Illustrative inference demo omitted a newly required critical baseline value | Supply an explicitly synthetic declared value, excluded from model features and not derived from the sale target. |
| Missing local frontend dependencies prevented typecheck/build | Install locked dependencies; build and tests now pass. |
| Sandbox blocked local network/server binding | Run authorized localhost verification with escalation; this was an environment restriction, not an application defect. |

## Remaining limitations and owners

1. **Person 3:** provide observed property/energy records, audited benchmark applicability and a leakage-safe EPC/transaction join. Current data has only 100 synthetic homes, below the PRD's preferred larger dataset. Curated eligibility/cost/tariff assumptions are examples, not surveys or quotes.
2. **Person 4:** independently validate retrofit reduction assumptions and proposed-system performance; provide supported estimators for whole-home insulation category, renewable contribution and projected EPC. Fuel/carbon changes work, but solar can leave the after-scenario full score unavailable; loft installation alone does not justify rewriting the whole-home insulation category. Annual fixed solar self-consumption is bounded but does not model hourly timing or seasonal COP.
3. **Person 5:** retrain and externally validate on observed sales when available. Snapshot MAE is £47,391, RMSE £55,334, R² 0.809 on only 20 synthetic held-out homes; interval coverage 20/20 with mean width £301,820 is too broad to establish useful market accuracy. Real uplift remains unavailable; calibrated marginal value intervals do not validate counterfactual uplift coverage or causality.
4. **Person 2:** review all 25 responses independently for groundedness, factual accuracy, completeness and tool selection. Zero unsupported numeric tokens does not establish ≥90% semantic quality. Hypothetical missing-data questions and package requests without a budget can require clarification. The LLM selects supplied facts; it does not freely compose numerical claims.
5. **Persons 1 and 2:** manually verify desktop/mobile browser interactions and accessibility. In-app browser attachment timed out and native computer-use permission was absent, so browser clicking/rendering was not verified. Production page delivery, proxy, typecheck, build and API contracts did pass. User cost sources/tariffs are persisted but their external authenticity is not verified.

Carbon estimates use 2026 operational factors with 2025 synthetic readings as documented scenario assumptions; they exclude lifecycle retrofit, upstream and grid distribution emissions. Optional long-term advisor memory and production deployment/security are outside this local hackathon verification.

For reproduction and demo startup, follow [the current README](../../../README.md). Suggested smooth demo: `DEMO-P00001`, £15,000 carbon objective; demonstrate both supported calculations and honest unavailable value impact.
