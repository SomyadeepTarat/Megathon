import json
from pathlib import Path

import pytest

from carbon_engine import (calculate_baseline_carbon, rank_retrofits_by_carbon,
                           simulate_carbon_impact)

ROOT = Path(__file__).resolve().parents[2]
DEMO = json.loads((ROOT / "backend/data/demo_properties.json").read_text())

# Test-only arithmetic fixtures. Not published emission factors and never
# used as runtime defaults.
FACTORS = {
    "electricity": {"fuel": "electricity", "kg_co2e_per_kwh": 0.2,
                    "source": "TEST FIXTURE ONLY", "source_year": 2026,
                    "accounting_boundary": "test boundary", "version": "test-v1"},
    "gas": {"fuel": "gas", "kg_co2e_per_kwh": 0.18,
            "source": "TEST FIXTURE ONLY", "source_year": 2026,
            "accounting_boundary": "test boundary", "version": "test-v1"},
}


def property_with_heat_inputs():
    data = json.loads(json.dumps(DEMO[0]))
    data["property"].update({
        "boiler_efficiency": 0.8,
        "scop": 4.0,
        "thermal_demand_kwh": 8000,
        "roof_suitable_for_loft": True,
        "roof_suitable_for_solar": True,
        "solar_generation_kwh": 1000,
        "solar_self_consumption_fraction": 0.5,
    })
    return data


def test_baseline_uses_project_demo_and_separates_fuels():
    result = calculate_baseline_carbon(DEMO[0], FACTORS)
    assert result["status"] == "available"
    assert result["energy_use"] == {"electricity_kwh": 4800.0, "gas_kwh": 12000.0,
                                    "total_kwh": 16800.0}
    assert result["emissions"]["electricity_kg_co2e"] == 960
    assert result["emissions"]["gas_kg_co2e"] == 2160
    assert result["emissions"]["total_kg_co2e"] == 3120


def test_missing_fuel_is_not_zero():
    data = json.loads(json.dumps(DEMO[0]))
    data["annual_energy"]["gas_kwh"] = None
    result = calculate_baseline_carbon(data, FACTORS)
    assert result["status"] == "unavailable"
    assert result["energy_use"]["gas_kwh"] is None
    assert result["emissions"]["gas_kg_co2e"] is None
    assert result["emissions"]["total_kg_co2e"] is None
    assert any("not treated as zero" in warning for warning in result["warnings"])


def test_known_zero_gas_is_calculated_as_zero():
    result = calculate_baseline_carbon(DEMO[2], FACTORS)
    assert result["status"] == "available"
    assert result["energy_use"]["gas_kwh"] == 0
    assert result["emissions"]["gas_kg_co2e"] == 0
    assert result["emissions"]["total_kg_co2e"] == 1100


def test_factor_without_provenance_is_rejected():
    with pytest.raises(ValueError, match="requires source"):
        calculate_baseline_carbon(DEMO[0], {**FACTORS, "gas": 0.18})


def test_missing_thermal_data_makes_retrofit_unavailable():
    result = simulate_carbon_impact(DEMO[0], ["loft_insulation"], FACTORS)
    assert result["status"] == "unavailable"
    assert result["after"] is None
    assert result["savings"]["annual_carbon_reduction_kg_co2e"] is None
    assert "Heating demand is missing" in result["reason"]


def test_heat_pump_switches_gas_heating_to_scop_electricity():
    result = simulate_carbon_impact(property_with_heat_inputs(), ["heat_pump"], FACTORS)
    assert result["status"] == "available"
    assert result["after"]["energy_use"]["electricity_kwh"] == 6800
    assert result["after"]["energy_use"]["gas_kwh"] == 2000
    assert result["savings"]["electricity_kwh"] == -2000
    assert result["savings"]["gas_kwh"] == 10000
    assert result["savings"]["annual_carbon_reduction_kg_co2e"] == 1400


def test_solar_uses_self_consumption_and_does_not_change_demand():
    result = simulate_carbon_impact(property_with_heat_inputs(), ["solar_panels"], FACTORS)
    assert result["status"] == "available"
    assert result["after"]["energy_use"]["electricity_kwh"] == 4300
    assert result["after"]["energy_use"]["gas_kwh"] == 12000
    assert result["savings"]["annual_carbon_reduction_kg_co2e"] == pytest.approx(100)


def test_solar_without_generation_or_self_consumption_is_unavailable():
    data = property_with_heat_inputs()
    del data["property"]["solar_generation_kwh"]
    del data["property"]["solar_self_consumption_fraction"]
    result = simulate_carbon_impact(data, ["solar_panels"], FACTORS)
    assert result["status"] == "unavailable"
    assert "generation and self-consumption data are missing" in result["reason"]


def test_combined_measures_apply_thermal_effects_sequentially_then_hp_and_solar():
    data = property_with_heat_inputs()
    result = simulate_carbon_impact(data,
        ["solar_panels", "heat_pump", "double_glazing", "loft_insulation"], FACTORS)
    assert result["status"] == "available"
    assert result["after"]["energy_use"]["electricity_kwh"] == pytest.approx(5830)
    # Gas left after the switch is the preserved non-heating load. Envelope
    # measures change heat-pump electricity but cannot affect that gas load.
    assert result["after"]["energy_use"]["gas_kwh"] == pytest.approx(2000)
    assert result["after"]["energy_use"]["total_kwh"] == pytest.approx(7830)
    assert len(result["assumptions"]) == 5


def test_existing_retrofit_is_not_recommended_or_applied():
    data = property_with_heat_inputs()
    data["property"]["glazing"] = "double"
    result = simulate_carbon_impact(data, ["double_glazing"], FACTORS)
    assert result["status"] == "unavailable"
    assert result["feasibility"]["double_glazing"]["status"] == "infeasible"
    ranking = rank_retrofits_by_carbon(data, FACTORS)
    assert "double_glazing" in {item["retrofit"] for item in ranking["unavailable_options"]}


def test_rank_separates_missing_data_options_and_is_deterministic():
    data = property_with_heat_inputs()
    first = rank_retrofits_by_carbon(data, FACTORS)
    second = rank_retrofits_by_carbon(data, FACTORS)
    assert first == second
    assert first["ranking"]
    assert "heat_pump" in {item["retrofit"] for item in first["ranking"]}
    assert "smart_thermostat" in {item["retrofit"] for item in first["ranking"]}


def test_results_are_json_serializable():
    for result in (calculate_baseline_carbon(DEMO[0], FACTORS),
                   simulate_carbon_impact(property_with_heat_inputs(), ["heat_pump"], FACTORS),
                   rank_retrofits_by_carbon(property_with_heat_inputs(), FACTORS)):
        json.dumps(result, allow_nan=False)
