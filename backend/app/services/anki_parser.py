"""
Anki .apkg parser — pure parsing, no I/O side effects.

.apkg is a ZIP archive containing a SQLite collection DB and a media manifest.
Supports both legacy schema (col.models JSON) and new schema (notetypes table,
introduced in Anki 2.1.28 / schema version 18).

DB file priority: collection.anki21 > collection.anki2
"""

import io
import json
import os
import re
import sqlite3
import tempfile
import zipfile
from dataclasses import dataclass
from html.parser import HTMLParser

_DB_NAMES = ("collection.anki21", "collection.anki2")

_TERM_FIELDS = frozenset(
    ["front", "expression", "word", "vocabulary", "kanji", "hanzi", "term", "japanese"]
)
_TRANSLATION_FIELDS = frozenset(
    ["back", "meaning", "definition", "english", "translation", "glossary"]
)
_CONTEXT_FIELDS = frozenset(
    ["sentence", "example", "context", "reading", "usage", "example sentence"]
)
_LEMMA_FIELDS = frozenset(
    ["transcription", "pronunciation", "reading", "lemma", "base form", "phonetics"]
)
_POS_FIELDS = frozenset(["part of speech", "pos", "word type", "grammatical category", "type"])
_IMAGE_FIELDS = frozenset(["image", "picture", "photo", "img"])
_AUDIO_FIELDS = frozenset(["word audio", "audio", "sound", "pronunciation audio", "recording"])

_CLOZE_RE = re.compile(r"\{\{c\d+::")
_CLOZE_TAG_RE = re.compile(r"\{\{c(\d+)::([^:}]+)(?:::[^}]*)?\}\}")
_IMG_RE = re.compile(r'<img[^>]+src=["\']([^"\']+)["\']', re.IGNORECASE)
_SOUND_RE = re.compile(r"\[sound:([^\]]+)\]")

# Synthetic field name injected for cloze notes so the user can map the gap sentence
CLOZE_CONTEXT_FIELD = "Cloze Sentence (auto)"


def _strip_cloze_markup(text: str) -> str:
    """Replace {{c1::word::hint}} → word"""
    return _CLOZE_TAG_RE.sub(lambda m: m.group(2), text)


