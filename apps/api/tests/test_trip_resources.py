from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient
import pytest

from app.api.deps import get_db
from app.database.base import Base
from app.main import app
from app.models import Accommodation, AuthIdentity, Flight, Trip, User  # noqa: F401

TEST_DATABASE_URL = "sqlite+pysqlite:///:memory:"
PASSWORD = "Correct-Horse-Battery-2026!"


@pytest.fixture()
def client() -> TestClient:
    engine = create_engine(
        TEST_DATABASE_URL,
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


def create_trip(client: TestClient, email: str) -> tuple[str, str]:
    registration = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": PASSWORD, "display_name": "Resource Tester"},
    )
    assert registration.status_code == 201
    login = client.post("/api/v1/auth/login", json={"email": email, "password": PASSWORD})
    assert login.status_code == 200
    token = login.json()["access_token"]
    created = client.post(
        "/api/v1/trips",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "Viagem de teste", "destination": "Lisboa"},
    )
    assert created.status_code == 201
    return token, created.json()["id"]


def headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_user_can_add_and_list_flights_for_trip(client: TestClient) -> None:
    token, trip_id = create_trip(client, "flight-owner@example.com")
    payload = {
        "provider": "Companhia exemplo",
        "origin": "opo",
        "destination": "lis",
        "departure_at": "2027-08-01T08:00:00Z",
        "arrival_at": "2027-08-01T09:00:00Z",
        "price_amount": "89.90",
        "price_currency": "eur",
    }
    created = client.post(
        f"/api/v1/trips/{trip_id}/flights", headers=headers(token), json=payload
    )
    assert created.status_code == 201
    assert created.json()["origin"] == "OPO"
    assert created.json()["destination"] == "LIS"
    assert created.json()["price_currency"] == "EUR"

    listed = client.get(f"/api/v1/trips/{trip_id}/flights", headers=headers(token))
    assert listed.status_code == 200
    assert len(listed.json()) == 1


def test_user_can_add_and_list_accommodations_for_trip(client: TestClient) -> None:
    token, trip_id = create_trip(client, "stay-owner@example.com")
    payload = {
        "provider": "Fornecedor exemplo",
        "name": "Hotel Central",
        "location": "Lisboa",
        "check_in": "2027-08-01",
        "check_out": "2027-08-05",
        "price_amount": "420.00",
        "price_currency": "eur",
    }
    created = client.post(
        f"/api/v1/trips/{trip_id}/accommodations",
        headers=headers(token),
        json=payload,
    )
    assert created.status_code == 201
    assert created.json()["name"] == "Hotel Central"
    assert created.json()["price_currency"] == "EUR"

    listed = client.get(
        f"/api/v1/trips/{trip_id}/accommodations", headers=headers(token)
    )
    assert listed.status_code == 200
    assert len(listed.json()) == 1


def test_trip_resources_reject_invalid_data_and_other_users(client: TestClient) -> None:
    owner_token, trip_id = create_trip(client, "resource-owner@example.com")
    other_token, _ = create_trip(client, "resource-other@example.com")

    invalid_flight = client.post(
        f"/api/v1/trips/{trip_id}/flights",
        headers=headers(owner_token),
        json={
            "origin": "OPO",
            "destination": "OPO",
            "departure_at": "2027-08-01T08:00:00Z",
        },
    )
    assert invalid_flight.status_code == 422

    invalid_stay = client.post(
        f"/api/v1/trips/{trip_id}/accommodations",
        headers=headers(owner_token),
        json={
            "name": "Hotel",
            "location": "Lisboa",
            "check_in": "2027-08-05",
            "check_out": "2027-08-01",
        },
    )
    assert invalid_stay.status_code == 422

    assert client.get(
        f"/api/v1/trips/{trip_id}/flights", headers=headers(other_token)
    ).status_code == 404
    assert client.get(
        f"/api/v1/trips/{trip_id}/accommodations", headers=headers(other_token)
    ).status_code == 404


