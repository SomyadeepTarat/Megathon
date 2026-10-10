"""Deterministic annual household carbon and retrofit calculations."""
from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from typing import Any

from .retrofit_catalogue import RETROFIT_CATALOGUE, SEQUENTIAL_ORDER
from .schemas import property_and_energy, validate_factor_set

MONTHLY_ROUNDING_TOLERANCE_KWH = 0.06  # 12 monthly readings rounded to 0.01 kWh


def _number(value: Any, label: str, *, allow_zero: bool = True) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError):
        raise ValueError(f"{label} must be a number") from None
    if not math.isfinite(result) or result < 0 or (not allow_zero and result == 0):
        raise ValueError(f"{label} is outside its valid range")
    return result


def _energies(prop: Mapping[str, Any], energy: Mapping[str, Any]) -> tuple[float | None, float | None]:
    def pick(*keys):
        return next((energy[k] for k in keys if energy.get(k) is not None),
                    next((prop[k] for k in keys if prop.get(k) is not None), None))
    e, g = pick("electricity_kwh"), pick("gas_kwh")
    return (None if e is None else _number(e, "electricity_kwh"),
            None if g is None else _number(g, "gas_kwh"))


def _factor_data(emission_factors: Mapping[str, Any] | None):
    return validate_factor_set(emission_factors) if emission_factors is not None else None


def _emissions(electricity: float | None, gas: float | None,
               factors: Mapping[str, Mapping[str, Any]] | None) -> dict[str, Any]:
    if factors is None:
        return {"status": "unavailable", "electricity_kg_co2e": None,
                "gas_kg_co2e": None, "total_kg_co2e": None,
                "reason": "Documented electricity and gas emission factors were not supplied.", "factors": {}}
    e_factor = factors["electricity"]["kg_co2e_per_kwh"]
    g_factor = factors["gas"]["kg_co2e_per_kwh"]
    e = None if electricity is None else electricity * e_factor
    g = None if gas is None else gas * g_factor
    return {"status": "available" if e is not None and g is not None else "unavailable",
            "electricity_kg_co2e": e, "gas_kg_co2e": g,
            "total_kg_co2e": None if e is None or g is None else e + g,
            "reason": None if e is not None and g is not None else "Both annual fuel totals are required for carbon.",
            "factors": {fuel: dict(factors[fuel]) for fuel in ("electricity", "gas")}}


def calculate_baseline_carbon(property_data: Mapping[str, Any],
                              emission_factors: Mapping[str, Any]) -> dict[str, Any]:
    """Calculate annual emissions from purchased electricity and gas."""
    factors = _factor_data(emission_factors)
    prop, energy = property_and_energy(property_data)
    electricity, gas = _energies(prop, energy)
    carbon = _emissions(electricity, gas, factors)
    warnings = list(energy.get("warnings", []))
    if electricity is None:
        warnings.append("Annual electricity use is missing; it was not treated as zero.")
    if gas is None:
        warnings.append("Annual gas use is missing; it was not treated as zero.")
    return {"status": carbon["status"], "property_id": prop.get("property_id"),
            "energy_use": {"electricity_kwh": electricity, "gas_kwh": gas,
                           "total_kwh": None if electricity is None or gas is None else electricity + gas},
            "emissions": carbon, "warnings": warnings}


def _present(key: str, prop: Mapping[str, Any]) -> bool:
    if prop.get(f"{key}_installed") is True:
        return True
    if key == "double_glazing":
        return prop.get("glazing") in ("double", "triple")
    if key == "smart_thermostat":
        return prop.get("smart_controls") in ("basic", "advanced")
    if key == "solar_panels":
        return prop.get("solar_installed") is True or prop.get("solar") is True or prop.get("renewable_contribution") in ("limited", "substantial")
    if key == "heat_pump":
        return prop.get("heating_system") in ("air_source_heat_pump", "ground_source_heat_pump", "heat_pump")
    return False


