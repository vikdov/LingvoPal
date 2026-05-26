"""
.lpset bundle import service.

Parses a .lpset ZIP file (manifest.json + media), uploads media to S3,
and creates a set + items + translations in a single transaction.

Deduplicates items via content_hash — existing items are reused, not duplicated.
"""

import io
import json
import logging
import mimetypes
import zipfile
from pathlib import PurePosixPath

from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import ContentStatus
from app.models.language import Language
from app.repositories.item_repo import ItemRepository
from app.repositories.set_repo import SetRepository
from app.schemas.lpset import LpsetManifest
from app.services.hashing import compute_item_content_hash
from app.services.storage import StorageService

logger = logging.getLogger(__name__)

_IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
_AUDIO_EXTS = {".mp3", ".ogg", ".wav", ".m4a", ".opus"}


def _mime(path: str) -> tuple[str, str]:
    """Return (content_type, ext) for a media path."""
    ext = PurePosixPath(path).suffix.lower()
    ct = mimetypes.types_map.get(ext) or "application/octet-stream"
    return ct, ext.lstrip(".")


class LpsetImportError(Exception):
    pass


class LpsetImportService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._items = ItemRepository(db)
        self._sets = SetRepository(db)
        self._storage = StorageService()

    async def import_lpset(
        self,
        file_bytes: bytes,
        user_id: int | None,
        status: ContentStatus = ContentStatus.DRAFT,
    ) -> dict:
        """
        Import a .lpset bundle.

        Args:
            file_bytes: Raw ZIP bytes of the .lpset file.
            user_id: Owner of the created set. None = system/official content.
            status: ContentStatus applied to set, items, and translations.

        Returns:
            dict with set_id, title, item_count, skipped_count, media_uploaded.
        """
        try:
            zf = zipfile.ZipFile(io.BytesIO(file_bytes))
        except zipfile.BadZipFile as exc:
            raise LpsetImportError("Not a valid .lpset file (bad ZIP).") from exc

        with zf:
            manifest = self._parse_manifest(zf)
            lang_map = await self._resolve_languages(manifest)
            source_lang_id = lang_map[manifest.set.source_lang]
            target_lang_id = lang_map.get(manifest.set.target_lang) if manifest.set.target_lang else None

            # Dedup: compute hashes for all items, bulk-lookup existing
            hashes = [
                compute_item_content_hash(source_lang_id, item.term, item.context)
                for item in manifest.items
            ]
            existing = await self._items.find_by_content_hashes(hashes)

            # Check for an identical existing set (including soft-deleted)
            db_set = await self._find_identical_set(
                manifest.set.title, source_lang_id, target_lang_id, hashes
            )
            if db_set is not None:
                if db_set.deleted_at is not None:
                    await self._sets.restore(db_set.id)
                n_items = len(manifest.items)
                return {
                    "set_id": db_set.id,
                    "title": db_set.title,
                    "item_count": 0,
                    "skipped_count": n_items,
                    "media_uploaded": 0,
                }

            # Create set (no library entry for system content)
            db_set = await self._sets.create(
                title=manifest.set.title,
                description=manifest.set.description,
                difficulty=manifest.set.difficulty,
                source_lang_id=source_lang_id,
                target_lang_id=target_lang_id,
                creator_id=user_id,
                status=status,
            )
            if user_id is not None:
                await self._sets.save_to_library(user_id, db_set.id)

            item_count = 0
            skipped_count = 0
            media_uploaded = 0

            for sort_order, (lpset_item, content_hash) in enumerate(
                zip(manifest.items, hashes)
            ):
                if content_hash in existing:
                    db_item = existing[content_hash]
                    skipped_count += 1
                else:
                    image_url, n_img = await self._upload_media(
                        zf, lpset_item.image, _IMAGE_EXTS
                    )
                    audio_url, n_audio = await self._upload_media(
                        zf, lpset_item.audio, _AUDIO_EXTS
                    )
                    ctx_audio_url, n_ctx = await self._upload_media(
                        zf, lpset_item.context_audio, _AUDIO_EXTS
                    )
                    media_uploaded += n_img + n_audio + n_ctx

                    db_item = await self._items.create(
                        term=lpset_item.term,
                        language_id=source_lang_id,
                        creator_id=user_id,
                        context=lpset_item.context,
                        difficulty=lpset_item.difficulty,
                        part_of_speech=lpset_item.part_of_speech,
                        lemma=lpset_item.lemma,
                        image_url=image_url,
                        audio_url=audio_url,
                        context_audio_url=ctx_audio_url,
                        status=status,
                        content_hash=content_hash,
                    )
                    item_count += 1

                # Pin the first matching translation for this set's target lang
                translation_id: int | None = None
                for t in lpset_item.translations:
                    t_lang_id = lang_map.get(t.lang)
                    if t_lang_id is None:
                        continue
                    if content_hash in existing:
                        db_trans = await self._items.get_item_translation_by_language(
                            db_item.id, t_lang_id
                        )
                        if db_trans is None:
                            db_trans = await self._items.create_translation(
                                item_id=db_item.id,
                                language_id=t_lang_id,
                                term_trans=t.term_trans,
                                context_trans=t.context_trans,
                                creator_id=user_id,
                                status=status,
                            )
                    else:
                        db_trans = await self._items.create_translation(
                            item_id=db_item.id,
                            language_id=t_lang_id,
                            term_trans=t.term_trans,
                            context_trans=t.context_trans,
                            creator_id=user_id,
                            status=status,
                        )
                    if target_lang_id and t_lang_id == target_lang_id and translation_id is None:
                        translation_id = db_trans.id

                await self._items.add_to_set(
                    db_set.id, db_item.id, sort_order, translation_id
                )

        return {
            "set_id": db_set.id,
            "title": db_set.title,
            "item_count": item_count,
            "skipped_count": skipped_count,
            "media_uploaded": media_uploaded,
        }

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    async def _find_identical_set(
        self,
        title: str,
        source_lang_id: int,
        target_lang_id: int | None,
        hashes: list[str],
    ):
        """Return existing Set (active or deleted) if title + langs + item hashes match exactly."""
        candidates = await self._sets.find_by_title_and_langs(
            title, source_lang_id, target_lang_id
        )
        for candidate in candidates:
            candidate_hashes = await self._sets.get_ordered_item_hashes(candidate.id)
            if candidate_hashes == hashes:
                return candidate
        return None

    def _parse_manifest(self, zf: zipfile.ZipFile) -> LpsetManifest:
        try:
            raw = zf.read("manifest.json")
        except KeyError as exc:
            raise LpsetImportError("manifest.json not found in bundle.") from exc
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise LpsetImportError(f"manifest.json is not valid JSON: {exc}") from exc
        try:
            return LpsetManifest.model_validate(data)
        except ValidationError as exc:
            raise LpsetImportError(f"manifest.json validation failed:\n{exc}") from exc

    async def _resolve_languages(self, manifest: LpsetManifest) -> dict[str, int]:
        """Resolve ISO codes used in the manifest to DB language IDs."""
        codes: set[str] = {manifest.set.source_lang}
        if manifest.set.target_lang:
            codes.add(manifest.set.target_lang)
        for item in manifest.items:
            for t in item.translations:
                codes.add(t.lang)

        result = await self._db.execute(
            select(Language.code, Language.id).where(Language.code.in_(codes))
        )
        lang_map: dict[str, int] = {row.code: row.id for row in result.fetchall()}

        missing = codes - lang_map.keys()
        if missing:
            raise LpsetImportError(
                f"Unknown language code(s) in bundle: {', '.join(sorted(missing))}. "
                "Run bootstrap_prod.py to seed languages first."
            )
        return lang_map

    async def _upload_media(
        self,
        zf: zipfile.ZipFile,
        path: str | None,
        allowed_exts: set[str],
    ) -> tuple[str | None, int]:
        """Read a media file from ZIP and upload to S3. Returns (url, count)."""
        if not path:
            return None, 0
        ext = PurePosixPath(path).suffix.lower()
        if ext not in allowed_exts:
            logger.warning("Skipping media %r — extension %r not allowed", path, ext)
            return None, 0
        try:
            data = zf.read(path)
        except KeyError:
            logger.warning("Media file %r listed in manifest but missing from ZIP", path)
            return None, 0
        content_type, ext_str = _mime(path)
        if ext in _IMAGE_EXTS:
            url = await self._storage.upload_image(data, content_type, ext_str)
        else:
            url = await self._storage.upload_audio(data, content_type, ext_str)
        return url, 1
