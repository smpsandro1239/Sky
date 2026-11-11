import hashlib
import json
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.price_alert import PriceAlert
from app.models.price_observation import PriceObservation


def build_search_fingerprint(search_type: str, criteria: dict[str, Any]) -> str:
    """Cria uma chave estável para critérios equivalentes, sem incluir dados do utilizador."""
    if search_type not in {"flight", "hotel"}:
        raise ValueError("Tipo de pesquisa inválido.")
    canonical = json.dumps(
        {"type": search_type, "criteria": criteria},
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        default=str,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def price_alert_matches(
    *, observed_price: Decimal, currency: str, target_price: Decimal, alert_currency: str
) -> bool:
    """Compara preços apenas na mesma moeda; o alerta dispara no preço-alvo ou abaixo."""
    return (
        currency.upper() == alert_currency.upper()
        and observed_price.is_finite()
        and observed_price > 0
        and observed_price <= target_price
    )


def evaluate_price_alerts(
    db: Session,
    *,
    user_id: UUID,
    search_type: str,
    search_key: str,
    observations: list[PriceObservation],
) -> int:
    """Marca como atingidos os alertas compatíveis com as novas ofertas desta captura."""
    available = {
        (item.item_key, item.currency.upper()): item
        for item in observations
        if item.is_available
    }
    if not available:
        return 0

    alerts = db.scalars(
        select(PriceAlert).where(
            PriceAlert.user_id == user_id,
            PriceAlert.search_type == search_type,
            PriceAlert.search_key == search_key,
            PriceAlert.is_active.is_(True),
            PriceAlert.triggered_at.is_(None),
        )
    ).all()
    triggered = 0
    now = datetime.now(timezone.utc)
    for alert in alerts:
        observed = available.get((alert.item_key, alert.currency.upper()))
        if observed is None:
            continue
        if price_alert_matches(
            observed_price=observed.amount,
            currency=observed.currency,
            target_price=alert.target_price,
            alert_currency=alert.currency,
        ):
            alert.is_active = False
            alert.triggered_price = observed.amount
            alert.triggered_at = now
            triggered += 1
    return triggered


def record_price_observations(
    db: Session,
    *,
    user_id: UUID,
    search_type: str,
    criteria: dict[str, Any],
    observations: list[dict[str, Any]],
) -> str:
    """Guarda preços reais do fornecedor e avalia alertas pessoais na mesma captura."""
    search_key = build_search_fingerprint(search_type, criteria)
    if not observations:
        return search_key

    capture_id = uuid4()
    rows: list[PriceObservation] = []
    for item in observations:
        try:
            amount = Decimal(str(item["amount"]))
            currency = str(item["currency"]).upper()
            item_key = str(item["item_key"]).strip()
            item_name = str(item["item_name"]).strip()
            provider = str(item["provider"]).strip().lower()
        except (KeyError, TypeError, ValueError):
            continue
        if (
            not amount.is_finite()
            or amount <= 0
            or len(currency) != 3
            or not currency.isalpha()
            or not item_key
            or len(item_key) > 160
            or not item_name
            or len(item_name) > 200
            or not provider
            or len(provider) > 40
        ):
            continue
        rows.append(
            PriceObservation(
                capture_id=capture_id,
                user_id=user_id,
                search_type=search_type,
                search_key=search_key,
                provider=provider,
                item_key=item_key,
                item_name=item_name[:200],
                amount=amount,
                currency=currency,
                is_available=bool(item.get("is_available", True)),
                search_criteria=criteria,
            )
        )

    if rows:
        db.add_all(rows)
        db.flush()
        evaluate_price_alerts(
            db,
            user_id=user_id,
            search_type=search_type,
            search_key=search_key,
            observations=rows,
        )
        db.commit()
    return search_key
