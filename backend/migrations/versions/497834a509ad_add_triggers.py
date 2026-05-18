"""add_triggers: updated_at triggers + audit logging + user stats repair functions

Revision ID: 497834a509ad
Revises: 928f022370b7
Create Date: 2026-05-10 19:06:23.439970
"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "497834a509ad"
down_revision: Union[str, Sequence[str], None] = "928f022370b7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None
CONTENT_TABLES = ["items", "sets", "translations", "item_synonym_terms"]


def upgrade() -> None:
    """Upgrade schema."""

    # ================================================================
    # 1. Shared updated_at trigger function
    # ================================================================
    op.execute("""
        CREATE OR REPLACE FUNCTION set_updated_at()
        RETURNS TRIGGER
        LANGUAGE plpgsql
        AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$;
    """)

    # Create BEFORE UPDATE triggers for all tables that track updated_at
    updated_at_tables = CONTENT_TABLES
    for table in updated_at_tables:
        op.execute(f"""
            CREATE TRIGGER trg_{table}_updated_at
            BEFORE UPDATE ON {table}
            FOR EACH ROW EXECUTE FUNCTION set_updated_at();
        """)

    # ================================================================
    # 2. Audit logging function + triggers
    # ================================================================
    op.execute("""
        CREATE OR REPLACE FUNCTION audit_log_content_changes()
        RETURNS TRIGGER
        LANGUAGE plpgsql
        AS $$
        DECLARE
            v_user_id     INTEGER;
            v_old_json    JSONB;
            v_new_json    JSONB;
            v_changed_old JSONB;
            v_changed_new JSONB;
        BEGIN
            v_user_id := NULLIF(current_setting('app.current_user_id', true), '')::INTEGER;

            IF TG_OP = 'INSERT' THEN
                INSERT INTO content_audit_log (table_name, record_id, action, new_values, user_id)
                VALUES (TG_TABLE_NAME, NEW.id, 'INSERT', row_to_json(NEW)::jsonb, v_user_id);

            ELSIF TG_OP = 'UPDATE' THEN
                v_old_json := row_to_json(OLD)::jsonb;
                v_new_json := row_to_json(NEW)::jsonb;

                IF v_old_json IS DISTINCT FROM v_new_json THEN
                    SELECT jsonb_object_agg(key, value) INTO v_changed_old
                    FROM jsonb_each(v_old_json)
                    WHERE value IS DISTINCT FROM v_new_json->key;

                    SELECT jsonb_object_agg(key, value) INTO v_changed_new
                    FROM jsonb_each(v_new_json)
                    WHERE value IS DISTINCT FROM v_old_json->key;

                    INSERT INTO content_audit_log (table_name, record_id, action, old_values, new_values, user_id)
                    VALUES (TG_TABLE_NAME, NEW.id, 'UPDATE', v_changed_old, v_changed_new, v_user_id);
                END IF;

            ELSIF TG_OP = 'DELETE' THEN
                INSERT INTO content_audit_log (table_name, record_id, action, old_values, user_id)
                VALUES (TG_TABLE_NAME, OLD.id, 'DELETE', row_to_json(OLD)::jsonb, v_user_id);
            END IF;

            RETURN COALESCE(NEW, OLD);
        END;
        $$;
    """)

    # Create AFTER INSERT/UPDATE/DELETE audit triggers
    audit_tables = CONTENT_TABLES
    for table in audit_tables:
        op.execute(f"""
            CREATE TRIGGER trg_audit_{table}
            AFTER INSERT OR UPDATE OR DELETE ON {table}
            FOR EACH ROW EXECUTE FUNCTION audit_log_content_changes();
        """)

    # ================================================================
    # 3. User stats repair functions
    # ================================================================
    op.execute("""
        CREATE OR REPLACE FUNCTION repair_user_stats(p_user_id INTEGER)
        RETURNS TABLE (daily_fixed INTEGER, totals_fixed INTEGER)
        LANGUAGE plpgsql
        AS $$
        DECLARE
            v_daily_count  INTEGER := 0;
            v_totals_count INTEGER := 0;
        BEGIN
            -- 1. Daily stats (with proper new_words detection)
            WITH first_reviews AS (
                SELECT item_id, MIN(DATE(reviewed_at)) AS first_seen_date
                FROM study_reviews
                WHERE user_id = p_user_id AND was_correct IS NOT NULL
                GROUP BY item_id
            ),
            daily_recalc AS (
                SELECT
                    sr.user_id,
                    sr.language_id,
                    DATE(sr.reviewed_at) AS stat_date,
                    SUM(CASE WHEN sr.was_correct THEN 1 ELSE 0 END)::INTEGER AS correct_count,
                    SUM(CASE WHEN NOT sr.was_correct THEN 1 ELSE 0 END)::INTEGER AS incorrect_count,
                    SUM(sr.response_time::NUMERIC / 1000.0) AS seconds_spent,
                    COUNT(DISTINCT fr.item_id)::INTEGER AS new_words_count
                FROM study_reviews sr
                LEFT JOIN first_reviews fr
                    ON sr.item_id = fr.item_id
                   AND DATE(sr.reviewed_at) = fr.first_seen_date
                WHERE sr.user_id = p_user_id
                  AND sr.was_correct IS NOT NULL
                GROUP BY sr.user_id, sr.language_id, DATE(sr.reviewed_at)
            )
            INSERT INTO user_daily_stats (
                user_id, language_id, stat_date,
                correct_count, incorrect_count, seconds_spent, new_words_count
            )
            SELECT * FROM daily_recalc
            ON CONFLICT (user_id, language_id, stat_date) DO UPDATE SET
                correct_count   = EXCLUDED.correct_count,
                incorrect_count = EXCLUDED.incorrect_count,
                seconds_spent   = EXCLUDED.seconds_spent,
                new_words_count = EXCLUDED.new_words_count;

            GET DIAGNOSTICS v_daily_count = ROW_COUNT;

            -- 2. Totals from daily stats
            INSERT INTO user_stats_total (user_id, language_id, total_seconds, total_words, last_recalculated_at)
            SELECT
                user_id,
                language_id,
                SUM(seconds_spent),
                SUM(new_words_count),
                NOW()
            FROM user_daily_stats
            WHERE user_id = p_user_id
            GROUP BY user_id, language_id
            ON CONFLICT (user_id, language_id) DO UPDATE SET
                total_seconds = EXCLUDED.total_seconds,
                total_words   = EXCLUDED.total_words,
                last_recalculated_at = EXCLUDED.last_recalculated_at;

            GET DIAGNOSTICS v_totals_count = ROW_COUNT;

            RETURN QUERY SELECT v_daily_count, v_totals_count;
        END;
        $$;
    """)

    op.execute("""
        CREATE OR REPLACE FUNCTION repair_all_user_stats()
        RETURNS TABLE (user_id INTEGER, daily_fixed INTEGER, totals_fixed INTEGER)
        LANGUAGE plpgsql
        AS $$
        BEGIN
            RETURN QUERY
            SELECT u.id, r.daily_fixed, r.totals_fixed
            FROM users u
            CROSS JOIN LATERAL repair_user_stats(u.id) AS r(daily_fixed, totals_fixed)
            WHERE u.deleted_at IS NULL;
        END;
        $$;
    """)


def downgrade() -> None:
    """Downgrade schema - safely remove everything in reverse order."""

    # Drop repair functions first (they depend on other tables)
    op.execute("DROP FUNCTION IF EXISTS repair_all_user_stats();")
    op.execute("DROP FUNCTION IF EXISTS repair_user_stats(INTEGER);")

    # Drop audit triggers and function
    audit_tables = CONTENT_TABLES
    for table in audit_tables:
        op.execute(f"DROP TRIGGER IF EXISTS trg_audit_{table} ON {table};")

    op.execute("DROP FUNCTION IF EXISTS audit_log_content_changes();")

    # Drop updated_at triggers and function
    updated_at_tables = CONTENT_TABLES
    for table in updated_at_tables:
        op.execute(f"DROP TRIGGER IF EXISTS trg_{table}_updated_at ON {table};")

    op.execute("DROP FUNCTION IF EXISTS set_updated_at();")
