from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_current_user, get_db
from app.api.routes.expenses import get_trip_expense
from app.api.routes.trips import get_user_trip
from app.models.expense_share import ExpenseShare
from app.models.participant import TripParticipant
from app.models.user import User
from app.schemas.expense_share import ExpenseShareInput, ExpenseShareResponse

router = APIRouter(prefix="/trips/{trip_id}/expenses/{expense_id}/shares", tags=["expense-shares"])


@router.get("", response_model=list[ExpenseShareResponse])
def list_expense_shares(
    trip_id: UUID,
    expense_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[ExpenseShare]:
    trip = get_user_trip(db, trip_id, user.id)
    get_trip_expense(db, trip.id, expense_id)
    statement = (
        select(ExpenseShare)
        .join(TripParticipant, ExpenseShare.participant_id == TripParticipant.id)
        .where(ExpenseShare.expense_id == expense_id, TripParticipant.trip_id == trip.id)
        .options(selectinload(ExpenseShare.participant))
        .order_by(TripParticipant.name)
    )
    return list(db.scalars(statement).all())


@router.patch("", response_model=list[ExpenseShareResponse])
def replace_expense_shares(
    trip_id: UUID,
    expense_id: UUID,
    payload: list[ExpenseShareInput],
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[ExpenseShare]:
    trip = get_user_trip(db, trip_id, user.id)
    expense = get_trip_expense(db, trip.id, expense_id)

    participant_ids = [item.participant_id for item in payload]
    if len(participant_ids) != len(set(participant_ids)):
        raise HTTPException(status_code=422, detail="Cada participante só pode surgir uma vez na divisão.")

    if not payload:
        db.query(ExpenseShare).filter(ExpenseShare.expense_id == expense.id).delete()
        db.commit()
        return []

    participants = list(db.scalars(
        select(TripParticipant).where(
            TripParticipant.trip_id == trip.id,
            TripParticipant.id.in_(participant_ids),
        )
    ).all())
    if len(participants) != len(participant_ids):
        raise HTTPException(status_code=422, detail="Todos os participantes têm de pertencer a esta viagem.")

    total_cents = sum(int((item.amount * 100).quantize(Decimal("1"))) for item in payload)
    expense_cents = int((expense.amount * 100).quantize(Decimal("1")))
    if total_cents != expense_cents:
        raise HTTPException(
            status_code=422,
            detail="A soma das partes tem de ser exactamente igual ao valor total da despesa.",
        )

    db.query(ExpenseShare).filter(ExpenseShare.expense_id == expense.id).delete()
    shares = [
        ExpenseShare(expense_id=expense.id, participant_id=item.participant_id, amount=item.amount)
        for item in payload
    ]
    db.add_all(shares)
    db.commit()
    for share in shares:
        db.refresh(share)
    return shares
