"""Create expenses associated with trips.

Revision ID: 0003_trip_expenses
Revises: 0002_trip_budget
Create Date: 2026-11-10
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0003_trip_expenses"
down_revision = "0002_trip_budget"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "trip_expenses",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("trip_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("category", sa.String(length=40), nullable=False),
        sa.Column("description", sa.String(length=180), nullable=False),
        sa.Column("expense_date", sa.Date(), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("currency", sa.String(length=3), server_default="EUR", nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["trip_id"], ["trips.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_trip_expenses_trip_id", "trip_expenses", ["trip_id"])


def downgrade() -> None:
    op.drop_index("ix_trip_expenses_trip_id", table_name="trip_expenses")
    op.drop_table("trip_expenses")
