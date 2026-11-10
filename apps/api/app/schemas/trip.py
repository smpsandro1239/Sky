from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class TripCreate(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    destination: str = Field(min_length=2, max_length=160)
    start_date: date | None = None
    end_date: date | None = None
    notes: str | None = Field(default=None, max_length=10000)

    @model_validator(mode="after")
    def validate_dates(self):
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValueError("A data de regresso não pode ser anterior à data de partida.")
        return self


class TripUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=160)
    destination: str | None = Field(default=None, min_length=2, max_length=160)
    start_date: date | None = None
    end_date: date | None = None
    notes: str | None = Field(default=None, max_length=10000)

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
