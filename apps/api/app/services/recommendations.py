from datetime import datetime
from decimal import Decimal
from app.schemas.flight_search import FlightSearchOffer


_WEIGHTS = {
    "price": 0.50,
    "duration": 0.30,
    "stops": 0.20,
}


def _offer_duration_minutes(offer: FlightSearchOffer) -> int | None:
    total_minutes = 0
    found_itinerary = False

    for itinerary in offer.itineraries:
        if not itinerary:
            continue
        try:
            departure = datetime.fromisoformat(
                itinerary[0].departure_at.replace("Z", "+00:00")
            )
            arrival = datetime.fromisoformat(
                itinerary[-1].arrival_at.replace("Z", "+00:00")
            )
            duration = (arrival - departure).total_seconds() / 60
        except (TypeError, ValueError):
            return None
        if duration <= 0:
            return None
        total_minutes += round(duration)
        found_itinerary = True

    return total_minutes if found_itinerary else None


def _normalise(values: list[Decimal | int | None]) -> list[float | None]:
    available = [float(value) for value in values if value is not None]
    if not available:
        return [None for _ in values]

    minimum = min(available)
    maximum = max(available)
    if maximum == minimum:
        return [100.0 if value is not None else None for value in values]

    return [
        None if value is None else 100.0 * (maximum - float(value)) / (maximum - minimum)
        for value in values
    ]


def rank_flight_offers(offers: list[FlightSearchOffer]) -> list[FlightSearchOffer]:
    """Rank offers within one search using price, elapsed journey time and stops.

    Scores are relative to the supplied result set; they are not a prediction
    of quality or a comparison across different searches.
    """
    if not offers:
        return []

    durations = [_offer_duration_minutes(offer) for offer in offers]
    price_scores = _normalise([offer.price_total for offer in offers])
    duration_scores = _normalise(durations)
    stop_scores = _normalise([offer.number_of_stops for offer in offers])

    ranked: list[FlightSearchOffer] = []
    for index, offer in enumerate(offers):
        dimensions = (
            ("price", price_scores[index], "Melhor preço"),
            ("duration", duration_scores[index], "Menor duração"),
            ("stops", stop_scores[index], "Menos escalas"),
        )
        weighted_score = 0.0
        available_weight = 0.0
        reasons: list[str] = []

        for key, score, reason in dimensions:
            if score is None:
                continue
            weight = _WEIGHTS[key]
            weighted_score += score * weight
            available_weight += weight
            if score == 100.0 and len(offers) > 1:
                reasons.append(reason)

        score = round(weighted_score / available_weight, 1) if available_weight else 0.0
        if len(offers) == 1:
            reasons = ["Única oferta devolvida para estes critérios"]
        elif not reasons:
            reasons = ["Melhor equilíbrio entre os critérios avaliados"]

        ranked.append(
            offer.model_copy(
                update={
                    "duration_minutes": durations[index],
                    "recommendation_score": score,
                    "recommendation_reasons": reasons,
                }
            )
        )

    ranked.sort(
        key=lambda offer: (
            -(offer.recommendation_score or 0.0),
            offer.price_total,
            offer.number_of_stops,
            offer.id,
        )
    )
    return ranked
