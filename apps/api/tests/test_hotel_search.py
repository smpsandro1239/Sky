from datetime import date
from decimal import Decimal

import pytest

from app.api.routes.hotel_search import _map_offers
from app.schemas.hotel_search import HotelSearchRequest


def test_hotel_search_normalizes_city_and_currency():
    criteria = HotelSearchRequest(
        city_code=" lis ",
        check_in="2027-08-10",
        check_out="2027-08-15",
        currency="eur",
    )
    assert criteria.city_code == "LIS"
    assert criteria.currency == "EUR"


def test_hotel_search_rejects_invalid_stay():
    with pytest.raises(ValueError):
        HotelSearchRequest(city_code="LIS", check_in="2027-08-10", check_out="2027-08-10")
    with pytest.raises(ValueError):
        HotelSearchRequest(city_code="LIS", check_in="2027-08-10", check_out="2027-09-15")


def test_amadeus_hotel_offers_are_normalized_and_sorted():
    criteria = HotelSearchRequest(city_code="LIS", check_in="2027-08-10", check_out="2027-08-15")
    results = [
        {
            "hotel": {"hotelId": "HOTEL002", "name": "Hotel B", "address": {"cityName": "Lisbon", "countryCode": "PT"}},
            "offers": [{"id": "offer-b", "price": {"total": "520.00", "currency": "EUR"}}],
        },
        {
            "hotel": {"hotelId": "HOTEL001", "name": "Hotel A", "address": {"cityName": "Lisbon", "countryCode": "PT"}},
            "offers": [{"id": "offer-a", "price": {"total": "410.50", "currency": "EUR"}, "room": {"description": {"text": "Quarto duplo"}}}],
        },
    ]
    offers = _map_offers(results, criteria)
    assert [item.id for item in offers] == ["offer-a", "offer-b"]
    assert offers[0].price_total == Decimal("410.50")
    assert offers[0].hotel_name == "Hotel A"
    assert offers[0].location == "Lisbon, PT"


def test_hotel_search_requires_valid_iata_city_code():
    with pytest.raises(ValueError):
        HotelSearchRequest(city_code="Lisbon", check_in=date(2027, 8, 10), check_out=date(2027, 8, 11))


def test_amadeus_mapper_ignores_malformed_and_non_finite_offers():
    criteria = HotelSearchRequest(city_code="LIS", check_in="2027-08-10", check_out="2027-08-12")
    results = [
        None,
        {"hotel": None, "offers": [{"id": "missing-hotel", "price": {"total": "100", "currency": "EUR"}}]},
        {
            "hotel": {"hotelId": "HOTEL003", "name": "Hotel C"},
            "offers": [
                None,
                {"id": "no-price"},
                {"id": "infinite", "price": {"total": "Infinity", "currency": "EUR"}},
                {"id": "bad-currency", "price": {"total": "100", "currency": "EURO"}},
                {"id": "valid", "price": {"total": "125.00", "currency": "EUR"}},
            ],
        },
    ]
    offers = _map_offers(results, criteria)
    assert len(offers) == 1
    assert offers[0].id == "valid"
    assert offers[0].price_total == Decimal("125.00")


def test_amadeus_mapper_uses_stable_sort_for_equal_prices():
    criteria = HotelSearchRequest(city_code="LIS", check_in="2027-08-10", check_out="2027-08-12")
    results = [
        {"hotel": {"hotelId": "B", "name": "Hotel Z"}, "offers": [{"id": "z", "price": {"total": "100", "currency": "EUR"}}]},
        {"hotel": {"hotelId": "A", "name": "Hotel A"}, "offers": [{"id": "a", "price": {"total": "100", "currency": "EUR"}}]},
    ]
    assert [offer.id for offer in _map_offers(results, criteria)] == ["a", "z"]



def test_amadeus_mapper_exposes_only_returned_cancellation_and_payment_terms():
    criteria = HotelSearchRequest(city_code="LIS", check_in="2027-08-10", check_out="2027-08-12")
    results = [
        {
            "hotel": {"hotelId": "HOTEL004", "name": "Hotel D"},
            "offers": [
                {
                    "id": "with-policies",
                    "price": {"total": "250.00", "currency": "EUR"},
                    "policies": {
                        "paymentType": "GUARANTEE",
                        "cancellation": {
                            "deadline": "2027-08-08T23:59:00+01:00",
                            "description": {"text": "Cancelamento gratuito até à data indicada."},
                        },
                    },
                },
                {
                    "id": "without-policies",
                    "price": {"total": "260.00", "currency": "EUR"},
                },
            ],
        }
    ]

    offers = _map_offers(results, criteria)

    assert offers[0].payment_type == "GUARANTEE"
    assert offers[0].cancellation_deadline == "2027-08-08T23:59:00+01:00"
    assert offers[0].cancellation_description == "Cancelamento gratuito até à data indicada."
    assert offers[1].payment_type is None
    assert offers[1].cancellation_deadline is None
    assert offers[1].cancellation_description is None


def test_amadeus_mapper_ignores_malformed_policy_values():
    criteria = HotelSearchRequest(city_code="LIS", check_in="2027-08-10", check_out="2027-08-12")
    results = [
        {
            "hotel": {"hotelId": "HOTEL005", "name": "Hotel E"},
            "offers": [
                {
                    "id": "malformed-policies",
                    "price": {"total": "180.00", "currency": "EUR"},
                    "policies": {
                        "paymentType": {"unexpected": "object"},
                        "cancellation": {
                            "deadline": 12345,
                            "description": "not-an-object",
                        },
                    },
                }
            ],
        }
    ]

    offer = _map_offers(results, criteria)[0]

    assert offer.payment_type is None
    assert offer.cancellation_deadline is None
    assert offer.cancellation_description is None
