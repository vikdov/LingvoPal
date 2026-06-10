# Experiment 04 — Database Migrations (Alembic)

**Branch:** `experiment/04-migrations`
**Measures:** upgrade time (s), downgrade time (s), rollback correctness (yes/no)

---

## Pre-conditions (once, untimed)

```bash
git checkout experiment/04-migrations
cd ~/code/LingvoPal/backend
ls alembic.ini && echo "EXISTS"
uv sync --quiet
set -a && source ~/code/LingvoPal/.env && set +a
uv run alembic current     # verify DB connection
uv run alembic history     # confirm 4-revision chain ends at b3c4d5e6f7a8 (head)
```

Expected history (base → head):
```
928f022370b7 → 497834a509ad → fef8054c1463 → b3c4d5e6f7a8 (head)
```

---

## Phase 1 — Upgrade time (3 runs)

### Teardown between runs

```bash
cd ~/code/LingvoPal
docker compose down -v
docker compose up -d --wait postgres redis
cd backend
```

### Timed run (from `backend/`):

```bash
time uv run alembic upgrade head
```

Record: `real` from each run. Median → Appendix A.4 upgrade row.

---

## Phase 2 — Downgrade time (3 runs)

Starting state: after Phase 1 Run 3, DB is fully migrated (at head). Use that as Run 1.

Per run (×3):

```bash
# Ensure at head (untimed)
uv run alembic upgrade head

# Timed
time uv run alembic downgrade -1
```

Record: `real` from each run. Median → Appendix A.4 downgrade row.

After Run 3, leave DB in downgraded state — proceed directly to Phase 3.

---

## Phase 3 — Rollback verification (once, binary)

```bash
set -a && source ~/code/LingvoPal/.env && set +a

PGPASSWORD=$DATABASE_PASSWORD psql -h localhost -p "$DATABASE_PORT" \
  -U "$DATABASE_USER" -d "$DATABASE_NAME" \
  -c "\d users" | grep pending_email
```

**Expected:** no output (column absent → rollback confirmed).

```bash
uv run alembic current
# Expected: fef8054c1463 (one revision before pending_email migration)
```

Record: Yes (column absent) / No → §4.4.3 rollback correctness.
