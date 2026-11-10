from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.api.routes.trips import get_accessible_trip, get_user_trip, require_trip_editor
from app.models.accommodation import Accommodation
from app.models.user import User
from app.schemas.accommodation import (
    AccommodationCreate,
    AccommodationResponse,
    AccommodationUpdate,
)

router = APIRouter(prefix="/trips/{trip_id}/accommodations", tags=["accommodations"])


def get_trip_accommodation(
    db: Session, trip_id: UUID, accommodation_id: UUID
) -> Accommodation:
    accommodation = db.scalar(
        select(Accommodation).where(
            Accommodation.id == accommodation_id,
            Accommodation.trip_id == trip_id,
        )
    )
    if accommodation is None:
        raise HTTPException(status_code=404, detail="Alojamento não encontrado.")
    return accommodation


@router.post("", response_model=AccommodationResponse, status_code=status.HTTP_201_CREATED)
def create_accommodation(
    trip_id: UUID,
    payload: AccommodationCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Accommodation:
    trip = require_trip_editor(db, trip_id, user.id)
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
    trip = get_accessible_trip(db, trip_id, user.id)
    statement = select(Accommodation).where(
        Accommodation.trip_id == trip.id
    ).order_by(Accommodation.check_in)
    return list(db.scalars(statement).all())


@router.patch("/{accommodation_id}", response_model=AccommodationResponse)
def update_accommodation(
    trip_id: UUID,
    accommodation_id: UUID,
    payload: AccommodationUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Accommodation:
    trip = require_trip_editor(db, trip_id, user.id)
    accommodation = get_trip_accommodation(db, trip.id, accommodation_id)
    changes = payload.model_dump(exclude_unset=True)
    values = {
        field: getattr(accommodation, field)
        for field in AccommodationCreate.model_fields
    }
    values.update(changes)
    try:
        validated = AccommodationCreate.model_validate(values)
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    for field, value in validated.model_dump().items():
        setattr(accommodation, field, value)
    db.commit()
    db.refresh(accommodation)
    return accommodation


@router.delete("/{accommodation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_accommodation(
    trip_id: UUID,
    accommodation_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Response:
    trip = require_trip_editor(db, trip_id, user.id)
    accommodation = get_trip_accommodation(db, trip.id, accommodation_id)
    db.delete(accommodation)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
