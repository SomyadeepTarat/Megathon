# Active London demo verification

The active demo now serves the 1,900 fresh Greater London synthetic properties. The original 100 properties are excluded from deployment and remain diagnostic only. `scripts/prepare_london_demo.py` regenerates the supplied dataset and trains the baseline artifact using the supplied split manifest. No unsupported input columns, survey eligibility, tariffs or installation prices were inferred.

## What was checked

The complete submission reproduction command exits successfully: model generation/training, deterministic engine reference and held-out checks, API runtime tests, Python tests, dependency checks, frontend type checking, frontend tests, production build and submission packaging. See `../current_pipeline/submission_verification.json` for each command and exit code.

`workflow.json` records 12 non-preset scenario cases, 12 budget/objective combinations and five valuation/missing-input checks. The custom home uses 103.7 m², £482,750 current value, 2,731.9 kWh electricity, 11,747.2 kWh gas and documented synthetic physical assumptions. These inputs are temporary test fixtures, not source-data enrichment or observed measurements. Scenarios cover each upgrade, combined fabric/heating/control effects, infeasibility, contradictory flags and thermal totals, missing fuel/value, zero consumption, incomplete annual observations, negative budgets and out-of-support floor area. Missing critical valuation features return unavailable. Heat pumps preserve thermal demand and may increase electricity while reducing gas. Package effects are recalculated rather than summed.

Budgets £0, £1,733, £2,750 and £15,875 were tested against energy, carbon and payback objectives. Selected costs cannot exceed the budget. An unavailable recommendation on an unedited source home means eligibility or cost evidence is missing; it is not permission to invent that evidence. Supply explicitly labeled synthetic assumptions through Assessment for an illustrative full-package demo.

The live browser checks cover assessment, baseline valuation, planner blockers, portfolio search/pagination and advisor integration. An edited 103.7 m² home with explicitly synthetic £1,500 loft and £200 controls costs selected a £1,700 package under a £1,733 budget. The UI showed £33 remaining, approximately £298 annual bill savings, 786 kg CO2e annual carbon reduction and 5.7-year payback, versus the £200 controls-only alternative with approximately £104 savings and 1.9-year payback. Comparison recalculated a score of 38 to 45 and 4,313 kWh/year purchased-energy savings; the illustrative value-change range crossed zero. These are calculation results from explicit synthetic inputs, not measured outcomes. Property ranking remains separate from retrofit recommendation comparison. Property pickers search the larger cohort without rendering thousands of options. Table pages contain 50 homes.

The advisor receives engine outputs, not arbitrary model predictions from the language model. Baseline valuation questions are routed to baseline evidence, separately from retrofit uplift. Numeric sentences are rendered from backend-owned facts. Local Ollama question checks and the human review sheet are in `local_ollama/`; numeric checks do not certify all qualitative claims. Somyadeep still needs to review the recorded answers.

## Model results and practical limitations

The supplied frozen partitions contain 803 fit, 334 selection, 381 calibration and 382 test homes. Ridge was selected under the existing model-selection rule. Test MAE is approximately £210,234, RMSE £318,059 and R² 0.243. Nominal 90% price-proportional intervals achieved 89.5% marginal coverage, with average width approximately £701,118. These broad intervals limit individual valuation usefulness. The already-exposed holdout is reproduced, not a fresh independent evaluation. The larger dataset is geographically relevant; size alone does not establish observed-market accuracy.

All 1,900 homes have calculable baseline scores. Baseline valuation is illustrative for 1,896; four homes are outside floor-area development support. The dataset contains synthetic individual homes anchored to aggregate public references, not matched observed EPC/sale transactions. It does not establish a causal energy or retrofit premium. Retrofit-impact modeling remains separately disclosed synthetic modeling; these baseline labels were not repurposed to invent uplift labels.

Solar scenarios calculate purchased-grid savings and carbon where supported; projected score remains partial if no documented renewable-contribution mapping exists. Unknown suitability, costs and tariffs remain explicit. Human explanation-quality targets and real-world savings/valuation accuracy are not certified. These limits follow the Lloyds statement's missing-data and insufficient-value-impact requirements.

## Run and inspect

```sh
.venv/bin/python scripts/prepare_london_demo.py
.venv/bin/python scripts/reproduce_submission.py
LLM_PROVIDER=ollama LLM_MODEL=qwen3:4b .venv/bin/python -m evaluation.verify_london_workflow
GREENPRINT_PROPERTY_DATASET=london LLM_PROVIDER=ollama LLM_MODEL=qwen3:4b .venv/bin/python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8001
npm --prefix frontend run build
npm --prefix frontend start -- --port 3000
```

Review `workflow.json` to follow each input and expected outcome. Treat synthetic prices, costs and savings as illustrative demo evidence. Do not describe them as real sale prices or verified contractor savings.
