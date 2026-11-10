from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


EXPENSE_CATEGORIES = {
    "alimentacao",
    "alojamento",
    "atividades",
    "compras",
    "transportes",
    "outros",
}


class ExpenseCreate(BaseModel):
    category: str = Field(min_length=2, max_length=40)
    description: str = Field(min_length=2, max_length=180)
    expense_date: date
    amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    currency: str = Field(default="EUR", min_length=3, max_length=3)
    paid_by_participant_id: UUID | None = None
    notes: str | None = Field(default=None, max_length=2000)

    @field_validator("category")
    @classmethod
    def validate_category(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in EXPENSE_CATEGORIES:
            raise ValueError("Categoria de despesa inválida.")
        return normalized

    @field_validator("description")
    @classmethod
    def normalize_description(cls, value: str) -> str:
        normalized = value.strip()
        if len(normalized) < 2:
            raise ValueError("A descrição tem de ter pelo menos 2 caracteres.")
        return normalized

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


class ExpenseUpdate(ExpenseCreate):
    category: str | None = Field(default=None, min_length=2, max_length=40)
    description: str | None = Field(default=None, min_length=2, max_length=180)
    expense_date: date | None = None
    amount: Decimal | None = Field(default=None, gt=0, max_digits=12, decimal_places=2)
    currency: str | None = Field(default=None, min_length=3, max_length=3)

    @field_validator("category")
    @classmethod
    def validate_optional_category(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip().lower()
        if normalized not in EXPENSE_CATEGORIES:
            raise ValueError("Categoria de despesa inválida.")
        return normalized

    @field_validator("description")
    @classmethod
    def normalize_optional_description(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        if len(normalized) < 2:
            raise ValueError("A descrição tem de ter pelo menos 2 caracteres.")
        return normalized

    @field_validator("currency")
    @classmethod
    def normalize_optional_currency(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip().upper()
        if len(normalized) != 3 or not normalized.isalpha():
            raise ValueError("A moeda deve ser um código de três letras.")
        return normalized

    @field_validator("notes")
    @classmethod
    def normalize_optional_notes(cls, value: str | None) -> str | None:
        return value.strip() or None if value is not None else None


class ExpenseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    category: str
    description: str
    expense_date: date
    amount: Decimal
    currency: str
    paid_by_participant_id: UUID | None
    notes: str | None
    created_at: datetime
