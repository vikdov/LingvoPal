Package manager - uv
## 1️⃣ Exact function of each file (from top to bottom)

---

## `backend/app/main.py`

**Purpose:** Application bootstrap

**What it does**

* Creates `FastAPI()` instance
* Loads settings
* Includes routers (`auth`, `items`, `practice`, etc.)
* Configures CORS, middleware
* Starts the app

**What it must NOT do**

* No business logic
* No DB queries
* No JWT code

✅ Correct place for this file

---

## `app/core/`

### `config.py`

**Purpose:** Central configuration

**Contains**

* Environment variables (DB URL, JWT secret, token expiry)
* App mode (dev/prod)
* Settings class (`BaseSettings`)

**Used by**

* `main.py`
* `security.py`
* database session

✅ Required for MVP

---

### `security.py`

**Purpose:** Security primitives

**Contains**

* Password hashing (`bcrypt`, `argon2`)
* JWT encode/decode
* Token verification helpers

**Does NOT**

* Call DB
* Know about FastAPI routes

✅ Required for MVP

---

### `dependencies.py`

**Purpose:** Shared FastAPI dependencies

**Contains**

* `get_db()`
* `get_current_user()`
* `get_current_active_user()`

**Used by**

* routes only

This is the **bridge** between FastAPI and your business logic.

✅ Required

---

## `app/database/`

### `session.py`

**Purpose:** DB session lifecycle

**Contains**

* SQLAlchemy engine
* `SessionLocal`
* session generator for FastAPI

✅ Required

---

### `base.py`

**Purpose:** SQLAlchemy Base

**Contains**

* `Base = declarative_base()`
* Possibly shared mixins (timestamps, soft delete)

Used by **all models**.

✅ Required

---

## `app/models/` (SQLAlchemy – persistence layer)

These files **map directly to your DB schema**.
Each file = one table (+ relationships).

### `user.py`

* users
* relationships: sets, progress, stats

### `language.py`

* languages reference table

### `item.py`

* vocabulary item (source word)
* language, creator, visibility

### `translation.py`

* translated terms
* FK to item

### `set.py`

* vocabulary sets
* set_items association

### `progress.py`

* spaced repetition state per user + translation

### `daily_stats.py`

* daily aggregates (correct, time, new words)

**Rules**

* NO business logic
* NO FastAPI imports
* Relationships only

✅ All are necessary for your MVP scope
✅ Excellent coverage

---

## `app/schemas/` (Pydantic – API contract)

These define **what goes in and out of your API**.

### `auth.py`

* Login request
* Token response

### `user.py`

* UserCreate
* UserResponse
* UserSettingsUpdate

### `item.py`

* ItemCreate
* ItemResponse

### `translation.py`

* TranslationCreate
* TranslationResponse

### `set.py`

* SetCreate
* SetResponse
* AddItemToSet

### `practice.py`

* PracticeSessionStart
* AnswerSubmission
* PracticeResult

### `stats.py`

* DailyStatsResponse
* DashboardStatsResponse

**Purpose**

* Validation
* API documentation
* Decoupling DB from API

✅ Required
✅ Well split

---

## `app/repositories/` (DB access layer)

**Golden rule:**

> Repositories talk to SQLAlchemy, nothing else.

### `item_repo.py`

* get/create/search items
* filtering by language, visibility

### `translation_repo.py`

* fetch translations
* link to items

### `set_repo.py`

* CRUD sets
* manage set_items junction

### `progress_repo.py`

* read/update spaced repetition state

### `user_repo.py`

* users
* settings

This layer:

* keeps SQL out of services
* makes testing easier

✅ Not strictly required for MVP
⚠️ But **very good design choice**
I’d keep it.

---

## `app/services/` (business logic core)

This is where your app **actually lives**.

### `auth_service.py`

* register user
* authenticate
* issue tokens

### `practice_service.py`

* build practice sessions
* select due cards
* evaluate answers
* update progress & stats

### `spaced_repetition.py`

* SM-2 (or variant)
* pure logic, no DB

### `item_service.py`

* item creation rules
* visibility logic
* approval workflows (later)

### `stats_service.py`

* update daily stats
* aggregate dashboard data

**Rules**

* No FastAPI
* No raw SQL
* Coordinates repositories

✅ This is the **heart of the MVP**
✅ Very good separation

---

## `app/routes/` (HTTP layer)

Routes:

* Parse request
* Call service
* Return schema

### `auth.py`

* `/login`
* `/register`
* `/refresh`

### `users.py`

* `/me`
* `/settings`

### `practice.py`

* `/practice/start`
* `/practice/answer`
* `/practice/summary`

### `items.py`

* CRUD vocabulary

### `sets.py`

* CRUD sets
* add/remove items

### `stats.py`

* dashboard endpoints

✅ Perfectly aligned with your schema & services

---

## `app/utils/errors.py`

**Purpose**

* Custom exceptions
* Domain errors (`ItemNotFound`, `UnauthorizedAction`)
* Mapped to HTTP responses

✅ Optional but very clean
Good for MVP+

---

## `tests/`

### `test_practice.py`

* session flow
* answering logic

### `test_items.py`

* item creation
* visibility

### `test_sets.py`

* set logic

### `test_spaced_repetition.py`

* SM-2 correctness

✅ Excellent test focus
Even one or two tests per file is enough for MVP

---

## Root-level files

### `migrations/`

* Alembic versions
* DB evolution

✅ Optional for MVP
But **very good to include early**

---

### `Dockerfile`

* Build backend image

### `docker-compose.yml`

* API + DB locally

### `requirements.txt`

* Runtime deps

### `pyproject.toml`

* Tooling (black, ruff, mypy)

### `README.md`

* How to run
* What the app does

✅ All correct

---

## 2️⃣ Is this enough for an MVP?

### ✅ YES — fully sufficient for:

* Auth
* Vocabulary items
* Translations
* Sets
* Spaced repetition
* Practice sessions
* Stats dashboard
* Public/private content

This is **already above average MVP quality**.

---

## 3️⃣ What’s optional / missing / postponeable

### 🟡 Optional (can add later)

* `admin` routes
* moderation/approval workflow
* activity log table
* notifications
* search indexing

---

### 🔴 One thing I’d ADD (small but important)

#### `app/routes/__init__.py`

and optionally

#### `app/services/__init__.py`

Not strictly required in Python 3.11+, but:

* Improves IDE support
* Makes imports cleaner
* Avoids edge cases
