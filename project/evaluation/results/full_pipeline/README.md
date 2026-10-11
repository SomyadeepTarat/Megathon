# Full pipeline audit — 10 October 2026

## Outcome

The checked-out modules pass their existing tests, but the integrated application cannot complete the PRD demo flow. An API health response is not evidence that retrofit, advisor, valuation or frontend integration is ready. Test adapters are distinct from production dependencies.

Fetched origin and confirmed the checkout matches `origin/main`, revision `856cecd`. The runtime API was exercised in-process through the real ASGI app, without dependency overrides. Requests and responses, including status codes and latency, are saved in `api_audit.json`. No remote deployment or browser session was tested. Dataset regression and quality checks were rerun separately in `../initial_dataset/`.

## Live Ollama results

All **25 prepared questions** were run through the advisor service with installed `qwen3:4b` using the existing provider options. **Zero responses used grounded_llm mode**: all 25 used deterministic behavior. Nine produced baseline explanations, five reported unavailable scenario dependencies and eleven requested clarification. The 32 provider calls (including three adversarial intent probes) failed JSON parsing with `JSONDecodeError`. No models were downloaded.

Total elapsed time across the 25 questions was 366.15 seconds (mean 14.65 seconds, slowest 29.65 seconds); direct offline-parsed scenario questions stopped immediately at the unavailable dependency. Numeric-token checks found no unsupported numbers in the final outputs, but zero cases have independent human review, so groundedness/accuracy targets remain unverified. Raw responses, selected intents, tool attempts, fallbacks and per-question latency are recorded in `ollama_responses.json`; provider failures and metrics are in `ollama_metrics.json`.

These live service tests used an explicitly evaluation-only adapter that formats actual baseline assessment results. They do not imply the absent `/advisor/chat` route works. No retrofit numerical outputs were substituted when engines were missing. A separate `ollama_transport_probe.json` compares default thinking with disabled thinking to identify the JSON transport failure; that diagnostic configuration is not installed into production.

The transport probe confirmed the default response had empty `message.content`, `done_reason="length"`, 512 generated tokens and 2,200 thinking characters. Setting `think=false` returned a valid heat-pump-only intent (correctly excluding negated solar) in 1.03 seconds. A no-thinking explanation took 2.21 seconds but echoed the input instead of returning `fact_ids`, so it would still fail the service's validation. Disabling thinking solves this token-exhaustion failure but does not by itself establish a working explanation provider; enforce task-specific output schemas and rerun live tests.

## Verified runtime results

| Step | Actual result |
|---|---|
| Health and property list | HTTP 200; 100 synthetic properties |
| All property assessments | HTTP 200; 100/100 full scores unavailable |
| Edited/observed-quality input schema probe | HTTP 200 with partial components; numbers were a synthetic test probe, not genuine household data |
| Heat-pump scenario | HTTP 503: P4 engine not integrated |
| Retrofit recommendations | HTTP 404: route absent |
| Advisor chat | HTTP 404: router not mounted |
| Valuation endpoint | HTTP 404: route absent |
| Portfolio rank | HTTP 404: route absent (secondary feature) |
| Frontend | `frontend/` absent from tracked checkout |
| Observed CSV ingestion | Rejected: `This dataset adapter requires declared synthetic properties` |

The combined test command explicitly includes `carbon_engine/tests`, which the current default `pytest.ini` excludes. Final run: **110 tests and 17 subtests passed**, with two dependency warnings. The P5 arithmetic verifier was corrected to match P1's HALF_UP rounding and a regression test added. See `../full_pipeline_tests.xml`.

## Exact drawbacks and responsible owners

### Person 1 — runtime integration (demo blocker)

`backend/app/main.py` still returns `PendingRetrofitEngine` and `PendingCarbonEngine`; add real adapters after aligning P4's contracts. Mount the advisor router and initialize its service. Add recommendation and valuation routes, and expose actual dependency readiness rather than just process liveness. Portfolio can wait until the main flow works.

P4's standalone outputs use `status="available"` and nested energy/emissions, whereas P1 expects `SimulationResult` with updated property, after fuel state, cost and applied measures. P2's advisor expects `status="success"`, flattened energy metrics and `all_feasible`; P1's complete results can be `partial`. Explicitly translate these shapes. Allow the advisor to explain verified energy/carbon even when valuation is unavailable; do not suppress all useful evidence because one optional estimate is missing.

The strict API schema cannot accept P4's thermal demand, heating load, boiler efficiency, SCOP or solar-generation inputs. Add an explicit validated physical-input contract shared by P3/P4, preserving per-field provenance and unknowns. Preserve installed-solar state as a typed field instead of burying it as a string in provenance.

The orchestrator currently protects EPC from change, while P5's valuation uses EPC as its only energy-efficiency feature. Establish a separate supported projected-EPC input if an estimator exists; otherwise retain recorded EPC and mark scenario value impact unavailable. Do not introduce guessed EPC uplifts to force the demo to display a number.

### Person 2 — frontend and advisor (demo blocker)

No frontend exists in this checkout; provide the promised selection, input, assessment and scenario screens or explicitly agree that the initial demo uses API docs. The advisor module is implemented but disconnected. Coordinate the async engine adapters with P1, provide Ollama environment settings, and confirm fallback behavior in the actual UI.

The live test uses the existing installed `qwen3:4b` through the unchanged provider. It selects fact IDs rather than writing original prose. This prevents invented explanation numbers but produces raw evidence text/JSON, with limited conversational usefulness. Improve backend fact rendering into concise human-readable explanations while keeping numerical values server-owned.

