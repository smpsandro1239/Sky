from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.price_alert import PriceAlert
from app.models.price_observation import PriceObservation
from app.models.user import User
from app.schemas.price_alert import PriceAlertCreate, PriceAlertResponse, PriceAlertUpdate

router = APIRouter(prefix="/prices/alerts", tags=["price-intelligence"])


@router.get("", response_model=list[PriceAlertResponse])
def list_price_alerts(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[PriceAlert]:
    return list(db.scalars(
        select(PriceAlert)
        .where(PriceAlert.user_id == user.id)
        .order_by(PriceAlert.created_at.desc())
    ).all())


@router.post("", response_model=PriceAlertResponse, status_code=status.HTTP_201_CREATED)
def create_price_alert(
    payload: PriceAlertCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> PriceAlert:
    observed = db.scalar(
        select(PriceObservation).where(
            PriceObservation.user_id == user.id,
            PriceObservation.search_type == payload.search_type,
            PriceObservation.search_key == payload.search_key,
            PriceObservation.item_key == payload.item_key,
            PriceObservation.currency == payload.currency,
            PriceObservation.is_available.is_(True),
        ).order_by(PriceObservation.captured_at.desc()).limit(1)
    )
    if observed is None:
        raise HTTPException(
            status_code=404,
            detail="Não existe uma oferta disponível correspondente no teu histórico de preços.",
        )

    alert = PriceAlert(user_id=user.id, **payload.model_dump())
    if observed.amount <= payload.target_price:
        alert.is_active = False
        alert.triggered_price = observed.amount
        alert.triggered_at = datetime.now(timezone.utc)
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return alert


@router.patch("/{alert_id}", response_model=PriceAlertResponse)
def update_price_alert(
    alert_id: UUID,
    payload: PriceAlertUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> PriceAlert:
    alert = db.scalar(select(PriceAlert).where(
        PriceAlert.id == alert_id,
        PriceAlert.user_id == user.id,
    ))
    if alert is None:
        raise HTTPException(status_code=404, detail="Alerta não encontrado.")
    if payload.is_active and alert.triggered_at is not None:
        raise HTTPException(
            status_code=409,
            detail="Este alerta já foi atingido. Cria um novo alerta para definir outro objetivo.",
        )
    alert.is_active = payload.is_active
    db.commit()
    db.refresh(alert)
    return alert


@router.delete("/{alert_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_price_alert(
    alert_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Response:
    alert = db.scalar(select(PriceAlert).where(
        PriceAlert.id == alert_id,
        PriceAlert.user_id == user.id,
    ))
    if alert is None:
        raise HTTPException(status_code=404, detail="Alerta não encontrado.")
    db.delete(alert)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
