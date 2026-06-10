# Experiment 01 — Version Control Structure

**Branch:** `experiment/01-vcs`
**Measures:** branch isolation (yes/no), fix:/feat: ratio, bisectable history (yes/no)

---

## Step 1 — Branch isolation

```bash
git checkout experiment/01-vcs
git branch -a | grep "experiment/"
# Expected all 10: 00-baseline, 01-vcs, 02-deps, 03-docker, 04-migrations,
#                  05-scripts, 06-tests, 07-security, 08-ci, 09-deploy
# NOTE: verify actual branch names against git output above — thesis uses
# 04-migrations / 05-scripts; check whether your repo uses that order.

for b in 00-baseline 01-vcs 02-deps 03-docker 04-migrations \
         05-scripts 06-tests 07-security 08-ci 09-deploy; do
  git checkout experiment/$b -- 2>&1 | head -1 && echo "OK: $b" || echo "FAIL: $b"
done
git checkout experiment/01-vcs
```

Record: Yes / No (all 10 reachable) → §4.1.3

---

## Step 2 — Commit convention ratio

```bash
git checkout main

# CUTOFF = hash of the commit that introduced the convention (set manually).
# fix:/feat: and the post-discipline conventional % are both measured from here.
CUTOFF=<first-conventional-commit-hash>

# fix:/feat: ratio — only feat/fix-tagged commits count, so this is post-discipline by construction.
feat_count=$(git log --format="%s" $CUTOFF..HEAD | grep -c "^feat")
fix_count=$(git log --format="%s" $CUTOFF..HEAD | grep -c "^fix")
echo "feat: $feat_count  fix: $fix_count  ratio: $(echo "scale=2; $fix_count / $feat_count" | bc)"

# Conventional adoption — full history vs post-discipline.
total_conv=$(git log --format="%s" | grep -cE "^(feat|fix|chore|refactor|docs|test|ci|perf|style)")
total=$(git log --format="%s" | wc -l)
echo "conventional (full history): $total_conv / $total commits"
pd_conv=$(git log --format="%s" $CUTOFF..HEAD | grep -cE "^(feat|fix|chore|refactor|docs|test|ci|perf|style)")
pd_total=$(git log --format="%s" $CUTOFF..HEAD | wc -l)
echo "conventional (post-discipline): $pd_conv / $pd_total commits"
```

Record: fix/feat ratio (post-discipline), conventional % (full history + post-discipline) → §4.1.3

---

## Step 3 — Bisect demonstration

Run **after** Experiment 06 Phase 5 (bug injection + commit).
See `experiment-06-tests-protocol.md` for the full bisect sequence.
Result backfills §4.1.3 bisect row.
