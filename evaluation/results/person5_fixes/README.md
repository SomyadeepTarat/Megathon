# Person 5 fixes and current verification

Verified against the updated repository dataset: 100 synthetic property records and 1,200 complete monthly readings. This supersedes the historical audit's missing-score and incompatible-snapshot-artifact findings.

## Changes

- CSV ingestion now uses supplied heating subtype, renewable contribution and property-type benchmark fields. All **100/100 full scores** and all seven components are available. P00001 scores **22/100**. Benchmark source and assumed/synthetic-input warnings remain visible; these are not official reference standards.
- Added validated GET/POST `/properties/{property_id}/valuation` baseline inference. **97/100 illustrative estimates**, with three explicit refusals because floor area lies outside development-data bounds. Missing artifacts/dependencies return a reason, never a made-up estimate. The backend-directory launch can import the ML package.
- Snapshot training/evaluation/inference now share one artifact contract. Target is the supplied synthetic current estimate; features are area, age, bedrooms, region and property type. EPC, the target and market index are excluded. The snapshot model cannot claim retrofit uplift.
- Added five-fold grouped validation using fit groups only, held-out subgroup error/coverage diagnostics, and a separate chronological backtest for observed dated sales. Current data has no such sales. Sales preparation accepts dataset area naming and EPC-at-sale fields, and rejects EPC dates after sale.
- Initial dataset evaluation tolerates blank optional physical fields, validates required snapshot inputs, verifies energy regeneration, and creates inference-compatible artifacts. Default pytest now includes carbon-engine tests.

## Measured model limitations

Ridge was selected on validation data. On 20 held-out synthetic properties: **MAE £47,391; RMSE £55,334; R² 0.809**. Nominal 90% intervals cover 20/20 test targets but average **£301,820 wide**. Five-fold fit-only Ridge mean MAE is approximately £99,462, indicating instability with very little data. The model remains an illustrative baseline, not a precise market valuation. Removing the unsupported EPC feature changes metrics relative to the historical experiment; no improvement in market accuracy is claimed.

Three out-of-support properties deliberately retain unavailable valuations rather than silently extrapolating. No observed sale prices, independent future-period evaluation, reviewed EPC premium evidence, paired retrofit outcome data or human factual-accuracy sign-off were supplied. Subgroup sample sizes are too small to certify fairness. Those evidence limitations cannot be fixed by fabricating data or changing a status label.

The scenario route still uses pending retrofit/carbon adapters in `backend/app/main.py`. Their integration, physical-input mapping and official carbon factors remain with Persons 1/3/4. UI rendering is Person 2's responsibility; the backend now returns `score.score` and `score.status="available"` for every dataset property.

## Run locally

```sh
.venv/bin/python -m ml.train_valuation --target-kind snapshot --data Data/csv/properties.csv --provenance ml/snapshot_provenance.json --output ml/models/snapshot.joblib --reports ml/reports/current_snapshot
.venv/bin/python -m evaluation.evaluate_initial_dataset --output evaluation/results/person5_fixes
.venv/bin/python -m pytest -q
.venv/bin/python -m uvicorn app.main:app --app-dir backend --reload --port 8001
```

Restart an already-running backend to reload CSVs: the repository is initialized at startup. Check `/properties/P00001/assessment` for score and `/properties/P00001/valuation` for baseline inference. Generated model binaries are ignored by Git, so collaborators must run training or use a trusted compatible model path via `VALUATION_BASELINE_MODEL_PATH`.

Evidence: `initial_metrics.json`, `property_scores.csv`, `assessments.json`, `snapshot_split_manifest.csv`, `held_out_snapshot_predictions.csv`, and `api_verification.json`; training details in `ml/reports/current_snapshot/valuation_metrics.json`.
