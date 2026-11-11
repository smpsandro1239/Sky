import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.deps import get_db
from app.database.base import Base
from app.main import app
from app.models.notification import Notification
from app.models.user import User

PASSWORD = "Correct-Horse-Battery-2026!"


@pytest.fixture()
def client():
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


def register_and_login(client, email):
    registered = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": PASSWORD, "display_name": "Notification Tester"},
    )
    assert registered.status_code == 201
    response = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": PASSWORD},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def create_notification(client, token, title="Preço atingido"):
    response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    user_id = response.json()["id"]
    # The test uses the same dependency-overridden SQLite database as the API.
    db = next(app.dependency_overrides[get_db]())
    try:
        db.add(Notification(
            user_id=UUID(user_id),
            notification_type="price_alert_triggered",
            title=title,
            message="O voo OPO-LHR atingiu o preço definido.",
            link="/dashboard",
            metadata_json={"alert_id": "test-alert"},
        ))
        db.commit()
    finally:
        db.close()


def test_notifications_are_private_and_return_unread_count(client):
    owner = register_and_login(client, "notifications-owner@example.com")
    other = register_and_login(client, "notifications-other@example.com")
    create_notification(client, owner)

    own = client.get("/api/v1/notifications", headers={"Authorization": f"Bearer {owner}"})
    assert own.status_code == 200
    assert own.json()["unread_count"] == 1
    assert len(own.json()["items"]) == 1
    assert own.json()["items"][0]["notification_type"] == "price_alert_triggered"
    assert own.json()["items"][0]["metadata_json"]["alert_id"] == "test-alert"

    private = client.get("/api/v1/notifications", headers={"Authorization": f"Bearer {other}"})
    assert private.status_code == 200
    assert private.json()["items"] == []
    assert private.json()["unread_count"] == 0


def test_notifications_can_be_marked_read_individually_and_in_bulk(client):
    token = register_and_login(client, "notifications-read@example.com")
    create_notification(client, token, "Primeiro alerta")
    create_notification(client, token, "Segundo alerta")
    headers = {"Authorization": f"Bearer {token}"}

    listing = client.get("/api/v1/notifications", headers=headers)
    assert listing.status_code == 200
    assert listing.json()["unread_count"] == 2
    first_id = listing.json()["items"][0]["id"]

    marked = client.patch(f"/api/v1/notifications/{first_id}/read", headers=headers)
    assert marked.status_code == 200
    assert marked.json()["read_at"] is not None

    remaining = client.get("/api/v1/notifications?unread_only=true", headers=headers)
    assert remaining.status_code == 200
    assert len(remaining.json()["items"]) == 1
    assert remaining.json()["unread_count"] == 1

    all_read = client.post("/api/v1/notifications/read-all", headers=headers)
    assert all_read.status_code == 200
    assert all_read.json()["updated"] == 1

    final = client.get("/api/v1/notifications", headers=headers)
    assert final.json()["unread_count"] == 0


def test_notifications_require_authentication(client):
    response = client.get("/api/v1/notifications")
    assert response.status_code == 401
