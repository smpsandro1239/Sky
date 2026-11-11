from decimal import Decimal

from app.schemas.hotel_search import HotelSearchOffer


_FREE_CANCELLATION_PHRASES = (
    "free cancellation",
    "free cancelation",
    "cancelamento gratuito",
    "cancelamento grátis",
    "annulation gratuite",
    "kostenlose stornierung",
    "cancellazione gratuita",
)


def _has_explicit_free_cancellation(offer: HotelSearchOffer) -> bool | None:
    description = (offer.cancellation_description or "").casefold()
    if not description.strip():
        return None
    return any(phrase in description for phrase in _FREE_CANCELLATION_PHRASES)


def _normalise_lower_is_better(values: list[Decimal | None]) -> list[float | None]:
    available = [float(value) for value in values if value is not None]
    if not available:
        return [None for _ in values]
    minimum, maximum = min(available), max(available)
    if maximum == minimum:
        return [100.0 if value is not None else None for value in values]
    return [
        None if value is None else 100.0 * (maximum - float(value)) / (maximum - minimum)
        for value in values
    ]


def rank_hotel_offers(offers: list[HotelSearchOffer]) -> list[HotelSearchOffer]:
    """Rank hotel offers by comparable stay price and explicitly stated free cancellation.

    Scores are relative to this result set. Cancellation contributes only when
    the provider supplied a description; missing terms are never treated as
    refundable or non-refundable.
    """
    if not offers:
        return []

    nights = [(offer.check_out - offer.check_in).days for offer in offers]
    prices_per_night = [
        (offer.price_total / Decimal(night_count)).quantize(Decimal("0.01"))
        if night_count > 0 else None
        for offer, night_count in zip(offers, nights)
    ]
    price_scores = _normalise_lower_is_better(prices_per_night)
    cancellation_values = [_has_explicit_free_cancellation(offer) for offer in offers]

    ranked: list[HotelSearchOffer] = []
    for index, offer in enumerate(offers):
        price_score = price_scores[index]
        cancellation_score = (
            100.0 if cancellation_values[index] is True
            else 0.0 if cancellation_values[index] is False
            else None
        )
        weighted_score = 0.0
        available_weight = 0.0
        reasons: list[str] = []

        if price_score is not None:
            weighted_score += price_score * 0.70
            available_weight += 0.70
            if price_score == 100.0 and len(offers) > 1:
                reasons.append("Melhor preço por noite")

        if cancellation_score is not None:
            weighted_score += cancellation_score * 0.30
            available_weight += 0.30
            if cancellation_score == 100.0:
                reasons.append("Cancelamento gratuito indicado")

        score = round(weighted_score / available_weight, 1) if available_weight else 0.0
        if len(offers) == 1:
            reasons = ["Única oferta devolvida para estes critérios"]
        elif not reasons:
            reasons = ["Melhor equilíbrio entre preço e condições indicadas"]

        ranked.append(
            offer.model_copy(
                update={
                    "nights": nights[index] if nights[index] > 0 else None,
                    "price_per_night": prices_per_night[index],
                    "recommendation_score": score,
                    "recommendation_reasons": reasons,
                }
            )
        )

    ranked.sort(
        key=lambda offer: (
            -(offer.recommendation_score or 0.0),
            offer.price_total,
            offer.hotel_name.casefold(),
            offer.id,
        )
    )
    return ranked
