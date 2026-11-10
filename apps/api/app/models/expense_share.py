from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, ForeignKey, Numeric, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class ExpenseShare(Base):
    __tablename__ = "expense_shares"
    __table_args__ = (
        UniqueConstraint("expense_id", "participant_id", name="uq_expense_share_participant"),
        CheckConstraint("amount > 0", name="ck_expense_share_amount_positive"),
    )

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    expense_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("trip_expenses.id", ondelete="CASCADE"), nullable=False, index=True
    )
    participant_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("trip_participants.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    expense: Mapped["Expense"] = relationship(back_populates="shares")
    participant: Mapped["TripParticipant"] = relationship(back_populates="expense_shares")