def _feasibility(key: str, prop: Mapping[str, Any]) -> dict[str, str]:
    if _present(key, prop):
        return {"status": "infeasible", "reason": "This measure is already present; installing it again is not recommended."}
    if key == "loft_insulation" and prop.get("insulation") == "good":
        return {"status": "infeasible", "reason": "The property already has good insulation recorded; loft insulation is not recommended from this evidence."}
    if key == "loft_insulation" and prop.get("insulation") is None:
        return {"status": "conditional", "reason": "Overall insulation condition is unknown; confirm that an upgrade is needed."}
    field = RETROFIT_CATALOGUE[key].get("feasibility_field")
    if field and prop.get(field) is False:
        return {"status": "infeasible", "reason": f"{field} is explicitly unsuitable."}
    if key == "heat_pump":
        if prop.get("heat_pump_compatible") is False:
            return {"status": "infeasible", "reason": "Heat pump compatibility is explicitly false."}
        if prop.get("heat_pump_compatible") is not True:
            return {"status": "conditional", "reason": "Heat pump compatibility is unknown; a site assessment is required."}
        if prop.get("heating_system") is None:
            return {"status": "conditional", "reason": "The existing heating system is unknown."}
    if key == "smart_thermostat":
        if prop.get("controls_compatible") is False:
            return {"status": "infeasible", "reason": "Controls compatibility is explicitly false."}
        if prop.get("controls_compatible") is not True:
            return {"status": "conditional", "reason": "Controls compatibility is unknown; confirm before recommendation."}
    if field and prop.get(field) is not True:
        return {"status": "conditional", "reason": f"{field} is unknown; confirm site suitability."}
    if key == "loft_insulation" and prop.get("loft_insulation_installed") is None:
        return {"status": "conditional", "reason": "Loft-specific installation status is unknown."}
    if key == "double_glazing" and prop.get("glazing") is None:
        return {"status": "conditional", "reason": "Current glazing is unknown."}
    if key == "solar_panels" and prop.get("solar_installed") is None and prop.get("solar") is None:
        return {"status": "conditional", "reason": "Existing solar installation status is unknown."}
    if key == "smart_thermostat" and prop.get("smart_controls") is None:
        return {"status": "conditional", "reason": "Existing smart-control status is unknown."}
    return {"status": "feasible", "reason": "Known installation and compatibility fields permit screening; survey confirmation may still be needed."}


def _physical(prop: Mapping[str, Any], *keys: str):
    return next((prop[key] for key in keys if prop.get(key) is not None), None)


