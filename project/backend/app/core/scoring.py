from decimal import Decimal, ROUND_HALF_UP
from app.schemas.models import AssessmentRequest, ScoreComponent, ScoreResult

WEIGHTS = {
    "energy_efficiency": .25, "consumption_intensity": .20,
    "insulation": .15, "heating_system": .15, "windows": .10,
    "renewable_energy": .10, "smart_management": .05,
}
EPC = {"A": 100, "B": 85, "C": 70, "D": 55, "E": 40, "F": 20, "G": 0}
INSULATION = {"poor": 20, "average": 60, "good": 100}
HEATING = {"old_gas_boiler": 20, "modern_gas_boiler": 50,
           "electric_resistance": 60, "air_source_heat_pump": 90,
           "ground_source_heat_pump": 100}
GLAZING = {"single": 20, "double": 75, "triple": 100}
RENEWABLE = {"none": 0, "limited": 50, "substantial": 100}
CONTROLS = {"none": 0, "basic": 50, "advanced": 100}


def energy_intensity(request: AssessmentRequest) -> float | None:
    energy = request.annual_energy
    if energy.electricity_kwh is None or energy.gas_kwh is None:
        return None
    return (energy.electricity_kwh + energy.gas_kwh) / request.property.floor_area_m2


def classify(score: int) -> str:
    for threshold, category in [(80, "Highly efficient"), (65, "Good"),
                                (50, "Moderate"), (30, "Poor"), (0, "Very poor")]:
        if score >= threshold:
            return category
    raise ValueError("score must be nonnegative")


def calculate_score(request: AssessmentRequest) -> ScoreResult:
    prop = request.property
    components = []
    missing = []
    mappings = [
        ("energy_efficiency", "energy_rating", EPC),
        ("insulation", "insulation", INSULATION),
        ("heating_system", "heating_system", HEATING),
        ("windows", "glazing", GLAZING),
        ("renewable_energy", "renewable_contribution", RENEWABLE),
        ("smart_management", "smart_controls", CONTROLS),
    ]
    values = {}
    for name, field, mapping in mappings:
        value = getattr(prop, field)
        subscore = mapping[value] if value is not None else None
        if value is None:
            missing.append(f"property.{field}")
        values[name] = (subscore, {field: value})
    intensity = energy_intensity(request)
    for fuel in ("electricity", "gas"):
        if getattr(request.annual_energy, f"{fuel}_kwh") is None:
            missing.append(f"annual_energy.{fuel}_kwh")
    if request.benchmark is None:
        missing.append("benchmark")
    consumption = None
    if intensity is not None and request.benchmark is not None:
        ratio = intensity / request.benchmark.intensity_kwh_m2_year
        consumption = max(0., min(100., 100 - 50 * (ratio - .5)))
    values["consumption_intensity"] = (consumption, {
        "intensity_kwh_m2_year": intensity,
        "benchmark_kwh_m2_year": request.benchmark.intensity_kwh_m2_year if request.benchmark else None,
        "benchmark_source": request.benchmark.source if request.benchmark else None,
    })
    total = Decimal("0")
    for name, weight in WEIGHTS.items():
        subscore, evidence = values[name]
        contribution = None
        if subscore is not None:
            exact = Decimal(str(subscore)) * Decimal(str(weight))
            contribution = float(exact)
            total += exact
        components.append(ScoreComponent(name=name, subscore=subscore, weight=weight,
                                         contribution=contribution, evidence=evidence))
    if missing:
        return ScoreResult(status="unavailable", score=None, unrounded_score=None,
                           classification=None, components=components, missing_fields=missing)
    score = int(total.quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    return ScoreResult(status="available", score=score, unrounded_score=float(total),
                       classification=classify(score), components=components, missing_fields=[])
