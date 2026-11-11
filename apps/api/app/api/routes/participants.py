from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.api.routes.trips import get_accessible_trip, get_user_trip, require_trip_editor
from app.models.expense import Expense
from app.models.expense_share import ExpenseShare
from app.models.invitation import TripInvitation
from app.models.participant import TripParticipant
from app.models.user import User
from app.schemas.participant import ParticipantCreate, ParticipantResponse, ParticipantUpdate

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
    trip = get_accessible_trip(db, trip_id, user.id)
    statement = select(TripParticipant).where(
        TripParticipant.trip_id == trip.id
    ).order_by(TripParticipant.created_at, TripParticipant.name)
    return list(db.scalars(statement).all())


@router.patch("/{participant_id}", response_model=ParticipantResponse)
def update_participant(
    trip_id: UUID,
    participant_id: UUID,
    payload: ParticipantUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> TripParticipant:
    trip = get_user_trip(db, trip_id, user.id)
    participant = db.scalar(
        select(TripParticipant).where(
            TripParticipant.id == participant_id,
            TripParticipant.trip_id == trip.id,
        )
    )
    if participant is None:
        raise HTTPException(status_code=404, detail="Participante não encontrado.")
    participant.role = payload.role
    if participant.email:
        pending_invitations = db.scalars(
            select(TripInvitation).where(
                TripInvitation.trip_id == trip.id,
                TripInvitation.email == participant.email.lower(),
                TripInvitation.status == "pending",
            )
        ).all()
        for invitation in pending_invitations:
            invitation.role = payload.role
    db.commit()
    db.refresh(participant)
    return participant


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
        raise HTTPException(status_code=404, detail="Participante não encontrado.")
    has_shares = db.scalar(
        select(ExpenseShare.id).where(ExpenseShare.participant_id == participant.id).limit(1)
    )
    is_payer = db.scalar(
        select(Expense.id).where(Expense.paid_by_participant_id == participant.id).limit(1)
    )
    if has_shares is not None or is_payer is not None:
        raise HTTPException(
            status_code=409,
            detail="Não é possível remover este participante enquanto estiver associado a despesas como pagador ou participante.",
        )
    db.delete(participant)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
