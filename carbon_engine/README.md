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
screening values: loft insulation 15% (12–18%), heat pump 20% (15–25%, treated
as a brief-level purchased-energy statement but not applied as a blanket fuel
cut), solar import reduction 27.5% (20–35%, usable only with physical
self-consumption data), double glazing 10% (8–12%), and thermostat 7.5%
(5–10%). Envelope and thermostat percentages apply sequentially to explicit
thermal demand only. Gas heating needs boiler efficiency; a heat pump needs
SCOP. Solar offsets only supplied/projected self-consumed generation and is
capped at post-measure grid imports. The engine does not count exports.

Retrofit input data should provide, as applicable:

- annual purchased `electricity_kwh` and `gas_kwh` (null is missing; zero is known zero);
- `heating_system`, `thermal_demand_kwh`, and `boiler_efficiency` for gas systems;
- `scop` for existing or proposed heat pumps; optional explicit `heating_energy_kwh` can be cross-checked;
- `solar_self_consumed_kwh`, or both `solar_generation_kwh` and
  `solar_self_consumption_fraction` for proposed PV;
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
