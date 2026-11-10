"""Track who paid each group expense.

Revision ID: 0006_expense_payer
Revises: 0005_expense_shares
Create Date: 2026-11-10
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0006_expense_payer"
down_revision = "0005_expense_shares"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "trip_expenses",
        sa.Column("paid_by_participant_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_trip_expenses_paid_by_participant",
        "trip_expenses",
        "trip_participants",
        ["paid_by_participant_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_index(
        "ix_trip_expenses_paid_by_participant_id",
        "trip_expenses",
        ["paid_by_participant_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_trip_expenses_paid_by_participant_id", table_name="trip_expenses")
    op.drop_constraint("fk_trip_expenses_paid_by_participant", "trip_expenses", type_="foreignkey")
    op.drop_column("trip_expenses", "paid_by_participant_id")
