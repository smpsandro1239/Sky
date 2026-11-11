from datetime import date
from decimal import Decimal

from app.schemas.hotel_search import HotelSearchOffer
from app.services.hotel_recommendations import rank_hotel_offers


def _hotel(
    offer_id: str,
    price: str,
    cancellation: str | None = None,
    check_in: date = date(2027, 8, 10),
    check_out: date = date(2027, 8, 15),
) -> HotelSearchOffer:
    return HotelSearchOffer(
        id=offer_id,
        price_tracking_key="hotel:test-" + offer_id,
        provider="amadeus",
        hotel_name="Hotel " + offer_id,
        hotel_id="HOTEL-" + offer_id,
        location="Lisbon, PT",
        check_in=check_in,
        check_out=check_out,
        price_total=Decimal(price),
        currency="EUR",
        cancellation_description=cancellation,
    )


def test_hotel_ranking_prefers_lowest_price_when_terms_are_unknown():
    offers = [
        _hotel("expensive", "600.00"),
        _hotel("cheap", "400.00"),
    ]

    ranked = rank_hotel_offers(offers)

    assert [offer.id for offer in ranked] == ["cheap", "expensive"]
    assert ranked[0].nights == 5
    assert ranked[0].price_per_night == Decimal("80.00")
    assert ranked[0].recommendation_score == 100.0
    assert ranked[0].recommendation_reasons == ["Melhor preço por noite"]


def test_hotel_ranking_rewards_only_explicit_free_cancellation():
    offers = [
        _hotel("refundable", "500.00", "Cancelamento gratuito até 8 de agosto."),
        _hotel("nonrefundable", "450.00", "Non-refundable rate."),
        _hotel("unknown", "475.00", "Condições especiais aplicáveis."),
    ]

    ranked = rank_hotel_offers(offers)

    refundable = next(offer for offer in ranked if offer.id == "refundable")
    nonrefundable = next(offer for offer in ranked if offer.id == "nonrefundable")
    unknown = next(offer for offer in ranked if offer.id == "unknown")

    assert "Cancelamento gratuito indicado" in refundable.recommendation_reasons
    assert nonrefundable.recommendation_score is not None
    assert unknown.recommendation_score is not None
    assert "Cancelamento gratuito indicado" not in unknown.recommendation_reasons


def test_hotel_ranking_handles_single_offer_and_empty_results():
    offer = _hotel("only", "300.00")

    ranked = rank_hotel_offers([offer])

    assert ranked[0].recommendation_score == 100.0
    assert ranked[0].recommendation_reasons == [
        "Única oferta devolvida para estes critérios"
    ]
    assert rank_hotel_offers([]) == []


def test_hotel_ranking_does_not_calculate_price_per_night_for_invalid_stay():
    offer = _hotel(
        "invalid-stay",
        "300.00",
        check_in=date(2027, 8, 10),
        check_out=date(2027, 8, 10),
    )

    ranked = rank_hotel_offers([offer])

    assert ranked[0].nights is None
    assert ranked[0].price_per_night is None
    assert ranked[0].recommendation_score == 0.0
