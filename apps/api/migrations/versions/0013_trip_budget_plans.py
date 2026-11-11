"""Add monthly category budget plans.

Revision ID: 0013_trip_budget_plans
Revises: 0012_participant_budgets
Create Date: 2026-11-11
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0013_trip_budget_plans"
down_revision = "0012_participant_budgets"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "trip_budget_plans",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("trip_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("month", sa.String(length=7), nullable=False),
        sa.Column("category", sa.String(length=40), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["trip_id"], ["trips.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "trip_id", "month", "category", "currency",
            name="uq_trip_budget_plans_trip_month_category_currency",
        ),
    )
    op.create_index("ix_trip_budget_plans_trip_id", "trip_budget_plans", ["trip_id"])


def downgrade() -> None:
    op.drop_index("ix_trip_budget_plans_trip_id", table_name="trip_budget_plans")
    op.drop_table("trip_budget_plans")
