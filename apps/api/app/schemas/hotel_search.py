from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator


class HotelSearchRequest(BaseModel):
    city_code: str = Field(min_length=3, max_length=3)
    check_in: date
    check_out: date
    adults: int = Field(default=2, ge=1, le=9)
    room_quantity: int = Field(default=1, ge=1, le=8)
    currency: str = Field(default="EUR", min_length=3, max_length=3)
    radius: int = Field(default=20, ge=1, le=50)
    max_hotels: int = Field(default=20, ge=1, le=40)

    @field_validator("city_code", "currency", mode="before")
    @classmethod
    def normalize_codes(cls, value: str) -> str:
        normalized = value.strip().upper()
        if not normalized.isalpha() or len(normalized) != 3:
            raise ValueError("Utiliza um código de cidade IATA ou moeda com três letras.")
        return normalized

    @model_validator(mode="after")
    def validate_stay(self):
        if self.check_out <= self.check_in:
            raise ValueError("A data de saída tem de ser posterior à entrada.")
        if (self.check_out - self.check_in).days > 30:
            raise ValueError("A estadia não pode exceder 30 noites.")
        return self


class HotelSearchOffer(BaseModel):
    id: str
    provider: Literal["amadeus"]
    hotel_name: str
    hotel_id: str
    location: str
    check_in: date
    check_out: date
    price_total: Decimal
    currency: str
    room_description: str | None = None
    board_type: str | None = None


class HotelSearchResponse(BaseModel):
    provider: Literal["amadeus"]
    results_count: int
    offers: list[HotelSearchOffer]
