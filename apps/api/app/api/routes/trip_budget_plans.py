from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.api.routes.trips import get_accessible_trip, require_trip_editor
from app.core.activity import record_trip_activity
from app.models.trip_budget_plan import TripBudgetPlan
from app.models.user import User
from app.schemas.trip_budget_plan import TripBudgetPlanResponse, TripBudgetPlanUpsert

router = APIRouter(prefix="/trips/{trip_id}/budget-plans", tags=["budget-plans"])


@router.get("", response_model=list[TripBudgetPlanResponse])
def list_budget_plans(
    trip_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[TripBudgetPlan]:
    trip = get_accessible_trip(db, trip_id, user.id)
    return list(db.scalars(select(TripBudgetPlan).where(
        TripBudgetPlan.trip_id == trip.id
    ).order_by(TripBudgetPlan.month, TripBudgetPlan.currency, TripBudgetPlan.category)).all())


@router.put("", response_model=TripBudgetPlanResponse)
def upsert_budget_plan(
    trip_id: UUID,
    payload: TripBudgetPlanUpsert,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> TripBudgetPlan:
    trip = require_trip_editor(db, trip_id, user.id)
    plan = db.scalar(select(TripBudgetPlan).where(
        TripBudgetPlan.trip_id == trip.id,
        TripBudgetPlan.month == payload.month,
        TripBudgetPlan.category == payload.category,
        TripBudgetPlan.currency == payload.currency,
    ))
    if plan is None:
        plan = TripBudgetPlan(trip_id=trip.id, **payload.model_dump())
        db.add(plan)
        action = "definiu"
    else:
        plan.amount = payload.amount
        action = "atualizou"
    db.flush()
    record_trip_activity(
        db, trip_id=trip.id, actor=user, action="updated",
        entity_type="budget_plan", entity_id=plan.id,
        summary=f"{action} o planeamento mensal de uma categoria",
    )
    db.commit()
    db.refresh(plan)
    return plan


@router.delete("/{month}/{category}/{currency}", status_code=status.HTTP_204_NO_CONTENT)
def delete_budget_plan(
    trip_id: UUID,
    month: str,
    category: str,
    currency: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Response:
    trip = require_trip_editor(db, trip_id, user.id)
    normalized_category = category.strip().lower()
    normalized_currency = currency.strip().upper()
    plan = db.scalar(select(TripBudgetPlan).where(
        TripBudgetPlan.trip_id == trip.id,
        TripBudgetPlan.month == month,
        TripBudgetPlan.category == normalized_category,
        TripBudgetPlan.currency == normalized_currency,
    ))
    if plan is None:
        raise HTTPException(status_code=404, detail="Previsão orçamental não encontrada.")
    db.delete(plan)
    record_trip_activity(
        db, trip_id=trip.id, actor=user, action="deleted",
        entity_type="budget_plan", entity_id=plan.id,
        summary="removeu uma previsão orçamental mensal",
    )
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
