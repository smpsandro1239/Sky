"""Add viewer and editor roles to trip participants and invitations.

Revision ID: 0008_trip_member_roles
Revises: 0007_trip_invitations
Create Date: 2026-11-10
"""

from alembic import op
import sqlalchemy as sa

revision = "0008_trip_member_roles"
down_revision = "0007_trip_invitations"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "trip_participants",
        sa.Column("role", sa.String(length=20), server_default="viewer", nullable=False),
    )
    op.add_column(
        "trip_invitations",
        sa.Column("role", sa.String(length=20), server_default="viewer", nullable=False),
    )


def downgrade() -> None:
    op.drop_column("trip_invitations", "role")
    op.drop_column("trip_participants", "role")
