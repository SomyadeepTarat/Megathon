# Person 5: valuation methodology and handoff

This module owns valuation and evaluation only. It does not implement scoring, energy simulation, the API or an LLM provider.

## Data contract for Person 3

One CSV row is a transaction. Required columns: `property_id`, `sale_date` (ISO date), `sale_price` (GBP), `region`, `property_type`, `floor_area` (m²), `bedrooms` (integer), `age` (years **at sale**), `market_index` (positive market-condition index known at sale). Optional `customer_id` groups all that customer's properties; a property must have one consistent grouping ID. Optional `energy_rating` must be A–G and the EPC known **at sale**, not an EPC created after a retrofit or transaction. Map `energy_rating_at_sale` from the PRD to this field. IDs must uniquely identify buildings, not individual sale transactions.

Unknown numeric values are rejected at ingestion. No price, current-value estimate, address identifier or future observation enters the predictors. Extra CSV columns are ignored. Person 3 must audit joins, EPC dates, market-index availability, duplicate buildings under different IDs and missingness before handoff; these cannot be proven from this simplified CSV.

Supply provenance JSON containing `kind` (`observed` or `synthetic`), `source`, `license`. For observed data, enabling scenario valuation also requires `energy_evidence: {"reviewed": true, "reference": "path or URL to reviewed evidence"}`. That evidence should document comparable transactions, matching quality, EPC feature quality, subgroup/temporal performance and sensitivity with/without EPC. This is an explicit human evidence gate, not an automatic statistical certification. Never set it merely because EPC exists.

The official [Land Registry guidance](https://www.gov.uk/guidance/about-the-price-paid-data) describes sales coverage and licensing. A joined sales/EPC dataset is still needed; this project has downloaded no public training data.

## Training and uncertainty

GroupShuffleSplit allocates approximately 70% of independent groups to development, 15% to calibration and 15% to final test. Within development, roughly 55% of total groups fit candidates and 15% select the model. Row fractions vary with group size. Ridge and [HistGradientBoostingRegressor](https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.HistGradientBoostingRegressor.html) share training-only preprocessing. The nonlinear candidate must lower selection MAE by more than 2%; otherwise use Ridge. Refit both on development, then calibrate only the selected model. The final test selects nothing.

Calibration samples one transaction per property/customer group to avoid treating correlated rows as independent. For `n` absolute calibration residuals and error rate `alpha`, the radius is the `ceil((n+1)*(1-alpha))` order statistic. Insufficient samples cause an error. Default value intervals target 90% marginal coverage under exchangeability. Reported transaction-level coverage on all test rows is descriptive and can weight large customer groups more heavily.

For a changed EPC, the model contrast is `f(after)-f(before)`. Its conservative range subtracts two marginal bands calibrated at `alpha/2`, giving contrast ± twice that radius. This uses a union-bound construction under exchangeability for both observations. It is **not a validated causal-effect interval**, and no paired counterfactual coverage is claimed. A scenario EPC may lie outside the observational distribution. Negative contrasts are preserved. Exact identical supported features produce zero model contrast and [0,0]; that does not assert a real-world zero effect.

We report held-out MAE, RMSE, R², median baseline, both candidate results, interval coverage/width, split counts, overlap audit and dataset hash. A validation-only ablation trains the selected model family without EPC; reviewed observed evidence can enable inference only if adding EPC also improves selection MAE. This predictive signal is not causal proof. Random grouped testing does not assess market drift; chronological evaluation remains explicitly unrun until dated observed data is supplied.

## Backend contract for Persons 1 and 4

```python
from backend.app.services.valuation_service import predict_value_impact
result = predict_value_impact(baseline_property, updated_property)
```

Both mappings contain the same `property_id`, region, type, area, bedrooms, age and market index. Person 4 supplies a complete updated property state. The only modeled retrofit feature is EPC. Heating, glazing, solar and insulation do not independently enter this model, so do not invent an EPC change from retrofit names. Person 1 must supply a supported EPC estimate or preserve the recorded rating and disclose the limitation.

The service defaults to `ml/models/valuation.joblib`; override with `VALUATION_MODEL_PATH` or `model_path`. It returns `unavailable` with a reason for missing models/data, unsupported categories, numeric values outside development bounds, synthetic data in normal mode, unrelated changes, or absent reviewed evidence. Synthetic demonstrations require explicit `allow_illustrative=True` and return `status="illustrative"`. Observed supported estimates return `status="indicative"`. Output includes baseline/after predictions and bands, signed value change, contrast band, method and warnings. Both values use the same model; `current_value_estimate` is never used to anchor only one side.

Only load trusted local joblib artifacts (pickle can execute code). Keep the repository root importable; run CLI commands from it. No FastAPI routes or shared schemas are owned here; Person 1 adapts the mappings to the API.
