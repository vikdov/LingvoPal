# backend/app/services/session_manager.py
"""
Session Manager — buffered practice state in Redis.

Architecture:
  Two keys per session, both with a sliding 24-hour TTL:

  practice:session:{session_id}
    → JSON string of SessionState (metadata: item_order, current_index,
      config, item_hints cache).

  practice:raw:{session_id}
    → Redis LIST of RawAnswerEvent JSON strings (one element per answer).
      Appended with RPUSH; read with LRANGE.

  practice:active:{user_id}
    → Plain string: the session_id of the user's current in-progress session.
      Used for recovery ("is there an active session?") without a DB query.

Atomicity guarantee:
  append_raw_answer() uses a Lua script to RPUSH the raw event AND
  increment SessionState.current_index in a single Redis round-trip,
  preventing any interleaving between the two operations.

Safety valve:
  Before a session key nears its TTL, the application can call
  save_pending_session() to persist the buffered events to PostgreSQL
  (pending_sessions table). The background sweeper uses this path.
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Final

import redis.asyncio as aioredis

logger = logging.getLogger(__name__)

# ============================================================================
# Constants
# ============================================================================

SESSION_KEY_PREFIX: Final[str] = "practice:session:"
RAW_KEY_PREFIX: Final[str] = "practice:raw:"
ACTIVE_KEY_PREFIX: Final[str] = "practice:active:"
FLUSHING_KEY_PREFIX: Final[str] = "practice:flushing:"
SEEN_KEY_PREFIX: Final[str] = "practice:seen:"
TTL_SECONDS: Final[int] = 24 * 3600  # 24-hour sliding window
FLUSH_LOCK_TTL: Final[int] = 120      # flushing lock expires after 2 min

INTENSITY_MAP: Final[dict[str, float]] = {
    "light": 1.3,
    "balanced": 1.0,
    "intensive": 0.75,
}

# ============================================================================
# Data contracts
# ============================================================================


@dataclass
class BatchConfig:
    """User-settings-derived configuration for a practice batch."""

    # SM-2 scheduling
    evaluation_mode: str = "normal"
    review_intensity: float = 1.0
    batch_size: int = 10
    new_items_per_session: int = 10
    target_lang_id: int = 0

    # Hint visibility (sent to frontend as ComparisonConfig)
    show_hints_on_fails: bool = True
    show_translations: bool = True
    show_images: bool = True
    show_synonyms: bool = True
    show_part_of_speech: bool = True
    auto_play_audio: bool = False

    def to_dict(self) -> dict:
        return {
            "evaluation_mode": self.evaluation_mode,
            "review_intensity": self.review_intensity,
            "batch_size": self.batch_size,
            "new_items_per_session": self.new_items_per_session,
            "target_lang_id": self.target_lang_id,
            "show_hints_on_fails": self.show_hints_on_fails,
            "show_translations": self.show_translations,
            "show_images": self.show_images,
            "show_synonyms": self.show_synonyms,
            "show_part_of_speech": self.show_part_of_speech,
            "auto_play_audio": self.auto_play_audio,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "BatchConfig":
        return cls(
            evaluation_mode=d.get("evaluation_mode", "normal"),
            review_intensity=d.get("review_intensity", 1.0),
            batch_size=d.get("batch_size", 10),
            new_items_per_session=d.get("new_items_per_session", 10),
            target_lang_id=d.get("target_lang_id", 0),
            show_hints_on_fails=d.get("show_hints_on_fails", True),
            show_translations=d.get("show_translations", True),
            show_images=d.get("show_images", True),
            show_synonyms=d.get("show_synonyms", True),
            show_part_of_speech=d.get("show_part_of_speech", True),
            auto_play_audio=d.get("auto_play_audio", False),
        )


@dataclass
class RawAnswerEvent:
    """
    Per-answer event stored in Redis LIST during a session.

    Contains raw input + fast pre-computed evaluation results (similarity,
    correctness). SM-2 scheduling is intentionally deferred to finalize().

    Fields:
      item_id          — The item being practiced.
      translation_id   — Translation shown as the prompt (may be None for
                         same-language or fallback sets).
      user_answer      — Raw text typed by the user.
      response_time_ms — Raw timing in milliseconds (capped at finalize).
      confidence_override — Optional "easy"/"good"/"hard" from user.
      answered_at      — ISO-8601 UTC timestamp.
      is_correct       — Pre-computed from Levenshtein similarity.
      similarity       — Normalised similarity in [0.0, 1.0].
      correct_answer   — item.term (stored here to avoid re-fetching at
                         finalize and to include in immediate feedback).
    """

    item_id: int
    translation_id: int | None
    user_answer: str
    response_time_ms: int
    confidence_override: int | None  # 1=blackout … 5=easy; None = speed-based
    answered_at: str                 # ISO-8601 UTC
    is_correct: bool
    similarity: float
    correct_answer: str              # item.term
    answer_id: str                   # UUID4 idempotency key

    def to_dict(self) -> dict:
        return {
            "item_id": self.item_id,
            "translation_id": self.translation_id,
            "user_answer": self.user_answer,
            "response_time_ms": self.response_time_ms,
            "confidence_override": self.confidence_override,
            "answered_at": self.answered_at,
            "is_correct": self.is_correct,
            "similarity": self.similarity,
            "correct_answer": self.correct_answer,
            "answer_id": self.answer_id,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "RawAnswerEvent":
        return cls(
            item_id=d["item_id"],
            translation_id=d.get("translation_id"),
            user_answer=d["user_answer"],
            response_time_ms=d["response_time_ms"],
            confidence_override=d.get("confidence_override"),
            answered_at=d["answered_at"],
            is_correct=d["is_correct"],
            similarity=d["similarity"],
            correct_answer=d["correct_answer"],
            answer_id=d.get("answer_id", ""),
        )


@dataclass
class SessionState:
    """
    Metadata for one practice batch, stored in Redis.

    Does NOT store per-answer events — those live in the raw LIST key.
    Reconstructed from DB if the Redis key is lost.

    item_hints: maps str(item_id) → {"prompt", "answer", "context",
    "translation_id"} — pre-fetched at session start to eliminate
    per-answer DB lookups.
    """

    session_id: int
    user_id: int
    set_id: int
    item_order: list[int]
    current_index: int
    config: BatchConfig
    started_at: str            # ISO-8601 UTC
    item_hints: dict[str, dict] = field(default_factory=dict)
    last_answered_at: str | None = None  # updated by Lua on each answer

    # ── Derived helpers ──────────────────────────────────────────────────────

    @property
    def is_complete(self) -> bool:
        return self.current_index >= len(self.item_order)

    @property
    def next_item_id(self) -> int | None:
        if self.is_complete:
            return None
        return self.item_order[self.current_index]

    @property
    def remaining_count(self) -> int:
        return max(0, len(self.item_order) - self.current_index)

    def get_hint(self, item_id: int) -> dict | None:
        return self.item_hints.get(str(item_id))

    # ── Serialisation ────────────────────────────────────────────────────────

    def to_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "set_id": self.set_id,
            "item_order": self.item_order,
            "current_index": self.current_index,
            "config": self.config.to_dict(),
            "started_at": self.started_at,
            "item_hints": self.item_hints,
            "last_answered_at": self.last_answered_at,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "SessionState":
        return cls(
            session_id=d["session_id"],
            user_id=d["user_id"],
            set_id=d["set_id"],
            item_order=d["item_order"],
            current_index=d["current_index"],
            config=BatchConfig.from_dict(d["config"]),
            started_at=d["started_at"],
            item_hints=d.get("item_hints", {}),
            last_answered_at=d.get("last_answered_at"),
        )


# ============================================================================
# Lua script — atomic RPUSH raw event + increment current_index + TTL reset
# ============================================================================

# Atomically appends a raw answer event to the raw LIST, records the
# answer_id in a seen-set for idempotency, updates last_answered_at, and
# increments current_index — all in a single Redis round-trip.
#
# KEYS[1] = practice:session:{session_id}
# KEYS[2] = practice:raw:{session_id}
# KEYS[3] = practice:seen:{session_id}
# ARGV[1] = event JSON string
# ARGV[2] = TTL seconds
# ARGV[3] = answer_id (UUID4)
#
# Returns: updated session JSON string, or error reply.

_APPEND_RAW_LUA = """
local session_key = KEYS[1]
local raw_key     = KEYS[2]
local seen_key    = KEYS[3]
local event_json  = ARGV[1]
local ttl         = tonumber(ARGV[2])
local answer_id   = ARGV[3]

