from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.database.base import Base
from app.models import Notification, PriceAlert, PriceObservation, User
from app.services.price_intelligence import evaluate_price_alerts, price_alert_matches


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


def test_alert_does_not_match_non_positive_price():
    assert not price_alert_matches(
        observed_price=Decimal("0"),
        currency="EUR",
        target_price=Decimal("120.00"),
        alert_currency="EUR",
    )


def test_triggered_price_alert_creates_persistent_notification():
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    user_id = uuid4()
    search_key = "a" * 64
    item_key = "flight:" + "b" * 64
    try:
        with Session(engine) as db:
            db.add(User(id=user_id, email="price-alert-notification@example.com"))
            alert = PriceAlert(
                user_id=user_id,
                search_type="flight",
                search_key=search_key,
                item_key=item_key,
                item_name="OPO-LHR",
                currency="EUR",
                target_price=Decimal("150.00"),
                is_active=True,
            )
            db.add(alert)
            db.flush()
            observation = PriceObservation(
                capture_id=uuid4(),
                user_id=user_id,
                search_type="flight",
                search_key=search_key,
                provider="amadeus",
                item_key=item_key,
                item_name="OPO-LHR",
                amount=Decimal("129.90"),
                currency="EUR",
                is_available=True,
                search_criteria={"origin": "OPO", "destination": "LHR"},
            )
            db.add(observation)
            db.flush()

            count = evaluate_price_alerts(
                db,
                user_id=user_id,
                search_type="flight",
                search_key=search_key,
                observations=[observation],
            )
            db.commit()

            notifications = list(db.scalars(select(Notification).where(Notification.user_id == user_id)).all())
            assert count == 1
            assert len(notifications) == 1
            assert notifications[0].notification_type == "price_alert_triggered"
            assert notifications[0].metadata_json["alert_id"] == str(alert.id)
            assert notifications[0].read_at is None
            assert alert.is_active is False
            assert alert.triggered_at is not None
    finally:
        Base.metadata.drop_all(bind=engine)
        engine.dispose()
