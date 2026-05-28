"""
Anki import orchestration.

Uses repositories directly (not ItemService/SetService) to create all records
in a single transaction — avoids per-item commits that would kill performance
on large decks.

Two-phase flow:
  store_and_build_preview()  — saves parsed cards + .apkg bytes to temp storage
  confirm_import()           — loads from temp, bulk-creates set/items, uploads media
"""

import json
import logging
import os
import uuid
import zipfile

import redis.asyncio as aioredis
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ResourceNotFoundError
from app.models.enums import ContentStatus, PartOfSpeech
from app.repositories.item_repo import ItemRepository
from app.repositories.set_repo import SetRepository
from app.schemas.anki_import import (
    AnkiConfirmRequest,
    AnkiImportResponse,
    AnkiPreviewResponse,
    DetectedFieldInfo,
    FieldMappingSchema,
)
from app.services.anki_parser import (
    AnkiParseResult,
    ParsedCard,
    extract_audio_filename,
    extract_image_filename,
)
from app.services.hashing import compute_item_content_hash
from app.services.morphology import find_surface_form, wrap_surface_form
from app.services.storage import StorageService

logger = logging.getLogger(__name__)

IMPORT_KEY_PREFIX = "anki_import:"
IMPORT_TTL_SECONDS = 1800  # 30 min

_APKG_TMP_DIR = "/tmp"  # nosec B108

# Map common Anki POS strings (lower-cased) to LingvoPal enum values
_POS_MAP: dict[str, PartOfSpeech] = {
    "noun": PartOfSpeech.NOUN,
    "n": PartOfSpeech.NOUN,
    "verb": PartOfSpeech.VERB,
    "v": PartOfSpeech.VERB,
    "adjective": PartOfSpeech.ADJECTIVE,
    "adj": PartOfSpeech.ADJECTIVE,
    "adverb": PartOfSpeech.ADVERB,
    "adv": PartOfSpeech.ADVERB,
    "pronoun": PartOfSpeech.PRONOUN,
    "pron": PartOfSpeech.PRONOUN,
    "preposition": PartOfSpeech.PREPOSITION,
    "prep": PartOfSpeech.PREPOSITION,
    "conjunction": PartOfSpeech.CONJUNCTION,
    "conj": PartOfSpeech.CONJUNCTION,
    "interjection": PartOfSpeech.INTERJECTION,
    "interj": PartOfSpeech.INTERJECTION,
    "article": PartOfSpeech.ARTICLE,
    "art": PartOfSpeech.ARTICLE,
    "other": PartOfSpeech.OTHER,
}

_IMAGE_MIMES: dict[str, str] = {
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "png": "image/png",
    "webp": "image/webp",
    "gif": "image/gif",
}
_AUDIO_MIMES: dict[str, str] = {
    "mp3": "audio/mpeg",
    "ogg": "audio/ogg",
    "wav": "audio/wav",
    "m4a": "audio/mp4",
    "aac": "audio/aac",
    "webm": "audio/webm",
    "flac": "audio/flac",
}


def _parse_pos(raw: str) -> PartOfSpeech | None:
    return _POS_MAP.get(raw.lower().strip())


def _apkg_tmp_path(token: str) -> str:
    return os.path.join(_APKG_TMP_DIR, f"anki_import_{token}.apkg")


