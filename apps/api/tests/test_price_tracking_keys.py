from datetime import date

from app.api.routes.flight_search import _map_offer
from app.api.routes.hotel_search import _map_offers
from app.schemas.hotel_search import HotelSearchRequest


def _flight_offer(offer_id: str, price: str, departure: str = "2027-08-10T08:00:00") -> dict:
    return {
        "id": offer_id,
        "price": {"grandTotal": price, "currency": "EUR"},
        "itineraries": [
            {
                "segments": [
                    {
                        "carrierCode": "TP",
                        "number": "100",
                        "departure": {"iataCode": "OPO", "at": departure},
                        "arrival": {"iataCode": "LHR", "at": "2027-08-10T10:00:00"},
                    }
                ]
            }
        ],
        "travelerPricings": [
            {
                "fareDetailsBySegment": [
                    {"cabin": "ECONOMY", "class": "Y", "fareBasis": "YLOW"}
                ]
            }
        ],
    }


def test_flight_tracking_key_survives_provider_id_and_price_changes():
    first = _map_offer(_flight_offer("provider-id-1", "150.00"))
    second = _map_offer(_flight_offer("provider-id-2", "135.00"))

    assert first.id != second.id
    assert first.price_total != second.price_total
    assert first.price_tracking_key == second.price_tracking_key


def test_flight_tracking_key_changes_when_itinerary_changes():
    first = _map_offer(_flight_offer("provider-id-1", "150.00"))
    changed = _map_offer(
        _flight_offer("provider-id-2", "150.00", departure="2027-08-10T09:00:00")
    )

    assert first.price_tracking_key != changed.price_tracking_key


def test_hotel_tracking_key_survives_provider_id_and_price_changes():
    criteria = HotelSearchRequest(
        city_code="LIS",
        check_in=date(2027, 8, 10),
        check_out=date(2027, 8, 15),
    )

    def result(offer_id: str, price: str) -> list[dict]:
        return [
            {
                "hotel": {
                    "hotelId": "HOTEL-123",
                    "name": "Hotel Example",
                    "address": {"cityName": "Lisbon", "countryCode": "PT"},
                },
                "offers": [
                    {
                        "id": offer_id,
                        "price": {"total": price, "currency": "EUR"},
                        "room": {"description": {"text": "Double room"}},
                        "boardType": "BREAKFAST",
                        "policies": {
                            "paymentType": "guarantee",
                            "cancellation": {
                                "deadline": "2027-08-08T23:59:00",
                                "description": {"text": "Free cancellation"},
                            },
                        },
                    }
                ],
            }
        ]

    first = _map_offers(result("provider-id-1", "500.00"), criteria)[0]
    second = _map_offers(result("provider-id-2", "450.00"), criteria)[0]

    assert first.id != second.id
    assert first.price_total != second.price_total
    assert first.price_tracking_key == second.price_tracking_key
