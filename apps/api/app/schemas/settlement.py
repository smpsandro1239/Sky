from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class SettlementCreate(BaseModel):
    from_participant_id: UUID
    to_participant_id: UUID
    amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    currency: str = Field(min_length=3, max_length=3)
    paid_at: datetime | None = None
    notes: str | None = Field(default=None, max_length=1000)

    @field_validator("currency")
    @classmethod
    def normalize_currency(cls, value: str) -> str:
        normalized = value.strip().upper()
        if len(normalized) != 3 or not normalized.isalpha():
            raise ValueError("A moeda deve ser um código de três letras.")
        return normalized

    @field_validator("notes")
    @classmethod
    def normalize_notes(cls, value: str | None) -> str | None:
        return value.strip() or None if value is not None else None


class SettlementResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    from_participant_id: UUID
    to_participant_id: UUID
    amount: Decimal
    currency: str
    paid_at: datetime
    notes: str | None
