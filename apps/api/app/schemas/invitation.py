from datetime import datetime
from uuid import UUID

from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class InvitationCreate(BaseModel):
    email: EmailStr
    role: Literal["editor", "viewer"] = "viewer"

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: EmailStr) -> str:
        return str(value).strip().lower()


class InvitationAccept(BaseModel):
    token: str = Field(min_length=32, max_length=128)


class InvitationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    trip_id: UUID
    email: str
    role: str
    status: str
    expires_at: datetime
    accepted_at: datetime | None
    created_at: datetime


class InvitationCreated(InvitationResponse):
    invitation_token: str
    email_sent: bool = False
