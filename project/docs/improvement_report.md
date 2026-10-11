# Five-priority implementation and evaluation report

Scope: team 254's local synthetic hackathon prototype. The official brief permits synthetic property/sales data and documented rule/simulator labels. Results below distinguish synthetic model generalisation, documented-rule agreement, software checks and pending human review.

## Implemented requirements

1. **Complete illustrative value impact:** explicitly synthetic property/energy scenarios use before/after purchased-energy intensity from the actual fuel simulator, preserving recorded EPC. Missing critical/model-used fields, unknown categories, changed fixed characteristics, missing artifacts and observed inputs retain structured unavailable responses. Baseline current value is a supplied anchor, never a regression feature. Paired uncertainty is separately calibrated. See [methodology](synthetic_impact_methodology.md).
2. **Expanded held-out evaluation:** 1,800 synthetic price/scenario pairs with independent fit/selection/calibration/test groups; 24 additional held-out physical homes covering five types, three regions, four heating systems, existing installations/PV, unknown eligibility, interactions and three optimisation objectives. A separately coded closed-form oracle supplies explicit reference labels; it does not call the production engine to create expectations. Rule/simulator evaluators now require documented label methodology and identify agreement separately from independent observed validation.
3. **Recommendation tradeoffs:** best scenarios contain their objective/budget explanation and alternative carbon/energy/payback winners under the same feasibility/budget constraints. The comparison dashboard displays installation cost, signed energy/carbon outcomes, bill savings and payback. It explains financial exclusions and shows the simulation sequence without claiming it is an installation specification.
4. **Suitability and priority:** frontend preserves backend High/Medium/Low labels, suitability reasons and nullable priorities. Ranked cards appear in backend priority order; other options remain unranked and visibly marked. Synthetic evidence continues to be disclosed rather than promoted to observed confidence.
5. **Consistent submission:** current architecture diagram, synthetic label/features documentation, current metrics and held-out outputs, trusted locally trained model binaries, reproducible verification commands and checksum ZIP. Private SQLite data/secrets/dependencies/build output are excluded; models and ZIPs stay outside Git.

## Held-out numerical evidence

| Measure | Result | Interpretation |
|---|---|---|
| Selected synthetic impact model | Monotonic HistGradientBoosting | Selected on validation MAE, not test results |
| Synthetic price MAE / RMSE / R² | £23,642 / £32,866 / 0.992 | Fit to invented synthetic prices only |
| Ridge baseline test MAE | £67,422 | Same held-out synthetic price rows |
| Median baseline test MAE | £284,196 | Same held-out synthetic price rows |
| Nominal 90% price-band coverage | 90.8% | 360 untouched synthetic test properties |
| Synthetic paired uplift MAE | £5,655 | Against known invented paired labels |
| Nominal 90% paired uplift coverage / mean width | **86.4% / £23,975** | Shortfall disclosed; no real-world guarantee |
| Improving intensity gives nonnegative predicted change | 100% | Boosting monotonic constraint |
| Property-group overlap | None | Separate 720 fit / 360 selection / 360 calibration / 360 test |
| Feasible fuel/reference cases | 119 | From all 32 packages across 24 held-out homes |
| Per-fuel/carbon arithmetic MAE | Below 1e-7 | Agreement under shared assumptions, not measured savings accuracy |
| Feasibility decisions | 120 | Explicit feasible/conditional/infeasible reference labels |
| Recommendation ranking / optimiser matches | 72/72 each | Includes empty/unavailable cases; nonempty counts and baselines are reported in JSON |

Exact metrics, subgroup-independent split manifests and predictions: `ml/reports/synthetic_impact` and `evaluation/results/held_out_retrofits`. The supplied snapshot baseline remains separately trained/reported in `ml/reports/snapshot`; its price interval does not calibrate uplift.

## Verification and reproduced failures

The reproduction command writes `evaluation/results/current_pipeline/submission_verification.json`, per-command logs, JUnit results and runtime verification. It regenerates both shipped models, validates 100 supplied assessments, exercises 10 curated demo homes × three objectives × all 32 decisions, verifies missing-critical-field null responses, and runs Python/frontend/dependency/build checks. The current reproduction run passed all 11 commands with exit 0: **224 Python tests plus 34 subtests**, **13 frontend tests**, type checking, dependency checks, production build, reference evaluation and runtime verification.

During implementation, the first unconstrained impact model occasionally predicted a negative contrast for improved intensity; constraining the boosting energy feature corrected this. A legacy frontend fixture lacked the new suitability/ranking fields; its explicit conditional fixture contract was corrected. Tests initially read a previously persisted developer snapshot and counted 101 homes; test startup now uses an isolated temporary SQLite database instead of modifying/deleting developer data. The held-out generator initially reused a detached benchmark for other property types; it now declares that benchmark unavailable and evaluates the fuel/ranking contracts independently.

## Evidence limits and review status

The existing 25 recorded Ollama answers and Somyadeep review sheet predate this impact feature. They remain historical evidence with human labels pending; do not claim human factual-accuracy/groundedness targets have passed. Fresh desktop/mobile browser checks for these UI changes passed and are stored separately in `evaluation/results/current_pipeline/improvement_browser_verification.json`. Earlier browser/audit reports describe earlier code.

Current uplift interval coverage falls below its nominal target, its width can include zero, and some improved synthetic homes receive zero model contrast. Annual purchased-energy intensity is an imperfect valuation proxy. The reference oracle shares assumptions with production; no measured savings, observed-market accuracy or causal effect is established. Solar-related full after scores may still be unavailable without a supported renewable scoring category; fuel/carbon/value outputs remain separately available. These limits are shown/documented rather than hidden.

Future work: independent measured retrofit/observed-sale validation, richer energy/market features, better interval calibration using new calibration data, seasonal heat-pump/PV behaviour and optional customer memory. Human explanation review remains Somyadeep's task.
