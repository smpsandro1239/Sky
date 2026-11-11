import pytest
from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.deps import get_db
from app.database.base import Base
from app.main import app
from app.models import Accommodation, AuthIdentity, Expense, Flight, Trip, TripInvitation, TripParticipant, User  # noqa: F401

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
        json={"email": email, "password": PASSWORD, "display_name": "Invitation Tester"},
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
        json={"name": "Viagem com amigos", "destination": "Porto Santo"},
    )
    assert response.status_code == 201
    return response.json()["id"]


def create_invitation(client: TestClient, owner_token: str, trip_id: str, email: str) -> dict:
    response = client.post(
        f"/api/v1/trips/{trip_id}/invitations",
        headers=auth(owner_token),
        json={"email": email},
    )
    assert response.status_code == 201
    return response.json()


def test_invitation_acceptance_links_existing_participant_to_account(client: TestClient) -> None:
    owner = register_and_login(client, "owner-invitation@example.com")
    guest = register_and_login(client, "guest-invitation@example.com")
    trip_id = create_trip(client, owner)
    participant_response = client.post(
        f"/api/v1/trips/{trip_id}/participants",
        headers=auth(owner),
        json={"name": "Convidado", "email": "GUEST-INVITATION@example.com"},
    )
    assert participant_response.status_code == 201
    participant_id = participant_response.json()["id"]

    invitation = create_invitation(
        client, owner, trip_id, "guest-invitation@example.com"
    )
    assert invitation["status"] == "pending"
    assert invitation["email_sent"] is False
    assert len(invitation["invitation_token"]) >= 32

    listed = client.get(
        f"/api/v1/trips/{trip_id}/invitations", headers=auth(owner)
    )
    assert listed.status_code == 200
    assert "invitation_token" not in listed.json()[0]
    assert invitation["invitation_token"] not in listed.text

    accepted = client.post(
        "/api/v1/invitations/accept",
        headers=auth(guest),
        json={"token": invitation["invitation_token"]},
    )
    assert accepted.status_code == 200
    assert accepted.json()["status"] == "accepted"

    participant = client.get(
        f"/api/v1/trips/{trip_id}/participants", headers=auth(owner)
    ).json()[0]
    assert participant["id"] == participant_id

    # Reusing a one-time token must not create another membership.
    reused = client.post(
        "/api/v1/invitations/accept",
        headers=auth(guest),
        json={"token": invitation["invitation_token"]},
    )
    assert reused.status_code == 409


def test_invitation_requires_matching_account_email(client: TestClient) -> None:
    owner = register_and_login(client, "owner-email-check@example.com")
    wrong_user = register_and_login(client, "wrong-email@example.com")
    trip_id = create_trip(client, owner)
    invitation = create_invitation(
        client, owner, trip_id, "intended-person@example.com"
    )

    response = client.post(
        "/api/v1/invitations/accept",
        headers=auth(wrong_user),
        json={"token": invitation["invitation_token"]},
    )
    assert response.status_code == 403


def test_invitation_rejects_duplicate_pending_and_can_be_revoked(client: TestClient) -> None:
    owner = register_and_login(client, "owner-revoke@example.com")
    trip_id = create_trip(client, owner)
    invitation = create_invitation(client, owner, trip_id, "friend-revoke@example.com")
    duplicate = client.post(
        f"/api/v1/trips/{trip_id}/invitations",
        headers=auth(owner),
        json={"email": "FRIEND-REVOKE@example.com"},
    )
    assert duplicate.status_code == 409

    revoked = client.delete(
        f"/api/v1/trips/{trip_id}/invitations/{invitation['id']}",
        headers=auth(owner),
    )
    assert revoked.status_code == 204
    assert client.get(
        f"/api/v1/trips/{trip_id}/invitations", headers=auth(owner)
    ).json()[0]["status"] == "revoked"


def test_invitation_token_is_stored_as_hash_and_expiration_is_enforced(client: TestClient) -> None:
    owner = register_and_login(client, "owner-expiry@example.com")
    guest = register_and_login(client, "guest-expiry@example.com")
    trip_id = create_trip(client, owner)
    invitation = create_invitation(client, owner, trip_id, "guest-expiry@example.com")

    from app.api.deps import get_db
    # The raw bearer token is never persisted in the invitation record.
    db_generator = app.dependency_overrides[get_db]()
    db = next(db_generator)
    record = db.scalar(select(TripInvitation).where(TripInvitation.id == UUID(invitation["id"])))
    assert record is not None
    assert record.token_hash != invitation["invitation_token"]
    record.expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
    db.commit()
    db.close()
    db_generator.close()

    response = client.post(
        "/api/v1/invitations/accept",
        headers=auth(guest),
        json={"token": invitation["invitation_token"]},
    )
    assert response.status_code == 410


