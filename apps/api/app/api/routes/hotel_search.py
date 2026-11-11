from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.encoders import jsonable_encoder
from pydantic import ValidationError

from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.hotel_search import HotelSearchRequest, HotelSearchOffer, HotelSearchResponse
from app.services.amadeus_hotels import (
    HotelProviderError,
    HotelProviderNotConfigured,
    amadeus_hotel_provider,
)

router = APIRouter(prefix="/hotels", tags=["hotel-search"])


def _map_offers(hotel_results: list[dict[str, Any]], criteria: HotelSearchRequest) -> list[HotelSearchOffer]:
    offers: list[HotelSearchOffer] = []
    for result in hotel_results:
        hotel = result.get("hotel") or {}
        hotel_id = str(hotel.get("hotelId", ""))
        hotel_name = str(hotel.get("name", "")).strip()
        address = hotel.get("address") or {}
        city = str(address.get("cityName") or criteria.city_code)
        country = str(address.get("countryCode") or "")
        location = ", ".join(part for part in (city, country) if part)
        for offer in result.get("offers", []):
            price = offer.get("price") or {}
            try:
                total = Decimal(str(price.get("total", "")))
                currency = str(price.get("currency", criteria.currency)).upper()
                offer_id = str(offer.get("id", ""))
                if not hotel_id or not hotel_name or not offer_id or total <= 0:
                    continue
                room = offer.get("room") or {}
                description = room.get("description") or {}
                board = offer.get("boardType")
                offers.append(
                    HotelSearchOffer(
                        id=offer_id,
                        provider="amadeus",
                        hotel_name=hotel_name,
                        hotel_id=hotel_id,
                        location=location,
                        check_in=criteria.check_in,
                        check_out=criteria.check_out,
                        price_total=total,
                        currency=currency,
                        room_description=description.get("text"),
                        board_type=board,
                    )
                )
            except (InvalidOperation, ValueError, TypeError):
                continue
    offers.sort(key=lambda item: item.price_total)
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
    _: User = Depends(get_current_user),
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
        offers = _map_offers(raw_results, criteria)
    except HotelProviderNotConfigured as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Pesquisa externa indisponível: configura as credenciais Amadeus no ambiente da API.",
        ) from exc
    except HotelProviderError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

    return HotelSearchResponse(provider="amadeus", results_count=len(offers), offers=offers)
