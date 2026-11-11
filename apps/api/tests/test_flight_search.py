import pytest
from decimal import Decimal
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.deps import get_db
from app.core.config import settings
from app.database.base import Base
from app.main import app
from app.models import Accommodation, AuthIdentity, Flight, Trip, User  # noqa: F401
from app.schemas.flight_search import FlightSearchRequest
from app.api.routes.flight_search import _map_offer

PASSWORD = "Correct-Horse-Battery-2026!"


@pytest.fixture()
def client() -> TestClient:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    testing_session = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        with testing_session() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


def register_and_login(client: TestClient) -> str:
    client.post(
        "/api/v1/auth/register",
        json={"email": "flight-search@example.com", "password": PASSWORD, "display_name": "Flight Tester"},
    )
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "flight-search@example.com", "password": PASSWORD},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def test_flight_search_requires_authentication(client: TestClient) -> None:
    response = client.get(
        "/api/v1/flights/search",
        params={"origin": "OPO", "destination": "LIS", "departure_date": "2027-08-10"},
    )
    assert response.status_code == 401


def test_flight_search_reports_missing_provider_configuration(client: TestClient, monkeypatch) -> None:
    monkeypatch.setattr(settings, "amadeus_client_id", None)
    monkeypatch.setattr(settings, "amadeus_client_secret", None)
    token = register_and_login(client)

    response = client.get(
        "/api/v1/flights/search",
        headers={"Authorization": f"Bearer {token}"},
        params={"origin": "opo", "destination": "lis", "departure_date": "2027-08-10"},
    )

    assert response.status_code == 503
    assert "Amadeus" in response.json()["detail"]


def test_flight_search_rejects_same_airport_and_invalid_dates() -> None:
    with pytest.raises(ValueError):
        FlightSearchRequest(
            origin="OPO",
            destination="opo",
            departure_date="2027-08-10",
        )

    with pytest.raises(ValueError):
        FlightSearchRequest(
            origin="OPO",
            destination="LIS",
            departure_date="2027-08-10",
            return_date="2027-08-10",
        )


def test_flight_search_normalizes_iata_and_currency_codes() -> None:
    criteria = FlightSearchRequest(
        origin=" opo ",
        destination="lis",
        departure_date="2027-08-10",
        currency="eur",
    )
    assert criteria.origin == "OPO"
    assert criteria.destination == "LIS"
    assert criteria.currency == "EUR"


def test_amadeus_offer_is_normalized_for_comparison() -> None:
    offer = _map_offer(
        {
            "id": "offer-1",
            "price": {"grandTotal": "149.90", "currency": "eur"},
            "itineraries": [
                {
                    "segments": [
                        {
                            "carrierCode": "TP",
                            "number": "1923",
                            "departure": {"iataCode": "OPO", "at": "2027-08-10T08:00:00"},
                            "arrival": {"iataCode": "LIS", "at": "2027-08-10T09:00:00"},
                        },
                        {
                            "carrierCode": "TP",
                            "number": "1924",
                            "departure": {"iataCode": "LIS", "at": "2027-08-10T10:00:00"},
                            "arrival": {"iataCode": "FNC", "at": "2027-08-10T11:00:00"},
                        },
                    ]
                }
            ],
        }
    )
    assert offer.price_total == Decimal("149.90")
    assert offer.currency == "EUR"
    assert offer.number_of_stops == 1
    assert offer.itineraries[0][0].origin == "OPO"


def test_flight_search_returns_422_for_invalid_route(client: TestClient) -> None:
    token = register_and_login(client)
    response = client.get(
        "/api/v1/flights/search",
        headers={"Authorization": f"Bearer {token}"},
        params={"origin": "OPO", "destination": "opo", "departure_date": "2027-08-10"},
    )
    assert response.status_code == 422
