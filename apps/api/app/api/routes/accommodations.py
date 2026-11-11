from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.core.activity import record_trip_activity
from app.core.notifications import notify_trip_members
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
    db.flush()
    record_trip_activity(db, trip_id=trip.id, actor=user, action="created", entity_type="accommodation", entity_id=accommodation.id, summary="adicionou um alojamento")
    notify_trip_members(db, trip=trip, actor_user_id=user.id, notification_type="trip_accommodation_created", title="Novo alojamento na viagem", message=f"Foi adicionado o alojamento {accommodation.name}.", metadata={"accommodation_id": str(accommodation.id), "name": accommodation.name})
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
    record_trip_activity(db, trip_id=trip.id, actor=user, action="updated", entity_type="accommodation", entity_id=accommodation.id, summary="atualizou um alojamento")
    notify_trip_members(db, trip=trip, actor_user_id=user.id, notification_type="trip_accommodation_updated", title="Alojamento actualizado", message=f"O alojamento {accommodation.name} foi actualizado.", metadata={"accommodation_id": str(accommodation.id), "name": accommodation.name, "changed_fields": sorted(changes)})
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
    record_trip_activity(db, trip_id=trip.id, actor=user, action="deleted", entity_type="accommodation", entity_id=accommodation.id, summary="eliminou um alojamento")
    notify_trip_members(db, trip=trip, actor_user_id=user.id, notification_type="trip_accommodation_deleted", title="Alojamento eliminado", message=f"O alojamento {accommodation.name} foi eliminado.", metadata={"accommodation_id": str(accommodation.id), "name": accommodation.name})
    db.delete(accommodation)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
