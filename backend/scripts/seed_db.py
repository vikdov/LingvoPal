import sys
from pathlib import Path

current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent
sys.path.insert(0, str(project_root / "backend"))

import asyncio

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.database.session import (
    get_session,
    init_async_session_factory,
    shutdown_db_engine,
)


async def reset_sequence(db: AsyncSession, table: str, pk_column: str = "id"):
    """Reset PostgreSQL sequence after manual ID inserts."""
    await db.execute(
        text(f"""
            SELECT setval(
                pg_get_serial_sequence('{table}', '{pk_column}'),
                COALESCE(MAX({pk_column}), 1),
                MAX({pk_column}) IS NOT NULL
            )
            FROM {table};
        """)
    )


async def clear_seed_data(db: AsyncSession):
    """Safely clear seed data in reverse dependency order."""
    tables = [
        "study_reviews",
        "pending_sessions",
        "study_sessions",
        "user_progress",
        "user_set_library",
        "set_items",
        "pending_moderation",
        "content_complaints",
        "translations",
        "item_synonym_terms",
        "item_quality_metrics",
        "items",
        "sets",
        "user_daily_stats",
        "user_stats_total",
        "user_settings",
        "user_languages",
        "users",
        "languages",
    ]

    for table in tables:
        await db.execute(text(f"TRUNCATE TABLE {table} CASCADE;"))
    print("✓ Cleared existing seed data")


async def seed_languages(db: AsyncSession):
    """Seed language references."""
    print("Seeding Languages...")
    await db.execute(
        text("""
            INSERT INTO languages (id, code, name) VALUES
            (1, 'en', 'English'),
            (2, 'pl', 'Polish'),
            (3, 'de', 'German'),
            (4, 'es', 'Spanish'),
            (5, 'fr', 'French'),
            (6, 'uk', 'Ukrainian')
            ON CONFLICT (id) DO NOTHING;
        """)
    )
    await reset_sequence(db, "languages")


async def seed_users(db: AsyncSession):
    """Seed test users."""
    print("Seeding Users...")
    # Dummy bcrypt hash for "Password1"
    dummy_hash = "$2b$12$XbbY670KjWrbOgYJ/XipFO3ociSlj7V0nvor//yYwd5vGLw0wS3Zq"

    await db.execute(
        text("""
            INSERT INTO users (id, user_status, email, email_verified, password_hash, username)
            VALUES
            (1, 'admin', 'admin@lingvopal.com', true, :hash, 'admin_user'),
            (2, 'user', 'user@example.com', true, :hash, 'user'),
            (3, 'user', 'user1@example.com', true, :hash, 'user2'),
            (4, 'user', 'test.user@example.com', false, :hash, 'test_user')
            ON CONFLICT (id) DO NOTHING;
        """),
        {"hash": dummy_hash},
    )
    await reset_sequence(db, "users")


async def seed_user_settings(db: AsyncSession):
    """Seed user settings aligned with schema."""
    print("Seeding User Settings...")
    await db.execute(
        text("""
            INSERT INTO user_settings (
                user_id, native_lang_id, interface_lang_id, learning_intensity,
                evaluation_mode, show_hints_on_fails, daily_study_goal,
                reminder_time, streak_reminders_enabled, show_translations,
                show_images, show_synonyms, show_part_of_speech,
                auto_play_audio, new_items_per_day_limit, new_items_per_session,
                retention_priority, max_review_load_per_day, created_at
            ) VALUES
            (1, 1, 1, 'intensive', 'normal', true, 30, '09:00:00', true, true, true, true, true, true, 15, 10, 'long_term_mastery', 100, NOW()),
            (2, 2, 1, 'balanced', 'normal', true, 20, '10:00:00', true, true, true, true, true, true, 10, 5, 'balanced', 50, NOW()),
            (3, 4, 1, 'light', 'forgiving', false, 10, NULL, false, true, false, true, true, false, 5, 3, 'speed_learning', NULL, NOW()),
            (4, 1, 2, 'balanced', 'strict', true, 15, '08:00:00', true, true, true, true, true, true, 8, 4, 'balanced', 75, NOW())
            ON CONFLICT (user_id) DO NOTHING;
        """)
    )


async def seed_user_languages(db: AsyncSession):
    """Seed user language learning preferences."""
    print("Seeding User Languages...")
    await db.execute(
        text("""
            INSERT INTO user_languages (user_id, language_id, is_active, created_at)
            VALUES
            (1, 2, true, NOW()),
            (1, 3, false, NOW()),
            (2, 1, true, NOW()),
            (2, 4, false, NOW()),
            (3, 5, true, NOW()),
            (4, 1, true, NOW())
            ON CONFLICT (user_id, language_id) DO NOTHING;
        """)
    )


