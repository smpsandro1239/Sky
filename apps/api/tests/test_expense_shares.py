import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.deps import get_db
from app.database.base import Base
from app.main import app
from app.models import Accommodation, AuthIdentity, Expense, ExpenseShare, Flight, Trip, TripParticipant, User  # noqa: F401

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


def register_and_login(client: TestClient, email: str) -> str:
    response = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": PASSWORD, "display_name": "Share Tester"},
    )
    assert response.status_code == 201
    login = client.post("/api/v1/auth/login", json={"email": email, "password": PASSWORD})
    assert login.status_code == 200
    return login.json()["access_token"]


def auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def create_trip(client: TestClient, token: str, name: str = "Viagem") -> str:
    response = client.post(
        "/api/v1/trips",
        headers=auth(token),
        json={"name": name, "destination": "Porto"},
    )
    assert response.status_code == 201
    return response.json()["id"]


def create_expense(client: TestClient, token: str, trip_id: str, amount: str = "30.00") -> str:
    response = client.post(
        f"/api/v1/trips/{trip_id}/expenses",
        headers=auth(token),
        json={
            "category": "alimentacao",
            "description": "Jantar de grupo",
            "expense_date": "2027-08-02",
            "amount": amount,
            "currency": "EUR",
        },
    )
    assert response.status_code == 201
    return response.json()["id"]


def create_participant(client: TestClient, token: str, trip_id: str, name: str) -> str:
    response = client.post(
        f"/api/v1/trips/{trip_id}/participants",
        headers=auth(token),
        json={"name": name},
    )
    assert response.status_code == 201
    return response.json()["id"]


def test_expense_shares_must_sum_to_expense_total(client: TestClient) -> None:
    token = register_and_login(client, "shares-total@example.com")
    trip_id = create_trip(client, token)
    expense_id = create_expense(client, token, trip_id, "10.01")
    first = create_participant(client, token, trip_id, "Ana")
    second = create_participant(client, token, trip_id, "Rui")
    url = f"/api/v1/trips/{trip_id}/expenses/{expense_id}/shares"
    headers = auth(token)

    invalid = client.patch(
        url, headers=headers,
        json=[
            {"participant_id": first, "amount": "5.00"},
            {"participant_id": second, "amount": "5.00"},
        ],
    )
    assert invalid.status_code == 422
    assert "soma" in invalid.json()["detail"]

    saved = client.patch(
        url, headers=headers,
        json=[
            {"participant_id": first, "amount": "5.01"},
            {"participant_id": second, "amount": "5.00"},
        ],
    )
    assert saved.status_code == 200
    assert {item["participant_id"]: item["amount"] for item in saved.json()} == {
        first: "5.01",
        second: "5.00",
    }
    listed = client.get(url, headers=headers)
    assert listed.status_code == 200
    assert len(listed.json()) == 2


def test_expense_shares_reject_foreign_and_duplicate_participants(client: TestClient) -> None:
    token = register_and_login(client, "shares-scope@example.com")
    trip_id = create_trip(client, token, "Viagem A")
    other_trip_id = create_trip(client, token, "Viagem B")
    expense_id = create_expense(client, token, trip_id, "20.00")
    local_id = create_participant(client, token, trip_id, "Pessoa local")
    foreign_id = create_participant(client, token, other_trip_id, "Pessoa externa")
    url = f"/api/v1/trips/{trip_id}/expenses/{expense_id}/shares"
    headers = auth(token)

    foreign = client.patch(
        url, headers=headers,
        json=[{"participant_id": foreign_id, "amount": "20.00"}],
    )
    assert foreign.status_code == 422

    duplicate = client.patch(
        url, headers=headers,
        json=[
            {"participant_id": local_id, "amount": "10.00"},
            {"participant_id": local_id, "amount": "10.00"},
        ],
    )
    assert duplicate.status_code == 422


def test_participant_with_shares_cannot_be_deleted_and_shares_can_be_cleared(client: TestClient) -> None:
    token = register_and_login(client, "shares-delete@example.com")
    trip_id = create_trip(client, token)
    expense_id = create_expense(client, token, trip_id, "12.00")
    participant_id = create_participant(client, token, trip_id, "Pessoa")
    shares_url = f"/api/v1/trips/{trip_id}/expenses/{expense_id}/shares"
    headers = auth(token)

    saved = client.patch(
        shares_url, headers=headers,
        json=[{"participant_id": participant_id, "amount": "12.00"}],
    )
    assert saved.status_code == 200
    assert client.delete(
        f"/api/v1/trips/{trip_id}/participants/{participant_id}", headers=headers
    ).status_code == 409

    cleared = client.patch(shares_url, headers=headers, json=[])
    assert cleared.status_code == 200
    assert cleared.json() == []
    assert client.delete(
        f"/api/v1/trips/{trip_id}/participants/{participant_id}", headers=headers
    ).status_code == 204


def test_expense_shares_require_trip_ownership(client: TestClient) -> None:
    owner = register_and_login(client, "shares-owner@example.com")
    other = register_and_login(client, "shares-other@example.com")
    trip_id = create_trip(client, owner)
    expense_id = create_expense(client, owner, trip_id)
    url = f"/api/v1/trips/{trip_id}/expenses/{expense_id}/shares"

    assert client.get(url, headers=auth(other)).status_code == 404
    assert client.patch(url, headers=auth(other), json=[]).status_code == 404
