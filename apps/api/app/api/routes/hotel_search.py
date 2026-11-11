from datetime import date
from uuid import UUID
from decimal import Decimal, InvalidOperation
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from fastapi.encoders import jsonable_encoder
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.models.hotel_favorite import HotelFavorite
from app.schemas.hotel_favorite import HotelFavoriteCreate, HotelFavoriteResponse
from app.schemas.hotel_search import HotelSearchRequest, HotelSearchOffer, HotelSearchResponse
from app.services.hotel_recommendations import rank_hotel_offers
from app.services.price_intelligence import build_item_fingerprint, record_price_observations
from app.services.amadeus_hotels import (
    HotelProviderError,
    HotelProviderNotConfigured,
    amadeus_hotel_provider,
)

router = APIRouter(prefix="/hotels", tags=["hotel-search"])


def _map_offers(hotel_results: list[dict[str, Any]], criteria: HotelSearchRequest) -> list[HotelSearchOffer]:
    offers: list[HotelSearchOffer] = []
    for result in hotel_results:
        if not isinstance(result, dict):
            continue
        hotel = result.get("hotel")
        if not isinstance(hotel, dict):
            continue
        hotel_id = str(hotel.get("hotelId", "")).strip()
        hotel_name = str(hotel.get("name", "")).strip()
        address = hotel.get("address")
        address = address if isinstance(address, dict) else {}
        city = str(address.get("cityName") or criteria.city_code).strip()
        country = str(address.get("countryCode") or "").strip().upper()
        location = ", ".join(part for part in (city, country) if part)
        raw_offers = result.get("offers")
        if not isinstance(raw_offers, list):
            continue
        for offer in raw_offers:
            if not isinstance(offer, dict):
                continue
            price = offer.get("price")
            if not isinstance(price, dict):
                continue
            try:
                total = Decimal(str(price.get("total", "")))
                currency = str(price.get("currency", criteria.currency)).strip().upper()
                offer_id = str(offer.get("id", "")).strip()
                if (
                    not hotel_id
                    or not hotel_name
                    or not offer_id
                    or not total.is_finite()
                    or total <= 0
                    or len(currency) != 3
                    or not currency.isalpha()
                ):
                    continue
                room = offer.get("room")
                room = room if isinstance(room, dict) else {}
                description = room.get("description")
                description = description if isinstance(description, dict) else {}
                board = offer.get("boardType")
                policies = offer.get("policies")
                policies = policies if isinstance(policies, dict) else {}
                cancellation = policies.get("cancellation")
                cancellation = cancellation if isinstance(cancellation, dict) else {}
                cancellation_description = cancellation.get("description")
                cancellation_description = cancellation_description if isinstance(cancellation_description, dict) else {}
                payment_type = policies.get("paymentType")
                cancellation_deadline = cancellation.get("deadline")
                cancellation_text = cancellation_description.get("text")
                stable_identity = {
                    "hotel_id": hotel_id,
                    "room_description": str(description.get("text") or "").strip().casefold(),
                    "board_type": str(board or "").strip().upper(),
                    "payment_type": str(payment_type or "").strip().upper(),
                    "cancellation_deadline": str(cancellation_deadline or "").strip(),
                    "cancellation_description": str(cancellation_text or "").strip().casefold(),
                }
                offers.append(
                    HotelSearchOffer(
                        id=offer_id,
                        price_tracking_key=build_item_fingerprint("hotel", stable_identity),
                        provider="amadeus",
                        hotel_name=hotel_name,
                        hotel_id=hotel_id,
                        location=location,
                        check_in=criteria.check_in,
                        check_out=criteria.check_out,
                        price_total=total,
                        currency=currency,
                        room_description=description.get("text"),
                        board_type=str(board)[:80] if isinstance(board, str) and board.strip() else None,
                        payment_type=str(payment_type)[:80] if isinstance(payment_type, str) and payment_type.strip() else None,
                        cancellation_deadline=str(cancellation_deadline)[:80] if isinstance(cancellation_deadline, str) and cancellation_deadline.strip() else None,
                        cancellation_description=str(cancellation_text)[:500] if isinstance(cancellation_text, str) and cancellation_text.strip() else None,
                    )
                )
            except (InvalidOperation, ValueError, TypeError):
                continue
    offers.sort(key=lambda item: (item.price_total, item.hotel_name.casefold(), item.id))
    return offers


@router.get("/search", response_model=HotelSearchResponse)
async def search_hotels(
    city_code: str = Query(min_length=3, max_length=3),
    check_in: date = Query(),
    check_out: date = Query(),
    adults: int = Query(default=2, ge=1, le=9),
    room_quantity: int = Query(default=1, ge=1, le=8),
    currency: str = Query(default="EUR", min_length=3, max_length=3),
    radius: int = Query(default=20, ge=1, le=50),
    max_hotels: int = Query(default=20, ge=1, le=40),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> HotelSearchResponse:
    try:
        criteria = HotelSearchRequest(
            city_code=city_code,
            check_in=check_in,
            check_out=check_out,
            adults=adults,
            room_quantity=room_quantity,
            currency=currency,
            radius=radius,
            max_hotels=max_hotels,
        )
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=jsonable_encoder(exc.errors())) from exc

    try:
        raw_results = await amadeus_hotel_provider.search(criteria.model_dump())
        offers = rank_hotel_offers(_map_offers(raw_results, criteria))
    except HotelProviderNotConfigured as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Pesquisa externa indisponível: configura as credenciais Amadeus no ambiente da API.",
        ) from exc
    except HotelProviderError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

    criteria_data = criteria.model_dump(mode="json")
    search_key = record_price_observations(
        db,
        user_id=user.id,
        search_type="hotel",
        criteria=criteria_data,
        observations=[
            {
                "item_key": offer.price_tracking_key,
                "item_name": offer.hotel_name,
                "provider": offer.provider,
                "amount": offer.price_total,
                "currency": offer.currency,
                "is_available": True,
            }
            for offer in offers
        ],
    )
    return HotelSearchResponse(
        provider="amadeus", results_count=len(offers), search_key=search_key, offers=offers
    )



@router.get("/favorites", response_model=list[HotelFavoriteResponse])
def list_hotel_favorites(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[HotelFavorite]:
    statement = (
        select(HotelFavorite)
        .where(HotelFavorite.user_id == user.id)
        .order_by(HotelFavorite.hotel_name)
    )
    return list(db.scalars(statement).all())


@router.post("/favorites", response_model=HotelFavoriteResponse)
def create_hotel_favorite(
    payload: HotelFavoriteCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> HotelFavorite:
    existing = db.scalar(
        select(HotelFavorite).where(
            HotelFavorite.user_id == user.id,
            HotelFavorite.hotel_id == payload.hotel_id,
        )
    )
    if existing is not None:
        return existing

    favorite = HotelFavorite(user_id=user.id, **payload.model_dump())
    db.add(favorite)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        existing = db.scalar(
            select(HotelFavorite).where(
                HotelFavorite.user_id == user.id,
                HotelFavorite.hotel_id == payload.hotel_id,
            )
        )
        if existing is not None:
            return existing
        raise
    db.refresh(favorite)
    return favorite


@router.delete("/favorites/{favorite_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_hotel_favorite(
    favorite_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Response:
    favorite = db.scalar(
        select(HotelFavorite).where(
            HotelFavorite.id == favorite_id,
            HotelFavorite.user_id == user.id,
        )
    )
    if favorite is None:
        raise HTTPException(status_code=404, detail="Favorito não encontrado.")
    db.delete(favorite)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
