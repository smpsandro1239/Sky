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
    with op.batch_alter_table("trip_participants") as batch_op:
        batch_op.create_check_constraint("ck_trip_participant_role", "role IN ('editor', 'viewer')")
    with op.batch_alter_table("trip_invitations") as batch_op:
        batch_op.create_check_constraint("ck_trip_invitation_role", "role IN ('editor', 'viewer')")


def downgrade() -> None:
    with op.batch_alter_table("trip_invitations") as batch_op:
        batch_op.drop_constraint("ck_trip_invitation_role", type_="check")
        batch_op.drop_column("role")
    with op.batch_alter_table("trip_participants") as batch_op:
        batch_op.drop_constraint("ck_trip_participant_role", type_="check")
        batch_op.drop_column("role")
