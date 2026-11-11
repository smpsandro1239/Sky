from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.price_observation import PriceObservation
from app.models.user import User
from app.schemas.price_history import PriceHistoryResponse

router = APIRouter(prefix="/prices", tags=["price-intelligence"])


@router.get("/history", response_model=PriceHistoryResponse)
def get_price_history(
    search_type: Literal["flight", "hotel"] = Query(),
    search_key: str = Query(min_length=64, max_length=64, pattern=r"^[a-f0-9]{64}$"),
    item_key: str | None = Query(default=None, min_length=1, max_length=160),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> PriceHistoryResponse:
    """Devolve apenas observações recolhidas pelo utilizador autenticado."""
    statement = select(PriceObservation).where(
        PriceObservation.user_id == user.id,
        PriceObservation.search_type == search_type,
        PriceObservation.search_key == search_key,
    )
    if item_key:
        statement = statement.where(PriceObservation.item_key == item_key)
    statement = statement.order_by(PriceObservation.captured_at.desc()).limit(limit)
    observations = list(db.scalars(statement).all())
    observations.reverse()

    if not observations:
        raise HTTPException(
            status_code=404,
            detail="Ainda não existem observações para esta pesquisa.",
        )

    return PriceHistoryResponse(
        search_type=search_type,
        search_key=search_key,
        item_key=item_key,
        observations_count=len(observations),
        observations=observations,
    )
