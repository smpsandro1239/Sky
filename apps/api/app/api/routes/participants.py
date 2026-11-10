from uuid import UUID

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.api.routes.trips import get_user_trip
from app.models.participant import TripParticipant
from app.models.user import User
from app.schemas.participant import ParticipantCreate, ParticipantResponse

router = APIRouter(prefix="/trips/{trip_id}/participants", tags=["participants"])


@router.post("", response_model=ParticipantResponse, status_code=status.HTTP_201_CREATED)
def create_participant(
    trip_id: UUID,
    payload: ParticipantCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> TripParticipant:
    trip = get_user_trip(db, trip_id, user.id)
    participant = TripParticipant(trip_id=trip.id, **payload.model_dump())
    db.add(participant)
    db.commit()
    db.refresh(participant)
    return participant


@router.get("", response_model=list[ParticipantResponse])
def list_participants(
    trip_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[TripParticipant]:
    trip = get_user_trip(db, trip_id, user.id)
    statement = select(TripParticipant).where(
        TripParticipant.trip_id == trip.id
    ).order_by(TripParticipant.created_at, TripParticipant.name)
    return list(db.scalars(statement).all())


@router.delete("/{participant_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_participant(
    trip_id: UUID,
    participant_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Response:
    trip = get_user_trip(db, trip_id, user.id)
    participant = db.scalar(
        select(TripParticipant).where(
            TripParticipant.id == participant_id,
            TripParticipant.trip_id == trip.id,
        )
    )
    if participant is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Participante não encontrado.")
    db.delete(participant)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
