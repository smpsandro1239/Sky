import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.deps import get_db
from app.database.base import Base
from app.main import app
from app.models import AuthIdentity, Trip, TripBudgetPlan, User  # noqa: F401

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
        json={"email": email, "password": PASSWORD, "display_name": "Plan Tester"},
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


def test_monthly_budget_plan_upserts_lists_and_deletes(client: TestClient) -> None:
    token = register_and_login(client, "budget-plan@example.com")
    trip_id = create_trip(client, token)
    url = f"/api/v1/trips/{trip_id}/budget-plans"
    headers = auth(token)
    payload = {"month": "2027-08", "category": "alimentacao", "amount": "250.00", "currency": "eur"}

    created = client.put(url, headers=headers, json=payload)
    assert created.status_code == 200
    assert created.json()["amount"] == "250.00"
    assert created.json()["currency"] == "EUR"
    assert created.json()["month"] == "2027-08"

    updated = client.put(url, headers=headers, json={**payload, "amount": "300.50"})
    assert updated.status_code == 200
    assert updated.json()["id"] == created.json()["id"]
    assert updated.json()["amount"] == "300.50"

    listed = client.get(url, headers=headers)
    assert listed.status_code == 200
    assert len(listed.json()) == 1

    deleted = client.delete(f"{url}/2027-08/alimentacao/EUR", headers=headers)
    assert deleted.status_code == 204
    assert client.get(url, headers=headers).json() == []


def test_monthly_budget_plan_validates_month_category_amount_and_currency(client: TestClient) -> None:
    token = register_and_login(client, "budget-plan-validation@example.com")
    trip_id = create_trip(client, token)
    url = f"/api/v1/trips/{trip_id}/budget-plans"
    headers = auth(token)

    base = {"month": "2027-08", "category": "alimentacao", "amount": "100", "currency": "EUR"}
    assert client.put(url, headers=headers, json={**base, "month": "2027-13"}).status_code == 422
    assert client.put(url, headers=headers, json={**base, "category": "invalid"}).status_code == 422
    assert client.put(url, headers=headers, json={**base, "amount": "-1"}).status_code == 422
    assert client.put(url, headers=headers, json={**base, "currency": "EURO"}).status_code == 422


def test_monthly_budget_plan_requires_trip_access(client: TestClient) -> None:
    owner = register_and_login(client, "budget-plan-owner@example.com")
    other = register_and_login(client, "budget-plan-other@example.com")
    trip_id = create_trip(client, owner)
    url = f"/api/v1/trips/{trip_id}/budget-plans"
    payload = {"month": "2027-08", "category": "alimentacao", "amount": "100", "currency": "EUR"}

    assert client.get(url, headers=auth(other)).status_code == 404
    assert client.put(url, headers=auth(other), json=payload).status_code == 404
