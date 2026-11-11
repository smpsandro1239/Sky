"""Add per-trip activity history.

Revision ID: 0009_trip_activity
Revises: 0008_trip_member_roles
Create Date: 2026-11-11
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0009_trip_activity"
down_revision = "0008_trip_member_roles"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "trip_activity",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("trip_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("actor_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("actor_name", sa.String(length=120), nullable=False),
        sa.Column("action", sa.String(length=20), nullable=False),
        sa.Column("entity_type", sa.String(length=30), nullable=False),
        sa.Column("entity_id", sa.String(length=36), nullable=True),
        sa.Column("summary", sa.String(length=240), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["trip_id"], ["trips.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["actor_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_trip_activity_trip_created", "trip_activity", ["trip_id", "created_at"])


def downgrade() -> None:
    op.drop_index("ix_trip_activity_trip_created", table_name="trip_activity")
    op.drop_table("trip_activity")
