from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.api.routes.trips import get_accessible_trip
from app.models.activity import TripActivity
from app.models.user import User
from app.schemas.activity import TripActivityPage, TripActivityResponse

router = APIRouter(prefix="/trips/{trip_id}/activity", tags=["activity"])


@router.get("", response_model=TripActivityPage)
def list_trip_activity(
    trip_id: UUID,
    limit: int = Query(default=30, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> TripActivityPage:
    trip = get_accessible_trip(db, trip_id, user.id)
    statement = (
        select(TripActivity)
        .where(TripActivity.trip_id == trip.id)
        .order_by(TripActivity.created_at.desc(), TripActivity.id.desc())
        .offset(offset)
        .limit(limit + 1)
    )
    rows = list(db.scalars(statement).all())
    has_more = len(rows) > limit
    return TripActivityPage(
        items=[TripActivityResponse.model_validate(item) for item in rows[:limit]],
        limit=limit,
        offset=offset,
        has_more=has_more,
    )
