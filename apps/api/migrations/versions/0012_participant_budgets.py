"""Add individual participant budgets.

Revision ID: 0012_participant_budgets
Revises: 0011_hotel_favorites
Create Date: 2026-11-11
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0012_participant_budgets"
down_revision = "0011_hotel_favorites"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "participant_budgets",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("trip_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("participant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["trip_id"], ["trips.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["participant_id"], ["trip_participants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("participant_id", "currency", name="uq_participant_budgets_participant_currency"),
    )
    op.create_index("ix_participant_budgets_trip_id", "participant_budgets", ["trip_id"])
    op.create_index("ix_participant_budgets_participant_id", "participant_budgets", ["participant_id"])


def downgrade() -> None:
    op.drop_index("ix_participant_budgets_participant_id", table_name="participant_budgets")
    op.drop_index("ix_participant_budgets_trip_id", table_name="participant_budgets")
    op.drop_table("participant_budgets")
