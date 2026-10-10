# CSV dataset integration

The running backend loads Data/csv/properties.csv (100 synthetic properties) and Data/csv/energy_usage.csv (1,200 synthetic monthly readings) by default. The source files and generation scripts are unchanged.

Schema adapter: case-normalize categories, rename age to property_age_years and current_value_estimate_gbp to current_property_value_gbp, and preserve source provenance. Boolean smart controls are mapped true to advanced and false to none as a documented simplification of the CSV field; the file cannot distinguish basic programmable controls. Generic Heat pump lacks source subtype, so heating_system remains null while the source category is retained in provenance. Solar=true lacks a contribution category, so renewable_contribution remains null; solar=false maps to none. Eligibility fields and market_index remain unknown.

Annualization: require one calendar year per property, reject duplicate property/month pairs and orphan readings, sum each fuel only with twelve valid months. Negative/nonfinite readings are rejected. Missing readings remain unknown; no seasonal extrapolation is performed. Structural zero gas is preserved for electric heating. Energy is labeled synthetic and retains coverage/year metadata in its method. Property snapshot and energy-year mismatch is disclosed according to the source methodology.

No source-backed intensity benchmark is provided by this dataset. Complete scores therefore remain unavailable. Known score components, energy intensity, annual energy and efficiency issues are returned. Retrofit feasibility/simulation and carbon remain pending P4 integration; the backend does not manufacture new scores or savings.

Live checks on port 8003:

| Property | Annual electricity kWh | Annual gas kWh |
|---|---:|---:|
| P00001 | 2997.41 | 27040.56 |
| P00002 | 1755.41 | 3543.74 |
| P00003 | 5051.29 | 0.00 |

GET /properties returned 100 records. GET /properties/P00001/assessment returned an unavailable overall score with benchmark identified as missing. A heat-pump scenario request returned HTTP 503 because the retrofit engine is absent. Captured responses are in dataset-run.json.

New tests cover dataset loading and sums, preserved unknown categories, missing fuel coverage, duplicate months, and orphan readings. Existing property route tests were updated for the default CSV dataset.
