"""Add platform access roles to users.

Revision ID: 0019_platform_roles
Revises: 0018_auth_sessions
Create Date: 2026-11-11
"""

from alembic import op
import sqlalchemy as sa

revision = "0019_platform_roles"
down_revision = "0018_auth_sessions"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("role", sa.String(length=20), server_default="traveler", nullable=False),
    )
    op.create_check_constraint(
        "ck_users_role",
        "users",
        "role IN ('traveler', 'support', 'admin')",
    )


def downgrade() -> None:
    op.drop_constraint("ck_users_role", "users", type_="check")
    op.drop_column("users", "role")
