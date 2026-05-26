"""
.lpset bundle export service.

Reads a set + items + translations from the DB, downloads media from S3,
and packs everything into an in-memory .lpset ZIP file.
"""

import io
import json
import logging
import zipfile
from pathlib import PurePosixPath

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.language import Language
from app.repositories.item_repo import ItemRepository
from app.repositories.set_repo import SetRepository
from app.schemas.lpset import LPSET_VERSION
from app.services.storage import StorageService

logger = logging.getLogger(__name__)

_SAFE_CHARS = frozenset(
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"
)


def _safe_filename(name: str) -> str:
    return "".join(c if c in _SAFE_CHARS else "_" for c in name)


class LpsetExportError(Exception):
    pass


class LpsetExportService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._items = ItemRepository(db)
        self._sets = SetRepository(db)
        self._storage = StorageService()

    async def export_set(self, set_id: int) -> tuple[bytes, str]:
        """
        Export a set as a .lpset ZIP bundle.

        Returns:
            (zip_bytes, filename)
        Raises:
            LpsetExportError if set not found.
        """
        db_set = await self._sets.get_by_id(set_id)
        if db_set is None:
            raise LpsetExportError(f"Set {set_id} not found.")

        lang_ids: set[int] = {db_set.source_lang_id}
        if db_set.target_lang_id:
            lang_ids.add(db_set.target_lang_id)
        lang_id_to_code = await self._resolve_lang_codes(lang_ids)

        source_lang_code = lang_id_to_code.get(db_set.source_lang_id, "xx")
        target_lang_code = (
            lang_id_to_code.get(db_set.target_lang_id)
            if db_set.target_lang_id
            else None
        )

        # Load all items (up to 500, matching manifest limit)
        set_items = await self._items.get_set_items(set_id, limit=500)

        # Collect translation language IDs not yet resolved
        extra_ids: set[int] = set()
        for si in set_items:
            for t in si.item.translations:
                if t.language_id not in lang_id_to_code:
                    extra_ids.add(t.language_id)
        if extra_ids:
            lang_id_to_code.update(await self._resolve_lang_codes(extra_ids))

        buf = io.BytesIO()
        with zipfile.ZipFile(buf, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
            manifest_items = []

            for si in set_items:
                item = si.item
                item_data: dict = {"term": item.term}

                if item.context:
                    item_data["context"] = item.context
                if item.part_of_speech:
                    item_data["part_of_speech"] = item.part_of_speech.value
                if item.difficulty:
                    item_data["difficulty"] = item.difficulty
                if item.lemma:
                    item_data["lemma"] = item.lemma

                audio_path = await self._embed_media(zf, item.audio_url, "audio")
                if audio_path:
                    item_data["audio"] = audio_path

                ctx_audio_path = await self._embed_media(zf, item.context_audio_url, "audio")
                if ctx_audio_path:
                    item_data["context_audio"] = ctx_audio_path

                image_path = await self._embed_media(zf, item.image_url, "images")
                if image_path:
                    item_data["image"] = image_path

                translations = []
                for t in item.translations:
                    lang_code = lang_id_to_code.get(t.language_id)
                    if lang_code is None:
                        continue
                    td: dict = {"lang": lang_code, "term_trans": t.term_trans}
                    if t.context_trans:
                        td["context_trans"] = t.context_trans
                    translations.append(td)
                if translations:
                    item_data["translations"] = translations

                manifest_items.append(item_data)

            set_data: dict = {
                "title": db_set.title,
                "source_lang": source_lang_code,
            }
            if db_set.description:
                set_data["description"] = db_set.description
            if target_lang_code:
                set_data["target_lang"] = target_lang_code
            if db_set.difficulty:
                set_data["difficulty"] = db_set.difficulty

            manifest = {
                "version": LPSET_VERSION,
                "set": set_data,
                "items": manifest_items,
            }
            zf.writestr("manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2))

        filename = f"{_safe_filename(db_set.title)}.lpset"
        return buf.getvalue(), filename

    async def _resolve_lang_codes(self, ids: set[int]) -> dict[int, str]:
        if not ids:
            return {}
        result = await self._db.execute(
            select(Language.id, Language.code).where(Language.id.in_(ids))
        )
        return {row.id: row.code for row in result.fetchall()}

    async def _embed_media(
        self,
        zf: zipfile.ZipFile,
        url: str | None,
        folder: str,
    ) -> str | None:
        """Download media from S3 and write to ZIP. Returns ZIP-relative path or None."""
        if not url:
            return None
        data = await self._storage.get_object_by_url(url)
        if data is None:
            logger.warning("Media not found in S3: %s", url)
            return None
        filename = PurePosixPath(url).name
        zip_path = f"{folder}/{filename}"
        try:
            zf.getinfo(zip_path)
            return zip_path
        except KeyError:
            pass
        zf.writestr(zip_path, data)
        return zip_path
