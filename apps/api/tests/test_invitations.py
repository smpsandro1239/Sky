from datetime import datetime, timedelta, timezone

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
    record = db.scalar(select(TripInvitation).where(TripInvitation.id == invitation["id"]))
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
