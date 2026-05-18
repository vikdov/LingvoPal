"""Convert email/username unique constraints to partial (exclude soft-deleted rows)

Revision ID: c7d8e9f0a1b2
Revises: b3c4d5e6f7a8
Create Date: 2026-05-18 00:00:00.000000

Without this migration, soft-deleted users permanently lock their email and
username — new registrations with the same credentials are rejected even though
the original account is inactive.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "c7d8e9f0a1b2"
down_revision: Union[str, Sequence[str], None] = "b3c4d5e6f7a8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop hard unique constraints that ignore soft-deletion
    op.drop_index("ix_users_email", table_name="users", if_exists=True)
    op.drop_constraint("uq_users_email", table_name="users", type_="unique", if_exists=True)
    op.drop_index("ix_users_username", table_name="users", if_exists=True)
    op.drop_constraint("uq_users_username", table_name="users", type_="unique", if_exists=True)

    # Partial unique indexes: only active (non-deleted) rows participate
    op.execute(
        "CREATE UNIQUE INDEX uq_users_email_active ON users (email) WHERE deleted_at IS NULL"
    )
    op.execute(
        "CREATE UNIQUE INDEX uq_users_username_active ON users (username) WHERE deleted_at IS NULL AND username IS NOT NULL"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS uq_users_email_active")
    op.execute("DROP INDEX IF EXISTS uq_users_username_active")

    # Restore original hard unique constraints (data loss risk if duplicates exist)
    op.create_unique_constraint("uq_users_email", "users", ["email"])
    op.create_unique_constraint("uq_users_username", "users", ["username"])
