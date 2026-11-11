from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.deps import get_db
from app.database.base import Base
from app.main import app
from app.models import Expense, ExpenseShare, Trip, TripParticipant, TripSettlement, User  # noqa: F401

PASSWORD = "Correct-Horse-Battery-2026!"


def client_fixture():
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
    return engine, testing_session


def register_and_login(client: TestClient, email: str) -> str:
    registered = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": PASSWORD, "display_name": "Settlement Tester"},
    )
    assert registered.status_code == 201
    logged_in = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": PASSWORD},
    )
    assert logged_in.status_code == 200
    return logged_in.json()["access_token"]


def test_settlements_reduce_outstanding_balances_and_reject_overpayment() -> None:
    engine, _ = client_fixture()
    try:
        with TestClient(app) as client:
            token = register_and_login(client, "settlement-owner@example.com")
            headers = {"Authorization": f"Bearer {token}"}
            trip = client.post(
                "/api/v1/trips",
                headers=headers,
                json={"name": "Viagem com acertos", "destination": "Porto"},
            )
            assert trip.status_code == 201
            trip_id = trip.json()["id"]

            participants = []
            for name in ("Ana", "Rui"):
                response = client.post(
                    f"/api/v1/trips/{trip_id}/participants",
                    headers=headers,
                    json={"name": name},
                )
                assert response.status_code == 201
                participants.append(response.json()["id"])
            ana, rui = participants

            expense = client.post(
                f"/api/v1/trips/{trip_id}/expenses",
                headers=headers,
                json={
                    "category": "alimentacao",
                    "description": "Jantar",
                    "expense_date": "2027-08-02",
                    "amount": "30.00",
                    "currency": "EUR",
                    "paid_by_participant_id": ana,
                },
            )
            assert expense.status_code == 201
            expense_id = expense.json()["id"]
            shares = client.patch(
                f"/api/v1/trips/{trip_id}/expenses/{expense_id}/shares",
                headers=headers,
                json=[
                    {"participant_id": ana, "amount": "10.00"},
                    {"participant_id": rui, "amount": "20.00"},
                ],
            )
            assert shares.status_code == 200

            settlements_url = f"/api/v1/trips/{trip_id}/settlements"
            invalid = client.post(
                settlements_url,
                headers=headers,
                json={
                    "from_participant_id": rui,
                    "to_participant_id": ana,
                    "amount": "21.00",
                    "currency": "EUR",
                },
            )
            assert invalid.status_code == 422

            recorded = client.post(
                settlements_url,
                headers=headers,
                json={
                    "from_participant_id": rui,
                    "to_participant_id": ana,
                    "amount": "7.50",
                    "currency": "EUR",
                    "notes": "Transferência parcial",
                },
            )
            assert recorded.status_code == 201

            balances = client.get(
                f"/api/v1/trips/{trip_id}/balances",
                headers=headers,
            )
            assert balances.status_code == 200
            eur = balances.json()["currencies"][0]
            positions = {item["participant_id"]: item for item in eur["participants"]}
            assert positions[rui]["net"] == "-12.50"
            assert positions[ana]["net"] == "12.50"
            assert eur["suggested_transfers"][0]["amount"] == "12.50"

            listed = client.get(settlements_url, headers=headers)
            assert listed.status_code == 200
            assert len(listed.json()) == 1
            assert listed.json()[0]["amount"] == "7.50"

            history = client.get(
                f"/api/v1/trips/{trip_id}/activity",
                headers=headers,
            )
            assert history.status_code == 200
            assert any(item["entity_type"] == "settlement" for item in history.json()["items"])
    finally:
        app.dependency_overrides.clear()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()
