"""Create explicit synthetic demo scenarios; never modify the supplied CSV homes."""
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'backend'))
sys.path.insert(0, str(ROOT))
from app.db.repository import CsvPropertyRepository
from app.schemas.engines import PropertyRecord
from app.schemas.models import RetrofitCost


def main():
    records = CsvPropertyRepository.from_project_root(ROOT).list_properties()[:10]
    catalogue = json.loads((ROOT / 'backend/catalog.json').read_text())
    names = ['loft_insulation', 'heat_pump', 'solar_panels', 'double_glazing', 'smart_thermostat']
    source = 'Curated synthetic demo assumptions; not survey evidence, market tariffs or contractor quotes'
    costs = {name: {'amount_gbp': entry['cost'], 'source': 'backend/catalog.json; illustrative team cost assumption', 'date': '2026-10-11'}
             for name, entry in zip(names, catalogue)}
    for record in records:
        p = record.property
        p.property_id = 'DEMO-' + p.property_id
        p.roof_suitable_for_loft = p.property_type != 'flat'
        p.roof_suitable_for_solar = p.property_type != 'flat'
        p.heat_pump_compatible = p.property_type != 'flat'
        p.controls_compatible = True
        p.loft_insulation_installed = p.insulation == 'good'
        if p.heating_system in ('old_gas_boiler', 'modern_gas_boiler'):
            p.physical_inputs.scop = 3
            p.physical_inputs.hot_water_cop = 2.5
            p.physical_inputs.proposed_heat_pump_type = 'air_source_heat_pump'
        if p.solar_installed is False and p.roof_suitable_for_solar:
            p.physical_inputs.proposed_solar_generation_kwh = 3000
            p.physical_inputs.proposed_solar_self_consumption_fraction = .45
        p.provenance.update(record='synthetic', source='Data/csv/properties.csv', demo_assumptions=source)
        p.physical_inputs.provenance['demo_assumptions'] = source
        for key, value in p.physical_inputs.model_dump().items():
            if key == 'provenance' or value is None:
                continue
            assumed = key.startswith('proposed_') or key in ('scop', 'hot_water_cop') and p.heating_system in ('old_gas_boiler', 'modern_gas_boiler')
            p.physical_inputs.provenance[key] = source if assumed else 'Synthetic source columns in Data/csv/properties.csv; Data/relations/energy_methodology.md'
        record.dataset_source = source + '; base data from Data/csv/properties.csv and energy_usage.csv'
        record.retrofit_costs = {key: RetrofitCost.model_validate(value) for key, value in costs.items()}
        record.electricity_tariff_gbp_per_kwh = .25
        record.gas_tariff_gbp_per_kwh = .06
    # Round-trip validates every generated API input before publishing it.
    rows = [PropertyRecord.model_validate(record.model_dump()).model_dump(mode='json') for record in records]
    output = ROOT / 'backend/data/curated_demo_properties.json'
    output.write_text(json.dumps(rows, indent=2) + '\n')
    print(f'Prepared {len(rows)} labelled synthetic scenarios: {output}')

if __name__ == '__main__':
    main()
