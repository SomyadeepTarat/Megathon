import os
from pathlib import Path
from carbon_engine.engine import _feasibility, simulate_carbon_impact, calculate_baseline_carbon
from carbon_engine.emission_factors import load_emission_factors
from app.schemas.models import FactorSet, Heating
from app.schemas.engines import FeasibilityResult, FeasibilityItem, SimulationResult, FuelState, CarbonResult, EmissionFactor


class CalculationUnavailable(Exception):
    pass


def configured_factors():
    default = Path(__file__).resolve().parents[3] / 'Data/csv/emission_factors_2026.csv'
    path = os.getenv('GREENPRINT_EMISSION_FACTORS_FILE', str(default))
    if not path:
        return None
    return FactorSet.model_validate(load_emission_factors(Path(path)))


def factor_data(request=None):
    value = request.emission_factors if request is not None else None
    try:
        value = value or configured_factors()
    except (ValueError, OSError) as exc:
        raise CalculationUnavailable('Configured emissions factors are invalid or unreadable.') from exc
    if value is None:
        raise CalculationUnavailable('Documented electricity and gas emissions factors have not been supplied.')
    return value.model_dump(mode='json')


def engine_payload(request):
    prop = request.property.model_dump(mode='json')
    physical = prop.pop('physical_inputs')
    prop.update({key: value for key, value in physical.items()
                 if key not in ('provenance', 'proposed_heat_pump_type') and value is not None})
    if prop.get('heat_pump_installed') and prop.get('heating_system') is None:
        prop['heating_system'] = 'heat_pump'
    return {'property': prop, 'annual_energy': request.annual_energy.model_dump(mode='json')}


