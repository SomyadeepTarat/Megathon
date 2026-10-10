# Synthetic property-value impact

This is the integrated hackathon demonstration model, separate from the existing snapshot baseline and experimental EPC-sales model. Synthetic data is permitted by the official brief; these results do not establish real-market prices or real causal retrofit effects.

## Features and labels

`python -m ml.synthetic_impact` generates 1,800 independent synthetic property/scenario pairs with seed 254. Region vocabulary and regional median GBP/m² scales come from the supplied synthetic property CSV. Types include detached, semi-detached, terraced, flat and bungalow. New property IDs prevent overlap with supplied demo homes.

Inputs: floor area, bedrooms, age, region, property type and annual purchased-energy intensity `(grid electricity + gas) / area`. Current property value, synthetic sale targets, future scenario labels, and property IDs are not model features. EPC is preserved and is not projected.

The fully disclosed invented price equation is:

`area * regional_rate + type_offset + bedrooms*5000 - age*100 + coefficient*(300-intensity) + noise`

Type offsets are 30,000/15,000/5,000/0/10,000 GBP for detached/semi-detached/terraced/flat/bungalow. The hidden per-property coefficient is Uniform(100,140), and noise is Normal(0,15000). After intensity is baseline intensity × Uniform(0,1); every other feature, coefficient and noise term is fixed. Thus paired labels are known synthetic potential outcomes, not observed transactions or invented measurements presented as evidence.

## Training, selection and uncertainty

Separate property-group partitions: 720 fit, 360 selection, 360 calibration, 360 held-out test. Ridge is the baseline; HistGradientBoosting is selected only when selection MAE improves by at least 2%. Boosting is constrained nonincreasing in energy intensity. Selection-only energy ablation is reported. Calibration/test labels never choose the model or fit it.

Absolute baseline residuals calibrate price bands; paired contrast residuals calibrate the **separate uplift band**, using the finite-sample corrected 90% order statistic. The output current value is a supplied fixed anchor, with `[anchor, anchor]` baseline range; after value is anchor plus the same-model before/after contrast. Its band uses the paired radius, not two unrelated price bands. This explicitly differs from the legacy unanchored EPC-sales model.

Held-out metrics, generated pairs, split manifest, provenance and predictions are in `ml/reports/synthetic_impact`. The current nominal 90% paired band achieves approximately **86.4%** test coverage. This shortfall is disclosed, not tuned away using test labels. The interval is illustrative and not a guarantee, particularly outside the generator's scenario distribution.

## Runtime guards

Only records with `property.provenance.record = synthetic` and `annual_energy.quality = synthetic` use this path. Floor area, region, type, current value, recorded EPC, age, bedrooms and both fuel states must be present; values must be finite and within declared generator support. No model input is silently imputed. The two property states must preserve identity and all protected characteristics. Unseen regions/types and missing artifacts return unavailable. No numeric uplift is invented when an input fails.

`POST /scenarios/simulate` and budget/advisor scenarios use the actual simulator output. `POST /properties/{id}/valuation/impact` optionally accepts `scenario_annual_energy` alongside a complete `scenario_property`; these user-supplied totals are scenario assumptions, not certified physical simulation. Without scenario energy, physical upgrades retain the legacy unsupported-projected-EPC fallback.

Limits: annual purchased-energy intensity is affected by occupancy/behaviour and is not EPC. Distribution shifts invalidate coverage. The synthetic price relation deliberately contains an energy signal; recovering it is implementation evidence only. Real-market validation, causal inference and measured retrofit savings remain future work.
