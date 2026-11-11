from datetime import date
from decimal import Decimal
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.flight_search import (
    FlightSearchOffer,
    FlightSearchRequest,
    FlightSearchResponse,
    FlightSearchSegment,
)
from app.services.amadeus_flights import (
    FlightProviderError,
    FlightProviderNotConfigured,
    amadeus_flight_provider,
)

router = APIRouter(prefix="/flights", tags=["flight-search"])


def _map_offer(offer: dict[str, Any]) -> FlightSearchOffer:
    itineraries: list[list[FlightSearchSegment]] = []
    stop_count = 0

    for itinerary in offer.get("itineraries", []):
        segments: list[FlightSearchSegment] = []
        raw_segments = itinerary.get("segments", [])
        stop_count += max(len(raw_segments) - 1, 0)
        for segment in raw_segments:
            departure = segment.get("departure", {})
            arrival = segment.get("arrival", {})
            segments.append(
                FlightSearchSegment(
                    carrier=segment.get("carrierCode", ""),
                    flight_number=segment.get("number", ""),
                    origin=departure.get("iataCode", ""),
                    destination=arrival.get("iataCode", ""),
                    departure_at=departure.get("at", ""),
                    arrival_at=arrival.get("at", ""),
                )
            )
        itineraries.append(segments)

    price = offer.get("price", {})
    return FlightSearchOffer(
        id=str(offer.get("id", "")),
        provider="amadeus",
        price_total=Decimal(str(price.get("grandTotal", price.get("total", "0")))),
        currency=str(price.get("currency", "EUR")).upper(),
        number_of_stops=stop_count,
        itineraries=itineraries,
    )


@router.get("/search", response_model=FlightSearchResponse)
async def search_flights(
    origin: str = Query(min_length=3, max_length=3),
    destination: str = Query(min_length=3, max_length=3),
    departure_date: date = Query(),
    return_date: date | None = Query(default=None),
    adults: int = Query(default=1, ge=1, le=9),
    currency: str = Query(default="EUR", min_length=3, max_length=3),
    non_stop: bool = Query(default=False),
    max_results: int = Query(default=20, ge=1, le=50),
    _: User = Depends(get_current_user),
) -> FlightSearchResponse:
    criteria = FlightSearchRequest(
        origin=origin,
        destination=destination,
        departure_date=departure_date,
        return_date=return_date,
        adults=adults,
        currency=currency,
        non_stop=non_stop,
        max_results=max_results,
    )

    try:
        raw_offers = await amadeus_flight_provider.search(criteria.model_dump())
        offers = [_map_offer(offer) for offer in raw_offers]
    except FlightProviderNotConfigured as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Pesquisa externa indisponível: configura as credenciais Amadeus no ambiente da API.",
        ) from exc
    except FlightProviderError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc
    except (KeyError, ValueError, TypeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="O fornecedor devolveu uma oferta inválida.",
        ) from exc

    offers.sort(key=lambda item: (item.price_total, item.number_of_stops))
    return FlightSearchResponse(provider="amadeus", results_count=len(offers), offers=offers)
