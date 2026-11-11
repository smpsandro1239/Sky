import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.deps import get_db
from app.database.base import Base
from app.main import app
from app.models import AuthIdentity, ParticipantBudget, Trip, TripParticipant, User  # noqa: F401

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


def register_and_login(client: TestClient, email: str) -> str:
    response = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": PASSWORD, "display_name": "Budget Tester"},
    )
    assert response.status_code == 201
    login = client.post("/api/v1/auth/login", json={"email": email, "password": PASSWORD})
    assert login.status_code == 200
    return login.json()["access_token"]


def auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def create_trip(client: TestClient, token: str) -> str:
    response = client.post(
        "/api/v1/trips", headers=auth(token),
        json={"name": "Viagem", "destination": "Porto"},
    )
    assert response.status_code == 201
    return response.json()["id"]


def create_participant(client: TestClient, token: str, trip_id: str) -> str:
    response = client.post(
        f"/api/v1/trips/{trip_id}/participants", headers=auth(token),
        json={"name": "Ana"},
    )
    assert response.status_code == 201
    return response.json()["id"]


def test_participant_budget_can_be_created_updated_listed_and_deleted(client: TestClient) -> None:
    token = register_and_login(client, "participant-budget@example.com")
    trip_id = create_trip(client, token)
    participant_id = create_participant(client, token, trip_id)
    url = f"/api/v1/trips/{trip_id}/participants/{participant_id}/budgets"
    headers = auth(token)

    created = client.put(url, headers=headers, json={"amount": "450.00", "currency": "eur"})
    assert created.status_code == 200
    assert created.json()["amount"] == "450.00"
    assert created.json()["currency"] == "EUR"

    updated = client.put(url, headers=headers, json={"amount": "525.50", "currency": "EUR"})
    assert updated.status_code == 200
    assert updated.json()["id"] == created.json()["id"]
    assert updated.json()["amount"] == "525.50"

    listed = client.get(url, headers=headers)
    assert listed.status_code == 200
    assert len(listed.json()) == 1
    assert listed.json()[0]["amount"] == "525.50"

    deleted = client.delete(f"{url}/EUR", headers=headers)
    assert deleted.status_code == 204
    assert client.get(url, headers=headers).json() == []


def test_participant_budget_rejects_invalid_amount_currency_and_foreign_participant(client: TestClient) -> None:
    token = register_and_login(client, "participant-budget-validation@example.com")
    trip_id = create_trip(client, token)
    participant_id = create_participant(client, token, trip_id)
    other_trip = create_trip(client, token)
    foreign_participant = create_participant(client, token, other_trip)
    url = f"/api/v1/trips/{trip_id}/participants/{participant_id}/budgets"
    headers = auth(token)

    assert client.put(url, headers=headers, json={"amount": "-1", "currency": "EUR"}).status_code == 422
    assert client.put(url, headers=headers, json={"amount": "10", "currency": "EURO"}).status_code == 422
    foreign_url = f"/api/v1/trips/{trip_id}/participants/{foreign_participant}/budgets"
    assert client.put(foreign_url, headers=headers, json={"amount": "10", "currency": "EUR"}).status_code == 404


def test_participant_budget_requires_trip_access_and_editor_role(client: TestClient) -> None:
    owner = register_and_login(client, "participant-budget-owner@example.com")
    other = register_and_login(client, "participant-budget-other@example.com")
    trip_id = create_trip(client, owner)
    participant_id = create_participant(client, owner, trip_id)
    url = f"/api/v1/trips/{trip_id}/participants/{participant_id}/budgets"

    assert client.get(url, headers=auth(other)).status_code == 404
    assert client.put(url, headers=auth(other), json={"amount": "100", "currency": "EUR"}).status_code == 404
