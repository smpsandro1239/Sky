"""Store real price observations returned by travel providers.

Revision ID: 0013_price_observations
Revises: 0012_participant_budgets
Create Date: 2026-11-11
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0013_price_observations"
down_revision = "0012_participant_budgets"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "price_observations",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("capture_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("search_type", sa.String(length=12), nullable=False),
        sa.Column("search_key", sa.String(length=64), nullable=False),
        sa.Column("provider", sa.String(length=40), nullable=False),
        sa.Column("item_key", sa.String(length=160), nullable=False),
        sa.Column("item_name", sa.String(length=200), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("is_available", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("search_criteria", sa.JSON(), nullable=False),
        sa.Column("captured_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("capture_id", "item_key", name="uq_price_observations_capture_item"),
    )
    op.create_index(
        "ix_price_observations_history",
        "price_observations",
        ["user_id", "search_type", "search_key", "item_key", "captured_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_price_observations_history", table_name="price_observations")
    op.drop_table("price_observations")
