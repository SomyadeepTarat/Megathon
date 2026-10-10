"""Loading and documenting emission factors.

No factor values are bundled. Supply an authoritative, versioned JSON file,
or pass the same mapping directly to the public engine functions. The PRD
calls for UK DESNZ factors with explicit source year and accounting boundary;
factor choice is deliberately an operator/data-owner decision.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .schemas import validate_factor_set


def load_emission_factors(path: str | Path) -> dict[str, dict[str, Any]]:
    """Load and validate a JSON object containing documented fuel factors."""
    with Path(path).open(encoding="utf-8") as stream:
        data = json.load(stream)
    return validate_factor_set(data)
