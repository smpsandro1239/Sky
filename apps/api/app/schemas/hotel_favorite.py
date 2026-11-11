from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class HotelFavoriteCreate(BaseModel):
    provider: str = Field(default="amadeus", min_length=1, max_length=40)
    hotel_id: str = Field(min_length=1, max_length=80)
    hotel_name: str = Field(min_length=2, max_length=180)
    location: str = Field(min_length=2, max_length=180)

    @field_validator("provider", "hotel_id", "hotel_name", "location")
    @classmethod
    def normalize_text(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("O campo não pode estar vazio.")
        return normalized


class HotelFavoriteResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    provider: str
    hotel_id: str
    hotel_name: str
    location: str
    created_at: datetime
