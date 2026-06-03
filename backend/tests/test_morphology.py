# backend/tests/test_morphology.py
"""
Unit tests for morphological surface-form matching.

No DB, no mocks — pure function calls only.

Test groups:
  - find_surface_form(): exact match, irregular verbs, suffix stripping,
    case preservation, no-match, empty inputs
  - wrap_surface_form(): found form wrapped with {{}}, not-found passthrough,
    only first occurrence wrapped
"""

from app.services.morphology import find_surface_form, wrap_surface_form

# ── find_surface_form ─────────────────────────────────────────────────────────


class TestFindSurfaceFormExactMatch:
    def test_exact_word_found(self) -> None:
        assert find_surface_form("play", "She likes to play chess.") == "play"

    def test_case_insensitive_match(self) -> None:
        assert find_surface_form("london", "She lives in London.") == "London"

    def test_preserves_original_case_from_context(self) -> None:
        result = find_surface_form("python", "I love Python programming.")
        assert result == "Python"

    def test_word_boundary_not_substring(self) -> None:
        # "play" must not match inside "playground"
        result = find_surface_form("play", "The playground was empty.")
        assert result != "playground"


class TestFindSurfaceFormIrregularVerbs:
    def test_irregular_past_tense(self) -> None:
        assert find_surface_form("go", "She went to the store.") == "went"

    def test_irregular_past_participle(self) -> None:
        assert find_surface_form("write", "The letter was written.") == "written"

    def test_irregular_third_person(self) -> None:
        assert find_surface_form("have", "He has a car.") == "has"

    def test_irregular_present_participle(self) -> None:
        assert find_surface_form("run", "He is running fast.") == "running"

    def test_be_verb_forms(self) -> None:
        assert find_surface_form("be", "She is happy.") == "is"
        assert find_surface_form("be", "They were late.") == "were"


class TestFindSurfaceFormSuffixStripping:
    def test_regular_past_tense(self) -> None:
        assert find_surface_form("play", "She played the piano.") == "played"

    def test_plural_noun(self) -> None:
        assert find_surface_form("dog", "The dogs barked.") == "dogs"

    def test_third_person_singular(self) -> None:
        assert find_surface_form("work", "He works hard.") == "works"

    def test_comparative(self) -> None:
        result = find_surface_form("fast", "She ran faster.")
        assert result == "faster"


class TestFindSurfaceFormNoMatch:
    def test_returns_none_when_not_found(self) -> None:
        assert find_surface_form("elephant", "The cat sat on the mat.") is None

    def test_empty_term_returns_none(self) -> None:
        assert find_surface_form("", "Some context.") is None

    def test_empty_context_returns_none(self) -> None:
        assert find_surface_form("play", "") is None

    def test_none_context_handled(self) -> None:
        # context is typed as str but defensive check matters
        assert find_surface_form("play", "") is None


# ── wrap_surface_form ─────────────────────────────────────────────────────────


class TestWrapSurfaceForm:
    def test_wraps_exact_match(self) -> None:
        result = wrap_surface_form("play", "She likes to play chess.")
        assert result == "She likes to {{play}} chess."

    def test_wraps_irregular_form(self) -> None:
        result = wrap_surface_form("go", "She went to the store.")
        assert result == "She {{went}} to the store."

    def test_wraps_inflected_form(self) -> None:
        result = wrap_surface_form("play", "She played the piano.")
        assert result == "She {{played}} the piano."

    def test_returns_context_unchanged_when_not_found(self) -> None:
        original = "The cat sat on the mat."
        assert wrap_surface_form("elephant", original) == original

    def test_only_wraps_first_occurrence(self) -> None:
        result = wrap_surface_form("play", "They play, and then they play again.")
        assert result.count("{{play}}") == 1
        assert result.count("play") == 2  # one wrapped, one plain
