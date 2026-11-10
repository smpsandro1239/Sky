import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.deps import get_db
from app.database.base import Base
from app.main import app
from app.models import Accommodation, AuthIdentity, Expense, Flight, Trip, TripParticipant, User  # noqa: F401

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
    registration = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": PASSWORD, "display_name": "Participant Tester"},
    )
    assert registration.status_code == 201
    login = client.post("/api/v1/auth/login", json={"email": email, "password": PASSWORD})
    assert login.status_code == 200
    return login.json()["access_token"]


def auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def create_trip(client: TestClient, token: str) -> str:
    response = client.post(
        "/api/v1/trips",
        headers=auth(token),
        json={"name": "Viagem de grupo", "destination": "Madeira"},
    )
    assert response.status_code == 201
    return response.json()["id"]


def test_participants_can_be_created_listed_and_deleted(client: TestClient) -> None:
    token = register_and_login(client, "participants@example.com")
    trip_id = create_trip(client, token)
    headers = auth(token)
    url = f"/api/v1/trips/{trip_id}/participants"

    created = client.post(
        url, headers=headers, json={"name": " Ana Silva ", "email": " ANA@EXAMPLE.COM "}
    )
    assert created.status_code == 201
    participant = created.json()
    assert participant["name"] == "Ana Silva"
    assert participant["email"] == "ana@example.com"
    assert participant["trip_id"] == trip_id

    listed = client.get(url, headers=headers)
    assert listed.status_code == 200
    assert [item["id"] for item in listed.json()] == [participant["id"]]

    deleted = client.delete(f"{url}/{participant['id']}", headers=headers)
    assert deleted.status_code == 204
    assert client.get(url, headers=headers).json() == []


def test_participants_require_trip_ownership(client: TestClient) -> None:
    owner = register_and_login(client, "participant-owner@example.com")
    other = register_and_login(client, "participant-other@example.com")
    trip_id = create_trip(client, owner)
    url = f"/api/v1/trips/{trip_id}/participants"

    assert client.get(url, headers=auth(other)).status_code == 404
    assert client.post(
        url, headers=auth(other), json={"name": "Pessoa externa"}
    ).status_code == 404


def test_participant_validation_and_scoped_deletion(client: TestClient) -> None:
    token = register_and_login(client, "participant-validation@example.com")
    trip_id = create_trip(client, token)
    headers = auth(token)
    url = f"/api/v1/trips/{trip_id}/participants"

    assert client.post(url, headers=headers, json={"name": " "}).status_code == 422
    assert client.post(
        url, headers=headers, json={"name": "Pessoa", "email": "email-invalido"}
    ).status_code == 422
    assert client.delete(
        f"{url}/00000000-0000-4000-8000-000000000000", headers=headers
    ).status_code == 404


def test_deleting_trip_cascades_to_participants(client: TestClient) -> None:
    token = register_and_login(client, "participant-cascade@example.com")
    trip_id = create_trip(client, token)
    headers = auth(token)
    response = client.post(
        f"/api/v1/trips/{trip_id}/participants",
        headers=headers,
        json={"name": "Pessoa a remover"},
    )
    assert response.status_code == 201

    assert client.delete(f"/api/v1/trips/{trip_id}", headers=headers).status_code == 204
    assert client.get(f"/api/v1/trips/{trip_id}/participants", headers=headers).status_code == 404
