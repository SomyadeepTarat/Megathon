# Expanded synthetic snapshot retraining — 11 October 2026

The pulled handoff expands the existing unchanged schema to 2,000 synthetic properties and 24,000 monthly readings. It supplies no observed transactions, dates, market indices or energy-related price signal. Training therefore uses only the provided baseline target `current_value_estimate_gbp`, with floor area, bedrooms, age, region and property type. No prices become predictors, no dates/eligibility/energy-price relationships are fabricated, and QA fixtures are excluded.

The full data is reproduced using the supplied generator. Every output/source checksum matches either byte-for-byte or solely after LF/CRLF conversion; all training CSVs and the split manifest match exactly. Physical/data audits report no errors; the original 100 properties are preserved. See data_verification.json.

The training CLI now supports the supplied persistent property/customer manifest, rejecting missing/extra/duplicate IDs, inconsistent customer IDs, invalid partitions and cross-partition customer leakage. All original assignments are retained. Counts: fit 1,088; selection 315; calibration 310; test 287. Candidate selection and grouped CV never use calibration or test labels.

HistGradientBoosting was selected because selection MAE £47,175 beat Ridge £50,221 by 6.1%, exceeding the existing 2% selection threshold. Both candidates were refitted on fit+selection before calibration and final evaluation.

| Expanded test set (287 properties) | MAE GBP | RMSE GBP | R² |
| --- | ---: | ---: | ---: |
| HistGradientBoosting | 45,985 | 69,285 | 0.801 |
| Ridge | 50,362 | 71,424 | 0.789 |
| Median baseline | 111,143 | 163,537 | -0.109 |
| Previous saved snapshot model | 73,478 | 99,980 | 0.586 |

The saved artifact reproduces every held-out prediction. Backend inference smoke-tested all 2,000 supplied properties successfully, with explicit illustrative status. Full test suite: 278 tests plus 34 subtests passed. Its nominal 90% split-conformal interval achieved **85.0%** empirical test coverage, with mean width **£182,525**. On the original 20-property holdout, MAE regressed from £47,391 to £50,685; RMSE regressed from £55,334 to £96,978. This small subset includes substantial tail error. See model_comparison.json and subgroup metrics.

**Promotion decision:** retain `ml/models/expanded_snapshot.joblib` as a separately evaluated candidate; do not overwrite the active `snapshot.joblib`. Expanded point prediction improves overall, but interval undercoverage and original-holdout regression prevent an unqualified replacement recommendation. Do not tune or widen intervals using test labels. Further model/uncertainty development needs fresh validation data or a predeclared nested evaluation protocol. Do not claim real-market accuracy.

The existing synthetic retrofit-impact model remains separate. These new price labels have no energy-dependent price relationship and cannot train a defensible new uplift model. Retraining that model on fabricated paired labels would violate the scope of the provided data.

## Reproduce

Run from the repository root:

```sh
.venv/bin/python Data/scripts/expand_dataset.py --total 2000
.venv/bin/python -m ml.train_valuation \
  --target-kind snapshot \
  --data Data/generated/kew_synthetic_v2/properties.csv \
  --provenance ml/expanded_snapshot_provenance.json \
  --split-manifest Data/reports/kew_synthetic_v2/split_manifest.csv \
  --output ml/models/expanded_snapshot.joblib \
  --reports ml/reports/expanded_snapshot
.venv/bin/python -m pytest -q
```

Full generated CSVs and model binaries remain ignored by Git. Reports, provenance, split assignments and reproducible code provide the handoff. The optional backend override `VALUATION_BASELINE_MODEL_PATH=ml/models/expanded_snapshot.joblib` is available for explicit candidate review, not enabled by default.
