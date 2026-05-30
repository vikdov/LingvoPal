"""Add pending_email to users

Revision ID: b3c4d5e6f7a8
Revises: fef8054c1463
Create Date: 2026-05-18 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "b3c4d5e6f7a8"
down_revision: Union[str, Sequence[str], None] = "fef8054c1463"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "pending_email", sa.String(), nullable=True, comment="New email awaiting confirmation"
        ),
    )


def downgrade() -> None:
    op.drop_column("users", "pending_email")
