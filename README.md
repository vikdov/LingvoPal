# Experiment 06 — Automated Testing

**Branch:** `experiment/06-tests`
**Measures:** suite run time (s), coverage (%), mutation score (%), bug detection time (s), bisect steps

---

## Pre-conditions (once, untimed)

```bash
git checkout experiment/06-tests
cd ~/code/LingvoPal/backend
uv sync
uv add --dev pytest-cov mutmut

# Verify suite passes clean before any measurement
uv run pytest tests/ -q
# Expected: all green, 0 failures
```

No infrastructure needed — all tests are pure unit (AsyncMock for Redis, no DB fixtures).

---

## Phase 1 — Suite run time (3 runs)

```bash
time uv run pytest tests/ -q
time uv run pytest tests/ -q
time uv run pytest tests/ -q
```

Record: `real` from each run. Median → §4.6.3 "Suite run time".

---

## Phase 2 — Coverage (1 run)

```bash
uv run pytest tests/ --cov=app --cov-report=term-missing -q
```

Record: overall coverage % from the summary line → §4.6.3.

---

## Phase 3 — Mutation score (1 run, slow)

Scope: `sm2_engine.py` only.

```bash
uv run mutmut run --paths-to-mutate app/services/sm2_engine.py
uv run mutmut results
```

Record: killed / total = score % → §4.6.3.

---

## Phase 4 — Bug injection detection time (1 trial)

**Inject bug** in `backend/app/services/sm2_engine.py` line 154:

```python
# Change:
if q < QUALITY_THRESHOLD:
# To:
if q <= QUALITY_THRESHOLD:
```

**Run targeted suite, timed:**

```bash
time uv run pytest tests/test_sm2_engine.py -q
```

**Stop** when suite exits non-zero (failures detected).

Record: `real` → automated detection time → §4.6.3.
Manual counterfactual baseline: pre-registered 6.0 min (time to spot `<` vs `<=` in a diff without running tests).

---

## Phase 5 — git bisect demonstration (backfills §4.1.3)

Bug from Phase 4 is still in working tree. Commit it:

```bash
git commit -am "test: inject sm2 boundary bug"
```

Run bisect — mark current HEAD as bad, identify a known-good ancestor:

```bash
git log --oneline | head -15   # find a commit before any sm2 changes
git bisect start
git bisect bad HEAD
git bisect good <good-ancestor-hash>
```

At each bisect prompt, run the targeted suite to determine good/bad:

```bash
uv run pytest tests/test_sm2_engine.py -q
# Pass:  git bisect good
# Fail:  git bisect bad
```

Bisect terminates when the fault commit is identified.

```bash
git bisect reset
```

**Revert the injected commit:**

```bash
git reset --soft HEAD~1
git restore backend/app/services/sm2_engine.py
uv run pytest tests/ -q   # verify clean
```

Record: number of bisect steps, identified commit hash → §4.1.3.
