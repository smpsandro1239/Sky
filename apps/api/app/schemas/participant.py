from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ParticipantCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: str | None = Field(default=None, max_length=320)

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        normalized = value.strip()
        if len(normalized) < 2:
            raise ValueError("O nome tem de ter pelo menos 2 caracteres.")
        return normalized

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str | None) -> str | None:
        if value is None or not value.strip():
            return None
        normalized = value.strip().lower()
        if "@" not in normalized or normalized.startswith("@") or normalized.endswith("@"):
            raise ValueError("Indica um endereço de email válido.")
        return normalized


class ParticipantResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    trip_id: UUID
    name: str
    email: str | None
    role: str
    created_at: datetime



class ParticipantUpdate(BaseModel):
    role: Literal["editor", "viewer"]