def test_user_can_update_and_delete_flight(client: TestClient) -> None:
    token, trip_id = create_trip(client, "flight-update@example.com")
    created = client.post(
        f"/api/v1/trips/{trip_id}/flights",
        headers=headers(token),
        json={
            "origin": "OPO",
            "destination": "LIS",
            "departure_at": "2027-08-01T08:00:00Z",
            "price_amount": "50.00",
        },
    )
    assert created.status_code == 201
    flight_id = created.json()["id"]

    updated = client.patch(
        f"/api/v1/trips/{trip_id}/flights/{flight_id}",
        headers=headers(token),
        json={"price_amount": "75.50", "destination": "FNC"},
    )
    assert updated.status_code == 200
    assert updated.json()["destination"] == "FNC"
    assert updated.json()["price_amount"] == "75.50"

    invalid = client.patch(
        f"/api/v1/trips/{trip_id}/flights/{flight_id}",
        headers=headers(token),
        json={"destination": "OPO"},
    )
    assert invalid.status_code == 422

    deleted = client.delete(
        f"/api/v1/trips/{trip_id}/flights/{flight_id}", headers=headers(token)
    )
    assert deleted.status_code == 204
    assert client.get(
        f"/api/v1/trips/{trip_id}/flights", headers=headers(token)
    ).json() == []


def test_user_can_update_and_delete_accommodation(client: TestClient) -> None:
    token, trip_id = create_trip(client, "accommodation-update@example.com")
    created = client.post(
        f"/api/v1/trips/{trip_id}/accommodations",
        headers=headers(token),
        json={
            "name": "Hotel Central",
            "location": "Lisboa",
            "check_in": "2027-08-01",
            "check_out": "2027-08-05",
            "price_amount": "400.00",
        },
    )
    assert created.status_code == 201
    accommodation_id = created.json()["id"]

    updated = client.patch(
        f"/api/v1/trips/{trip_id}/accommodations/{accommodation_id}",
        headers=headers(token),
        json={"name": "Hotel Renovado", "check_out": "2027-08-06"},
    )
    assert updated.status_code == 200
    assert updated.json()["name"] == "Hotel Renovado"
    assert updated.json()["check_out"] == "2027-08-06"

    invalid = client.patch(
        f"/api/v1/trips/{trip_id}/accommodations/{accommodation_id}",
        headers=headers(token),
        json={"check_out": "2027-07-31"},
    )
    assert invalid.status_code == 422

    deleted = client.delete(
        f"/api/v1/trips/{trip_id}/accommodations/{accommodation_id}",
        headers=headers(token),
    )
    assert deleted.status_code == 204
    assert client.get(
        f"/api/v1/trips/{trip_id}/accommodations", headers=headers(token)
    ).json() == []


def test_user_cannot_modify_another_users_flight_or_accommodation(
    client: TestClient,
) -> None:
    owner_token, trip_id = create_trip(client, "resource-edit-owner@example.com")
    other_token, _ = create_trip(client, "resource-edit-other@example.com")

    flight = client.post(
        f"/api/v1/trips/{trip_id}/flights",
        headers=headers(owner_token),
        json={
            "origin": "OPO",
            "destination": "LIS",
            "departure_at": "2027-08-01T08:00:00Z",
        },
    ).json()
    accommodation = client.post(
        f"/api/v1/trips/{trip_id}/accommodations",
        headers=headers(owner_token),
        json={
            "name": "Hotel Central",
            "location": "Lisboa",
            "check_in": "2027-08-01",
            "check_out": "2027-08-05",
        },
    ).json()

    assert client.patch(
        f"/api/v1/trips/{trip_id}/flights/{flight['id']}",
        headers=headers(other_token),
        json={"destination": "FNC"},
    ).status_code == 404
    assert client.delete(
        f"/api/v1/trips/{trip_id}/accommodations/{accommodation['id']}",
        headers=headers(other_token),
    ).status_code == 404
