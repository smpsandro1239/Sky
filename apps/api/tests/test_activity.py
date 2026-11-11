import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.deps import get_db
from app.database.base import Base
from app.main import app
from app.models import TripActivity  # noqa: F401

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
        json={"email": email, "password": PASSWORD, "display_name": "Activity Tester"},
    )
    assert response.status_code == 201
    login = client.post("/api/v1/auth/login", json={"email": email, "password": PASSWORD})
    assert login.status_code == 200
    return login.json()["access_token"]


def test_trip_activity_records_changes_and_supports_pagination(client: TestClient) -> None:
    token = register_and_login(client, "activity-owner@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    created = client.post(
        "/api/v1/trips",
        headers=headers,
        json={"name": "Viagem com histórico", "destination": "Porto"},
    )
    assert created.status_code == 201
    trip_id = created.json()["id"]

    updated = client.patch(
        f"/api/v1/trips/{trip_id}",
        headers=headers,
        json={"destination": "Braga"},
    )
    assert updated.status_code == 200

    page = client.get(f"/api/v1/trips/{trip_id}/activity?limit=1", headers=headers)
    assert page.status_code == 200
    data = page.json()
    assert len(data["items"]) == 1
    assert data["has_more"] is True
    assert data["items"][0]["action"] == "updated"
    assert data["items"][0]["actor_name"] == "Activity Tester"
    assert "token" not in data["items"][0]["summary"].lower()

    older = client.get(
        f"/api/v1/trips/{trip_id}/activity?limit=1&offset=1", headers=headers
    )
    assert older.status_code == 200
    assert older.json()["items"][0]["action"] == "created"
    assert older.json()["has_more"] is False


def test_trip_activity_requires_access_to_trip(client: TestClient) -> None:
    owner_token = register_and_login(client, "activity-private@example.com")
    other_token = register_and_login(client, "activity-outsider@example.com")
    trip = client.post(
        "/api/v1/trips",
        headers={"Authorization": f"Bearer {owner_token}"},
        json={"name": "Privada", "destination": "Lisboa"},
    ).json()
    response = client.get(
        f"/api/v1/trips/{trip['id']}/activity",
        headers={"Authorization": f"Bearer {other_token}"},
    )
    assert response.status_code == 404


def test_trip_activity_requires_authentication(client: TestClient) -> None:
    response = client.get(
        "/api/v1/trips/00000000-0000-4000-8000-000000000000/activity"
    )
    assert response.status_code == 401
