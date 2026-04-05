"""add_stats_repair_functions

Revision ID: 8a8a4dcf2ed9
Revises: caef4dd3ae6b
Create Date: 2026-04-05 23:06:11.825148

"""

from typing import Sequence, Union
import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = "8a8a4dcf2ed9"
down_revision: Union[str, Sequence[str], None] = "caef4dd3ae6b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create the user-specific repair function
    op.execute(
        sa.text(
            # language=postgresql
            """
        CREATE OR REPLACE FUNCTION repair_user_stats(p_user_id INTEGER)
        RETURNS TABLE (daily_fixed INTEGER, totals_fixed INTEGER) AS $$
        DECLARE
            v_daily_count INTEGER := 0;
            v_totals_count INTEGER := 0;
        BEGIN
            WITH first_reviews AS (
                SELECT item_id, MIN(DATE(reviewed_at)) as first_seen_date
                FROM study_reviews WHERE user_id = p_user_id AND was_correct IS NOT NULL
                GROUP BY item_id
            ),
            daily_recalc AS (
                SELECT sr.user_id, sr.language_id, DATE(sr.reviewed_at) as stat_date,
                    SUM(CASE WHEN sr.was_correct = TRUE THEN 1 ELSE 0 END)::INTEGER as correct_count,
                    SUM(CASE WHEN sr.was_correct = FALSE THEN 1 ELSE 0 END)::INTEGER as incorrect_count,
                    SUM(sr.response_time::NUMERIC / 1000.0) as seconds_spent,
                    COUNT(DISTINCT fr.item_id)::INTEGER as new_words_count
                FROM study_reviews sr
                LEFT JOIN first_reviews fr ON sr.item_id = fr.item_id AND DATE(sr.reviewed_at) = fr.first_seen_date
                WHERE sr.user_id = p_user_id AND sr.was_correct IS NOT NULL
                GROUP BY sr.user_id, sr.language_id, DATE(sr.reviewed_at)
            )
            INSERT INTO user_daily_stats (
                user_id, language_id, stat_date, correct_count, incorrect_count, seconds_spent, new_words_count
            )
            SELECT user_id, language_id, stat_date, correct_count, incorrect_count, seconds_spent, new_words_count
            FROM daily_recalc
            ON CONFLICT (user_id, language_id, stat_date) DO UPDATE SET
                correct_count = EXCLUDED.correct_count,
                incorrect_count = EXCLUDED.incorrect_count,
                seconds_spent = EXCLUDED.seconds_spent,
                new_words_count = EXCLUDED.new_words_count;

            GET DIAGNOSTICS v_daily_count = ROW_COUNT;

            INSERT INTO user_stats_total (user_id, language_id, total_seconds, total_words, last_repaired)
            SELECT user_id, language_id, SUM(seconds_spent), SUM(new_words_count), NOW()
            FROM user_daily_stats WHERE user_id = p_user_id
            GROUP BY user_id, language_id
            ON CONFLICT (user_id, language_id) DO UPDATE SET
                total_seconds = EXCLUDED.total_seconds,
                total_words = EXCLUDED.total_words,
                last_repaired = EXCLUDED.last_repaired;

            GET DIAGNOSTICS v_totals_count = ROW_COUNT;
            RETURN QUERY SELECT v_daily_count, v_totals_count;
        END;
        $$ LANGUAGE plpgsql;
        """
        )
    )

    # 2. Create the ALL users repair function
    op.execute(
        sa.text(
            # language=postgresql
            """
        CREATE OR REPLACE FUNCTION repair_all_user_stats()
        RETURNS TABLE (user_id INTEGER, daily_fixed INTEGER, totals_fixed INTEGER) AS $$
        BEGIN
            RETURN QUERY
            SELECT u.id, daily_result.daily_fixed, daily_result.totals_fixed
            FROM users u
            CROSS JOIN LATERAL repair_user_stats(u.id) AS daily_result(daily_fixed, totals_fixed)
            WHERE u.deleted_at IS NULL;
        END;
        $$ LANGUAGE plpgsql;
        """
        )
    )


def downgrade() -> None:
    op.execute(sa.text("DROP FUNCTION IF EXISTS repair_all_user_stats();"))
    op.execute(sa.text("DROP FUNCTION IF EXISTS repair_user_stats(INTEGER);"))
