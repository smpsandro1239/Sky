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

def test_participant_changes_are_recorded_without_exposing_email(client: TestClient) -> None:
    token = register_and_login(client, "activity-participant-owner@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    trip = client.post(
        "/api/v1/trips",
        headers=headers,
        json={"name": "Viagem de grupo", "destination": "Madeira"},
    ).json()
    trip_id = trip["id"]

    created = client.post(
        f"/api/v1/trips/{trip_id}/participants",
        headers=headers,
        json={"name": "Convidado", "email": "guest@example.com"},
    )
    assert created.status_code == 201
    participant_id = created.json()["id"]

    updated = client.patch(
        f"/api/v1/trips/{trip_id}/participants/{participant_id}",
        headers=headers,
        json={"role": "editor"},
    )
    assert updated.status_code == 200
    assert updated.json()["role"] == "editor"

    history = client.get(
        f"/api/v1/trips/{trip_id}/activity?limit=20",
        headers=headers,
    )
    assert history.status_code == 200
    events = history.json()["items"]
    assert any(item["entity_type"] == "participant" and item["action"] == "created" for item in events)
    assert any(item["entity_type"] == "participant" and item["action"] == "updated" for item in events)
    assert all("guest@example.com" not in item["summary"] for item in events)


def test_shared_members_can_read_activity_and_viewers_cannot_write(client: TestClient) -> None:
    owner = register_and_login(client, "activity-shared-owner@example.com")
    editor = register_and_login(client, "activity-shared-editor@example.com")
    viewer = register_and_login(client, "activity-shared-viewer@example.com")
    owner_headers = {"Authorization": f"Bearer {owner}"}
    trip = client.post(
        "/api/v1/trips",
        headers=owner_headers,
        json={"name": "Viagem partilhada", "destination": "Açores"},
    )
    assert trip.status_code == 201
    trip_id = trip.json()["id"]

    invitations = []
    for email, role in [
        ("activity-shared-editor@example.com", "editor"),
        ("activity-shared-viewer@example.com", "viewer"),
    ]:
        response = client.post(
            f"/api/v1/trips/{trip_id}/invitations",
            headers=owner_headers,
            json={"email": email, "role": role},
        )
        assert response.status_code == 201
        invitations.append(response.json())

    for token, invitation in [(editor, invitations[0]), (viewer, invitations[1])]:
        accepted = client.post(
            "/api/v1/invitations/accept",
            headers={"Authorization": f"Bearer {token}"},
            json={"token": invitation["invitation_token"]},
        )
        assert accepted.status_code == 200

    flight_payload = {
        "origin": "OPO",
        "destination": "PDL",
        "departure_at": "2027-08-01T08:00:00Z",
    }
    editor_headers = {"Authorization": f"Bearer {editor}"}
    created_flight = client.post(
        f"/api/v1/trips/{trip_id}/flights",
        headers=editor_headers,
        json=flight_payload,
    )
    assert created_flight.status_code == 201

    activity_url = f"/api/v1/trips/{trip_id}/activity"
    for token in (editor, viewer):
        history = client.get(
            activity_url,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert history.status_code == 200
        assert any(
            item["entity_type"] == "flight" and item["action"] == "created"
            for item in history.json()["items"]
        )

    denied = client.post(
        f"/api/v1/trips/{trip_id}/flights",
        headers={"Authorization": f"Bearer {viewer}"},
        json=flight_payload,
    )
    assert denied.status_code == 403


def test_activity_covers_expenses_accommodation_shares_and_invitations(client: TestClient) -> None:
    owner = register_and_login(client, "activity-full-owner@example.com")
    guest = register_and_login(client, "activity-full-guest@example.com")
    headers = {"Authorization": f"Bearer {owner}"}
    trip = client.post(
        "/api/v1/trips",
        headers=headers,
        json={"name": "Viagem com atividade completa", "destination": "Madeira"},
    )
    assert trip.status_code == 201
    trip_id = trip.json()["id"]

    participant = client.post(
        f"/api/v1/trips/{trip_id}/participants",
        headers=headers,
        json={"name": "Ana", "email": "activity-full-guest@example.com"},
    )
    assert participant.status_code == 201
    participant_id = participant.json()["id"]

    expense_url = f"/api/v1/trips/{trip_id}/expenses"
    expense = client.post(
        expense_url,
        headers=headers,
        json={
            "category": "alimentacao",
            "description": "Jantar",
            "expense_date": "2027-08-02",
            "amount": "30.00",
            "currency": "EUR",
            "paid_by_participant_id": participant_id,
        },
    )
    assert expense.status_code == 201
    expense_id = expense.json()["id"]
    expense_item_url = f"{expense_url}/{expense_id}"
    assert client.patch(
        expense_item_url, headers=headers, json={"description": "Jantar atualizado"}
    ).status_code == 200

    shares_url = f"{expense_item_url}/shares"
    assert client.patch(
        shares_url,
        headers=headers,
        json=[{"participant_id": participant_id, "amount": "30.00"}],
    ).status_code == 200
    assert client.patch(shares_url, headers=headers, json=[]).status_code == 200

    accommodation_url = f"/api/v1/trips/{trip_id}/accommodations"
    accommodation = client.post(
        accommodation_url,
        headers=headers,
        json={
            "name": "Hotel de teste",
            "location": "Funchal",
            "check_in": "2027-08-01",
            "check_out": "2027-08-05",
            "price_amount": "300.00",
            "price_currency": "EUR",
        },
    )
    assert accommodation.status_code == 201
    accommodation_id = accommodation.json()["id"]
    accommodation_item_url = f"{accommodation_url}/{accommodation_id}"
    assert client.patch(
        accommodation_item_url, headers=headers, json={"name": "Hotel atualizado"}
    ).status_code == 200
    assert client.delete(accommodation_item_url, headers=headers).status_code == 204

    accepted_invitation = client.post(
        f"/api/v1/trips/{trip_id}/invitations",
        headers=headers,
        json={"email": "activity-full-guest@example.com", "role": "viewer"},
    )
    assert accepted_invitation.status_code == 201
    accepted = client.post(
        "/api/v1/invitations/accept",
        headers={"Authorization": f"Bearer {guest}"},
        json={"token": accepted_invitation.json()["invitation_token"]},
    )
    assert accepted.status_code == 200

    revoked_invitation = client.post(
        f"/api/v1/trips/{trip_id}/invitations",
        headers=headers,
        json={"email": "activity-full-revoked@example.com"},
    )
    assert revoked_invitation.status_code == 201
    revoked_id = revoked_invitation.json()["id"]
    assert client.delete(
        f"/api/v1/trips/{trip_id}/invitations/{revoked_id}", headers=headers
    ).status_code == 204

    assert client.delete(expense_item_url, headers=headers).status_code == 204

    history = client.get(
        f"/api/v1/trips/{trip_id}/activity?limit=100",
        headers=headers,
    )
    assert history.status_code == 200
    events = history.json()["items"]
    event_keys = {(item["entity_type"], item["action"]) for item in events}

    for expected in (
        ("expense", "created"),
        ("expense", "updated"),
        ("expense", "deleted"),
        ("expense_share", "updated"),
        ("accommodation", "created"),
        ("accommodation", "updated"),
        ("accommodation", "deleted"),
        ("invitation", "created"),
        ("invitation", "accepted"),
        ("invitation", "revoked"),
    ):
        assert expected in event_keys, f"Falta o evento {expected}"

    assert all(
        "activity-full-guest@example.com" not in item["summary"]
        and "activity-full-revoked@example.com" not in item["summary"]
        for item in events
    )

