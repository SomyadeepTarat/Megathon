# London public-reference simulation v3

The property schema (51 ordered columns), monthly energy schema (13 columns),
API contracts and ML input features are unchanged. This version contains the
original 100 rows and readings unchanged, plus 1,900 new London properties and
their complete 2025 readings. It supersedes v2 as the recommended expanded
simulation; the original CSV pair, v2 outputs, models and emission factors are
retained. Full v3 files are under `Data/generated/kew_london_v3/`, excluded from
Git; tracked reports and a 30-property sample are under the corresponding
`Data/reports/` and `Data/samples/` directories.

## References actually used

`Data/manifests/london_reference_v1.json` records extracted values, periods,
sheet/row references, download URLs and raw SHA-256 checksums.

| Reference | Use | Scope and limitation |
|---|---|---|
| [HM Land Registry HPI July 2026 downloads](https://www.gov.uk/government/statistical-data-sets/uk-house-price-index-data-downloads-july-2026) | London type and 33 borough/type price anchors | Aggregate HPI averages, **not observed prices matched to synthetic homes**. No Price Paid record is joined. |
| [London's Housing Stock, November 2024](https://www.london.gov.uk/media/107179/download) | Census 2021 household accommodation mix; EHS 2021 build-age bands and post-2002 flat share | Excludes mobile/temporary accommodation unsupported by the existing schema. Historical population shares are not extrapolated to current stock. |
| [EPC live tables, EB1](https://www.gov.uk/government/statistical-data-sets/live-tables-on-energy-performance-of-buildings-certificates) | London existing-dwelling certificate ratings and average floor area, four 2025 quarters | Lodgements can repeat a property and are biased by sales/lettings. They are not a stock sample or current individual EPC evidence. Bulk EPC access now requires sign-in; no account or personal records were used. |
| [NEED 2026 headline tables, 2024 data](https://www.gov.uk/government/statistics/national-energy-efficiency-data-framework-need-consumption-data-tables-2026) | London gas/electricity medians from tables 15/16 | Separate fuel samples and a different population/year from the Census/EPC/HPI references. Marginal energy anchors, not a verified joint distribution. |
| [London SmartMeter catalogue](https://data.london.gov.uk/dataset/smartmeter-energy-consumption-data-in-london-households-vqm0d) | Reviewed scope and limitations only | 2011–2014 data, including a dynamic-tariff subgroup. Household readings were not downloaded; the existing seasonal shape remains an assumption. Old tariffs are not applied to current scenarios. |

The downloaded HPI attribute CSV is approximately 16 MB (the catalogue's file
size is understated), EPC 1.9 MB and NEED 0.55 MB. Raw files remain ignored.
Public government tables are subject to their published Open Government Licence
and exceptions; the London source retains its source attribution. The
SmartMeter catalogue states Creative Commons Attribution but no meter data is
redistributed here. Generated property/meter rows are explicitly synthetic.

## Frozen generation rules

Independent hash RNG streams use seed 20261011 for physical characteristics and
pricing. Fresh property/customer IDs begin at P100001/C100001, so revised labels
cannot silently replace previously inspected v2 IDs. The original hundred are
retained solely as `legacy_diagnostic` in the evaluation manifest.

Property types follow the published London household mix after excluding the
mobile category. Age bands use the EHS shares; years are drawn uniformly inside
each band, with the oldest band truncated at 1850. Newer-than-2002 homes use the
reported 86.7% flat share; the older cohort is adjusted to preserve the overall
flat marginal. This is a partial joint reconstruction, not observed microdata.
Build years after the 2021 survey are not invented. Age is expressed for the
2026 scenario and reduced by one in the inherited 2025 energy calculation.

Conditional floor areas use the existing type means with a disclosed lognormal
sigma of 0.30 and bounds 25–350 m2. Bedroom/fabric/glazing/system/solar/control
probabilities remain modelling assumptions. The published EPC average area is
reported as a comparison, not forced into a claim of stock representativeness.
The EPC rating distribution is mapped monotonically from the physical latent
efficiency score using quantiles fitted on a disjoint 3,000-home pilot. A
simulated letter is neither an official certificate nor a calculated SAP score.

An independently seeded `PILOT` population anchors the space-heat and appliance
intercepts to NEED London's 2024 medians. It never reads development,
calibration or test valuation errors. Hot-water demand, boiler efficiency,
SCOP/COP, PV generation and behavioural dispersion retain the existing model.
Every adjusted monthly fuel/demand/PV balance and annual physical field is
recomputed; missing eligibility fields stay blank. New benchmarks are explicitly
synthetic London references using the same v3 scales, fixed 100 m2/3 occupants/
age 54, average fabric, double glazing, modern boiler and no PV/controls.
They are not official consumption standards.

Prices use type-specific official borough anchors, size/bedroom/age modifiers
and the unchanged 0.18 log-price noise. Equal latent borough weights are an
assumption; borough is a provenance sidecar, **not a new ML input**. Type
intercepts are normalised against public London type averages using the pilot.
No EPC/fabric/heating/retrofit improvement enters the pricing formula. Residual
location variation therefore remains unknowable to the unchanged region-level
ML inputs, creating legitimate irreducible synthetic uncertainty. Noise is not
reduced to inflate measured accuracy. No tariffs/costs/eligibility are invented.

## Evaluation protocol

Fresh customers are reserved by a version-specific SHA-256 hash before any
valuation evaluation: approximately 40% fit, 20% selection, 20% calibration,
20% test, matching the current snapshot trainer's proportions. All records for
a customer stay together. The development evaluator actually consumes this
manifest; the production trainer itself is unchanged and must explicitly adopt
the manifest before using these assignments. Running its usual random splitter
on all 2,000 rows would not preserve the reserved holdout.

Development diagnostics break errors down by region, property type, size and
target price band. Price bands are diagnostic groupings only, never model
features. Learning curves use five grouped folds of fit rows only. Existing
Ridge/HistGradientBoosting candidates and the existing 2% selection improvement
rule are reused; there is no production model switch. Calibration uses fresh,
independent groups after refitting on fit+selection.

The declared interval method calibrates absolute residual divided by
`max(predicted price, GBP 50,000)` to allow larger absolute uncertainty for
expensive homes. A constant-width comparator is reported without selecting a
method based on test coverage. Coverage is marginal under synthetic
exchangeability, not guaranteed for each region/type. Both calibration samples
and evaluation labels are simulated, so results cannot establish real-market
accuracy or causal retrofit premiums. The supplied 85% historical coverage claim
is not used as a tuning target; the current checked-in original snapshot report
records 100% on its own small test split, demonstrating that those runs are not
directly comparable.

`--final` evaluates the fresh test set once after choices are frozen and records
a marker preventing repeat evaluation. After viewing it, treat it as exposed:
further development needs another independently reserved version/cohort. Routine
schema/physical integrity checks do not tune generator/model parameters from
test performance. Production models, API calls and backend functionality are
unchanged. Retrofit-value uplift remains unsupported by this baseline dataset.

## Reproduce and consume

Generation uses Python 3.10+ and the standard library with the tracked reference
JSON; network access is unnecessary:

```powershell
python Data/scripts/simulate_london.py --total 2000 --handoff
$env:OMP_NUM_THREADS='1'
$env:OPENBLAS_NUM_THREADS='1'
.venv/Scripts/python.exe Data/scripts/evaluate_london.py
.venv/Scripts/python.exe -m pytest Data/tests backend/tests/test_dataset.py ml/tests/test_snapshot.py -q
```

Use `.venv` with existing backend/ML dependencies for tests/evaluation. For a
byte-identical reproduction use Python 3.10.11, the recorded generation runtime;
other Python versions can produce small floating-point differences. For a
new, unexposed cohort, append `--final` to the evaluator only after freezing all
decisions; the delivered cohort has already undergone its final evaluation.
Do not remove its marker to repeat the test. Re-running generation reproduces
the dataset and retains the marker; existing-model/deployment paths are not
updated automatically. Pass the v3 CSV pair to CsvPropertyRepository or Person
5's manifest-aware training workflow when deliberately consuming it.

The final marker is also archived in `Data/reports/kew_london_v3/FINAL_EVALUATION.json`.
If ignored generated files are removed and reproduced, restore that marker to
the generated directory to retain the local repeat-evaluation guard. The
tracked final report already exposes this cohort; recreating files does not
make it a new independent test set.

To retrieve and re-extract the official references, run
`python Data/scripts/fetch_london_references.py` with network access and then
`python Data/scripts/prepare_london_references.py` with a read-only `openpyxl`
installation (the bundled workspace Python includes it). Compare checksums
before accepting revisions. Do not overwrite the reviewed reference snapshot
without versioning the generator and reserving new evaluation customers.

The existing data dictionary still applies. No new CSV column, required input,
observed transaction date, UPRN or feature engineering is introduced. Diagnostic
and latent-provenance sidecars are not read by the ML feature pipeline.
