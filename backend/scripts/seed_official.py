"""
Seed official .lpset sets into the database.

Reads every *.lpset file from content/official/ and imports it with
ContentStatus.OFFICIAL. Safe to re-run — existing sets (matched by title +
source_lang_id) are skipped.

Usage:
    cd backend
    uv run python scripts/seed_official.py

Required env: full production settings (DATABASE_* etc.) or a local .env.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select

from app.core.config import get_settings
from app.database.session import (
    get_session,
    init_async_session_factory,
    shutdown_db_engine,
)
from app.models.enums import ContentStatus
from app.models.language import Language
from app.models.set import Set
from app.services.lpset_import_service import LpsetImportError, LpsetImportService

CONTENT_DIR = Path(__file__).resolve().parents[2] / "content" / "official"


async def _set_exists(db, title: str, source_lang_id: int) -> bool:
    result = await db.execute(
        select(Set.id).where(
            Set.title == title,
            Set.source_lang_id == source_lang_id,
            Set.deleted_at.is_(None),
        )
    )
    return result.scalar_one_or_none() is not None


async def _resolve_source_lang_id(db, code: str) -> int | None:
    result = await db.execute(select(Language.id).where(Language.code == code))
    return result.scalar_one_or_none()


async def seed_official_sets() -> None:
    if not CONTENT_DIR.exists():
        print(f"No content directory found at {CONTENT_DIR}. Nothing to seed.")
        return

    lpset_files = sorted(CONTENT_DIR.glob("*.lpset"))
    if not lpset_files:
        print(f"No .lpset files found in {CONTENT_DIR}. Nothing to seed.")
        return

    settings = get_settings()
    await init_async_session_factory(settings.DATABASE_URL)

    print(f"Seeding {len(lpset_files)} official set(s) into {settings.DATABASE_HOST}...\n")

    try:
        async with get_session() as db:
            svc = LpsetImportService(db)

            for lpset_file in lpset_files:
                data = lpset_file.read_bytes()

                # Peek at manifest to check for duplicates before importing
                import io, json, zipfile
                try:
                    with zipfile.ZipFile(io.BytesIO(data)) as zf:
                        manifest_raw = json.loads(zf.read("manifest.json"))
                    title = manifest_raw.get("set", {}).get("title", "")
                    source_lang_code = manifest_raw.get("set", {}).get("source_lang", "")
                except Exception:
                    print(f"  SKIP {lpset_file.name} — cannot read manifest")
                    continue

                source_lang_id = await _resolve_source_lang_id(db, source_lang_code)
                if source_lang_id and await _set_exists(db, title, source_lang_id):
                    print(f"  SKIP {lpset_file.name} — '{title}' already exists")
                    continue

                try:
                    result = await svc.import_lpset(
                        data,
                        user_id=None,
                        status=ContentStatus.OFFICIAL,
                    )
                    print(
                        f"  OK   {lpset_file.name} — "
                        f"{result['item_count']} new items, "
                        f"{result['skipped_count']} reused, "
                        f"{result['media_uploaded']} media files uploaded"
                    )
                except LpsetImportError as exc:
                    print(f"  FAIL {lpset_file.name} — {exc}")
                    raise

            await db.commit()

    finally:
        await shutdown_db_engine()

    print("\nDone.")


if __name__ == "__main__":
    asyncio.run(seed_official_sets())
