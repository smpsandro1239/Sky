from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class TripActivityResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    trip_id: UUID
    actor_user_id: UUID | None
    actor_name: str
    action: str
    entity_type: str
    entity_id: str | None
    summary: str
    created_at: datetime


class TripActivityPage(BaseModel):
    items: list[TripActivityResponse]
    limit: int
    offset: int
    has_more: bool
