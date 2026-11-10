"""Add account-linked participants and secure trip invitations.

Revision ID: 0007_trip_invitations
Revises: 0006_expense_payer
Create Date: 2026-11-10
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0007_trip_invitations"
down_revision = "0006_expense_payer"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "trip_participants",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    with op.batch_alter_table("trip_participants") as batch_op:
        batch_op.create_foreign_key(
            "fk_trip_participants_user_id", "users", ["user_id"], ["id"], ondelete="SET NULL"
        )
        batch_op.create_unique_constraint(
            "uq_trip_participant_user", ["trip_id", "user_id"]
        )
    op.create_index("ix_trip_participants_user_id", "trip_participants", ["user_id"])

    op.create_table(
        "trip_invitations",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("trip_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("invited_by_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=20), server_default="pending", nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["trip_id"], ["trips.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["invited_by_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token_hash", name="uq_trip_invitations_token_hash"),
    )
    op.create_index("ix_trip_invitations_trip_id", "trip_invitations", ["trip_id"])
    op.create_index("ix_trip_invitations_invited_by_user_id", "trip_invitations", ["invited_by_user_id"])
    op.create_index("ix_trip_invitations_email", "trip_invitations", ["email"])


def downgrade() -> None:
    op.drop_index("ix_trip_invitations_email", table_name="trip_invitations")
    op.drop_index("ix_trip_invitations_invited_by_user_id", table_name="trip_invitations")
    op.drop_index("ix_trip_invitations_trip_id", table_name="trip_invitations")
    op.drop_table("trip_invitations")
    op.drop_index("ix_trip_participants_user_id", table_name="trip_participants")
    with op.batch_alter_table("trip_participants") as batch_op:
        batch_op.drop_constraint("uq_trip_participant_user", type_="unique")
        batch_op.drop_constraint("fk_trip_participants_user_id", type_="foreignkey")
        batch_op.drop_column("user_id")
