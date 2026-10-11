"""Reject contradictory observations rather than choosing an input silently."""
import math


def conflicting_inputs(prop):
    p = prop.physical_inputs
    conflicts = []
    heat_pump = prop.heating_system in ('air_source_heat_pump', 'ground_source_heat_pump')
    if prop.heating_system is not None and prop.heat_pump_installed is not None and heat_pump != prop.heat_pump_installed:
        conflicts.append('heating_system and heat_pump_installed')
    if prop.solar_installed is False and any((value or 0) > 0 for value in (p.solar_generation_kwh, p.solar_self_consumed_kwh)):
        conflicts.append('solar_installed and existing solar generation/self-consumption')
    if prop.smart_thermostat_installed is True and prop.smart_controls == 'none':
        conflicts.append('smart_thermostat_installed and smart_controls')

    def compare(left, right, names):
        # Twelve rounded monthly readings can differ by up to 0.06 kWh.
        if left is not None and right is not None and not math.isclose(left, right, abs_tol=.06, rel_tol=1e-6):
            conflicts.append(names)

    if p.thermal_demand_scope == 'space_heating':
        compare(p.thermal_demand_kwh, p.space_heating_demand_kwh, 'thermal_demand_kwh and space_heating_demand_kwh')
    elif p.thermal_demand_scope in ('total', 'space_heating_plus_hot_water') and p.space_heating_demand_kwh is not None and p.hot_water_demand_kwh is not None:
        compare(p.thermal_demand_kwh, p.space_heating_demand_kwh + p.hot_water_demand_kwh, 'thermal_demand_kwh and space/hot-water demand')
    if prop.heating_system in ('old_gas_boiler', 'modern_gas_boiler'):
        conversion, space, water = p.boiler_efficiency, p.gas_space_heating_kwh, p.gas_hot_water_kwh
    elif heat_pump:
        conversion, space, water = p.scop, p.electric_space_heating_kwh, p.electric_hot_water_kwh
    elif prop.heating_system == 'electric_resistance':
        conversion, space, water = p.electric_resistance_efficiency, p.electric_space_heating_kwh, p.electric_hot_water_kwh
    else:
        conversion, space, water = None, None, None
    if conversion is not None:
        compare(p.space_heating_demand_kwh, None if space is None else space * conversion, 'space_heating_demand_kwh and heating fuel component/efficiency')
        water_conversion = p.hot_water_cop if heat_pump else conversion
        if water_conversion is not None:
            compare(p.hot_water_demand_kwh, None if water is None else water * water_conversion, 'hot_water_demand_kwh and hot-water fuel component/efficiency')
    return conflicts
