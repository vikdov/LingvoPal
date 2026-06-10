# Experiment 07 — Security Hardening

**Branch:** `experiment/07-security`
**Measures:** CVE counts, SAST block time (s), secret detection block time (s), container user, rate limit boundary

---

## Pre-conditions (once, untimed)

```bash
cd ~/code/LingvoPal
git checkout experiment/07-security
git log --oneline -3   # security commit must be on top of 06-tests chain
pre-commit install

# Verify pre-commit hooks are clean on current codebase
pre-commit run --all-files
# Expected: all hooks pass (bandit, detect-secrets, ruff)
```

---

## Phase 1 — Dependency CVE scanning

**Backend:**

```bash
cd ~/code/LingvoPal/backend
uv audit
```

**Frontend:**

```bash
cd ~/code/LingvoPal/frontend
npm audit --audit-level=none
```

Record: Critical / High / Medium / Low counts for backend and frontend → §4.7.3 / Appendix A.7.

---

## Phase 2a — Bandit SAST injection

**Inject insecure code:**

```bash
cat >> ~/code/LingvoPal/backend/app/main.py << 'EOF'

# TEST INJECTION — remove after test
import subprocess
result = subprocess.call("ls", shell=True)
EOF
```

**Attempt commit, timed:**

```bash
time git commit -am "test: bandit injection" 2>&1
```

**Expected:** commit blocked; bandit fires on `subprocess.call(shell=True)`.

**Cleanup:**

```bash
git restore backend/app/main.py
```

Record: blocked Yes/No, wall time (real) → §4.7.3.

---

## Phase 2b — Secret detection injection

**Create fake key file:**

```bash
cat > ~/code/LingvoPal/backend/app/fake_key.py << 'EOF'
SECRET = """
-----BEGIN RSA PRIVATE KEY-----
MIIEowIBAAKCAQEA2a2rwplBQLzHPZe5TNJN+KMjbmFGSGd8PqGwlqnvuZwmxkBh
-----END RSA PRIVATE KEY-----
"""
EOF
```

**Attempt commit, timed:**

```bash
git add backend/app/fake_key.py
time git commit -m "test: secret injection" 2>&1
```

**Expected:** commit blocked; `detect-private-key` hook fires.

**Cleanup:**

```bash
git restore --staged backend/app/fake_key.py
rm backend/app/fake_key.py
```

Record: blocked Yes/No, wall time (real) → §4.7.3.

---

## Phase 3 — Container hardening

```bash
cd ~/code/LingvoPal
docker build -t lingvopal-security-test ./backend
docker inspect lingvopal-security-test --format '{{.Config.User}}'
```

**Expected:** `appuser` (not empty string / root).

Record: before = `` (root) → after = `appuser` → §4.7.3.

---

## Phase 4 — Rate limiting

### 4a — Baseline static inspection

```bash
git worktree add /tmp/baseline-check experiment/00-baseline
grep -rn "slowapi\|auth_rate_limit\|limiter" /tmp/baseline-check/backend/app/
git worktree remove /tmp/baseline-check
```

**Expected:** no output — rate limiting absent from baseline.

Record: absent on baseline → §4.7.3.

### 4b — Negative test (experiment/00-baseline)

```bash
git worktree add /tmp/baseline-run experiment/00-baseline
cd /tmp/baseline-run/backend
REDIS_HOST=localhost uv run uvicorn app.main:app --host 0.0.0.0 --port 8002 \
  > /tmp/uvicorn-baseline.log 2>&1 &
echo $! > /tmp/uvicorn-baseline.pid
until curl -sf http://localhost:8002/health > /dev/null 2>&1; do sleep 1; done

for i in {1..20}; do
  curl -s -o /dev/null -w "%{http_code}\n" \
    -X POST http://localhost:8002/api/v1/auth/login \
    -H "Content-Type: application/json" \
    -d '{"email":"test@test.com","password":"wrong"}'
done

kill $(cat /tmp/uvicorn-baseline.pid)
git worktree remove /tmp/baseline-run
```

**Expected:** requests 1–20 all return 401 — no 429, brute-force unconstrained.

### 4c — Positive test (experiment/07-security)

```bash
# Flush any leftover rate-limit keys
redis-cli -h localhost KEYS "*127.0.0.1*" | xargs -r redis-cli -h localhost DEL

cd ~/code/LingvoPal/backend
REDIS_HOST=localhost uv run uvicorn app.main:app --host 0.0.0.0 --port 8001 \
  > /tmp/uvicorn.log 2>&1 &
echo $! > /tmp/uvicorn.pid
until curl -sf http://localhost:8001/health > /dev/null 2>&1; do sleep 1; done

for i in {1..20}; do
  curl -s -o /dev/null -w "%{http_code}\n" \
    -X POST http://localhost:8001/api/v1/auth/login \
    -H "Content-Type: application/json" \
    -d '{"email":"test@test.com","password":"wrong"}'
done

kill $(cat /tmp/uvicorn.pid)
```

**Expected:** requests 1–10 → 401, requests 11–20 → 429 (rate limit fires at 10/min boundary).

Record: limit boundary and first 429 request number → §4.7.3.
