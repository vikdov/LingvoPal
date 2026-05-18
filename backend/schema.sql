-- LingvoPal database schema
-- Run: psql -d lingvopal -f schema.sql

-- ============================================================
-- ENUMS
-- ============================================================

CREATE TYPE user_role AS ENUM ('user', 'admin');
CREATE TYPE content_status AS ENUM ('draft', 'community', 'approved', 'official');
CREATE TYPE part_of_speech_type AS ENUM (
    'noun', 'verb', 'adjective', 'adverb', 'pronoun',
    'preposition', 'conjunction', 'interjection', 'article', 'other'
);
CREATE TYPE moderation_target_type AS ENUM ('item', 'translation', 'set', 'mixed');
CREATE TYPE complaintreason AS ENUM (
    'WRONG_LANGUAGE', 'INCORRECT_TRANSLATION', 'INAPPROPRIATE',
    'SPAM', 'DUPLICATE', 'OTHER'
);
CREATE TYPE moderation_status AS ENUM ('pending', 'approved', 'rejected');
CREATE TYPE session_status_type AS ENUM ('in_progress', 'completed', 'abandoned');
CREATE TYPE learning_intensity AS ENUM ('light', 'balanced', 'intensive');
CREATE TYPE evaluation_mode AS ENUM ('strict', 'normal', 'forgiving');
CREATE TYPE retention_priority AS ENUM ('speed_learning', 'balanced', 'long_term_mastery');

-- ============================================================
-- TABLES
-- ============================================================

CREATE TABLE languages (
    id   SERIAL PRIMARY KEY,
    code TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL
);

