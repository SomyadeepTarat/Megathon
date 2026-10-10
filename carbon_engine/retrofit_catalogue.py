"""Deterministic central assumptions and known model constraints.

The PRD supplies ranges, not measured property-specific effects. We use each
range midpoint as a transparent deterministic demonstration assumption;
these are not confidence intervals or guaranteed savings. Heating-demand
reductions apply only to explicit thermal demand, never all purchased energy.
"""

RETROFIT_CATALOGUE = {
    "loft_insulation": {
        "label": "Loft insulation", "effect_kind": "space_heating_demand_reduction",
        "range_fraction": [0.12, 0.18], "fraction": 0.15,
        "assumption": "Reduces remaining space-heating demand by 15% (brief range 12–18%); hot-water demand is unchanged.",
        "feasibility_field": "roof_suitable_for_loft",
    },
    "heat_pump": {
        "label": "Heat pump", "effect_kind": "heating_fuel_substitution",
        "range_fraction": [0.15, 0.25], "fraction": 0.20,
        "assumption": "Brief reports a 15–25% purchased-energy reduction range for context; scenario fuel changes are calculated from useful demand / supplied SCOP (and hot-water COP), with no blanket percentage applied.",
    },
    "solar_panels": {
        "label": "Solar panels", "effect_kind": "grid_import_reduction",
        "range_fraction": [0.20, 0.35], "fraction": 0.275,
        "assumption": "Brief gives 20–35% grid-import reduction; midpoint 27.5% is used only when the caller supplies generation or self-consumption data, and the reduction is capped by remaining import demand.",
        "feasibility_field": "roof_suitable_for_solar",
    },
    "double_glazing": {
        "label": "Double glazing", "effect_kind": "space_heating_demand_reduction",
        "range_fraction": [0.08, 0.12], "fraction": 0.10,
        "assumption": "Reduces remaining space-heating demand by 10% (brief range 8–12%); hot-water demand is unchanged.",
    },
    "smart_thermostat": {
        "label": "Smart thermostat", "effect_kind": "space_heating_demand_reduction",
        "range_fraction": [0.05, 0.10], "fraction": 0.075,
        "assumption": "Reduces remaining space-heating demand by 7.5% (brief range 5–10%); hot-water demand is unchanged.",
    },
}

# Fixed application order makes package results reproducible and prevents the
# same space-heating percentage being applied to an unchanged baseline.
SEQUENTIAL_ORDER = (
    "loft_insulation", "double_glazing", "smart_thermostat", "heat_pump", "solar_panels"
)
