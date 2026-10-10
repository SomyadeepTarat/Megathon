"""Valuation input checks shared by HTTP orchestration and ML inference."""
import math


def missing(value):
    if value is None or isinstance(value, str) and not value.strip():
        return True
    if isinstance(value, (int, float)):
        return not math.isfinite(value)
    return False


def normalize_property(state):
    row = state.model_dump(mode='json') if hasattr(state, 'model_dump') else dict(state or {})
    for target, aliases in {
        'floor_area': ['floor_area_m2'], 'age': ['property_age_years'],
        'baseline_value': ['current_property_value_gbp', 'current_value_estimate_gbp',
                           'current_value_estimate', 'baseline_value_gbp', 'value_before'],
    }.items():
        if missing(row.get(target)):
            row[target] = next((row[a] for a in aliases if not missing(row.get(a))), None)
    return row


def impact_input_reason(baseline, scenario):
    baseline, scenario = normalize_property(baseline), normalize_property(scenario)
    absent = []
    for label, row in [('baseline', baseline), ('scenario', scenario)]:
        for field, name in [('floor_area', 'floor area'), ('region', 'region'), ('property_type', 'property type')]:
            if missing(row.get(field)):
                absent.append(f'{label} {name}')
    if missing(baseline.get('baseline_value')):
        absent.append('current baseline value')
    # The current impact model uses recorded/projected EPC as its energy input.
    for label, row in [('baseline', baseline), ('scenario', scenario)]:
        if missing(row.get('energy_rating')):
            absent.append(f'{label} energy rating')
    if absent:
        return f"Insufficient property details provided (missing {', '.join(absent)}). Value impact cannot be estimated."
    for field in ['floor_area', 'baseline_value']:
        states = [baseline, scenario] if field == 'floor_area' else [baseline]
        for row in states:
            try:
                valid = math.isfinite(float(row[field])) and float(row[field]) > 0
            except (TypeError, ValueError):
                valid = False
            if not valid:
                return f"Invalid {field.replace('_', ' ')}; a finite positive value is required. Value impact cannot be estimated."
    return None
