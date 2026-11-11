import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.deps import get_db
from app.database.base import Base
from app.main import app
from app.models import ExpenseShare, TripSettlement  # noqa: F401

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


def test_settlements_reduce_outstanding_balances_and_reject_overpayment(client: TestClient) -> None:
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

    other_trip = client.post(
        "/api/v1/trips",
        headers=headers,
        json={"name": "Outra viagem", "destination": "Braga"},
    )
    assert other_trip.status_code == 201
    outsider_response = client.post(
        f"/api/v1/trips/{other_trip.json()['id']}/participants",
        headers=headers,
        json={"name": "Participante externo"},
    )
    assert outsider_response.status_code == 201
    outsider = outsider_response.json()["id"]

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
    outsider_payment = client.post(
        settlements_url,
        headers=headers,
        json={
            "from_participant_id": outsider,
            "to_participant_id": ana,
            "amount": "1.00",
            "currency": "EUR",
        },
    )
    assert outsider_payment.status_code == 422

    self_payment = client.post(
        settlements_url,
        headers=headers,
        json={
            "from_participant_id": rui,
            "to_participant_id": rui,
            "amount": "1.00",
            "currency": "EUR",
        },
    )
    assert self_payment.status_code == 422

    unknown_currency = client.post(
        settlements_url,
        headers=headers,
        json={
            "from_participant_id": rui,
            "to_participant_id": ana,
            "amount": "1.00",
            "currency": "USD",
        },
    )
    assert unknown_currency.status_code == 422

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
            "currency": "eur",
            "notes": "Transferência parcial",
        },
    )
    assert recorded.status_code == 201
    assert recorded.json()["currency"] == "EUR"

    overpayment_after_partial = client.post(
        settlements_url,
        headers=headers,
        json={
            "from_participant_id": rui,
            "to_participant_id": ana,
            "amount": "12.51",
            "currency": "EUR",
        },
    )
    assert overpayment_after_partial.status_code == 422

    balances = client.get(f"/api/v1/trips/{trip_id}/balances", headers=headers)
    assert balances.status_code == 200
    eur = balances.json()["currencies"][0]
    positions = {item["participant_id"]: item for item in eur["participants"]}
    assert positions[rui]["settled_sent"] == "7.50"
    assert positions[ana]["settled_received"] == "7.50"
    assert positions[rui]["net"] == "-12.50"
    assert positions[ana]["net"] == "12.50"
    assert eur["suggested_transfers"][0]["amount"] == "12.50"

    listed = client.get(settlements_url, headers=headers)
    assert listed.status_code == 200
    assert len(listed.json()) == 1
    assert listed.json()[0]["amount"] == "7.50"

    history = client.get(f"/api/v1/trips/{trip_id}/activity", headers=headers)
    assert history.status_code == 200
    assert any(item["entity_type"] == "settlement" for item in history.json()["items"])

    db = next(app.dependency_overrides[get_db]())
    try:
        db.query(ExpenseShare).filter(ExpenseShare.participant_id == UUID(rui)).delete()
        db.commit()
    finally:
        db.close()

    protected_participant = client.delete(
        f"/api/v1/trips/{trip_id}/participants/{rui}",
        headers=headers,
    )
    assert protected_participant.status_code == 409
    assert "acertos financeiros" in protected_participant.json()["detail"]
