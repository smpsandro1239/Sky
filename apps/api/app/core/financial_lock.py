from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.expense import Expense

from app.models.settlement import TripSettlement
from app.models.trip import Trip


def lock_trip_financials(db: Session, trip_id: UUID) -> None:
    """Serializa mutações financeiras da mesma viagem em bases de dados com row locks.

    PostgreSQL mantém o bloqueio até commit/rollback. SQLite, usado nos testes,
    não implementa SELECT FOR UPDATE.
    """
    db.execute(
        select(Trip.id).where(Trip.id == trip_id).with_for_update()
    ).scalar_one()


def expense_has_prior_settlement(db: Session, expense: Expense) -> bool:
    """Indica se já existia um acerto quando esta despesa foi criada."""
    return db.scalar(
        select(TripSettlement.id)
        .where(
            TripSettlement.trip_id == expense.trip_id,
            TripSettlement.created_at >= expense.created_at,
        )
        .limit(1)
    ) is not None
