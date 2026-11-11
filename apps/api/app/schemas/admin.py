from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

PLATFORM_ROLES = {"traveler", "support", "admin"}


class PlatformRoleUpdate(BaseModel):
    role: str = Field(min_length=1, max_length=20)

    @field_validator("role")
    @classmethod
    def validate_role(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in PLATFORM_ROLES:
            raise ValueError("Papel inválido. Valores permitidos: traveler, support, admin.")
        return normalized


class AdminUserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: EmailStr
    display_name: str | None
    role: str
    is_active: bool
    is_verified: bool
    created_at: datetime
