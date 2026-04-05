"""add_stats_sync_trigger

Revision ID: b8b38838f78b
Revises: 766670f924f5
Create Date: 2026-04-05 23:03:43.262593

"""

from typing import Sequence, Union
import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = "b8b38838f78b"
down_revision: Union[str, Sequence[str], None] = "766670f924f5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create the function
    op.execute(
        sa.text(
            # language=postgresql
            """
        CREATE OR REPLACE FUNCTION sync_study_review_stats()
        RETURNS TRIGGER LANGUAGE plpgsql AS $$
        BEGIN
            INSERT INTO user_daily_stats (
                user_id, language_id, stat_date, 
                correct_count, incorrect_count, seconds_spent, new_words_count
            ) VALUES (
                NEW.user_id, NEW.language_id, DATE(NEW.reviewed_at),
                CASE WHEN NEW.was_correct = TRUE THEN 1 ELSE 0 END,
                CASE WHEN NEW.was_correct = FALSE THEN 1 ELSE 0 END,
                NEW.response_time::NUMERIC / 1000.0,
                0  
            )
            ON CONFLICT (user_id, language_id, stat_date) DO UPDATE SET
                correct_count = user_daily_stats.correct_count + EXCLUDED.correct_count,
                incorrect_count = user_daily_stats.incorrect_count + EXCLUDED.incorrect_count,
                seconds_spent = user_daily_stats.seconds_spent + EXCLUDED.seconds_spent;

            INSERT INTO user_stats_total (
                user_id, language_id, total_seconds, total_words
            ) VALUES (
                NEW.user_id, NEW.language_id, NEW.response_time::NUMERIC / 1000.0, 0  
            )
            ON CONFLICT (user_id, language_id) DO UPDATE SET
                total_seconds = user_stats_total.total_seconds + EXCLUDED.total_seconds;

            RETURN NEW;
        END;
        $$;
        """
        )
    )

    # 2. Create the trigger
    op.execute(
        sa.text("DROP TRIGGER IF EXISTS trg_sync_study_review_stats ON study_reviews;")
    )
    op.execute(
        sa.text("""
        CREATE TRIGGER trg_sync_study_review_stats
        AFTER INSERT ON study_reviews
        FOR EACH ROW EXECUTE FUNCTION sync_study_review_stats();
    """)
    )


def downgrade() -> None:
    op.execute(
        sa.text("DROP TRIGGER IF EXISTS trg_sync_study_review_stats ON study_reviews;")
    )
    op.execute(sa.text("DROP FUNCTION IF EXISTS sync_study_review_stats();"))
