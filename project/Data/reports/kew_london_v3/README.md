# Reviewed London simulation v3 — 2026-10-11

Generated 2,000 properties and 24,000 readings with unchanged 51/13-column
schemas. Original 100 properties and 1,200 readings remain cell-for-cell intact.
The 1,900 new homes are London simulations, not observed matched records.

- Official references and raw download hashes:
  `Data/manifests/london_reference_v1.json`.
- Generation/provenance/limits: `Data/relations/london_simulation.md`.
- Development errors and grouped learning curves: `development_diagnostics.json`.
- Independent calibration and one final evaluation: `final_evaluation.json`.
- Stable customer assignments: `split_manifest.csv`.
- Frozen pilot coefficients: `parameters.json`.
- Audit and marginal source comparison: `quality_report.json`.
- Final configuration marker: `FINAL_EVALUATION.json` (also in ignored output).

## Validation

29 tests passed across Data/tests, backend/tests/test_dataset.py and
ml/tests/test_snapshot.py. All 2,000 records load through the unchanged backend,
produce available scores and pass the existing ML snapshot validator. A full
rerun under Python 3.10.11 was byte-identical; output checksums were verified.
No canonical CSV, emission-factor, model, API or frontend code was changed.
The backend API test needed to run outside the network-restricted sandbox and
emitted one upstream TestClient deprecation warning.

New London median grid electricity: 2,463.60 kWh versus the NEED 2024 London
reference 2,466.30. Median gas among simulated gas-heated homes: 10,787.22 kWh
versus the reference 10,817.37. These are marginal simulation checks across
different historical samples, not measured validation of real homes.

## Frozen evaluation findings

803 fresh fit customers, 334 selection, 381 independent calibration and 382
fresh test customers. The original 100 are diagnostic-only and excluded from
all four partitions. New customers do not reuse v2 identifiers. Ridge was
selected on development errors by the existing candidate rule; no production
artifact was replaced. Model features remain area, bedrooms, age, region and
property type. No EPC, sale price, retrofit uplift or latent borough feature
was added.

Selection MAE was GBP 209,002. Errors were largest for detached homes and the
GBP 1 million-plus band. Grouped fit-only learning curves did not show a
consistent improvement from 250 to 803 examples. More samples do not recover
missing location information: latent borough variation is intentionally not
available to the unchanged region-level inputs.

The final test was evaluated once after freezing the generator and calibration:
MAE GBP 210,234; nominal 90% price-proportional intervals covered 89.53% of 382
synthetic labels. Mean interval width was GBP 701,118, indicating substantial
uncertainty. Type coverage was 88.0% detached, 88.0% flats, 92.4% semi-detached
and 91.6% terraces. The declared constant-width comparator covered 91.36%
overall but only 60% of detached homes and had a wider mean interval of
GBP 873,794. The interval policy was not chosen using these test outcomes.

These findings are agreement with a public-reference simulator, **not evidence
of accurate market valuation or causal retrofit premiums**. They cannot be
directly compared with the earlier quoted 85% run without matching its exact
dataset, split and model version. No parameters were adjusted after the fresh
test result. Future development requires another independent cohort; do not
delete the evaluation marker to keep testing this one.

Unknown eligibility remains blank. Costs/tariffs were not invented or added to
the schema. EPC certificate-lodgement bias, equal latent borough weights,
assumed conditional size/equipment distributions and unmatched source periods
remain material limits. SmartMeter household readings were not imported, so
seasonal profiles are still an assumption. Dated observed EPC/transaction joins
would require a separate verified source and matching process.

Run generation with `python Data/scripts/simulate_london.py --total 2000 --handoff`.
Use the generated pair and the manifest deliberately; the live app still reads
its original CSV pair and the existing production trainer does not automatically
consume the new manifest.
