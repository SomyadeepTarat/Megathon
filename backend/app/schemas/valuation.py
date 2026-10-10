from typing import Literal
from pydantic import Field, model_validator
from app.schemas.models import StrictModel


class BaselineValuationResponse(StrictModel):
    property_id: str
    status: Literal['unavailable', 'illustrative', 'indicative']
    reason: str | None = None
    value_gbp: float | None = Field(default=None, gt=0, allow_inf_nan=False)
    range_gbp: tuple[float, float] | None = None
    confidence_level: float | None = Field(default=None, gt=0, lt=1)
    target_kind: Literal['sales', 'snapshot'] | None = None
    method: str | None = None
    warnings: list[str] = Field(default_factory=list)

    @model_validator(mode='after')
    def consistent_result(self):
        import math
        values = (self.value_gbp, self.range_gbp, self.confidence_level, self.target_kind, self.method)
        if self.status == 'unavailable':
            if not self.reason or any(v is not None for v in values):
                raise ValueError('Unavailable valuation requires a reason and no estimates')
        else:
            if self.reason or any(v is None for v in values):
                raise ValueError('Available valuation requires complete estimates')
            low, high = self.range_gbp
            if not all(math.isfinite(v) for v in (low, high)) or not 0 <= low <= self.value_gbp <= high:
                raise ValueError('Invalid baseline interval')
        return self
