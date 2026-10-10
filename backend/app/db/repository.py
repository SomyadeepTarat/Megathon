import json
from pathlib import Path
from app.schemas.engines import PropertyRecord


class JsonPropertyRepository:
    def __init__(self, path: Path):
        records = [PropertyRecord.model_validate(row) for row in json.loads(path.read_text())]
        self._records = {row.property.property_id: row for row in records}
        if len(self._records) != len(records):
            raise ValueError('Duplicate property IDs in repository')

    def list_properties(self):
        return [row.model_copy(deep=True) for row in self._records.values()]

    def load_property(self, property_id):
        if property_id not in self._records:
            raise KeyError(property_id)
        return self._records[property_id].model_copy(deep=True)


class CsvPropertyRepository:
    def __init__(self, properties_path: Path, energy_path: Path):
        import csv
        from datetime import datetime
        from decimal import Decimal
        from app.schemas.models import Property, AnnualEnergy, Benchmark, Heating

        with properties_path.open(newline='') as stream:
            properties = list(csv.DictReader(stream))
        with energy_path.open(newline='') as stream:
            readings = list(csv.DictReader(stream))
        ids = [row['property_id'] for row in properties]
        if len(set(ids)) != len(ids):
            raise ValueError('Duplicate property IDs in CSV')
        grouped = {identifier: [] for identifier in ids}
        keys = set()
        for row in readings:
            identifier = row['property_id']
            if identifier not in grouped:
                raise ValueError(f'Unknown energy property ID: {identifier}')
            month = datetime.strptime(row['month'], '%Y-%m')
            key = (identifier, month.year, month.month)
            if key in keys:
                raise ValueError(f'Duplicate energy month: {key}')
            keys.add(key)
            grouped[identifier].append((month, row))
        heating = {'Old gas boiler': 'old_gas_boiler', 'Modern gas boiler': 'modern_gas_boiler',
                   'Electric resistance': 'electric_resistance'}
        self._records = {}
        for row in properties:
            identifier = row['property_id']
            if row['data_status'] != 'synthetic':
                raise ValueError('This dataset adapter requires declared synthetic properties')
            if row['solar'] not in ('true', 'false') or row['smart_controls'] not in ('true', 'false'):
                raise ValueError('Invalid property boolean')
            warnings = []
            system = row.get('heating_system', '').strip() or heating.get(row['heating'])
            if system is not None and system not in {value.value for value in Heating}:
                raise ValueError(f'Unknown heating_system: {system}')
            if system is None:
                if row['heating'] != 'Heat pump':
                    raise ValueError(f'Unknown heating category: {row["heating"]}')
                warnings.append('Heat pump recorded, but air-source/ground-source subtype is unknown.')
            solar = row['solar'] == 'true'
            renewable = row.get('renewable_contribution', '').strip() or (None if solar else 'none')
            if solar and renewable is None:
                warnings.append('Solar is present, but contribution category is not supplied.')
            if not solar and renewable not in (None, 'none'):
                raise ValueError('Renewable contribution contradicts solar installation flag')
            benchmark = None
            benchmark_fields = ['benchmark_property_type', 'benchmark_intensity_kwh_m2_year',
                                'benchmark_source', 'benchmark_methodology']
            benchmark_values = [row.get(field, '').strip() for field in benchmark_fields]
            if any(benchmark_values):
                if not all(benchmark_values):
                    raise ValueError('Incomplete benchmark metadata in property CSV')
                benchmark = Benchmark(property_type=benchmark_values[0],
                                      intensity_kwh_m2_year=benchmark_values[1],
                                      source=benchmark_values[2], methodology=benchmark_values[3])
                if row.get('benchmark_data_status') == 'synthetic':
                    warnings.append('Score uses a synthetic reference benchmark, not an official consumption standard.')
            if row.get('heating_system_status', '').startswith(('synthetic', 'derived_from_synthetic')):
                warnings.append('Heating subtype is a disclosed synthetic modeling input, not survey evidence.')
            monthly = grouped[identifier]
            years = {month.year for month, _ in monthly}
            if len(years) > 1:
                raise ValueError('Select a single calendar year for annualization')
            totals, coverage = {}, {}
            for fuel in ('electricity', 'gas'):
                values = []
                for _, reading in monthly:
                    if reading['reading_status'] not in ('synthetic', 'missing'):
                        raise ValueError('Unsupported reading provenance')
                    raw = reading[f'{fuel}_kwh'].strip()
                    if raw and reading['reading_status'] != 'missing':
                        value = Decimal(raw)
                        if not value.is_finite() or value < 0:
                            raise ValueError('Energy values must be finite and nonnegative')
                        values.append(value)
                coverage[fuel] = len(values)
                totals[fuel] = float(sum(values)) if len(values) == 12 else None
                if len(values) != 12:
                    warnings.append(f'{fuel}: {len(values)}/12 months; annual total unavailable.')
            year = next(iter(years)) if years else None
            prop = Property(
                property_id=identifier, property_type=row['property_type'].lower().replace('-', '_'),
                region=row['region'], floor_area_m2=row['floor_area_m2'],
                property_age_years=row['age'], bedrooms=row['bedrooms'], energy_rating=row['energy_rating'],
                insulation=row['insulation'].lower(), heating_system=system, glazing=row['glazing'].lower(),
                renewable_contribution=renewable,
                smart_controls='advanced' if row['smart_controls'] == 'true' else 'none',
                current_property_value_gbp=row['current_value_estimate_gbp'],
                provenance={'record': 'synthetic', 'source': str(properties_path),
                            'source_heating': row['heating'], 'solar_installed': row['solar'],
                            'generation_seed': row['generation_seed'], 'customer_id': row['customer_id']})
            annual = AnnualEnergy(
                electricity_kwh=totals['electricity'], gas_kwh=totals['gas'],
                quality='synthetic' if any(value is not None for value in totals.values()) else 'missing',
                method=f'Sum of 12 monthly purchased-energy readings for {year}; incomplete fuel totals remain null',
                electricity_months_covered=coverage['electricity'], gas_months_covered=coverage['gas'],
                warnings=warnings + ['Property snapshot and energy year differ; see dataset methodology.'])
            self._records[identifier] = PropertyRecord(property=prop, annual_energy=annual, benchmark=benchmark,
                dataset_kind='synthetic', dataset_source='Data/csv/properties.csv and Data/csv/energy_usage.csv')

    def list_properties(self):
        return [record.model_copy(deep=True) for record in self._records.values()]

    def load_property(self, property_id):
        if property_id not in self._records:
            raise KeyError(property_id)
        return self._records[property_id].model_copy(deep=True)
