# Kew synthetic dataset v2 — unchanged schema

Generate 2,000 properties and 24,000 monthly readings from the project root:

```powershell
python Data/scripts/expand_dataset.py --total 2000 --handoff
.venv/Scripts/python.exe -m pytest Data/tests/test_expansion.py backend/tests/test_dataset.py ml/tests/test_snapshot.py -q
```

Python 3.10+ and the standard library suffice for generation. Tests require the
existing backend and ML dependencies (`python -m venv .venv`, then
`.venv/Scripts/python.exe -m pip install -r backend/requirements.txt -r ml/requirements.txt`). Full outputs are in
`Data/generated/kew_synthetic_v2/` and excluded from Git. The reviewed audit,
provenance/checksums, split manifest and 30-property sample are retained under
`Data/reports/kew_synthetic_v2/` and `Data/samples/kew_synthetic_v2/`.
The generator reproduces all of them. `Data/manifests/kew_schema_v1.json` locks
the exact 51 property and 13 meter columns, including their order;
`Data/manifests/kew_data_dictionary_v1.json` documents the existing fields.

## Migration and inference

There is no schema migration, field rename, new ML input, model retraining,
frontend/API change or change to emission factors. The canonical 100-property
CSV pair remains unchanged, including all original cell values. To consume the
expansion, pass the two generated CSV paths to `CsvPropertyRepository` or the
existing snapshot-training CLI's input argument. Changing the live application's
data paths is a separate integration decision. No observed transaction-training
file is generated: this schema lacks sale dates and observed sale prices.

Existing snapshot ML features remain floor area, bedrooms, age, region and
property type, using the existing `floor_area_m2` alias. Price is a target, never
an input; energy ratings and retrofit uplift are not new valuation features.
`derived_diagnostics.json` is a separate diagnostic artifact, **not consumed by
ML**. It contains purchased energy/area, log area, area/age bands and existing
region/year metadata. Missing readings, incomplete calendar-year coverage or
missing/nonpositive area produce unavailable intensity; there is no imputation,
target encoding or inferred transaction date. Adopting any diagnostic as an ML
feature requires Person 5's separate agreement and pipeline update.

## Generation and provenance

The first 100 properties and 1,200 readings are preserved cell-for-cell. New IDs
start at P00101/C00101. The existing generator's conditional distributions are
reused in independently seeded batches of 90 (seeds 43, 44, ...). Partial final
batches keep a stable prefix when the requested size grows. These are inherited
synthetic assumptions, not a newly verified UK population distribution; small
batches enforce type/heating quotas and may leave distribution artifacts.

Price uses inherited regional/type anchors, floor area, bedrooms, age and
independent lognormal noise. It does not use energy categories or a retrofit
uplift formula. Reusing historical anchors is a simulation choice, not current
market evidence. Energy retains the existing physical model, stable per-ID seed
42, assumed occupancy from bedrooms, fabric/climate modifiers, boiler efficiencies
0.72/0.90, heat-pump SCOP 3 and hot-water COP 2.5, and resistance efficiency 1.
Solar offsets grid imports; generation and self-consumption are separate.
Annual component fields are recomputed from each new property's monthly model.
The existing benchmark is a fixed synthetic reference per property type, not
an official NEED consumption standard. Heat pumps assume air-source subtype.
Unknown surveyed eligibility remains blank; nonapplicable efficiencies remain
blank while zero fuel use for electric homes is a genuine modelled zero.

Meter energy is the 2025 calendar year. Source age is approximately one year
newer; equipment is assumed unchanged throughout the scenario. The schema has
no dated snapshot to establish observed alignment. Applying unchanged 2026
emission factors to these meters is a scenario calculation, not an estimate of
historical 2025 emissions. Original source rows cite a missing P3_HANDOFF.md;
the source audit discloses this, without inventing replacement evidence.

No external records are joined. Only property_id joins monthly readings to
properties; duplicate IDs, duplicate months and unmatched records are rejected.
No postcode-only matching, inferred UPRNs, actual EPC records or sales are
introduced. Reliable observed enrichment needs an authorised source plus stable
keys and dates; those are unavailable in this unchanged schema. Provenance
separates inherited rows, simulated new base fields, modelled physical fields,
synthetic benchmarks and unavailable compatibility fields. Checksums capture
sources, scripts, schema, outputs and unchanged emission-factor provenance.

## Evaluation and QA

`split_manifest.csv` preserves all assignments in
`ml/reports/current_snapshot/split_manifest.csv`, including the existing test
holdout. New customers are assigned using a stable SHA-256 hash with approximate
55% fit / 15% selection / 15% calibration / 15% test proportions, matching the
existing four-way ML protocol. All months follow their property's/customer's
assignment. No chronological split is claimed because there are no transaction
dates. Reports include category coverage and counts by split.

The manifest is an explicit handoff: existing `ml.valuation.train()` still uses
its own GroupShuffleSplit and does **not** read this manifest. Person 5 must wire
it in before evaluating the expansion with these persistent assignments. Do
not tune using test rows or calculate full-dataset target encodings. Synthetic
evaluation only measures agreement with the simulator; it cannot establish
real-market accuracy, causal retrofit premiums or actual savings.

`edge_cases/` contains 60 isolated QA properties, with the same headers, covering
missing months/readings/physical inputs/area, real modelled zero gas, a zero-use
scenario, conflicting equipment flags and explicitly infeasible retrofits.
They are excluded from training and split manifests. Invalid fixtures are
intentional and should be rejected or produce unavailable results, not repaired
using fabricated defaults. The main audit checks ID/month uniqueness, coverage,
nonnegative finite energy, fuel/thermal balances, PV balances, annual/monthly
agreement, categories and ranges. Extreme ranges are descriptive synthetic
checks, not empirical validation against real homes. Retrofit eligibility and
property ranking remain separate existing engine responsibilities.
