# Experiment 03 — Docker Compose Infrastructure

**Branch:** `experiment/03-docker`
**Measures:** service startup time (s), full onboarding time (s), step count

Services brought up: postgres, redis, pgadmin, redisinsight, mailpit, minio.

---

## Pre-conditions (once, untimed — one-time per machine)

- Docker Engine installed and running: `docker info` exits 0
- Node.js + npm installed; host `psql` client available

```bash
git checkout experiment/03-docker

# Branch predates scripts/postgres.conf — required by docker-compose.yml:
mkdir -p scripts
git show main:scripts/postgres.conf > scripts/postgres.conf

# Create .env at repo root:
cp backend/.env.example .env
# Edit .env — confirm: DATABASE_USER, DATABASE_PASSWORD, DATABASE_NAME,
#                       DATABASE_PORT=5432, REDIS_PORT=6379
# Append to .env:
cat >> .env << 'EOF'
PGADMIN_EMAIL=admin@lingvopal.local
PGADMIN_PASSWORD=admin
PGADMIN_PORT=5050
S3_ACCESS_KEY=minioadmin
S3_SECRET_KEY=minioadmin
EOF
```

---

## Phase 1 — Service startup time (3 runs)

### Teardown between runs

```bash
pkill -f uvicorn 2>/dev/null; pkill -f vite 2>/dev/null
docker compose down -v
rm -rf frontend/node_modules backend/.venv
```

### Timed run — start stopwatch:

```bash
time docker compose up postgres redis pgadmin redisinsight mailpit minio --wait
```

**Verification after each run:**

```bash
docker compose ps   # postgres and redis must show (healthy)
```

Record: `real` from each run. Median → Appendix A.3 Docker services row.

**Cold build (informational, once — not included in median):**

```bash
docker compose down --rmi all -v
docker compose build --no-cache
time docker compose up postgres redis pgadmin redisinsight mailpit minio --wait
```

---

## Phase 2 — Full onboarding time (3 runs)

### Teardown between runs

```bash
pkill -f uvicorn 2>/dev/null; pkill -f vite 2>/dev/null
cd ~/code/LingvoPal
docker compose down -v
rm -rf frontend/node_modules backend/.venv
```

### Timed run — start stopwatch, then type each step:

```bash
# Step 1
cd ~/code/LingvoPal && git checkout experiment/03-docker

# Step 2
set -a && source .env && set +a

# Step 3
docker compose up postgres redis pgadmin redisinsight mailpit minio --wait

# Step 4
PGPASSWORD=$DATABASE_PASSWORD psql -h localhost -p $DATABASE_PORT \
  -U $DATABASE_USER -d $DATABASE_NAME \
  -v ON_ERROR_STOP=1 < backend/schema.sql

# Step 5
PGPASSWORD=$DATABASE_PASSWORD psql -h localhost -p $DATABASE_PORT \
  -U $DATABASE_USER -d $DATABASE_NAME \
  -v ON_ERROR_STOP=1 < backend/seed.sql

# Step 6
cd backend && uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &

# Step 7
cd ../frontend && npm install

# Step 8
npm run dev
```

**Stop** when: login as `user@example.com` succeeds in browser.

Record: `real` time each run. Median → §4.3.3 and Appendix A.3.

---

## Phase 3 — Step count

8 steps (Steps 1–8 above, including the single `docker compose up` that brings up all six services) vs Experiment 00 baseline (12 steps, including its four manual service-provisioning actions) = −4 steps.

Record: 8 → §4.3.3 step count.
