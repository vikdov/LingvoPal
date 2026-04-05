"""add_timestamp_triggers

Revision ID: 766670f924f5
Revises: 31041260b64b
Create Date: 2026-04-05 22:19:24.008994

"""

from typing import Sequence, Union
import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = "766670f924f5"
down_revision: Union[str, Sequence[str], None] = "31041260b64b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create the function (This is one single command)
    op.execute(
        sa.text(
            # language=postgresql
            """
        CREATE OR REPLACE FUNCTION set_updated_at()
        RETURNS TRIGGER LANGUAGE plpgsql AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$;
        """
        )
    )

    # 2. Attach to Items (Split into two commands)
    op.execute(sa.text("DROP TRIGGER IF EXISTS trg_items_updated_at ON items;"))
    op.execute(
        sa.text(
            "CREATE TRIGGER trg_items_updated_at BEFORE UPDATE ON items FOR EACH ROW EXECUTE FUNCTION set_updated_at();"
        )
    )

    # 3. Attach to Sets
    op.execute(sa.text("DROP TRIGGER IF EXISTS trg_sets_updated_at ON sets;"))
    op.execute(
        sa.text(
            "CREATE TRIGGER trg_sets_updated_at BEFORE UPDATE ON sets FOR EACH ROW EXECUTE FUNCTION set_updated_at();"
        )
    )

    # 4. Attach to Translations
    op.execute(
        sa.text("DROP TRIGGER IF EXISTS trg_translations_updated_at ON translations;")
    )
    op.execute(
        sa.text(
            "CREATE TRIGGER trg_translations_updated_at BEFORE UPDATE ON translations FOR EACH ROW EXECUTE FUNCTION set_updated_at();"
        )
    )

    # 5. Attach to Synonyms
    op.execute(
        sa.text("DROP TRIGGER IF EXISTS trg_item_synonyms_updated_at ON item_synonyms;")
    )
    op.execute(
        sa.text(
            "CREATE TRIGGER trg_item_synonyms_updated_at BEFORE UPDATE ON item_synonyms FOR EACH ROW EXECUTE FUNCTION set_updated_at();"
        )
    )


def downgrade() -> None:
    # Split the downgrades as well!
    op.execute(sa.text("DROP TRIGGER IF EXISTS trg_items_updated_at ON items;"))
    op.execute(sa.text("DROP TRIGGER IF EXISTS trg_sets_updated_at ON sets;"))
    op.execute(
        sa.text("DROP TRIGGER IF EXISTS trg_translations_updated_at ON translations;")
    )
    op.execute(
        sa.text("DROP TRIGGER IF EXISTS trg_item_synonyms_updated_at ON item_synonyms;")
    )
    op.execute(sa.text("DROP FUNCTION IF EXISTS set_updated_at();"))
