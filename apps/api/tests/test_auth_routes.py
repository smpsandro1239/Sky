import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.deps import get_db
from app.database.base import Base
from app.main import app
from app.models import Accommodation, AuthIdentity, AuthSession, Flight, Trip, User  # noqa: F401

TEST_DATABASE_URL = "sqlite+pysqlite:///:memory:"


@pytest.fixture()
def client() -> TestClient:
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        with TestingSessionLocal() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


def test_register_login_and_get_current_user(client: TestClient) -> None:
    registration = client.post(
        "/api/v1/auth/register",
        json={
            "email": "Sky.User@example.com",
            "password": "Correct-Horse-Battery-2026!",
            "display_name": "Sky User",
        },
    )

    assert registration.status_code == 201
    user = registration.json()
    assert user["email"] == "sky.user@example.com"
    assert user["display_name"] == "Sky User"
    assert user["is_active"] is True
    assert user["is_verified"] is False
    assert "password" not in user
    assert "password_hash" not in user

    login = client.post(
        "/api/v1/auth/login",
        json={
            "email": "sky.user@example.com",
            "password": "Correct-Horse-Battery-2026!",
        },
    )

    assert login.status_code == 200
    token_data = login.json()
    assert token_data["token_type"] == "bearer"
    assert token_data["expires_in"] > 0
    assert token_data["access_token"]

    profile = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token_data['access_token']}"},
    )
    assert profile.status_code == 200
    assert profile.json()["id"] == user["id"]
    assert profile.json()["email"] == user["email"]


def test_logout_revokes_only_the_current_session(client: TestClient) -> None:
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "sessions@example.com",
            "password": "Correct-Horse-Battery-2026!",
            "display_name": "Session User",
        },
    )
    credentials = {"email": "sessions@example.com", "password": "Correct-Horse-Battery-2026!"}
    first_token = client.post("/api/v1/auth/login", json=credentials).json()["access_token"]
    second_token = client.post("/api/v1/auth/login", json=credentials).json()["access_token"]

    first_headers = {"Authorization": f"Bearer {first_token}"}
    second_headers = {"Authorization": f"Bearer {second_token}"}

    logout = client.post("/api/v1/auth/logout", headers=first_headers)
    assert logout.status_code == 204
    assert client.get("/api/v1/auth/me", headers=first_headers).status_code == 401
    assert client.get("/api/v1/auth/me", headers=second_headers).status_code == 200


def test_register_rejects_duplicate_email(client: TestClient) -> None:
    payload = {
        "email": "duplicate@example.com",
        "password": "Correct-Horse-Battery-2026!",
        "display_name": "Duplicate",
    }

    first = client.post("/api/v1/auth/register", json=payload)
    second = client.post("/api/v1/auth/register", json=payload)

    assert first.status_code == 201
    assert second.status_code == 409


def test_login_rejects_invalid_password(client: TestClient) -> None:
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "login@example.com",
            "password": "Correct-Horse-Battery-2026!",
            "display_name": "Login User",
        },
    )

    response = client.post(
        "/api/v1/auth/login",
        json={"email": "login@example.com", "password": "incorrect-password"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Email ou palavra-passe inválidos."


@pytest.mark.parametrize(
    "authorization",
    [None, "Bearer invalid-token"],
)
def test_profile_requires_valid_access_token(
    client: TestClient,
    authorization: str | None,
) -> None:
    headers = {}
    if authorization is not None:
        headers["Authorization"] = authorization

    response = client.get("/api/v1/auth/me", headers=headers)

    assert response.status_code == 401


def test_register_normalizes_display_name(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "name@example.com",
            "password": "Correct-Horse-Battery-2026!",
            "display_name": "  Sky Traveller  ",
        },
    )

    assert response.status_code == 201
    assert response.json()["display_name"] == "Sky Traveller"


def test_register_rejects_blank_display_name(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "blank-name@example.com",
            "password": "Correct-Horse-Battery-2026!",
            "display_name": "   ",
        },
    )

    assert response.status_code == 422
