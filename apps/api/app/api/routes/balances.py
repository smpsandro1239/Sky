from collections import defaultdict
from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.api.routes.trips import get_accessible_trip
from app.models.expense import Expense
from app.models.expense_share import ExpenseShare
from app.models.participant import TripParticipant
from app.models.settlement import TripSettlement
from app.models.user import User

router = APIRouter(prefix="/trips/{trip_id}/balances", tags=["balances"])


@router.get("")
def get_trip_balances(
    trip_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    trip = get_accessible_trip(db, trip_id, user.id)
    participants = list(db.scalars(
        select(TripParticipant).where(TripParticipant.trip_id == trip.id).order_by(TripParticipant.name)
    ).all())
    ledger: dict[str, dict[UUID, dict[str, Decimal]]] = defaultdict(
        lambda: defaultdict(lambda: {
            "paid": Decimal("0.00"),
            "owed": Decimal("0.00"),
            "settled_sent": Decimal("0.00"),
            "settled_received": Decimal("0.00"),
        })
    )

    expenses = list(db.scalars(select(Expense).where(
        Expense.trip_id == trip.id,
        Expense.paid_by_participant_id.is_not(None),
    )).all())
    for expense in expenses:
        shares = list(db.scalars(
            select(ExpenseShare).where(ExpenseShare.expense_id == expense.id)
        ).all())
        if not shares:
            continue
        ledger[expense.currency][expense.paid_by_participant_id]["paid"] += expense.amount
        for share in shares:
            ledger[expense.currency][share.participant_id]["owed"] += share.amount

    settlements = list(db.scalars(
        select(TripSettlement).where(TripSettlement.trip_id == trip.id)
    ).all())
    for settlement in settlements:
        ledger[settlement.currency][settlement.from_participant_id]["settled_sent"] += settlement.amount
        ledger[settlement.currency][settlement.to_participant_id]["settled_received"] += settlement.amount

    result = []
    for currency in sorted(ledger):
        rows = []
        for participant in participants:
            values = ledger[currency][participant.id]
            net = values["paid"] - values["owed"] + values["settled_sent"] - values["settled_received"]
            rows.append({
                "participant_id": str(participant.id),
                "name": participant.name,
                "paid": str(values["paid"].quantize(Decimal("0.01"))),
                "owed": str(values["owed"].quantize(Decimal("0.01"))),
                "settled_sent": str(values["settled_sent"].quantize(Decimal("0.01"))),
                "settled_received": str(values["settled_received"].quantize(Decimal("0.01"))),
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
        transfers = []
        creditor_index = debtor_index = 0
        while creditor_index < len(creditors) and debtor_index < len(debtors):
            creditor, debtor = creditors[creditor_index], debtors[debtor_index]
            cents = min(creditor["cents"], debtor["cents"])
            if cents > 0:
                transfers.append({
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
        result.append({"currency": currency, "participants": rows, "suggested_transfers": transfers})
    return {"currencies": result}
