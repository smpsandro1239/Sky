from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.core.activity import record_trip_activity
from app.core.financial_lock import lock_trip_financials
from app.core.notifications import add_notification
from app.api.routes.trips import get_accessible_trip, get_user_trip
from app.models.expense import Expense
from app.models.expense_share import ExpenseShare
from app.models.invitation import TripInvitation
from app.models.participant import TripParticipant
from app.models.settlement import TripSettlement
from app.models.user import User
from app.schemas.participant import ParticipantCreate, ParticipantResponse, ParticipantUpdate

router = APIRouter(prefix="/trips/{trip_id}/participants", tags=["participants"])


@router.post("", response_model=ParticipantResponse, status_code=status.HTTP_201_CREATED)
def create_participant(
    trip_id: UUID,
    payload: ParticipantCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ParticipantResponse:
    trip = get_user_trip(db, trip_id, user.id)
    if payload.email and db.scalar(
        select(TripParticipant.id).where(
            TripParticipant.trip_id == trip.id,
            func.lower(TripParticipant.email) == payload.email.lower(),
        )
    ) is not None:
        raise HTTPException(status_code=409, detail="Já existe um participante com este email nesta viagem.")
    participant = TripParticipant(trip_id=trip.id, **payload.model_dump())
    db.add(participant)
    db.flush()
    record_trip_activity(
        db, trip_id=trip.id, actor=user, action="created",
        entity_type="participant", entity_id=participant.id,
        summary="adicionou um participante",
    )
    db.commit()
    db.refresh(participant)
    return ParticipantResponse.model_validate(participant).model_copy(
        update={"is_linked": participant.user_id is not None}
    )


@router.get("", response_model=list[ParticipantResponse])
def list_participants(
    trip_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[ParticipantResponse]:
    trip = get_accessible_trip(db, trip_id, user.id)
    statement = select(TripParticipant).where(
        TripParticipant.trip_id == trip.id
    ).order_by(TripParticipant.created_at, TripParticipant.name)
    participants = list(db.scalars(statement).all())
    return [
        ParticipantResponse.model_validate(participant).model_copy(
            update={"is_linked": participant.user_id is not None}
        )
        for participant in participants
    ]


@router.patch("/{participant_id}", response_model=ParticipantResponse)
def update_participant(
    trip_id: UUID,
    participant_id: UUID,
    payload: ParticipantUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ParticipantResponse:
    trip = get_user_trip(db, trip_id, user.id)
    participant = db.scalar(
        select(TripParticipant).where(
            TripParticipant.id == participant_id,
            TripParticipant.trip_id == trip.id,
        )
    )
    if participant is None:
        raise HTTPException(status_code=404, detail="Participante não encontrado.")
    previous_role = participant.role
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
    if previous_role != participant.role:
        record_trip_activity(
            db, trip_id=trip.id, actor=user, action="updated",
            entity_type="participant", entity_id=participant.id,
            summary="alterou a permissão de um participante",
        )
        if participant.user_id is not None and participant.user_id != user.id:
            role_label = "editor" if participant.role == "editor" else "leitor"
            add_notification(
                db,
                user_id=participant.user_id,
                notification_type="trip_role_changed",
                title="Permissões da viagem actualizadas",
                message=f"A tua permissão na viagem {trip.name} foi alterada para {role_label}.",
                metadata={"trip_id": str(trip.id), "participant_id": str(participant.id), "role": participant.role},
            )
    db.commit()
    db.refresh(participant)
    return ParticipantResponse.model_validate(participant).model_copy(
        update={"is_linked": participant.user_id is not None}
    )


@router.delete("/{participant_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_participant(
    trip_id: UUID,
    participant_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Response:
    trip = get_user_trip(db, trip_id, user.id)
    lock_trip_financials(db, trip.id)
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
    has_settlements = db.scalar(
        select(TripSettlement.id).where(
            (TripSettlement.from_participant_id == participant.id)
            | (TripSettlement.to_participant_id == participant.id)
        ).limit(1)
    )
    if has_shares is not None or is_payer is not None or has_settlements is not None:
        raise HTTPException(
            status_code=409,
            detail="Não é possível remover este participante enquanto estiver associado a despesas ou acertos financeiros.",
        )
    record_trip_activity(
        db, trip_id=trip.id, actor=user, action="deleted",
        entity_type="participant", entity_id=participant.id,
        summary="removeu um participante",
    )
    db.delete(participant)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
