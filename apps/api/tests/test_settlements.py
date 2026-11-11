import pytest
from decimal import Decimal
from uuid import UUID
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

    expense_currency_change = client.patch(
        f"/api/v1/trips/{trip_id}/expenses/{expense_id}",
        headers=headers,
        json={"currency": "USD"},
    )
    assert expense_currency_change.status_code == 409
    assert "acertos financeiros" in expense_currency_change.json()["detail"]

    expense_description_change = client.patch(
        f"/api/v1/trips/{trip_id}/expenses/{expense_id}",
        headers=headers,
        json={"description": "Jantar actualizado"},
    )
    assert expense_description_change.status_code == 200
    assert expense_description_change.json()["currency"] == "EUR"
    assert expense_description_change.json()["amount"] == "30.00"

    changed_shares = client.patch(
        f"/api/v1/trips/{trip_id}/expenses/{expense_id}/shares",
        headers=headers,
        json=[
            {"participant_id": ana, "amount": "9.00"},
            {"participant_id": rui, "amount": "21.00"},
        ],
    )
    assert changed_shares.status_code == 409
    assert "acertos financeiros" in changed_shares.json()["detail"]

    deleted_settled_expense = client.delete(
        f"/api/v1/trips/{trip_id}/expenses/{expense_id}",
        headers=headers,
    )
    assert deleted_settled_expense.status_code == 409
    assert "acertos financeiros" in deleted_settled_expense.json()["detail"]

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
    assert eur["reconciliation"]["total_expenses"] == "30.00"
    assert eur["reconciliation"]["total_paid"] == "30.00"
    assert eur["reconciliation"]["total_allocated"] == "30.00"
    assert eur["reconciliation"]["expense_difference"] == "0.00"
    assert eur["reconciliation"]["settlement_difference"] == "0.00"
    assert eur["reconciliation"]["net_total"] == "0.00"
    assert eur["reconciliation"]["is_balanced"] is True

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

    unallocated = client.post(
        f"/api/v1/trips/{trip_id}/expenses",
        headers=headers,
        json={
            "category": "outros",
            "description": "Despesa por atribuir",
            "expense_date": "2027-08-03",
            "amount": "5.00",
            "currency": "EUR",
        },
    )
    assert unallocated.status_code == 201
    late_allocation = client.patch(
        f"/api/v1/trips/{trip_id}/expenses/{unallocated.json()['id']}/shares",
        headers=headers,
        json=[{"participant_id": ana, "amount": "5.00"}],
    )
    assert late_allocation.status_code == 409
    assert "acertos financeiros" in late_allocation.json()["detail"]

    audited_balances = client.get(f"/api/v1/trips/{trip_id}/balances", headers=headers)
    assert audited_balances.status_code == 200
    audited_eur = audited_balances.json()["currencies"][0]
    assert audited_eur["reconciliation"]["is_balanced"] is False
    assert audited_eur["reconciliation"]["unallocated_expenses"] == [
        {
            "expense_id": unallocated.json()["id"],
            "description": "Despesa por atribuir",
            "amount": "5.00",
            "reason": "missing_payer",
        }
    ]

    missing_shares = client.post(
        f"/api/v1/trips/{trip_id}/expenses",
        headers=headers,
        json={
            "category": "transportes",
            "description": "Despesa sem divisão",
            "expense_date": "2027-08-04",
            "amount": "6.00",
            "currency": "EUR",
            "paid_by_participant_id": ana,
        },
    )
    assert missing_shares.status_code == 201
    audited_balances = client.get(f"/api/v1/trips/{trip_id}/balances", headers=headers)
    assert audited_balances.status_code == 200
    unallocated_items = audited_balances.json()["currencies"][0]["reconciliation"]["unallocated_expenses"]
    assert {item["reason"] for item in unallocated_items} == {"missing_payer", "missing_shares"}
    assert {item["expense_id"] for item in unallocated_items} == {
        unallocated.json()["id"],
        missing_shares.json()["id"],
    }
    assert audited_balances.json()["currencies"][0]["reconciliation"]["total_expenses"] == "41.00"
    assert audited_balances.json()["currencies"][0]["reconciliation"]["total_paid"] == "36.00"
    assert audited_balances.json()["currencies"][0]["reconciliation"]["total_allocated"] == "10.00"
    assert audited_balances.json()["currencies"][0]["reconciliation"]["expense_difference"] == "26.00"



