from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.core.activity import record_trip_activity
from app.core.notifications import notify_trip_members
from app.models.trip import Trip
from app.models.participant import TripParticipant
from app.models.user import User
from app.schemas.trip import TripCreate, TripResponse, TripUpdate

router = APIRouter(prefix="/trips", tags=["trips"])


def get_user_trip(db: Session, trip_id: UUID, user_id: UUID) -> Trip:
    trip = db.scalar(select(Trip).where(Trip.id == trip_id, Trip.user_id == user_id))
    if trip is None:
        raise HTTPException(status_code=404, detail="Viagem não encontrada.")
    return trip


def get_accessible_trip(db: Session, trip_id: UUID, user_id: UUID) -> Trip:
    trip = db.scalar(
        select(Trip)
        .outerjoin(TripParticipant, TripParticipant.trip_id == Trip.id)
        .where(
            Trip.id == trip_id,
            or_(Trip.user_id == user_id, TripParticipant.user_id == user_id),
        )
    )
    if trip is None:
        raise HTTPException(status_code=404, detail="Viagem não encontrada.")
    return trip


def get_trip_role(db: Session, trip: Trip, user_id: UUID) -> str:
    if trip.user_id == user_id:
        return "owner"
    participant = db.scalar(
        select(TripParticipant).where(
            TripParticipant.trip_id == trip.id,
            TripParticipant.user_id == user_id,
        )
    )
    if participant is None:
        raise HTTPException(status_code=404, detail="Viagem não encontrada.")
    return participant.role


def require_trip_editor(db: Session, trip_id: UUID, user_id: UUID) -> Trip:
    trip = get_accessible_trip(db, trip_id, user_id)
    if get_trip_role(db, trip, user_id) not in {"owner", "editor"}:
        raise HTTPException(status_code=403, detail="Tens acesso de leitura, mas não podes alterar esta viagem.")
    return trip


@router.post("", response_model=TripResponse, status_code=status.HTTP_201_CREATED)
def create_trip(
    payload: TripCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Trip:
    trip = Trip(user_id=user.id, **payload.model_dump())
    db.add(trip)
    db.flush()
    record_trip_activity(db, trip_id=trip.id, actor=user, action="created", entity_type="trip", entity_id=trip.id, summary="criou a viagem")
    db.commit()
    db.refresh(trip)
    return trip


@router.get("", response_model=list[TripResponse])
def list_trips(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[Trip]:
    statement = (
        select(Trip)
        .outerjoin(TripParticipant, TripParticipant.trip_id == Trip.id)
        .where(or_(Trip.user_id == user.id, TripParticipant.user_id == user.id))
        .distinct()
        .order_by(Trip.created_at.desc())
    )
    trips = list(db.scalars(statement).all())
    return [
        TripResponse.model_validate(trip).model_copy(update={"role": get_trip_role(db, trip, user.id)})
        for trip in trips
    ]


@router.get("/{trip_id}", response_model=TripResponse)
def read_trip(
    trip_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Trip:
    trip = get_accessible_trip(db, trip_id, user.id)
    return TripResponse.model_validate(trip).model_copy(update={"role": get_trip_role(db, trip, user.id)})


@router.get("/{trip_id}/access")
def read_trip_access(
    trip_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict[str, str]:
    trip = get_accessible_trip(db, trip_id, user.id)
    return {"role": get_trip_role(db, trip, user.id)}


@router.patch("/{trip_id}", response_model=TripResponse)
def update_trip(
    trip_id: UUID,
    payload: TripUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Trip:
    trip = get_user_trip(db, trip_id, user.id)
    changes = payload.model_dump(exclude_unset=True)
    new_start = changes.get("start_date", trip.start_date)
    new_end = changes.get("end_date", trip.end_date)
    if new_start and new_end and new_end < new_start:
        raise HTTPException(
            status_code=422,
            detail="A data de regresso não pode ser anterior à data de partida.",
        )
    for field, value in changes.items():
        setattr(trip, field, value)
    if changes:
        record_trip_activity(db, trip_id=trip.id, actor=user, action="updated", entity_type="trip", entity_id=trip.id, summary="atualizou os dados da viagem")
        notify_trip_members(
            db,
            trip=trip,
            actor_user_id=user.id,
            notification_type="trip_updated",
            title="Viagem actualizada",
            message=f"Os dados da viagem {trip.name} foram actualizados.",
            metadata={"changed_fields": sorted(changes.keys())},
        )
    db.commit()
    db.refresh(trip)
    return trip


@router.delete("/{trip_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_trip(
    trip_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Response:
    trip = get_user_trip(db, trip_id, user.id)
    db.delete(trip)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
