# Verification — 2026-10-11

- Generated 2,000 properties, 24,000 monthly readings and 60 separate QA fixtures.
- Exact existing 51-property-column and 13-meter-column names/order retained.
- All original 100 properties and 1,200 readings preserved cell-for-cell;
  canonical CSVs and emission-factor files have no Git diff.
- Source audit and expanded physical/coverage/join audits report no errors.
- A full rerun was byte-identical; every recorded output SHA-256 was verified.
- All 2,000 records loaded through CsvPropertyRepository, produced available
  scores and passed the unchanged ML validate_snapshot function.
- 24 regression tests passed: Data/tests/test_expansion.py,
  backend/tests/test_dataset.py and ml/tests/test_snapshot.py.
- Test runtime: project-local Python 3.10 venv with existing backend/ML
  requirement ranges. One external Starlette TestClient deprecation warning.
  The local API test stalled in the network-restricted sandbox and passed
  outside that sandbox. OMP_NUM_THREADS/OPENBLAS_NUM_THREADS were limited to 1
  for the final test run. No application or model code was changed to pass it.
- Splits: 1,088 fit; 315 selection; 310 calibration; 287 test. No unseen
  property type, region, heating or EPC categories relative to fit.

Limits: synthetic data has no observed-market or causal validation. Eligibility
is unknown unless explicitly provided in isolated fixtures. No dated observed
snapshot/transaction alignment can be established. The existing trainer must
explicitly adopt the supplied split manifest before it can preserve these
assignments on the expanded dataset; no expanded model was trained here.
Derived diagnostics are sidecars and are not new model inputs. The running
application still uses its unchanged original CSVs until deliberately pointed
at the versioned expanded pair.