def test_balances_reconcile_each_currency_independently(client: TestClient) -> None:
    token = register_and_login(client, "multi-currency@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    trip = client.post(
        "/api/v1/trips",
        headers=headers,
        json={"name": "Viagem multi-moeda", "destination": "Europa"},
    )
    assert trip.status_code == 201
    trip_id = trip.json()["id"]

    participant_ids = []
    for name in ("Ana", "Rui"):
        response = client.post(
            f"/api/v1/trips/{trip_id}/participants",
            headers=headers,
            json={"name": name},
        )
        assert response.status_code == 201
        participant_ids.append(response.json()["id"])
    ana, rui = participant_ids

    for description, amount, currency, payer in (
        ("Hotel", "20.00", "EUR", ana),
        ("Comboio", "12.00", "USD", rui),
    ):
        created = client.post(
            f"/api/v1/trips/{trip_id}/expenses",
            headers=headers,
            json={
                "category": "transportes",
                "description": description,
                "expense_date": "2027-08-05",
                "amount": amount,
                "currency": currency,
                "paid_by_participant_id": payer,
            },
        )
        assert created.status_code == 201
        divided = client.patch(
            f"/api/v1/trips/{trip_id}/expenses/{created.json()['id']}/shares",
            headers=headers,
            json=[
                {"participant_id": ana, "amount": str(Decimal(amount) / 2)},
                {"participant_id": rui, "amount": str(Decimal(amount) / 2)},
            ],
        )
        assert divided.status_code == 200

    response = client.get(f"/api/v1/trips/{trip_id}/balances", headers=headers)
    assert response.status_code == 200
    currencies = {item["currency"]: item for item in response.json()["currencies"]}

    assert set(currencies) == {"EUR", "USD"}
    eur = currencies["EUR"]
    usd = currencies["USD"]

    assert eur["reconciliation"]["total_expenses"] == "20.00"
    assert eur["reconciliation"]["total_paid"] == "20.00"
    assert eur["reconciliation"]["total_allocated"] == "20.00"
    assert eur["reconciliation"]["is_balanced"] is True
    assert len(eur["suggested_transfers"]) == 1
    assert eur["suggested_transfers"][0]["from_participant_id"] == rui
    assert eur["suggested_transfers"][0]["to_participant_id"] == ana
    assert eur["suggested_transfers"][0]["amount"] == "10.00"

    assert usd["reconciliation"]["total_expenses"] == "12.00"
    assert usd["reconciliation"]["total_paid"] == "12.00"
    assert usd["reconciliation"]["total_allocated"] == "12.00"
    assert usd["reconciliation"]["is_balanced"] is True
    assert len(usd["suggested_transfers"]) == 1
    assert usd["suggested_transfers"][0]["from_participant_id"] == ana
    assert usd["suggested_transfers"][0]["to_participant_id"] == rui
    assert usd["suggested_transfers"][0]["amount"] == "6.00"

    eur_positions = {row["participant_id"]: row for row in eur["participants"]}
    usd_positions = {row["participant_id"]: row for row in usd["participants"]}
    assert eur_positions[ana]["paid"] == "20.00"
    assert eur_positions[rui]["paid"] == "0.00"
    assert usd_positions[ana]["paid"] == "0.00"
    assert usd_positions[rui]["paid"] == "12.00"



def test_expense_shares_reject_duplicates_and_inexact_totals(client: TestClient) -> None:
    token = register_and_login(client, "expense-shares-validation@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    trip = client.post(
        "/api/v1/trips",
        headers=headers,
        json={"name": "Validação de divisões", "destination": "Lisboa"},
    )
    assert trip.status_code == 201
    trip_id = trip.json()["id"]

    participant_ids = []
    for name in ("Ana", "Rui"):
        response = client.post(
            f"/api/v1/trips/{trip_id}/participants",
            headers=headers,
            json={"name": name},
        )
        assert response.status_code == 201
        participant_ids.append(response.json()["id"])
    ana, rui = participant_ids

    expense = client.post(
        f"/api/v1/trips/{trip_id}/expenses",
        headers=headers,
        json={
            "category": "alimentacao",
            "description": "Almoço",
            "expense_date": "2027-08-06",
            "amount": "10.00",
            "currency": "EUR",
            "paid_by_participant_id": ana,
        },
    )
    assert expense.status_code == 201
    shares_url = f"/api/v1/trips/{trip_id}/expenses/{expense.json()['id']}/shares"

    duplicate = client.patch(
        shares_url,
        headers=headers,
        json=[
            {"participant_id": ana, "amount": "5.00"},
            {"participant_id": ana, "amount": "5.00"},
        ],
    )
    assert duplicate.status_code == 422
    assert "uma vez" in duplicate.json()["detail"]

    short_total = client.patch(
        shares_url,
        headers=headers,
        json=[
            {"participant_id": ana, "amount": "5.00"},
            {"participant_id": rui, "amount": "4.99"},
        ],
    )
    assert short_total.status_code == 422
    assert "exactamente igual" in short_total.json()["detail"]

    excess_total = client.patch(
        shares_url,
        headers=headers,
        json=[
            {"participant_id": ana, "amount": "5.00"},
            {"participant_id": rui, "amount": "5.01"},
        ],
    )
    assert excess_total.status_code == 422
    assert "exactamente igual" in excess_total.json()["detail"]

    valid = client.patch(
        shares_url,
        headers=headers,
        json=[
            {"participant_id": ana, "amount": "5.01"},
            {"participant_id": rui, "amount": "4.99"},
        ],
    )
    assert valid.status_code == 200
    assert sum(Decimal(item["amount"]) for item in valid.json()) == Decimal("10.00")