CREATE TABLE users (
    id            SERIAL PRIMARY KEY,
    user_status   user_role NOT NULL,
    email         TEXT NOT NULL UNIQUE,
    email_verified BOOLEAN NOT NULL DEFAULT FALSE,
    pending_email TEXT,
    password_hash TEXT NOT NULL,
    username      TEXT UNIQUE,
    deleted_at    TIMESTAMPTZ,
    updated_at    TIMESTAMPTZ,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX ix_users_deleted_at ON users (deleted_at);

CREATE TABLE content_audit_log (
    id          BIGSERIAL PRIMARY KEY,
    table_name  TEXT NOT NULL,
    record_id   INTEGER NOT NULL,
    action      TEXT NOT NULL CHECK (action IN ('INSERT', 'UPDATE', 'DELETE')),
    old_values  JSONB,
    new_values  JSONB,
    user_id     INTEGER REFERENCES users(id) ON DELETE SET NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_content_audit_log_target ON content_audit_log (table_name, record_id);

CREATE TABLE content_complaints (
    id          SERIAL PRIMARY KEY,
    target_type moderation_target_type NOT NULL,
    target_id   INTEGER NOT NULL,
    reporter_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    reason      complaintreason NOT NULL,
    details     TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (reporter_id, target_type, target_id)
);
CREATE INDEX idx_complaints_reporter_day ON content_complaints (reporter_id, created_at);
CREATE INDEX idx_complaints_target ON content_complaints (target_type, target_id);

CREATE TABLE items (
    id            SERIAL PRIMARY KEY,
    language_id   INTEGER NOT NULL REFERENCES languages(id) ON DELETE RESTRICT,
    term          TEXT NOT NULL,
    difficulty    INTEGER CHECK (difficulty BETWEEN 1 AND 7),
    context       TEXT,
    image_url     TEXT,
    audio_url     TEXT,
    context_audio_url TEXT,
    part_of_speech part_of_speech_type,
    lemma         TEXT,
    creator_id    INTEGER REFERENCES users(id) ON DELETE SET NULL,
    verified_by   INTEGER REFERENCES users(id) ON DELETE SET NULL,
    status        content_status NOT NULL,
    content_hash  VARCHAR(64),
    deleted_at    TIMESTAMPTZ,
    updated_at    TIMESTAMPTZ,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_items_lookup ON items (language_id, term);
CREATE INDEX ix_items_deleted_at ON items (deleted_at);
CREATE UNIQUE INDEX uq_items_content_hash_active ON items (content_hash)
    WHERE deleted_at IS NULL AND content_hash IS NOT NULL;
CREATE INDEX idx_items_by_creator ON items (creator_id, status, created_at)
    WHERE deleted_at IS NULL;
CREATE INDEX idx_items_unverified ON items (created_at)
    WHERE deleted_at IS NULL AND verified_by IS NULL AND status = 'community';

CREATE TABLE pending_moderation (
    id                  SERIAL PRIMARY KEY,
    target_type         moderation_target_type NOT NULL,
    target_id           INTEGER NOT NULL,
    creator_id          INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    status              moderation_status NOT NULL,
    feedback            TEXT,
    patch_data          JSONB NOT NULL,
    resolved_at         TIMESTAMPTZ,
    moderator_id        INTEGER REFERENCES users(id) ON DELETE SET NULL,
    resolution_feedback TEXT,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_pending_mod_unresolved ON pending_moderation (resolved_at, created_at)
    WHERE resolved_at IS NULL;
CREATE INDEX idx_pending_mod_creator_unresolved ON pending_moderation (creator_id, resolved_at)
    WHERE resolved_at IS NULL;

CREATE TABLE sets (
    id            SERIAL PRIMARY KEY,
    title         TEXT NOT NULL,
    description   TEXT,
    difficulty    INTEGER CHECK (difficulty BETWEEN 1 AND 7),
    source_lang_id INTEGER NOT NULL REFERENCES languages(id) ON DELETE RESTRICT,
    target_lang_id INTEGER REFERENCES languages(id) ON DELETE RESTRICT,
    creator_id    INTEGER REFERENCES users(id) ON DELETE SET NULL,
    verified_by   INTEGER REFERENCES users(id) ON DELETE SET NULL,
    status        content_status NOT NULL,
    deleted_at    TIMESTAMPTZ,
    updated_at    TIMESTAMPTZ,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CHECK (target_lang_id IS NULL OR source_lang_id != target_lang_id)
);
CREATE INDEX ix_sets_deleted_at ON sets (deleted_at);
CREATE INDEX idx_sets_discovery ON sets (status, target_lang_id, difficulty)
    WHERE deleted_at IS NULL AND status IN ('approved', 'official');

CREATE TABLE set_items (
    set_id         INTEGER NOT NULL REFERENCES sets(id) ON DELETE CASCADE,
    item_id        INTEGER NOT NULL REFERENCES items(id) ON DELETE CASCADE,
    sort_order     INTEGER NOT NULL,
    translation_id INTEGER REFERENCES translations(id) ON DELETE SET NULL,
    PRIMARY KEY (set_id, item_id)
);

CREATE TABLE translations (
    id           SERIAL PRIMARY KEY,
    item_id      INTEGER NOT NULL REFERENCES items(id) ON DELETE CASCADE,
    language_id  INTEGER NOT NULL REFERENCES languages(id) ON DELETE RESTRICT,
    term_trans   TEXT NOT NULL,
    context_trans TEXT,
    creator_id   INTEGER REFERENCES users(id) ON DELETE SET NULL,
    verified_by  INTEGER REFERENCES users(id) ON DELETE SET NULL,
    status       content_status NOT NULL,
    deleted_at   TIMESTAMPTZ,
    updated_at   TIMESTAMPTZ,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE UNIQUE INDEX uq_translation_active ON translations (item_id, language_id)
    WHERE deleted_at IS NULL;
CREATE INDEX idx_translations_item ON translations (item_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_translations_item_status ON translations (item_id, status) WHERE deleted_at IS NULL;
CREATE INDEX idx_translations_status_lang ON translations (status, language_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_translations_creator_status ON translations (creator_id, status) WHERE deleted_at IS NULL;
CREATE INDEX ix_translations_deleted_at ON translations (deleted_at);
CREATE INDEX idx_translations_unverified ON translations (created_at)
    WHERE deleted_at IS NULL AND verified_by IS NULL AND status = 'community';

CREATE TABLE user_daily_stats (
    user_id        INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    language_id    INTEGER NOT NULL REFERENCES languages(id) ON DELETE RESTRICT,
    stat_date      DATE NOT NULL,
    correct_count  INTEGER NOT NULL CHECK (correct_count >= 0),
    incorrect_count INTEGER NOT NULL CHECK (incorrect_count >= 0),
    new_words_count INTEGER NOT NULL CHECK (new_words_count >= 0),
    seconds_spent  NUMERIC(10,2) NOT NULL CHECK (seconds_spent >= 0),
    PRIMARY KEY (user_id, language_id, stat_date)
);
CREATE INDEX idx_daily_stats_date ON user_daily_stats (user_id, language_id, stat_date);
CREATE INDEX idx_daily_stats_user_range ON user_daily_stats (user_id, stat_date);

CREATE TABLE user_languages (
    user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    language_id INTEGER NOT NULL REFERENCES languages(id) ON DELETE CASCADE,
    is_active   BOOLEAN NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL,
    PRIMARY KEY (user_id, language_id),
    UNIQUE (user_id, language_id)
);

CREATE TABLE user_settings (
    user_id                  INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    native_lang_id           INTEGER NOT NULL REFERENCES languages(id) ON DELETE RESTRICT,
    interface_lang_id        INTEGER NOT NULL REFERENCES languages(id) ON DELETE RESTRICT,
    learning_intensity       learning_intensity NOT NULL,
    evaluation_mode          evaluation_mode NOT NULL,
    show_hints_on_fails      BOOLEAN NOT NULL,
    daily_study_goal         INTEGER NOT NULL,
    reminder_time            TIME,
    streak_reminders_enabled BOOLEAN NOT NULL,
    show_translations        BOOLEAN NOT NULL,
    show_images              BOOLEAN NOT NULL,
    show_synonyms            BOOLEAN NOT NULL,
    show_part_of_speech      BOOLEAN NOT NULL,
    auto_play_audio          BOOLEAN NOT NULL,
    new_items_per_day_limit  INTEGER NOT NULL,
    new_items_per_session    INTEGER NOT NULL,
    retention_priority       retention_priority NOT NULL,
    max_review_load_per_day  INTEGER,
    updated_at               TIMESTAMPTZ,
    created_at               TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE user_stats_total (
    user_id               INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    language_id           INTEGER NOT NULL REFERENCES languages(id) ON DELETE RESTRICT,
    total_seconds         NUMERIC(12,2) NOT NULL CHECK (total_seconds >= 0),
    total_words           INTEGER NOT NULL CHECK (total_words >= 0),
    last_recalculated_at  TIMESTAMPTZ,
    PRIMARY KEY (user_id, language_id)
);

CREATE TABLE item_quality_metrics (
    item_id             INTEGER PRIMARY KEY REFERENCES items(id) ON DELETE CASCADE,
    learner_count       INTEGER NOT NULL,
    sample_size         INTEGER NOT NULL,
    avg_ease_factor     FLOAT NOT NULL,
    global_success_rate FLOAT NOT NULL,
    avg_interval        FLOAT NOT NULL,
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE item_synonym_terms (
    id          SERIAL PRIMARY KEY,
    item_id     INTEGER NOT NULL REFERENCES items(id) ON DELETE CASCADE,
    language_id INTEGER NOT NULL REFERENCES languages(id) ON DELETE CASCADE,
    term        TEXT NOT NULL,
    UNIQUE (item_id, term)
);
CREATE INDEX idx_item_synonym_terms_lang ON item_synonym_terms (language_id, term);

CREATE TABLE study_sessions (
    id              BIGSERIAL PRIMARY KEY,
    user_id         INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    set_id          INTEGER REFERENCES sets(id) ON DELETE CASCADE,
    source_lang_id  INTEGER REFERENCES languages(id) ON DELETE SET NULL,
    started_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    ended_at        TIMESTAMPTZ,
    status          session_status_type NOT NULL,
    correct_count   INTEGER NOT NULL,
    incorrect_count INTEGER NOT NULL,
    total_time_ms   INTEGER NOT NULL,
    items_reviewed  INTEGER NOT NULL
);
CREATE INDEX idx_study_sessions_user ON study_sessions (user_id, started_at);
CREATE INDEX idx_study_sessions_active ON study_sessions (user_id, status);

CREATE TABLE study_reviews (
    id            BIGSERIAL PRIMARY KEY,
    session_id    BIGINT NOT NULL REFERENCES study_sessions(id) ON DELETE CASCADE,
    user_id       INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    item_id       INTEGER NOT NULL REFERENCES items(id) ON DELETE CASCADE,
    language_id   INTEGER NOT NULL REFERENCES languages(id) ON DELETE RESTRICT,
    was_correct   BOOLEAN,
    response_time INTEGER,
    reviewed_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_study_reviews_session ON study_reviews (session_id);
CREATE INDEX idx_study_reviews_user_item ON study_reviews (user_id, item_id);

CREATE TABLE user_progress (
    user_id        INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    item_id        INTEGER NOT NULL REFERENCES items(id) ON DELETE CASCADE,
    ease_factor    FLOAT NOT NULL,
    interval       INTEGER NOT NULL,
    repetitions    INTEGER NOT NULL,
    lapsed_attempts INTEGER NOT NULL,
    last_reviewed  TIMESTAMPTZ,
    next_review    TIMESTAMPTZ NOT NULL,
    PRIMARY KEY (user_id, item_id)
);
CREATE INDEX idx_progress_due ON user_progress (user_id, next_review, item_id);

CREATE TABLE user_set_library (
    user_id      INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    set_id       INTEGER NOT NULL REFERENCES sets(id) ON DELETE CASCADE,
    added_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_opened_at TIMESTAMPTZ,
    is_pinned    BOOLEAN NOT NULL,
    PRIMARY KEY (user_id, set_id)
);
CREATE INDEX idx_user_set_library_pinned ON user_set_library (user_id, is_pinned, added_at);
CREATE INDEX idx_user_set_library_recent ON user_set_library (user_id, last_opened_at)
    WHERE last_opened_at IS NOT NULL;

CREATE TABLE pending_sessions (
    id                BIGSERIAL PRIMARY KEY,
    session_id        BIGINT NOT NULL UNIQUE REFERENCES study_sessions(id) ON DELETE CASCADE,
    user_id           INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    raw_events_json   JSONB NOT NULL,
    session_state_json JSONB NOT NULL,
    saved_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    recovered         BOOLEAN NOT NULL
);
CREATE INDEX idx_pending_sessions_user ON pending_sessions (user_id, recovered);

-- ============================================================
-- TRIGGERS
-- ============================================================

CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_items_updated_at
    BEFORE UPDATE ON items FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER trg_sets_updated_at
    BEFORE UPDATE ON sets FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER trg_translations_updated_at
    BEFORE UPDATE ON translations FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER trg_item_synonym_terms_updated_at
    BEFORE UPDATE ON item_synonym_terms FOR EACH ROW EXECUTE FUNCTION set_updated_at();