-- Idempotency: reject duplicate answer_ids
if redis.call('SISMEMBER', seen_key, answer_id) == 1 then
    return redis.error_reply('DUPLICATE')
end

-- Load session first (needed for completion check before RPUSH)
local raw = redis.call('GET', session_key)
if raw == false then
    return redis.error_reply('SESSION_NOT_FOUND')
end

local ok, session = pcall(cjson.decode, raw)
if not ok then
    return redis.error_reply('SESSION_CORRUPT')
end

-- Overflow guard: reject answers beyond the item list length
if session['current_index'] >= #session['item_order'] then
    return redis.error_reply('SESSION_COMPLETE')
end

-- Append raw event to list
redis.call('RPUSH', raw_key, event_json)
redis.call('EXPIRE', raw_key, ttl)
redis.call('SADD', seen_key, answer_id)
redis.call('EXPIRE', seen_key, ttl)

-- Advance index and track last activity time
session['current_index'] = session['current_index'] + 1
local ok2, event = pcall(cjson.decode, event_json)
if ok2 then
    session['last_answered_at'] = event['answered_at']
end

local updated = cjson.encode(session)
redis.call('SET', session_key, updated)
redis.call('EXPIRE', session_key, ttl)

return updated
"""


# ============================================================================
# Session Manager
# ============================================================================


class SessionManager:
    """
    Manages buffered practice session state in Redis.

    All mutating operations use Lua scripts or atomic SET — no partial state.
    """

    def __init__(self, redis_client: aioredis.Redis) -> None:
        self._redis = redis_client
        self._lua_append = redis_client.register_script(_APPEND_RAW_LUA)

    # ── Key helpers ──────────────────────────────────────────────────────────

    @staticmethod
    def _session_key(session_id: int) -> str:
        return f"{SESSION_KEY_PREFIX}{session_id}"

    @staticmethod
    def _raw_key(session_id: int) -> str:
        return f"{RAW_KEY_PREFIX}{session_id}"

    @staticmethod
    def _active_key(user_id: int) -> str:
        return f"{ACTIVE_KEY_PREFIX}{user_id}"

    @staticmethod
    def _seen_key(session_id: int) -> str:
        return f"{SEEN_KEY_PREFIX}{session_id}"

    # ── Session metadata CRUD ────────────────────────────────────────────────

    async def save_session(self, state: SessionState) -> None:
        """Persist (new or updated) session metadata with sliding TTL."""
        key = self._session_key(state.session_id)
        await self._redis.set(key, json.dumps(state.to_dict()), ex=TTL_SECONDS)
        logger.debug("session_saved", extra={"session_id": state.session_id})

    async def load_session(self, session_id: int) -> SessionState | None:
        """Load session metadata. Returns None on cache miss."""
        raw = await self._redis.get(self._session_key(session_id))
        if raw is None:
            logger.debug("session_cache_miss", extra={"session_id": session_id})
            return None
        try:
            return SessionState.from_dict(json.loads(raw))
        except (json.JSONDecodeError, KeyError) as exc:
            logger.error(
                "session_deserialization_failed",
                extra={"session_id": session_id, "error": str(exc)},
            )
            return None

    async def delete_session(self, session_id: int) -> None:
        """Remove all Redis keys for a session (call AFTER DB commit)."""
        await self._redis.delete(
            self._session_key(session_id),
            self._raw_key(session_id),
            self._seen_key(session_id),
        )
        logger.info("session_deleted_from_redis", extra={"session_id": session_id})

    async def session_exists(self, session_id: int) -> bool:
        return bool(await self._redis.exists(self._session_key(session_id)))

    # ── Per-answer buffering ──────────────────────────────────────────────────

    async def append_raw_answer(
        self, session_id: int, event: RawAnswerEvent
    ) -> SessionState | None:
        """
        Atomically RPUSH raw event + advance current_index + record answer_id.

        Returns the updated SessionState, or None if the session key is gone
        (cache miss — caller must reconstruct from DB).
        Returns the *existing* cached state unchanged on duplicate answer_id.
        """
        try:
            result = await self._lua_append(
                keys=[
                    self._session_key(session_id),
                    self._raw_key(session_id),
                    self._seen_key(session_id),
                ],
                args=[json.dumps(event.to_dict()), str(TTL_SECONDS), event.answer_id],
            )
        except aioredis.ResponseError as exc:
            err = str(exc)
            if "SESSION_NOT_FOUND" in err:
                logger.warning(
                    "session_append_cache_miss", extra={"session_id": session_id}
                )
                return None
            if "SESSION_COMPLETE" in err:
                logger.warning(
                    "session_append_overflow",
                    extra={"session_id": session_id, "answer_id": event.answer_id},
                )
                return await self.load_session(session_id)
            if "DUPLICATE" in err:
                logger.info(
                    "session_append_duplicate",
                    extra={"session_id": session_id, "answer_id": event.answer_id},
                )
                return await self.load_session(session_id)
            raise

        if result is None:
            return None

        try:
            return SessionState.from_dict(json.loads(result))
        except (json.JSONDecodeError, KeyError) as exc:
            logger.error(
                "session_append_deserialization_failed",
                extra={"session_id": session_id, "error": str(exc)},
            )
            return None

    async def get_raw_answers(self, session_id: int) -> list[RawAnswerEvent]:
        """Retrieve all buffered answer events from the Redis LIST (LRANGE 0 -1)."""
        raw_list = await self._redis.lrange(self._raw_key(session_id), 0, -1)
        events: list[RawAnswerEvent] = []
        for raw in raw_list:
            try:
                events.append(RawAnswerEvent.from_dict(json.loads(raw)))
            except (json.JSONDecodeError, KeyError) as exc:
                logger.error(
                    "raw_event_deserialization_failed",
                    extra={"session_id": session_id, "error": str(exc)},
                )
        return events

    async def raw_answer_count(self, session_id: int) -> int:
        """Return the length of the raw answers LIST (cheap LLEN call)."""
        return await self._redis.llen(self._raw_key(session_id))

    # ── Active session pointer (reverse lookup user → session) ───────────────

    async def set_active(self, user_id: int, session_id: int) -> None:
        """Record which session_id is the user's current in-progress session."""
        await self._redis.set(
            self._active_key(user_id), str(session_id), ex=TTL_SECONDS
        )

    async def get_active_session_id(self, user_id: int) -> int | None:
        """Return the active session_id for a user, or None."""
        raw = await self._redis.get(self._active_key(user_id))
        if raw is None:
            return None
        try:
            return int(raw)
        except ValueError:
            return None

    async def clear_active(self, user_id: int) -> None:
        """Remove the active session pointer after session completion."""
        await self._redis.delete(self._active_key(user_id))

    # ── TTL introspection (for safety valve) ────────────────────────────────

    async def session_ttl_seconds(self, session_id: int) -> int:
        """Return remaining TTL of the session key in seconds (-2 if gone)."""
        return await self._redis.ttl(self._session_key(session_id))

    # ── Flush lock (prevents concurrent double-finalize) ────────────────────

    @staticmethod
    def _flushing_key(session_id: int) -> str:
        return f"{FLUSHING_KEY_PREFIX}{session_id}"

    async def acquire_flush_lock(self, session_id: int) -> bool:
        """
        Atomically claim the flush lock (SET NX EX).

        Returns True if acquired, False if another caller already holds it.
        """
        result = await self._redis.set(
            self._flushing_key(session_id),
            "1",
            nx=True,
            ex=FLUSH_LOCK_TTL,
        )
        return result is not None

    async def release_flush_lock(self, session_id: int) -> None:
        await self._redis.delete(self._flushing_key(session_id))


# ============================================================================
# Factory helpers
# ============================================================================


def make_session_state(
    *,
    session_id: int,
    user_id: int,
    set_id: int,
    item_order: list[int],
    config: BatchConfig,
    item_hints: dict[str, dict],
) -> SessionState:
    """Construct a brand-new SessionState for a just-started batch."""
    return SessionState(
        session_id=session_id,
        user_id=user_id,
        set_id=set_id,
        item_order=item_order,
        current_index=0,
        config=config,
        started_at=datetime.now(timezone.utc).isoformat(),
        item_hints=item_hints,
    )


__all__ = [
    "SessionManager",
    "SessionState",
    "RawAnswerEvent",
    "BatchConfig",
    "make_session_state",
    "SESSION_KEY_PREFIX",
    "RAW_KEY_PREFIX",
    "ACTIVE_KEY_PREFIX",
    "FLUSHING_KEY_PREFIX",
    "SEEN_KEY_PREFIX",
    "TTL_SECONDS",
    "FLUSH_LOCK_TTL",
    "INTENSITY_MAP",
]
