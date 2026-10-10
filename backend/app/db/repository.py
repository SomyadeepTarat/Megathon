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
        self._source_properties = {row['property_id']: dict(row) for row in properties}
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
        self._source_monthly_energy = {
            identifier: [dict(row) for _, row in rows]
            for identifier, rows in grouped.items()
        }
        heating = {'Old gas boiler': 'old_gas_boiler', 'Modern gas boiler': 'modern_gas_boiler',
                   'Electric resistance': 'electric_resistance'}
        self._records = {}
        for row in properties:
            identifier = row['property_id']
            if row['data_status'] not in ('synthetic', 'observed', 'estimated', 'imported'):
                raise ValueError('Property data_status must declare provenance')
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
                    if reading['reading_status'] not in ('synthetic', 'missing', 'observed', 'estimated', 'imported'):
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
                solar_installed=solar,
                heat_pump_installed=row['heating'] == 'Heat pump',
                renewable_contribution=renewable,
                smart_controls='advanced' if row['smart_controls'] == 'true' else 'none',
                current_property_value_gbp=row['current_value_estimate_gbp'],
                provenance={'record': row['data_status'], 'source': str(properties_path),
                            'source_heating': row['heating'], 'solar_installed': row['solar'],
                            'generation_seed': row.get('generation_seed', ''), 'customer_id': row.get('customer_id', '')})
            statuses = {reading['reading_status'] for _, reading in monthly if reading['reading_status'] != 'missing'}
            quality = 'synthetic' if statuses == {'synthetic'} else 'estimated' if statuses & {'synthetic', 'estimated'} else 'observed'
            if all(value is None for value in totals.values()):
                quality = 'missing'
            annual = AnnualEnergy(
                electricity_kwh=totals['electricity'], gas_kwh=totals['gas'],
                quality=quality,
                method=f'Sum of 12 monthly purchased-energy readings for {year}; incomplete fuel totals remain null',
                electricity_months_covered=coverage['electricity'], gas_months_covered=coverage['gas'],
                warnings=warnings + ['Confirm alignment of the property snapshot and energy period; see source methodology.'])
            self._records[identifier] = PropertyRecord(property=prop, annual_energy=annual, benchmark=benchmark,
                dataset_kind=row['data_status'], dataset_source='Data/csv/properties.csv and Data/csv/energy_usage.csv')

    def list_properties(self):
        return [record.model_copy(deep=True) for record in self._records.values()]

    def load_property(self, property_id):
        if property_id not in self._records:
            raise KeyError(property_id)
        return self._records[property_id].model_copy(deep=True)

    @classmethod
    def from_project_root(cls, project_root=None):
        """Load the source CSVs using paths anchored at the project root."""
        root = Path(project_root) if project_root is not None else Path(__file__).resolve().parents[3]
        return cls(root / 'Data/csv/properties.csv', root / 'Data/csv/energy_usage.csv')

    def load_combined_record(self, property_id):
        """Return source property fields, annual energy sums and raw monthly rows.

        Additional monthly energy columns ending in ``_kwh`` are summed
        independently. Existing annual purchased electricity/gas and their
        metadata are kept from the typed record. Identifiers, categories,
        statuses and physical parameters are not aggregated. Columns absent
        from the source remain absent from ``annual_energy``.
        """
        if property_id not in self._source_properties:
            raise KeyError(property_id)
        record = self.load_property(property_id).model_dump(mode='json')
        monthly = self._source_monthly_energy[property_id]
        energy_fields = {
            name for row in monthly for name in row
            if name.endswith('_kwh') and name not in ('electricity_kwh', 'gas_kwh')
        }
        monthly_energy_totals = {
            name: sum(float(row[name]) for row in monthly)
            for name in sorted(energy_fields)
        }
        # Keep the existing PropertyRecord contract and purchased-energy
        # annualization, while adding every source monthly quantity separately.
        record['annual_energy'].update(monthly_energy_totals)
        record['property'] = {
            name: (None if value == '' else value)
            for name, value in self._source_properties[property_id].items()
        }
        record['monthly_energy'] = [dict(row) for row in monthly]
        return record


_project_csv_repository = None


def load_property_energy_data(property_id):
    """Load the combined source record for a property ID from project CSVs.

    The CSV repository is initialized once and reused for later property IDs.
    The returned dictionary contains source property fields, annual energy,
    benchmark and dataset metadata, plus the original monthly energy rows.
    """
    global _project_csv_repository
    if _project_csv_repository is None:
        _project_csv_repository = CsvPropertyRepository.from_project_root()
    return _project_csv_repository.load_combined_record(property_id)


class EditableRepository:
    def __init__(self, source):
        from threading import RLock
        self.source = source
        self.overrides = {}
        self.lock = RLock()

    def list_properties(self):
        with self.lock:
            rows = {row.property.property_id: row for row in self.source.list_properties()}
            rows.update(self.overrides)
            return [row.model_copy(deep=True) for row in rows.values()]

    def load_property(self, property_id):
        with self.lock:
            if property_id in self.overrides:
                return self.overrides[property_id].model_copy(deep=True)
            return self.source.load_property(property_id)

    def save_property(self, row):
        with self.lock:
            self.overrides[row.property.property_id] = row.model_copy(deep=True)
            return row.model_copy(deep=True)
