# backend/tests/test_anki_parser.py
"""
Unit tests for anki_parser pure helpers.

No I/O, no DB — all functions are pure / deterministic.

Test groups:
  - _strip_html(): tag removal, nested, self-closing, plain text passthrough
  - _strip_cloze_markup(): single, multi-cloze, hints, no-cloze passthrough
  - extract_image_filename(): src extraction, quotes, no-match
  - extract_audio_filename(): [sound:…] extraction, no-match
  - _find_root_deck_name(): shortest-name selection, empty fallback
  - _suggest_mapping(): standard vocab, image/audio bias, cloze context, no-dupe
  - _extract_cloze_cards(): single, multi-index, with-hint, no-cloze, context field
"""


from app.services.anki_parser import (
    CLOZE_CONTEXT_FIELD,
    DetectedField,
    _extract_cloze_cards,
    _find_root_deck_name,
    _strip_cloze_markup,
    _strip_html,
    _suggest_mapping,
    extract_audio_filename,
    extract_image_filename,
)

# ── _strip_html ───────────────────────────────────────────────────────────────


class TestStripHtml:
    def test_plain_text_unchanged(self) -> None:
        assert _strip_html("hello world") == "hello world"

    def test_removes_single_tag(self) -> None:
        assert _strip_html("<b>bold</b>") == "bold"

    def test_removes_nested_tags(self) -> None:
        assert _strip_html("<div><span>text</span></div>") == "text"

    def test_removes_self_closing_tag(self) -> None:
        # img tag yields no text content
        assert _strip_html('<img src="x.jpg" />') == ""

    def test_preserves_whitespace_trimmed(self) -> None:
        assert _strip_html("  <b>word</b>  ") == "word"

    def test_multi_element(self) -> None:
        assert _strip_html("<b>one</b> <i>two</i>") == "one two"

    def test_empty_string(self) -> None:
        assert _strip_html("") == ""

    def test_strips_br_leaves_no_tag(self) -> None:
        result = _strip_html("line1<br>line2")
        assert "<br>" not in result
        assert "line1" in result
        assert "line2" in result

    def test_attributes_discarded(self) -> None:
        assert _strip_html('<span class="highlight">word</span>') == "word"


# ── _strip_cloze_markup ───────────────────────────────────────────────────────


class TestStripClozeMarkup:
    def test_simple_cloze(self) -> None:
        assert _strip_cloze_markup("{{c1::apple}}") == "apple"

    def test_cloze_with_hint(self) -> None:
        assert _strip_cloze_markup("{{c1::apple::fruit}}") == "apple"

    def test_multiple_cloze_different_indices(self) -> None:
        result = _strip_cloze_markup("{{c1::one}} and {{c2::two}}")
        assert result == "one and two"

    def test_multiple_cloze_same_index(self) -> None:
        result = _strip_cloze_markup("{{c1::first}} {{c1::second}}")
        assert result == "first second"

    def test_no_cloze_passthrough(self) -> None:
        text = "I eat an apple every day."
        assert _strip_cloze_markup(text) == text

    def test_cloze_inside_sentence(self) -> None:
        result = _strip_cloze_markup("She {{c1::runs}} every morning.")
        assert result == "She runs every morning."

    def test_empty_string(self) -> None:
        assert _strip_cloze_markup("") == ""


# ── extract_image_filename ────────────────────────────────────────────────────


class TestExtractImageFilename:
    def test_double_quote_src(self) -> None:
        assert extract_image_filename('<img src="photo.jpg">') == "photo.jpg"

    def test_single_quote_src(self) -> None:
        assert extract_image_filename("<img src='photo.png'>") == "photo.png"

    def test_extra_attributes_before_src(self) -> None:
        assert extract_image_filename('<img class="x" src="img.gif">') == "img.gif"

    def test_extra_attributes_after_src(self) -> None:
        assert extract_image_filename('<img src="img.gif" alt="desc">') == "img.gif"

    def test_no_img_tag_returns_none(self) -> None:
        assert extract_image_filename("plain text") is None

    def test_empty_returns_none(self) -> None:
        assert extract_image_filename("") is None

    def test_audio_field_returns_none(self) -> None:
        assert extract_image_filename("[sound:audio.mp3]") is None

    def test_filepath_with_subdirectory(self) -> None:
        assert extract_image_filename('<img src="media/card.jpg">') == "media/card.jpg"


