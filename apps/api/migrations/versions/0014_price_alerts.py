"""Add user-defined price alerts.

Revision ID: 0014_price_alerts
Revises: 0013_price_observations
Create Date: 2026-11-11
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0014_price_alerts"
down_revision = "0013_price_observations"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "price_alerts",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("search_type", sa.String(length=12), nullable=False),
        sa.Column("search_key", sa.String(length=64), nullable=False),
        sa.Column("item_key", sa.String(length=160), nullable=False),
        sa.Column("item_name", sa.String(length=200), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("target_price", sa.Numeric(12, 2), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("triggered_price", sa.Numeric(12, 2), nullable=True),
        sa.Column("triggered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint("target_price > 0", name="ck_price_alerts_target_positive"),
    )
    op.create_index(
        "ix_price_alerts_matching",
        "price_alerts",
        ["user_id", "search_type", "search_key", "item_key", "is_active"],
    )


def downgrade() -> None:
    op.drop_index("ix_price_alerts_matching", table_name="price_alerts")
    op.drop_table("price_alerts")
