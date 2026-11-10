from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class AccommodationCreate(BaseModel):
    provider: str | None = Field(default=None, max_length=80)
    name: str = Field(min_length=2, max_length=180)
    location: str = Field(min_length=2, max_length=180)
    check_in: date
    check_out: date
    price_amount: Decimal | None = Field(default=None, gt=0, max_digits=12, decimal_places=2)
    price_currency: str = Field(default="EUR", min_length=3, max_length=3)

    @field_validator("name", "location")
    @classmethod
    def normalize_required_text(cls, value: str) -> str:
        normalized = value.strip()
        if len(normalized) < 2:
            raise ValueError("O campo tem de ter pelo menos 2 caracteres.")
        return normalized

    @field_validator("price_currency")
    @classmethod
    def normalize_currency(cls, value: str) -> str:
        normalized = value.strip().upper()
        if len(normalized) != 3 or not normalized.isalpha():
            raise ValueError("A moeda tem de ser identificada por três letras.")
        return normalized

    @field_validator("provider")
    @classmethod
    def normalize_provider(cls, value: str | None) -> str | None:
        return value.strip() or None if value is not None else None

    @model_validator(mode="after")
    def validate_stay(self):
        if self.check_out <= self.check_in:
            raise ValueError("A data de saída tem de ser posterior à entrada.")
        return self


class AccommodationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    provider: str | None
    name: str
    location: str
    check_in: date
    check_out: date
    price_amount: Decimal | None
    price_currency: str
    created_at: datetime
