from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.api.routes.trips import get_user_trip
from app.models.accommodation import Accommodation
from app.models.user import User
from app.schemas.accommodation import AccommodationCreate, AccommodationResponse

router = APIRouter(prefix="/trips/{trip_id}/accommodations", tags=["accommodations"])


@router.post("", response_model=AccommodationResponse, status_code=status.HTTP_201_CREATED)
def create_accommodation(
    trip_id: UUID,
    payload: AccommodationCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Accommodation:
    trip = get_user_trip(db, trip_id, user.id)
    accommodation = Accommodation(trip_id=trip.id, **payload.model_dump())
    db.add(accommodation)
    db.commit()
    db.refresh(accommodation)
    return accommodation


@router.get("", response_model=list[AccommodationResponse])
def list_accommodations(
    trip_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[Accommodation]:
    trip = get_user_trip(db, trip_id, user.id)
    statement = select(Accommodation).where(
        Accommodation.trip_id == trip.id
    ).order_by(Accommodation.check_in)
    return list(db.scalars(statement).all())
