# Synthetic monthly energy methodology

## Output and provenance

energy_usage.csv contains 1,200 rows: 100 existing properties × 12 months, January–December 2025. The exact columns are property_id, month, electricity_kwh, gas_kwh, reading_status. Each property_id matches properties.csv exactly. electricity_kwh means grid electricity imported/purchased, after solar self-consumption; gas_kwh means gas fuel purchased. Units are monthly kWh, rounded to two decimal places. Every reading_status is synthetic. These are generated scenarios, not real meter readings or predictions validated against households.

The 2026 property snapshot is assumed to apply throughout the 2025 scenario, with age reduced by one year, floored at zero. Retrofit dates and historical property condition are unknown. 2025 was chosen to represent a complete past calendar year; there is no claim of actual historical observation.

## Reference and calibration scope

[DESNZ NEED 2026 report](https://www.gov.uk/government/statistics/national-energy-efficiency-data-framework-need-report-summary-of-analysis-2026/national-energy-efficiency-data-framework-need-report-summary-of-analysis-2026-accessible-webpage), published 11 June 2026 and reviewed 10 October 2026, reports 2024 England/Wales median annual gas of 10,000 kWh and electricity of 2,500 kWh. Those statistics guide the rough scale, not individual readings. The synthetic dataset gives medians of 9,077 kWh for gas-heated homes and 2,322 kWh grid electricity across all homes. The samples, periods and definitions differ; this is a plausibility comparison, not a fitted or representative population model. NEED also supports qualitative size/efficiency relationships. Source licence: Open Government Licence v3.0, subject to exceptions. No source household rows were downloaded or copied.

## Generation rules: all numerical parameters below are modelling assumptions

Seed 42. Each home's random generator uses the first eight bytes of SHA256 of the string `42:property_id`, interpreted as a big-endian integer. This makes existing readings stable when property order changes or new properties are added. Household behaviour is a per-property uniform multiplier from 0.90 to 1.10. The same multiplier scales space heating, hot water and appliances. Noise is seeded, not arbitrary per-fuel energy assignment.

Annual delivered space-heating demand = floor_area_m2 × 65 kWh/m² × insulation factor × glazing factor × age factor × dwelling factor × regional climate factor × controls factor × behaviour.

| Driver | Factor |
|---|---|
| Insulation | Poor 1.30; Average 1.00; Good 0.75 |
| Glazing | Single 1.15; Double 1.00; Triple 0.90 |
| Age | 1 + 0.0015 × min(age in scenario year, 120) |
| Dwelling | Detached 1.10; Semi-detached 0.95; Terraced 0.85; Flat 0.70 |
| Smart controls | 0.94 if present; otherwise 1.00 |

Regional climate factors: Greater London .95; South East .97; South West .95; East of England 1.00; West Midlands 1.04; East Midlands 1.05; North West 1.08; North East 1.12; Yorkshire and The Humber 1.10; Wales 1.06. These are illustrative multipliers, not measured weather or published regional degree-days.

Assumed occupants = bedrooms, floored at one and capped at five. This is an unobserved occupancy proxy, not a new property field. Delivered annual hot-water demand = (600 + 350 × occupants) × behaviour. Annual appliance/lighting electricity = (800 + 500 × occupants + floor_area_m2) × behaviour. No gas cooking is modelled. Electricity base demand does not receive an age or insulation multiplier.

Old gas boiler efficiency = .72; modern gas boiler = .90. Both supply space heating and hot water. Fuel gas = delivered heat / efficiency. Heat pumps supply space heat at SCOP 3.0 and hot water at COP 2.5; gas is structurally zero. Electric resistance supplies both at efficiency 1.0; gas is structurally zero. These technology assumptions are illustrative, fixed across the year, and not claimed to be government standards. An electrically heated home is assumed to have no separate gas-consuming appliance.

EPC-style rating is not an additional multiplier: the physical features used to construct it already enter demand. This avoids counting insulation, glazing and heating effects twice. No property value or retrofit outcome is used as a demand input.

## Seasonality and solar

The following relative weights are normalised separately to sum to one. Heating and appliance weights receive independent per-month multipliers drawn uniformly from .95 to 1.05, then are normalised again so annual component totals are preserved. Hot water is distributed equally across 12 months. Final monthly values are rounded independently; annual sums may differ from unrounded totals by a few hundredths of a kWh.

| Month | Space heat | Appliances | PV generation |
|---|---|---|---|
| Jan | .170 | .095 | .025 |
| Feb | .145 | .085 | .040 |
| Mar | .120 | .085 | .075 |
| Apr | .080 | .080 | .100 |
| May | .040 | .080 | .125 |
| Jun | .015 | .075 | .135 |
| Jul | .005 | .075 | .135 |
| Aug | .005 | .075 | .115 |
| Sep | .035 | .080 | .090 |
| Oct | .085 | .085 | .065 |
| Nov | .130 | .090 | .035 |
| Dec | .170 | .095 | .025 |

Existing solar implies assumed PV capacity min(5, max(2, floor_area_m2 × .025)) kWp. Annual output per kWp is assumed as follows: Greater London 950, South East 980, South West 1000, East of England 950, West Midlands 900, East Midlands 900, North West 850, North East 850, Yorkshire and The Humber 870, Wales 880 kWh/kWp/year. Roof geometry and actual installed capacity are unknown.

For each month, solar self-consumed = min(electricity demand, .45 × PV generation). Grid import = max(electricity demand − solar self-consumed, 0). Electricity demand includes appliances plus electric space heating/hot water where applicable. PV does not reduce delivered heating demand or gas use. Surplus PV is assumed exported without credit; batteries are absent. Monthly self-consumption is an approximation and does not simulate half-hourly demand/generation coincidence. The CSV retains imports only; the generator keeps component calculations internally for checks.

## Coverage and missing values

All 100 properties have complete synthetic coverage, so annual imported electricity and gas are sums of their respective 12 monthly readings. No annualisation adjustment is needed. There are no missing readings in this version. Zero gas for heat-pump/resistance properties is a deliberate physical assumption and does not indicate missingness. Missing-data test fixtures can be added separately: represent unavailable values with blank cells and reading_status=missing, never impute them to zero. For partial readings, report per-fuel coverage explicitly and document an annualisation rule; this generator does not supply a partial-year annualisation function.

## Verification and reproducibility

Place generate_energy_usage.py alongside properties.csv, then run `python3 generate_energy_usage.py`. It generates energy_usage.csv and validates row count, exact fields, parent IDs, unique property/month keys, all 12 months, nonnegative readings, reading status and heating-system fuel consistency. Regeneration from unchanged properties and seed produced identical readings and CSV bytes.

Controlled comparisons hold other characteristics and behaviour constant and verify: poor > good insulation heating demand; single > triple glazing demand; solar decreases imports without changing underlying demand or gas; a heat pump increases electricity and removes boiler gas; heat pumps use less electricity than resistance for equivalent heat; doubling area raises total consumption without raising energy intensity; winter gas exceeds summer gas. These check internal consistency, not external accuracy.

Assumptions omit real occupancy, thermostat settings, daily weather, boiler part-load performance, heat-pump temperature dependence, meter errors, tariffs and retrofit interactions. Electricity-import intensity on a PV home differs from underlying demand intensity; downstream scoring should recognise this limitation. Large homes are not assigned worse thermal intensity merely for being larger. All months belonging to a property must remain together in any future train/validation/test split; group by customer if customer context is later introduced. This is baseline data generation, not P4's retrofit simulator or carbon accounting.
