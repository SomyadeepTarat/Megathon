from typing import Protocol
from app.schemas.models import ScenarioRequest, Property, AssessmentRequest
from app.schemas.engines import (FeasibilityResult, SimulationResult, EnergyImpact,
                                CarbonResult, ValuationResult, PropertyRecord)


class PropertyRepository(Protocol):
    def list_properties(self) -> list[PropertyRecord]: ...
    def load_property(self, property_id: str) -> PropertyRecord: ...


class RetrofitEngine(Protocol):
    version: str
    def check_feasibility(self, request: ScenarioRequest) -> FeasibilityResult: ...
    def simulate_retrofits(self, request: ScenarioRequest) -> SimulationResult: ...


class CarbonEngine(Protocol):
    def calculate_carbon(self, energy: EnergyImpact) -> CarbonResult: ...


class ValuationEngine(Protocol):
    def predict_value_impact(self, baseline: Property, scenario: Property) -> ValuationResult: ...
