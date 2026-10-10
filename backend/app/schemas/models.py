from enum import Enum
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Heating(str, Enum):
    OLD_GAS = "old_gas_boiler"
    MODERN_GAS = "modern_gas_boiler"
    ELECTRIC = "electric_resistance"
    AIR_HEAT_PUMP = "air_source_heat_pump"
    GROUND_HEAT_PUMP = "ground_source_heat_pump"


class Property(StrictModel):
    property_id: str = Field(min_length=1, max_length=100)
    property_type: Literal["detached", "semi_detached", "terraced", "flat", "bungalow"]
    region: str = Field(min_length=1)
    floor_area_m2: float = Field(gt=0, allow_inf_nan=False)
    property_age_years: int | None = Field(default=None, ge=0)
    bedrooms: int | None = Field(default=None, ge=0)
    energy_rating: Literal["A", "B", "C", "D", "E", "F", "G"] | None = None
    insulation: Literal["poor", "average", "good"] | None = None
    heating_system: Heating | None = None
    glazing: Literal["single", "double", "triple"] | None = None
    renewable_contribution: Literal["none", "limited", "substantial"] | None = None
    smart_controls: Literal["none", "basic", "advanced"] | None = None
    roof_suitable_for_loft: bool | None = None
    roof_suitable_for_solar: bool | None = None
    heat_pump_compatible: bool | None = None
    controls_compatible: bool | None = None
    current_property_value_gbp: float | None = Field(default=None, ge=0, allow_inf_nan=False)
    market_index: float | None = Field(default=None, gt=0, allow_inf_nan=False)
    provenance: dict[str, str] = Field(default_factory=dict)


class AnnualEnergy(StrictModel):
    electricity_kwh: float | None = Field(default=None, ge=0, allow_inf_nan=False)
    gas_kwh: float | None = Field(default=None, ge=0, allow_inf_nan=False)
    quality: Literal["observed", "estimated", "synthetic", "missing"]
    method: str = Field(min_length=1)
    electricity_months_covered: int = Field(ge=0, le=12)
    gas_months_covered: int = Field(ge=0, le=12)
    warnings: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def consistent_quality(self):
        if self.quality == "missing" and (self.electricity_kwh is not None or self.gas_kwh is not None):
            raise ValueError("missing quality requires both fuel values to be null")
        if self.quality == "observed":
            for fuel in ("electricity", "gas"):
                if getattr(self, f"{fuel}_kwh") is not None and getattr(self, f"{fuel}_months_covered") != 12:
                    raise ValueError("observed annual values require complete 12-month coverage")
        return self


class Benchmark(StrictModel):
    property_type: Literal["detached", "semi_detached", "terraced", "flat", "bungalow"]
    intensity_kwh_m2_year: float = Field(gt=0, allow_inf_nan=False)
    source: str = Field(min_length=1)
    methodology: str = Field(min_length=1)
    region: str | None = None


class AssessmentRequest(StrictModel):
    property: Property
    annual_energy: AnnualEnergy
    benchmark: Benchmark | None = None

    @model_validator(mode="after")
    def matching_benchmark(self):
        if self.benchmark:
            if self.benchmark.property_type != self.property.property_type:
                raise ValueError("benchmark property type does not match property")
            if self.benchmark.region and self.benchmark.region != self.property.region:
                raise ValueError("benchmark region does not match property")
        return self


class ScoreComponent(StrictModel):
    name: str
    subscore: float | None
    weight: float
    contribution: float | None
    evidence: dict[str, str | float | None]


class ScoreResult(StrictModel):
    status: Literal["available", "unavailable"]
    score: int | None
    unrounded_score: float | None
    classification: str | None
    components: list[ScoreComponent]
    missing_fields: list[str]
    methodology_version: str = "greenprint-score-v1"


class Issue(StrictModel):
    code: str
    severity: Literal["high", "medium", "low"]
    message: str
    evidence: dict[str, str | float | None]


class AssessmentResponse(StrictModel):
    property_id: str
    score: ScoreResult
    poor_home: bool | None
    intensity_kwh_m2_year: float | None
    issues: list[Issue]
    warnings: list[str]


Retrofit = Literal["loft_insulation", "heat_pump", "solar_panels", "double_glazing", "smart_thermostat"]


class ScenarioRequest(AssessmentRequest):
    retrofits: list[Retrofit]
    budget_gbp: float | None = Field(default=None, ge=0, allow_inf_nan=False)
    objective: Literal["carbon_reduction", "energy_reduction", "shortest_payback"] = "carbon_reduction"

    @model_validator(mode="after")
    def unique_retrofits(self):
        if len(self.retrofits) != len(set(self.retrofits)):
            raise ValueError("duplicate retrofits are not allowed")
        return self


class UnavailableResponse(StrictModel):
    status: Literal["unavailable"] = "unavailable"
    reason: str