class _HTMLStripper(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._parts: list[str] = []

    def handle_data(self, data: str) -> None:
        self._parts.append(data)

    def get_text(self) -> str:
        return "".join(self._parts).strip()


def _strip_html(text: str) -> str:
    stripper = _HTMLStripper()
    stripper.feed(text)
    return stripper.get_text()


def extract_image_filename(raw_value: str) -> str | None:
    """Extract filename from an Anki image field: <img src="filename.jpg">"""
    m = _IMG_RE.search(raw_value)
    return m.group(1) if m else None


def extract_audio_filename(raw_value: str) -> str | None:
    """Extract filename from an Anki audio field: [sound:filename.mp3]"""
    m = _SOUND_RE.search(raw_value)
    return m.group(1) if m else None


@dataclass
class DetectedField:
    name: str
    sample: str  # HTML-stripped sample value
    has_image: bool  # field contains <img ...> syntax
    has_audio: bool  # field contains [sound:...] syntax


@dataclass
class ParsedCard:
    fields: dict[str, str]  # HTML-stripped text values
    raw_fields: dict[str, str]  # raw values (for media extraction)
    tags: list[str]


@dataclass
class SuggestedMapping:
    term_field: str
    translation_field: str | None
    context_field: str | None
    context_trans_field: str | None
    lemma_field: str | None
    part_of_speech_field: str | None
    image_field: str | None
    audio_field: str | None


@dataclass
class AnkiParseResult:
    root_deck_name: str
    card_count: int
    media_size_bytes: int
    detected_fields: list[DetectedField]
    suggested_mapping: SuggestedMapping
    cards: list[ParsedCard]


def _suggest_mapping(
    field_names: list[str], field_meta: dict[str, DetectedField]
) -> SuggestedMapping:
    lower = {n.lower(): n for n in field_names}

    def pick(*candidates: frozenset, exclude: set[str] | None = None) -> str | None:
        used = exclude or set()
        for candidate_set in candidates:
            for raw_lower, original in lower.items():
                if raw_lower in candidate_set and original not in used:
                    return original
        return None

    term = pick(_TERM_FIELDS) or (field_names[0] if field_names else None)
    used = {term} if term else set()

    # For image/audio, prefer fields that actually contain media syntax
    image = next((n for n in field_names if field_meta[n].has_image), None) or pick(
        _IMAGE_FIELDS, exclude=used
    )

    audio = next((n for n in field_names if field_meta[n].has_audio and n != image), None) or pick(
        _AUDIO_FIELDS, exclude=used | ({image} if image else set())
    )

    if image:
        used.add(image)
    if audio:
        used.add(audio)

    translation = pick(_TRANSLATION_FIELDS, exclude=used)
    if translation:
        used.add(translation)

    # Prefer the auto-generated cloze context over regular context fields
    if CLOZE_CONTEXT_FIELD in field_names and CLOZE_CONTEXT_FIELD not in used:
        context = CLOZE_CONTEXT_FIELD
    else:
        context = pick(_CONTEXT_FIELDS, exclude=used)
    if context:
        used.add(context)

    lemma = pick(_LEMMA_FIELDS, exclude=used)
    if lemma:
        used.add(lemma)

    pos = pick(_POS_FIELDS, exclude=used)

    return SuggestedMapping(
        term_field=term or (field_names[0] if field_names else ""),
        translation_field=translation,
        context_field=context,
        context_trans_field=None,
        lemma_field=lemma,
        part_of_speech_field=pos,
        image_field=image,
        audio_field=audio,
    )


def parse_apkg(file_bytes: bytes) -> AnkiParseResult:
    """
    Parse an Anki .apkg file and extract cards + metadata.

    Raises ValueError for invalid or corrupt files.
    Does not upload or process media file contents — callers receive filenames
    and can extract bytes from the archive separately.
    """
    try:
        archive = zipfile.ZipFile(io.BytesIO(file_bytes))
    except zipfile.BadZipFile as exc:
        raise ValueError("Not a valid .apkg file (bad ZIP)") from exc

    with archive:
        media_size_bytes = _measure_media(archive)
        sqlite_bytes = _extract_db(archive)

    tmp_fd, tmp_path = tempfile.mkstemp(suffix=".anki2")
    try:
        os.write(tmp_fd, sqlite_bytes)
        os.close(tmp_fd)
        return _parse_sqlite(tmp_path, media_size_bytes)
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass


def _extract_db(archive: zipfile.ZipFile) -> bytes:
    for name in _DB_NAMES:
        try:
            return archive.read(name)
        except KeyError:
            continue
    raise ValueError(
        "Invalid .apkg: no collection database found "
        "(expected collection.anki21 or collection.anki2)"
    )


def _measure_media(archive: zipfile.ZipFile) -> int:
    try:
        with archive.open("media") as f:
            media_map: dict[str, str] = json.loads(f.read().decode("utf-8"))
    except (KeyError, json.JSONDecodeError):
        return 0
    zip_info = {info.filename: info.file_size for info in archive.infolist()}
    return sum(zip_info.get(numeric_id, 0) for numeric_id in media_map)


def _parse_sqlite(db_path: str, media_size_bytes: int) -> AnkiParseResult:
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("SELECT models, decks FROM col LIMIT 1")
        col_row = cursor.fetchone()
        if col_row is None:
            raise ValueError("Invalid .apkg: col table is empty")

        models: dict = json.loads(col_row["models"])
        decks_raw: dict = json.loads(col_row["decks"])

        if not models:
            models = _load_models_new_schema(cursor)
        if not decks_raw:
            root_deck_name = _load_root_deck_new_schema(cursor)
        else:
            root_deck_name = _find_root_deck_name(decks_raw)

        canonical_field_names = _find_canonical_field_names(models)

        cursor.execute("""
            SELECT n.mid, n.flds, n.tags
            FROM notes n
            JOIN cards c ON n.id = c.nid
            WHERE c.ord = 0 AND c.queue != -1
            ORDER BY n.id
        """)
        rows = cursor.fetchall()

    cards, field_samples, field_meta = _extract_cards(rows, models)

    field_names = (
        list(canonical_field_names) if canonical_field_names else list(field_samples.keys())
    )
    # Append synthetic cloze context field when present (cloze decks)
    if CLOZE_CONTEXT_FIELD in field_samples and CLOZE_CONTEXT_FIELD not in field_names:
        field_names.append(CLOZE_CONTEXT_FIELD)
    detected_fields = [
        field_meta.get(n, DetectedField(name=n, sample="", has_image=False, has_audio=False))
        for n in field_names
    ]

    return AnkiParseResult(
        root_deck_name=root_deck_name,
        card_count=len(cards),
        media_size_bytes=media_size_bytes,
        detected_fields=detected_fields,
        suggested_mapping=_suggest_mapping(field_names, {f.name: f for f in detected_fields}),
        cards=cards,
    )


def _find_root_deck_name(decks: dict) -> str:
    names = [d["name"] for d in decks.values() if isinstance(d, dict) and d.get("name")]
    return min(names, key=len) if names else "Imported Deck"


def _find_canonical_field_names(models: dict) -> list[str]:
    for model in models.values():
        if model.get("type", 0) == 0:
            return [f["name"] for f in model.get("flds", [])]
    return []


def _load_models_new_schema(cursor: sqlite3.Cursor) -> dict:
    result: dict = {}
    try:
        cursor.execute("SELECT id FROM notetypes")
        for row in cursor.fetchall():
            result[str(row["id"])] = {"type": 0, "flds": []}
    except sqlite3.OperationalError:
        return {}
    try:
        cursor.execute("SELECT ntid, ord, name FROM fields ORDER BY ntid, ord")
        for row in cursor.fetchall():
            ntid = str(row["ntid"])
            if ntid in result:
                result[ntid]["flds"].append({"name": row["name"], "ord": row["ord"]})
    except sqlite3.OperationalError:
        pass
    return result


def _load_root_deck_new_schema(cursor: sqlite3.Cursor) -> str:
    try:
        cursor.execute("SELECT name FROM decks ORDER BY length(name) ASC LIMIT 1")
        row = cursor.fetchone()
        if row:
            return row["name"]
    except sqlite3.OperationalError:
        pass
    return "Imported Deck"


def _extract_cloze_cards(
    fld_defs: list,
    raw_parts: list[str],
    tags: list[str],
) -> list[ParsedCard]:
    """
    Convert one cloze Anki note into one ParsedCard per unique cloze index.

    The cloze field value is replaced with the extracted term, and a
    CLOZE_CONTEXT_FIELD entry holds the full clean sentence so that
    _split_cloze can generate the gap at practice time.
    """
    cloze_idx: int | None = None
    for i, fld_def in enumerate(fld_defs):
        raw_val = raw_parts[i] if i < len(raw_parts) else ""
        if _CLOZE_RE.search(raw_val):
            cloze_idx = i
            break
    if cloze_idx is None:
        return []

    cloze_field_name = fld_defs[cloze_idx]["name"]
    raw_cloze = raw_parts[cloze_idx] if cloze_idx < len(raw_parts) else ""

    clean_context = _strip_html(_strip_cloze_markup(raw_cloze))

    # Base fields from non-cloze positions
    base_stripped: dict[str, str] = {}
    base_raw: dict[str, str] = {}
    for i, fld_def in enumerate(fld_defs):
        if i == cloze_idx:
            continue
        name = fld_def["name"]
        raw_val = raw_parts[i] if i < len(raw_parts) else ""
        base_stripped[name] = _strip_html(raw_val)
        base_raw[name] = raw_val

    # One card per unique cloze index ({{c1::…}}, {{c2::…}}, …)
    seen: dict[str, str] = {}
    for m in _CLOZE_TAG_RE.finditer(raw_cloze):
        cidx, term_raw = m.group(1), m.group(2)
        term = _strip_html(term_raw).strip()
        if cidx not in seen and term:
            seen[cidx] = term

    result: list[ParsedCard] = []
    for term in seen.values():
        fields = {cloze_field_name: term, **base_stripped}
        if clean_context and clean_context != term:
            fields[CLOZE_CONTEXT_FIELD] = clean_context
        result.append(
            ParsedCard(fields=fields, raw_fields={cloze_field_name: term, **base_raw}, tags=tags)
        )
    return result


def _extract_cards(
    rows: list, models: dict
) -> tuple[list[ParsedCard], dict[str, str], dict[str, DetectedField]]:
    cards: list[ParsedCard] = []
    field_samples: dict[str, str] = {}
    field_meta: dict[str, DetectedField] = {}

    for row in rows:
        mid = str(row["mid"])
        model = models.get(mid)
        if model is None:
            continue

        fld_defs = model.get("flds", [])
        raw_parts = row["flds"].split("\x1f")
        tags = [t for t in row["tags"].split() if t]

        is_cloze = model.get("type", 0) == 1 or bool(_CLOZE_RE.search(row["flds"]))
        if is_cloze:
            for ccard in _extract_cloze_cards(fld_defs, raw_parts, tags):
                cards.append(ccard)
                for name, val in ccard.fields.items():
                    if val and name not in field_samples:
                        field_samples[name] = val
                    if name not in field_meta:
                        field_meta[name] = DetectedField(
                            name=name, sample=val, has_image=False, has_audio=False
                        )
            continue

        stripped: dict[str, str] = {}
        raw: dict[str, str] = {}

        for idx, fld_def in enumerate(fld_defs):
            name = fld_def["name"]
            raw_val = raw_parts[idx] if idx < len(raw_parts) else ""
            text_val = _strip_html(raw_val)
            stripped[name] = text_val
            raw[name] = raw_val

            # Build DetectedField metadata from first encounter
            if name not in field_meta:
                field_meta[name] = DetectedField(
                    name=name,
                    sample=text_val,
                    has_image=bool(_IMG_RE.search(raw_val)),
                    has_audio=bool(_SOUND_RE.search(raw_val)),
                )
            else:
                # Update has_image/has_audio flags if we find evidence later
                meta = field_meta[name]
                if not meta.has_image and _IMG_RE.search(raw_val):
                    field_meta[name] = DetectedField(
                        name=name, sample=meta.sample, has_image=True, has_audio=meta.has_audio
                    )
                if not meta.has_audio and _SOUND_RE.search(raw_val):
                    field_meta[name] = DetectedField(
                        name=name,
                        sample=meta.sample,
                        has_image=field_meta[name].has_image,
                        has_audio=True,
                    )

            if text_val and name not in field_samples:
                field_samples[name] = text_val

        if stripped:
            cards.append(ParsedCard(fields=stripped, raw_fields=raw, tags=tags))

    return cards, field_samples, field_meta
