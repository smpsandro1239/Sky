from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.api.routes.trips import get_accessible_trip, get_user_trip, require_trip_editor
from app.models.flight import Flight
from app.models.user import User
from app.schemas.flight import FlightCreate, FlightResponse, FlightUpdate

router = APIRouter(prefix="/trips/{trip_id}/flights", tags=["flights"])


def get_trip_flight(db: Session, trip_id: UUID, flight_id: UUID) -> Flight:
    flight = db.scalar(
        select(Flight).where(Flight.id == flight_id, Flight.trip_id == trip_id)
    )
    if flight is None:
        raise HTTPException(status_code=404, detail="Voo não encontrado.")
    return flight


@router.post("", response_model=FlightResponse, status_code=status.HTTP_201_CREATED)
def create_flight(
    trip_id: UUID,
    payload: FlightCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Flight:
    trip = require_trip_editor(db, trip_id, user.id)
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
    trip = get_accessible_trip(db, trip_id, user.id)
    statement = select(Flight).where(Flight.trip_id == trip.id).order_by(Flight.departure_at)
    return list(db.scalars(statement).all())


@router.patch("/{flight_id}", response_model=FlightResponse)
def update_flight(
    trip_id: UUID,
    flight_id: UUID,
    payload: FlightUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Flight:
    trip = require_trip_editor(db, trip_id, user.id)
    flight = get_trip_flight(db, trip.id, flight_id)
    changes = payload.model_dump(exclude_unset=True)
    values = {
        field: getattr(flight, field)
        for field in FlightCreate.model_fields
    }
    values.update(changes)
    try:
        validated = FlightCreate.model_validate(values)
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    for field, value in validated.model_dump().items():
        setattr(flight, field, value)
    db.commit()
    db.refresh(flight)
    return flight


@router.delete("/{flight_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_flight(
    trip_id: UUID,
    flight_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Response:
    trip = require_trip_editor(db, trip_id, user.id)
    flight = get_trip_flight(db, trip.id, flight_id)
    db.delete(flight)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
