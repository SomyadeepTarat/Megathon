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


class PhysicalInputs(StrictModel):
    thermal_demand_kwh: float | None = Field(default=None, ge=0, allow_inf_nan=False)
    thermal_demand_scope: str | None = None
    space_heating_demand_kwh: float | None = Field(default=None, ge=0, allow_inf_nan=False)
    hot_water_demand_kwh: float | None = Field(default=None, ge=0, allow_inf_nan=False)
    base_appliance_electricity_kwh: float | None = Field(default=None, ge=0, allow_inf_nan=False)
    annual_electricity_demand_kwh: float | None = Field(default=None, ge=0, allow_inf_nan=False)
    gas_space_heating_kwh: float | None = Field(default=None, ge=0, allow_inf_nan=False)
    gas_hot_water_kwh: float | None = Field(default=None, ge=0, allow_inf_nan=False)
    electric_space_heating_kwh: float | None = Field(default=None, ge=0, allow_inf_nan=False)
    electric_hot_water_kwh: float | None = Field(default=None, ge=0, allow_inf_nan=False)
    heating_energy_kwh: float | None = Field(default=None, ge=0, allow_inf_nan=False)
    boiler_efficiency: float | None = Field(default=None, gt=0, le=1, allow_inf_nan=False)
    heating_efficiency: float | None = Field(default=None, gt=0, le=1, allow_inf_nan=False)
    scop: float | None = Field(default=None, gt=0, allow_inf_nan=False)
    hot_water_cop: float | None = Field(default=None, gt=0, allow_inf_nan=False)
    electric_resistance_efficiency: float | None = Field(default=None, gt=0, le=1, allow_inf_nan=False)
    solar_generation_kwh: float | None = Field(default=None, ge=0, allow_inf_nan=False)
    solar_self_consumed_kwh: float | None = Field(default=None, ge=0, allow_inf_nan=False)
    solar_self_consumption_fraction: float | None = Field(default=None, ge=0, le=1, allow_inf_nan=False)
    proposed_solar_generation_kwh: float | None = Field(default=None, ge=0, allow_inf_nan=False)
    proposed_solar_self_consumed_kwh: float | None = Field(default=None, ge=0, allow_inf_nan=False)
    proposed_solar_self_consumption_fraction: float | None = Field(default=None, ge=0, le=1, allow_inf_nan=False)
    proposed_heat_pump_type: Literal['air_source_heat_pump', 'ground_source_heat_pump'] | None = None
    provenance: dict[str, str] = Field(default_factory=dict)

    @model_validator(mode='after')
    def solar_consistency(self):
        # Physical observations are preserved even when inconsistent. The
        # simulation caps self-consumption at generation and eligible demand.
        return self


class DocumentedFactor(StrictModel):
    fuel: Literal['electricity', 'gas']
    kg_co2e_per_kwh: float = Field(ge=0, allow_inf_nan=False)
    source: str = Field(min_length=1)
    source_year: int = Field(ge=1900)
    accounting_boundary: str = Field(min_length=1)
    version: str = Field(min_length=1)


class FactorSet(StrictModel):
    electricity: DocumentedFactor
    gas: DocumentedFactor

    @model_validator(mode='after')
    def matching_fuel(self):
        if self.electricity.fuel != 'electricity' or self.gas.fuel != 'gas':
            raise ValueError('Factor names must match their fuel')
        return self


class RetrofitCost(StrictModel):
    amount_gbp: float = Field(ge=0, allow_inf_nan=False)
    source: str = Field(min_length=1)
    date: str = Field(min_length=1)


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
    solar_installed: bool | None = None
    heat_pump_installed: bool | None = None
    loft_insulation_installed: bool | None = None
    smart_thermostat_installed: bool | None = None
    physical_inputs: PhysicalInputs = Field(default_factory=PhysicalInputs)
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
    emission_factors: FactorSet | None = None

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
    retrofit_costs: dict[Literal["loft_insulation", "heat_pump", "solar_panels", "double_glazing", "smart_thermostat"], RetrofitCost] = Field(default_factory=dict)
    electricity_tariff_gbp_per_kwh: float | None = Field(default=None, ge=0, allow_inf_nan=False)
    gas_tariff_gbp_per_kwh: float | None = Field(default=None, ge=0, allow_inf_nan=False)

    @model_validator(mode="after")
    def unique_retrofits(self):
        if len(self.retrofits) != len(set(self.retrofits)):
            raise ValueError("duplicate retrofits are not allowed")
        return self


class UnavailableResponse(StrictModel):
    status: Literal["unavailable"] = "unavailable"
    reason: str


class RecommendationRequest(ScenarioRequest):
    retrofits: list[Retrofit] = Field(default_factory=list)