def _thermal_model(prop: Mapping[str, Any], electricity: float, gas: float):
    """Resolve component heating demand and preserve unaffected annual loads."""
    system = prop.get("heating_system")
    aliases = {"old_gas_boiler": "gas", "modern_gas_boiler": "gas",
               "air_source_heat_pump": "heat_pump", "ground_source_heat_pump": "heat_pump",
               "heat_pump": "heat_pump", "electric_resistance": "electric"}
    kind = aliases.get(system)
    if kind is None:
        return None, "A known heating_system is required to separate heating from other fuel use."
    space = _physical(prop, "space_heating_demand_kwh", "annual_space_heating_demand_kwh")
    water = _physical(prop, "hot_water_demand_kwh", "annual_hot_water_demand_kwh")
    total = _physical(prop, "thermal_demand_kwh")
    if space is None and total is not None and water is None and prop.get("thermal_demand_scope") not in ("space_heating_plus_hot_water", "total"):
        # Legacy contract: thermal_demand_kwh historically meant heating demand.
        space = total
    if space is None:
        return None, "Space-heating demand is missing; envelope and heating-system effects cannot be calculated."
    space = _number(space, "space_heating_demand_kwh")
    water = None if water is None else _number(water, "hot_water_demand_kwh")
    eta = _physical(prop, "boiler_efficiency", "heating_efficiency")
    scop = prop.get("scop")
    hot_cop = prop.get("hot_water_cop")
    resistance = _physical(prop, "electric_resistance_efficiency", "heating_efficiency")
    if kind == "gas" and eta is None:
        return None, "boiler_efficiency is required to recalculate gas heating after a space-heating measure."
    eta = None if eta is None else _number(eta, "boiler_efficiency", allow_zero=False)
    if kind == "heat_pump" and scop is None and _physical(prop, "electric_space_heating_kwh", "annual_electric_space_heating_kwh") is None:
        return None, "SCOP is required to derive existing heat-pump electricity."
    if kind == "electric" and resistance is None:
        return None, "Electric-resistance efficiency is required."
    if kind == "electric" and not (0 < float(resistance) <= 1):
        return None, "Electric-resistance efficiency must be a fraction no greater than 1."
    def component(keys, demand, conversion, label):
        given = _physical(prop, *keys)
        return _number(given, label) if given is not None else demand / conversion
    if kind == "gas":
        gs = component(("gas_space_heating_kwh", "annual_gas_space_heating_kwh"), space, eta, "gas_space_heating_kwh")
        gw = component(("gas_hot_water_kwh", "annual_gas_hot_water_kwh"), water, eta, "gas_hot_water_kwh") if water is not None and water > 0 else 0.0
        es = ew = 0.0
    elif kind == "heat_pump":
        sc = _number(scop, "scop", allow_zero=False) if scop is not None else space / _number(_physical(prop, "space_heating_demand_kwh") / _physical(prop, "electric_space_heating_kwh"), "derived SCOP", allow_zero=False)
        es = component(("electric_space_heating_kwh", "annual_electric_space_heating_kwh"), space, sc, "electric_space_heating_kwh")
        if water is not None and water > 0:
            if hot_cop is None and _physical(prop, "electric_hot_water_kwh", "annual_electric_hot_water_kwh") is None:
                return None, "Hot-water COP or measured electric hot-water use is required to preserve hot-water heating loads."
            hc = _number(hot_cop, "hot_water_cop", allow_zero=False) if hot_cop is not None else water / _physical(prop, "electric_hot_water_kwh", "annual_electric_hot_water_kwh")
            ew = component(("electric_hot_water_kwh", "annual_electric_hot_water_kwh"), water, hc, "electric_hot_water_kwh")
        else:
            ew = 0.0
        gs = gw = 0.0
    else:
        es = component(("electric_space_heating_kwh", "annual_electric_space_heating_kwh"), space, float(resistance), "electric_space_heating_kwh")
        ew = component(("electric_hot_water_kwh", "annual_electric_hot_water_kwh"), water, float(resistance), "electric_hot_water_kwh") if water is not None and water > 0 else 0.0
        gs = gw = 0.0
    rounding_warning = None
    if gs + gw > gas + MONTHLY_ROUNDING_TOLERANCE_KWH or es + ew > electricity + MONTHLY_ROUNDING_TOLERANCE_KWH:
        return None, "Modeled heating components exceed reported annual purchased fuel use."
    appliances = _physical(prop, "base_appliance_electricity_kwh", "annual_base_appliance_electricity_kwh")
    appliances = electricity - es - ew if appliances is None else _number(appliances, "base_appliance_electricity_kwh")
    other_electricity = electricity - appliances - es - ew
    nonheat_gas = gas - gs - gw
    if other_electricity < -MONTHLY_ROUNDING_TOLERANCE_KWH:
        return None, "Appliance electricity plus heating components exceeds reported electricity use."
    if other_electricity < 0 or gs + gw > gas or es + ew > electricity:
        rounding_warning = "Physical component totals differ from rounded monthly purchased-energy totals by at most 0.06 kWh; the small residual was capped at zero."
    return {"system_kind": kind, "space_demand": space, "water_demand": water,
            "space_fuel": "gas" if kind == "gas" else "electricity",
            "water_fuel": "gas" if kind == "gas" else "electricity",
            "space_use": gs if kind == "gas" else es,
            "water_use": gw if kind == "gas" else ew,
            "appliances": appliances, "other_electricity": max(0.0, other_electricity), "nonheat_gas": max(0.0, nonheat_gas),
            "rounding_warning": rounding_warning,
            "space_conversion": eta if kind == "gas" else _number(scop, "scop", allow_zero=False) if kind == "heat_pump" and scop is not None else float(resistance),
            "hot_water_conversion": eta if kind == "gas" else _number(hot_cop, "hot_water_cop", allow_zero=False) if kind == "heat_pump" and hot_cop is not None else float(resistance)}, None


def _unavailable_simulation(prop, selected, base_e, base_g, baseline, feasibility, reason, warnings):
    warnings = list(warnings)
    if base_e is None:
        warnings.append("Annual electricity use is missing; it was not treated as zero.")
    if base_g is None:
        warnings.append("Annual gas use is missing; it was not treated as zero.")
    return {"status": "unavailable", "reason": reason, "property_id": prop.get("property_id"),
            "selected_retrofits": selected,
            "baseline": {"energy_use": {"electricity_kwh": base_e, "gas_kwh": base_g,
                           "total_kwh": None if base_e is None or base_g is None else base_e + base_g}, "emissions": baseline},
            "after": None, "savings": {"electricity_kwh": None, "gas_kwh": None,
                           "net_energy_kwh": None, "annual_carbon_reduction_kg_co2e": None, "reason": reason},
            "feasibility": feasibility, "assumptions": [RETROFIT_CATALOGUE[k]["assumption"] for k in selected], "warnings": warnings}


