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
| **Practice** | Cloze sentences, manual text input, confidence override, session summary, unfinished-session resume |
| **Spaced Repetition** | SM-2 with lapsed-card recovery, intensity multiplier, 6-hour new-word phase |
| **Sets** | Create/edit vocab sets, public/private visibility, Anki import, `.lpset` bundle export/import |
| **AI Enrichment** | Item suggestions and enrichment via Groq (Llama 3.3), spaCy lemmatization, Unsplash image search |
| **Discovery** | Browse and filter public sets by language pair, level, source |
| **Stats** | Daily reviews, accuracy trends, activity charts |
| **Admin** | Moderation queue for community-submitted content |
| **Settings** | Interface language, target language, theme, account management, email change/verification |

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
- **PostgreSQL 16** — primary database (Neon in production)
- **Redis** — caching and session state
- **Docker Compose** — local dev environment
- **GitHub Actions** — CI + CD pipelines, CodeQL scanning
- **Render** (backend) + **Vercel** (frontend) — production hosting

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
- Python 3.13+ with [uv](https://docs.astral.sh/uv/)

### One-command setup

```bash
./scripts/setup.sh
```

Idempotent — checks prerequisites, starts services, installs dependencies, and applies migrations. Or do it manually:

### 1. Start infrastructure

```bash
docker compose up -d
```

Starts PostgreSQL 16, Redis, MinIO (S3), Mailpit (SMTP), pgAdmin, and RedisInsight.

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

## CI/CD

**CI** (`.github/workflows/ci.yml`) runs on every push: lint (ruff, eslint, tsc), tests (pytest, vitest), migration check, Docker builds, SAST (bandit), dependency audits, and secret scanning — for both stacks. CodeQL runs as a separate workflow.

**CD** (`.github/workflows/cd.yml`) owns the full commit → live path on `main`:

```
migrate (Neon) → deploy backend (Render) + deploy frontend (Vercel) → smoke (/health)
```

Migration runs first and gates the deploys, so a failed migration blocks the release instead of letting new code boot against an unmigrated schema. Frontend release is health-gated behind backend smoke.

**Pre-commit hooks** mirror CI locally: ruff, eslint, tsc, bandit, gitleaks, and standard hygiene checks.

Pipeline failures and fixes are recorded in [`docs/ci-incidents.md`](docs/ci-incidents.md).

---

## Spaced Repetition

`backend/app/services/sm2_engine.py` — pure SM-2 implementation, no side effects.

Key behaviors:
- New words: 6-hour initial interval before entering full SR schedule
- Lapsed cards: short retry loop (5–120 min) before resuming normal intervals
- User intensity multiplier: adjusts interval growth per user preference
- Confidence override: user can flag "knew it" / "didn't know it" regardless of typed answer

---

## Project Status

MVP v0.1 — core learning loop is complete, deployed, and functional.

- [x] Auth + sessions
- [x] Practice loop (cloze → answer → SM-2 → reschedule)
- [x] Vocabulary sets + Anki import + `.lpset` export/import
- [x] Public content discovery
- [x] Stats dashboard
- [x] Admin moderation queue
- [x] Email delivery (SMTP)
- [x] CI/CD pipeline (GitHub Actions)
- [x] Production deployment (Render + Vercel + Neon)

---

## Design Philosophy

> Type it. Don't tap it.

LingvoPal intentionally removes passive recognition. Writing activates different recall pathways than selecting from options. The app optimizes for long-term retention over short-term engagement metrics.

- Active recall over recognition
- Writing over tapping
- Quality content over quantity
- Focused method over feature sprawl

---

## Academic Context

LingvoPal serves as the primary case study for a bachelor's thesis:

> **"Impact of DevOps Practices on Software Delivery Efficiency and Business Performance"**

### Core Thesis Argument

DevOps is not a technology stack to install — it is a corrective toolkit applied to specific bottlenecks. The right question is never "which DevOps tools exist?" but "what hurts most right now, and which practice fixes it?"

Adopting tools without identifying the underlying inefficiency produces **Cargo Cult DevOps**: the rituals are followed, the tools are running, but no real friction is removed.

The thesis demonstrates the alternative: each practice was adopted when a specific bottleneck made it necessary, and gains compound as practices stack.

### DevOps Practices Inventory

| Practice | Tool | Status | Bottleneck it solves |
|---|---|---|---|
| Version control conventions | Conventional commits + feature branches | Present | Change traceability, rework visibility |
| Dependency management | `uv` + lockfile | Present | Reproducible installs, fast setup |
| Containerization | Docker Compose | Present | Environment parity, service orchestration |
| Environment automation | `scripts/setup.sh` | Present | Onboarding friction, manual steps |
| Database migrations | Alembic | Present | Schema safety, rollback capability |
| Test automation | pytest + Vitest | Present | Defect detection before integration |
| Security automation | pre-commit (bandit, gitleaks) + CodeQL + dependency audits | Present | Vulnerabilities and secrets caught before merge |
| Continuous Integration | GitHub Actions | Present | Automated validation on every push |
| Continuous Deployment | GitHub Actions → Render + Vercel + Neon | Present | Manual deploy eliminated, lead time reduced |
| Observability | Structured logging | Deferred | No production users yet — adding now = Cargo Cult |
| IaC / Orchestration | — | Deferred | Single server — no infra drift problem at this scale |

### Research Methodology

A controlled experiment reconstructs the adoption sequence on isolated git branches. Each practice is introduced one at a time; metrics are recorded before and after each addition to isolate its individual contribution.

```
experiment/00-baseline     ← no DevOps practices
experiment/01-vcs          ← + conventional commits & branching
experiment/02-deps         ← + uv + lockfile
experiment/03-docker       ← + Docker Compose
experiment/04-migrations   ← + Alembic
experiment/05-scripts      ← + setup.sh
experiment/06-tests        ← + pytest + Vitest
experiment/07-security     ← + pre-commit hooks, bandit, gitleaks
experiment/08-ci           ← + GitHub Actions CI
experiment/09-deploy       ← + CD pipeline + live deployment
```

Metrics are practice-specific — each practice is evaluated on the capability it introduces, not a single universal measure:

| Branch | Metric |
|---|---|
| `00-baseline` | Setup time (min), manual step count |
| `01-vcs` | `fix:`/`feat:` commit ratio, branch lifetime |
| `02-deps` | Install time, reproducibility |
| `03-docker` | Setup time delta, eliminated manual service steps |
| `04-migrations` | Migration apply + rollback time |
| `05-scripts` | Step count: manual vs scripted |
| `06-tests` | Time-to-detect injected bug, coverage % |
| `07-security` | Secrets/vulns caught pre-commit vs post-hoc |
| `08-ci` | Time-to-feedback (min), manual steps eliminated |
| `09-deploy` | Lead time commit→live (min), deploy step count |

### Compounding Effect

Practices in isolation give linear gains. Practices in combination give superlinear gains:

- Tests alone — catches bugs locally, sometimes skipped
- Tests + CI — catches bugs automatically on every push, never skipped
- Tests + CI + CD — catches bugs and ships fixes with a single `git push`

Each layer multiplies the value of the one before it.

### Deferred Practices

The following practices are understood but intentionally not yet adopted — the bottlenecks they solve have not materialized at current project scale:

| Practice | Adopted when |
|---|---|
| Kubernetes / orchestration | Multi-instance traffic scaling required |
| Feature flags | Multiple active user segments need independent releases |
| Full observability stack (Sentry, Prometheus) | First real production user complaints |
| Load testing | Pre-launch performance SLA defined |
| Secret management (Vault) | Multi-team credential access required |
| IaC (Terraform) | Multi-environment infra drift becomes a real problem |

Deferring these is the correct DevOps decision at MVP stage. Adopting them now would be Cargo Cult.
