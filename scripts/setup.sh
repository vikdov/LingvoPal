#!/bin/bash
# scripts/setup.sh
# Complete setup with proper shell variable handling and idempotent seeding

set -e

echo "Setting up LingvoPal development environment..."

# ============================================================================
# 1. Verify root .env exists
# ============================================================================

if [ ! -f .env ]; then
  echo "Creating .env from .env.example..."
  cp .env.example .env
else
  echo "Existing .env found"
fi

# ============================================================================
# 2. Load environment variables safely
# ============================================================================
# Use set -a / set +a to export all variables
# Use sed to strip carriage returns (handles Windows CRLF line endings)

echo "Loading environment variables..."
set -a
source <(sed 's/\r$//' .env)
set +a

# ============================================================================
# 3. Verify critical variables
# ============================================================================

echo "Verifying environment variables..."

required_vars=(
  "DATABASE_USER"
  "DATABASE_PASSWORD"
  "DATABASE_HOST"
  "DATABASE_PORT"
  "DATABASE_NAME"
  "ENV"
)

for var in "${required_vars[@]}"; do
  if [ -z "${!var}" ]; then
    echo "ERROR: $var is not set in .env"
    exit 1
  fi
done

echo "All required variables are set"

# ============================================================================
# 4. Start Docker services
# ============================================================================

echo "Starting Docker services..."
docker compose up -d postgres

echo "Waiting for PostgreSQL to be ready..."
attempt=0
max_attempts=30

until docker compose exec -T postgres pg_isready -U "$DATABASE_USER" -d "$DATABASE_NAME" >/dev/null 2>&1; do
  attempt=$((attempt + 1))
  if [ $attempt -ge $max_attempts ]; then
    echo "ERROR: PostgreSQL failed to start after $max_attempts attempts"
    docker compose logs postgres
    exit 1
  fi
  echo "  Waiting... (attempt $attempt/$max_attempts)"
  sleep 2
done

echo "PostgreSQL is ready"

# ============================================================================
# 5. Backend setup
# ============================================================================

echo "Setting up backend..."

cd backend

# Create virtual environment if needed
if [ ! -d .venv ]; then
  echo "  Creating virtual environment..."
  uv venv
fi

# Activate virtual environment for this script
. .venv/bin/activate

echo "  Syncing dependencies..."
uv sync

# ============================================================================
# 6. Database migrations
# ============================================================================

echo "Running database migrations..."

# Migrations use config.py which reads from ../.env
# docker-compose.yml anchor ensures reliable root detection
uv run alembic upgrade head

if [ $? -ne 0 ]; then
  echo "ERROR: Database migrations failed"
  exit 1
fi

# ============================================================================
# 7. Seed initial data (idempotent)
# ============================================================================

echo "Seeding database with initial data..."

# Set SEED_DB=false to skip seeding (useful in CI/CD after first run)
if [ "${SEED_DB:-true}" = "true" ]; then
  uv run python ../scripts/seed_db.py

  if [ $? -ne 0 ]; then
    echo "WARNING: Database seeding failed (this is non-critical)"
  fi
else
  echo "  Skipping seed (SEED_DB=false)"
fi

cd ..

# ============================================================================
# 8. Frontend setup
# ============================================================================

echo "Setting up frontend..."

cd frontend

# Create .env if it doesn't exist
if [ ! -f .env ]; then
  echo "  Creating frontend/.env..."
  cat >.env <<'EOF'
VITE_API_URL=http://localhost:8000/api/v1
VITE_APP_TITLE=LingvoPal (Development)
VITE_ENABLE_ANALYTICS=false
VITE_ENABLE_DEBUG_PANEL=true
EOF
fi

# Install dependencies if needed
if [ ! -d node_modules ]; then
  echo "  Installing frontend dependencies..."
  npm install
fi

cd ..

# ============================================================================
# 9. Final information
# ============================================================================

echo ""
echo "Setup completed successfully"
echo ""
echo "Environment Configuration:"
echo "  ENV: $ENV"
echo "  Database User: $DATABASE_USER"
echo "  Database Host: $DATABASE_HOST (Docker Compose)"
echo "  Database Port: $DATABASE_PORT"
echo "  Database Name: $DATABASE_NAME"
echo ""
echo "IMPORTANT - For local development:"
echo "  Backend will automatically use localhost (from .env.development)"
echo "  This allows uvicorn to connect to PostgreSQL running in Docker"
echo ""
echo "Service URLs:"
echo "  Backend API: http://localhost:8000"
echo "  API Documentation: http://localhost:8000/docs"
echo "  Frontend: http://localhost:5173"
echo "  pgAdmin (if enabled): http://localhost:5050"
echo ""
echo "To start development:"
echo ""
echo "  Terminal 1 - Backend:"
echo "    cd backend"
echo "    . .venv/bin/activate"
echo "    uvicorn app.main:app --reload"
echo ""
echo "  Terminal 2 - Frontend:"
echo "    cd frontend"
echo "    npm run dev"
echo ""
echo "To run tests:"
echo "  cd backend"
echo "  . .venv/bin/activate"
echo "  pytest -v"
echo ""
echo "To see database in psql:"
echo "  psql postgresql://lingvopal_user:***@localhost:5432/lingvopal_db"
echo ""
echo "To reset everything:"
echo "  docker compose down -v && ./scripts/setup.sh"
echo ""
echo "To run setup without seeding (e.g., on existing database):"
echo "  SEED_DB=false ./scripts/setup.sh"
echo ""
