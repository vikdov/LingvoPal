# Experiment 08 — Continuous Integration

**Branch:** `experiment/08-ci`
**Measures:** manual verification time (min), step count, CI time-to-feedback cold/warm (min), detection times per trial

Pipeline: 12 jobs — backend lint, tests, migrations+alembic-check, docker+Trivy, bandit, uv-audit, gitleaks; frontend lint-build, tests, audit, docker+Trivy; plus `ci-success` aggregate gate.
CodeQL runs separately on `main`/`develop` + weekly cron — never on `experiment/*`.
`ci-success` mirrors any failed job — stated once, not repeated per phase.

---

## Pre-conditions

```bash
cd ~/code/LingvoPal
git checkout experiment/08-ci
git status      # must be clean
gh auth status
```

One-time governance: set `ci-success` as a required status check on `main`
(Settings → Branches → branch protection). Screenshot → Appendix B.

---

## Timing helper — paste once per shell

Keys on the pushed commit SHA; never waits for a stale prior run.

```bash
ci_wait() {
  local sha rid=""
  sha=$(git rev-parse HEAD)
  for _ in $(seq 1 40); do
    rid=$(gh run list --workflow ci.yml --branch "$(git branch --show-current)" \
          --limit 15 --json databaseId,headSha \
          -q "[.[] | select(.headSha==\"$sha\")][0].databaseId")
    [ -n "$rid" ] && break
    sleep 3
  done
  [ -z "$rid" ] && { echo "no CI run found for $sha"; return 2; }
  echo "run $rid  (sha ${sha:0:8})"
  gh run watch "$rid" --exit-status; local rc=$?
  gh run view "$rid" --json conclusion,createdAt,updatedAt,jobs -q '
    "conclusion=\(.conclusion)  wall=\((((.updatedAt|fromdateiso8601)-(.createdAt|fromdateiso8601))/60*100|floor)/100) min",
    (.jobs[] | "  \(.conclusion // "running")  \(((((.completedAt//.startedAt)|fromdateiso8601)-(.startedAt|fromdateiso8601))/60*100|floor)/100)m  \(.name)")'
  return $rc
}
```

---

## Phase −1 — Green baseline + seam-cost log (run FIRST)

```bash
git commit --allow-empty -m "ci: green baseline check"
git push
ci_wait   # expect conclusion=success, all 12 green
```

If any job is red: fix it (bump dep / base image — never weaken a gate).
Log each incident with resolution time → Appendix A.9 `tests ↔ CI` row:

```
| tests ↔ CI | <what failed> | <min> |
```

---

## Phase 0 — Manual baseline (sequential, dev machine)

Record wall time AND step count.

**Warm first (untimed):** run the block once, discard timing — primes gitleaks pre-commit env, uvx bandit fetch, Docker build cache. Time the second run.

```bash
time (
  cd backend && \
  uv run ruff check . && \
  uv run ruff format --check . && \
  uv run pytest -q && \
  uv run alembic upgrade head && \
  uv run alembic check && \
  uv audit --no-dev && \
  uvx 'bandit[toml]==1.9.4' -c pyproject.toml -r app -l && \
  docker build -t lingvopal-backend:manual-check . > /dev/null && \
  cd .. && \
  pre-commit run gitleaks --all-files && \
  cd frontend && \
  npm run lint && \
  npx tsc --noEmit && \
  npm audit --audit-level=high --omit=dev && \
  npm run test:coverage && \
  npm run build > /dev/null
)
```

Record: total wall time (min); N = number of `&&`-separated commands typed by hand → §4.8.3 "manual steps eliminated" = N → 0.

> **Note — asymmetry:** Phase 0 measures checks a developer ran *by hand in the pre-CI world*. CI does strictly more (Trivy image scan, full-history gitleaks, CodeQL) — that model shift is the finding, not a like-for-like benchmark. Never subtract Phase 0 time from CI time.

| CI job | In manual baseline? |
|--------|-------------------|
| Backend lint / tests / migrations / bandit / uv audit | yes |
| Frontend lint+build / tests / npm audit | yes |
| gitleaks secret scan | partial — manual = working tree; CI = full history |
| Backend Docker — Trivy scan | NO |
| Frontend Docker — build + Trivy | NO |
| CodeQL | NO |

---

## Phase 1 — CI time-to-feedback (3 runs, serialized)

Run 1 = fully cold — clear all GHA caches first:

```bash
gh cache delete --all

git commit --allow-empty -m "ci: timing run 1 (cold)"; git push; ci_wait
git commit --allow-empty -m "ci: timing run 2 (warm)"; git push; ci_wait
git commit --allow-empty -m "ci: timing run 3 (warm)"; git push; ci_wait
git commit --allow-empty -m "ci: timing run 4 (warm)"; git push; ci_wait
```

Record per run: wall (min) + 12 per-job durations (`ci_wait` prints both).
Report Run 1 (cold) and Runs 2–4 (warm, n=3) separately — do not average across the cache boundary.
Time-to-feedback = slowest *work* job (critical path), not the sum. Report `ci-success` separately.

---

## Phase 2 — Broken-commit detection

