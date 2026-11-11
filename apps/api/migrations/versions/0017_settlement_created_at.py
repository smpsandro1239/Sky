"""Track when settlements are recorded independently of payment date.

Revision ID: 0017_settlement_created_at
Revises: 0016_notifications
Create Date: 2026-11-11
"""

from alembic import op
import sqlalchemy as sa

revision = "0017_settlement_created_at"
down_revision = "0016_notifications"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "trip_settlements",
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_trip_settlements_trip_created",
        "trip_settlements",
        ["trip_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_trip_settlements_trip_created", table_name="trip_settlements")
    op.drop_column("trip_settlements", "created_at")
