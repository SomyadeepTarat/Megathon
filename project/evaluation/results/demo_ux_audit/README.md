# Integrated demo and PDF compliance audit — 11 October 2026

Scope: current merged implementation. All eight proposed application fixes were approved and implemented. Backend runs on 8001 with curated synthetic demo records, local qwen3:4b, and isolated SQLite `/private/tmp/kew-demo-audit-fixed.db`. Frontend production server runs on 3000. Supplied 100-property CSV separately exercised by runtime harness.

## Verification
- Production build passed.
- Python: 271 tests + 34 subtests passed; frontend: 26 tests passed.
- Live browser: intro skip, property selection/assessment, budget optimization, detailed package comparison, return-to-planner, property ranking/search/poor-home filter, portfolio loading/sorting, saved recommendation display, and advisor streaming/answer.
- 100 CSV homes: all scores and baseline carbon available; 97 illustrative baseline valuations, three unavailable outside floor-area support.
- Frontend HTTP routes/proxy passed; saved recommendations POST/GET matched through frontend proxy.
- Serialized synthetic ML artifact reproduced all 360 held-out price and uplift predictions; source-data provenance hash matches.
- Eight local advisor cases: six grounded LLM responses, one generation-validation fallback, one deterministic infeasible response. No unsupported numeric tokens detected. Human review remains incomplete; this is not a semantic accuracy certification.
- Browser console inspection returned no warnings/errors during the reviewed flow.
- CSV export clicked, but browser automation did not receive a download event. File-delivery verification remains incomplete; no proven export defect.

## PDF edge cases
- Missing gas: unavailable, null simulation, HTTP 503.
- Infeasible heat pump: rejected, null simulation, HTTP 409.
- Heat pump: electricity savings -3896.50 kWh/year; gas savings +12600.62; signs preserved.
- Interacting loft/controls: combined gas savings 2279.01, not independent savings sum.
- Missing baseline value: partial success with useful energy estimates and unavailable valuation.
- Observed readings with six months coverage: explicit HTTP 422 validation; not silently annualised.
- Zero baseline: percentage reduction null; no divide-by-zero.
- Zero budget: no-upgrade package.
- Missing installation costs: upgrades unavailable, not free; no-upgrade package remains eligible.
- Missing request emissions factors: documented bundled factors used.
- FIXED: contradictory 100000 kWh space-heating demand is explicitly unavailable (503), with null energy/value impact. Live frontend-proxy regression verified.
- FIXED: gas boiler plus heat_pump_installed=true is explicitly unavailable (503), with conflicting-field reason. Direct valuation-impact bypass also blocked and tested.

## Approved fixes implemented
1. P0: physical/installed-state consistency checks before relevant calculations, explicit conflicting-fields reason and unavailable affected estimates. Retain unaffected scoring/outputs; support explicit hybrid systems only if modeled/documented. Add regression tests for contradictory demand/components, heating flags, and relevant solar/glazing/control conflicts.
2. P1: retain planner budget/objective/package/results on Edit my package within the same property snapshot; invalidate on changed inputs.
3. P1: group identical optimizer packages into one card with winning-objective badges; place current-priority winner first; keep genuine alternatives and compare actions.
4. P1: render eligible recommendations separately from conditional/rejected/over-budget other options. Preserve backend recommendation priority and display installation sequence. Property ranks remain exclusively in /ranking.
5. P2: deduplicate assumptions/reasons, collapse long methodology, consistent rounded precision and complete units. Preserve full sources/limitations.
6. P2: distinguish Portfolio inventory and improvement ranking using a shared workspace/tabs; retain friend's property-ranking feature and keep it independent from retrofit cards.
7. P2: mobile budget/priority fields stack at narrow widths (current priority text truncates); improve small badges and table scroll affordances, keep current theme.
8. P2: clarify baseline versus proposed scenario in advisor summary and answers; retain current stateless conversation scope.

## Scientific/compliance limits
Synthetic data is permitted by the official brief. Rule/reference agreement does not prove measured savings or market valuation accuracy. Uplift nominal 90% band has 86.4% stored held-out synthetic coverage. Generator-informed baseline MAE £1531 versus model £5655 (prior read-only comparison); include in future evaluation. Conflicting evidence and prioritized UI presentation are fixed. Official human explanation targets remain unevaluated; complete scientific validation is not claimed.

Screenshots: advisor-desktop.png, planner-full.png, planner-mobile.png, mobile-controls.png. Detailed live contradictory-input responses: edge_cases.json.

## Verification after fixes
- Production build and full Python/frontend suites pass. Twelve analytical reference cases pass with zero per-fuel MAE under shared assumptions.
- Live browser verified assessment (baseline score 32), ordered recommendations, two distinct optimizer cards, selected priority first, package comparison, and Edit my package retaining £5000 and selections. Alternative comparison reruns optimization and displays the smart-thermostat package (£200; 4.2-year payback).
- Mobile viewport 390×844: document width 390; budget/priority controls 310px wide at 14px font. No horizontal page overflow.
- Property workspace tabs preserve separate property ranking. Poor-home filter returns three homes, with signed per-fuel savings. Portfolio assesses ten demo homes.
- Advisor streamed a natural-language baseline explanation; answer labelled Recorded baseline home while summary clearly labels proposed scenario and baseline score separately. Browser console warning/error list empty.
- Live runtime harness, recommendation storage through proxy, and eight local advisor checks pass; no unsupported numeric tokens detected. One generation-validation fallback remains supported behavior.
- CSV download event remains unobservable in this in-app browser after the object-URL lifecycle fix; file delivery is not certified.
- New evidence: fixed_edge_cases.json, after-planner-desktop.png, after-planner-mobile.png. Earlier screenshots and edge_cases.json describe the pre-fix audit.
