from datetime import datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class PriceAlertCreate(BaseModel):
    search_type: Literal["flight", "hotel"]
    search_key: str = Field(min_length=64, max_length=64, pattern=r"^[a-f0-9]{64}$")
    item_key: str = Field(min_length=1, max_length=160)
    item_name: str = Field(min_length=1, max_length=200)
    currency: str = Field(min_length=3, max_length=3)
    target_price: Decimal = Field(gt=0, max_digits=12, decimal_places=2)

    @field_validator("currency")
    @classmethod
    def normalize_currency(cls, value: str) -> str:
        normalized = value.strip().upper()
        if len(normalized) != 3 or not normalized.isalpha():
            raise ValueError("A moeda deve ser um código de três letras.")
        return normalized


class PriceAlertUpdate(BaseModel):
    is_active: bool


class PriceAlertResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    search_type: Literal["flight", "hotel"]
    search_key: str
    item_key: str
    item_name: str
    currency: str
    target_price: Decimal
    is_active: bool
    triggered_price: Decimal | None
    triggered_at: datetime | None
    created_at: datetime
