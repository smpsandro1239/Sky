"""Add participants to trips.

Revision ID: 0004_trip_participants
Revises: 0003_trip_expenses
Create Date: 2026-11-10
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0004_trip_participants"
down_revision = "0003_trip_expenses"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "trip_participants",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("trip_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["trip_id"], ["trips.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_trip_participants_trip_id", "trip_participants", ["trip_id"])


def downgrade() -> None:
    op.drop_index("ix_trip_participants_trip_id", table_name="trip_participants")
    op.drop_table("trip_participants")
