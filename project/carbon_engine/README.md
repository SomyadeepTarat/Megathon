# Carbon engine

Standalone annual operational-carbon calculator and single-retrofit screening
ranker. It does not import or update the Green Home Score, the frontend, or the
valuation ML code. Public functions accept the existing repository property
record shape (`property` plus `annual_energy`) or a flat mapping.

## Emission factors

No emission factors are shipped: the PRD says to use official, documented
factors and not hardcode unverified values. Pass a mapping or load an operator
maintained JSON file. Each fuel record must contain `kg_co2e_per_kwh`, `source`,
`source_year`, `accounting_boundary`, and `version`. Units are kg CO2e per kWh
of purchased fuel; use the same accounting boundary and factor year for both
fuels. Preserve the exact official source/table row in the `source` field.

Example configuration shape (replace every placeholder with a checked source):

```json
{
  "electricity": {
    "fuel": "electricity", "kg_co2e_per_kwh": "REPLACE WITH VERIFIED NUMBER",
    "source": "REPLACE WITH OFFICIAL SOURCE AND TABLE ROW",
    "source_year": 2026, "accounting_boundary": "REPLACE WITH SOURCE BOUNDARY",
    "version": "REPLACE WITH DATASET VERSION"
  },
  "gas": {
    "fuel": "gas", "kg_co2e_per_kwh": "REPLACE WITH VERIFIED NUMBER",
    "source": "REPLACE WITH OFFICIAL SOURCE AND TABLE ROW",
    "source_year": 2026, "accounting_boundary": "REPLACE WITH SOURCE BOUNDARY",
    "version": "REPLACE WITH DATASET VERSION"
  }
}
```

The strings above are placeholders, not factors; replace them with numeric
values before use. Factors are never inferred, defaulted, or converted from an
unspecified unit. Direct numeric factor values are rejected because they lack
provenance.

## Run

From the project root, after creating `emission_factors.json` with verified
records as above:

```python
import json
from carbon_engine import load_emission_factors, calculate_baseline_carbon

with open("backend/data/demo_properties.json", encoding="utf-8") as f:
    property_data = json.load(f)[0]
factors = load_emission_factors("emission_factors.json")
print(json.dumps(calculate_baseline_carbon(property_data, factors), indent=2))
```

Use `simulate_carbon_impact(property_data, ["heat_pump"], factors)` for a
scenario, or `rank_retrofits_by_carbon(property_data, factors)` for separate
single-retrofit options. The demo JSON intentionally lacks thermal demand,
boiler efficiency, SCOP and solar generation, so its baseline can be
calculated while retrofit estimates that need those inputs correctly return
unavailable. The demo record is synthetic and is only a software fixture.

## Modeling assumptions

`retrofit_catalogue.py` records the brief's ranges and deterministic midpoint
assumptions: loft insulation 15% (12–18%), double glazing 10% (8–12%), and
thermostat 7.5% (5–10%). They are applied sequentially to explicit
space-heating demand; hot-water demand is unchanged. The heat-pump (15–25%)
and solar (20–35%) brief ranges are context, not blanket multipliers: heat
pump electricity is useful space/hot-water demand divided by supplied SCOP
and hot-water COP; solar requires separately supplied proposed generation and
self-consumption. Existing solar generation is never reused as predicted new
generation. Solar offsets grid imports only, is capped at generation and
remaining imports, and exports are reported separately.

## Physical input fields

Prefer separate `space_heating_demand_kwh` and `hot_water_demand_kwh`, with
`thermal_demand_scope` when a total is also provided. The adapter preserves
source gas/electric heating components, appliance electricity, boiler
efficiency, SCOP, hot-water COP, and provenance. A heat-pump scenario needs
SCOP and, when hot-water demand is present, hot-water COP (unless measured
electric hot-water use is available for the existing system). Missing values
remain unavailable; they are never filled with zero or a generic estimate.
For a proposed solar installation provide `proposed_solar_generation_kwh`
and either `proposed_solar_self_consumed_kwh` or
`proposed_solar_self_consumption_fraction`.

The backend exposes `POST /retrofits/optimize`. It enumerates all 32 measure
subsets against the same baseline, but only ranks packages whose eligibility,
objective inputs, and per-measure costs are known and whose total cost is
within `budget_gbp`. Costs must be supplied with source and date; no default
catalogue prices are treated as production evidence. Carbon ranking requires
documented fuel factors; energy ranking does not. Shortest-payback ranking
requires both tariffs, known cost, and positive bill savings. Every tested
subset is returned in `package_decisions` with an eligible, rejected,
conditional, or unavailable reason.

Recommendation suitability is an evidence label, not a rank score: High
requires confirmed eligibility, positive modeled objective benefit, observed
annual energy, and observed physical-input provenance; Medium identifies
conditional eligibility or synthetic/estimated screening evidence; Low marks
explicit incompatibility/already-present measures or non-positive modeled
benefit. Package ordering uses the selected objective directly and applies
cost/measure IDs only as deterministic tie-breakers.
Scenario state records the smart-thermostat installation flag while retaining
the prior smart-controls category; no unsupported score-category mapping is
assumed.

Retrofit input data should provide, as applicable:

- annual purchased `electricity_kwh` and `gas_kwh` (null is missing; zero is known zero);
- `heating_system`, `thermal_demand_kwh`, and `boiler_efficiency` for gas systems;
- `scop` for existing or proposed heat pumps; optional explicit `heating_energy_kwh` can be cross-checked;
- `proposed_solar_generation_kwh` and either
  `proposed_solar_self_consumed_kwh` or
  `proposed_solar_self_consumption_fraction` for a new PV installation;
- `roof_suitable_for_loft`, `roof_suitable_for_solar`, and explicit installed
  flags where the existing generic property fields cannot establish status.

Known existing measures are excluded as infeasible. Unknown site eligibility
is conditional. The ranking separates unavailable options and never sorts
them as zero-impact options. Conditional estimates require human feasibility
confirmation before recommendation.

## Tests

```bash
python -m pytest carbon_engine/tests -q
```

Tests use the checked-in `backend/data/demo_properties.json` as the requested
input fixture and test-only, clearly synthetic factors for arithmetic checks;
these factors are not production configuration.
