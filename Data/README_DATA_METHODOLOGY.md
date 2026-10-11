# Kew data methodology, formulas, quality and reproducibility

**Dataset version:** `kew_london_v3` · **Reviewed:** 11 October 2026

This README documents every field in the property, energy and emission-factor
CSVs, how labels and derived values are generated, and the evidence supporting
the reported results. The property schema has **51 columns**, energy has **13**,
and emission factors have **10**. Column names, order, API contracts and ML input
features are unchanged. This documentation does not modify the data or models.

The 2,000-property dataset comprises **100 retained synthetic legacy properties**
and **1,900 newly simulated London properties**, with **24,000 monthly energy
rows** for January–December 2025. The original hundred include multiple regions;
the new cohort is entirely Greater London. No property or meter row is an
observed household record. Published reference statistics and emission factors
are distinct from the synthetic property-level records they inform.

## 1. Files and evidence inventory

| File or directory, relative to `Data/` | Contents and role |
|---|---|
| `csv/properties.csv`, `csv/energy_usage.csv` | Unchanged canonical 100-property seed dataset; retained cell-for-cell in v3. The active application still uses this pair. |
| `generated/kew_london_v3/properties.csv` | Full versioned 2,000-property simulation; ignored by Git. |
| `generated/kew_london_v3/energy_usage.csv` | Full versioned 24,000-row meter simulation; ignored by Git. |
| `csv/emission_factors_2026.csv` | Two unchanged published operational-emission factors. |
| `csv/emission_factors_2026.provenance.json` | Source workbook URL/hash, licence, exact extracted rows and accounting limits. |
| [Locked schema](manifests/kew_schema_v1.json) | Exact ordered CSV headers; generation rejects schema drift. |
| [Machine-readable dictionary](manifests/kew_data_dictionary_v1.json) | Existing field types, units, blank semantics and provenance. This README explains the v3-specific formulas. |
| [Public-reference snapshot](manifests/london_reference_v1.json) | Extracted source values, geography, period, worksheet references and raw download SHA-256 hashes. |
| `generated/london_public_references/` | Downloaded official CSV/ODS/XLSX files and `downloads.json`; ignored by Git. |
| [Tracked sample](samples/kew_london_v3/) | 30 properties: first 10 legacy rows plus first 20 new rows, and all their 360 monthly records. It is an inspection sample, not a representative validation sample. |
| [Tracked reports](reports/kew_london_v3/) | Quality audit, pilot parameters, provenance/checksums, splits, development diagnostics and final evaluation. |
| `generated/kew_london_v3/edge_cases/` | 60 isolated synthetic QA properties and deliberately modified readings; excluded from model training/evaluation. |
| `generated/kew_london_v3/derived_diagnostics.json` | Optional descriptive transformations, not ML inputs. |
| `generated/kew_london_v3/latent_provenance.json` | Simulated borough, property ID, source-kind declaration and split; never an observed property match or a model feature. |
| `generated/kew_london_v3/FINAL_EVALUATION.json` | Frozen configuration/source hashes and exposed-test marker; also archived in tracked reports. |

`parameters.json` stores the pilot count/namespace, heat and appliance scales,
six EPC cutoffs, four price intercepts, residual price-noise sigma and freeze
policy. `provenance.json` stores version/runtime, schema/input declarations,
source/output hashes, reference location, pricing/eligibility/SmartMeter notes
and limits. `split_manifest.csv` contains `property_id`, `customer_id`, `split`.
These sidecars do not add required CSV columns or ML features.

## 2. Public sources: use, coverage and provenance

