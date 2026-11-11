from decimal import Decimal


def price_alert_matches(
    *, observed_price: Decimal, currency: str, target_price: Decimal, alert_currency: str
) -> bool:
    """A comparação é válida apenas na mesma moeda e ao atingir ou ultrapassar o objetivo."""
    return (
        currency.upper() == alert_currency.upper()
        and observed_price > 0
        and observed_price <= target_price
    )


def test_alert_matches_when_price_reaches_target():
    assert price_alert_matches(
        observed_price=Decimal("119.99"),
        currency="EUR",
        target_price=Decimal("120.00"),
        alert_currency="EUR",
    )


def test_alert_does_not_match_above_target_or_in_another_currency():
    assert not price_alert_matches(
        observed_price=Decimal("120.01"),
        currency="EUR",
        target_price=Decimal("120.00"),
        alert_currency="EUR",
    )
    assert not price_alert_matches(
        observed_price=Decimal("99.00"),
        currency="USD",
        target_price=Decimal("120.00"),
        alert_currency="EUR",
    )
