# LingvoPal

**Writing-first language learning app built on active recall and spaced repetition.**

Most language apps let you tap the right answer. LingvoPal makes you type it — inside a real sentence, from memory. That friction is the point.

---

## How it works

1. A sentence appears with one word missing
2. You type the answer (no hints, no multiple choice)
3. Immediate feedback — correct or not
4. SM-2 algorithm schedules the next review based on your performance

Active recall + contextual writing + spaced repetition in one focused loop.

---

## Features

| Area | What's implemented |
|---|---|
| **Auth** | Email/password signup, JWT sessions, password reset |
| **Practice** | Cloze sentences, manual text input, confidence override, session summary |
| **Spaced Repetition** | SM-2 with lapsed-card recovery, intensity multiplier, 6-hour new-word phase |
| **Sets** | Create/edit vocab sets, public/private visibility, Anki import |
| **Discovery** | Browse and filter public sets by language pair, level, source |
| **Stats** | Daily reviews, accuracy trends, activity charts |
| **Admin** | Moderation queue for community-submitted content |
| **Settings** | Interface language, target language, theme, account management |

---

## Tech Stack

### Frontend
- **React 19** + **TypeScript** — Vite 8 build
- **Tailwind CSS v4** — CSS-first, no config file
- **shadcn/ui** — accessible component primitives
- **Zustand 5** — lightweight feature-scoped state
- **TanStack Query 5** — server state, caching, mutations
- **Recharts** — progress and activity charts

### Backend
- **FastAPI** — async Python API, auto-generated OpenAPI docs
- **SQLAlchemy 2.0** — async ORM with `asyncpg`
- **Pydantic v2** — schema validation and settings
- **Redis** — session buffering, SRS queue
- **Alembic** — database migrations
- **uv** — fast Python package manager

### Infrastructure
- **PostgreSQL 16** — primary database
- **Redis** — caching and session state
- **Docker Compose** — local dev environment

---

## Architecture

### Backend — strict layered separation

```
Routes → Services → Repositories → Models
```

- **Routes** (`app/routes/`) — parse HTTP, call services, map exceptions to status codes. No logic.
- **Services** (`app/services/`) — all business logic, transaction boundaries, domain exceptions.
- **Repositories** (`app/repositories/`) — raw ORM queries only.
- **Models** (`app/models/`) — SQLAlchemy table definitions.
- **Schemas** (`app/schemas/`) — Pydantic request/response contracts.

### Frontend — feature-based structure

```
src/features/{feature}/
  api/          # TanStack Query hooks + fetch calls
  components/   # Feature-specific UI
  hooks/        # Custom hooks
  store/        # Zustand slice
  types/        # TypeScript types
  views/        # Page-level components
```

Shared UI primitives live in `src/components/ui/`. Features export public APIs via `index.ts` barrels.

---

## Getting Started

### Prerequisites

- Docker + Docker Compose
- Node.js 20+
- Python 3.12+ with [uv](https://docs.astral.sh/uv/)

### 1. Start infrastructure

```bash
docker compose up -d
```

Starts PostgreSQL 16, Redis, and pgAdmin.

### 2. Backend

```bash
cd backend
uv sync                              # Install dependencies
uv run alembic upgrade head          # Apply migrations
uvicorn app.main:app --reload        # Dev server → http://localhost:8000
```

API docs available at `http://localhost:8000/docs`.

### 3. Frontend

```bash
cd frontend
npm install
npm run dev                          # Dev server → http://localhost:5173
```

### Environment

Copy `.env.example` to `.env` and fill in values. The config loader resolves `.env` → `.env.{ENV}` → `.env.local`.

---

## Spaced Repetition

`backend/app/services/spaced_repetition.py` — pure SM-2 implementation, no side effects.

Key behaviors:
- New words: 6-hour initial interval before entering full SR schedule
- Lapsed cards: short retry loop (5–120 min) before resuming normal intervals
- User intensity multiplier: adjusts interval growth per user preference
- Confidence override: user can flag "knew it" / "didn't know it" regardless of typed answer

---

## Project Status

MVP v0.1 — core learning loop is complete and functional.

- [x] Auth + sessions
- [x] Practice loop (cloze → answer → SM-2 → reschedule)
- [x] Vocabulary sets + Anki import
- [x] Public content discovery
- [x] Stats dashboard
- [x] Admin moderation queue
- [ ] Email delivery (SMTP config required)
- [ ] CI/CD pipeline
- [ ] Production deployment

---

## Design Philosophy

> Type it. Don't tap it.

LingvoPal intentionally removes passive recognition. Writing activates different recall pathways than selecting from options. The app optimizes for long-term retention over short-term engagement metrics.

- Active recall over recognition
- Writing over tapping  
- Quality content over quantity
- Focused method over feature sprawl