class P4RetrofitAdapter:
    version = 'p4-carbon-package-adapter-v1'

    def check_feasibility(self, request):
        prop = engine_payload(request)['property']
        items = []
        for measure in request.retrofits:
            item = _feasibility(measure, prop)
            field = {'heat_pump': 'heat_pump_compatible', 'smart_thermostat': 'controls_compatible'}.get(measure)
            if item['status'] != 'infeasible' and field and prop.get(field) is not True:
                item = {'status': 'infeasible' if prop.get(field) is False else 'conditional',
                        'reason': f'{field} is incompatible.' if prop.get(field) is False else f'{field} must be confirmed.'}
            if item['status'] == 'feasible' and measure == 'double_glazing' and prop.get('glazing') is None:
                item = {'status': 'conditional', 'reason': 'Existing glazing must be confirmed.'}
            if item['status'] == 'feasible' and measure == 'solar_panels' and prop.get('solar_installed') is None and prop.get('renewable_contribution') is None:
                item = {'status': 'conditional', 'reason': 'Existing solar installation status must be confirmed.'}
            items.append(FeasibilityItem(retrofit=measure, **item))
        return FeasibilityResult(status='available', items=items)

    def raw_simulation(self, request):
        try:
            factors = factor_data(request)
        except CalculationUnavailable:
            # Fuel changes do not depend on emission factors. Carbon is attached
            # as explicitly unavailable by the carbon adapter in this case.
            factors = None
        result = simulate_carbon_impact(engine_payload(request), request.retrofits, factors)
        if result['status'] != 'available':
            raise CalculationUnavailable(result.get('reason', 'P4 simulation unavailable'))
        return result

    def simulate_retrofits(self, request):
        result = self.raw_simulation(request)
        updated = request.property.model_copy(deep=True)
        warnings = list(result['warnings'])
        if 'heat_pump' in request.retrofits:
            updated.heat_pump_installed = True
            kind = updated.physical_inputs.proposed_heat_pump_type
            updated.heating_system = Heating(kind) if kind else None
            if kind is None:
                warnings.append('Heat pump installed in scenario, but proposed subtype is unknown; heating subscore unavailable.')
        if 'solar_panels' in request.retrofits:
            updated.solar_installed = True
            updated.renewable_contribution = None
            warnings.append('Solar installed in scenario; scoring contribution needs a supported mapping.')
        if 'double_glazing' in request.retrofits:
            updated.glazing = 'double'
        if 'smart_thermostat' in request.retrofits:
            updated.smart_thermostat_installed = True
            updated.smart_controls = 'advanced'
        if 'loft_insulation' in request.retrofits:
            updated.loft_insulation_installed = True
            warnings.append('Loft upgraded; whole-home insulation category is retained without an estimator.')
        from carbon_engine.retrofit_catalogue import RETROFIT_CATALOGUE, SEQUENTIAL_ORDER
        space = updated.physical_inputs.space_heating_demand_kwh
        legacy_space_demand = space is None and updated.physical_inputs.thermal_demand_kwh is not None and updated.physical_inputs.hot_water_demand_kwh is None and updated.physical_inputs.thermal_demand_scope not in ('space_heating_plus_hot_water', 'total')
        if legacy_space_demand:
            space = updated.physical_inputs.thermal_demand_kwh
        if space is not None:
            for measure in SEQUENTIAL_ORDER:
                if measure in request.retrofits and RETROFIT_CATALOGUE[measure]['effect_kind'] == 'space_heating_demand_reduction':
                    space *= 1 - RETROFIT_CATALOGUE[measure]['fraction']
            updated.physical_inputs.space_heating_demand_kwh = space
            if updated.physical_inputs.thermal_demand_scope == 'space_heating' or legacy_space_demand:
                updated.physical_inputs.thermal_demand_kwh = space
            elif updated.physical_inputs.thermal_demand_scope == 'space_heating_plus_hot_water' and updated.physical_inputs.hot_water_demand_kwh is not None:
                updated.physical_inputs.thermal_demand_kwh = space + updated.physical_inputs.hot_water_demand_kwh
        if 'solar_panels' in request.retrofits:
            updated.physical_inputs.solar_generation_kwh = result['after']['solar']['generation_kwh']
            updated.physical_inputs.solar_self_consumed_kwh = result['after']['solar']['self_consumed_kwh']
        if result['after'].get('physical_inputs'):
            for field, value in result['after']['physical_inputs'].items():
                setattr(updated.physical_inputs, field, value)
        updated.physical_inputs.provenance = {**updated.physical_inputs.provenance,
            'scenario': self.version}
        if request.retrofits:
            updated.physical_inputs.heating_energy_kwh = None
        costs = request.retrofit_costs
        cost = sum(costs[measure].amount_gbp for measure in request.retrofits) if all(measure in costs for measure in request.retrofits) else None
        if cost is None:
            warnings.append('Installation cost unavailable; P4 catalogue does not supply documented costs.')
        for key, value in request.property.physical_inputs.model_dump().items():
            if key != 'provenance' and value is not None and key not in request.property.physical_inputs.provenance:
                warnings.append(f'Physical input {key} has no per-field source metadata.')
        e_saving = request.annual_energy.electricity_kwh - result['after']['energy_use']['electricity_kwh']
        g_saving = request.annual_energy.gas_kwh - result['after']['energy_use']['gas_kwh']
        bill = None
        bill_reason = None
        if request.electricity_tariff_gbp_per_kwh is None or request.gas_tariff_gbp_per_kwh is None:
            bill_reason = 'Both electricity and gas tariffs are required to calculate annual bill savings.'
        else:
            bill = e_saving * request.electricity_tariff_gbp_per_kwh + g_saving * request.gas_tariff_gbp_per_kwh
        payback = None
        payback_reason = None
        if cost is None:
            payback_reason = 'Documented installation cost is unavailable.'
        elif bill is None:
            payback_reason = bill_reason
        elif bill <= 0:
            payback_reason = 'Annual bill savings are not positive.'
        else:
            payback = cost / bill
        return SimulationResult(updated_property=updated, after=FuelState(**{
            fuel: result['after']['energy_use'][fuel] for fuel in ('electricity_kwh', 'gas_kwh')}),
            applied_retrofits=request.retrofits, installation_cost_gbp=cost,
            methodology_version=self.version, assumptions=result['assumptions'], warnings=warnings,
            annual_bill_savings_gbp=bill, bill_savings_reason=bill_reason,
            simple_payback_years=payback, payback_reason=payback_reason)


class P4CarbonAdapter:
    def __init__(self, factors=None):
        self.factors = factors

    def calculate_carbon(self, energy):
        try:
            factors = self.factors.model_dump(mode='json') if self.factors else factor_data()
        except CalculationUnavailable as exc:
            return CarbonResult(status='unavailable', reason=str(exc))
        before = calculate_baseline_carbon({'annual_energy': energy.baseline.model_dump()}, factors)
        after = calculate_baseline_carbon({'annual_energy': energy.after.model_dump()}, factors)
        return CarbonResult(status='available', reduction_kg_co2e=before['emissions']['total_kg_co2e']-after['emissions']['total_kg_co2e'],
            factors=[EmissionFactor.model_validate(item) for item in factors.values()])

    def baseline(self, request):
        try:
            return calculate_baseline_carbon(engine_payload(request), factor_data(request))['emissions']
        except CalculationUnavailable as exc:
            return {'status': 'unavailable', 'reason': str(exc)}
