# Experiment 09 — Continuous Deployment

**Branch:** `experiment/09-deploy` | deployed from: `main`
**Measures:** lead time commit→live (min), deployment steps manual vs automated, deployment frequency capability

Pipeline: 5 jobs, strictly sequential —
`migrate (Neon) → deploy-backend (Render) → smoke-backend (/health SHA-match) → deploy-frontend (Vercel) → smoke-frontend (200)`.
CD fires on `push: main` and `v*.*.*` tags only.

> **Branch reality:** `main` already carries `cd.yml` — no merge is needed. Render and Vercel build from `main` HEAD at hook-fire time (not a pushed image). The only timing lever is the PaaS build cache (cold vs warm); branch staleness is irrelevant.

> **Measurement boundary:** elapsed printed inside smoke jobs = hook→healthy window only, excludes the Render/Vercel build queue. The §4.9.3 lead-time figure is the EXTERNAL measure: push timestamp → first `/health` reporting the new commit (`lead_time` helper below).

---

## Pre-conditions

```bash
cd ~/code/LingvoPal
git checkout main
git status        # must be clean
gh auth status
gh secret list    # expect the 9 secrets
```

Provisioning (one-time, not counted in metric #2): Neon (pooled), Upstash, R2 bucket + public access, Gmail App Password; Render (Docker, root `backend/`, health `/health`, Auto-Deploy OFF, `REDIS_SSL=true`, `REDIS_PASSWORD`, strong `SECRET_KEY`, `CORS_ORIGINS`=vercel URL); Vercel (root `frontend/`, `VITE_API_URL=…/api/v1`, `vercel.json git.deploymentEnabled:false`, deploy hook).

---

## Env + timing helpers — paste once per shell

The deploy-hook URLs are write-only secrets — copy from dashboards (Render: Settings → Deploy Hook; Vercel: Settings → Git → Deploy Hooks).

```bash
BE=https://lingvopal.onrender.com
FE=https://FILL-app.vercel.app
RENDER_DEPLOY_HOOK_URL='FILL-from-render-dashboard'
VERCEL_DEPLOY_HOOK_URL='FILL-from-vercel-dashboard'
```

**`cd_wait`** — watch the CD run for the pushed commit; print wall + 5 per-job durations:

```bash
cd_wait() {
  local sha rid=""
  sha=$(git rev-parse HEAD)
  for _ in $(seq 1 40); do
    rid=$(gh run list --workflow cd.yml --branch main --limit 15 \
          --json databaseId,headSha \
          -q "[.[] | select(.headSha==\"$sha\")][0].databaseId")
    [ -n "$rid" ] && break
    sleep 3
  done
  [ -z "$rid" ] && { echo "no CD run for $sha"; return 2; }
  echo "run $rid  (sha ${sha:0:8})"
  gh run watch "$rid" --exit-status; local rc=$?
  gh run view "$rid" --json conclusion,createdAt,updatedAt,jobs -q '
    "conclusion=\(.conclusion)  wall=\((((.updatedAt|fromdateiso8601)-(.createdAt|fromdateiso8601))/60*100|floor)/100) min",
    (.jobs[] | "  \(.conclusion // "running")  \(((((.completedAt//.startedAt)|fromdateiso8601)-(.startedAt|fromdateiso8601))/60*100|floor)/100)m  \(.name)")'
  return $rc
}
```

**`lead_time`** — TRUE commit→live measure (metric #1). Run right after `git push`:

```bash
lead_time() {
  local sha start now live
  sha=$(git rev-parse HEAD); start=$(date +%s)
  echo "waiting for $BE/health to report ${sha:0:8} ..."
  for _ in $(seq 1 120); do
    live=$(curl -s --max-time 10 "$BE/health" | jq -r '.commit // empty' 2>/dev/null)
    if [ "$live" = "$sha" ]; then
      now=$(date +%s)
      echo "LIVE: push→backend-live = $(( now - start )) s  ($(( (now-start)/60 ))m$(( (now-start)%60 ))s)"
      return 0
    fi
    sleep 10
  done
  echo "did not go live within window"; return 1
}
```

**`bump`** — the timed change class. Increments `API_VERSION` by one patch level (one app-source line); only the final Docker `COPY` layer rebuilds. Same class used in every timed run so build-cache state is the only variable:

```bash
bump() {
  f=~/code/LingvoPal/backend/app/core/config.py
  cur=$(grep -oP 'API_VERSION: str = "\K[0-9.]+' "$f")
  IFS=. read -r a b c <<< "$cur"; new="$a.$b.$((c+1))"
  sed -i "s/API_VERSION: str = \"$cur\"/API_VERSION: str = \"$new\"/" "$f"
  echo "API_VERSION $cur -> $new"
}
```

---

## Phase 0 — Manual deploy baseline (metric #1 before, metric #2 before = 8)

Record wall time AND step count. The hand-run equivalent of `cd.yml`, job for job.
Provisioning excluded (one-time).

**Warm-first priming (untimed):** fire both hooks on current HEAD to prime cache and wake free instance. No bump needed:

```bash
curl -fsS -X POST "$RENDER_DEPLOY_HOOK_URL"
curl -fsS -X POST "$VERCEL_DEPLOY_HOOK_URL"
# Wait until both show Live/Ready in dashboards, then proceed.
```

**Change-class pre-step (untimed, not a counted action):** push the bump with `[skip ci]` so CD does not fire — in the manual world there is no pipeline:

```bash
bump
git commit -am "deploy: manual baseline release [skip ci]"
git push origin main   # CD skipped — no run fires
```

**Start timer. Run the 8 manual steps:**

```bash
# Step 1
cd ~/code/LingvoPal/backend && PGSSLMODE=require PGCHANNELBINDING=require \
  uv run alembic upgrade head

# Step 2
# Read migration output by hand: "Running upgrade … done"

# Step 3
curl -fsS -X POST "$RENDER_DEPLOY_HOOK_URL"

# Step 4
# Watch Render dashboard until status = Live

# Step 5
curl -s "$BE/health" | jq .    # eyeball version + commit (no automated commit match)

# Step 6
curl -fsS -X POST "$VERCEL_DEPLOY_HOOK_URL"

# Step 7
# Watch Vercel dashboard until status = Ready

# Step 8
curl -s -o /dev/null -w '%{http_code}' "$FE"
```

Record: total wall time (min) → metric #1 "before"; 8 steps → metric #2 "before".

> **Note — asymmetry:** manual baseline has no enforced ordering and no commit-matched health gate. This is the pre-CD state. The pipeline enforcing strict sequencing + health gating is the finding — do not add that discipline to the baseline.

---

## Phase 1 — First automated release, COLD

> ⚠ Phase 0 just warmed the cache and woke the free instance — Phase 1 is NOT cold after Phase 0. Either (a) run Phase 1 BEFORE Phase 0, or (b) clear Render's build cache in the dashboard and let the instance idle back to sleep (~15 min). State which in A.8.

```bash
bump
git commit -am "cd: cold release timing run"
git push origin main & lead_time   # external commit→live measure (COLD)
cd_wait                            # workflow wall + 5 per-job durations
```

Record: COLD lead time → A.8, with free-tier cold-start caveat.

**Verify gate functions:** `/health` must show `"commit":"<sha>"` not `"unknown"`. If `unknown`, `RENDER_GIT_COMMIT` not injected → `smoke-backend` never passes → set it in Render env manually.

**Functional verification (not metrics — confirms production is live):**

```bash
curl -s "$BE/health" | jq .   # asyncpg+Neon up; commit == sha
# browser: register / log in   → CORS + Redis (Upstash TLS) sessions
# browser: upload an image      → R2 (https + SigV4 + path-style)
# browser: request password reset → Gmail SMTP
```

---

## Phase 2 — Warm release (headline "after" figure)

```bash
bump
git commit -am "cd: warm release timing run"
git push origin main & lead_time   # WARM = §4.9.3 "after" lead time
cd_wait
```

Report WARM as the §4.9.3 "after" headline. COLD (Phase 1) goes to A.8 with free-tier cold-start note. Do NOT average across the cold/warm boundary. Metric #2 "after" = 1 (`git push`).

---

## Phase 3 — Failed migration halts release

```bash
# Verify current migration head first:
cd ~/code/LingvoPal/backend && uv run alembic heads
# Use the printed hash as down_revision below

cat > ~/code/LingvoPal/backend/migrations/versions/zzzz_drift_trial.py << 'EOF'
"""drift trial — reverted after test"""
from alembic import op
revision = "zzzz_drift_trial"
down_revision = "246fdd13f6ee"   # replace with actual head from alembic heads
def upgrade():
    op.execute("ALTER TABLE table_that_does_not_exist ADD COLUMN x int")
def downgrade():
    pass
EOF
git add backend/migrations/versions/zzzz_drift_trial.py
git commit -m "test: failing migration for release-gate trial"
git push origin main; cd_wait
```

**Expected red:** `migrate`. Verify `deploy-backend`, `smoke-backend`, `deploy-frontend`, `smoke-frontend` all **skipped**; `/health` still reports the PREVIOUS commit; frontend unchanged.

Record: binary — release blocked, nothing deployed → §4.9.1 / §4.9.5.

```bash
git revert HEAD --no-edit && git push origin main; cd_wait   # → green + live
```

### Phase 3b — Unhealthy backend blocks frontend (optional)

> ⚠ `smoke-backend` polls ~15 min before failing. Optionally lower the loop count in `cd.yml` for this trial only, then revert.

```bash
# Edit backend/app/main.py health_check: temporarily remove the "commit" field
git add backend/app/main.py
git commit -m "test: health-gate trial (commit not reported)"
git push origin main; cd_wait
```

**Expected red:** `smoke-backend`. Verify `deploy-frontend` + `smoke-frontend` **skipped**.

```bash
git revert HEAD --no-edit && git push origin main; cd_wait   # → green + live
```

---

## Phase 4 — Recovery path (note only)

The revert in Phase 3/3b IS the recovery path — one `git push` re-runs the full gated pipeline. Report qualitatively as "recovery uses the identical one-command release path." Do NOT report a time-to-restore number; MTTR is owned by §4.5 (Alembic rollback).

---

## Phase 5 — Friction / DORA mapping table (→ §4.9 / Appendix A.8)

| Release concern | Before (manual) | After (09-deploy) |
|-----------------|-----------------|-------------------|
| Trigger release | hand-run hooks + dashboard watch | `git push main` (1 step) |
| Migrate before deploy | developer may forget | enforced: `deploy-* needs migrate` |
| Backend healthy before frontend | no check | enforced: commit-matched `/health` gate |
| Failed migration | code can ship on bad schema | halts whole release; nothing deploys |
| Confirm new revision live | manual eyeball | `smoke-backend` matches `RENDER_GIT_COMMIT` |
| Deployment steps | 8 | 1 |
| Release status visibility | split Render + Vercel dashboards | single GitHub Actions run |

DORA (within this case study):
- **Lead time for changes** — push→live: warm headline (Phase 2) + cold in A.8 (Phase 1).
- **Deployment frequency** — on-demand capability: every push to `main` releases with no human step.

---

## Run order

Pre-conditions + fill 4 env vars → Phase 0 (warm priming, then timed 8-step baseline) → [clear Render cache + ~15 min idle if needed] → Phase 1 (cold automated release + functional verify) → Phase 2 (warm = headline "after") → Phase 3 (failed migration) → Phase 3b (optional) → Phase 5 table. Leave `main` green and live.
