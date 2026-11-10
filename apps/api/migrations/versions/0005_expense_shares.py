"""Add participant shares to trip expenses.

Revision ID: 0005_expense_shares
Revises: 0004_trip_participants
Create Date: 2026-11-10
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0005_expense_shares"
down_revision = "0004_trip_participants"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "expense_shares",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("expense_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("participant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.CheckConstraint("amount > 0", name="ck_expense_share_amount_positive"),
        sa.ForeignKeyConstraint(["expense_id"], ["trip_expenses.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["participant_id"], ["trip_participants.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("expense_id", "participant_id", name="uq_expense_share_participant"),
    )
    op.create_index("ix_expense_shares_expense_id", "expense_shares", ["expense_id"])
    op.create_index("ix_expense_shares_participant_id", "expense_shares", ["participant_id"])


def downgrade() -> None:
    op.drop_index("ix_expense_shares_participant_id", table_name="expense_shares")
    op.drop_index("ix_expense_shares_expense_id", table_name="expense_shares")
    op.drop_table("expense_shares")
