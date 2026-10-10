# Properties dataset: 100-row synthetic prototype

## Scope and provenance

Created 10 October 2026. Exactly 100 property rows and the original 16 columns, in their original order. P00001–P00010 are preserved curated demo homes; P00011–P00100 are generated using Python's random.Random(42). Every row is synthetic. No real household record, address or transaction has been copied or joined. All values, including EPC-style ratings and current baseline values, are synthetic; reference statistics are not observed values for these homes. For the curated rows, generation_seed=42 is dataset metadata rather than evidence of random generation.

## Reference sources and their actual use

All links were reviewed on 10 October 2026. No underlying bulk data files were downloaded. These pages do not jointly provide a directly joinable property dataset.

| Reference | Evidence and use |
|---|---|
| [ONS EPC counts](https://www.ons.gov.uk/economy/economicoutputandproductivity/output/datasets/energyperformancebuildingcertificatesepc) | Weekly certificate counts for new/existing domestic properties in England and Wales. Checked for scope; not a source of property-level ratings, floor areas or their distributions. |
| [London Smart Meter](https://data.london.gov.uk/dataset/smartmeter-energy-consumption-data-in-london-households-vqm0d) | Half-hourly consumption for 5,567 London households, November 2011–February 2014. Reviewed as a future energy-data reference; supplies no parameters for this property-only file. |
| [NEED 2026 report](https://www.gov.uk/government/statistics/national-energy-efficiency-data-framework-need-report-summary-of-analysis-2026/national-energy-efficiency-data-framework-need-report-summary-of-analysis-2026-accessible-webpage) | Around 90% of gas-consuming houses occupy 51–150 m²; newer homes tend to be more efficient; flats tend to be smaller. These guide sizes and age/efficiency dependencies. Its 8% electricity-main-heating figure is an England 2023 benchmark used loosely for this England/Wales prototype. Comparisons involving flat floor areas require caution because NEED uses a different area definition for flats. |
| [Land Registry Price Paid Data](https://www.gov.uk/government/collections/price-paid-data) | Historical registered sale prices in England/Wales. Reviewed for scope; transactions were not imported, and historical prices are not relabelled as current baseline values. |
| [Official UK HPI July 2026 summary](https://www.gov.uk/government/statistics/uk-house-price-index-for-july-2026/uk-house-price-index-summary-july-2026) | Additional Land Registry/ONS reference for regional and property-type price anchors. July 2026 figures are provisional. Individual generated values are assumed estimates around these anchors, not official valuations or October 2026 nowcasts. |

Government pages state Open Government Licence v3.0, subject to exceptions. London Datastore lists Creative Commons Attribution. Attribute the original providers if redistributing source material; this file contains generated rows, not their household records.

## Schema

`property_id,customer_id,property_type,age,floor_area_m2,bedrooms,energy_rating,heating,insulation,glazing,solar,smart_controls,region,current_value_estimate_gbp,data_status,generation_seed`

IDs are unique strings with one customer per property. Age and bedrooms are integers; age is evaluated in 2026. Floor area is an assumed total internal area in m². Values are GBP baseline estimates, separate from historical sale prices. Booleans are lowercase true/false. Provenance is synthetic. Rating categories are A–G; insulation Poor/Average/Good; glazing Single/Double/Triple; heating Old gas boiler/Modern gas boiler/Heat pump/Electric resistance.

## Generation assumptions and rules

The accompanying generator retains the first 10 rows of properties.csv as curated inputs and regenerates the remaining 90. Keep those rows intact when reproducing this version. The script uses only Python standard-library modules; execute `python3 generate_properties.py` alongside the CSV.

Type totals are deliberately 22 Detached, 28 Semi-detached, 27 Terraced and 23 Flat. Regions are deliberately balanced at 10 each across the 10 existing region categories. Neither quota is claimed to represent housing-stock population shares. Seeded shuffling determines the order of the 90 additional rows.

| Type | Floor-area normal mean/SD | Clipped range | Age normal mean/SD |
|---|---|---|---|
| Detached | 128/19 m² | 65–240 m² | 52/34 years |
| Semi-detached | 101/18 m² | 51–200 m² | 60/34 years |
| Terraced | 86/16 m² | 45–170 m² | 82/34 years |
| Flat | 63/16 m² | 30–130 m² | 38/34 years |

These numerical distribution parameters are modelling assumptions informed by source scope and the NEED size benchmark, not published type-specific distributions. Age is clipped to 1–180 and rounded to whole years; floor area to one decimal place. Bedrooms depend on size: under 55 m² selects 1/2 with probabilities .75/.25; under 90 selects 2/3 with .8/.2; under 140 selects 3/4 with .8/.2; larger selects 4/5/6 with .65/.30/.05.

| Age band | Poor/Average/Good insulation probabilities |
|---|---|
| ≤26 | .01/.04/.95 |
| 27–39 | .10/.45/.45 |
| 40–81 | .30/.50/.20 |
| ≥82 | .50/.35/.15 |

Single/Double/Triple glazing probabilities are .005/.845/.15 for age ≤26; .08/.87/.05 for ages 27–59; .25/.72/.03 otherwise. These permit efficient renovated older homes without recording renovation history.

Five additional homes are selected for electric heating: two heat pumps and three resistance systems. Together with demos there are four of each and 92 gas boilers. For remaining generated homes, old-boiler probabilities are .02 at age ≤26, .20 at ages 27–59, .45 otherwise; the remainder receive modern boilers. Solar probabilities are .18 Detached, .12 Semi-detached, .08 Terraced, .02 Flat. Smart-controls probabilities are .85 with heat pumps, otherwise .50 at age ≤26 and .30 for older homes. These are assumptions, not sourced adoption statistics. Solar=true records existing PV only; it does not establish roof suitability for an additional retrofit.

EPC-style latent score = 50 + insulation adjustment (Poor −12, Average +8, Good +20) + glazing adjustment (Single −10, Double +5, Triple +10) + heating adjustment (old gas −8, modern gas +3, heat pump +12, resistance −5) + 8 if solar + 4 if controls + 5 if age ≤26 + normal noise with mean 0/SD 5. Convert at thresholds 85/75/65/50/35/20 to A/B/C/D/E/F, otherwise G. This is a disclosed proxy, not a SAP/RdSAP calculation, certified EPC, or trained prediction.

## Baseline value assumptions for generated rows

| Region category | July 2026 HPI anchor, GBP |
|---|---|
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

Official UK type anchors are 444936 Detached, 278555 Semi-detached, 231945 Terraced, 192704 Flat/maisonette, and 272611 for all types. Map official London to Greater London, West Midlands Region to West Midlands, and Flat/maisonette to Flat.

Generated value = regional anchor × (UK type anchor / 272611) × (floor area / assumed type mean)^0.55 × (1 + 0.02 × (bedrooms − 3)) × (1.04 if age ≤10, otherwise 1) × lognormal noise. Noise is exp(N(−0.5 × 0.18², 0.18²)). Floor at GBP 50,000 and round to GBP 1,000. Adjustments, cross-region type ratios and noise are synthetic assumptions; they are not fitted to transactions. No explicit EPC premium is added. Indirect correlations may still arise through age and type. Curated demo values remain their original illustrative amounts.

## Validation and limitations

Checks passed: exactly 100 rows/16 columns, unchanged headers, first 10 rows preserved, unique property/customer IDs, complete fields, allowed categories/booleans, positive areas/values, age 1–180 and bedrooms 1–6. Rerunning the generator reproduced identical CSV bytes. There are 62 of 70 gas-heated houses in the 51–150 m² band (88.6%), close to the NEED benchmark. That check does not validate the whole dataset. Small samples and deliberately included demo extremes distort distributions.

No monthly energy, retrofit savings, feasibility labels, carbon factors, future sale prices, or value-uplift targets are included. Missing-data edge cases have not been introduced. Roof/loft suitability is unknown because it is outside the strict schema; downstream systems must not infer feasibility from type alone. This dataset is appropriate for integration and demonstration, not real-world accuracy claims or valuations. Synthetic agreement alone cannot establish predictive accuracy. Keep all records from a property together when later splitting data. ID, seed and provenance columns are metadata, not predictive features; ratings and values must be excluded as inputs when they are the prediction target or unavailable at the decision time.