# ── extract_audio_filename ────────────────────────────────────────────────────


class TestExtractAudioFilename:
    def test_mp3(self) -> None:
        assert extract_audio_filename("[sound:pronunciation.mp3]") == "pronunciation.mp3"

    def test_ogg(self) -> None:
        assert extract_audio_filename("[sound:word.ogg]") == "word.ogg"

    def test_no_sound_tag_returns_none(self) -> None:
        assert extract_audio_filename("plain text") is None

    def test_empty_returns_none(self) -> None:
        assert extract_audio_filename("") is None

    def test_img_tag_returns_none(self) -> None:
        assert extract_audio_filename('<img src="img.jpg">') is None

    def test_embeds_inside_longer_string(self) -> None:
        assert extract_audio_filename("word [sound:file.mp3] more") == "file.mp3"


# ── _find_root_deck_name ──────────────────────────────────────────────────────


class TestFindRootDeckName:
    def test_single_deck(self) -> None:
        decks = {"1": {"name": "Japanese"}}
        assert _find_root_deck_name(decks) == "Japanese"

    def test_picks_shortest_name(self) -> None:
        decks = {
            "1": {"name": "Japanese::Verbs"},
            "2": {"name": "Japanese"},
            "3": {"name": "Japanese::Verbs::Irregular"},
        }
        assert _find_root_deck_name(decks) == "Japanese"

    def test_empty_dict_returns_fallback(self) -> None:
        assert _find_root_deck_name({}) == "Imported Deck"

    def test_skips_non_dict_entries(self) -> None:
        decks = {"__type__": "Decks", "1": {"name": "French"}}
        assert _find_root_deck_name(decks) == "French"

    def test_skips_entries_without_name(self) -> None:
        decks = {"1": {"id": 1}, "2": {"name": "Spanish"}}
        assert _find_root_deck_name(decks) == "Spanish"


# ── _suggest_mapping ──────────────────────────────────────────────────────────


def _meta(names: list[str], has_image: str | None = None, has_audio: str | None = None) -> dict[str, DetectedField]:
    """Build a minimal field_meta dict for _suggest_mapping tests."""
    return {
        n: DetectedField(
            name=n,
            sample="sample",
            has_image=(n == has_image),
            has_audio=(n == has_audio),
        )
        for n in names
    }


class TestSuggestMapping:
    def test_front_back_maps_term_translation(self) -> None:
        names = ["Front", "Back"]
        result = _suggest_mapping(names, _meta(names))
        assert result.term_field == "Front"
        assert result.translation_field == "Back"

    def test_word_meaning_maps_term_translation(self) -> None:
        names = ["Word", "Meaning"]
        result = _suggest_mapping(names, _meta(names))
        assert result.term_field == "Word"
        assert result.translation_field == "Meaning"

    def test_sentence_field_maps_to_context(self) -> None:
        names = ["Expression", "Translation", "Sentence"]
        result = _suggest_mapping(names, _meta(names))
        assert result.context_field == "Sentence"

    def test_image_field_with_has_image_flag_preferred(self) -> None:
        names = ["Front", "Back", "Picture"]
        result = _suggest_mapping(names, _meta(names, has_image="Picture"))
        assert result.image_field == "Picture"

    def test_audio_field_with_has_audio_flag_preferred(self) -> None:
        names = ["Front", "Back", "Audio"]
        result = _suggest_mapping(names, _meta(names, has_audio="Audio"))
        assert result.audio_field == "Audio"

    def test_no_field_used_twice(self) -> None:
        names = ["Front", "Back", "Sentence", "Reading", "Picture", "Audio"]
        result = _suggest_mapping(
            names, _meta(names, has_image="Picture", has_audio="Audio")
        )
        assigned = [
            f for f in [
                result.term_field,
                result.translation_field,
                result.context_field,
                result.lemma_field,
                result.image_field,
                result.audio_field,
            ]
            if f is not None
        ]
        # No duplicates
        assert len(assigned) == len(set(assigned))

    def test_empty_field_names_returns_empty_term(self) -> None:
        result = _suggest_mapping([], {})
        assert result.term_field == ""
        assert result.translation_field is None

    def test_single_field_maps_to_term(self) -> None:
        names = ["Word"]
        result = _suggest_mapping(names, _meta(names))
        assert result.term_field == "Word"
        assert result.translation_field is None

    def test_cloze_context_field_preferred_over_generic_context(self) -> None:
        names = ["Text", "Sentence", CLOZE_CONTEXT_FIELD]
        result = _suggest_mapping(names, _meta(names))
        assert result.context_field == CLOZE_CONTEXT_FIELD

    def test_transcription_maps_to_lemma(self) -> None:
        # "Reading" is also in _CONTEXT_FIELDS so it wins context slot first.
        # "Transcription" is lemma-only.
        names = ["Word", "Meaning", "Transcription"]
        result = _suggest_mapping(names, _meta(names))
        assert result.lemma_field == "Transcription"

    def test_pos_field_maps_to_part_of_speech(self) -> None:
        names = ["Word", "Meaning", "Part of Speech"]
        result = _suggest_mapping(names, _meta(names))
        assert result.part_of_speech_field == "Part of Speech"


