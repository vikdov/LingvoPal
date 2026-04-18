import sys
from pathlib import Path

# 1. Add 'backend' to sys.path so we can import 'app'
# This assumes the script is in LingvoPal/scripts/ and config is in LingvoPal/backend/app/
# This ensures that /app is added to the path regardless of
# whether you run from host or docker
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent  # This should resolve to /app in Docker
sys.path.append(str(project_root))
import asyncio
from sqlalchemy import text
from app.core.config import get_settings
from app.database.session import (
    init_async_session_factory,
    get_session,
    shutdown_db_engine,
)


async def seed_database():
    settings = get_settings()

    # Use the SYNC url because this script is likely running in a standard
    # synchronous context (psycopg2), not asyncpg.
    await init_async_session_factory(settings.DATABASE_URL)

    print(f"Connecting to: {settings.DATABASE_HOST} ({settings.ENV} mode)")
    try:
        async with get_session() as db:
            print("🌱 Seeding Languages...")
            await db.execute(
                text("""
            INSERT INTO languages (id, code, name) VALUES 
            (1, 'en', 'English'),
            (2, 'pl', 'Polish'),
            (3, 'ge', 'German'),
            (4, 'es', 'Spanish'),
            (5, 'uk', 'Ukrainian')

            ON CONFLICT (id) DO NOTHING;
        """)
            )
            # Reset the sequence so future inserts work correctly
            await db.execute(
                text(
                    "SELECT setval(pg_get_serial_sequence('languages', 'id'), coalesce(max(id), 1), max(id) IS NOT null) FROM languages;"
                )
            )

            print("👤 Seeding Users...")
            # Note: In a real app, generate the password_hash using a library like Passlib or Werkzeug.
            dummy_hash = "$2a$12$zAbZ8jb6VIz9QfzhgqpLMeHw2EoLDllm4jXdhHIk8pBnT1UsOvFDe"  # "password"
            await db.execute(
                text("""
            INSERT INTO users (id, user_status, email, email_verified, password_hash, username) VALUES 
            (1, 'admin', 'admin@lingvopal.com', true, :hash, 'admin_user'),
            (2, 'user', 'jankowalski@example.com', true, :hash, 'jan_k')
            ON CONFLICT (id) DO NOTHING;
        """),
                {"hash": dummy_hash},
            )
            await db.execute(
                text(
                    "SELECT setval(pg_get_serial_sequence('users', 'id'), coalesce(max(id), 1), max(id) IS NOT null) FROM users;"
                )
            )

            print("⚙️ Seeding User Settings...")
            await db.execute(
                text("""
                    INSERT INTO user_settings (
                        user_id, native_lang_id, interface_lang_id, learning_intensity,
                        evaluation_mode, show_hints_on_fails, daily_study_goal,
                        reminder_time, streak_reminders_enabled,
                        show_translations, show_images, show_synonyms,
                        show_part_of_speech, auto_play_audio,
                        new_items_per_day_limit, new_items_per_session,
                        retention_priority, max_review_load_per_day,
                        updated_at, created_at
                    ) VALUES
                    -- Admin (English native)
                    (1, 1, 1, 'balanced', 'normal', true, 20,
                     NULL, true,
                     true, true, true,
                     true, true,
                     10, 5,
                     'long_term_mastery', NULL,
                     NULL, NOW()),
                    -- Regular user (Polish native)
                    (2, 2, 2, 'light', 'forgiving', true, 10,
                     NULL, true,
                     true, true, false,
                     true, false,
                     5, 5,
                     'balanced', NULL,
                     NULL, NOW())
                    ON CONFLICT (user_id) DO NOTHING;
                """)
            )

            print("📚 Seeding Vocabulary Items...")
            await db.execute(
                text("""
                    INSERT INTO items (
                        id, language_id, term, difficulty, context,
                        image_url, audio_url, part_of_speech, lemma,
                        creator_id, verified_by, status,
                        deleted_at, updated_at, created_at
                    ) VALUES
                    -- English items
                    (1, 1, 'Apple', 1, 1, NULL, NULL, 'noun', 'apple', 1, NULL, 'official', NULL, NULL, NOW()),
                    (2, 1, 'Run', 2, 1, NULL, NULL, 'verb', 'run', 1, NULL, 'official', NULL, NULL, NOW()),
                    (3, 1, 'Beautiful', 2, 3, NULL, NULL, 'adjective', 'beautiful', 1, NULL, 'official', NULL, NULL, NOW()),
                    -- Polish items
                    (4, 2, 'Jabłko', 1, NULL, NULL, NULL, 'noun', 'jabłko', 1, NULL, 'official', NULL, NULL, NOW()),
                    (5, 2, 'Biegać', 2, NULL, NULL, NULL, 'verb', 'biegać', 1, NULL, 'official', NULL, NULL, NOW()),
                    (6, 2, 'Piękny', 3, NULL, NULL, NULL, 'adjective', 'piękny', 1, NULL, 'official', NULL, NULL, NOW()),
                    -- Extra English items (used for synonyms demo)
                    (7, 1, 'Pretty', 3, NULL, NULL, NULL, 'adjective', 'pretty', 1, NULL, 'official', NULL, NULL, NOW()),
                    (8, 1, 'Car', 2, NULL, NULL, NULL, 'noun', 'car', 1, NULL, 'official', NULL, NULL, NOW()),
                    (9, 1, 'Automobile', 4, NULL, NULL, NULL, 'noun', 'automobile', 1, NULL, 'official', NULL, NULL, NOW())
                    ON CONFLICT (id) DO NOTHING;
                """)
            )
            await db.execute(
                text(
                    "SELECT setval(pg_get_serial_sequence('items', 'id'), coalesce(max(id), 1), max(id) IS NOT null) FROM items;"
                )
            )

            print("🔄 Seeding Translations...")
            await db.execute(
                text("""
            INSERT INTO translations (id, item_id, language_id, term_trans, creator_id, status) VALUES 
            (1, 1, 2, 'Jabłko', 1, 'official'),
            (2, 2, 2, 'Biegać', 1, 'official'),
            (3, 3, 2, 'Piękny', 1, 'official'),
            (4, 4, 1, 'Apple', 1, 'official'),
            (5, 5, 1, 'Run', 1, 'official'),
            (6, 6, 1, 'Beautiful', 1, 'official')
            ON CONFLICT (id) DO NOTHING;
        """)
            )
            await db.execute(
                text(
                    "SELECT setval(pg_get_serial_sequence('translations', 'id'), coalesce(max(id), 1), max(id) IS NOT null) FROM translations;"
                )
            )

            print("🗂️ Seeding Sets...")
            await db.execute(
                text("""
            INSERT INTO sets (id, title, description, difficulty, source_lang_id, target_lang_id, creator_id, status) VALUES 
            (1, 'Basic English for Polish Speakers', 'A starter pack for learning English.', 1, 2, 1, 1, 'official'),
            (2, 'Podstawy Polskiego', 'Basic Polish vocabulary for English speakers.', 1, 1, 2, 1, 'official')
            ON CONFLICT (id) DO NOTHING;
        """)
            )
            await db.execute(
                text(
                    "SELECT setval(pg_get_serial_sequence('sets', 'id'), coalesce(max(id), 1), max(id) IS NOT null) FROM sets;"
                )
            )

            print("🔗 Seeding Set Items...")
            await db.execute(
                text("""
            INSERT INTO set_items (set_id, item_id, sort_order, translation_id) VALUES 
            -- English items in Set 1 (for Polish speakers to learn)
            (1, 1, 1, 1),
            (1, 2, 2, 2),
            (1, 3, 3, 3),
            -- Polish items in Set 2 (for English speakers to learn)
            (2, 4, 1, 4),
            (2, 5, 2, 5),
            (2, 6, 3, 6)
            ON CONFLICT (set_id, item_id) DO NOTHING;
        """)
            )

        print("✅ Database successfully seeded!")
    except Exception as e:
        print(f"❌ Error seeding database: {e}")
    finally:
        await shutdown_db_engine()


if __name__ == "__main__":
    asyncio.run(seed_database())
