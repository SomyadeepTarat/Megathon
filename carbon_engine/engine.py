"""Standalone, deterministic annual household carbon calculations."""
from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from typing import Any

from .retrofit_catalogue import RETROFIT_CATALOGUE, SEQUENTIAL_ORDER
from .schemas import property_and_energy, validate_factor_set


def _number(value: Any, label: str, *, allow_zero: bool = True) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError):
        raise ValueError(f"{label} must be a number") from None
    if not math.isfinite(result) or result < 0 or (not allow_zero and result == 0):
        raise ValueError(f"{label} is outside its valid range")
    return result


def _energies(prop: Mapping[str, Any], energy: Mapping[str, Any]) -> tuple[float | None, float | None]:
    electricity = energy.get("electricity_kwh", prop.get("electricity_kwh"))
    gas = energy.get("gas_kwh", prop.get("gas_kwh"))
    return (None if electricity is None else _number(electricity, "electricity_kwh"),
            None if gas is None else _number(gas, "gas_kwh"))


def _factor_data(emission_factors: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    return validate_factor_set(emission_factors)


def _emissions(electricity: float | None, gas: float | None,
               factors: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    e_factor = factors["electricity"]["kg_co2e_per_kwh"]
    g_factor = factors["gas"]["kg_co2e_per_kwh"]
    e = None if electricity is None else electricity * e_factor
    g = None if gas is None else gas * g_factor
    return {
        "status": "available" if e is not None and g is not None else "unavailable",
        "electricity_kg_co2e": e,
        "gas_kg_co2e": g,
        "total_kg_co2e": None if e is None or g is None else e + g,
        "reason": None if e is not None and g is not None else "Both annual electricity and gas use are required for a total.",
        "factors": {fuel: dict(factors[fuel]) for fuel in ("electricity", "gas")},
    }


def calculate_baseline_carbon(property_data: Mapping[str, Any],
                              emission_factors: Mapping[str, Any]) -> dict[str, Any]:
    """Calculate annual baseline emissions from known purchased fuel use.

    Input may be the existing PropertyRecord JSON (``property`` and
    ``annual_energy``) or a flat mapping with the two fuel fields.
    Missing fuel remains null and makes the total unavailable; known zero is
    retained as zero.
    """
    factors = _factor_data(emission_factors)
    prop, energy = property_and_energy(property_data)
    electricity, gas = _energies(prop, energy)
    carbon = _emissions(electricity, gas, factors)
    warnings = list(energy.get("warnings", []))
    if electricity is None:
        warnings.append("Annual electricity use is missing; it was not treated as zero.")
    if gas is None:
        warnings.append("Annual gas use is missing; it was not treated as zero.")
    return {
        "status": carbon["status"],
        "property_id": prop.get("property_id"),
        "energy_use": {"electricity_kwh": electricity, "gas_kwh": gas,
                       "total_kwh": None if electricity is None or gas is None else electricity + gas},
        "emissions": carbon,
        "warnings": warnings,
    }


def _already_present(key: str, prop: Mapping[str, Any]) -> bool:
    explicit = prop.get(f"{key}_installed")
    if explicit is True:
        return True
    if key == "double_glazing":
        return prop.get("glazing") in ("double", "triple")
    if key == "smart_thermostat":
        return prop.get("smart_controls") in ("basic", "advanced")
    if key == "solar_panels":
        return (prop.get("solar_installed") is True or
                prop.get("solar") is True or
                prop.get("renewable_contribution") in ("limited", "substantial"))
    if key == "heat_pump":
        return prop.get("heating_system") in ("air_source_heat_pump", "ground_source_heat_pump", "heat_pump")
    return False


def _feasibility(key: str, prop: Mapping[str, Any]) -> dict[str, str]:
    if _already_present(key, prop):
        return {"status": "infeasible", "reason": "This retrofit appears to be already present; it is not recommended again."}
    field = RETROFIT_CATALOGUE[key].get("feasibility_field")
    if field and prop.get(field) is False:
        return {"status": "infeasible", "reason": f"{field} is recorded as unsuitable."}
    if field and prop.get(field) is not True:
        return {"status": "conditional", "reason": f"{field} is unknown; confirm site suitability."}
    if key == "loft_insulation" and "loft_insulation_installed" not in prop:
        return {"status": "conditional", "reason": "Loft-specific insulation status is unknown; generic insulation quality does not establish whether this measure is already installed."}
    if key == "heat_pump" and prop.get("heating_system") is None:
        return {"status": "conditional", "reason": "Existing heating system is unknown; replacement suitability cannot be checked."}
    return {"status": "feasible", "reason": "No known property input blocks this retrofit; site survey may still be needed."}


def _thermal_model(prop: Mapping[str, Any], energy: Mapping[str, Any],
                   electricity: float | None, gas: float | None) -> tuple[dict[str, Any] | None, str | None]:
    """Resolve heating fuel load and residual non-heating loads, if supported."""
    if electricity is None or gas is None:
        return None, "Both annual fuel totals are required to preserve non-heating loads."
    system = prop.get("heating_system")
    aliases = {"old_gas_boiler": "gas", "modern_gas_boiler": "gas",
               "air_source_heat_pump": "heat_pump", "ground_source_heat_pump": "heat_pump",
               "heat_pump": "heat_pump", "electric_resistance": "electric"}
    kind = aliases.get(system)
    if kind is None:
        return None, "A known heating_system is required to separate heating from other fuel use."
    demand = energy.get("thermal_demand_kwh", prop.get("thermal_demand_kwh"))
    heat_input = energy.get("heating_energy_kwh", prop.get("heating_energy_kwh"))
    if demand is None:
        if heat_input is None:
            return None, "Heating demand is missing; provide thermal_demand_kwh (or heating_energy_kwh with its conversion input)."
        heat_input = _number(heat_input, "heating_energy_kwh")
        if kind == "gas":
            efficiency = prop.get("boiler_efficiency", prop.get("heating_efficiency"))
            if efficiency is None:
                return None, "boiler_efficiency is required to infer thermal demand from heating_energy_kwh."
            efficiency = _number(efficiency, "boiler_efficiency", allow_zero=False)
            if efficiency > 1:
                return None, "boiler_efficiency must be a fraction no greater than 1."
            demand = heat_input * efficiency
        elif kind == "heat_pump":
            scop = prop.get("scop")
            if scop is None:
                return None, "scop is required to infer thermal demand from heat-pump heating_energy_kwh."
            demand = heat_input * _number(scop, "scop", allow_zero=False)
        else:
            demand = heat_input
    demand = _number(demand, "thermal_demand_kwh")
    if kind == "gas":
        efficiency = prop.get("boiler_efficiency", prop.get("heating_efficiency"))
        if efficiency is None:
            return None, "boiler_efficiency is required to calculate purchased gas for known thermal demand."
        efficiency = _number(efficiency, "boiler_efficiency", allow_zero=False)
        if efficiency > 1:
            return None, "boiler_efficiency must be a fraction no greater than 1."
        fuel, heat_use = "gas", demand / efficiency
    elif kind == "heat_pump":
        scop = prop.get("scop")
        if scop is None:
            return None, "scop is required to calculate heat-pump electricity for known thermal demand."
        fuel, heat_use = "electricity", demand / _number(scop, "scop", allow_zero=False)
    else:
        efficiency = prop.get("heating_efficiency", 1.0)
        efficiency = _number(efficiency, "heating_efficiency", allow_zero=False)
        fuel, heat_use = "electricity", demand / efficiency
    totals = {"electricity": electricity, "gas": gas}
    if heat_input is not None:
        # If an explicit purchased heating load was supplied, it must match
        # the derived fuel load so the residual does not silently change.
        supplied = _number(heat_input, "heating_energy_kwh")
        if not math.isclose(supplied, heat_use, rel_tol=1e-5, abs_tol=1e-5):
            return None, "heating_energy_kwh conflicts with thermal_demand_kwh and the heating conversion input."
    if heat_use > totals[fuel] + 1e-7:
        return None, f"Modeled heating use ({heat_use:g} kWh) exceeds reported {fuel} use."
    residual = {"electricity": electricity, "gas": gas}
    residual[fuel] -= heat_use
    return {"kind": kind, "system": system, "fuel": fuel, "heat_use_kwh": heat_use,
            "thermal_demand_kwh": demand, "non_heating": residual}, None


def _solar_self_consumption(prop: Mapping[str, Any], energy: Mapping[str, Any],
                            remaining_import: float) -> tuple[float | None, str | None]:
    direct = energy.get("solar_self_consumed_kwh", prop.get("solar_self_consumed_kwh"))
    generation = energy.get("solar_generation_kwh", prop.get("solar_generation_kwh"))
    rate = energy.get("solar_self_consumption_fraction", prop.get("solar_self_consumption_fraction"))
    if direct is not None:
        amount = _number(direct, "solar_self_consumed_kwh")
    elif generation is not None and rate is not None:
        generation = _number(generation, "solar_generation_kwh")
        rate = _number(rate, "solar_self_consumption_fraction")
        if rate > 1:
            return None, "solar_self_consumption_fraction must be between 0 and 1."
        amount = generation * rate
    else:
        return None, "Solar generation and self-consumption data are missing; the brief's import-reduction range alone cannot establish physical self-consumption."
    if amount > remaining_import + 1e-7:
        return min(amount, remaining_import), "Solar self-consumption was capped at remaining electricity demand."
    return amount, None


def simulate_carbon_impact(property_data: Mapping[str, Any], selected_retrofits: Sequence[str],
                           emission_factors: Mapping[str, Any]) -> dict[str, Any]:
    """Simulate a retrofit package with explicit energy decomposition.

    Envelope effects are applied sequentially to thermal demand, heat pumps
    substitute gas heating with electricity using supplied SCOP, and PV
    reduces purchased imports only by supplied self-consumed generation.
    """
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
    if blocked:
        reason = "Selected package includes already-present or unsuitable measures: " + ", ".join(blocked)
        return _unavailable_simulation(prop, selected, base_e, base_g, baseline, feasibility, reason, warnings)
    if base_e is None or base_g is None:
        reason = "Both annual electricity_kwh and gas_kwh are required for scenario energy and carbon totals."
        return _unavailable_simulation(prop, selected, base_e, base_g, baseline, feasibility, reason, warnings)
    thermal_keys = [k for k in SEQUENTIAL_ORDER if k in selected and
                    RETROFIT_CATALOGUE[k]["effect_kind"] in ("thermal_demand_reduction", "heating_fuel_substitution")]
    solar_selected = "solar_panels" in selected
    thermal = None
    if thermal_keys:
        thermal, reason = _thermal_model(prop, energy, base_e, base_g)
        if thermal is None:
            return _unavailable_simulation(prop, selected, base_e, base_g, baseline, feasibility, reason, warnings)
    after_demand = thermal["thermal_demand_kwh"] if thermal else None
    assumptions = []
    for key in thermal_keys:
        row = RETROFIT_CATALOGUE[key]
        assumptions.append(row["assumption"])
        if row["effect_kind"] == "thermal_demand_reduction":
            after_demand *= 1 - row["fraction"]
    after_e, after_g = base_e, base_g
    if thermal:
        non_heat = dict(thermal["non_heating"])
        if "heat_pump" in selected:
            if thermal["kind"] == "heat_pump":
                return _unavailable_simulation(prop, selected, base_e, base_g, baseline, feasibility,
                    "A heat pump is already the recorded heating system; this retrofit cannot be applied again.", warnings)
            scop = prop.get("scop")
            if scop is None:
                return _unavailable_simulation(prop, selected, base_e, base_g, baseline, feasibility,
                    "scop is required to model heat-pump electricity use.", warnings)
            after_e = non_heat["electricity"] + after_demand / _number(scop, "scop", allow_zero=False)
            after_g = non_heat["gas"]
            assumptions.append("Heat pump substitutes for existing heating fuel; heating electricity = post-measure thermal demand / supplied SCOP.")
        elif thermal["kind"] == "gas":
            efficiency = _number(prop.get("boiler_efficiency", prop.get("heating_efficiency")), "boiler_efficiency", allow_zero=False)
            after_e = non_heat["electricity"]
            after_g = non_heat["gas"] + after_demand / efficiency
        elif thermal["kind"] == "heat_pump":
            scop = _number(prop.get("scop"), "scop", allow_zero=False)
            after_e = non_heat["electricity"] + after_demand / scop
            after_g = non_heat["gas"]
        else:
            efficiency = _number(prop.get("heating_efficiency", 1.0), "heating_efficiency", allow_zero=False)
            after_e = non_heat["electricity"] + after_demand / efficiency
            after_g = non_heat["gas"]
    if solar_selected:
        self_consumed, solar_warning = _solar_self_consumption(prop, energy, after_e)
        if self_consumed is None:
            return _unavailable_simulation(prop, selected, base_e, base_g, baseline, feasibility, solar_warning, warnings)
        after_e -= self_consumed
        assumptions.append("Solar reduces grid imports by measured/projected self-consumed generation only; export is not counted as avoided purchased electricity.")
        if solar_warning:
            warnings.append(solar_warning)
    after_e = max(0.0, after_e)
    after_g = max(0.0, after_g)
    after_carbon = _emissions(after_e, after_g, factors)
    e_saving, g_saving = base_e - after_e, base_g - after_g
    reduction = baseline["total_kg_co2e"] - after_carbon["total_kg_co2e"]
    if reduction < 0:
        warnings.append("Scenario increases annual emissions under the supplied factors; reduction is negative.")
    for key in selected:
        feasibility[key] = dict(feasibility[key])
    return {
        "status": "available", "property_id": prop.get("property_id"), "selected_retrofits": selected,
        "baseline": {"energy_use": {"electricity_kwh": base_e, "gas_kwh": base_g,
                                      "total_kwh": base_e + base_g}, "emissions": baseline},
        "after": {"energy_use": {"electricity_kwh": after_e, "gas_kwh": after_g,
                                  "total_kwh": after_e + after_g}, "emissions": after_carbon},
        "savings": {"electricity_kwh": e_saving, "gas_kwh": g_saving,
                    "net_energy_kwh": e_saving + g_saving,
                    "annual_carbon_reduction_kg_co2e": reduction},
        "feasibility": feasibility, "assumptions": assumptions, "warnings": warnings,
    }


def _unavailable_simulation(prop: Mapping[str, Any], selected: list[str], electricity: float | None,
                            gas: float | None, baseline: dict[str, Any], feasibility: dict[str, Any],
                            reason: str, warnings: list[str]) -> dict[str, Any]:
    warnings = list(warnings)
    if electricity is None:
        warnings.append("Annual electricity use is missing; it was not treated as zero.")
    if gas is None:
        warnings.append("Annual gas use is missing; it was not treated as zero.")
    return {
        "status": "unavailable", "reason": reason, "property_id": prop.get("property_id"),
        "selected_retrofits": selected,
        "baseline": {"energy_use": {"electricity_kwh": electricity, "gas_kwh": gas,
                                      "total_kwh": None if electricity is None or gas is None else electricity + gas},
                     "emissions": baseline},
        "after": None,
        "savings": {"electricity_kwh": None, "gas_kwh": None, "net_energy_kwh": None,
                    "annual_carbon_reduction_kg_co2e": None, "reason": reason},
        "feasibility": feasibility,
        "assumptions": [RETROFIT_CATALOGUE[k]["assumption"] for k in selected],
        "warnings": warnings,
    }


def rank_retrofits_by_carbon(property_data: Mapping[str, Any],
                             emission_factors: Mapping[str, Any]) -> dict[str, Any]:
    """Evaluate every not-known-installed measure and rank calculable options."""
    prop, _ = property_and_energy(property_data)
    options = {}
    for key in RETROFIT_CATALOGUE:
        feasibility = _feasibility(key, prop)
        if feasibility["status"] == "infeasible":
            options[key] = {"status": "unavailable", "reason": feasibility["reason"],
                            "feasibility": feasibility, "annual_carbon_reduction_kg_co2e": None}
            continue
        result = simulate_carbon_impact(property_data, [key], emission_factors)
        if result["status"] == "unavailable":
            options[key] = {"status": "unavailable", "reason": result["reason"],
                            "feasibility": feasibility, "annual_carbon_reduction_kg_co2e": None,
                            "warnings": result["warnings"], "assumptions": result["assumptions"]}
        else:
            options[key] = {"status": "available", "reason": None, "feasibility": feasibility,
                            "annual_carbon_reduction_kg_co2e": result["savings"]["annual_carbon_reduction_kg_co2e"],
                            "simulation": result}
    ranked = sorted(({"retrofit": k, **v} for k, v in options.items() if v["status"] == "available"),
                    key=lambda row: (-row["annual_carbon_reduction_kg_co2e"], row["retrofit"]))
    return {"status": "available" if ranked else "unavailable",
            "reason": None if ranked else "No retrofit has enough data for a carbon estimate.",
            "ranking": ranked,
            "unavailable_options": [{"retrofit": k, **v} for k, v in options.items() if v["status"] == "unavailable"],
            "methodology": "Single-retrofit deterministic screening estimates; midpoint catalogue assumptions; sorted by signed annual kg CO2e reduction.",
            "warnings": ["Indicative assumptions are not property-specific measured savings.",
                         "Feasibility marked conditional requires site confirmation before recommendation."]}