async def seed_items(db: AsyncSession):
    """Seed vocabulary items."""
    print("Seeding Vocabulary Items...")
    await db.execute(
        text("""
            INSERT INTO items (
                id, language_id, term, difficulty, context, part_of_speech,
                lemma, creator_id, status, created_at
            ) VALUES
            -- English items
            (1, 1, 'serendipity', 5, 'Finding something valuable by chance', 'noun', 'serendipity', 1, 'approved', NOW()),
            (2, 1, 'ephemeral', 6, 'Lasting for a very short time', 'adjective', 'ephemeral', 1, 'approved', NOW()),
            (3, 1, 'eloquent', 5, 'Fluent or persuasive in speaking or writing', 'adjective', 'eloquent', 1, 'community', NOW()),
            (4, 1, 'meticulous', 4, 'Showing great attention to detail', 'adjective', 'meticulous', 2, 'community', NOW()),

            -- Polish items
            (5, 2, 'zwiedzać', 2, 'Odwiedzać miejsce turystyczne', 'verb', 'zwiedzić', 1, 'approved', NOW()),
            (6, 2, 'smuteczek', 3, 'Mały smutek, przygnębienie', 'noun', 'smuteczek', 1, 'community', NOW()),
            (7, 2, 'piękny', 1, 'Ładny, przystojna', 'adjective', 'piękny', 2, 'approved', NOW()),

            -- German items
            (8, 3, 'Wanderlust', 4, 'Lust auf Wanderungen und Reisen', 'noun', 'Wanderlust', 1, 'approved', NOW()),
            (9, 3, 'Schadenfreude', 5, 'Freude über das Missgeschick anderer', 'noun', 'Schadenfreude', 1, 'approved', NOW()),

            -- Spanish items
            (10, 4, 'Sobremesa', 4, 'El tiempo después de comer', 'noun', 'sobremesa', 1, 'approved', NOW()),
            (11, 4, 'Saudade', 6, 'Nostalgia profunda', 'noun', 'saudade', 2, 'community', NOW())
            ON CONFLICT (id) DO NOTHING;
        """)
    )
    await reset_sequence(db, "items")


async def seed_translations(db: AsyncSession):
    """Seed translations for items."""
    print("Seeding Translations...")
    await db.execute(
        text("""
            INSERT INTO translations (
                id, item_id, language_id, term_trans, context_trans, creator_id, status, created_at
            ) VALUES
            -- English -> Polish
            (1, 1, 2, 'zbiég szczęśliwych okoliczności', 'Znalezienie czegoś cennego przez przypadek', 1, 'approved', NOW()),
            (2, 2, 2, 'ulotny', 'Trwający bardzo krótko', 1, 'approved', NOW()),
            (3, 3, 2, 'wymowny', 'Płynny lub przekonujący w mówieniu', 2, 'community', NOW()),

            -- Polish -> English
            (4, 5, 1, 'to visit', 'Visit a tourist place', 1, 'approved', NOW()),
            (5, 6, 1, 'little sadness', 'Small sadness, melancholy', 2, 'community', NOW()),

            -- German -> English
            (6, 8, 1, 'wanderlust', 'Desire to hike and travel', 1, 'approved', NOW()),
            (7, 9, 1, 'schadenfreude', 'Joy in others'' misfortune', 1, 'approved', NOW()),

            -- Spanish -> English
            (8, 10, 1, 'the time after eating', 'The time spent after a meal', 1, 'approved', NOW())
            ON CONFLICT (id) DO NOTHING;
        """)
    )
    await reset_sequence(db, "translations")


async def seed_sets(db: AsyncSession):
    """Seed study sets."""
    print("Seeding Sets...")
    await db.execute(
        text("""
            INSERT INTO sets (
                id, title, description, difficulty, source_lang_id, target_lang_id,
                creator_id, status, created_at
            ) VALUES
            (1, 'Advanced English Vocabulary', 'High-level words for fluency', 5, 1, 2, 1, 'approved', NOW()),
            (2, 'Polish Basics', 'Essential Polish phrases for beginners', 2, 2, 1, 2, 'community', NOW()),
            (3, 'German Idioms', 'Common German expressions', 4, 3, 1, 1, 'approved', NOW()),
            (4, 'Spanish Culture', 'Spanish cultural terms and expressions', 3, 4, 1, 2, 'community', NOW())
            ON CONFLICT (id) DO NOTHING;
        """)
    )
    await reset_sequence(db, "sets")