The provider caps generation at 512 tokens, doesn't explicitly control thinking, and defaults to 20-second per-call timeout. Thinking models can spend the budget before emitting JSON; verify transport results before selecting demo settings. Ollama documents the `think` parameter at [its official API guidance](https://ollama.com/blog/thinking). Negation validation currently checks that requested upgrade words occur, not that they are positively requested; add tests and conservative guards for negation/comparisons instead of relying only on the prompt.

### Person 3 — usable real-input data (demo blocker)

All supplied homes and readings are synthetic. Add a documented property-type intensity benchmark table, heat-pump subtype and renewable contribution data: these currently prevent 100 full scores, with 4 unknown heat-pump subtypes and 9 unknown solar categories. Keep unsupported fields unknown rather than inventing values.

Agree with P1 on observed/estimated/imported provenance, support actual readings in the CSV loader, and accept real inputs through the same normalized contract used by the advisor. An arbitrary edited `/assessments` request cannot currently become a stored property for ID-based chat. Maintain complete-year coverage per fuel and retain nulls for missing energy.

Provide timestamped sale/EPC data, source/license metadata and market features for P5. Current CSV prices are invented baseline estimates, not sale targets. Supply physical heating/solar inputs with documented assumptions or measured evidence for P4. Fix the generator CLI paths: scripts reside in `Data/scripts/`, but expect CSVs beside themselves instead of in `Data/csv/`.

### Person 4 — retrofit correctness and completion (demo blocker)

The contributed code is a standalone carbon/single-option screening engine, not the complete PRD retrofit package service. It lacks installation costs, budget-constrained subset optimization, payback/tariffs, a P1-compatible interface and updated physical-property output. Test-only emission factors exist; official versioned production factors are absent. The supplied dataset lacks thermal demand/SCOP/efficiency, so even standalone heat-pump simulation returns unavailable.

Four additional defects were reproduced in `carbon_diagnostics.json` using labelled synthetic inputs/factors:

1. `heat_pump_compatible=False` still reports heat pump feasible and simulates it.
2. `controls_compatible=False` still reports smart thermostat feasible and simulates it. Unknown compatibility also needs a conditional result.
3. Supplying generation 10 kWh and self-consumption 1,000 kWh reduces grid imports by 1,000 kWh. Cross-check self-consumption against available generation as well as demand.
4. Existing solar in P00003 is recorded only in backend provenance; the engine fails to detect it and permits another installation. Fix the shared mapping/installed flag with P1/P3.

The engine can also calculate a conditional package and label its numerical output available; keep feasibility separately visible and never present this as confirmed installation eligibility. Demand/fuel arithmetic uses documented simplifying assumptions, not independently validated measured retrofit outcomes. Catalogue percentage ranges currently lack linked, dated source evidence.

### Person 5 — valuation/evaluation (your scope)

The synthetic snapshot experiment still selects Ridge: test MAE £43,912, RMSE £51,490, R² 0.835, MAPE 17.99%. Its 90% nominal bands cover all 20 test values but average £323,336 wide, so they are too broad to imply a precise valuation. EPC worsens selection MAE (£65,019 vs £63,110 without EPC); do not claim an EPC premium.

The saved production fixture model was trained on fictional regions and refuses real-world uplift by design. The separate snapshot artifact deliberately is not production-compatible. Complete observed-data preparation, baseline valuation inference and integration, chronological testing, grouped development validation and subgroup analysis. Keep uplift unavailable when evidence is insufficient; a baseline-value endpoint does not require a causal retrofit premium.

Human groundedness/factual-accuracy review is pending. No live model or simulator accuracy target is certified merely from numeric-token checks or passing unit tests. Add integration tests against real mounted routes; current tests deliberately verify pending-engine failures and therefore stay green while the demo is incomplete. Include P4 tests in default pytest/CI. P5's rounding verifier discrepancy and relative-path handling were fixed during this audit.

## Minimum smooth-demo sequence

1. P1/P2/P4 connect real adapters and routes; agree on one request/result contract and show partial estimates correctly.
2. P3/P4 supply one complete, documented input record and required benchmarks, eligibility, physical inputs and emission factors. If the record is synthetic, label the demo synthetic. If genuine customer readings are available, distinguish those observations from estimated physical parameters.
3. P4 demonstrate a valid feasible package, signed per-fuel savings and returned updated property; add budget costs/optimization before promising a budget demo.
4. P2 connect the screen or use API docs, warm the chosen Ollama model, then test explanation and what-if through the mounted endpoint.
5. P5 keep unsupported value uplift unavailable, publish baseline/model metrics with provenance, and rerun one-command API + numerical + live-advisor audit.

A real-input demo can work with valuation explicitly unavailable. It cannot currently run the promised package/scenario/advisor sequence from this checkout without these integration fixes.

## Reproduce

```sh
.venv/bin/python -m pytest backend/tests ml/tests evaluation/tests carbon_engine/tests -q --junitxml=evaluation/results/full_pipeline_tests.xml
.venv/bin/python -m evaluation.evaluate_initial_dataset --data Data
.venv/bin/python -m evaluation.audit_full_pipeline --ollama --model qwen3:4b --timeout 20
```

The live audit's advisor shape adapter is evaluation-only and calls real baseline assessment logic; missing scenario/optimizer engines remain unavailable. It does not mount a production route or replace missing engines with numerical mocks. Carbon adversarial diagnostics use explicit test-only factors and are not official carbon estimates. `ollama_responses.json` records actual outputs; independent human review remains required.
