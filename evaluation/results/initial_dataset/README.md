# Initial dataset evaluation — 10 October 2026

Evaluated the supplied `data/csv/properties.csv` and `energy_usage.csv` without altering them. All records are synthetic. This run is an implementation/integration experiment, not observed-market validation.

## Results

- 100 properties, 1,200 readings, 12 months per property, unique IDs/keys, no missing cells, valid parent links, nonnegative fuel values.
- Regenerated both fuels through P3's generator with maximum difference **0 kWh**; its controlled physical consistency assertions passed. This is self-agreement, not independent predictive accuracy.
- Annual median electricity: **2,322.04 kWh**; annual median gas among gas-heated homes: **9,076.71 kWh**.
- Full Green Home Score: **0 available / 100 unavailable**, because all properties lack a documented consumption-intensity benchmark. Four heat pumps also lack their source subtype; nine solar-equipped properties lack a contribution category. No defaults were invented.
- EPC, insulation, windows and smart-management components are available for all 100 properties. Heating is available for 96; renewable components for 91; consumption scoring for zero. `property_scores.csv` contains every calculable subscore and contribution; `assessments.json` retains reasons and warnings. Available contributions were not renormalized into a substitute full score.
- Combined existing test suite: **97 tests passed, 17 subtests passed**, with two dependency warnings. See `../initial_tests.xml`.

## Illustrative value-regression experiment

The target is `current_value_estimate_gbp`, kept explicitly as a synthetic snapshot estimate. It was not relabelled as a transaction price. Inputs are area, bedrooms, age, region, type and EPC. No sale date or market index was invented. IDs, provenance, target value and generator seed are excluded from predictors.

The dataset has 100 unique customer groups. A fixed 40/20/20/20 fit/selection/calibration/test allocation leaves 20 independent calibration groups for this small-sample experiment. This is explicitly different from the observed-sales pipeline's split. There is no group overlap. Selection chose Ridge before inspecting the test.

| Predictor | Test MAE GBP | Test RMSE GBP | Test R² | Test MAPE |
|---|---:|---:|---:|---:|
| Ridge (selected) | 43,912 | 51,490 | 0.835 | 17.99% |
| Histogram gradient boosting | 72,830 | 90,621 | 0.488 | 29.20% |
| Training median | 102,800 | 130,302 | -0.059 | 39.72% |

The 90% nominal residual-calibrated interval covered 20/20 test values, but the mean width was **£323,336**. That very broad range and the small test set limit its usefulness. Coverage is not proof of precision. Subgroup metrics in `initial_metrics.json` are descriptive; some groups have just one test home.

EPC ablation: validation MAE **£63,110 without EPC**, versus **£65,019 with EPC**. This dataset supplies no useful validated EPC price signal. No retrofit-value premium should be inferred, and none is enabled. The generator methodology independently states that it adds no explicit EPC premium.

The saved `snapshot_model.joblib` is an isolated experiment artifact, deliberately incompatible with production valuation loading. The existing production/fixture artifact is preserved. Test predictions and splits are saved separately. Chronological evaluation is unavailable without sales dates.

## Reproduce

From the repository root:

```sh
.venv/bin/python -m pip install -r ml/requirements.txt -r backend/requirements.txt
.venv/bin/python -m evaluation.evaluate_initial_dataset
PYTHONPATH=backend:. .venv/bin/python -m pytest ml/tests evaluation/tests backend/tests -q --junitxml=evaluation/results/initial_tests.xml
```

P3's scripts currently expect CSVs beside the scripts, but the repo stores them in `data/csv/`. Evaluation imports the energy generator's pure functions and passes the actual data directly; no contributor files were changed.

Pending: documented intensity benchmarks, heat-pump subtype and solar contribution; P4's feasibility/scenario/carbon outputs and factors; actual LLM responses and human reviews; observed sales and timestamp-correct features. Those evaluations were left pending as requested.
