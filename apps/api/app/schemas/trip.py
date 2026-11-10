from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class TripCreate(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    destination: str = Field(min_length=2, max_length=160)
    start_date: date | None = None
    end_date: date | None = None
    notes: str | None = Field(default=None, max_length=10000)

    @field_validator("name", "destination")
    @classmethod
    def normalize_required_text(cls, value: str) -> str:
        normalized = value.strip()
        if len(normalized) < 2:
            raise ValueError("O campo tem de ter pelo menos 2 caracteres.")
        return normalized

    @model_validator(mode="after")
    def validate_dates(self):
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValueError("A data de regresso não pode ser anterior à data de partida.")
        return self


class TripUpdate(BaseModel):
    # Defaults allow omitted fields; non-optional types reject explicit null values.
    name: str = Field(default=None, min_length=2, max_length=160)
    destination: str = Field(default=None, min_length=2, max_length=160)
    start_date: date | None = None
    end_date: date | None = None
    notes: str | None = Field(default=None, max_length=10000)

    @field_validator("name", "destination")
    @classmethod
    def normalize_required_text(cls, value: str) -> str:
        normalized = value.strip()
        if len(normalized) < 2:
            raise ValueError("O campo tem de ter pelo menos 2 caracteres.")
        return normalized

    @model_validator(mode="after")
    def validate_payload(self):
        if not self.model_fields_set:
            raise ValueError("Indica pelo menos um campo para atualizar.")
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValueError("A data de regresso não pode ser anterior à data de partida.")
        return self


class TripResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    destination: str
    start_date: date | None
    end_date: date | None
    notes: str | None
    created_at: datetime