def test_member_roles_control_trip_visibility_and_writes(client: TestClient) -> None:
    owner = register_and_login(client, "owner-roles@example.com")
    editor = register_and_login(client, "editor-roles@example.com")
    viewer = register_and_login(client, "viewer-roles@example.com")
    trip_id = create_trip(client, owner)

    editor_invite = client.post(
        f"/api/v1/trips/{trip_id}/invitations",
        headers=auth(owner),
        json={"email": "editor-roles@example.com", "role": "editor"},
    )
    viewer_invite = client.post(
        f"/api/v1/trips/{trip_id}/invitations",
        headers=auth(owner),
        json={"email": "viewer-roles@example.com", "role": "viewer"},
    )
    assert editor_invite.status_code == 201
    assert viewer_invite.status_code == 201

    for token, invitation in [
        (editor, editor_invite.json()),
        (viewer, viewer_invite.json()),
    ]:
        accepted = client.post(
            "/api/v1/invitations/accept",
            headers=auth(token),
            json={"token": invitation["invitation_token"]},
        )
        assert accepted.status_code == 200

    for token, expected_role in [(owner, "owner"), (editor, "editor"), (viewer, "viewer")]:
        access = client.get(f"/api/v1/trips/{trip_id}/access", headers=auth(token))
        assert access.status_code == 200
        assert access.json()["role"] == expected_role
        listed = client.get("/api/v1/trips", headers=auth(token))
        assert any(item["id"] == trip_id for item in listed.json())
        trip = client.get(f"/api/v1/trips/{trip_id}", headers=auth(token))
        assert trip.status_code == 200
        assert trip.json()["role"] == expected_role

    flight_payload = {
        "origin": "OPO",
        "destination": "FNC",
        "departure_at": "2027-08-01T08:00:00Z",
        "arrival_at": "2027-08-01T10:00:00Z",
        "price_amount": "100.00",
        "price_currency": "EUR",
    }
    flights_url = f"/api/v1/trips/{trip_id}/flights"
    assert client.get(flights_url, headers=auth(viewer)).status_code == 200
    assert client.post(flights_url, headers=auth(viewer), json=flight_payload).status_code == 403
    assert client.post(flights_url, headers=auth(editor), json=flight_payload).status_code == 201

    # Editors can manage trip content but cannot administer membership.
    assert client.post(
        f"/api/v1/trips/{trip_id}/participants",
        headers=auth(editor),
        json={"name": "Outro participante"},
    ).status_code == 404
    # A viewer cannot alter trip metadata or delete the trip.
    assert client.patch(
        f"/api/v1/trips/{trip_id}",
        headers=auth(viewer),
        json={"name": "Alteração não autorizada"},
    ).status_code == 404
    assert client.delete(f"/api/v1/trips/{trip_id}", headers=auth(editor)).status_code == 404


def test_editor_and_viewer_permissions_cover_financial_and_accommodation_resources(client: TestClient) -> None:
    owner = register_and_login(client, "owner-resource-roles@example.com")
    editor = register_and_login(client, "editor-resource-roles@example.com")
    viewer = register_and_login(client, "viewer-resource-roles@example.com")
    trip_id = create_trip(client, owner)

    participant = client.post(
        f"/api/v1/trips/{trip_id}/participants",
        headers=auth(owner),
        json={"name": "Ana", "email": "ana-resource-roles@example.com"},
    )
    assert participant.status_code == 201
    participant_id = participant.json()["id"]

    editor_invite = client.post(
        f"/api/v1/trips/{trip_id}/invitations",
        headers=auth(owner),
        json={"email": "editor-resource-roles@example.com", "role": "editor"},
    ).json()
    viewer_invite = client.post(
        f"/api/v1/trips/{trip_id}/invitations",
        headers=auth(owner),
        json={"email": "viewer-resource-roles@example.com", "role": "viewer"},
    ).json()
    for token, invitation in [(editor, editor_invite), (viewer, viewer_invite)]:
        accepted = client.post(
            "/api/v1/invitations/accept",
            headers=auth(token),
            json={"token": invitation["invitation_token"]},
        )
        assert accepted.status_code == 200

    expense_url = f"/api/v1/trips/{trip_id}/expenses"
    expense_payload = {
        "category": "alimentacao",
        "description": "Jantar partilhado",
        "expense_date": "2027-08-02",
        "amount": "24.00",
        "currency": "EUR",
        "paid_by_participant_id": participant_id,
    }
    created_expense = client.post(expense_url, headers=auth(editor), json=expense_payload)
    assert created_expense.status_code == 201
    expense_id = created_expense.json()["id"]

    accommodation_url = f"/api/v1/trips/{trip_id}/accommodations"
    accommodation_payload = {
        "name": "Hotel de teste",
        "location": "Funchal",
        "check_in": "2027-08-01",
        "check_out": "2027-08-05",
        "price_amount": "300.00",
        "price_currency": "EUR",
    }
    created_accommodation = client.post(
        accommodation_url, headers=auth(editor), json=accommodation_payload
    )
    assert created_accommodation.status_code == 201

    shares_url = f"{expense_url}/{expense_id}/shares"
    saved_shares = client.patch(
        shares_url,
        headers=auth(editor),
        json=[{"participant_id": participant_id, "amount": "24.00"}],
    )
    assert saved_shares.status_code == 200

    # Both shared roles can read trip resources, including financial data.
    for token in (editor, viewer):
        assert client.get(expense_url, headers=auth(token)).status_code == 200
        assert client.get(accommodation_url, headers=auth(token)).status_code == 200
        assert client.get(shares_url, headers=auth(token)).status_code == 200
        assert client.get(f"/api/v1/trips/{trip_id}/balances", headers=auth(token)).status_code == 200
        assert client.get(f"/api/v1/trips/{trip_id}/participants", headers=auth(token)).status_code == 200

    # Viewers cannot create or alter expenses, accommodation, or shares.
    assert client.post(expense_url, headers=auth(viewer), json=expense_payload).status_code == 403
    assert client.patch(
        shares_url, headers=auth(viewer),
        json=[{"participant_id": participant_id, "amount": "24.00"}],
    ).status_code == 403
    accommodation_id = created_accommodation.json()["id"]
    assert client.patch(
        f"{accommodation_url}/{accommodation_id}",
        headers=auth(viewer),
        json={"name": "Alteração não autorizada"},
    ).status_code == 403
    assert client.delete(
        f"{accommodation_url}/{accommodation_id}", headers=auth(viewer)
    ).status_code == 403

    # Editors cannot manage invitations or membership.
    assert client.get(
        f"/api/v1/trips/{trip_id}/invitations", headers=auth(editor)
    ).status_code == 404
    assert client.post(
        f"/api/v1/trips/{trip_id}/invitations",
        headers=auth(editor),
        json={"email": "another@example.com"},
    ).status_code == 404


