import math
from typing import Literal
from pydantic import Field, model_validator
from app.schemas.models import (StrictModel, Property, AnnualEnergy, AssessmentResponse,
                                AssessmentRequest, Retrofit)


class FeasibilityItem(StrictModel):
    retrofit: Retrofit
    status: Literal['feasible', 'conditional', 'infeasible']
    reason: str = Field(min_length=1)


class FeasibilityResult(StrictModel):
    status: Literal['available', 'unavailable']
    items: list[FeasibilityItem] = Field(default_factory=list)
    reason: str | None = None

    @model_validator(mode='after')
    def valid_status(self):
        if self.status == 'unavailable' and (not self.reason or self.items):
            raise ValueError('Unavailable feasibility requires a reason and no items')
        if len({item.retrofit for item in self.items}) != len(self.items):
            raise ValueError('Feasibility contains duplicate measures')
        return self


class FuelState(StrictModel):
    electricity_kwh: float = Field(ge=0, allow_inf_nan=False)
    gas_kwh: float = Field(ge=0, allow_inf_nan=False)


class SimulationResult(StrictModel):
    updated_property: Property
    after: FuelState
    applied_retrofits: list[Retrofit]
    installation_cost_gbp: float | None = Field(default=None, ge=0, allow_inf_nan=False)
    methodology_version: str = Field(min_length=1)
    assumptions: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    annual_bill_savings_gbp: float | None = Field(default=None, allow_inf_nan=False)
    bill_savings_reason: str | None = None
    simple_payback_years: float | None = Field(default=None, ge=0, allow_inf_nan=False)
    payback_reason: str | None = None


class EnergyImpact(StrictModel):
    baseline: FuelState
    after: FuelState
    electricity_savings_kwh: float = Field(allow_inf_nan=False)
    gas_savings_kwh: float = Field(allow_inf_nan=False)
    net_savings_kwh: float = Field(allow_inf_nan=False)
    improvement_percentage: float | None = Field(default=None, allow_inf_nan=False)

    @model_validator(mode='after')
    def consistent(self):
        e = self.baseline.electricity_kwh - self.after.electricity_kwh
        g = self.baseline.gas_kwh - self.after.gas_kwh
        for actual, expected in [(self.electricity_savings_kwh, e),
                                 (self.gas_savings_kwh, g), (self.net_savings_kwh, e + g)]:
            if not math.isclose(actual, expected, abs_tol=1e-7, rel_tol=1e-9):
                raise ValueError('Energy savings disagree with fuel states')
        total = self.baseline.electricity_kwh + self.baseline.gas_kwh
        if total == 0:
            if self.improvement_percentage is not None:
                raise ValueError('Zero baseline requires unavailable percentage')
        elif self.improvement_percentage is None or not math.isclose(
            self.improvement_percentage, 100 * (e + g) / total, abs_tol=1e-7):
            raise ValueError('Improvement percentage disagrees with energy states')
        return self


class EmissionFactor(StrictModel):
    fuel: Literal['electricity', 'gas']
    kg_co2e_per_kwh: float = Field(ge=0, allow_inf_nan=False)
    source: str = Field(min_length=1)
    source_year: int = Field(ge=1900)
    accounting_boundary: str = Field(min_length=1)
    version: str | None = None


class CarbonResult(StrictModel):
    status: Literal['available', 'unavailable']
    reduction_kg_co2e: float | None = Field(default=None, allow_inf_nan=False)
    factors: list[EmissionFactor] = Field(default_factory=list)
    reason: str | None = None

    @model_validator(mode='after')
    def complete(self):
        if self.status == 'unavailable':
            if not self.reason or self.reduction_kg_co2e is not None or self.factors:
                raise ValueError('Unavailable carbon requires reason and no estimates')
        elif self.reduction_kg_co2e is None or len(self.factors) != 2 or {f.fuel for f in self.factors} != {'electricity', 'gas'}:
            raise ValueError('Available carbon requires reduction and both documented fuel factors')
        return self


