from collections import defaultdict
from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.api.routes.trips import get_user_trip
from app.models.expense import Expense
from app.models.expense_share import ExpenseShare
from app.models.participant import TripParticipant
from app.models.user import User

router = APIRouter(prefix="/trips/{trip_id}/balances", tags=["balances"])


@router.get("")
def get_trip_balances(
    trip_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    trip = get_user_trip(db, trip_id, user.id)
    participants = list(db.scalars(
        select(TripParticipant).where(TripParticipant.trip_id == trip.id).order_by(TripParticipant.name)
    ).all())
    participant_names = {participant.id: participant.name for participant in participants}
    ledger: dict[str, dict[UUID, dict[str, Decimal]]] = defaultdict(
        lambda: defaultdict(lambda: {"paid": Decimal("0.00"), "owed": Decimal("0.00")})
    )

    expenses = list(db.scalars(
        select(Expense).where(
            Expense.trip_id == trip.id,
            Expense.paid_by_participant_id.is_not(None),
        )
    ).all())
    for expense in expenses:
        shares = list(db.scalars(
            select(ExpenseShare).where(ExpenseShare.expense_id == expense.id)
        ).all())
        if not shares:
            continue
        currency = expense.currency
        ledger[currency][expense.paid_by_participant_id]["paid"] += expense.amount
        for share in shares:
            ledger[currency][share.participant_id]["owed"] += share.amount

    result = []
    for currency in sorted(ledger):
        rows = []
        for participant in participants:
            values = ledger[currency][participant.id]
            net = values["paid"] - values["owed"]
            rows.append({
                "participant_id": str(participant.id),
                "name": participant_names[participant.id],
                "paid": str(values["paid"].quantize(Decimal("0.01"))),
                "owed": str(values["owed"].quantize(Decimal("0.01"))),
                "net": str(net.quantize(Decimal("0.01"))),
            })
        creditors = [
            {"id": UUID(row["participant_id"]), "name": row["name"], "cents": int(Decimal(row["net"]) * 100)}
            for row in rows if Decimal(row["net"]) > 0
        ]
        debtors = [
            {"id": UUID(row["participant_id"]), "name": row["name"], "cents": int(abs(Decimal(row["net"])) * 100)}
            for row in rows if Decimal(row["net"]) < 0
        ]
        settlements = []
        creditor_index = 0
        debtor_index = 0
        while creditor_index < len(creditors) and debtor_index < len(debtors):
            creditor = creditors[creditor_index]
            debtor = debtors[debtor_index]
            cents = min(creditor["cents"], debtor["cents"])
            if cents > 0:
                settlements.append({
                    "from_participant_id": str(debtor["id"]),
                    "from_name": debtor["name"],
                    "to_participant_id": str(creditor["id"]),
                    "to_name": creditor["name"],
                    "amount": f"{cents // 100}.{cents % 100:02d}",
                })
                creditor["cents"] -= cents
                debtor["cents"] -= cents
            if creditor["cents"] == 0:
                creditor_index += 1
            if debtor["cents"] == 0:
                debtor_index += 1
        result.append({"currency": currency, "participants": rows, "suggested_transfers": settlements})
    return {"currencies": result}
