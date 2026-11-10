from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.api.routes.trips import get_user_trip
from app.models.flight import Flight
from app.models.user import User
from app.schemas.flight import FlightCreate, FlightResponse

router = APIRouter(prefix="/trips/{trip_id}/flights", tags=["flights"])


@router.post("", response_model=FlightResponse, status_code=status.HTTP_201_CREATED)
def create_flight(
    trip_id: UUID,
    payload: FlightCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Flight:
    trip = get_user_trip(db, trip_id, user.id)
    flight = Flight(trip_id=trip.id, **payload.model_dump())
    db.add(flight)
    db.commit()
    db.refresh(flight)
    return flight


@router.get("", response_model=list[FlightResponse])
def list_flights(
    trip_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[Flight]:
    trip = get_user_trip(db, trip_id, user.id)
    statement = select(Flight).where(Flight.trip_id == trip.id).order_by(Flight.departure_at)
    return list(db.scalars(statement).all())
