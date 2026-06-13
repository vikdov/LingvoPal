"""
Production bootstrap — run ONCE after first deploy.

Seeds only the data the app cannot function without:
  - Languages (required for language selector, set creation)

Does NOT seed users, sets, items, or any dev fixtures.
Safe to re-run (INSERT ... ON CONFLICT DO NOTHING).

Usage:
    cd backend
    ENV=production uv run python scripts/bootstrap_prod.py
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import text

from app.core.config import get_settings
from app.database.session import get_session, init_async_session_factory, shutdown_db_engine

LANGUAGES = [
    (1, "en", "English"),
    (2, "pl", "Polish"),
    (3, "de", "German"),
    (4, "es", "Spanish"),
    (5, "fr", "French"),
    (6, "uk", "Ukrainian"),
]


async def bootstrap():
    settings = get_settings()

    print(f"Bootstrap target: {settings.DATABASE_HOST}/{settings.DATABASE_NAME} [{settings.ENV}]")
    print()

    confirmed = input("Type 'yes' to proceed: ").strip().lower()
    if confirmed != "yes":
        print("Aborted.")
        sys.exit(0)

    await init_async_session_factory(settings.DATABASE_URL)

    try:
        async with get_session() as db:
            await db.execute(
                text("""
                    INSERT INTO languages (id, code, name)
                    VALUES (:id, :code, :name)
                    ON CONFLICT (id) DO NOTHING
                """),
                [{"id": id_, "code": code, "name": name} for id_, code, name in LANGUAGES],
            )
            await db.execute(
                text("""
                    SELECT setval(
                        pg_get_serial_sequence('languages', 'id'),
                        COALESCE(MAX(id), 1),
                        MAX(id) IS NOT NULL
                    ) FROM languages;
                """)
            )
            await db.commit()

        count = len(LANGUAGES)
        print(f"Seeded {count} languages.")
        print()
        print("Next steps:")
        print("  1. Register your admin account via the app signup flow")
        print("  2. Create official sets and items through the app UI")

    finally:
        await shutdown_db_engine()


if __name__ == "__main__":
    asyncio.run(bootstrap())