# ── _extract_cloze_cards ──────────────────────────────────────────────────────


def _fld(name: str) -> dict:
    return {"name": name, "ord": 0}


class TestExtractClozeCards:
    def test_single_cloze_produces_one_card(self) -> None:
        fld_defs = [_fld("Text"), _fld("Extra")]
        raw_parts = ["{{c1::apple}} is a fruit.", "note"]
        cards = _extract_cloze_cards(fld_defs, raw_parts, [])
        assert len(cards) == 1
        assert cards[0].fields["Text"] == "apple"

    def test_two_cloze_indices_produce_two_cards(self) -> None:
        fld_defs = [_fld("Text")]
        raw_parts = ["{{c1::one}} and {{c2::two}}."]
        cards = _extract_cloze_cards(fld_defs, raw_parts, [])
        assert len(cards) == 2
        terms = {c.fields["Text"] for c in cards}
        assert terms == {"one", "two"}

    def test_hint_stripped_term_only(self) -> None:
        fld_defs = [_fld("Text")]
        raw_parts = ["{{c1::apple::fruit}}"]
        cards = _extract_cloze_cards(fld_defs, raw_parts, [])
        assert cards[0].fields["Text"] == "apple"

    def test_no_cloze_markup_returns_empty(self) -> None:
        fld_defs = [_fld("Text")]
        raw_parts = ["plain sentence without cloze"]
        cards = _extract_cloze_cards(fld_defs, raw_parts, [])
        assert cards == []

    def test_context_field_added_when_sentence_differs_from_term(self) -> None:
        fld_defs = [_fld("Text")]
        raw_parts = ["She {{c1::runs}} every morning."]
        cards = _extract_cloze_cards(fld_defs, raw_parts, [])
        assert len(cards) == 1
        assert CLOZE_CONTEXT_FIELD in cards[0].fields
        # Cloze markup syntax stripped — only plain text remains
        assert "{{" not in cards[0].fields[CLOZE_CONTEXT_FIELD]
        assert "She runs every morning." == cards[0].fields[CLOZE_CONTEXT_FIELD]

    def test_tags_propagated(self) -> None:
        fld_defs = [_fld("Text")]
        raw_parts = ["{{c1::word}}"]
        cards = _extract_cloze_cards(fld_defs, raw_parts, ["tag1", "tag2"])
        assert cards[0].tags == ["tag1", "tag2"]

    def test_non_cloze_fields_copied_to_card(self) -> None:
        fld_defs = [_fld("Text"), _fld("Extra")]
        raw_parts = ["{{c1::apple}}", "extra note"]
        cards = _extract_cloze_cards(fld_defs, raw_parts, [])
        assert cards[0].fields.get("Extra") == "extra note"

    def test_html_stripped_from_cloze_context(self) -> None:
        fld_defs = [_fld("Text")]
        raw_parts = ["<b>{{c1::word}}</b> in a sentence."]
        cards = _extract_cloze_cards(fld_defs, raw_parts, [])
        context = cards[0].fields.get(CLOZE_CONTEXT_FIELD, "")
        assert "<b>" not in context

    def test_duplicate_cloze_index_deduplicated(self) -> None:
        # Two {{c1::…}} in same note → only one card for that index
        fld_defs = [_fld("Text")]
        raw_parts = ["{{c1::first}} and {{c1::second}}"]
        cards = _extract_cloze_cards(fld_defs, raw_parts, [])
        assert len(cards) == 1