def test_owner_can_change_member_role_and_pending_invitation_role(client: TestClient) -> None:
    owner = register_and_login(client, "owner-change-role@example.com")
    guest = register_and_login(client, "guest-change-role@example.com")
    trip_id = create_trip(client, owner)
    participant = client.post(
        f"/api/v1/trips/{trip_id}/participants",
        headers=auth(owner),
        json={"name": "Convidado", "email": "guest-change-role@example.com"},
    )
    assert participant.status_code == 201
    participant_id = participant.json()["id"]
    assert participant.json()["is_linked"] is False

    invitation = client.post(
        f"/api/v1/trips/{trip_id}/invitations",
        headers=auth(owner),
        json={"email": "guest-change-role@example.com", "role": "viewer"},
    )
    assert invitation.status_code == 201

    changed = client.patch(
        f"/api/v1/trips/{trip_id}/participants/{participant_id}",
        headers=auth(owner),
        json={"role": "editor"},
    )
    assert changed.status_code == 200
    assert changed.json()["role"] == "editor"

    pending = client.get(
        f"/api/v1/trips/{trip_id}/invitations", headers=auth(owner)
    ).json()[0]
    assert pending["role"] == "editor"

    accepted = client.post(
        "/api/v1/invitations/accept",
        headers=auth(guest),
        json={"token": invitation.json()["invitation_token"]},
    )
    assert accepted.status_code == 200
    access = client.get(f"/api/v1/trips/{trip_id}/access", headers=auth(guest))
    assert access.status_code == 200
    assert access.json()["role"] == "editor"
    linked_participant = client.get(
        f"/api/v1/trips/{trip_id}/participants", headers=auth(owner)
    ).json()[0]
    assert linked_participant["is_linked"] is True

    # A member cannot change another member's permission.
    denied = client.patch(
        f"/api/v1/trips/{trip_id}/participants/{participant_id}",
        headers=auth(guest),
        json={"role": "viewer"},
    )
    assert denied.status_code == 404


def test_participant_email_cannot_be_duplicated_with_different_case(client: TestClient) -> None:
    owner = register_and_login(client, "owner-duplicate-member@example.com")
    trip_id = create_trip(client, owner)
    first = client.post(
        f"/api/v1/trips/{trip_id}/participants",
        headers=auth(owner),
        json={"name": "Primeira pessoa", "email": "Person@Example.com"},
    )
    assert first.status_code == 201
    duplicate = client.post(
        f"/api/v1/trips/{trip_id}/participants",
        headers=auth(owner),
        json={"name": "Pessoa duplicada", "email": "person@example.com"},
    )
    assert duplicate.status_code == 409


def test_create_invitation_sends_email_and_reports_delivery(client: TestClient, monkeypatch) -> None:
    owner = register_and_login(client, "owner-email-send@example.com")
    trip_id = create_trip(client, owner)
    captured: dict[str, str] = {}

    def fake_send(**kwargs) -> bool:
        captured.update(kwargs)
        return True

    monkeypatch.setattr(
        "app.api.routes.invitations.send_trip_invitation_email",
        fake_send,
    )
    response = client.post(
        f"/api/v1/trips/{trip_id}/invitations",
        headers=auth(owner),
        json={"email": "guest-email-send@example.com", "role": "editor"},
    )

    assert response.status_code == 201
    assert response.json()["email_sent"] is True
    assert captured["to_email"] == "guest-email-send@example.com"
    assert captured["role"] == "editor"
    assert response.json()["invitation_token"] in captured["accept_url"]
