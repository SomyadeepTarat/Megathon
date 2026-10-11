# Calculated retrofit recommendations and storage

## Existing engines

P4/carbon_engine remains the simulator. Recommendations simulate individual
measures against the same input baseline. Package simulation and the existing
32-subset budget optimizer recalculate physical interactions; never add individual
percentages. Scoring, benchmark and valuation calculations are unchanged.

## Ranking policy

RecommendationRequest and the planner default to `energy_reduction`.
For a positive, known baseline of purchased electricity plus gas, rank descending
by `100 * (baseline - after) / baseline`. Electricity and gas changes remain
separate and signed in `scenario.energy`. Explicit `carbon_reduction` and
`shortest_payback` objectives retain their existing calculated comparisons.
Ties use retrofit IDs for deterministic ordering.

Only confirmed-feasible measures with calculable, positive objective benefit are
in `recommendations`. Conditional, incompatible, unavailable, zero-benefit and
negative-benefit options remain in `other_options`, with null priority and a
`ranking_reason`; missing calculations never become zero savings. Carbon can
remain unavailable while energy ranking works. Zero baseline energy cannot
establish a percentage improvement.

Existing suitability policy is retained: High requires confirmed feasibility,
positive modeled benefit, and observed energy plus physical provenance. Synthetic
or estimated evidence, unavailable objective evidence and conditional eligibility
are Medium; explicit incompatibility/already-present or calculated nonpositive
benefit is Low. Rank alone does not establish High suitability.

`installation_order` uses the existing sequence: loft insulation, glazing,
thermostat, heat pump, solar, restricted to recommended measures. This is planning
guidance separate from benefit ranking, not an invented technical requirement
that every heat pump needs a loft upgrade. Confirm dependencies and sizing with
an installer. Budget checks require documented costs; individual recommendations
do not substitute for package optimization.

## Persistence and API

The existing EditableRepository now stores `recommendation_snapshots` in the same
SQLite database as `property_snapshots`. Default path is
`backend/data/user_properties.db`, configurable with `GREENPRINT_DB_PATH`.
`backend/app/db/migrations/001_recommendation_snapshots.sql` is applied
idempotently during repository initialization; no separate migration command.

POST `/retrofits/recommend` accepts the existing complete assessment input,
optional budget/objective, and optional `scenario_id`. The response is read back
from storage before returning. The row stores the full calculation input and
response, including assumptions, limitations, ordered recommendations and each
option's nested simulated state. Original property snapshots are not changed.

GET `/properties/{property_id}/recommendations?scenario_id={scenario_id}` retrieves
that property's specific saved scenario. Without a scenario ID, GET returns the
most recently updated recommendation snapshot. Missing or cross-property IDs
return 404. GET does not recalculate: the frontend should POST new input when
property details, costs, objectives or factors change.

An omitted scenario ID becomes `rec-<SHA256 of normalized input>`. Identical inputs
upsert one row and increment `revision`; changed inputs receive a different ID.
For a user scenario/session, pass its ID explicitly; recalculation updates the
same property/scenario row and increments revision. Revision is a counter, not
historical retention: old versions of that row are replaced. Individual options
still have their own simulated `scenario.scenario_id`; the outer `scenario_id`
identifies the recommendation context. To rank from a simulated post-retrofit
home, supply its updated property and after-energy snapshot explicitly. A saved
ID by itself does not load or infer changed physical inputs.

Response shape (abbreviated; existing nested scenario contract is preserved):

```json
{
  "property_id": "P00001",
  "scenario_id": "walkthrough-P00001",
  "revision": 1,
  "objective": "energy_reduction",
  "status": "partial",
  "recommendations": [{
    "retrofit": "double_glazing",
    "priority": 1,
    "feasibility": {"status": "feasible", "reason": "..."},
    "suitability": "Medium",
    "suitability_reason": "...",
    "ranking_reason": "...",
    "estimated_cost_gbp": null,
    "scenario": {"energy": {}, "carbon": {}, "assumptions": [], "warnings": []}
  }],
  "other_options": [],
  "installation_order": ["double_glazing"],
  "methodology": "...",
  "warnings": []
}
```

The planner calls POST then GET for the exact returned property/scenario context,
preserves stored priority order, shows per-fuel outcomes and unavailable reasons,
and displays installation guidance. `api.storedRecommendations(propertyId,
scenarioId?)` also allows retrieval without rerunning calculations. Existing
advisor recommendation calls use the same ranking engine; they do not persist
new snapshots unless they go through the mounted recommendation POST route.

## Reproduce

From the project root, start the backend:

```bash
GREENPRINT_PROPERTY_DATASET=csv venv/bin/python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8001
```

In another terminal:

```bash
venv/bin/python scripts/verify_recommendation_storage.py
npm --prefix frontend run dev
```

Open the planner, select a property, and click **Check recommendations**.
P00001's current synthetic inputs permit double-glazing simulation. Unknown loft,
heat-pump, roof and controls fields remain conditional; nothing is fabricated to
complete these options. Missing costs/tariffs keep cost/payback unavailable.

Tests:

```bash
venv/bin/python -m pytest backend/tests/test_recommendation_storage.py backend/tests/test_runtime_integration.py backend/tests/test_optimizer.py -q
venv/bin/python -m pytest -q
npm --prefix frontend test
npm --prefix frontend run typecheck
```
