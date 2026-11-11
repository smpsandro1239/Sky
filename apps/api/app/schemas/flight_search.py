from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator


class FlightSearchRequest(BaseModel):
    origin: str = Field(min_length=3, max_length=3)
    destination: str = Field(min_length=3, max_length=3)
    departure_date: date
    return_date: date | None = None
    adults: int = Field(default=1, ge=1, le=9)
    currency: str = Field(default="EUR", min_length=3, max_length=3)
    non_stop: bool = False
    max_results: int = Field(default=20, ge=1, le=50)

    @field_validator("origin", "destination", "currency", mode="before")
    @classmethod
    def normalize_code(cls, value: str) -> str:
        normalized = value.strip().upper()
        if not normalized.isalpha() or len(normalized) != 3:
            raise ValueError("Utiliza um código IATA ou de moeda com três letras.")
        return normalized

    @model_validator(mode="after")
    def validate_route_and_dates(self):
        if self.origin == self.destination:
            raise ValueError("A origem e o destino têm de ser diferentes.")
        if self.return_date and self.return_date <= self.departure_date:
            raise ValueError("A data de regresso tem de ser posterior à partida.")
        return self


class FlightSearchSegment(BaseModel):
    carrier: str
    flight_number: str
    origin: str
    destination: str
    departure_at: str
    arrival_at: str


class FlightSearchOffer(BaseModel):
    id: str
    provider: Literal["amadeus"]
    price_total: Decimal
    currency: str
    number_of_stops: int
    itineraries: list[list[FlightSearchSegment]]
    booking_url: str | None = None
    duration_minutes: int | None = None
    recommendation_score: float | None = None
    recommendation_reasons: list[str] = Field(default_factory=list)


class FlightSearchResponse(BaseModel):
    provider: Literal["amadeus"]
    results_count: int
    offers: list[FlightSearchOffer]
