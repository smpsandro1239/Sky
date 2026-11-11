from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import ValidationError
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.core.activity import record_trip_activity
from app.core.financial_lock import lock_trip_financials
from app.core.notifications import notify_trip_members
from app.api.routes.trips import get_accessible_trip, get_user_trip, require_trip_editor
from app.models.expense import Expense
from app.models.expense_share import ExpenseShare
from app.models.participant import TripParticipant
from app.models.settlement import TripSettlement
from app.models.user import User
from app.schemas.expense import ExpenseCreate, ExpenseResponse, ExpenseUpdate

router = APIRouter(prefix="/trips/{trip_id}/expenses", tags=["expenses"])


def get_trip_expense(db: Session, trip_id: UUID, expense_id: UUID) -> Expense:
    expense = db.scalar(
        select(Expense).where(Expense.id == expense_id, Expense.trip_id == trip_id)
    )
    if expense is None:
        raise HTTPException(status_code=404, detail="Despesa não encontrada.")
    return expense


def validate_payer(db: Session, trip_id: UUID, participant_id: UUID | None) -> None:
    if participant_id is None:
        return
    participant = db.scalar(
        select(TripParticipant.id).where(
            TripParticipant.id == participant_id,
            TripParticipant.trip_id == trip_id,
        )
    )
    if participant is None:
        raise HTTPException(
            status_code=422,
            detail="Quem pagou a despesa tem de ser um participante desta viagem.",
        )


@router.post("", response_model=ExpenseResponse, status_code=status.HTTP_201_CREATED)
def create_expense(
    trip_id: UUID,
    payload: ExpenseCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Expense:
    trip = require_trip_editor(db, trip_id, user.id)
    lock_trip_financials(db, trip.id)
    validate_payer(db, trip.id, payload.paid_by_participant_id)
    expense = Expense(trip_id=trip.id, **payload.model_dump())
    db.add(expense)
    db.flush()
    record_trip_activity(db, trip_id=trip.id, actor=user, action="created", entity_type="expense", entity_id=expense.id, summary="registou uma despesa")
    notify_trip_members(db, trip=trip, actor_user_id=user.id, notification_type="trip_expense_created", title="Nova despesa na viagem", message=f"Foi registada uma despesa: {expense.description}.", metadata={"expense_id": str(expense.id), "description": expense.description})
    db.commit()
    db.refresh(expense)
    return expense


@router.get("", response_model=list[ExpenseResponse])
def list_expenses(
    trip_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[Expense]:
    trip = get_accessible_trip(db, trip_id, user.id)
    statement = select(Expense).where(Expense.trip_id == trip.id).order_by(
        Expense.expense_date.desc(), Expense.created_at.desc()
    )
    return list(db.scalars(statement).all())


@router.patch("/{expense_id}", response_model=ExpenseResponse)
def update_expense(
    trip_id: UUID,
    expense_id: UUID,
    payload: ExpenseUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Expense:
    trip = require_trip_editor(db, trip_id, user.id)
    lock_trip_financials(db, trip.id)
    expense = get_trip_expense(db, trip.id, expense_id)
    changes = payload.model_dump(exclude_unset=True)
    values = {field: getattr(expense, field) for field in ExpenseCreate.model_fields}
    values.update(changes)
    try:
        validated = ExpenseCreate.model_validate(values)
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    validate_payer(db, trip.id, validated.paid_by_participant_id)

    financial_fields = {"amount", "currency", "paid_by_participant_id"}
    changed_financial_fields = financial_fields.intersection(changes)
    if changed_financial_fields:
        has_settlements = db.scalar(
            select(TripSettlement.id)
            .where(TripSettlement.trip_id == trip.id)
            .limit(1)
        )
        if has_settlements is not None:
            raise HTTPException(
                status_code=409,
                detail=(
                    "Não é possível alterar o valor, a moeda ou o pagador de uma despesa "
                    "depois de existirem acertos financeiros na viagem. "
                    "Revê primeiro os acertos registados."
                ),
            )

    existing_share_total = db.scalar(
        select(func.coalesce(func.sum(ExpenseShare.amount), 0)).where(
            ExpenseShare.expense_id == expense.id
        )
    )
    if existing_share_total and existing_share_total != validated.amount:
        raise HTTPException(
            status_code=409,
            detail="O novo valor não corresponde às partilhas existentes. Actualiza primeiro a divisão da despesa.",
        )

    for field, value in validated.model_dump().items():
        setattr(expense, field, value)
    record_trip_activity(db, trip_id=trip.id, actor=user, action="updated", entity_type="expense", entity_id=expense.id, summary="atualizou uma despesa")
    notify_trip_members(db, trip=trip, actor_user_id=user.id, notification_type="trip_expense_updated", title="Despesa actualizada", message=f"A despesa {expense.description} foi actualizada.", metadata={"expense_id": str(expense.id), "description": expense.description, "changed_fields": sorted(changes)})
    db.commit()
    db.refresh(expense)
    return expense


@router.delete("/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_expense(
    trip_id: UUID,
    expense_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Response:
    trip = require_trip_editor(db, trip_id, user.id)
    lock_trip_financials(db, trip.id)
    expense = get_trip_expense(db, trip.id, expense_id)
    record_trip_activity(db, trip_id=trip.id, actor=user, action="deleted", entity_type="expense", entity_id=expense.id, summary="eliminou uma despesa")
    notify_trip_members(db, trip=trip, actor_user_id=user.id, notification_type="trip_expense_deleted", title="Despesa eliminada", message=f"A despesa {expense.description} foi eliminada.", metadata={"expense_id": str(expense.id), "description": expense.description})
    db.delete(expense)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
