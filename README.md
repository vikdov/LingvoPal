# Experiment 02 — Dependency Management (uv)

**Branch:** `experiment/02-deps`
**Measures:** install time cold/warm (s), lockfile integrity, compatibility, step count

---

## Pre-conditions (once, untimed)

```bash
git checkout experiment/02-deps
cd ~/code/LingvoPal/backend
ls uv.lock        && echo "uv.lock: EXISTS"
ls pyproject.toml && echo "pyproject.toml: EXISTS"
grep "requires-python" pyproject.toml
uv python pin
```

---

## Step 1 — Lockfile integrity

```bash
uv sync --frozen && echo "lockfile in sync: YES"
```

Record: Yes / No → §4.2.3

---

## Step 2 — Cold install time (3 runs)

Purge venv and download cache before each run:

```bash
rm -rf .venv ~/.cache/uv && time uv sync   # Run 1
rm -rf .venv ~/.cache/uv && time uv sync   # Run 2
rm -rf .venv ~/.cache/uv && time uv sync   # Run 3
```

Record: `real` from each run. Median → Appendix A.2 uv-cold row.

---

## Step 3 — Warm install time (3 runs)

Pre-populate cache (untimed, run twice):

```bash
rm -rf .venv && uv sync
rm -rf .venv && uv sync
```

Delete only `.venv` between timed runs — keep `~/.cache/uv` intact:

```bash
rm -rf .venv && time uv sync   # Run 1
rm -rf .venv && time uv sync   # Run 2
rm -rf .venv && time uv sync   # Run 3
```

Record: `real` from each run. Median → Appendix A.2 uv-warm row.

---

## Step 4 — Compatibility verification

```bash
uv run python --version
uv run python -c "import spacy;   print('spacy OK:',   spacy.__version__)"
uv run python -c "import fastapi; print('fastapi OK:', fastapi.__version__)"
```

Record: both imports succeed → "spacy + fastapi compat: YES" → §4.2.3

---

## Step 5 — Step count

Commands from clean state to working environment: `git checkout`, `cd`, `uv sync` = **3 steps**.

Record: 3 → §4.2.3 step count.
