"""add_audit_logging

Revision ID: caef4dd3ae6b
Revises: b8b38838f78b
Create Date: 2026-04-05 23:04:58.841136

"""

from typing import Sequence, Union
import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = "caef4dd3ae6b"
down_revision: Union[str, Sequence[str], None] = "b8b38838f78b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create the function
    op.execute(
        sa.text(
            # language=postgresql
            """
        CREATE OR REPLACE FUNCTION audit_log_content_changes()
        RETURNS TRIGGER LANGUAGE plpgsql AS $$
        DECLARE
            v_user_id INTEGER;
            v_old_json JSONB;
            v_new_json JSONB;
            v_changed_old JSONB;
            v_changed_new JSONB;
        BEGIN
            v_user_id := NULLIF(current_setting('app.current_user_id', true), '')::INTEGER;

            IF TG_OP = 'INSERT' THEN
                INSERT INTO content_audit_log (table_name, record_id, action, new_values, user_id)
                VALUES (TG_TABLE_NAME, NEW.id, 'INSERT', row_to_json(NEW), v_user_id);
            ELSIF TG_OP = 'UPDATE' THEN
                v_old_json := row_to_json(OLD);
                v_new_json := row_to_json(NEW);
                IF v_old_json IS DISTINCT FROM v_new_json THEN
                    SELECT jsonb_object_agg(key, value) INTO v_changed_old
                    FROM jsonb_each(v_old_json) WHERE value IS DISTINCT FROM v_new_json->key;
                    
                    SELECT jsonb_object_agg(key, value) INTO v_changed_new
                    FROM jsonb_each(v_new_json) WHERE value IS DISTINCT FROM v_old_json->key;
                    
                    INSERT INTO content_audit_log (table_name, record_id, action, old_values, new_values, user_id)
                    VALUES (TG_TABLE_NAME, NEW.id, 'UPDATE', v_changed_old, v_changed_new, v_user_id);
                END IF;
            ELSIF TG_OP = 'DELETE' THEN
                INSERT INTO content_audit_log (table_name, record_id, action, old_values, user_id)
                VALUES (TG_TABLE_NAME, OLD.id, 'DELETE', row_to_json(OLD), v_user_id);
            END IF;
            RETURN COALESCE(NEW, OLD);
        END;
        $$;
        """
        )
    )

    # 2. Triggers for items
    op.execute(sa.text("DROP TRIGGER IF EXISTS trg_audit_items ON items;"))
    op.execute(
        sa.text(
            "CREATE TRIGGER trg_audit_items AFTER INSERT OR UPDATE OR DELETE ON items FOR EACH ROW EXECUTE FUNCTION audit_log_content_changes();"
        )
    )

    # 3. Triggers for translations
    op.execute(
        sa.text("DROP TRIGGER IF EXISTS trg_audit_translations ON translations;")
    )
    op.execute(
        sa.text(
            "CREATE TRIGGER trg_audit_translations AFTER INSERT OR UPDATE OR DELETE ON translations FOR EACH ROW EXECUTE FUNCTION audit_log_content_changes();"
        )
    )

    # 4. Triggers for sets
    op.execute(sa.text("DROP TRIGGER IF EXISTS trg_audit_sets ON sets;"))
    op.execute(
        sa.text(
            "CREATE TRIGGER trg_audit_sets AFTER INSERT OR UPDATE OR DELETE ON sets FOR EACH ROW EXECUTE FUNCTION audit_log_content_changes();"
        )
    )

    # 5. Triggers for item_synonyms
    op.execute(
        sa.text("DROP TRIGGER IF EXISTS trg_audit_item_synonyms ON item_synonyms;")
    )
    op.execute(
        sa.text(
            "CREATE TRIGGER trg_audit_item_synonyms AFTER INSERT OR UPDATE OR DELETE ON item_synonyms FOR EACH ROW EXECUTE FUNCTION audit_log_content_changes();"
        )
    )


def downgrade() -> None:
    op.execute(sa.text("DROP TRIGGER IF EXISTS trg_audit_items ON items;"))
    op.execute(
        sa.text("DROP TRIGGER IF EXISTS trg_audit_translations ON translations;")
    )
    op.execute(sa.text("DROP TRIGGER IF EXISTS trg_audit_sets ON sets;"))
    op.execute(
        sa.text("DROP TRIGGER IF EXISTS trg_audit_item_synonyms ON item_synonyms;")
    )
    op.execute(sa.text("DROP FUNCTION IF EXISTS audit_log_content_changes();"))
