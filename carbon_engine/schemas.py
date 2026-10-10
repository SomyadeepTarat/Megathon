"""Input/output contracts for the standalone carbon engine.

Inputs accept the project's existing ``property`` / ``annual_energy`` JSON
shape, with explicit supplementary physical inputs for retrofit modeling.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(frozen=True)
class EmissionFactor:
    fuel: str
    kg_co2e_per_kwh: float
    source: str
    source_year: int
    accounting_boundary: str
    version: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "fuel": self.fuel,
            "kg_co2e_per_kwh": self.kg_co2e_per_kwh,
            "source": self.source,
            "source_year": self.source_year,
            "accounting_boundary": self.accounting_boundary,
            "version": self.version,
        }


def json_value(value: Any) -> Any:
    """Convert common Pydantic/dataclass inputs into ordinary JSON values."""
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    if hasattr(value, "dict") and callable(value.dict):
        return value.dict()
    if hasattr(value, "__dataclass_fields__"):
        from dataclasses import asdict
        return asdict(value)
    return value


def property_and_energy(data: Mapping[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    """Accept either a PropertyRecord-like object or flat property input."""
    data = json_value(data)
    prop = json_value(data.get("property", data))
    # Backend Property keeps P4 physical inputs nested; flatten a copy for the
    # standalone numerical engine while preserving the caller's original data.
    physical = json_value(prop.pop("physical_inputs", {}))
    if isinstance(physical, Mapping):
        prop.update({key: value for key, value in physical.items()
                     if key != "provenance" and value is not None})
    energy = json_value(data.get("annual_energy", data.get("energy", {})))
    return dict(prop), dict(energy)


def validate_factor_set(factors: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    """Require fully documented electricity and gas factors; no default values."""
    if not isinstance(factors, Mapping):
        raise ValueError("emission_factors must provide electricity and gas records")
    result: dict[str, dict[str, Any]] = {}
    for fuel in ("electricity", "gas"):
        raw = json_value(factors.get(fuel))
        if raw is None:
            raise ValueError(f"Missing {fuel} emission factor")
        if isinstance(raw, (int, float)):
            raise ValueError(f"{fuel} factor requires source, year, boundary and version metadata")
        if isinstance(raw, EmissionFactor):
            raw = raw.as_dict()
        if not isinstance(raw, Mapping):
            raise ValueError(f"Invalid {fuel} emission factor")
        value = raw.get("kg_co2e_per_kwh")
        try:
            value = float(value)
        except (TypeError, ValueError):
            raise ValueError(f"Invalid {fuel} kg_co2e_per_kwh") from None
        if value < 0 or not __import__("math").isfinite(value):
            raise ValueError(f"Invalid {fuel} kg_co2e_per_kwh")
        for field in ("source", "source_year", "accounting_boundary", "version"):
            if raw.get(field) in (None, ""):
                raise ValueError(f"{fuel} emission factor requires {field}")
        if raw.get("fuel", fuel) != fuel:
            raise ValueError(f"Factor fuel mismatch for {fuel}")
        result[fuel] = {**dict(raw), "fuel": fuel, "kg_co2e_per_kwh": value}
    return result
