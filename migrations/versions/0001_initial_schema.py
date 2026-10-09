"""initial schema

Creates user, role, policy and todo. Each table is created only if it is missing, so databases
that were built by the pre-Alembic `create_all` (releases <= 0.4) are adopted rather than
failing; they simply gain whatever tables they lack (e.g. role/policy for 0.3 databases).

Revision ID: 0001
Revises:
Create Date: 2026-10-09
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import context, op

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _missing(table: str) -> bool:
    if context.is_offline_mode():  # `alembic upgrade --sql`: nothing to inspect, emit everything
        return True
    return not sa.inspect(op.get_bind()).has_table(table)


def upgrade() -> None:
    if _missing("role"):
        op.create_table(
            "role",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("name", sa.String(length=32), nullable=False),
            sa.Column("description", sa.String(), nullable=True),
            sa.Column("is_system", sa.Boolean(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_role_name", "role", ["name"], unique=True)

    if _missing("user"):
        op.create_table(
            "user",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("email", sa.String(length=254), nullable=False),
            sa.Column("hashed_password", sa.String(), nullable=False),
            sa.Column("role", sa.String(), nullable=False),
            sa.Column("is_active", sa.Boolean(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_user_email", "user", ["email"], unique=True)
        op.create_index("ix_user_role", "user", ["role"], unique=False)

    if _missing("policy"):
        op.create_table(
            "policy",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("role_id", sa.Integer(), nullable=False),
            sa.Column("action", sa.String(length=16), nullable=False),
            sa.Column("subject", sa.String(length=32), nullable=False),
            sa.Column("conditions", sa.JSON(), nullable=True),
            sa.Column("fields", sa.JSON(), nullable=True),
            sa.Column("inverted", sa.Boolean(), nullable=False),
            sa.ForeignKeyConstraint(["role_id"], ["role.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_policy_role_id", "policy", ["role_id"], unique=False)

    if _missing("todo"):
        op.create_table(
            "todo",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("title", sa.String(length=200), nullable=False),
            sa.Column("description", sa.String(), nullable=True),
            sa.Column("completed", sa.Boolean(), nullable=False),
            sa.Column("owner_id", sa.Integer(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(["owner_id"], ["user.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_todo_owner_id", "todo", ["owner_id"], unique=False)
        op.create_index("ix_todo_title", "todo", ["title"], unique=False)


def downgrade() -> None:
    op.drop_table("todo")
    op.drop_table("policy")
    op.drop_table("user")
    op.drop_table("role")
