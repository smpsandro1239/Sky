"""Add per-user favorite hotels.

Revision ID: 0011_hotel_favorites
Revises: 0010_trip_settlements
Create Date: 2026-11-11
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0011_hotel_favorites"
down_revision = "0010_trip_settlements"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "hotel_favorites",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("provider", sa.String(length=40), nullable=False),
        sa.Column("hotel_id", sa.String(length=80), nullable=False),
        sa.Column("hotel_name", sa.String(length=180), nullable=False),
        sa.Column("location", sa.String(length=180), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "hotel_id", name="uq_hotel_favorites_user_hotel"),
    )
    op.create_index("ix_hotel_favorites_user_id", "hotel_favorites", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_hotel_favorites_user_id", table_name="hotel_favorites")
    op.drop_table("hotel_favorites")
