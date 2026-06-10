# Experiment 05 — Automation Scripts

**Branch:** `experiment/05-scripts`
**Measures:** step count, full onboarding time (s), idempotency (yes/no)

---

## Phase 1 — Step count (once, untimed)

```bash
# Step 1
git checkout experiment/05-scripts

# Step 2
./scripts/setup.sh

# Step 3
cd backend && uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &

# Step 4
cd ../frontend && npm run dev
```

Record: 4 steps (vs 8 in Experiment 03) → §4.5.3
Prerequisites checked by `setup.sh`: docker, uv, npm, DATABASE_HOST sanity, idempotency.

---

## Phase 2 — Full onboarding time (3 runs)

### Teardown between runs

```bash
pkill -f uvicorn 2>/dev/null; pkill -f vite 2>/dev/null
docker compose -f ~/code/LingvoPal/docker-compose.yml down -v
rm -rf ~/code/LingvoPal/backend/.venv
rm -rf ~/code/LingvoPal/frontend/node_modules
cd ~/code/LingvoPal
```

### Timed run — start stopwatch:

```bash
# Step 1
cd ~/code/LingvoPal && git checkout experiment/05-scripts

# Step 2
./scripts/setup.sh

# Step 3
cd backend && uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &

# Step 4
cd ../frontend && npm run dev
```

**Stop** when: `npm run dev` prints `Local: http://localhost:5173`.

Record: `real` time each run. Median → Appendix A.3 scripts row.

---

## Phase 3 — Idempotency (once, not timed)

Immediately after Phase 2 Run 3, without teardown:

```bash
./scripts/setup.sh
```

**Expected:** exits 0 and prints a line containing `✓ Setup complete`.

Record: Yes / No → §4.5.3