async def seed_set_items(db: AsyncSession):
    """Seed set membership (items in sets)."""
    print("Seeding Set Items...")
    await db.execute(
        text("""
            INSERT INTO set_items (set_id, item_id, sort_order, translation_id)
            VALUES
            (1, 1, 1, 1),
            (1, 2, 2, 2),
            (1, 3, 3, 3),
            (2, 5, 1, 4),
            (2, 6, 2, 5),
            (2, 7, 3, NULL),
            (3, 8, 1, 6),
            (3, 9, 2, 7),
            (4, 10, 1, 8),
            (4, 11, 2, NULL)
            ON CONFLICT (set_id, item_id) DO NOTHING;
        """)
    )


async def seed_user_set_library(db: AsyncSession):
    """Seed user's study set library."""
    print("Seeding User Set Library...")
    await db.execute(
        text("""
            INSERT INTO user_set_library (user_id, set_id, added_at, last_opened_at, is_pinned)
            VALUES
            (1, 1, NOW(), NOW(), true),
            (1, 3, NOW() - INTERVAL '1 day', NOW() - INTERVAL '1 day', false),
            (2, 2, NOW(), NULL, true),
            (3, 4, NOW() - INTERVAL '3 days', NOW() - INTERVAL '2 days', false),
            (4, 1, NOW(), NOW(), true)
            ON CONFLICT (user_id, set_id) DO NOTHING;
        """)
    )


async def seed_user_progress(db: AsyncSession):
    """Seed user learning progress for spaced repetition (SM-2)."""
    print("Seeding User Progress...")
    await db.execute(
        text("""
            INSERT INTO user_progress (
                user_id, item_id, ease_factor, interval, repetitions, lapsed_attempts,
                last_reviewed, next_review
            ) VALUES
            -- User 1 progress on set 1
            (1, 1, 2.5, 1, 0, 0, NULL, NOW() + INTERVAL '1 day'),
            (1, 2, 2.8, 3, 2, 0, NOW() - INTERVAL '2 days', NOW() + INTERVAL '1 day'),
            (1, 3, 2.3, 1, 1, 1, NOW() - INTERVAL '1 day', NOW()),

            -- User 2 progress on set 2
            (2, 5, 2.6, 2, 1, 0, NOW() - INTERVAL '1 day', NOW() + INTERVAL '2 days'),
            (2, 6, 2.5, 1, 0, 0, NULL, NOW()),

            -- User 4 progress on set 1
            (4, 1, 2.9, 4, 3, 0, NOW() - INTERVAL '4 days', NOW() + INTERVAL '3 days')
            ON CONFLICT (user_id, item_id) DO NOTHING;
        """)
    )


async def seed_study_sessions(db: AsyncSession):
    """Seed sample study sessions."""
    print("Seeding Study Sessions...")
    await db.execute(
        text("""
            INSERT INTO study_sessions (
                id, user_id, set_id, source_lang_id, started_at, ended_at, status,
                correct_count, incorrect_count, total_time_ms, items_reviewed
            ) VALUES
            (1, 1, 1, 2, NOW() - INTERVAL '2 days', NOW() - INTERVAL '2 days' + INTERVAL '15 minutes', 'completed', 8, 2, 900000, 10),
            (2, 2, 2, 1, NOW() - INTERVAL '1 day', NOW() - INTERVAL '1 day' + INTERVAL '10 minutes', 'completed', 5, 1, 600000, 6),
            (3, 1, 3, 1, NOW() - INTERVAL '3 hours', NULL, 'in_progress', 3, 1, 180000, 4),
            (4, 4, 1, 2, NOW() - INTERVAL '5 days', NOW() - INTERVAL '5 days' + INTERVAL '20 minutes', 'completed', 9, 1, 1200000, 10)
            ON CONFLICT (id) DO NOTHING;
        """)
    )
    await reset_sequence(db, "study_sessions", "id")


