from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.api.routes.balances import get_trip_balances
from app.api.routes.trips import get_accessible_trip, require_trip_editor
from app.core.activity import record_trip_activity
from app.models.participant import TripParticipant
from app.models.settlement import TripSettlement
from app.models.user import User
from app.schemas.settlement import SettlementCreate, SettlementResponse

router = APIRouter(prefix="/trips/{trip_id}/settlements", tags=["settlements"])


@router.get("", response_model=list[SettlementResponse])
def list_settlements(
    trip_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[TripSettlement]:
    trip = get_accessible_trip(db, trip_id, user.id)
    statement = (
        select(TripSettlement)
        .where(TripSettlement.trip_id == trip.id)
        .order_by(TripSettlement.paid_at.desc(), TripSettlement.id.desc())
    )
    return list(db.scalars(statement).all())


@router.post("", response_model=SettlementResponse, status_code=status.HTTP_201_CREATED)
def create_settlement(
    trip_id: UUID,
    payload: SettlementCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> TripSettlement:
    trip = require_trip_editor(db, trip_id, user.id)
    if payload.from_participant_id == payload.to_participant_id:
        raise HTTPException(status_code=422, detail="O pagador e o destinatário têm de ser diferentes.")

    participant_ids = {payload.from_participant_id, payload.to_participant_id}
    participants = list(db.scalars(
        select(TripParticipant).where(
            TripParticipant.trip_id == trip.id,
            TripParticipant.id.in_(participant_ids),
        )
    ).all())
    if len(participants) != 2:
        raise HTTPException(status_code=422, detail="Os dois participantes têm de pertencer a esta viagem.")

    balances = get_trip_balances(trip.id, db, user)
    currency_balance = next(
        (item for item in balances["currencies"] if item["currency"] == payload.currency),
        None,
    )
    if currency_balance is None:
        raise HTTPException(status_code=422, detail="Não existem saldos nesta moeda para a viagem.")

    positions = {item["participant_id"]: item for item in currency_balance["participants"]}
    debtor = positions[str(payload.from_participant_id)]
    creditor = positions[str(payload.to_participant_id)]
    if Decimal(debtor["net"]) >= 0 or Decimal(creditor["net"]) <= 0:
        raise HTTPException(status_code=422, detail="O pagamento tem de ser feito por um participante devedor a um participante credor.")
    if payload.amount > min(abs(Decimal(debtor["net"])), Decimal(creditor["net"])):
        raise HTTPException(status_code=422, detail="O pagamento não pode exceder a dívida ou o crédito em aberto entre os participantes.")

    settlement = TripSettlement(
        trip_id=trip.id,
        from_participant_id=payload.from_participant_id,
        to_participant_id=payload.to_participant_id,
        amount=payload.amount,
        currency=payload.currency,
        paid_at=payload.paid_at or datetime.now(timezone.utc),
        notes=payload.notes,
        created_by_user_id=user.id,
    )
    db.add(settlement)
    db.flush()
    record_trip_activity(
        db,
        trip_id=trip.id,
        actor=user,
        action="created",
        entity_type="settlement",
        entity_id=settlement.id,
        summary="registou um acerto entre participantes",
    )
    db.commit()
    db.refresh(settlement)
    return settlement
