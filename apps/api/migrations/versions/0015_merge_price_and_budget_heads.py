"""Merge price intelligence and monthly budget migration branches.

Revision ID: 0015_merge_price_and_budget_heads
Revises: 0014_price_alerts, 0013_trip_budget_plans
Create Date: 2026-11-11
"""

revision = "0015_merge_price_and_budget_heads"
down_revision = ("0014_price_alerts", "0013_trip_budget_plans")
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
