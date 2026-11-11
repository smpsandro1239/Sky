from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ParticipantBudgetUpsert(BaseModel):
    amount: Decimal = Field(ge=0, max_digits=12, decimal_places=2)
    currency: str = Field(min_length=3, max_length=3)

    @field_validator("currency")
    @classmethod
    def normalize_currency(cls, value: str) -> str:
        normalized = value.strip().upper()
        if len(normalized) != 3 or not normalized.isalpha():
            raise ValueError("A moeda deve ser um código de três letras.")
        return normalized


class ParticipantBudgetResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    trip_id: UUID
    participant_id: UUID
    amount: Decimal
    currency: str
    created_at: datetime
    updated_at: datetime