async def seed_study_reviews(db: AsyncSession):
    """Seed individual review records (answers)."""
    print("Seeding Study Reviews...")
    await db.execute(
        text("""
            INSERT INTO study_reviews (
                user_id, item_id, language_id, translation_id, set_id, session_id,
                was_correct, user_answer, response_time, ease_before, interval_before,
                ease_after, interval_after, reviewed_at
            ) VALUES
            -- Session 1 reviews (user 1, set 1, Polish)
            (1, 1, 2, 1, 1, 1, true, 'zbiég szczęśliwych okoliczności', 2500, 2.5, 0, 2.6, 1, NOW() - INTERVAL '2 days' + INTERVAL '1 minute'),
            (1, 2, 2, 2, 1, 1, true, 'ulotny', 3000, 2.5, 0, 2.6, 1, NOW() - INTERVAL '2 days' + INTERVAL '2 minutes'),
            (1, 3, 2, 3, 1, 1, false, 'wymowny', 4000, 2.5, 0, 2.3, 1, NOW() - INTERVAL '2 days' + INTERVAL '3 minutes'),
            (1, 1, 2, 1, 1, 1, true, 'zbiég', 2200, 2.6, 1, 2.8, 3, NOW() - INTERVAL '2 days' + INTERVAL '5 minutes'),

            -- Session 2 reviews (user 2, set 2, English)
            (2, 5, 1, 4, 2, 2, true, 'to visit', 1800, 2.5, 0, 2.6, 1, NOW() - INTERVAL '1 day' + INTERVAL '1 minute'),
            (2, 6, 1, 5, 2, 2, true, 'little sadness', 1500, 2.5, 0, 2.6, 1, NOW() - INTERVAL '1 day' + INTERVAL '2 minutes'),

            -- Session 3 ongoing reviews (user 1, set 3, English)
            (1, 8, 1, 6, 3, 3, true, 'wanderlust', 2800, 2.5, 0, 2.6, 1, NOW() - INTERVAL '3 hours' + INTERVAL '1 minute'),
            (1, 9, 1, 7, 3, 3, false, 'schadenfreude', 3500, 2.5, 0, 2.3, 1, NOW() - INTERVAL '3 hours' + INTERVAL '2 minutes')
            ON CONFLICT DO NOTHING;
        """)
    )
    await reset_sequence(db, "study_reviews", "id")


async def seed_user_daily_stats(db: AsyncSession):
    """Seed aggregated daily stats."""
    print("Seeding User Daily Stats...")
    await db.execute(
        text("""
            INSERT INTO user_daily_stats (
                user_id, language_id, stat_date, correct_count, incorrect_count,
                new_words_count, seconds_spent
            ) VALUES
            (1, 1, CURRENT_DATE - INTERVAL '5 days', 15, 3, 5, 1200.50),
            (1, 1, CURRENT_DATE - INTERVAL '4 days', 12, 2, 3, 950.75),
            (1, 1, CURRENT_DATE - INTERVAL '3 days', 18, 4, 6, 1450.25),
            (1, 2, CURRENT_DATE - INTERVAL '2 days', 10, 2, 4, 900.00),
            (1, 1, CURRENT_DATE - INTERVAL '1 day', 8, 1, 2, 750.50),
            (2, 2, CURRENT_DATE - INTERVAL '3 days', 6, 1, 3, 600.00),
            (2, 2, CURRENT_DATE - INTERVAL '1 day', 5, 2, 2, 500.25),
            (4, 1, CURRENT_DATE - INTERVAL '5 days', 20, 1, 8, 1500.00)
            ON CONFLICT (user_id, language_id, stat_date) DO NOTHING;
        """)
    )


async def seed_user_stats_total(db: AsyncSession):
    """Seed total aggregated stats per user per language."""
    print("Seeding User Stats Total...")
    await db.execute(
        text("""
            INSERT INTO user_stats_total (
                user_id, language_id, total_seconds, total_words, last_recalculated_at
            ) VALUES
            (1, 1, 5351.00, 20, NOW()),
            (1, 2, 900.00, 4, NOW()),
            (2, 2, 1100.25, 5, NOW()),
            (3, 5, 0, 0, NOW()),
            (4, 1, 1500.00, 8, NOW())
            ON CONFLICT (user_id, language_id) DO NOTHING;
        """)
    )


async def seed_database():
    """Main seed orchestration."""
    settings = get_settings()

    if settings.ENV not in ("development", "staging", "test"):
        print("Seeding is only allowed in development/staging/test environments!")
        return

    await init_async_session_factory(settings.DATABASE_URL)
    print(f"Seeding database: {settings.DATABASE_HOST} ({settings.ENV} mode)\n")

    try:
        async with get_session() as db:
            # Uncomment to clear before seeding
            # await clear_seed_data(db)

            # Seed in dependency order (no foreign key violations)
            await seed_languages(db)
            await seed_users(db)
            await seed_user_settings(db)
            await seed_user_languages(db)
            await seed_items(db)
            await seed_translations(db)
            await seed_sets(db)
            await seed_set_items(db)
            await seed_user_set_library(db)
            await seed_user_progress(db)
            await seed_study_sessions(db)
            await seed_study_reviews(db)
            await seed_user_daily_stats(db)
            await seed_user_stats_total(db)

            await db.commit()

        print("\n Database seeded successfully!")

    except Exception as e:
        print(f"\n Error seeding database: {e}")
        import traceback

        traceback.print_exc()
        raise
    finally:
        await shutdown_db_engine()


if __name__ == "__main__":
    asyncio.run(seed_database())
