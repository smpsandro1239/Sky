from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class TripSettlement(Base):
    __tablename__ = "trip_settlements"
    __table_args__ = (
        CheckConstraint("amount > 0", name="ck_trip_settlement_amount_positive"),
        CheckConstraint("from_participant_id <> to_participant_id", name="ck_trip_settlement_distinct_participants"),
    )

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    trip_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("trips.id", ondelete="CASCADE"), nullable=False, index=True
    )
    from_participant_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("trip_participants.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    to_participant_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("trip_participants.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    paid_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    notes: Mapped[str | None] = mapped_column(Text)
    created_by_user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
