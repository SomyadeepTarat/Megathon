# London v3 model review and integration decision

## Data review

This pull contains a public-reference synthetic London simulator with the same 51 property / 13 meter columns. It generates 1,900 fresh London properties plus 100 legacy diagnostics, with 24,000 monthly readings. No matched observed sale transactions, transaction dates, borough-level inference feature or energy-related price signal is provided. Unknown compatibility remains unknown and prices remain synthetic.

The local generation passes the physical/schema audit and preserves the original 100 records. Tracked 30-property/360-reading samples match exactly. Source/checksum verification is recorded in data_verification.json: most checks match exactly or after line-ending conversion. Generated properties/diagnostics are not byte-identical to the supplied Python 3.10.11 run under this Python 3.13 runtime. Frozen selected model and proportional calibration reproduce within 1e-9. No external reference re-extraction was performed.

The supplied final_evaluation.json is a frozen configuration marker, not a full metrics report, despite its name. It is preserved as generated FINAL_EVALUATION.json. This cohort was already exposed; local scoring is a deployment reproduction/comparison, not a fresh independent evaluation. No choices were tuned from its test results.

## Training and results

The trainer explicitly excludes legacy_diagnostic and consumes the supplied manifest: 803 fit, 334 selection, 381 calibration, 382 test customers. No group overlap. Features remain floor area, bedrooms, age, region and property type. Ridge is selected by the existing selection-MAE rule. Price-proportional intervals use the data team's predeclared max(predicted price, £50,000) scale and separate calibration residuals. The backend now supports that optional artifact policy; existing absolute-interval artifacts retain their behavior.

| Same fresh London test cohort | MAE | RMSE | R² |
| --- | ---: | ---: | ---: |
| Active snapshot model | £223,010 | £383,700 | -0.102 |
| v2 candidate | £197,665 | £328,595 | 0.192 |
| v3 Ridge | £210,234 | £318,059 | 0.243 |

Nominal 90% proportional interval coverage: **89.53%**, mean width **£701,118**. These broad intervals expose missing location detail rather than concealing it. On ten legacy London diagnostics, v3 MAE is £208,234 versus £148,674 for the active model; these are diagnostic/in-sample comparisons, not an independent legacy holdout claim.

## Earlier comparison decision (superseded by the London-only demo scope)

**Do not replace the active demo model or dataset.** v3 improves RMSE and coverage for its own London cohort, but does not uniformly improve point predictions, regresses on existing London examples, and supports only Greater London. Replacing the active global baseline would make other regions unavailable. The new dataset also has unknown eligibility and no installed-cost/tariff evidence; it cannot independently drive a complete retrofit-budget demo. No such values were invented. Retrofit-uplift training remains unsupported by these price labels; its existing separately disclosed illustrative demo model is unchanged.

Candidate artifact: ml/models/london_snapshot.joblib (ignored, reproducible). Baseline API integration tested with explicit candidate path and repository override; assessment succeeds, synthetic status/ranges are preserved, unknown heat-pump compatibility is rejected. All 2,000 scores are available; 1,896 of the 1,900 fresh homes return illustrative valuation; four explicitly return unavailable for floor area outside development support. Full fresh-cohort inference results are in integration_verification.json. Active default configuration is unchanged.

## Reproduce

```sh
.venv/bin/python Data/scripts/simulate_london.py --total 2000
# Preserve the already-exposed final-evaluation guard; do not rerun --final.
cp Data/reports/kew_london_v3/final_evaluation.json Data/generated/kew_london_v3/FINAL_EVALUATION.json
.venv/bin/python -m ml.train_valuation \
  --target-kind snapshot \
  --data Data/generated/kew_london_v3/properties.csv \
  --provenance ml/london_snapshot_provenance.json \
  --split-manifest Data/reports/kew_london_v3/split_manifest.csv \
  --exclude-split legacy_diagnostic \
  --interval-policy price_proportional \
  --output ml/models/london_snapshot.joblib \
  --reports ml/reports/london_snapshot
.venv/bin/python -m pytest -q
```

Before future promotion: obtain observed dated labels and usable location features, or explicitly narrow the product to a London illustrative simulation; predeclare new model choices, reserve fresh independent evaluation data, and assess point error, coverage, interval usefulness and demo-input support together. Do not fabricate an energy premium, survey eligibility or model input.

## Active London demo adoption — 11 October 2026

The user explicitly narrowed the active demo to London and authorized replacement. The default now serves the 1,900 fresh London rows and london_snapshot.joblib. The original 100 rows remain diagnostic only. This promotion reflects the requested geographic scope, not uniformly better error or observed-market validation. Unknown eligibility, costs and tariffs remain unknown. Run scripts/prepare_london_demo.py to reproduce the active data and artifact; evaluation/results/london_active/README.md documents integration checks and limitations.
