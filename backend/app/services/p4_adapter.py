import os
from pathlib import Path
from carbon_engine.engine import _feasibility, simulate_carbon_impact, calculate_baseline_carbon
from carbon_engine.emission_factors import load_emission_factors
from app.schemas.models import FactorSet, Heating
from app.schemas.engines import FeasibilityResult, FeasibilityItem, SimulationResult, FuelState, CarbonResult, EmissionFactor


class CalculationUnavailable(Exception):
    pass


def configured_factors():
    path = os.getenv('GREENPRINT_EMISSION_FACTORS_FILE')
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
        result = simulate_carbon_impact(engine_payload(request), request.retrofits, factor_data(request))
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
            updated.smart_controls = 'advanced'
        if 'loft_insulation' in request.retrofits:
            updated.loft_insulation_installed = True
            warnings.append('Loft upgraded; whole-home insulation category is retained without an estimator.')
        demand = updated.physical_inputs.thermal_demand_kwh
        if demand is not None:
            from carbon_engine.retrofit_catalogue import RETROFIT_CATALOGUE, SEQUENTIAL_ORDER
            for measure in SEQUENTIAL_ORDER:
                if measure in request.retrofits and RETROFIT_CATALOGUE[measure]['effect_kind'] == 'thermal_demand_reduction':
                    demand *= 1 - RETROFIT_CATALOGUE[measure]['fraction']
            updated.physical_inputs.thermal_demand_kwh = demand
        if request.retrofits:
            updated.physical_inputs.heating_energy_kwh = None
        costs = request.retrofit_costs
        cost = sum(costs[measure].amount_gbp for measure in request.retrofits) if all(measure in costs for measure in request.retrofits) else None
        if cost is None:
            warnings.append('Installation cost unavailable; P4 catalogue does not supply documented costs.')
        for key, value in request.property.physical_inputs.model_dump().items():
            if key != 'provenance' and value is not None and key not in request.property.physical_inputs.provenance:
                warnings.append(f'Physical input {key} has no per-field source metadata.')
        return SimulationResult(updated_property=updated, after=FuelState(**{
            fuel: result['after']['energy_use'][fuel] for fuel in ('electricity_kwh', 'gas_kwh')}),
            applied_retrofits=request.retrofits, installation_cost_gbp=cost,
            methodology_version=self.version, assumptions=result['assumptions'], warnings=warnings)


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