class AnkiImportService:
    def __init__(
        self,
        session: AsyncSession,
        redis: aioredis.Redis,
        storage: StorageService,
    ) -> None:
        self._session = session
        self._redis = redis
        self._storage = storage
        self._sets = SetRepository(session)
        self._items = ItemRepository(session)

    # ── Phase 1: Preview ─────────────────────────────────────────────────────

    async def store_and_build_preview(
        self, file_bytes: bytes, result: AnkiParseResult
    ) -> AnkiPreviewResponse:
        token = str(uuid.uuid4())

        # Persist parsed cards (text) in Redis
        key = f"{IMPORT_KEY_PREFIX}{token}"
        payload = json.dumps(
            {
                "deck_name": result.root_deck_name,
                "cards": [
                    {"fields": c.fields, "raw_fields": c.raw_fields, "tags": c.tags}
                    for c in result.cards
                ],
            }
        )
        await self._redis.set(key, payload, ex=IMPORT_TTL_SECONDS)

        # Persist .apkg bytes to disk for media extraction during confirm
        apkg_path = _apkg_tmp_path(token)
        try:
            with open(apkg_path, "wb") as fh:
                fh.write(file_bytes)
        except OSError as exc:
            logger.warning("Could not save .apkg tmp file: %s", exc)

        m = result.suggested_mapping
        return AnkiPreviewResponse(
            import_token=token,
            deck_name=result.root_deck_name,
            card_count=result.card_count,
            media_size_bytes=result.media_size_bytes,
            detected_fields=[
                DetectedFieldInfo(
                    name=f.name,
                    sample=f.sample,
                    has_image=f.has_image,
                    has_audio=f.has_audio,
                )
                for f in result.detected_fields
            ],
            suggested_mapping=FieldMappingSchema(
                term_field=m.term_field,
                translation_field=m.translation_field,
                context_field=m.context_field,
                context_trans_field=m.context_trans_field,
                lemma_field=m.lemma_field,
                part_of_speech_field=m.part_of_speech_field,
                image_field=m.image_field,
                audio_field=m.audio_field,
            ),
        )

    # ── Phase 2: Confirm ─────────────────────────────────────────────────────

    async def confirm_import(self, user_id: int, request: AnkiConfirmRequest) -> AnkiImportResponse:
        key = f"{IMPORT_KEY_PREFIX}{request.import_token}"
        raw = await self._redis.get(key)
        if raw is None:
            raise ResourceNotFoundError("Import session", request.import_token)

        stored = json.loads(raw)
        title = (request.title or stored.get("deck_name") or "Imported Deck").strip()
        cards = [
            ParsedCard(
                fields=c["fields"],
                raw_fields=c["raw_fields"],
                tags=c["tags"],
            )
            for c in stored["cards"]
        ]

        # Load media lookup from .apkg file if available
        media_lookup: dict[str, str] = {}  # anki_filename → numeric_id_in_zip
        apkg_archive: zipfile.ZipFile | None = None
        apkg_path = _apkg_tmp_path(request.import_token)
        if os.path.exists(apkg_path):
            try:
                apkg_archive = zipfile.ZipFile(apkg_path)
                media_lookup = _build_media_lookup(apkg_archive)
            except Exception as exc:
                logger.warning("Could not open .apkg for media extraction: %s", exc)
                apkg_archive = None

        try:
            new_set = await self._sets.create(
                title=title,
                description=None,
                difficulty=None,
                source_lang_id=request.source_lang_id,
                target_lang_id=request.target_lang_id,
                creator_id=user_id,
                status=ContentStatus.DRAFT,
            )
            await self._sets.save_to_library(user_id, new_set.id)

            item_count, skipped_count, reused_count, no_gap_count = await self._bulk_create_items(
                user_id=user_id,
                set_id=new_set.id,
                cards=cards,
                mapping=request.field_mapping,
                source_lang_id=request.source_lang_id,
                target_lang_id=request.target_lang_id,
                apkg_archive=apkg_archive,
                media_lookup=media_lookup,
            )

            await self._session.commit()
        finally:
            if apkg_archive is not None:
                apkg_archive.close()
            # Clean up temp files
            await self._redis.delete(key)
            try:
                os.unlink(apkg_path)
            except OSError:
                pass

        return AnkiImportResponse(
            set_id=new_set.id,
            title=title,
            item_count=item_count,
            skipped_count=skipped_count,
            reused_count=reused_count,
            no_gap_count=no_gap_count,
        )

    # ── Bulk item creation ────────────────────────────────────────────────────

    async def _bulk_create_items(
        self,
        *,
        user_id: int,
        set_id: int,
        cards: list[ParsedCard],
        mapping: FieldMappingSchema,
        source_lang_id: int,
        target_lang_id: int | None,
        apkg_archive: zipfile.ZipFile | None,
        media_lookup: dict[str, str],
    ) -> tuple[int, int, int, int]:
        item_count = 0
        skipped_count = 0
        reused_count = 0
        no_gap_count = 0

        # ── Phase 0: parse all cards + compute hashes (no DB) ────────────────
        CardData = dict  # just for readability below
        valid_cards: list[CardData] = []

        for sort_order, card in enumerate(cards):
            term = card.fields.get(mapping.term_field, "").strip()
            if not term:
                skipped_count += 1
                continue

            context = (
                card.fields.get(mapping.context_field, "").strip() or None
                if mapping.context_field
                else None
            )
            truncated_context = context[:1000] if context else None

            # Normalise term to exact surface form used in sentence.
            # Gap is mandatory: skip cards where term not findable in context.
            raw_term = term[:500]
            if truncated_context:
                surface = find_surface_form(raw_term, truncated_context)
                if not surface:
                    no_gap_count += 1
                    continue
                truncated_term = surface
            else:
                no_gap_count += 1
                continue

            valid_cards.append(
                {
                    "sort_order": sort_order,
                    "card": card,
                    "term": truncated_term,
                    "context": truncated_context,
                    "translation": (
                        card.fields.get(mapping.translation_field, "").strip()
                        if mapping.translation_field
                        else ""
                    ),
                    "context_trans": (
                        card.fields.get(mapping.context_trans_field, "").strip() or None
                        if mapping.context_trans_field
                        else None
                    ),
                    "lemma": (
                        card.fields.get(mapping.lemma_field, "").strip()[:500] or None
                        if mapping.lemma_field
                        else None
                    ),
                    "pos": (
                        _parse_pos(card.fields.get(mapping.part_of_speech_field, "").strip())
                        if mapping.part_of_speech_field
                        else None
                    ),
                    "hash": compute_item_content_hash(
                        source_lang_id, truncated_term, truncated_context
                    ),
                }
            )

        # ── Phase 1: one bulk lookup for all hashes ───────────────────────────
        all_hashes = {d["hash"] for d in valid_cards}
        existing_by_hash = await self._items.find_by_content_hashes(all_hashes)

        # ── Phase 2: per card — reuse or create ───────────────────────────────
        for data in valid_cards:
            h = data["hash"]

            if h in existing_by_hash:
                # REUSE PATH: item already exists, just link it
                item = existing_by_hash[h]
                if await self._items.set_item_exists(set_id, item.id):
                    # intra-batch duplicate (same card appears twice in deck)
                    skipped_count += 1
                    continue
                translation_id = await self._resolve_translation(
                    item.id, target_lang_id, data, user_id
                )
                await self._items.add_to_set(set_id, item.id, data["sort_order"], translation_id)
                reused_count += 1

            else:
                # NEW PATH: upload media, create item, create translation
                card = data["card"]
                image_url = await self._upload_image(
                    card.raw_fields.get(mapping.image_field, "") if mapping.image_field else "",
                    apkg_archive,
                    media_lookup,
                )
                audio_url = await self._upload_audio(
                    card.raw_fields.get(mapping.audio_field, "") if mapping.audio_field else "",
                    apkg_archive,
                    media_lookup,
                )
                try:
                    async with self._session.begin_nested():  # savepoint
                        item = await self._items.create(
                            term=data["term"],
                            language_id=source_lang_id,
                            creator_id=user_id,
                            context=data["context"],
                            difficulty=None,
                            part_of_speech=data["pos"],
                            lemma=data["lemma"],
                            image_url=image_url,
                            audio_url=audio_url,
                            status=ContentStatus.DRAFT,
                            content_hash=h,
                        )
                except IntegrityError:
                    # Concurrent import won the race on this hash — reuse it
                    item = await self._items.find_by_content_hash(h)
                    if item is None:
                        raise
                    existing_by_hash[h] = item
                    translation_id = await self._resolve_translation(
                        item.id, target_lang_id, data, user_id
                    )
                    await self._items.add_to_set(
                        set_id, item.id, data["sort_order"], translation_id
                    )
                    reused_count += 1
                    item_count += 1
                    continue

                existing_by_hash[h] = item  # register for intra-batch dedup
                translation_id = await self._resolve_translation(
                    item.id, target_lang_id, data, user_id
                )
                await self._items.add_to_set(set_id, item.id, data["sort_order"], translation_id)

            item_count += 1

        return item_count, skipped_count, reused_count, no_gap_count

    async def _resolve_translation(
        self,
        item_id: int,
        target_lang_id: int | None,
        data: dict,
        user_id: int,
    ) -> int | None:
        """Return translation_id to attach to set_items. Reuse existing or create."""
        if not target_lang_id or not data["translation"]:
            return None
        existing = await self._items.get_item_translation_by_language(item_id, target_lang_id)
        if existing:
            return existing.id
        term_trans = data["translation"][:500]
        raw_ctx = data["context_trans"][:1000] if data["context_trans"] else None
        context_trans = wrap_surface_form(term_trans, raw_ctx) if raw_ctx else None
        trans = await self._items.create_translation(
            item_id=item_id,
            language_id=target_lang_id,
            term_trans=term_trans,
            context_trans=context_trans,
            creator_id=user_id,
            status=ContentStatus.DRAFT,
        )
        return trans.id

    # ── Media helpers ─────────────────────────────────────────────────────────

    async def _upload_image(
        self,
        raw_value: str,
        archive: zipfile.ZipFile | None,
        media_lookup: dict[str, str],
    ) -> str | None:
        if not raw_value or archive is None:
            return None
        filename = extract_image_filename(raw_value)
        if not filename:
            return None
        ext = filename.rsplit(".", 1)[-1].lower()
        mime = _IMAGE_MIMES.get(ext)
        if not mime:
            return None
        data = _read_media_file(archive, filename, media_lookup)
        if not data:
            return None
        try:
            return await self._storage.upload_image(data, mime, ext)
        except Exception as exc:
            logger.warning("Image upload failed for %s: %s", filename, exc)
            return None

    async def _upload_audio(
        self,
        raw_value: str,
        archive: zipfile.ZipFile | None,
        media_lookup: dict[str, str],
    ) -> str | None:
        if not raw_value or archive is None:
            return None
        filename = extract_audio_filename(raw_value)
        if not filename:
            return None
        ext = filename.rsplit(".", 1)[-1].lower()
        mime = _AUDIO_MIMES.get(ext)
        if not mime:
            return None
        data = _read_media_file(archive, filename, media_lookup)
        if not data:
            return None
        try:
            return await self._storage.upload_audio(data, mime, ext)
        except Exception as exc:
            logger.warning("Audio upload failed for %s: %s", filename, exc)
            return None


# ── Module-level helpers ──────────────────────────────────────────────────────


def _build_media_lookup(archive: zipfile.ZipFile) -> dict[str, str]:
    """Build {anki_filename → numeric_id_in_zip} reverse map."""
    try:
        with archive.open("media") as f:
            media_map: dict[str, str] = json.loads(f.read().decode("utf-8"))
        return {v: k for k, v in media_map.items()}
    except Exception:
        return {}


def _read_media_file(
    archive: zipfile.ZipFile,
    filename: str,
    media_lookup: dict[str, str],
) -> bytes | None:
    numeric_id = media_lookup.get(filename)
    if numeric_id is None:
        return None
    try:
        return archive.read(numeric_id)
    except KeyError:
        return None
