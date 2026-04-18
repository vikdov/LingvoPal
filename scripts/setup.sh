#!/usr/bin/env bash
# scripts/setup.sh — LingvoPal development environment setup
# Run from the project root: ./scripts/setup.sh

set -euo pipefail

# ── Output helpers ────────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; BOLD='\033[1m'; NC='\033[0m'
ok()   { echo -e "  ${GREEN}✓${NC} $*"; }
info() { echo -e "  ${CYAN}→${NC} $*"; }
warn() { echo -e "  ${YELLOW}⚠${NC} $*"; }
die()  { echo -e "\n  ${RED}✗ ERROR:${NC} $*\n" >&2; exit 1; }
step() { echo -e "\n${BOLD}${CYAN}──${NC} $*"; }

# ── Verify project root ───────────────────────────────────────────────────────
[[ -f docker-compose.yml ]] || die "Run this script from the project root (where docker-compose.yml lives)."

# ── Prerequisites ─────────────────────────────────────────────────────────────
step "Checking prerequisites..."
command -v docker >/dev/null 2>&1 || die "docker not found — install Docker Desktop."
command -v uv     >/dev/null 2>&1 || die "uv not found — install: curl -LsSf https://astral.sh/uv/install.sh | sh"
command -v npm    >/dev/null 2>&1 || die "npm not found — install Node.js from https://nodejs.org"
ok "docker, uv, npm found"

# ── Environment file ──────────────────────────────────────────────────────────
step "Checking environment file..."
if [[ ! -f .env ]]; then
  cp .env.example .env
  info "Created .env from .env.example — review credentials before first use"
else
  ok ".env exists"
fi

# Load vars: strip CR (Windows CRLF), skip comments and blank lines
set -a
# shellcheck disable=SC1090
source <(grep -v '^\s*#' .env | grep -v '^\s*$' | sed 's/\r$//')
set +a

# ── Verify required variables ─────────────────────────────────────────────────
step "Verifying required environment variables..."
required_vars=(DATABASE_USER DATABASE_PASSWORD DATABASE_HOST DATABASE_PORT DATABASE_NAME REDIS_PORT ENV)
for var in "${required_vars[@]}"; do
  [[ -n "${!var:-}" ]] || die "$var is not set in .env"
done
ok "All required variables set  (ENV=${ENV})"

# ── Docker services ───────────────────────────────────────────────────────────
step "Starting infrastructure services..."
info "Bringing up postgres + redis (waiting for healthchecks)..."

# --wait blocks until all started services pass their built-in healthchecks.
# No manual polling loop needed — both services declare healthchecks in docker-compose.yml.
docker compose up -d --wait postgres redis

ok "postgres healthy  (port ${DATABASE_PORT})"
ok "redis healthy     (port ${REDIS_PORT})"

# Optional monitoring UIs — not started by default to keep things lightweight
if [[ "${LINGVOPAL_TOOLS:-false}" == "true" ]]; then
  info "Starting pgadmin + redisinsight..."
  docker compose up -d pgadmin redisinsight
  ok "pgadmin      → http://localhost:${PGADMIN_PORT:-5050}"
  ok "redisinsight → http://localhost:5540"
fi

# ── Sanity-check DATABASE_HOST ────────────────────────────────────────────────
# Migrations run on the host, not inside Docker. If DATABASE_HOST is set to a
# Docker service/container name it won't resolve here. Catch this early.
case "${DATABASE_HOST}" in
  localhost|127.0.0.1|0.0.0.0) ;;
  *)
    warn "DATABASE_HOST='${DATABASE_HOST}' looks like a Docker hostname."
    warn "For host-based migrations this must be 'localhost' (Docker exposes postgres on the host port)."
    warn "Set DATABASE_HOST=localhost in .env — docker-compose.yml overrides it inside containers."
    die "Fix DATABASE_HOST in .env then re-run."
    ;;
esac

# ── Backend setup ─────────────────────────────────────────────────────────────
step "Setting up backend..."
cd backend

if [[ ! -d .venv ]]; then
  info "Creating virtual environment..."
  uv venv
fi

info "Syncing dependencies..."
uv sync --quiet
ok "Dependencies synced"

# ── Database migrations ───────────────────────────────────────────────────────
step "Running database migrations..."
# Run alembic locally — config.py reads DATABASE_URL from .env via the
# docker-compose.yml anchor. Do NOT use `docker compose exec app` here:
# the app container is not started for local dev; uvicorn runs on the host.
uv run alembic upgrade head
ok "Migrations applied"

# ── Seed initial data ─────────────────────────────────────────────────────────
if [[ "${SEED_DB:-true}" == "true" ]]; then
  step "Seeding database..."
  # PYTHONPATH=. ensures `app` is importable from backend/ without a package install.
  # seed_db.py was written for Docker (where backend/ is mounted at /app/);
  # PYTHONPATH=. replicates that mapping for local execution.
  PYTHONPATH=. uv run python ../scripts/seed_db.py \
    || warn "Seeding reported errors — data likely already exists, safe to ignore"
else
  step "Skipping seed  (SEED_DB=false)"
fi

cd ..

# ── Frontend setup ────────────────────────────────────────────────────────────
step "Setting up frontend..."
cd frontend

if [[ ! -f .env ]]; then
  cat > .env <<EOF
VITE_API_URL=http://localhost:8000/api/v1
VITE_APP_TITLE=LingvoPal (dev)
EOF
  ok "Created frontend/.env"
else
  ok "frontend/.env exists"
fi

if [[ ! -d node_modules ]]; then
  info "Installing npm dependencies..."
  npm install --silent
  ok "npm install complete"
else
  ok "node_modules present"
fi

cd ..

# ── Done ──────────────────────────────────────────────────────────────────────
echo ""
echo -e "${BOLD}${GREEN}  ✓ Setup complete${NC}   ENV=${CYAN}${ENV}${NC}   DB=${CYAN}${DATABASE_NAME}${NC}"
echo ""
echo -e "  ${BOLD}Terminal 1${NC} — Backend"
echo -e "    ${CYAN}cd backend && uv run uvicorn app.main:app --reload${NC}"
echo ""
echo -e "  ${BOLD}Terminal 2${NC} — Frontend"
echo -e "    ${CYAN}cd frontend && npm run dev${NC}"
echo ""
echo -e "  API docs  http://localhost:8000/docs"
echo -e "  Frontend  http://localhost:5173"
echo ""
echo -e "  Teardown:    docker compose down -v && ./scripts/setup.sh"
echo -e "  No seed:     SEED_DB=false ./scripts/setup.sh"
echo -e "  With UIs:    LINGVOPAL_TOOLS=true ./scripts/setup.sh"
echo ""
