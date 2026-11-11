"""Add recorded participant settlements.

Revision ID: 0010_trip_settlements
Revises: 0009_trip_activity
Create Date: 2026-11-11
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0010_trip_settlements"
down_revision = "0009_trip_activity"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "trip_settlements",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("trip_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("from_participant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("to_participant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("paid_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.CheckConstraint("amount > 0", name="ck_trip_settlement_amount_positive"),
        sa.CheckConstraint(
            "from_participant_id <> to_participant_id",
            name="ck_trip_settlement_distinct_participants",
        ),
        sa.ForeignKeyConstraint(["trip_id"], ["trips.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["from_participant_id"], ["trip_participants.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["to_participant_id"], ["trip_participants.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_trip_settlements_trip_id", "trip_settlements", ["trip_id"])
    op.create_index(
        "ix_trip_settlements_from_participant_id",
        "trip_settlements",
        ["from_participant_id"],
    )
    op.create_index(
        "ix_trip_settlements_to_participant_id",
        "trip_settlements",
        ["to_participant_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_trip_settlements_to_participant_id", table_name="trip_settlements")
    op.drop_index("ix_trip_settlements_from_participant_id", table_name="trip_settlements")
    op.drop_index("ix_trip_settlements_trip_id", table_name="trip_settlements")
    op.drop_table("trip_settlements")
