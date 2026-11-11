import re
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.expense import EXPENSE_CATEGORIES


class TripBudgetPlanUpsert(BaseModel):
    month: str = Field(min_length=7, max_length=7)
    category: str = Field(min_length=2, max_length=40)
    amount: Decimal = Field(ge=0, max_digits=12, decimal_places=2)
    currency: str = Field(min_length=3, max_length=3)

    @field_validator("month")
    @classmethod
    def validate_month(cls, value: str) -> str:
        if not re.fullmatch(r"\d{4}-(0[1-9]|1[0-2])", value):
            raise ValueError("O mês deve estar no formato AAAA-MM.")
        return value

    @field_validator("category")
    @classmethod
    def validate_category(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in EXPENSE_CATEGORIES:
            raise ValueError("Categoria de despesa inválida.")
        return normalized

    @field_validator("currency")
    @classmethod
    def normalize_currency(cls, value: str) -> str:
        normalized = value.strip().upper()
        if len(normalized) != 3 or not normalized.isalpha():
            raise ValueError("A moeda deve ser um código de três letras.")
        return normalized


class TripBudgetPlanResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    trip_id: UUID
    month: str
    category: str
    amount: Decimal
    currency: str
    created_at: datetime
    updated_at: datetime
