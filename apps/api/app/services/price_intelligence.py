import hashlib
import json
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy.orm import Session

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


def record_price_observations(
    db: Session,
    *,
    user_id: UUID,
    search_type: str,
    criteria: dict[str, Any],
    observations: list[dict[str, Any]],
) -> str:
    """Guarda apenas preços efetivamente recebidos do fornecedor nesta pesquisa."""
    search_key = build_search_fingerprint(search_type, criteria)
    if not observations:
        return search_key

    capture_id = uuid4()
    rows: list[PriceObservation] = []
    for item in observations:
        amount = Decimal(str(item["amount"]))
        currency = str(item["currency"]).upper()
        item_key = str(item["item_key"]).strip()
        item_name = str(item["item_name"]).strip()
        provider = str(item["provider"]).strip().lower()
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
        db.commit()
    return search_key
