from decimal import Decimal

from app.schemas.flight_search import FlightSearchOffer, FlightSearchSegment
from app.services.recommendations import rank_flight_offers


def _offer(
    offer_id: str,
    price: str,
    stops: int,
    departure: str,
    arrival: str,
) -> FlightSearchOffer:
    return FlightSearchOffer(
        id=offer_id,
        price_tracking_key="flight:test-" + offer_id,
        provider="amadeus",
        price_total=Decimal(price),
        currency="EUR",
        number_of_stops=stops,
        itineraries=[
            [
                FlightSearchSegment(
                    carrier="TP",
                    flight_number="100",
                    origin="OPO",
                    destination="LHR",
                    departure_at=departure,
                    arrival_at=arrival,
                )
            ]
        ],
    )


def test_flight_recommendations_rank_best_combination_first():
    offers = [
        _offer("balanced", "150.00", 0, "2027-08-10T08:00:00Z", "2027-08-10T12:00:00Z"),
        _offer("expensive-slow", "200.00", 1, "2027-08-10T08:00:00Z", "2027-08-10T13:00:00Z"),
        _offer("best", "100.00", 0, "2027-08-10T08:00:00Z", "2027-08-10T11:00:00Z"),
    ]

    ranked = rank_flight_offers(offers)

    assert [offer.id for offer in ranked] == ["best", "balanced", "expensive-slow"]
    assert ranked[0].recommendation_score == 100.0
    assert ranked[0].duration_minutes == 180
    assert "Melhor preço" in ranked[0].recommendation_reasons
    assert "Menor duração" in ranked[0].recommendation_reasons


def test_flight_recommendations_handle_missing_duration():
    valid = _offer("valid", "100.00", 0, "2027-08-10T08:00:00Z", "2027-08-10T10:00:00Z")
    invalid_time = _offer("invalid-time", "200.00", 1, "not-a-date", "also-not-a-date")

    ranked = rank_flight_offers([invalid_time, valid])

    assert ranked[0].id == "valid"
    assert ranked[0].duration_minutes == 120
    assert ranked[1].duration_minutes is None
    assert ranked[1].recommendation_score is not None


def test_flight_recommendations_return_empty_list_for_no_offers():
    assert rank_flight_offers([]) == []


def test_single_flight_offer_is_explained_without_false_comparison():
    offer = _offer("only", "120.00", 0, "2027-08-10T08:00:00Z", "2027-08-10T10:00:00Z")

    ranked = rank_flight_offers([offer])

    assert ranked[0].recommendation_score == 100.0
    assert ranked[0].recommendation_reasons == [
        "Única oferta devolvida para estes critérios"
    ]