class ValuationResult(StrictModel):
    status: Literal['indicative', 'illustrative', 'unavailable']
    reason: str | None = None
    value_before: float | None = Field(default=None, gt=0, allow_inf_nan=False)
    value_after: float | None = Field(default=None, gt=0, allow_inf_nan=False)
    uplift_range: tuple[float, float] | None = None
    baseline_value_gbp: float | None = Field(default=None, gt=0, allow_inf_nan=False)
    after_value_gbp: float | None = Field(default=None, gt=0, allow_inf_nan=False)
    baseline_range_gbp: tuple[float, float] | None = None
    after_range_gbp: tuple[float, float] | None = None
    value_change_gbp: float | None = Field(default=None, allow_inf_nan=False)
    value_change_range_gbp: tuple[float, float] | None = None
    confidence_level: float | None = Field(default=None, gt=0, lt=1)
    method: str | None = None
    warnings: list[str] = Field(default_factory=list)

    @model_validator(mode='after')
    def valid_result(self):
        if self.status != 'unavailable':
            for alias, original in [('value_before', 'baseline_value_gbp'), ('value_after', 'after_value_gbp'), ('uplift_range', 'value_change_range_gbp')]:
                if getattr(self, alias) is None:
                    setattr(self, alias, getattr(self, original))
                elif getattr(self, alias) != getattr(self, original):
                    raise ValueError('Valuation aliases disagree with estimates')
        numeric = [self.value_before, self.value_after, self.uplift_range, self.baseline_value_gbp, self.after_value_gbp, self.value_change_gbp,
                   self.baseline_range_gbp, self.after_range_gbp, self.value_change_range_gbp,
                   self.confidence_level]
        if self.status == 'unavailable':
            if not self.reason or any(x is not None for x in numeric):
                raise ValueError('Unavailable valuation requires reason and no estimates')
        else:
            if any(x is None for x in numeric) or not self.method:
                raise ValueError('Available valuation requires estimates, ranges and calibration method')
            for interval in [self.baseline_range_gbp, self.after_range_gbp, self.value_change_range_gbp]:
                if not all(math.isfinite(x) for x in interval) or interval[0] > interval[1]:
                    raise ValueError('Invalid valuation interval')
            if self.baseline_range_gbp[0] < 0 or self.after_range_gbp[0] < 0:
                raise ValueError('Property value ranges cannot be negative')
            if not math.isclose(self.after_value_gbp - self.baseline_value_gbp, self.value_change_gbp, abs_tol=1e-7):
                raise ValueError('Valuation contrast disagrees with predictions')
        return self


class PackageTradeoff(StrictModel):
    objective: Literal['carbon_reduction', 'energy_reduction', 'shortest_payback']
    retrofits: list[Retrofit]
    installation_cost_gbp: float
    carbon_reduction_kg_co2e: float | None = None
    net_energy_savings_kwh: float
    annual_bill_savings_gbp: float | None = None
    simple_payback_years: float | None = None


class OptimizationContext(StrictModel):
    objective: Literal['carbon_reduction', 'energy_reduction', 'shortest_payback']
    budget_gbp: float
    explanation: str
    alternatives: list[PackageTradeoff] = Field(default_factory=list)
    installation_order: list[Retrofit] = Field(default_factory=list)


class ScenarioResponse(StrictModel):
    scenario_id: str
    property_id: str
    status: Literal['success', 'partial', 'rejected', 'unavailable']
    baseline_carbon: dict | None = None
    after_carbon: dict | None = None
    carbon_savings_by_fuel_kg_co2e: dict[str, float] | None = None
    reason: str | None = None
    baseline_assessment: AssessmentResponse
    feasibility: FeasibilityResult
    after_assessment: AssessmentResponse | None = None
    updated_property: Property | None = None
    energy: EnergyImpact | None = None
    carbon: CarbonResult
    valuation: ValuationResult
    installation_cost_gbp: float | None = None
    applied_retrofits: list[Retrofit] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    versions: dict[str, str] = Field(default_factory=dict)
    annual_bill_savings_gbp: float | None = Field(default=None, allow_inf_nan=False)
    bill_savings_reason: str | None = None
    simple_payback_years: float | None = Field(default=None, ge=0, allow_inf_nan=False)
    payback_reason: str | None = None
    optimization_context: OptimizationContext | None = None


