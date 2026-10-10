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
        "thermal_demand_scope": "space_heating",
        "space_heating_demand_kwh": 8000,
        "hot_water_demand_kwh": 0,
        "heat_pump_compatible": True,
        "heat_pump_installed": False,
        "loft_insulation_installed": False,
        "solar_installed": False,
        "solar": False,
        "roof_suitable_for_loft": True,
        "roof_suitable_for_solar": True,
        "glazing": "single",
        "smart_controls": "none",
        "controls_compatible": True,
        "proposed_solar_generation_kwh": 1000,
        "proposed_solar_self_consumption_fraction": 0.5,
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
    data = json.loads(json.dumps(DEMO[0]))
    data["property"].update(loft_insulation_installed=False, roof_suitable_for_loft=True)
    result = simulate_carbon_impact(data, ["loft_insulation"], FACTORS)
    assert result["status"] == "unavailable"
    assert result["after"] is None
    assert result["savings"]["annual_carbon_reduction_kg_co2e"] is None
    assert "Space-heating demand is missing" in result["reason"]


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
    del data["property"]["proposed_solar_generation_kwh"]
    del data["property"]["proposed_solar_self_consumption_fraction"]
    result = simulate_carbon_impact(data, ["solar_panels"], FACTORS)
    assert result["status"] == "unavailable"
    assert "Proposed solar generation is missing" in result["reason"]


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
    assert len(result["assumptions"]) == 6


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


def test_unknown_and_explicitly_incompatible_eligibility_stay_distinct():
    data = property_with_heat_inputs()
    data["property"].pop("roof_suitable_for_loft")
    unknown = simulate_carbon_impact(data, ["loft_insulation"], FACTORS)
    assert unknown["feasibility"]["loft_insulation"]["status"] == "conditional"
    data["property"]["roof_suitable_for_loft"] = False
    blocked = simulate_carbon_impact(data, ["loft_insulation"], FACTORS)
    assert blocked["feasibility"]["loft_insulation"]["status"] == "infeasible"
    data["property"].update(roof_suitable_for_loft=True, loft_insulation_installed=False, insulation="good")
    assert simulate_carbon_impact(data, ["loft_insulation"], FACTORS)["feasibility"]["loft_insulation"]["status"] == "infeasible"


def test_space_heat_reductions_do_not_change_hot_water_demand():
    data = property_with_heat_inputs()
    data["property"].update(space_heating_demand_kwh=8000, hot_water_demand_kwh=2000,
                            thermal_demand_kwh=10000, thermal_demand_scope="space_heating_plus_hot_water",
                            gas_space_heating_kwh=10000, gas_hot_water_kwh=2500,
                            base_appliance_electricity_kwh=4800)
    data["annual_energy"]["gas_kwh"] = 12500
    result = simulate_carbon_impact(data, ["loft_insulation"], FACTORS)
    assert result["status"] == "available"
    # Space heat drops 15%; hot water remains 2,000 thermal kWh.
    assert result["after"]["energy_use"]["gas_kwh"] == pytest.approx(11000)


def test_solar_caps_self_consumption_and_never_uses_existing_generation_as_proposal():
    data = property_with_heat_inputs()
    data["property"].update(proposed_solar_generation_kwh=10000,
                            proposed_solar_self_consumed_kwh=9000)
    result = simulate_carbon_impact(data, ["solar_panels"], FACTORS)
    assert result["after"]["solar"] == {"generation_kwh": 10000, "self_consumed_kwh": 4800, "exported_kwh": 5200}
    data["property"].pop("proposed_solar_generation_kwh")
    data["property"].pop("proposed_solar_self_consumed_kwh")
    data["property"]["solar_generation_kwh"] = 10000
    result = simulate_carbon_impact(data, ["solar_panels"], FACTORS)
    assert result["status"] == "unavailable"


def test_energy_simulation_survives_missing_production_factors():
    result = simulate_carbon_impact(property_with_heat_inputs(), ["heat_pump"], None)
    assert result["status"] == "available"
    assert result["after"]["energy_use"]["gas_kwh"] == 2000
    assert result["after"]["emissions"]["status"] == "unavailable"
    assert result["savings"]["annual_carbon_reduction_kg_co2e"] is None


def test_missing_boiler_scop_and_hot_water_cop_never_get_defaulted():
    data = property_with_heat_inputs()
    data["property"].pop("boiler_efficiency")
    assert "boiler_efficiency is required" in simulate_carbon_impact(data, ["loft_insulation"], FACTORS)["reason"]
    data = property_with_heat_inputs()
    data["property"].pop("scop")
    assert "SCOP is required" in simulate_carbon_impact(data, ["heat_pump"], FACTORS)["reason"]
    data = property_with_heat_inputs()
    data["property"].pop("hot_water_demand_kwh")
    assert "Hot-water demand is missing" in simulate_carbon_impact(data, ["heat_pump"], FACTORS)["reason"]
    data = property_with_heat_inputs()
    data["property"].update(hot_water_demand_kwh=2000)
    data["annual_energy"]["gas_kwh"] = 12500
    assert "Hot-water COP is required" in simulate_carbon_impact(data, ["heat_pump"], FACTORS)["reason"]


def test_signed_carbon_reduction_can_be_negative():
    data = property_with_heat_inputs()
    factors = {**FACTORS, "electricity": {**FACTORS["electricity"], "kg_co2e_per_kwh": 2.0}}
    result = simulate_carbon_impact(data, ["heat_pump"], factors)
    assert result["savings"]["annual_carbon_reduction_kg_co2e"] < 0


def test_results_are_json_serializable():
    for result in (calculate_baseline_carbon(DEMO[0], FACTORS),
                   simulate_carbon_impact(property_with_heat_inputs(), ["heat_pump"], FACTORS),
                   rank_retrofits_by_carbon(property_with_heat_inputs(), FACTORS)):
        json.dumps(result, allow_nan=False)


def test_nested_backend_physical_inputs_are_accepted_without_mutating_record():
    from app.db.repository import CsvPropertyRepository
    record = CsvPropertyRepository.from_project_root(ROOT).load_property('P00001')
    original = record.model_dump(mode='json')
    record.property.roof_suitable_for_loft = True
    record.property.loft_insulation_installed = False
    original_space = record.property.physical_inputs.space_heating_demand_kwh
    result = simulate_carbon_impact(record, ['loft_insulation'], FACTORS)
    assert result['status'] == 'available'
    assert result['baseline']['energy_use']['gas_kwh'] == record.annual_energy.gas_kwh
    assert original['property']['physical_inputs']['scop'] is None
    assert record.property.physical_inputs.scop is None
    assert record.property.physical_inputs.space_heating_demand_kwh == original_space
