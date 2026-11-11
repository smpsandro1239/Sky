"""Worker periódico de monitorização de alertas de preço.

Executar como processo separado: python -m app.price_monitor_worker
Cada pesquisa activa é limitada por uma chave Redis com TTL para evitar chamadas excessivas.
"""
import asyncio
import logging
import time
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

import redis
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.database.session import SessionLocal
from app.models.price_alert import PriceAlert
from app.models.price_observation import PriceObservation
from app.services.amadeus_flights import amadeus_flight_provider
from app.services.amadeus_hotels import amadeus_hotel_provider
from app.services.hotel_recommendations import rank_hotel_offers
from app.services.price_intelligence import record_price_observations
from app.services.recommendations import rank_flight_offers
from app.api.routes.flight_search import _map_offer
from app.api.routes.hotel_search import _map_offers
from app.schemas.flight_search import FlightSearchRequest
from app.schemas.hotel_search import HotelSearchRequest

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [sky-price-monitor] %(message)s",
)
logger = logging.getLogger("sky.price_monitor")


def _active_searches(db: Session) -> list[dict[str, Any]]:
    alerts = db.scalars(
        select(PriceAlert).where(
            PriceAlert.is_active.is_(True),
            PriceAlert.triggered_at.is_(None),
        )
    ).all()
    grouped: dict[tuple[UUID, str, str], dict[str, Any]] = {}
    for alert in alerts:
        key = (alert.user_id, alert.search_type, alert.search_key)
        if key in grouped:
            continue
        latest = db.scalar(
            select(PriceObservation)
            .where(
                PriceObservation.user_id == alert.user_id,
                PriceObservation.search_type == alert.search_type,
                PriceObservation.search_key == alert.search_key,
            )
            .order_by(PriceObservation.captured_at.desc())
            .limit(1)
        )
        if latest is None or not isinstance(latest.search_criteria, dict):
            logger.warning("Sem critérios guardados para pesquisa %s", alert.search_key)
            continue
        grouped[key] = {
            "user_id": alert.user_id,
            "search_type": alert.search_type,
            "search_key": alert.search_key,
            "criteria": latest.search_criteria,
            "last_captured_at": latest.captured_at,
        }
    return list(grouped.values())


async def _fetch_observations(search: dict[str, Any]) -> list[dict[str, Any]]:
    search_type = search["search_type"]
    criteria_data = search["criteria"]
    if search_type == "flight":
        criteria = FlightSearchRequest.model_validate(criteria_data)
        raw = await amadeus_flight_provider.search(criteria.model_dump())
        offers = rank_flight_offers([_map_offer(item) for item in raw])
        return [
            {
                "item_key": offer.price_tracking_key,
                "item_name": f"{criteria.origin} → {criteria.destination}",
                "provider": offer.provider,
                "amount": offer.price_total,
                "currency": offer.currency,
                "is_available": True,
            }
            for offer in offers
        ]
    if search_type == "hotel":
        criteria = HotelSearchRequest.model_validate(criteria_data)
        raw = await amadeus_hotel_provider.search(criteria.model_dump())
        offers = rank_hotel_offers(_map_offers(raw, criteria))
        return [
            {
                "item_key": offer.price_tracking_key,
                "item_name": offer.hotel_name,
                "provider": offer.provider,
                "amount": offer.price_total,
                "currency": offer.currency,
                "is_available": True,
            }
            for offer in offers
        ]
    raise ValueError(f"Tipo de pesquisa não suportado: {search_type}")


def monitor_once(client: redis.Redis, db: Session) -> int:
    searches = _active_searches(db)
    completed = 0
    for search in searches:
        lock_key = (
            f"sky:price-monitor:{search['user_id']}:"
            f"{search['search_type']}:{search['search_key']}"
        )
        last_captured_at = search["last_captured_at"]
        if last_captured_at.tzinfo is None:
            last_captured_at = last_captured_at.replace(tzinfo=timezone.utc)
        remaining = settings.price_monitor_interval_seconds - int(
            (datetime.now(timezone.utc) - last_captured_at).total_seconds()
        )
        if remaining > 0:
            client.set(lock_key, "recent-database-capture", nx=True, ex=remaining)
            continue
        acquired = client.set(
            lock_key,
            str(int(time.time())),
            nx=True,
            ex=settings.price_monitor_interval_seconds,
        )
        if not acquired:
            continue
        try:
            observations = asyncio.run(_fetch_observations(search))
            record_price_observations(
                db,
                user_id=search["user_id"],
                search_type=search["search_type"],
                criteria=search["criteria"],
                observations=observations,
            )
            completed += 1
            logger.info(
                "Pesquisa monitorizada: tipo=%s chave=%s ofertas=%d",
                search["search_type"],
                search["search_key"],
                len(observations),
            )
        except Exception:
            db.rollback()
            logger.exception(
                "Falha ao monitorizar %s (%s)",
                search["search_type"],
                search["search_key"],
            )
            client.expire(lock_key, settings.price_monitor_retry_seconds)
    return completed


def main() -> None:
    client = redis.Redis.from_url(settings.redis_url, decode_responses=True)
    client.ping()
    logger.info(
        "Worker iniciado; intervalo=%ds, polling=%ds",
        settings.price_monitor_interval_seconds,
        settings.price_monitor_poll_seconds,
    )
    while True:
        try:
            with SessionLocal() as db:
                monitor_once(client, db)
        except Exception:
            logger.exception("Erro no ciclo de monitorização.")
        time.sleep(settings.price_monitor_poll_seconds)


if __name__ == "__main__":
    main()
