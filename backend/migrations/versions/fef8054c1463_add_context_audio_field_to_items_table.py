"""ADD context_audio field to items table

Revision ID: fef8054c1463
Revises: 497834a509ad
Create Date: 2026-05-16 12:59:30.129249

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = "fef8054c1463"
down_revision: Union[str, Sequence[str], None] = "497834a509ad"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("items", sa.Column("context_audio_url", sa.String(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("items", "context_audio_url")
