import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.deps import get_db
from app.database.base import Base
from app.main import app
from app.models import Accommodation, AuthIdentity, Flight, Trip, User  # noqa: F401

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
        json={"email": email, "password": PASSWORD, "display_name": "Trip Tester"},
    )
    assert registration.status_code == 201
    login = client.post("/api/v1/auth/login", json={"email": email, "password": PASSWORD})
    assert login.status_code == 200
    return login.json()["access_token"]


def auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_user_can_create_list_read_update_and_delete_trip(client: TestClient) -> None:
    token = register_and_login(client, "owner@example.com")
    headers = auth(token)
    created = client.post(
        "/api/v1/trips",
        headers=headers,
        json={
            "name": "Férias de verão",
            "destination": "Madeira",
            "start_date": "2027-08-01",
            "end_date": "2027-08-10",
            "notes": "Viagem em família",
        },
    )
    assert created.status_code == 201
    trip = created.json()
    assert trip["name"] == "Férias de verão"
    assert trip["destination"] == "Madeira"
    trip_id = trip["id"]

    listed = client.get("/api/v1/trips", headers=headers)
    assert listed.status_code == 200
    assert [item["id"] for item in listed.json()] == [trip_id]

    fetched = client.get(f"/api/v1/trips/{trip_id}", headers=headers)
    assert fetched.status_code == 200
    assert fetched.json()["notes"] == "Viagem em família"

    updated = client.patch(
        f"/api/v1/trips/{trip_id}",
        headers=headers,
        json={"destination": "Porto Santo"},
    )
    assert updated.status_code == 200
    assert updated.json()["destination"] == "Porto Santo"

    deleted = client.delete(f"/api/v1/trips/{trip_id}", headers=headers)
    assert deleted.status_code == 204
    assert client.get(f"/api/v1/trips/{trip_id}", headers=headers).status_code == 404


def test_user_cannot_read_or_modify_another_users_trip(client: TestClient) -> None:
    owner_token = register_and_login(client, "trip-owner@example.com")
    other_token = register_and_login(client, "other-user@example.com")
    created = client.post(
        "/api/v1/trips",
        headers=auth(owner_token),
        json={"name": "Viagem privada", "destination": "Lisboa"},
    )
    assert created.status_code == 201
    trip_id = created.json()["id"]

    assert client.get(f"/api/v1/trips/{trip_id}", headers=auth(other_token)).status_code == 404
    assert client.patch(
        f"/api/v1/trips/{trip_id}",
        headers=auth(other_token),
        json={"name": "Acesso indevido"},
    ).status_code == 404
    assert client.delete(
        f"/api/v1/trips/{trip_id}", headers=auth(other_token)
    ).status_code == 404


def test_trip_rejects_invalid_date_range(client: TestClient) -> None:
    token = register_and_login(client, "dates@example.com")
    response = client.post(
        "/api/v1/trips",
        headers=auth(token),
        json={
            "name": "Datas inválidas",
            "destination": "Braga",
            "start_date": "2027-08-10",
            "end_date": "2027-08-01",
        },
    )
    assert response.status_code == 422


def test_trip_end_date_cannot_be_moved_before_start_date(client: TestClient) -> None:
    token = register_and_login(client, "patch-dates@example.com")
    created = client.post(
        "/api/v1/trips",
        headers=auth(token),
        json={
            "name": "Datas",
            "destination": "Braga",
            "start_date": "2027-08-10",
            "end_date": "2027-08-20",
        },
    )
    trip_id = created.json()["id"]
    response = client.patch(
        f"/api/v1/trips/{trip_id}",
        headers=auth(token),
        json={"end_date": "2027-08-05"},
    )
    assert response.status_code == 422


def test_trip_endpoints_require_authentication(client: TestClient) -> None:
    assert client.get("/api/v1/trips").status_code == 401
    assert client.post(
        "/api/v1/trips", json={"name": "Sem token", "destination": "Porto"}
    ).status_code == 401


def test_trip_rejects_blank_required_fields_and_null_updates(client: TestClient) -> None:
    token = register_and_login(client, "trip-validation@example.com")
    headers = auth(token)

    blank = client.post(
        "/api/v1/trips",
        headers=headers,
        json={"name": "   ", "destination": "Lisboa"},
    )
    assert blank.status_code == 422

    created = client.post(
        "/api/v1/trips",
        headers=headers,
        json={"name": "Viagem", "destination": "Lisboa"},
    )
    assert created.status_code == 201
    trip_id = created.json()["id"]

    null_name = client.patch(
        f"/api/v1/trips/{trip_id}", headers=headers, json={"name": None}
    )
    assert null_name.status_code == 422


