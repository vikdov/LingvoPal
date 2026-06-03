from pydantic import BaseModel, Field


class FieldMappingSchema(BaseModel):
    term_field: str  # required — what the user learns
    translation_field: str | None = None  # term_trans (may not exist in monolingual decks)
    context_field: str | None = None  # example sentence in source language
    context_trans_field: str | None = None  # example sentence in target language
    lemma_field: str | None = None  # base form / transcription / pronunciation
    part_of_speech_field: str | None = None  # parsed to PartOfSpeech enum
    image_field: str | None = None  # must contain <img src="...">
    audio_field: str | None = None  # must contain [sound:...]


class DetectedFieldInfo(BaseModel):
    name: str
    sample: str
    has_image: bool
    has_audio: bool


class AnkiPreviewResponse(BaseModel):
    import_token: str
    deck_name: str
    card_count: int
    media_size_bytes: int
    detected_fields: list[DetectedFieldInfo]
    suggested_mapping: FieldMappingSchema


class AnkiConfirmRequest(BaseModel):
    import_token: str = Field(min_length=1)
    source_lang_id: int = Field(gt=0)
    target_lang_id: int | None = Field(default=None, gt=0)
    title: str | None = Field(default=None, max_length=200)
    field_mapping: FieldMappingSchema


class AnkiImportResponse(BaseModel):
    set_id: int
    title: str
    item_count: int
    skipped_count: int
    reused_count: int = 0
    no_gap_count: int = 0  # cards skipped because term not findable in context sentence