| Source | Reference period and extraction | Actual use and limitations |
|---|---|---|
| [London's Housing Stock, November 2024](https://www.london.gov.uk/media/107179/download) | Printed pages 10–12: Census 2021 accommodation counts; English Housing Survey 2021 age bands and post-2002 flat share. | Guides marginal type/age distributions. Household counts are not the same as all dwelling counts. Excludes 4,406 mobile/temporary households unsupported by the schema. No update to 2026 stock is inferred. |
| [HM Land Registry HPI July 2026](https://www.gov.uk/government/statistical-data-sets/uk-house-price-index-data-downloads-july-2026) | Attribute CSV filtered to `Date=2026-07-01`, London `E12000007`, and 33 borough codes beginning `E09`. | Supplies type/borough average-price anchors. Aggregate HPI values are not sale prices matched to generated homes; no Price Paid transactions were joined. |
| [EPC live tables](https://www.gov.uk/government/statistical-data-sets/live-tables-on-energy-performance-of-buildings-certificates) | Existing-dwelling EB1 ODS, `EB1_by_Region`, London quarters `2025/1`–`2025/4`. | Rating counts calibrate a synthetic latent score; total certificate area/count gives a descriptive mean-area comparison. Lodgements may repeat properties and are biased by sale/letting activity; not stock-representative microdata. |
| [NEED consumption tables 2026](https://www.gov.uk/government/statistics/national-energy-efficiency-data-framework-need-consumption-data-tables-2026) | Headline England/Wales workbook, 2024 row 27, `Table_15` gas and `Table_16` electricity; H sample, V mean, AJ median. | London medians anchor a disjoint physical pilot. Gas and electricity have different sample populations; their counts are not used to estimate heating-system prevalence. |
| [London SmartMeter catalogue](https://data.london.gov.uk/dataset/smartmeter-energy-consumption-data-in-london-households-vqm0d) | 2011–2014 trial, including a dynamic-tariff subgroup. | Catalogue reviewed only. Household readings were not imported, seasonal profiles remain assumptions, and historical tariffs are not reused as current tariffs. |
| [DESNZ conversion factors 2026](https://www.gov.uk/government/publications/greenhouse-gas-reporting-conversion-factors-2026) | Revised flat-format workbook, 31 July 2026 version; exact workbook rows recorded in provenance. | Operational emissions only. Applying 2026 factors to 2025 simulated readings is a scenario convention, not historical 2025 emissions validation. |

Government datasets carry their published Open Government Licence and exceptions;
source attribution is retained for the London housing report. The SmartMeter
catalogue declares Creative Commons Attribution; no meter data is redistributed.
Download URLs and checksums identify the reviewed snapshots. Revisions require
a new reference/generator version and independently reserved evaluation cohort.

There are **zero external property-level joins**. Internal joins use
`property_id`; monthly uniqueness uses `(property_id, month)`. There is no
postcode-only matching, inferred UPRN, observed sale date or future EPC join.
The selected sources describe different historical populations and cannot
establish a verified joint distribution for current individual homes.

## 3. Notation, units and missing-value conventions

- `A`: floor area in m2; `a`: scenario property age in years; `b`: bedrooms.
- `o = min(5, max(1, b))`: assumed occupants, not observed household occupancy.
- `H_m`, `W_m`: delivered space heat/hot water in month `m`, kWh.
- `B_m`: base appliance electricity; `D_m`: total electrical demand, kWh.
- `G_m`: purchased gas; `I_m`: purchased/grid electricity, kWh.
- `V_m`: PV generation; `S_m`: PV self-consumption; `X_m`: PV export, kWh.
- `eta`: boiler efficiency; `c_s`: space-heating COP; `c_w`: hot-water COP.
- `k_h`, `k_e`: pilot-calibrated space-heat and appliance multipliers.
- `sum_m`: sum of the twelve calendar months; `clip(x,l,u)=max(l,min(u,x))`.
- `N(mu,sigma)`: normal draw with standard deviation `sigma`; `U(l,u)`: uniform draw.

CSV numbers are stored as text. Purchased monthly gas/grid values are formatted
to 2 decimal places; monthly and annual physical kWh components to 6; renewable
share to 9; floor area to 1; generated prices to the nearest GBP 1,000. Python
`round()` and formatting semantics are used, including nearest-even ties.
Several annual fields sum already rounded monthly physical values, so formula
identities are verified with explicit rounding tolerances, not exact float equality.

Blank compatibility flags mean **unknown**, not false. Blank efficiencies/COPs
mean **not applicable to that heating system** in this complete main simulation.
Genuine modelled zero gas for electric homes is `0`, distinct from a missing
reading. Missing/incomplete annual readings remain unavailable; they are not
imputed as zero. False feasibility in QA fixtures is an explicit synthetic
test condition, not survey evidence. `solar` does not imply roof suitability.

## 4. Property generation and label formulas

### 4.1 Stable random streams and identity

For the 1,900 new rows, `i=0..1899`:

```text
property_id = 'P' + six-digit(100001 + i)
customer_id = replace first 'P' with 'C'
seed(channel,id) = integer(SHA256('20261011:' + channel + ':' + id), base 16)
channel = 'physical' or 'price'
```

Each stream uses Python `random.Random`. Pricing uses a separate stream; changing
the EPC letter alone cannot create a price premium. Physical and price values
still share area, bedroom and age characteristics; statistical correlation is
not causal evidence. The stable ID scheme prevents reuse of previously exposed
v2 IDs. Increasing the total preserves the existing generated prefix with the
same runtime/reference snapshot. A separate fixed pilot uses `PILOT00000`–
`PILOT02999`, disjoint from every development/calibration/test property.

### 4.2 Types, age, floor area and categorical characteristics

London accommodation weights use counts: Detached **208,078**, Semi-detached
**636,084**, Terraced **727,673**, Flat **1,847,649**, normalised over these four.
Flats include maisonettes/apartments and houses include bungalows within the
existing type vocabulary. Build-year bands are:

| Build years | Probability |
|---|---:|
| 1850–1918 | 0.276 |
| 1919–1944 | 0.223 |
| 1945–1964 | 0.128 |
| 1965–1980 | 0.146 |
| 1981–1990 | 0.029 |
| 1991–2002 | 0.078 |
| 2003–2021 | 0.120 |

Choose a band, draw an inclusive uniform integer year inside it, then
`age = 2026 - build_year`. The pre-1919 lower bound of 1850 and uniform
within-band distribution are assumptions; post-2021 construction is not invented.
For the recent band `P(Flat)=0.867`; for other bands:

```text
f = Flat_count / sum(four supported type counts)
P(Flat | older) = (f - 0.12 * 0.867) / 0.88
P(non-flat kind | non-flat) proportional to its published count
```

Conditional area means `mu_type` are 128 Detached, 101 Semi-detached, 86 Terraced
and 63 Flat. Their numerical values and conditional variance remain assumptions:

```text
A = round(clip(mu_type * exp(N(-0.5 * 0.30^2, 0.30)), 25, 350), 1)
```

| Characteristic | Exact new-row rule |
|---|---|
| Bedrooms | A<55: 1/2 with weights .8/.2; 55<=A<90: 2/3 with .8/.2; 90<=A<140: 3/4 with .75/.25; A>=140: 4/5/6 with .65/.30/.05. |
| Insulation Poor/Average/Good | age<=26: .01/.04/.95; 27–81: .30/.50/.20; age>81: .50/.35/.15. |
| Glazing Single/Double/Triple | age<=26: .005/.845/.15; 27–59: .08/.87/.05; age>=60: .25/.72/.03. |
| Heating | P(electric)=.06; conditional electric: pump/resistance .4/.6. Otherwise old/modern gas: age<=26 .02/.98; 27–59 .2/.8; age>=60 .45/.55. These are assumptions, not London fuel-prevalence estimates. |
| Solar installed | Bernoulli probability .18 Detached, .12 Semi-detached, .08 Terraced, .02 Flat. |
| Smart controls | Bernoulli probability .85 if pump; otherwise .5 if age<=26, else .3. |
| Region | `Greater London` for every new row. |

### 4.3 Synthetic EPC label

The latent score is:

```text
L = 50 + insulation_bonus + glazing_bonus + heating_bonus
    + 8*solar + 4*smart_controls + 5*1(age<=26) + N(0,5)
insulation: Poor -12, Average +8, Good +20
glazing: Single -10, Double +5, Triple +10
heating: old gas -8, modern gas +3, pump +12, resistance -5
```

Sum the official London 2025 EB1 rating counts. On the 3,000-home pilot, sort
latent scores. For each cumulative rating count in order **G,F,E,D,C,B**, choose
the pilot cutoff at index `min(2999, round(3000*cumulative_count/total_count))`.
The six ascending thresholds are recorded in `parameters.json`:
14.2373884067, 18.5522113097, 28.0040395537, 50.9180391488,
86.3459897315 and 104.0883477129.

```text
energy_rating = 'GFEDCBA'[bisect_right(cutoffs, L)]
```

Equality moves to the higher label. This maps a modelled physical ordering to
certificate-lodgement marginals. It is **not SAP calculation, an actual EPC or
evidence of stock-wide rating proportions**. `energy_rating` is not a feature
in the baseline snapshot valuation evaluator.

### 4.4 Synthetic valuation target: no retrofit uplift

Choose a latent borough uniformly from sorted boroughs with a positive HPI
price for the property's type. Equal borough weights are an assumption, not
household/transaction weights. Let `P_b,t` be that borough/type's July 2026 HPI
anchor and `sigma_p=.18`, unchanged from the original price generator:

```text
raw_price = P_b,t * (A/mu_type)^0.55
            * (1 + 0.02*(b-3))
            * (1.04 if age<=10 else 1)
            * exp(N(-0.5*sigma_p^2, sigma_p))
j_type = public_London_type_HPI_mean / mean(pilot raw_price for that type)
current_value_estimate_gbp = 1000 * round(max(50000, raw_price*j_type)/1000)
```

Published London type anchors are GBP 1,167,718 Detached, 724,106 Semi-detached,
642,452 Terraced and 424,013 Flat. Pilot intercepts are approximately .760147107,
.722832429, .847460528 and .997134979 respectively; exact values are in the report.
Intercept normalisation uses public references and the independent pilot,
never held-out valuation errors. It does not force the finite final cohort's
type means to equal the public means exactly.

**No EPC, fabric, heating, controls, solar, retrofit cost, savings or uplift
formula enters this target.** Noise was not reduced to improve reported MAE.
Labels are simulated baseline estimates, not matched observed transaction
prices. Latent borough variation is withheld from the unchanged ML inputs,
leaving irreducible synthetic uncertainty. The dataset cannot train or establish
a causal retrofit-value premium.

### 4.5 Retained legacy cohort and v2 history

The first ten legacy properties are curated fixed synthetic demonstrations;
their values are copied from the canonical source, not re-labelled as observed.
The other ninety use `generate_properties.generate_base(..., seed=42)`:
types have fixed additional counts 17 Detached/26 Semi/26 Terraced/21 Flat,
shuffled alongside regions so the original dataset has ten homes per region.
Five of the ninety are electric (two pumps, three resistance); others are gas.

Legacy areas are clipped normal draws `(mean,sd,low,high)`:
Detached `(128,19,65,240)`, Semi `(101,18,51,200)`, Terraced `(86,16,45,170)`,
Flat `(63,16,30,130)`. Legacy ages are rounded normals with SD 34, clipped 1–180,
and type means 52/60/82/38. Below 55 m2 the bedroom weights are .75/.25;
90–139 m2 uses .8/.2; other bedroom bands match v3. Legacy insulation additionally
uses .10/.45/.45 at ages 27–39, then .30/.50/.20 at 40–81. Other categorical
weights match the rules above apart from the fixed electric allocation.
Legacy EPC uses the same latent expression but fixed thresholds
85 A, 75 B, 65 C, 50 D, 35 E, 20 F, otherwise G.

```text
legacy raw_price = region_anchor * (national_type_anchor/272611)
                   * (A/mu_type)^0.55 * (1+.02*(b-3))
                   * (1.04 if age<=10 else 1) * exp(N(-.5*.18^2,.18))
legacy target = 1000*round(max(50000, legacy raw_price)/1000)
```

| Region | Inherited synthetic price anchor GBP |
|---|---:|
| Greater London | 550037 |
| South East | 380878 |
| South West | 302298 |
| East of England | 337518 |
| West Midlands | 250880 |
| East Midlands | 242274 |
| North West | 221445 |
| North East | 166943 |
| Yorkshire and The Humber | 209116 |
| Wales | 215037 |

National type anchors are 444936/278555/231945/192704 for Detached/Semi/Terraced/Flat.
These inherited assumptions are not newly matched observations. Legacy energy
uses the physical model below with `k_h=k_e=1`; its benchmark uses the original
fixed reference with climate 1.0. The unchanged first hundred retain all original
physical/provenance strings, including a missing `P3_HANDOFF.md` reference disclosed
by the audit. V2 appended independently seeded batches of ninety using seeds
43,44,...; it is archived rather than mixed into the new fresh evaluation cohort.

## 5. Energy, annual components and benchmark formulas

### 5.1 Physical model before monthly allocation

The energy RNG seed is the big-endian integer from the **first eight bytes** of
`SHA256('42:'+property_id)`, distinct from the property/price seed. Draw household
behaviour `u~U(.90,1.10)`; draw heat-profile and appliance-profile multipliers
independently from `U(.95,1.05)` for each of twelve months, in that order.
For 2025, `a25=max(0,a-1)` and:

```text
H0 = A*65 * fabric_factor * glazing_factor * (1+.0015*min(a25,120))
     * dwelling_factor * climate_factor * controls_factor * u
W = (600+350*o)*u
B0 = (800+500*o+A)*u
PV_capacity = clip(.025*A,2,5)                  # assumed kWp when installed
V = PV_capacity*regional_yield if solar else 0 # kWh/year
```

| Factor | Values |
|---|---|
| Fabric | Poor 1.30; Average 1.00; Good .75 |
| Glazing | Single 1.15; Double 1.00; Triple .90 |
| Dwelling | Detached 1.10; Semi .95; Terraced .85; Flat .70 |
| Controls | .94 when present, otherwise 1.0 |
| Boiler | Old .72; modern .90 |
| Pump | Space-heating COP 3.0; hot-water COP 2.5; gas zero |
| Resistance | Efficiency 1.0; gas zero |

| Region | Climate multiplier | PV yield kWh/kWp/year |
|---|---:|---:|
| Greater London | .95 | 950 |
| South East | .97 | 980 |
| South West | .95 | 1000 |
| East of England | 1.00 | 950 |
| West Midlands | 1.04 | 900 |
| East Midlands | 1.05 | 900 |
| North West | 1.08 | 850 |
| North East | 1.12 | 850 |
| Yorkshire and The Humber | 1.10 | 870 |
| Wales | 1.06 | 880 |

All factors, occupancy inference, system performance, PV capacity and behavioural
noise are modelling assumptions. They are not surveyed or site-specific designs.

### 5.2 Seasonal allocation, fuel conversion and PV accounting

Raw January–December profiles are:

```text
heat = [.17,.145,.12,.08,.04,.015,.005,.005,.035,.085,.13,.17]
appliances = [.095,.085,.085,.08,.08,.075,.075,.075,.08,.085,.09,.095]
solar = [.025,.04,.075,.10,.125,.135,.135,.115,.09,.065,.035,.025]
```

Normalise each vector to sum to one. Apply the per-month jitter before normalising
heat/appliances; solar has no jitter. Then:

```text
H_m = k_h*H0*normalised_heat_m
W_m = W/12
B_m = k_e*B0*normalised_appliance_m
V_m = V*normalised_solar_m

gas home:        G_m=(H_m+W_m)/eta; D_m=B_m
pump home:       G_m=0; D_m=B_m+H_m/3+W_m/2.5
resistance home: G_m=0; D_m=B_m+H_m+W_m

S_m=min(D_m, .45*V_m)
I_m=max(0,D_m-S_m)
X_m=V_m-S_m
```

The implementation first generates six-decimal raw physical monthly values,
then rescales heat/base appliances and recomputes fuel/PV balances; this rounding
order matters for exact reproduction. PV reduces purchased electricity, not
the underlying electrical demand or gas. Export receives no invented revenue.

### 5.3 Pilot calibration, separate from valuation calibration

On the disjoint fixed 3,000-home pilot, use **35 bisection iterations** within
`[.1,5]` to solve for `k_h` so median annual purchased gas among gas homes matches
London NEED 2024's **10,817.37253845012 kWh**. With that heat scale fixed, solve
for `k_e` so median annual grid imports across all pilot homes match
**2,466.300000126385 kWh**. The electricity calculation respects PV clipping and
electric heating. Hot-water demand, COPs, efficiency and behavioural noise are
not rescaled to improve valuation accuracy.

Recorded scales: `k_h=1.9030779568522123`, `k_e=1.2586991921489243`.
The pilot also determines EPC quantiles and price intercepts. No final-cohort
valuation errors enter these calculations. Matching two energy medians does
not verify variance, tails, heating prevalence, temporal behaviour or joint realism.

### 5.4 Annual aggregation and fixed benchmark

Annual H/W/D/V/S fields sum their twelve physical monthly columns. Gas-space and
gas-water fields divide annual delivered H/W by applicable `eta`; electric
space/water fields divide them by applicable COP/efficiency. Nonapplicable fuel
components are zero. Base appliance electricity equals annual D minus electric
space and water components. Purchased annual gas/grid, when loaded by the
backend, sum the **two-decimal import readings**, not six-decimal demand fields.
Incomplete fuel coverage yields an unavailable annual import total.

For each new-row benchmark, evaluate a fixed synthetic home of the same type:
100 m2, age 54 (53 during energy year), 3 assumed occupants, average insulation,
double glazing, modern gas boiler .90, no PV/controls, London climate .95,
behaviour 1, and the v3 scales. Its purchased-energy intensity is:

```text
benchmark = ((k_h*H0_reference + W_reference)/.90 + k_e*B0_reference)/100
```

This is a modelled reference, **not an official NEED efficiency threshold**.
Legacy benchmark metadata/values remain unchanged. Renewable share is
`annual S / annual D` (zero when demand is zero). Contribution is `none` for
zero PV generation, otherwise `substantial` at share>=.20 and `limited` below.
This category concerns electrical PV contribution, not the share of all heat.

## 6. Complete property-field dictionary: 51 columns, in CSV order

The following rules describe **new v3 rows**; original hundred are copied with
their original values/provenance as described in section 4.5.

| # | Field | Meaning, unit and source/formula |
|---:|---|---|
| 1 | `property_id` | Stable synthetic identifier P100001 onward; section 4.1. Not UPRN. |
| 2 | `customer_id` | Stable synthetic customer/group ID C100001 onward; one per new property. |
| 3 | `property_type` | Detached/Semi-detached/Terraced/Flat; source-weighted draw in 4.2. |
| 4 | `age` | Years: 2026 minus sampled build year. Not surveyed or dated at sale. |
| 5 | `floor_area_m2` | m2; type-conditional clipped lognormal, section 4.2. |
| 6 | `bedrooms` | Integer, area-conditional categorical draw, section 4.2. |
| 7 | `energy_rating` | Synthetic A–G label; latent score and pilot EPC quantiles, section 4.3. |
| 8 | `heating` | Human-readable synthetic system category from 4.2. |
| 9 | `insulation` | Poor/Average/Good age-conditional assumption, 4.2. |
| 10 | `glazing` | Single/Double/Triple age-conditional assumption, 4.2. |
| 11 | `solar` | Boolean text from type-conditional Bernoulli draw; not roof evidence. |
| 12 | `smart_controls` | Boolean text from heating/age-conditional draw. |
| 13 | `region` | Greater London for new rows; legacy ten-region vocabulary retained. |
| 14 | `current_value_estimate_gbp` | Synthetic GBP target from HPI/size/bedroom/age/noise formula, 4.4. Never a model input. |
| 15 | `data_status` | Literal `synthetic`; cannot be promoted to observed because references are public. |
| 16 | `generation_seed` | Property/price root seed 20261011; legacy seed 42. |
| 17 | `heating_system` | Maps old/modern gas to `old_gas_boiler`/`modern_gas_boiler`, pump to assumed `air_source_heat_pump`, resistance to `electric_resistance`. |
| 18 | `heating_system_status` | `synthetic_assumption` for pump subtype, otherwise `derived_from_synthetic`. |
| 19 | `renewable_contribution` | none/limited/substantial from PV generation and share rule, 5.4. |
| 20 | `renewable_share` | Dimensionless annual S/annual D; nine decimals, zero if D=0. |
| 21 | `annual_electricity_demand_kwh` | kWh/year; sum D_m, including electrical heat, before PV offset. |
| 22 | `annual_solar_generation_kwh` | kWh/year; sum V_m, not net imports. |
| 23 | `annual_solar_self_consumed_kwh` | kWh/year; sum S_m, bounded by generation and demand. |
| 24 | `benchmark_property_type` | Existing lowercase/underscore type name: detached/semi_detached/terraced/flat. |
| 25 | `benchmark_intensity_kwh_m2_year` | Purchased kWh/m2/year for the fixed v3 reference, 5.4. |
| 26 | `benchmark_source` | Declares synthetic London v3/NEED-2024 anchor and nonofficial benchmark status. |
| 27 | `benchmark_methodology` | Records fixed dimensions, performance, climate, behaviour, scales and PV/subtype assumptions. |
| 28 | `benchmark_source_year` | Existing benchmark metadata year 2025; reference scenario year, not NEED publication year. |
| 29 | `benchmark_data_status` | `synthetic`; retained type metadata. |
| 30 | `annual_space_heating_demand_kwh` | kWh/year delivered space heat; sum H_m. |
| 31 | `annual_hot_water_demand_kwh` | kWh/year delivered hot water; sum W_m. |
| 32 | `thermal_demand_kwh` | kWh/year delivered heat; annual H + annual W. Not fuel purchased. |
| 33 | `thermal_demand_scope` | `space_heating_plus_hot_water`. |
| 34 | `annual_base_appliance_electricity_kwh` | kWh/year; annual D minus annual electric-space and electric-water components. |
| 35 | `annual_gas_space_heating_kwh` | kWh/year fuel: annual H/eta for gas homes, else zero. |
| 36 | `annual_gas_hot_water_kwh` | kWh/year fuel: annual W/eta for gas homes, else zero. |
| 37 | `annual_electric_space_heating_kwh` | kWh/year electricity: H/3 for pump, H/1 for resistance, else zero. |
| 38 | `annual_electric_hot_water_kwh` | kWh/year electricity: W/2.5 for pump, W/1 for resistance, else zero. |
| 39 | `boiler_efficiency` | Dimensionless .72 old/.90 modern; blank for electric systems. |
| 40 | `scop` | Dimensionless assumed seasonal space COP 3.0 for pump; blank otherwise. |
| 41 | `hot_water_cop` | Dimensionless hot-water COP 2.5 for pump; blank otherwise. |
| 42 | `electric_resistance_efficiency` | Dimensionless 1.0 for resistance; blank otherwise. |
| 43 | `solar_installed` | Copies `solar`, enabling a cross-field consistency check. |
| 44 | `roof_suitable_for_loft` | Blank: no surveyed feasibility evidence. |
| 45 | `roof_suitable_for_solar` | Blank: no surveyed feasibility evidence. |
| 46 | `heat_pump_compatible` | Blank: no surveyed feasibility evidence. |
| 47 | `controls_compatible` | Blank: no surveyed feasibility evidence. |
| 48 | `physical_inputs_status` | `synthetic_modelled`. |
| 49 | `physical_inputs_source` | v3 simulation script/methodology pointer, explicitly not measured. |
| 50 | `physical_inputs_year` | 2025: simulated energy calendar year. |
| 51 | `physical_inputs_generation_seed` | 42: per-property energy RNG root; distinct from property/price seed. |

## 7. Complete monthly energy-field dictionary: 13 columns

| # | Field | Meaning, unit and source/formula |
|---:|---|---|
| 1 | `property_id` | Exact parent synthetic ID; foreign-key join only. |
| 2 | `month` | `2025-01` through `2025-12`; one row per property/month. |
| 3 | `electricity_kwh` | Purchased monthly grid I_m=D_m-S_m; two decimals. Genuine zero allowed. |
| 4 | `gas_kwh` | Purchased monthly gas G_m; zero for electric systems; two decimals. |
| 5 | `reading_status` | `synthetic` in main dataset; `missing` only when explicitly altered in QA. |
| 6 | `electricity_demand_kwh` | Monthly D_m before PV offset; six decimals. |
| 7 | `solar_generation_kwh` | Monthly V_m from installed capacity/yield/profile; six decimals. |
| 8 | `solar_self_consumed_kwh` | Monthly S_m=min(D_m,.45*V_m); six decimals. |
| 9 | `solar_export_kwh` | Monthly X_m=V_m-S_m; six decimals. |
| 10 | `space_heating_demand_kwh` | Monthly delivered H_m; six decimals. |
| 11 | `hot_water_demand_kwh` | Monthly delivered W_m=W/12; six decimals. |
| 12 | `physical_inputs_status` | `synthetic_modelled`; no meter evidence implied. |
| 13 | `reading_source` | New rows declare `simulate_london.py v3`, NEED-2024 anchoring and nonobserved scenario status; legacy strings retained. |

Annual purchased totals require all twelve valid months for each fuel. The
backend excludes readings labelled missing and does not annualise partial
coverage by extrapolation. Physical demand fields and net purchased fuel are
separate quantities; adding PV generation to demand would double-count it.

## 8. Complete emission-factor dictionary: 10 columns

| # | Field | Meaning and provenance |
|---:|---|---|
| 1 | `fuel` | `electricity` or `gas`; lookup key, not a property label. |
| 2 | `kg_co2e_per_kwh` | Published multiplier: electricity .13096; gas .18231, kg CO2e per purchased kWh. |
| 3 | `source` | Official DESNZ 2026 publication URL. |
| 4 | `source_year` | 2026; differs from simulated energy year 2025. |
| 5 | `accounting_boundary` | Electricity: Scope 2 location-based UK generation, excludes T&D/WTT. Gas: Scope 1 natural-gas combustion, gross calorific value, excludes WTT. |
| 6 | `version` | `DESNZ-2026-flat-revised-2026-07-31`. |
| 7 | `source_row_id` | Electricity `7_400_4000_5_1`; gas `1_100_1004_6_1`; exact workbook factor identifiers. |
| 8 | `units` | `kg CO2e/kWh`. |
| 9 | `source_sheet` | Workbook XML worksheet `xl/worksheets/sheet2.xml`. |
| 10 | `source_excel_row` | Electricity 3066; gas 83. |

```text
operational kg CO2e = annual purchased electricity*.13096
                     + annual purchased gas*.18231
operational tonnes CO2e = kg CO2e/1000
```

This is an optional scenario calculation, not a new CSV/valuation target. No
export credit, tariff-derived savings, lifecycle manufacturing/installation
emissions or causal retrofit effect is inferred. If a required annual fuel is
unavailable, a complete combined emissions estimate is unavailable.
The provenance JSON records publication/download, licence, source workbook
SHA-256, the two extracted rows and limits. Workbook hash:
`a9a455ab396dae226d510c7be6233748416d490c41a5d20f3dc7a0c45feecd5e`.

## 9. Diagnostic transformations: not new ML inputs

| Sidecar field | Derivation |
|---|---|
| `property_id` | Existing identifier; joins diagnostics to their parent. |
| `purchased_energy_intensity_kwh_m2_year` | sum_m(I_m+G_m)/A only if twelve distinct expected 2025 months have nonmissing purchased readings and A>0; otherwise null. Zero valid consumption produces zero intensity. |
| `log_floor_area` | Natural logarithm ln(A) when A>0, otherwise null. |
| `floor_area_band` | A<55; 55<=A<90; 90<=A<140; A>=140, labelled `<55`, `55-89`, `90-139`, `140+`; missing area -> null. |
| `age_band` | age<=26, 27–59, 60–81, >81; missing age -> null. |
| `energy_year` | 2025 only when purchased readings satisfy completeness; otherwise null. |
| `region` | Existing region, or null if unavailable. |

Latent-provenance `latent_borough` is a generated location draw; `source_kind`
explicitly states synthetic/nonmatched status; `split` copies the stable
customer reservation. No target encoding is performed. Price-band diagnostics
in evaluation use the target only to group errors, never to predict it.

## 10. Measured quality, missingness and known biases

From [quality_report.json](reports/kew_london_v3/quality_report.json):

| Check | Recorded finding |
|---|---|
| Size/schema | 2,000 properties / 24,000 monthly rows; 51/13 ordered fields. |
| Provenance | 2,000 synthetic properties; 2,000 synthetic-modelled physical records. |
| Coverage | All main properties have January–December 2025; no missing main meter cells. |
| Duplicates/joins | Zero duplicate property IDs or property-months; no unmatched energy IDs or homes without meters. |
| Eligibility | All 2,000 values blank for each of four feasibility columns; deliberately unknown. |
| Nonapplicable performance | Boiler efficiency blank in 113 electric homes; SCOP/hot-water COP blank in 1,951 non-pump homes; resistance efficiency blank in 1,936 non-resistance homes. |
| Preservation | Original 100 properties/1,200 readings match source cells exactly. |
| Audit errors | None in the main cohort. This is internal integrity, not real-world accuracy. |

New-row types: **115 Detached, 346 Semi-detached, 447 Terraced, 992 Flat**.
New mean area is **78.93 m2**. New median purchased electricity is **2,463.60 kWh**
versus NEED London's **2,466.30**; gas-heated median is **10,787.22 kWh** versus
**10,817.37**. Finite-sample marginals need not match source weights exactly.
The complete cohort additionally contains the geographically mixed legacy rows.

Numeric ranges, categorical counts and engineering outlier IDs are retained in
the JSON report. Outlier flags use area<25 or >300 m2, age>200, or delivered
thermal intensity>400 kWh/m2/year; they are review flags, not empirical price
validation or automatic deletion. Source generation itself clips new areas to
25–350; therefore a >300 flag can be a valid deliberately retained large home.

Material limits: certificate-lodgement bias/repeat certificates; unmatched
source populations and years; assumed within-type sizes and equipment mix;
uniform latent borough weights; inferred occupancy; no weather/site survey;
no imported SmartMeter seasonal calibration; no observed transaction labels;
no assessed eligibility/cost/tariff data; inherited broken handoff pointer.
Schema/physical consistency cannot establish representativeness, correct
individual market value, actual savings or causal retrofit premiums.

## 11. Validation methodology and edge fixtures

The generator calls `generate_energy_usage.validate()` and `expand_dataset.audit()`
before publishing the main files. They check exact headers, unique IDs/months,
foreign keys, calendar coverage, synthetic status, finite/nonnegative numeric
values, positive area, accepted booleans, heating/subtype agreement, solar flag
agreement, zero gas for electric systems, and consistency of physical components.

| Identity checked | Absolute tolerance |
|---|---:|
| I_m+S_m=D_m; fuel vs delivered heat after efficiency | .011 kWh per month |
| S_m+X_m=V_m | .00001 kWh |
| Annual H/W/D/V/S vs monthly physical sums | .00003 kWh |
| H+W=thermal; component efficiency/COP products | .00001 thermal sum; .00003 efficiency products |
| Annual base + electric space + electric water = annual D | .00003 kWh |
| Annual gas components vs sum purchased gas | .08 kWh, allowing twelve two-decimal rounding errors |
| PV share vs annual S/D | .00000001 dimensionless |

Controlled comparisons in the existing energy validator check poor vs good
insulation, single vs triple glazing, PV reducing grid imports without changing
demand/gas, pump fuel/COP behaviour, larger homes' consumption/intensity and
winter vs summer heating. These compare the **underlying model**; v3's complete
rescaled rows additionally undergo the balance audit. They are not comparisons
with measured households or proof of realised savings.

The 60 isolated QA fixtures cycle through ten cases, six examples each:
missing month; missing purchased reading; genuine zero gas in an electric home;
zero all consumption; conflicting heating subtype; conflicting solar flag;
explicitly infeasible solar; explicitly infeasible pump; unknown floor area;
missing thermal inputs. They use the existing headers. Missing/invalid cases
are intentionally outside the valid main contract and must yield rejection,
unavailable quantities or eligibility gating. Fixture contradictions are not
silently repaired; the missing-thermal fixture deliberately leaves other source
components intact to exercise incomplete/conflicting-input behaviour.

**29 relevant tests passed** across `Data/tests`, `backend/tests/test_dataset.py`
and `ml/tests/test_snapshot.py`. Tests cover source/schema preservation,
determinism and stable prefixes, corrupted physical balance detection, fresh
customer reservation, missing-versus-zero diagnostics, backend loading/scoring,
ML snapshot validation and the final-evaluation guard. All 2,000 full records
were also loaded through the existing backend, produced available scores and
passed the unchanged ML snapshot validator. The local API test ran outside the
network-restricted sandbox and emitted one upstream TestClient deprecation
warning. These are recorded completed checks, not tests rerun by this README.

## 12. Leakage controls, model selection and independent calibration

The original hundred are `legacy_diagnostic`, excluded from all new model
partitions. New customer reservation is independent of targets:

```text
u = int(first 16 hex digits of SHA256('kew_london_v3:reserve:'+customer_id))/2^64
u < .40 -> fit
.40 <= u < .60 -> selection
.60 <= u < .80 -> calibration
u >= .80 -> test
```

Actual counts: **803 fit, 334 selection, 381 calibration, 382 test**, plus
100 legacy diagnostics. Every property/customer's records share a split.
Evaluation validates manifest uniqueness and one-to-one ID/customer joins and
rejects customer overlap. There is no chronological evaluation because no
observed transaction/snapshot dates exist. New IDs do not reuse exposed v2 rows.

The evaluator uses only **floor_area, bedrooms, age, region, property_type**,
with the existing `floor_area_m2` -> `floor_area` alias. It excludes the target,
EPC letter, energy fields, future assessments, derived price proxies, bands and
latent borough. Existing preprocessing median-imputes/scales numeric features
and one-hot encodes categories with unknown-category handling inside each fitted
pipeline. The main numeric inputs are complete, so imputation is not a mechanism
for fabricating missing source data. No full-dataset target encoding occurs.

Existing candidates: Ridge(alpha=10) and HistGradientBoosting(max_iter=120,
max_leaf_nodes=15, l2_regularization=10, random_state=42, early_stopping=False).
Choose boosting only if its selection MAE is <.98 times Ridge selection MAE;
otherwise Ridge. The selected candidate is refitted on fit+selection; calibration
and test labels remain excluded. Five grouped fit-only folds at sizes
100/250/500/803 provide the learning curve. These curves are development
diagnostics conditional on selection; not independent held-out market evidence.

Valuation calibration is distinct from section 5.3's physical pilot. For the
381 independent calibration customers with prediction `p_i` and target `y_i`:

```text
absolute residual r_i = abs(y_i-p_i)
relative residual z_i = r_i/max(50000,p_i)
alpha=.1; n=381
k=ceil((n+1)*(1-alpha))=344
q = sorted residual[k-1]                      # finite-sample order statistic
price-proportional interval: p +/- q_relative*max(50000,p)
constant-width comparator: p +/- q_absolute
```

The evaluator reports symmetric intervals without clipping negative endpoints.
Price-proportional scaling was declared before test evaluation; the comparator
is not selected using test coverage. Exchangeability supports marginal
synthetic coverage, not guaranteed subgroup coverage, future market coverage
or causal effects. Production model artifacts/inference code are unchanged.
The existing production trainer does not automatically consume this manifest;
Person 5 must explicitly adopt it before using these holdout assignments.

## 13. Reported metrics and interpretation

For targets `y`, predictions `p`, count `n`:

```text
MAE = sum(abs(y-p))/n                         # GBP
RMSE = sqrt(sum((y-p)^2)/n)                   # GBP
R2 = 1 - sum((y-p)^2)/sum((y-mean(y))^2)      # dimensionless; null for one row
coverage = count(abs(y-p)<=interval_half_width)/n
mean interval width = mean(2*interval_half_width)
```

Error breakdowns use region, property type, area bins `[0,55),[55,90),[90,140),
[140,infinity)` and target-price bins below GBP 300k, 300–500k, 500–750k,
750k–1m, and >=1m. These are **reporting groups**, not inputs. Coverage reports
overall and type-specific counts. Small subgroups yield less reliable estimates;
no subgroup significance claim or real-market confidence bound is reported.

| Frozen v3 result | Recorded value |
|---|---:|
| Selected development candidate | Ridge |
| Selection MAE | GBP 209,002.43 |
| Fresh test count | 382 |
| Fresh test MAE | GBP 210,233.97 |
| Fresh test RMSE | GBP 318,059.17 |
| Fresh test R2 | .242747 |
| Nominal price-proportional interval coverage | 90% |
| Actual price-proportional coverage | 89.53% |
| Mean price-proportional interval width | GBP 701,118.46 |
| Constant-width comparator coverage | 91.36% |
| Mean constant-width interval width | GBP 873,793.60 |

Price-proportional type coverage: Detached 88.0% (25), Flat 87.98% (208),
Semi-detached 92.42% (66), Terraced 91.57% (83). The constant-width comparator
covered only 60% of detached test labels despite its higher overall coverage.
Large absolute errors cluster in detached/expensive homes. Fit-only learning
curves did not show consistent improvement from 250 to 803 examples; additional
rows do not recover unobserved borough information under the unchanged features.

The final test was evaluated **once after freezing** generation/model/calibration
choices. No parameters were tuned after inspecting it. It is now exposed: further
development needs another independently reserved version/cohort. The earlier
quoted 85% run is not a comparable benchmark without its exact dataset, split
and model version. Synthetic metrics measure agreement with the generator;
large interval width and remaining errors preclude claims of accurate individual
market valuation. Baseline valuation and retrofit-value uplift remain separate.

## 14. Reproducibility: commands, fingerprints and evaluation guard

Use the reviewed reference JSON for offline generation; raw downloads are not
required. Python 3.10+ and the standard library suffice for simulation. The
recorded byte-identical reproduction used **Python 3.10.11**; other Python
versions can produce small floating-point differences. Existing backend/ML
requirements are needed for evaluation/tests; package ranges alone do not fix
all versions, so record the runtime and resolved packages when reproducing.

From the repository root in PowerShell:

```powershell
python -m venv .venv
.venv/Scripts/python.exe -m pip install -r backend/requirements.txt -r ml/requirements.txt
.venv/Scripts/python.exe Data/scripts/simulate_london.py --total 2000 --handoff
$env:OMP_NUM_THREADS='1'
$env:OPENBLAS_NUM_THREADS='1'
.venv/Scripts/python.exe Data/scripts/evaluate_london.py
.venv/Scripts/python.exe -m pytest Data/tests backend/tests/test_dataset.py ml/tests/test_snapshot.py -q
.venv/Scripts/python.exe -m pip freeze
```

Default evaluation generates development/calibration diagnostics without scoring
the test partition. The delivered test was already evaluated; **do not append
`--final` again** or delete its marker. If ignored generated files were removed,
restore the archived guard after reproducing:

```powershell
Copy-Item -LiteralPath Data/reports/kew_london_v3/FINAL_EVALUATION.json -Destination Data/generated/kew_london_v3/FINAL_EVALUATION.json
```

The guard is file-based; deleting it or recreating the directory can bypass it.
The archive and this policy are therefore essential: recreating exposed labels
does not make them a fresh test set. On a genuinely new version/cohort, reserve
new customers and freeze choices before a one-time `--final` evaluation.

To retrieve/re-extract references, use network access for
`scripts/fetch_london_references.py`, then a Python environment with read-only
`openpyxl` for `scripts/prepare_london_references.py`. The bundled workspace Python
provides this reader. The HPI CSV is approximately 16 MB, EPC 1.9 MB, NEED .55 MB;
raw files remain ignored. Extraction checks London codes, quarter completeness
and NEED worksheet layout. Compare recorded SHA-256 hashes before accepting any
public-source revision. Do not silently replace the reviewed reference snapshot.

`provenance.json` fingerprints source CSVs, factors/provenance, reference snapshot,
schema, generator and helper scripts, and generated outputs existing when the
manifest was written. Final evaluation separately records data/manifest/evaluator
hashes and a frozen-configuration hash. Its marker is created afterwards, so it
is archived separately rather than assumed covered by the earlier output manifest.
SHA-256 authenticates byte identity, not source correctness or statistical quality.

Completed reproduction checks: same-runtime full regeneration was byte-identical;
all recorded output checksums verified; original source cells preserved; 29
relevant tests passed; full 2,000-row backend/ML compatibility verified. This
README documents those results without rerunning the exposed final evaluation.

## 15. What a reviewer can and cannot conclude

Review data lineage, generator assumptions, explicit missingness, label formulas,
physical identities, split independence, interval widths and subgroup errors
alongside headline scores. The dataset demonstrates a reproducible, internally
consistent, public-reference simulation under the unchanged schema. It does not
prove current London representativeness, trustworthy observed price labels,
real-property EPC accuracy, surveyed retrofit feasibility, real bills/savings,
market-calibrated intervals or causal retrofit premiums. Obtaining those claims
requires appropriately licensed observed records, verified keys/dates, survey
evidence, and a new independent validation design.

Implementation sources: [simulate_london.py](scripts/simulate_london.py),
[generate_energy_usage.py](scripts/generate_energy_usage.py),
[expand_dataset.py](scripts/expand_dataset.py),
[evaluate_london.py](scripts/evaluate_london.py),
[reference extraction](scripts/prepare_london_references.py), and
[legacy generator](scripts/generate_properties.py).