def test_trip_budget_can_be_created_updated_and_cleared(client: TestClient) -> None:
    token = register_and_login(client, "budget@example.com")
    headers = auth(token)
    created = client.post(
        "/api/v1/trips",
        headers=headers,
        json={
            "name": "Orçamento",
            "destination": "Paris",
            "budget_amount": "1250.50",
            "budget_currency": "eur",
        },
    )
    assert created.status_code == 201
    trip = created.json()
    assert trip["budget_amount"] == "1250.50"
    assert trip["budget_currency"] == "EUR"

    trip_id = trip["id"]
    updated = client.patch(
        f"/api/v1/trips/{trip_id}",
        headers=headers,
        json={"budget_amount": "1500.00", "budget_currency": "GBP"},
    )
    assert updated.status_code == 200
    assert updated.json()["budget_amount"] == "1500.00"
    assert updated.json()["budget_currency"] == "GBP"

    cleared = client.patch(
        f"/api/v1/trips/{trip_id}",
        headers=headers,
        json={"budget_amount": None},
    )
    assert cleared.status_code == 200
    assert cleared.json()["budget_amount"] is None


def test_trip_budget_rejects_negative_amount_and_invalid_currency(client: TestClient) -> None:
    token = register_and_login(client, "invalid-budget@example.com")
    headers = auth(token)

    negative = client.post(
        "/api/v1/trips",
        headers=headers,
        json={"name": "Orçamento", "destination": "Roma", "budget_amount": "-1"},
    )
    assert negative.status_code == 422

    invalid_currency = client.post(
        "/api/v1/trips",
        headers=headers,
        json={
            "name": "Orçamento",
            "destination": "Roma",
            "budget_amount": "100",
            "budget_currency": "EURO",
        },
    )
    assert invalid_currency.status_code == 422


def test_trip_expenses_crud_and_user_isolation(client: TestClient) -> None:
    owner_token = register_and_login(client, "expense-owner@example.com")
    other_token = register_and_login(client, "expense-other@example.com")
    headers = auth(owner_token)
    trip_response = client.post(
        "/api/v1/trips",
        headers=headers,
        json={"name": "Férias", "destination": "Porto"},
    )
    trip_id = trip_response.json()["id"]
    expense_response = client.post(
        f"/api/v1/trips/{trip_id}/expenses",
        headers=headers,
        json={
            "category": "alimentacao",
            "description": "Jantar",
            "expense_date": "2027-08-02",
            "amount": "42.50",
            "currency": "eur",
            "notes": "Restaurante local",
        },
    )
    assert expense_response.status_code == 201
    expense = expense_response.json()
    assert expense["category"] == "alimentacao"
    assert expense["amount"] == "42.50"
    assert expense["currency"] == "EUR"

    listed = client.get(f"/api/v1/trips/{trip_id}/expenses", headers=headers)
    assert listed.status_code == 200
    assert len(listed.json()) == 1

    expense_id = expense["id"]
    updated = client.patch(
        f"/api/v1/trips/{trip_id}/expenses/{expense_id}",
        headers=headers,
        json={"amount": "50.00", "description": "Jantar atualizado"},
    )
    assert updated.status_code == 200
    assert updated.json()["amount"] == "50.00"
    assert updated.json()["description"] == "Jantar atualizado"

    assert client.get(
        f"/api/v1/trips/{trip_id}/expenses", headers=auth(other_token)
    ).status_code == 404
    deleted = client.delete(
        f"/api/v1/trips/{trip_id}/expenses/{expense_id}", headers=headers
    )
    assert deleted.status_code == 204
    assert client.get(
        f"/api/v1/trips/{trip_id}/expenses", headers=headers
    ).json() == []


def test_expenses_reject_invalid_category_and_non_positive_amount(client: TestClient) -> None:
    token = register_and_login(client, "expense-validation@example.com")
    headers = auth(token)
    trip = client.post(
        "/api/v1/trips", headers=headers,
        json={"name": "Teste", "destination": "Braga"},
    ).json()
    url = f"/api/v1/trips/{trip['id']}/expenses"
    base = {"description": "Despesa", "expense_date": "2027-08-02", "amount": "10"}
    invalid_category = client.post(url, headers=headers, json={**base, "category": "categoria-x"})
    assert invalid_category.status_code == 422
    invalid_amount = client.post(url, headers=headers, json={**base, "category": "outros", "amount": "0"})
    assert invalid_amount.status_code == 422
