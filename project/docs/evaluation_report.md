# Current Person 5 fixes

The latest verified results are in [Person 5 verification](../evaluation/results/person5_fixes/README.md). All 100 full scores are now available; the baseline valuation API works for 97 properties and explicitly refuses three outside development bounds. Earlier audits below describe historical states, not current behavior.

# Evaluation report — Person 5

## Integrated-runtime audit

After the carbon/advisor contributions arrived, the [full pipeline audit](../evaluation/results/full_pipeline/README.md) exercised the actual ASGI routes, standalone carbon edge cases, snapshot regression and local Ollama. The full suite passed 110 tests and 17 subtests, but production scenarios remain HTTP 503 and the advisor/recommendation/valuation endpoints remain HTTP 404. All full scores remain unavailable, observed CSV ingestion is rejected, and no frontend is present. See that report for exact reproduced drawbacks and tasks for each team member; passing unit tests does not establish demo readiness.

## Latest supplied-dataset run

The newly supplied `data/` dataset has now been evaluated. See [the initial dataset report](../evaluation/results/initial_dataset/README.md) and its `initial_metrics.json` for authoritative results. It contains 100 synthetic property snapshots and 1,200 monthly readings, with no observed transactions. All calculable score components and annual fuel totals were recorded; full scores are unavailable without benchmarks. Ridge won the illustrative snapshot comparison; EPC worsened validation error. The combined suite passed 97 tests and 17 subtests. The earlier fixture results below remain a separate experiment.

## Status

The repository started with only the PRD. No observed joined sales/EPC data, scoring engine, retrofit engine or LLM responses were supplied. Valuation training and inference are implemented and exercised on an explicitly synthetic fixture. Overall predictive accuracy, retrofit quality and LLM challenge targets remain unverified.

Recorded results are in `ml/reports/valuation_metrics.json`, `held_out_predictions.csv` and `split_manifest.csv`. Use the JSON as the authoritative metrics after retraining. The fixture has 600 invented transactions and 300 fictional customer groups, with 330 fit rows, 90 selection rows, 90 calibration rows and 90 final test rows. Calibration uses 45 independent customer observations. IDs do not overlap splits.

Initial fixture training selected HistGradientBoosting using validation MAE. Final test MAE was £19,613, RMSE £24,456, R² 0.956; Ridge test MAE was £16,373 and median-baseline MAE £95,223. Nominal 90% value interval coverage was 94.44%, with mean width £88,421. These are software-fixture measurements, **not market performance**. Selection favored the nonlinear model; the final test favored Ridge. We do not switch models using the test results. Updated runs preserve their measured outputs in JSON.

## Automated verification

Tests cover customer/property separation and reproducibility, input validation, exclusion of price-derived predictors, calibration rank correction and insufficient samples, model persistence, synthetic default refusal, missing artifacts, out-of-support scenarios, unrelated feature changes, signed fuel savings, zero/missing energy, monotonicity adapters, and pending human review. Run `python -m pytest ml/tests evaluation/tests -q` for current results.

The evaluation harness checks recorded PRD nested energy outputs and score breakdowns. It checks arithmetic consistency and can use explicit supplied emissions factors; it does not establish that the factors or physical estimates are correct. Person 4 must supply sources and independently prepared energy reference estimates before any accuracy claim. Feasibility metrics require separately reviewed labels with references and distinguish eligible, rejected and conditional cases.

## Pending integration evaluations

- Person 1: pass all seven-component score outputs and ordered worse-to-better property states to `check_score` and `check_monotonicity`; verify the team's agreed rounding rule.
- Person 4: record insulation, glazing, thermostat, solar, heat pump, interactions, infeasible packages, zero and missing consumption. Include updated physical states and independent reference estimates. Never call agreement with the same simulator predictive validation.
- Person 2: record actual responses and structured-output numeric whitelists for the 25 questions in `evaluation/explanation_cases.json`. Human reviewers fill groundedness, factual accuracy, completeness, tool invocation, unavailable handling and `no_unsupported_claims`. Automated tokens cannot assess semantics. Targets stay pending until every response has a review.
- Person 3: provide audited observed transactions, timestamp-correct EPCs and market features, source/license information and stable grouping IDs.
- Person 5 with observed data: temporal evaluation, subgroup MAE/coverage, EPC matching and sensitivity review. Contrast coverage cannot be validated without defensible paired counterfactual/reference data.

No full-system pass, latency result, causal premium or LLM target attainment is claimed.
