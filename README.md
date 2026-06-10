# Experiment 00 — Baseline (No DevOps)

**Branch:** `experiment/00-baseline`
**Measures:** A.2 pip install time (warm + cold), A.3 full onboarding time, step count

---

## Pre-conditions (once, untimed)

```bash
sudo systemctl start postgresql
sudo systemctl start redis

sudo -u postgres psql << 'SQL'
CREATE USER lingvopal WITH PASSWORD 'changeme';
CREATE DATABASE lingvopal OWNER lingvopal;
SQL

psql -U lingvopal -d lingvopal -v ON_ERROR_STOP=1 --single-transaction -f backend/schema.sql

# pyenv with Python 3.12 must be installed and on PATH
# Add to ~/.zshrc if missing:
# export PYENV_ROOT="$HOME/.pyenv"
# export PATH="$PYENV_ROOT/bin:$PATH"
# eval "$(pyenv init -)"

cd ~/code/LingvoPal
git checkout experiment/00-baseline
cp backend/.env.example backend/.env
# Edit backend/.env — fill all required variables
```

---

## Measurement A.2 — pip install time (warm + cold, 3 runs each)

From `~/code/LingvoPal/backend`:

**Warm** (system cache `~/.cache/pip` retained), run 3×:

```bash
python3.12 -m venv venv_run && source venv_run/bin/activate
time pip install -r requirements.txt
deactivate && rm -rf venv_run
```

Record: `real` from each run. Median → Appendix A.2 pip-warm row.

**Cold** (cache purged before each run), run 3×:

```bash
rm -rf ~/.cache/pip
python3.12 -m venv venv_run && source venv_run/bin/activate
time pip install -r requirements.txt
deactivate && rm -rf venv_run
```

Record: `real` from each run. Median → Appendix A.2 pip-cold row.

---

## Measurement A.3 — Full onboarding time (3 runs)

### Teardown — run before **each** of the 3 runs

```bash
pkill -f uvicorn 2>/dev/null; pkill -f vite 2>/dev/null
cd ~/code/LingvoPal
sudo -u postgres psql -c "DROP SCHEMA public CASCADE;" lingvopal
sudo -u postgres psql -c "CREATE SCHEMA public AUTHORIZATION lingvopal;" lingvopal
deactivate 2>/dev/null
rm -rf backend/venv frontend/node_modules
pyenv shell 3.12
```

### Timed run — start stopwatch, then type each step:

```bash
git checkout experiment/00-baseline

cd ~/code/LingvoPal/backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
psql -U lingvopal -d lingvopal -v ON_ERROR_STOP=1 -f schema.sql
psql -U lingvopal -d lingvopal -v ON_ERROR_STOP=1 -f seed.sql
uvicorn app.main:app --reload &

cd ../frontend
npm install
npm run dev
```

**Stop** when: login page loads and login as `test@test.com` succeeds in browser.

Record: `real` time each run. Run 1 only: count operator actions (per §2.5 rule — `cd` and shell toggles excluded), and add the four service-provisioning actions from pre-conditions (start PostgreSQL, start Redis, create role, create database) → 12 total.
Median of 3 → Appendix A.3 Manual (pre-Docker) row. Step count (12) → §4.3 / §4.4 tables.
