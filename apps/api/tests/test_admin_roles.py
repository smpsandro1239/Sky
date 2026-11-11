from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.deps import get_db
from app.database.base import Base
from app.main import app
from app.models import AuthSession, User  # noqa: F401
from app.core.security import hash_password

TEST_DATABASE_URL = "sqlite+pysqlite:///:memory:"


def test_platform_role_permissions_and_admin_management() -> None:
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
    try:
        with testing_session() as db:
            admin = User(
                email="admin@sky.example",
                display_name="SKY Admin",
                password_hash=hash_password("Correct-Horse-Battery-2026!"),
                role="admin",
            )
            traveler = User(
                email="traveler@sky.example",
                display_name="SKY Traveller",
                password_hash=hash_password("Correct-Horse-Battery-2026!"),
                role="traveler",
            )
            support = User(
                email="support@sky.example",
                display_name="SKY Support",
                password_hash=hash_password("Correct-Horse-Battery-2026!"),
                role="support",
            )
            db.add_all([admin, traveler, support])
            db.commit()
            admin_id = str(admin.id)
            traveler_id = str(traveler.id)

        with TestClient(app) as client:
            traveler_login = client.post(
                "/api/v1/auth/login",
                json={"email": "traveler@sky.example", "password": "Correct-Horse-Battery-2026!"},
            )
            admin_login = client.post(
                "/api/v1/auth/login",
                json={"email": "admin@sky.example", "password": "Correct-Horse-Battery-2026!"},
            )
            support_login = client.post(
                "/api/v1/auth/login",
                json={"email": "support@sky.example", "password": "Correct-Horse-Battery-2026!"},
            )
            assert traveler_login.status_code == 200
            assert admin_login.status_code == 200
            assert support_login.status_code == 200
            traveler_headers = {"Authorization": f"Bearer {traveler_login.json()['access_token']}"}
            admin_headers = {"Authorization": f"Bearer {admin_login.json()['access_token']}"}
            support_headers = {"Authorization": f"Bearer {support_login.json()['access_token']}"}

            profile = client.get("/api/v1/auth/me", headers=traveler_headers)
            assert profile.status_code == 200
            assert profile.json()["role"] == "traveler"

            denied = client.get("/api/v1/admin/users", headers=traveler_headers)
            assert denied.status_code == 403

            support_listed = client.get("/api/v1/admin/users", headers=support_headers)
            assert support_listed.status_code == 200
            assert len(support_listed.json()) == 3
            assert all("password_hash" not in item for item in support_listed.json())

            first_page = client.get("/api/v1/admin/users?limit=1&offset=0", headers=admin_headers)
            second_page = client.get("/api/v1/admin/users?limit=1&offset=1", headers=admin_headers)
            assert first_page.status_code == 200
            assert second_page.status_code == 200
            assert len(first_page.json()) == 1
            assert len(second_page.json()) == 1
            assert first_page.json()[0]["id"] != second_page.json()[0]["id"]

            support_change_denied = client.patch(
                f"/api/v1/admin/users/{traveler_id}/role",
                json={"role": "admin"},
                headers=support_headers,
            )
            assert support_change_denied.status_code == 403

            listed = client.get("/api/v1/admin/users", headers=admin_headers)
            assert listed.status_code == 200
            assert {item["email"] for item in listed.json()} == {
                "admin@sky.example",
                "traveler@sky.example",
                "support@sky.example",
            }
            assert all("password_hash" not in item for item in listed.json())

            changed = client.patch(
                f"/api/v1/admin/users/{traveler_id}/role",
                json={"role": "support"},
                headers=admin_headers,
            )
            assert changed.status_code == 200
            assert changed.json()["role"] == "support"

            self_demotion = client.patch(
                f"/api/v1/admin/users/{admin_id}/role",
                json={"role": "traveler"},
                headers=admin_headers,
            )
            assert self_demotion.status_code == 409
    finally:
        app.dependency_overrides.clear()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()
