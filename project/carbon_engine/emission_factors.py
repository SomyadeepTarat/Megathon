"""Loading and documenting emission factors.

The backend defaults to the sourced, corrected 2026 DESNZ CSV in Data/csv.
Standalone functions require an explicit factor mapping. JSON and CSV files
are supported; each factor retains its source, year, boundary and version.
"""
from __future__ import annotations

import json
import csv
from pathlib import Path
from typing import Any

from .schemas import validate_factor_set


def load_emission_factors(path: str | Path) -> dict[str, dict[str, Any]]:
    """Load and validate documented fuel factors from JSON or CSV."""
    path = Path(path)
    with path.open(encoding="utf-8") as stream:
        if path.suffix == '.csv':
            rows = list(csv.DictReader(stream))
            if len(rows) != 2 or {row['fuel'] for row in rows} != {'electricity', 'gas'}:
                raise ValueError('Factor CSV must contain exactly one electricity and gas row')
            fields = ['fuel', 'kg_co2e_per_kwh', 'source', 'source_year', 'accounting_boundary', 'version']
            data = {row['fuel']: {key: row[key] for key in fields} for row in rows}
        else:
            data = json.load(stream)
    return validate_factor_set(data)