```bash
cat >> backend/tests/test_sm2_engine.py << 'EOF'

def test_intentional_failure():
    """CI detection trial — reverted after test."""
    assert False, "intentional failure"
EOF
git add backend/tests/test_sm2_engine.py
git commit -m "test: inject failing test for CI detection trial"
git push; ci_wait
```

**Expected red:** `Backend · Tests` + `CI Success`.

Record: root-cause job + push→failure wall (min).

```bash
git revert HEAD --no-edit && git push; ci_wait   # → 12-green
```

### Phase 2b — Counterfactual: no gate on pre-CI branch

```bash
# Verify chosen branch has no workflow file:
git show experiment/07-security:.github/workflows/ci.yml 2>/dev/null \
  && echo "HAS CI — use 06-tests instead" || echo "no CI on 07-security ✓"

git stash -u 2>/dev/null; git checkout experiment/07-security
cat >> backend/tests/test_sm2_engine.py << 'EOF'

def test_optional_side_counterfactual():
    assert False, "no CI gate here"
EOF
git add -A && git commit -m "test: optional-side counterfactual (no CI)"
git push
gh run list --branch experiment/07-security --limit 3   # expect: 0 runs triggered

git revert HEAD --no-edit && git push
git checkout experiment/08-ci; git stash pop 2>/dev/null || true
```

Record: broken code pushed, zero gate fired → §5.4 counterfactual.

---

## Phase 3 — Bypass enforcement: SAST

```bash
cat >> backend/app/main.py << 'EOF'

# CI BYPASS TEST — reverted after test
import subprocess
subprocess.call("ls", shell=True)   # bandit B602/B607
EOF
git add backend/app/main.py
git commit --no-verify -m "test: bypass pre-commit for CI SAST trial"
git push; ci_wait
```

**Expected red:** `Backend · SAST (bandit)` + `Backend · Lint` (ruff E402) + `CI Success`.

Record: local hooks bypassed via `--no-verify`, CI blocks independently; push→failure wall (min).

```bash
git revert HEAD --no-edit && git push; ci_wait   # → 12-green
```

### Phase 3b — Bypass enforcement: secret scan (throwaway branch)

```bash
git checkout -b experiment/08-ci-secrettrial
printf '%s\n' '-----BEGIN RSA PRIVATE KEY-----' \
  'MIIEowIBAAKCAQEAfaketestkeyDONOTUSE000000000000000000000000000000' \
  '-----END RSA PRIVATE KEY-----' > FAKE_TEST_KEY_DELETE_ME.pem
git add FAKE_TEST_KEY_DELETE_ME.pem
git commit --no-verify -m "test: gitleaks CI enforcement trial"
git push -u origin experiment/08-ci-secrettrial
ci_wait   # expect red: Security · Secret scan (gitleaks) + CI Success
# Screenshot the red gitleaks job → Appendix B

# Teardown — key ends up on no live branch:
git checkout experiment/08-ci
git branch -D experiment/08-ci-secrettrial
git push origin --delete experiment/08-ci-secrettrial
```

Record: local hook bypassed via `--no-verify`, CI gitleaks blocked it; push→failure wall (min).

---

## Phase 4 — Migration-drift detection

```bash
# Verify current head revision first:
cd backend && uv run alembic heads
# Use the printed hash as down_revision below

cat > backend/migrations/versions/zzzz_drift_trial.py << 'EOF'
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
git commit -m "test: add unmigrated model field for alembic check trial"
git push; ci_wait
```

**Expected red:** `Backend · Migrations` + `CI Success`.

Record: model↔migration drift caught, schema blocked before production; push→failure wall (min).

```bash
git revert HEAD --no-edit && git push; ci_wait   # → 12-green (final clean state)
```

---

## Final sanity

```bash
git status
ls FAKE_TEST_KEY_DELETE_ME.pem 2>/dev/null && echo "LEFTOVER KEY — remove" || echo "no leftover key ✓"
ci_wait   # last run on experiment/08-ci must be 12-green
```

---

## Phase 5 — Friction table (→ §4.8 / Appendix A.8)

| Check | Before (ad hoc, unenforced) | After (08-ci, enforced) |
|-------|-----------------------------|------------------------|
| Lint (ruff + eslint) | ad hoc, skippable | mandatory every push |
| Tests (pytest + vitest) | ad hoc, skippable | mandatory every push |
| TS type-check + build | ad hoc, skippable | mandatory every push |
| Migration drift (alembic check) | unenforced | mandatory every push |
| Docker image build + Trivy (×2) | unenforced | mandatory every push |
| Dependency CVE audit (uv + npm) | unenforced | mandatory (own jobs) |
| SAST (bandit) | unenforced | mandatory (own job) |
| Secret scan (gitleaks) | local hook only, bypassable | mandatory server-side |
| CodeQL | none | enforced on main/develop + cron |
| Pre-commit bypass (--no-verify) | undetected, no fallback | CI re-runs independently |
| Aggregate required gate | none | `ci-success` branch-protection |
| Execution model | sequential, manual, optional | parallel, automated, mandatory |

---

## Run order

Phase −1 (green + seam log + branch protection) → Phase 0 (warm then timed) → Phase 1 (cold, then warm ×2) → Phase 2 + 2b → Phase 3 + 3b → Phase 4 + final sanity → Phase 5 table.
