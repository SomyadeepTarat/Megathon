# Understand your implementation

Your model answers: “What price does this pattern of property characteristics predict?” It does not know how much a particular renovation truly causes a buyer to pay.

1. **Prepare transactions.** Person 3 supplies each house's characteristics at the time of sale and its observed sale price. `sale_price` is the answer the model learns to predict. It is never supplied as a prediction feature.
2. **Keep evaluation honest.** All properties of one customer stay together. Fit data teaches the model; selection data chooses Ridge versus boosting; calibration data sets uncertainty; test data measures final performance. No test house teaches the model.
3. **Learn the relationship.** Ridge learns a regularized additive relationship. Histogram gradient boosting can learn nonlinear relationships and interactions. One-hot encoding turns region, property type and EPC categories into model inputs. A validation-only EPC ablation asks whether adding EPC improves predictions.
4. **Measure uncertainty.** We observe how far calibration predictions miss actual prices. A finite-sample residual quantile becomes the value interval radius. This is based on measured errors rather than an invented percentage. A wider conservative range accompanies the difference between two predictions.
5. **Compare the same home twice.** `predict_value_impact` predicts the baseline and complete updated property with the same fitted model. Region, type, floor area, age, bedrooms and market conditions must stay fixed. Only EPC can affect this model's retrofit contrast. No EPC change means no change in the model prediction—even if a retrofit has genuine energy benefits.
6. **Return an honest status.** No artifact, missing inputs, unsupported categories or absent evidence produce `unavailable`. Explicit fixture demonstrations produce `illustrative`. Reviewed observed-data models with a positive EPC validation signal can produce `indicative`, with causal and uncertainty warnings.

Try `.venv/bin/python -m ml.demo_valuation` after training. It prints the normal-mode refusal and the explicitly illustrative before/after estimate. The example EPC change is invented for the software demonstration, not calculated from a renovation.

For the judges, explain MAE as average absolute price error, RMSE as an error measure that penalizes large misses, R² as performance relative to a constant prediction, and interval coverage as the fraction of actual held-out prices inside the returned bands. A high synthetic R² does not demonstrate a useful real-world model.

Your handoff to Person 1 is the function in `backend/app/services/valuation_service.py`. Your request to Person 3 is the CSV/provenance contract in `docs/valuation_methodology.md`. Your coordination with Person 2 and Person 4 is the recorded-response and reference-case formats in `evaluation/`. The PRD's numerical scoring and retrofit code belongs to them, so the evaluation helpers consume their results rather than recreating their implementations.