class PropertyRecord(AssessmentRequest):
    dataset_kind: Literal['synthetic', 'observed', 'estimated', 'imported']
    dataset_source: str = Field(min_length=1)


class PropertySummary(StrictModel):
    property_id: str
    property_type: str
    region: str
    dataset_kind: Literal['synthetic', 'observed', 'estimated', 'imported']
    dataset_source: str


class Recommendation(StrictModel):
    retrofit: Retrofit
    feasibility: FeasibilityItem
    suitability: Literal['High', 'Medium', 'Low']
    priority: int = Field(ge=1)
    estimated_cost_gbp: float = Field(ge=0, allow_inf_nan=False)
    energy: EnergyImpact | None = None
    carbon: CarbonResult | None = None
    reason: str = Field(min_length=1)
    assumptions: list[str] = Field(default_factory=list)


class OptimizationResult(StrictModel):
    status: Literal['available', 'unavailable']
    reason: str | None = None
    ranked_packages: list[SimulationResult] = Field(default_factory=list)
    best_scenario: ScenarioResponse | None = None
    package_decisions: list[dict] = Field(default_factory=list)
    objective: Literal['carbon_reduction', 'energy_reduction', 'shortest_payback']
    methodology: str

    @model_validator(mode='after')
    def valid_status(self):
        if self.status == 'unavailable' and (not self.reason or self.ranked_packages):
            raise ValueError('Unavailable optimization requires reason and no packages')
        if not self.methodology.strip():
            raise ValueError('Optimization requires a documented methodology')
        return self


class RecommendationOption(StrictModel):
    retrofit: Retrofit
    feasibility: FeasibilityItem
    scenario: ScenarioResponse
    suitability: Literal['High', 'Medium', 'Low']
    suitability_reason: str = Field(min_length=1)
    ranking_reason: str | None = None
    priority: int | None = Field(default=None, ge=1)
    estimated_cost_gbp: float | None = Field(default=None, ge=0, allow_inf_nan=False)


class RecommendationResponse(StrictModel):
    property_id: str
    scenario_id: str | None = None
    revision: int | None = Field(default=None, ge=1)
    objective: Literal['carbon_reduction', 'energy_reduction', 'shortest_payback'] = 'energy_reduction'
    installation_order: list[Retrofit] = Field(default_factory=list)
    status: Literal['available', 'partial', 'unavailable']
    recommendations: list[RecommendationOption]
    other_options: list[RecommendationOption]
    methodology: str
    warnings: list[str] = Field(default_factory=list)


class ValuationProperty(Property):
    """Allow incomplete impact inputs to reach the explicit availability guard."""
    floor_area_m2: float | None = Field(default=None, gt=0, allow_inf_nan=False)
    region: str | None = None
    property_type: Literal['detached', 'semi_detached', 'terraced', 'flat', 'bungalow'] | None = None

    @model_validator(mode='before')
    @classmethod
    def blank_critical_fields(cls, value):
        if isinstance(value, dict):
            value = dict(value)
            for field in ['floor_area_m2', 'region', 'property_type', 'current_property_value_gbp', 'energy_rating']:
                if isinstance(value.get(field), str) and not value[field].strip():
                    value[field] = None
        return value


class ValuationRequest(StrictModel):
    scenario_property: ValuationProperty | None = None
    scenario_annual_energy: AnnualEnergy | None = None


class FullAssessmentResponse(StrictModel):
    property_id: str
    assessment: AssessmentResponse
    annual_energy: AnnualEnergy
    baseline_carbon: dict
    valuation: ValuationResult


class HealthResponse(StrictModel):
    status: Literal['ok']
    version: str
    capabilities: dict
    readiness: dict


class PortfolioEntry(StrictModel):
    property_id: str
    property_type: str
    region: str
    dataset_kind: str
    score: int | None
    intensity: float | None
    classification: str | None
    improvement: float | None
    carbon: float | None
    reason: str | None = None
