"""Add an optional per-trip budget.

Revision ID: 0002_trip_budget
Revises: 0001_initial
Create Date: 2026-11-10
"""

from alembic import op
import sqlalchemy as sa

revision = "0002_trip_budget"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("trips", sa.Column("budget_amount", sa.Numeric(12, 2), nullable=True))
    op.add_column(
        "trips",
        sa.Column("budget_currency", sa.String(length=3), server_default="EUR", nullable=False),
    )


def downgrade() -> None:
    op.drop_column("trips", "budget_currency")
    op.drop_column("trips", "budget_amount")
