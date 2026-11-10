from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class FlightCreate(BaseModel):
    provider: str | None = Field(default=None, max_length=80)
    origin: str = Field(min_length=3, max_length=3)
    destination: str = Field(min_length=3, max_length=3)
    departure_at: datetime
    arrival_at: datetime | None = None
    price_amount: Decimal | None = Field(default=None, gt=0, max_digits=12, decimal_places=2)
    price_currency: str = Field(default="EUR", min_length=3, max_length=3)

    @field_validator("origin", "destination", "price_currency")
    @classmethod
    def normalize_codes(cls, value: str) -> str:
        normalized = value.strip().upper()
        if len(normalized) != 3 or not normalized.isalpha():
            raise ValueError("O código tem de conter exatamente três letras.")
        return normalized

    @field_validator("provider")
    @classmethod
    def normalize_provider(cls, value: str | None) -> str | None:
        return value.strip() or None if value is not None else None

    @model_validator(mode="after")
    def validate_route_and_times(self):
        if self.origin == self.destination:
            raise ValueError("A origem e o destino têm de ser diferentes.")
        if self.arrival_at and self.arrival_at <= self.departure_at:
            raise ValueError("A chegada tem de ser posterior à partida.")
        return self


class FlightResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    provider: str | None
    origin: str
    destination: str
    departure_at: datetime
    arrival_at: datetime | None
    price_amount: Decimal | None
    price_currency: str
    created_at: datetime
