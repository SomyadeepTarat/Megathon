from app.core.scoring import energy_intensity
from app.schemas.models import AssessmentRequest, AssessmentResponse, Issue
from app.core.scoring import calculate_score


def assess(request: AssessmentRequest) -> AssessmentResponse:
    score = calculate_score(request)
    prop = request.property
    intensity = energy_intensity(request)
    issues = []
    conditions = [
        (prop.insulation == "poor", "poor_insulation", "high", "Insulation is poor.", {"insulation": prop.insulation}),
        (prop.heating_system == "old_gas_boiler", "old_heating", "high", "An old gas boiler is recorded.", {"heating_system": prop.heating_system}),
        (prop.glazing == "single", "single_glazing", "medium", "Windows are single glazed.", {"glazing": prop.glazing}),
        (prop.renewable_contribution == "none", "no_renewables", "low", "No renewable contribution is recorded.", {"renewable_contribution": prop.renewable_contribution}),
        (prop.smart_controls == "none", "no_controls", "low", "No smart energy controls are recorded.", {"smart_controls": prop.smart_controls}),
    ]
    if intensity is not None and request.benchmark:
        conditions.append((intensity > request.benchmark.intensity_kwh_m2_year,
                           "above_benchmark_intensity", "high",
                           "Purchased-energy intensity exceeds the supplied benchmark.",
                           {"intensity_kwh_m2_year": intensity,
                            "benchmark_kwh_m2_year": request.benchmark.intensity_kwh_m2_year}))
    for condition, code, severity, message, evidence in conditions:
        if condition:
            issues.append(Issue(code=code, severity=severity, message=message, evidence=evidence))
    warnings = list(request.annual_energy.warnings)
    if request.annual_energy.quality != "observed":
        warnings.append(f"Energy data quality: {request.annual_energy.quality}.")
    if score.missing_fields:
        warnings.append("Full score unavailable: required inputs are missing.")
    return AssessmentResponse(property_id=prop.property_id, score=score,
                              poor_home=score.score < 50 if score.score is not None else None,
                              intensity_kwh_m2_year=intensity, issues=issues, warnings=warnings)
