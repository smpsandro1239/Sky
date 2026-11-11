from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.api.routes.trips import get_accessible_trip, require_trip_editor
from app.core.activity import record_trip_activity
from app.models.participant import TripParticipant
from app.models.participant_budget import ParticipantBudget
from app.models.user import User
from app.schemas.participant_budget import ParticipantBudgetResponse, ParticipantBudgetUpsert

router = APIRouter(prefix="/trips/{trip_id}/participants/{participant_id}/budgets", tags=["participant-budgets"])


@router.get("", response_model=list[ParticipantBudgetResponse])
def list_participant_budgets(
    trip_id: UUID,
    participant_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[ParticipantBudget]:
    trip = get_accessible_trip(db, trip_id, user.id)
    participant = db.scalar(select(TripParticipant).where(
        TripParticipant.id == participant_id, TripParticipant.trip_id == trip.id
    ))
    if participant is None:
        raise HTTPException(status_code=404, detail="Participante não encontrado.")
    return list(db.scalars(select(ParticipantBudget).where(
        ParticipantBudget.trip_id == trip.id, ParticipantBudget.participant_id == participant.id
    ).order_by(ParticipantBudget.currency)).all())


@router.put("", response_model=ParticipantBudgetResponse)
def upsert_participant_budget(
    trip_id: UUID,
    participant_id: UUID,
    payload: ParticipantBudgetUpsert,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ParticipantBudget:
    trip = require_trip_editor(db, trip_id, user.id)
    participant = db.scalar(select(TripParticipant).where(
        TripParticipant.id == participant_id, TripParticipant.trip_id == trip.id
    ))
    if participant is None:
        raise HTTPException(status_code=404, detail="Participante não encontrado.")
    budget = db.scalar(select(ParticipantBudget).where(
        ParticipantBudget.trip_id == trip.id,
        ParticipantBudget.participant_id == participant.id,
        ParticipantBudget.currency == payload.currency,
    ))
    if budget is None:
        budget = ParticipantBudget(
            trip_id=trip.id, participant_id=participant.id,
            amount=payload.amount, currency=payload.currency,
        )
        db.add(budget)
        action = "definiu"
    else:
        budget.amount = payload.amount
        action = "atualizou"
    db.flush()
    record_trip_activity(
        db, trip_id=trip.id, actor=user, action="updated",
        entity_type="participant_budget", entity_id=budget.id,
        summary=f"{action} o orçamento individual de um participante",
    )
    db.commit()
    db.refresh(budget)
    return budget


@router.delete("/{currency}", status_code=status.HTTP_204_NO_CONTENT)
def delete_participant_budget(
    trip_id: UUID,
    participant_id: UUID,
    currency: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Response:
    trip = require_trip_editor(db, trip_id, user.id)
    participant = db.scalar(select(TripParticipant).where(
        TripParticipant.id == participant_id, TripParticipant.trip_id == trip.id
    ))
    if participant is None:
        raise HTTPException(status_code=404, detail="Participante não encontrado.")
    normalized_currency = currency.strip().upper()
    budget = db.scalar(select(ParticipantBudget).where(
        ParticipantBudget.trip_id == trip.id,
        ParticipantBudget.participant_id == participant.id,
        ParticipantBudget.currency == normalized_currency,
    ))
    if budget is None:
        raise HTTPException(status_code=404, detail="Orçamento individual não encontrado.")
    db.delete(budget)
    record_trip_activity(
        db, trip_id=trip.id, actor=user, action="deleted",
        entity_type="participant_budget", entity_id=budget.id,
        summary="removeu o orçamento individual de um participante",
    )
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
