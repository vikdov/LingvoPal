"""Pydantic schemas for the .lpset bundle format."""

from pydantic import BaseModel, Field, model_validator

from app.models.enums import PartOfSpeech

LPSET_VERSION = 1


class LpsetTranslation(BaseModel):
    lang: str = Field(..., min_length=2, max_length=8)
    term_trans: str = Field(..., min_length=1, max_length=500)
    context_trans: str | None = Field(None, max_length=1000)


class LpsetItem(BaseModel):
    term: str = Field(..., min_length=1, max_length=500)
    context: str | None = Field(None, max_length=1000)
    part_of_speech: PartOfSpeech | None = None
    difficulty: int | None = Field(None, ge=1, le=7)
    lemma: str | None = Field(None, max_length=500)
    audio: str | None = None
    context_audio: str | None = None
    image: str | None = None
    translations: list[LpsetTranslation] = []


class LpsetSet(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str | None = Field(None, max_length=2000)
    source_lang: str = Field(..., min_length=2, max_length=8)
    target_lang: str | None = Field(None, min_length=2, max_length=8)
    difficulty: int | None = Field(None, ge=1, le=7)

    @model_validator(mode="after")
    def langs_must_differ(self) -> "LpsetSet":
        if self.target_lang and self.target_lang == self.source_lang:
            raise ValueError("source_lang and target_lang must differ")
        return self


class LpsetManifest(BaseModel):
    version: int
    set: LpsetSet
    items: list[LpsetItem] = Field(..., min_length=1, max_length=500)

    @model_validator(mode="after")
    def check_version(self) -> "LpsetManifest":
        if self.version != LPSET_VERSION:
            raise ValueError(
                f"Unsupported .lpset version {self.version!r}. Expected {LPSET_VERSION}."
            )
        return self
