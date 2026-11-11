from datetime import datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


class PriceObservationResponse(BaseModel):
    id: UUID
    search_type: Literal["flight", "hotel"]
    search_key: str
    provider: str
    item_key: str
    item_name: str
    amount: Decimal
    currency: str
    is_available: bool
    search_criteria: dict
    captured_at: datetime

    model_config = {"from_attributes": True}


class PriceHistoryResponse(BaseModel):
    search_type: Literal["flight", "hotel"]
    search_key: str
    item_key: str | None = None
    observations_count: int = Field(ge=0)
    observations: list[PriceObservationResponse]
