from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.trip import Trip


def lock_trip_financials(db: Session, trip_id: UUID) -> None:
    """Serializa mutações financeiras da mesma viagem em bases de dados com row locks.

    PostgreSQL mantém o bloqueio até commit/rollback. SQLite, usado nos testes,
    não implementa SELECT FOR UPDATE.
    """
    db.execute(
        select(Trip.id).where(Trip.id == trip_id).with_for_update()
    ).scalar_one()