def simulate_carbon_impact(property_data: Mapping[str, Any], selected_retrofits: Sequence[str],
                           emission_factors: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Simulate one measure or a package; energy remains calculable without factors."""
    factors = _factor_data(emission_factors)
    if isinstance(selected_retrofits, (str, bytes)):
        raise ValueError("selected_retrofits must be a sequence of retrofit IDs")
    selected = list(selected_retrofits)
    if len(selected) != len(set(selected)):
        raise ValueError("selected_retrofits contains duplicates")
    unknown = sorted(set(selected) - RETROFIT_CATALOGUE.keys())
    if unknown:
        raise ValueError(f"Unknown retrofit(s): {', '.join(unknown)}")
    prop, energy = property_and_energy(property_data)
    base_e, base_g = _energies(prop, energy)
    baseline = _emissions(base_e, base_g, factors)
    warnings = list(energy.get("warnings", []))
    feasibility = {key: _feasibility(key, prop) for key in selected}
    blocked = [key for key in selected if feasibility[key]["status"] == "infeasible"]
    conditional = [key for key in selected if feasibility[key]["status"] == "conditional"]
    if blocked:
        return _unavailable_simulation(prop, selected, base_e, base_g, baseline, feasibility,
            "Selected package includes explicitly infeasible or already-installed measures: " + ", ".join(blocked), warnings)
    if conditional:
        return _unavailable_simulation(prop, selected, base_e, base_g, baseline, feasibility,
            "Selected package has unknown eligibility and remains conditional: " + ", ".join(conditional), warnings)
    if base_e is None or base_g is None:
        return _unavailable_simulation(prop, selected, base_e, base_g, baseline, feasibility,
            "Both annual electricity_kwh and gas_kwh are required for scenario fuel totals.", warnings)
    has_heating = any(RETROFIT_CATALOGUE[k]["effect_kind"] in ("space_heating_demand_reduction", "heating_fuel_substitution") for k in selected)
    model = None
    if has_heating:
        model, reason = _thermal_model(prop, base_e, base_g)
        if model is None:
            return _unavailable_simulation(prop, selected, base_e, base_g, baseline, feasibility, reason, warnings)
        if model["rounding_warning"]:
            warnings.append(model["rounding_warning"])
    space_after = model["space_demand"] if model else None
    assumptions = []
    for key in SEQUENTIAL_ORDER:
        if key not in selected:
            continue
        row = RETROFIT_CATALOGUE[key]
        assumptions.append(row["assumption"])
        if row["effect_kind"] == "space_heating_demand_reduction":
            space_after *= 1 - row["fraction"]
    after_e, after_g = base_e, base_g
    if model:
        space_use = model["space_use"]
        water_use = model["water_use"]
        if "heat_pump" in selected:
            if model["water_demand"] is None:
                return _unavailable_simulation(prop, selected, base_e, base_g, baseline, feasibility,
                    "Hot-water demand is missing; replacing the heating system cannot be modeled without silently dropping its load.", warnings)
            scop = prop.get("scop")
            if scop is None:
                return _unavailable_simulation(prop, selected, base_e, base_g, baseline, feasibility, "SCOP is required to model proposed heat-pump electricity use.", warnings)
            hp_space = space_after / _number(scop, "scop", allow_zero=False)
            if model["water_demand"] > 0:
                cop = prop.get("hot_water_cop")
                if cop is None:
                    return _unavailable_simulation(prop, selected, base_e, base_g, baseline, feasibility,
                        "Hot-water COP is required to model heat-pump hot-water electricity; existing gas hot-water use was not discarded.", warnings)
                hp_water = model["water_demand"] / _number(cop, "hot_water_cop", allow_zero=False)
            else:
                hp_water = 0.0
            after_e = model["appliances"] + model["other_electricity"] + hp_space + hp_water
            after_g = model["nonheat_gas"]
            assumptions.append("Heat pump substitutes for space and hot-water heating using supplied SCOP and hot-water COP; appliance electricity and non-heating gas are preserved.")
        elif model["system_kind"] == "gas":
            eta = _number(_physical(prop, "boiler_efficiency", "heating_efficiency"), "boiler_efficiency", allow_zero=False)
            after_g = base_g + space_after / eta - model["space_use"]
            after_e = model["appliances"] + model["other_electricity"]
        elif model["system_kind"] == "heat_pump":
            scop = _number(prop.get("scop"), "scop", allow_zero=False)
            after_e = model["appliances"] + model["other_electricity"] + space_after / scop + water_use
            after_g = model["nonheat_gas"]
        else:
            efficiency = _number(prop.get("electric_resistance_efficiency", prop.get("heating_efficiency", 1)), "electric_resistance_efficiency", allow_zero=False)
            after_e = model["appliances"] + model["other_electricity"] + space_after / efficiency + water_use
            after_g = model["nonheat_gas"]
    solar_generation = solar_used = exports = None
    if "solar_panels" in selected:
        generation = _physical(prop, "proposed_solar_generation_kwh")
        direct = _physical(prop, "proposed_solar_self_consumed_kwh")
        rate = _physical(prop, "proposed_solar_self_consumption_fraction")
        if generation is None:
            return _unavailable_simulation(prop, selected, base_e, base_g, baseline, feasibility,
                "Proposed solar generation is missing. Existing solar generation is not reused as a new-installation estimate.", warnings)
        solar_generation = _number(generation, "proposed_solar_generation_kwh")
        if direct is not None:
            requested = _number(direct, "proposed_solar_self_consumed_kwh")
        elif rate is not None:
            requested = solar_generation * _number(rate, "proposed_solar_self_consumption_fraction")
        else:
            return _unavailable_simulation(prop, selected, base_e, base_g, baseline, feasibility,
                "Proposed solar self-consumption or a documented self-consumption fraction is required.", warnings)
        solar_used = min(requested, solar_generation, after_e)
        exports = solar_generation - solar_used
        if solar_used < requested:
            warnings.append("Proposed solar self-consumption was capped at generation and remaining eligible grid imports.")
        after_e -= solar_used
        assumptions.append("Solar changes grid imports only; generation, self-consumption, exports and underlying demand remain separate.")
    after_e, after_g = max(0.0, after_e), max(0.0, after_g)
    after_carbon = _emissions(after_e, after_g, factors)
    e_saving, g_saving = base_e - after_e, base_g - after_g
    reduction = (baseline["total_kg_co2e"] - after_carbon["total_kg_co2e"]
                 if baseline["total_kg_co2e"] is not None and after_carbon["total_kg_co2e"] is not None else None)
    if reduction is not None and reduction < 0:
        warnings.append("Scenario increases annual emissions under supplied factors; reduction is signed and negative.")
    return {"status": "available", "property_id": prop.get("property_id"), "selected_retrofits": selected,
        "baseline": {"energy_use": {"electricity_kwh": base_e, "gas_kwh": base_g, "total_kwh": base_e + base_g}, "emissions": baseline},
        "after": {"energy_use": {"electricity_kwh": after_e, "gas_kwh": after_g, "total_kwh": after_e + after_g}, "emissions": after_carbon,
                  "solar": {"generation_kwh": solar_generation, "self_consumed_kwh": solar_used, "exported_kwh": exports}},
        "savings": {"electricity_kwh": e_saving, "gas_kwh": g_saving, "net_energy_kwh": e_saving + g_saving,
                    "annual_carbon_reduction_kg_co2e": reduction,
                    "carbon_reason": None if reduction is not None else baseline["reason"] or after_carbon["reason"]},
        "feasibility": feasibility, "assumptions": assumptions, "warnings": warnings}


def rank_retrofits_by_carbon(property_data: Mapping[str, Any], emission_factors: Mapping[str, Any] | None) -> dict[str, Any]:
    """Rank calculable individual options; keep unknown/infeasible options separate."""
    prop, _ = property_and_energy(property_data)
    options = {}
    for key in RETROFIT_CATALOGUE:
        feasibility = _feasibility(key, prop)
        if feasibility["status"] != "feasible":
            options[key] = {"status": "unavailable", "reason": feasibility["reason"], "feasibility": feasibility,
                            "annual_carbon_reduction_kg_co2e": None}
            continue
        result = simulate_carbon_impact(property_data, [key], emission_factors)
        if result["status"] != "available" or result["savings"]["annual_carbon_reduction_kg_co2e"] is None:
            options[key] = {"status": "unavailable", "reason": result.get("reason") or result["savings"].get("carbon_reason"),
                            "feasibility": feasibility, "annual_carbon_reduction_kg_co2e": None,
                            "warnings": result["warnings"], "assumptions": result["assumptions"]}
        else:
            options[key] = {"status": "available", "reason": None, "feasibility": feasibility,
                            "annual_carbon_reduction_kg_co2e": result["savings"]["annual_carbon_reduction_kg_co2e"], "simulation": result}
    ranked = sorted(({"retrofit": k, **v} for k, v in options.items() if v["status"] == "available"),
                    key=lambda row: (-row["annual_carbon_reduction_kg_co2e"], row["retrofit"]))
    unavailable = [{"retrofit": k, **v} for k, v in options.items() if v["status"] == "unavailable"]
    return {"status": "available" if ranked else "unavailable", "reason": None if ranked else "No option has calculable carbon reduction with known feasibility.",
            "ranking": ranked, "unavailable_options": unavailable,
            "methodology": "Individual deterministic simulations using sequential physical calculations and supplied emission factors; sorted by signed carbon reduction.",
            "warnings": ["Screening assumptions are not property-specific measured savings.", "Conditional measures are withheld until eligibility is confirmed."]}
