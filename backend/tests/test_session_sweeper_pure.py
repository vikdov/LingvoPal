# backend/tests/test_session_sweeper_pure.py
"""
Pure-logic unit tests for SessionSweeper — no Redis, no DB, no async.

Covers:
  - _is_inactive: TTL threshold decisions
  - _build_sweeper_config: settings → BatchConfig mapping
"""

from types import SimpleNamespace

import pytest

from app.services.session_manager import INTENSITY_MAP, TTL_SECONDS, BatchConfig
from app.services.session_sweeper import (
    INACTIVITY_TIMEOUT_SECONDS,
    SessionSweeper,
    _build_sweeper_config,
)

# ── Helpers ───────────────────────────────────────────────────────────────────

_SWEEPER = SessionSweeper(db_factory=None, redis=None)  # type: ignore[arg-type]


def _settings(**overrides):
    """Minimal UserSettings-like namespace for _build_sweeper_config."""
    defaults = dict(
        evaluation_mode=SimpleNamespace(value="normal"),
        learning_intensity=SimpleNamespace(value="balanced"),
        daily_study_goal=10,
        new_items_per_session=10,
        show_hints_on_fails=True,
        show_translations=True,
        show_images=True,
        show_synonyms=True,
        show_part_of_speech=True,
        auto_play_audio=False,
    )
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


# ── _is_inactive ──────────────────────────────────────────────────────────────


class TestIsInactive:
    def test_negative_ttl_not_inactive(self):
        # TTL < 0 means Redis key expired — sweeper handles separately via threshold
        assert _SWEEPER._is_inactive(-1) is False

    def test_zero_ttl_inactive(self):
        # 0 means just expired; TTL_SECONDS - 0 = TTL_SECONDS >> INACTIVITY_TIMEOUT
        assert _SWEEPER._is_inactive(0) is True

    def test_fresh_session_not_inactive(self):
        # Session answered < 1 second ago — TTL is almost TTL_SECONDS
        assert _SWEEPER._is_inactive(TTL_SECONDS - 1) is False

    def test_exactly_at_timeout_not_inactive(self):
        # (TTL_SECONDS - ttl) must be strictly greater than timeout
        ttl = TTL_SECONDS - INACTIVITY_TIMEOUT_SECONDS
        assert _SWEEPER._is_inactive(ttl) is False

    def test_one_second_past_timeout_inactive(self):
        ttl = TTL_SECONDS - INACTIVITY_TIMEOUT_SECONDS - 1
        assert _SWEEPER._is_inactive(ttl) is True

    def test_very_old_session_inactive(self):
        # 23 hours of inactivity
        ttl = TTL_SECONDS - 23 * 3600
        assert _SWEEPER._is_inactive(ttl) is True

    def test_just_under_30min_not_inactive(self):
        ttl = TTL_SECONDS - (INACTIVITY_TIMEOUT_SECONDS - 1)
        assert _SWEEPER._is_inactive(ttl) is False

    def test_just_over_30min_inactive(self):
        ttl = TTL_SECONDS - (INACTIVITY_TIMEOUT_SECONDS + 1)
        assert _SWEEPER._is_inactive(ttl) is True


# ── _build_sweeper_config ─────────────────────────────────────────────────────


class TestBuildSweeperConfig:
    def test_none_settings_returns_defaults(self):
        cfg = _build_sweeper_config(None, target_lang_id=3)
        assert isinstance(cfg, BatchConfig)
        assert cfg.target_lang_id == 3
        # Should match BatchConfig defaults
        assert cfg.evaluation_mode == "normal"
        assert cfg.review_intensity == 1.0
        assert cfg.batch_size == 10

    def test_target_lang_id_passed_through(self):
        cfg = _build_sweeper_config(_settings(), target_lang_id=7)
        assert cfg.target_lang_id == 7

    def test_evaluation_mode_mapped(self):
        s = _settings(evaluation_mode=SimpleNamespace(value="strict"))
        cfg = _build_sweeper_config(s, target_lang_id=1)
        assert cfg.evaluation_mode == "strict"

    def test_learning_intensity_light_maps_to_1_3(self):
        s = _settings(learning_intensity=SimpleNamespace(value="light"))
        cfg = _build_sweeper_config(s, target_lang_id=1)
        assert cfg.review_intensity == INTENSITY_MAP["light"]

    def test_learning_intensity_balanced_maps_to_1_0(self):
        s = _settings(learning_intensity=SimpleNamespace(value="balanced"))
        cfg = _build_sweeper_config(s, target_lang_id=1)
        assert cfg.review_intensity == INTENSITY_MAP["balanced"]

    def test_learning_intensity_intensive_maps_to_0_75(self):
        s = _settings(learning_intensity=SimpleNamespace(value="intensive"))
        cfg = _build_sweeper_config(s, target_lang_id=1)
        assert cfg.review_intensity == INTENSITY_MAP["intensive"]

    def test_unknown_intensity_falls_back_to_1_0(self):
        s = _settings(learning_intensity=SimpleNamespace(value="unknown"))
        cfg = _build_sweeper_config(s, target_lang_id=1)
        assert cfg.review_intensity == 1.0

    def test_batch_size_from_settings(self):
        s = _settings(daily_study_goal=25)
        cfg = _build_sweeper_config(s, target_lang_id=1)
        assert cfg.batch_size == 25

    def test_new_items_per_session_from_settings(self):
        s = _settings(new_items_per_session=3)
        cfg = _build_sweeper_config(s, target_lang_id=1)
        assert cfg.new_items_per_session == 3

    def test_display_flags_mapped(self):
        s = _settings(
            show_hints_on_fails=False,
            show_translations=False,
            show_images=False,
            show_synonyms=False,
            show_part_of_speech=False,
            auto_play_audio=True,
        )
        cfg = _build_sweeper_config(s, target_lang_id=1)
        assert cfg.show_hints_on_fails is False
        assert cfg.show_translations is False
        assert cfg.show_images is False
        assert cfg.show_synonyms is False
        assert cfg.show_part_of_speech is False
        assert cfg.auto_play_audio is True
