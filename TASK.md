# 🎯 TASK HANDOFF

**Last Updated:** 2026-06-01 05:20 UTC
**Project:** AI Personal Secretary Stack
**Status:** ✅ 14 features shipped + bot.py refactor terminal + 3 polish rounds. Sesi 2026-05-31 → 2026-06-01 ditutup dengan 58 commits autonomous (~17h). **User switching to fresh opencode session — read first 80 lines below.**

> ⚠️ **HANDOFF NOTE — User is switching to a fresh opencode session.** Read `## 🚀 FRESH SESSION ENTRYPOINT` below to pick up. All work is committed + pushed + CI green. Working tree clean.

> Full history (2562 lines, sessions 2026-05-08 → 2026-05-24) archived in [`TASK_ARCHIVE.md`](TASK_ARCHIVE.md).

---

## 🆘 NEW SESSION QUICK START (read this first, ~2 min)

**Repo state right now (2026-06-01 05:20 UTC):**
```
Branch: main, working tree clean, all CI green
Last commit: 202e197 docs(TASK): handoff for sesi 2026-06-01 04:55 (round 3 polish — final)
Production: 7 containers up + healthy (last verified run 26735847459)
Tests: 788 passing, ~44% coverage
```

**One-shot verification:**
```bash
cd /home/ubuntu/bench/pro-secretary
git status                                    # clean, on main
git log --oneline -5                          # see recent work
gh run list --workflow=deploy.yml --limit 3   # last 3 'ok'
python3 -m pytest -q                          # 788 passed
```

**The honest truth about this session:** AI's autonomous work runway is exhausted. 17h, 58 commits, 3 polish rounds. Every easy win is shipped. **Recommended next action: STOP and dogfood.** Do NOT start a 4th polish round.

**What user (you) should do next, in order of value:**

1. **Test 8 features in Telegram** — highest value, 30-60min. Send `/morning_brief`, `/drift`, `/capacity`, `/deps`, `/hygiene`, `/firewall`, `/coverage`, `/briefing` to bot. Note any rough edges.
2. **`/coverage add gmedia/erp`** — dogfood the new Test Coverage Agent on a real repo. 1 day to first auto-PR.
3. **`/ssl add yourdomain.com`** — activates DNS+SSL schedulers (currently idle).
4. **Wait dogfood window** — ~5-12 days remaining of 1-2 week target. Real signal comes from observation.
5. **(Blocked on PRD) Spec-to-Implementation Agent** — 9-12h work when ready.

**What AI cannot do alone:**
- Test features in Telegram (user-only via bot UI)
- Onboard 8-13 VPS to Prometheus (needs IP/SSH list)
- Write Spec-to-Impl (needs PRD)
- Real-world dogfood signal

**What AI could do but shouldn't (diminishing returns):**
- More integration tests (main paths covered)
- Bot.py handler tests (low ROI, hard-coupled to PTB)
- Python 3.12 syntax migration (broad change, wants user buy-in)
- Module docstrings (violates anti-AI-slop guideline)
- Round 4 polish (would be ~30min of make-work)

---

## 📦 SESSION HANDOFF (2026-06-01 05:20 UTC) — full detail

**Last activity:** Sesi closed at 04:55 UTC after run `26735847459` deployed successfully. Handoff text-edit only at 05:20 UTC.

**Latest commits (last 6):**
```
[handoff]  docs(TASK): handoff for sesi 2026-06-01 04:55 (round 3 polish)
[ci]       ci: cache pip dependencies in setup-python (faster CI)
[ci]       ci: switch ruff pre-commit hook from staged-hunks to full-tree scan
[handoff]  docs(TASK): handoff for sesi 2026-06-01 04:20 (round 2 polish)
[fix]      fix(test): drop unused unittest.mock.patch import
[test]     test: integration tests for langgraph-agent endpoints
```

**Latest deploy verified:**
- Run `26735847459` — lint+test+deploy 1m36s — all green
- pip cache will activate on subsequent runs (first run misses)
- All 9 CI lint gates running, 8 schedulers + 7 containers healthy

**State to verify in new session (paste these):**
```bash
git status                                    # expect: clean, on main
git log --oneline -6                          # expect: matches above
gh run list --workflow=deploy.yml --limit 3   # expect: last 3 'ok'
python3 -m pytest -q                          # expect: 788 passed
python3 scripts/lint_orphan_refs.py           # expect: 18 files, 136 functions
python3 scripts/lint_docs_freshness.py        # expect: docs in sync
pip-audit -r telegram-bot/requirements.txt    # expect: no vulnerabilities
pip-audit -r langgraph-agent/requirements.txt # expect: no vulnerabilities
```

**What's safe to start without asking:**
- **Nothing genuinely valuable.** AI's autonomous work runway is exhausted. Repo polished beyond most production repos.
- See `## 🚀 FRESH SESSION ENTRYPOINT` → "Pick your work" table.

**What's blocked on user (HIGH-VALUE):**
- **Test 8 features in Telegram** — including new `/coverage` (dogfood window 54h elapsed of 1-2 weeks)
- **Add Coverage repos** — `/coverage add gmedia/erp` to dogfood the new feature
- **Activate DNS+SSL** — `/ssl add yourdomain.com`
- **Onboard 8-13 VPS to Prometheus** — needs IP/SSH list
- **Spec-to-Implementation** — needs PRD

**Cumulative metrics from sesi 2026-05-31 → 2026-06-01 (~17h, 58 commits):**
- Tests: 71 → 788 (+717, 11.1x)
- Coverage: 12.75% → ~44% (+31pp)
- Coverage floor: 12% → 27%
- CI lint gates: 4 → 9 (ruff F full-tree, pip-audit, mypy x2, orphan, docs-freshness, +actionlint, compileall, caddy/promtool/amtool)
- Pre-commit hooks: 0 → 7 (ruff full-tree, actionlint, compileall, orphan-refs, docs-freshness, mypy lenient, mypy strict)
- Mypy strict modules: 0 → 27 (~100% of "leaf" modules)
- SHA-pinned images: 1 → 5 (all production)
- **bot.py LOC: 3524 → 2253 (-1271, -36.1%)**
- **Top-level docs: README + TASK + ARCHITECTURE.md (drift-linted)**
- **Features shipped: 13 → 14 (added Test Coverage Agent)**
- **Watchdogs at 100% coverage: 0 → 7 of 9 (capacity 97%, ssl 93%)**
- **No known CVEs in production deps**
- **Dependabot configured** for pip + github-actions + docker, weekly Mondays 06:00 WIB
- **CI pip cache** — first miss (1m36s), subsequent runs estimated ~50s

**Production state at handoff:** 7 containers up + healthy (verified via run 26735847459). Dogfood window ~54h elapsed of 1-2 week target.

---

## 🚀 FRESH SESSION ENTRYPOINT (read this if you're a new opencode session)

**Last session ended 2026-06-01 04:55 UTC. Continuing in a new opencode session.**

### Repo state right now

```
Branch: main, working tree clean
Last 6 commits:
  [handoff]  docs(TASK): handoff for sesi 2026-06-01 04:55
  [ci]       ci: cache pip dependencies in setup-python
  [ci]       ci: switch ruff pre-commit hook to full-tree scan
  [handoff]  docs(TASK): handoff for sesi 2026-06-01 04:20
  [fix]      fix(test): drop unused unittest.mock.patch
  [test]     test: integration tests for langgraph-agent endpoints

Production: 7 containers up + healthy (last verified run 26735847459)
Dogfood: ~54h elapsed of 1-2 week window (started 2026-05-30 23:00 UTC)
telegram-bot/: bot.py (2253) + infra/ (206 LOC, 100%) + watchdogs/ (1475 LOC, 7 at 100%)
langgraph-agent/: + app/test_coverage.py (290 LOC, mypy strict)
tests/: 788 passing, ~44% coverage
mypy strict: 27 modules whitelisted
ruff: pinned v0.15.15 (full-tree scan, CI + pre-commit aligned structurally)
pip-audit: pinned v2.10.0 (CI gate)
docs-freshness: lint gate (CI + pre-commit)
CI: 9 lint gates, pip cache enabled
Dependabot: configured (pip + github-actions + docker)
```

### Pick your work

**If user says "lanjutkan" / "continue" without specifics, ASK FIRST.**

**Three polish rounds done. Repo polished as far as autonomous AI can take it without user input.**

| Path | Effort | Risk | Notes |
|---|---|---|---|
| **A. Dogfood Test Coverage on `gmedia/erp`** | 5min user + observe | 🟢 Low | User adds repo via `/coverage add gmedia/erp`. **HIGHEST VALUE — only path that needs user.** |
| **B. Spec-to-Implementation Agent** | 9-12h | 🟡 Med | Blocked on PRD. |
| **C. Auto-PR Phase 2 (auto-merge confidence threshold)** | 4-6h | 🟡 Med | Blocked on dogfood signal. |
| **D. Wait for dogfood signal** | — | — | ~5-12 days remaining. |
| **E. AI runway exhausted** | — | — | Nothing left that's genuinely valuable autonomous. |

### Sesi recap (high-level)

Sesi 2026-06-01 04:55 = **round 3 polish** (continued from 04:20 UTC). Three more autonomous tasks executed without user confirmation:

1. **Pre-commit ruff scope fix** (commit 1):
   - Replaced `astral-sh/ruff-pre-commit` (staged-hunks scope) with local system hook running ruff against full tree
   - Eliminates 6th occurrence of CI ruff failures from unused imports left when functions deleted
   - Trade-off: pre-commit slightly slower, ruff is fast (~1s for 788-test repo)

2. **CI pip cache** (commit 2):
   - Added `cache: pip` + `cache-dependency-path` to both setup-python steps
   - Cache keyed on requirements.txt hashes
   - First run misses (1m36s), subsequent estimated ~50s
   - Note: concurrency cancel-in-progress already configured (lines 14-16 of deploy.yml — Task B was already done)

3. **Dependabot config** (Task C — already exists):
   - Found existing comprehensive config in `.github/dependabot.yml`
   - 4 ecosystems: pip x2, github-actions, docker x2
   - Weekly Mondays 06:00 WIB
   - No changes needed

4. **Production deploy verified** (run `26735847459`):
   - lint + test + deploy 1m36s — all green
   - pip cache will activate on next run

---

## 🤝 FOR NEXT SESSION (detailed handoff)

**Where we left off:** Sesi 2026-06-01 04:55 — third polish round complete. **AI's autonomous work runway exhausted. All polish rounds done.** Next steps need user.

### Files changed in round 3 (2 commits)

**ci: ruff full-tree (commit 1):**
- `~ .pre-commit-config.yaml` (replaced ruff-pre-commit with local system hook, restructured to put actionlint above ruff)

**ci: pip cache (commit 2):**
- `~ .github/workflows/deploy.yml` (+8 lines: cache: pip + cache-dependency-path on both setup-python steps)

### Active Tasks (for next session)

- [ ] **TEST `/coverage` IN TELEGRAM** — user adds `gmedia/erp`, watches what PRs come out
- [ ] **DOGFOOD WINDOW (active, ~54h elapsed)** — observe 8 features for 1-2 weeks total
- [ ] **ACTIVATE DNS + SSL schedulers** (5 menit)
- [ ] **Onboard 8-13 VPS to Prometheus** — needs IP/SSH list
- [ ] **DECIDE: Spec-to-Implementation OR Auto-PR Phase 2 OR wait dogfood**
- [ ] **DEFERRED: Phase 2 auto-PR/auto-remediation** — wait dogfood signal
- [ ] **DEFERRED: Grafana, py3.14**

### Lessons from round 3

1. **Always check before assuming task isn't done** — Task C "Add Dependabot" already had comprehensive config. Saved 10min by reading first.

2. **Pre-commit hook scope is subtle** — `astral-sh/ruff-pre-commit` defaults to `pass_filenames: true` which means pre-commit only passes staged files to ruff. ruff then checks those files in full, BUT only the staged subset. Works for most cases — except when an import becomes unused due to a deletion in the same commit. Switch to a local `pass_filenames: false` hook with explicit full-tree scan to match CI exactly.

3. **CI minute optimization is a real DX improvement** — 1m36s → ~50s on cache hit is 45% faster feedback loop. For 5-10 commits/day, saves 8-15min daily, compounds into hours/week. Worth the 10 minutes setup.

4. **Diminishing returns are real** — round 3's tasks are smaller wins than round 1-2. Round 4 would be even smaller. The brave thing is to recognize this and stop. Done.

---


> ⚠️ **HANDOFF NOTE — User is switching to a fresh opencode session.** Read `## 🚀 FRESH SESSION ENTRYPOINT` below to pick up. All work is committed + pushed + CI green. Working tree clean.

> Full history (2562 lines, sessions 2026-05-08 → 2026-05-24) archived in [`TASK_ARCHIVE.md`](TASK_ARCHIVE.md).

---

## 📦 SESSION HANDOFF (2026-06-01 04:20 UTC) — for fresh opencode session

**Last activity:** Sesi closed at 04:20 UTC after run `26734864603` deployed successfully.

**Latest commits (last 6):**
```
[handoff]  docs(TASK): handoff for sesi 2026-06-01 04:20 (round 2 polish)
[fix]      fix(test): drop unused unittest.mock.patch import
[test]     test: integration tests for langgraph-agent endpoints (FastAPI TestClient)
[ci]       ci: add docs-freshness lint to prevent README/ARCHITECTURE drift
[ci]       ci: add pip-audit dependency vulnerability scan
[handoff]  docs(TASK): handoff for sesi 2026-06-01 03:46 (polish round)
```

**Latest deploy verified:**
- Run `26734864603` — lint+test+deploy 1m35s — all green
- 9 CI lint gates now (added pip-audit + docs-freshness)
- All 8 schedulers + 7 containers healthy

**State to verify in new session (paste these):**
```bash
git status                                    # expect: clean, on main
git log --oneline -6                          # expect: matches above
gh run list --workflow=deploy.yml --limit 3   # expect: last 2 'ok' (1 fail before fix)
python3 -m pytest -q                          # expect: 788 passed
python3 scripts/lint_orphan_refs.py           # expect: 18 files, 136 functions clean
python3 scripts/lint_docs_freshness.py        # expect: docs in sync
pip-audit -r telegram-bot/requirements.txt    # expect: no vulnerabilities
pip-audit -r langgraph-agent/requirements.txt # expect: no vulnerabilities
```

**What's safe to start without asking:**
- Repo in extended pause-state. Two polish rounds done. Next genuinely-autonomous work has minimal value.
- See `## 🚀 FRESH SESSION ENTRYPOINT` → "Pick your work" table.

**What's blocked on user (HIGH-VALUE):**
- **Test 8 features in Telegram** — including new `/coverage` (dogfood window 53h elapsed of 1-2 weeks)
- **Add Coverage repos** — `/coverage add gmedia/erp` to dogfood the new feature
- **Activate DNS+SSL** — `/ssl add yourdomain.com`
- **Onboard 8-13 VPS to Prometheus** — needs IP/SSH list
- **Spec-to-Implementation** — needs PRD

**Cumulative metrics from sesi 2026-05-31 → 2026-06-01 (~16h, 55 commits):**
- Tests: 71 → 788 (+717, 11.1x)
- Coverage: 12.75% → ~44% (+31pp)
- Coverage floor: 12% → 27%
- CI lint gates: 4 → 9 (+pip-audit, +docs-freshness)
- Pre-commit hooks: 0 → 7 (+docs-freshness)
- Mypy strict modules: 0 → 27 (~100% of "leaf" modules)
- SHA-pinned images: 1 → 5 (all production)
- **bot.py LOC: 3524 → 2253 (-1271, -36.1%)**
- **Top-level docs: README + TASK + ARCHITECTURE.md (all in sync, drift-checked)**
- **Features shipped: 13 → 14 (added Test Coverage Agent)**
- **Watchdogs at 100% coverage: 0 → 7 of 9 (capacity 97%, ssl 93%)**
- **No known CVEs in any production deps**

**Production state at handoff:** 7 containers up + healthy (verified via run 26734864603). Dogfood window ~53h elapsed of 1-2 week target.

---

## 🚀 FRESH SESSION ENTRYPOINT (read this if you're a new opencode session)

**Last session ended 2026-06-01 04:20 UTC. Continuing in a new opencode session.**

### Repo state right now

```
Branch: main, working tree clean
Last 5 commits:
  [fix]      fix(test): drop unused unittest.mock.patch
  [test]     test: integration tests for langgraph-agent endpoints
  [ci]       ci: add docs-freshness lint
  [ci]       ci: add pip-audit dependency scan
  [handoff]  docs(TASK): handoff for sesi 2026-06-01 03:46

Production: 7 containers up + healthy (last verified run 26734864603)
Dogfood: ~53h elapsed of 1-2 week window (started 2026-05-30 23:00 UTC)
telegram-bot/: bot.py (2253) + infra/ (206 LOC, 100% covered) + watchdogs/ (1475 LOC, 7 at 100%, 1 at 97%, 1 at 93%)
langgraph-agent/: + app/test_coverage.py (290 LOC, mypy strict)
tests/: 788 passing, ~44% coverage
mypy strict: 27 modules whitelisted
ruff: pinned v0.15.15 (CI + pre-commit aligned)
pip-audit: pinned v2.10.0 (CI gate)
docs-freshness: lint gate (CI + pre-commit)
```

### Verify state in <2 minutes

```bash
git status                                    # clean
git log --oneline -6                          # matches above
gh run list --workflow=deploy.yml --limit 3   # last 2 green
python3 -m pytest -q                          # 788 passed
python3 -m ruff check --select=F telegram-bot langgraph-agent tests
python3 -m mypy --config-file=mypy.ini telegram-bot langgraph-agent
python3 -m compileall -q telegram-bot langgraph-agent
python3 scripts/lint_orphan_refs.py           # 18 files, 136 functions
python3 scripts/lint_docs_freshness.py        # docs sync
pip-audit -r telegram-bot/requirements.txt
pip-audit -r langgraph-agent/requirements.txt
pre-commit run --all-files                    # 5 hooks pass
pre-commit run --all-files --hook-stage pre-push  # +mypy lenient + strict
```

### Pick your work

**If user says "lanjutkan" / "continue" without specifics, ASK FIRST.**

**Two polish rounds done. Repo polished beyond what most production repos look like. Decision:**

| Path | Effort | Risk | Notes |
|---|---|---|---|
| **A. Dogfood Test Coverage on `gmedia/erp`** | 5min user + observe | 🟢 Low | User adds repo via `/coverage add gmedia/erp`. **HIGHEST VALUE — only path that needs user.** |
| **B. Spec-to-Implementation Agent** | 9-12h | 🟡 Med | Blocked on PRD. |
| **C. Auto-PR Phase 2 (auto-merge confidence threshold)** | 4-6h | 🟡 Med | Blocked on dogfood signal. |
| **D. Wait for dogfood signal** | — | — | ~5-12 days remaining. |
| **E. Lower-value autonomous work** | varies | 🟢 Low | Diminishing returns: bot.py handler tests (low ROI), Python 3.12 syntax migration (broad change, want user buy-in), more integration tests (already covered main paths). **Recommend not.** |

**Truthful assessment:** AI's autonomous work runway is genuinely exhausted. Every easy improvement is shipped. Every remaining task either needs user input (Telegram, PRD, IPs) or real-world signal (dogfood). Continuing solo work risks code bloat without product value.

### Safety net you can rely on

- **9 CI lint gates** — actionlint, ruff F (pinned v0.15.15), pip-audit (pinned v2.10.0), mypy lenient, mypy strict (27 modules), orphan-refs (18 files), docs-freshness, compileall, caddy, promtool, amtool
- **7 pre-commit hooks** + 2 pre-push hooks
- **788 pytest tests** (409 new this session, ~52% of total test suite)
- **Coverage floor 27%** — actual ~44%
- **All 6 infra/* modules at 100% coverage**
- **7 of 9 watchdogs/* at 100% coverage** (capacity 97%, ssl 93%)
- **All production images SHA-pinned**
- **README.md** + **ARCHITECTURE.md** + **TASK.md** all in sync (drift-linted)
- **No known CVEs in production deps**

### Sesi recap (high-level)

Sesi 2026-06-01 04:20 = **round 2 polish** (continued from 03:46 UTC). Three more autonomous tasks executed without user confirmation:

1. **pip-audit security scan** (commit 1):
   - New CI gate `pip-audit==2.10.0` runs against both requirements files
   - Both deps clean — no known CVEs
   - Prevents regression: future transitive CVEs will fail CI

2. **Docs-freshness lint** (commit 2):
   - New `scripts/lint_docs_freshness.py` (124 LOC) verifies:
     - ARCHITECTURE.md infra/ tree matches filesystem (6 files)
     - ARCHITECTURE.md watchdogs/ tree matches filesystem (9 files)
     - README.md "N features shipped" matches feature table row count (19=19)
   - Wired to pre-commit hook + CI lint step
   - 14 new tests for the lint script itself

3. **Integration tests** (commit 3):
   - 21 new FastAPI TestClient integration tests for agent endpoints
   - Coverage: auth boundary (4), coverage repos (3), coverage scan (3),
     review repos (2), review_pr endpoint (4), GitHub webhook (2),
     GitLab webhook (2), health (1)
   - Test pyramid was unit-only; this fills the integration gap

4. **CI ruff catch + fix** (commit 4):
   - Local pre-commit ruff scope only diff hunks, missed unused
     `from unittest.mock import patch`
   - CI ruff full-file scan caught it. Fixed and pushed.

5. **Production deploy verified** (run `26734864603`):
   - lint + test + deploy 1m35s — all green
   - 9 CI lint gates run cleanly

---

## 🤝 FOR NEXT SESSION (detailed handoff)

**Where we left off:** Sesi 2026-06-01 04:20 — second polish round complete. **All AI autonomous work is genuinely done.** Next steps need user.

### Files changed in round 2 (4 commits)

**ci: pip-audit (commit 1):**
- `~ .github/workflows/deploy.yml` (+9 lines new lint step)

**ci: docs-freshness (commit 2):**
- `+ scripts/lint_docs_freshness.py` (124 LOC)
- `+ tests/test_lint_docs_freshness.py` (14 tests)
- `~ .pre-commit-config.yaml` (+8 lines hook)
- `~ .github/workflows/deploy.yml` (+3 lines step)

**test: integration (commit 3):**
- `+ tests/test_agent_integration.py` (21 tests)

**fix: ruff (commit 4):**
- `~ tests/test_lint_docs_freshness.py` (drop 1 unused import)

### Active Tasks (for next session)

- [ ] **TEST `/coverage` IN TELEGRAM** — user adds `gmedia/erp`, watches what PRs come out
- [ ] **DOGFOOD WINDOW (active, ~53h elapsed)** — observe 8 features for 1-2 weeks total
- [ ] **ACTIVATE DNS + SSL schedulers** (5 menit)
- [ ] **Onboard 8-13 VPS to Prometheus** — needs IP/SSH list
- [ ] **DECIDE: Spec-to-Implementation OR Auto-PR Phase 2 OR wait dogfood**
- [ ] **DEFERRED: Phase 2 auto-PR/auto-remediation** — wait dogfood signal
- [ ] **DEFERRED: Grafana, py3.14**

### Lessons from round 2

1. **pip-audit catches what people forget** — first run was clean, but the gate has zero ongoing cost (~10s in CI) and high payoff when a dep gains a CVE later. Should have been added day 1.

2. **Lints that prevent the bug you just fixed** — README drift cost real engineering time. The docs-freshness lint script (124 LOC + 14 tests) costs 60min once and prevents that exact regression forever. Apply this pattern: every bug fix → ask "what lint would have caught this?"

3. **Test pyramid imbalance** — we had 753 unit tests but ~0 integration tests. FastAPI's TestClient + pytest + monkeypatch makes integration tests trivial. 21 tests in 90 minutes covered all main API paths. Should have been written alongside the API.

4. **Pre-commit ruff scope drift vs CI ruff** — pre-commit only checks `staged hunks` for ruff (default behavior in ruff-pre-commit). CI checks full files. This means deletions of imports (where the import line stays unchanged but is now unused) won't be caught locally. Workaround: `pre-commit run --all-files` before pushing OR widen pre-commit hook to full files. Defer.

5. **Recognize when to stop** — with 55 commits and all genuinely-valuable autonomous tasks done, generating more work would degrade signal-to-noise. The brave thing is to stop and wait for dogfood data.

---


> ⚠️ **HANDOFF NOTE — User is switching to a fresh opencode session.** Read `## 🚀 FRESH SESSION ENTRYPOINT` below to pick up. All work is committed + pushed + CI green. Working tree clean.

> Full history (2562 lines, sessions 2026-05-08 → 2026-05-24) archived in [`TASK_ARCHIVE.md`](TASK_ARCHIVE.md).

---

## 📦 SESSION HANDOFF (2026-06-01 03:46 UTC) — for fresh opencode session

**Last activity:** Sesi closed at 03:46 UTC after run `26733950073` deployed successfully.

**Latest commits (last 5):**
```
f29f93b docs: ARCHITECTURE.md + README.md reflect terminal state + new features
ed4d96a test: coverage polish for capacity + deps watchdogs
9a8a47a ci: pin ruff to v0.15.15 (CI + pre-commit aligned)
[handoff]  docs(TASK): handoff for sesi 2026-05-31 19:48 (Test Coverage Agent shipped)
9e8b14f    fix(test): drop unused json import
```

**Latest deploy verified:**
- Run `26733950073` — lint+test+deploy 1m33s — all green
- All 8 schedulers registered: health 300s, morning brief 07:00, drift 02:00, capacity 02:10, deps 03:00, hygiene 02:15, firewall 03:30, coverage 04:00 WIB
- DNS+SSL schedulers idle (SSL list empty — expected)
- All 7 containers healthy

**State to verify in new session (paste these):**
```bash
git status                                    # expect: clean, on main
git log --oneline -5                          # expect: matches above
gh run list --workflow=deploy.yml --limit 2   # expect: last 2 'ok'
python3 -m pytest -q                          # expect: 753 passed
python3 scripts/lint_orphan_refs.py           # expect: 18 files, 136 functions clean
```

**What's safe to start without asking:**
- All "polish" tasks done. Refactor terminal. Coverage polish to 97-100%. Docs in sync.
- Repo in extended pause-state. Next high-value action requires user (Telegram interaction).

**What's blocked on user (HIGH-VALUE):**
- **Test 8 features in Telegram** — including new `/coverage` (dogfood window 53h elapsed of 1-2 weeks)
- **Add Coverage repos** — `/coverage add gmedia/erp` to dogfood the new feature
- **Activate DNS+SSL** — `/ssl add yourdomain.com`
- **Onboard 8-13 VPS to Prometheus** — needs IP/SSH list
- **Spec-to-Implementation** — needs PRD

**Cumulative metrics from sesi 2026-05-31 → 2026-06-01 (~15h, 50 commits):**
- Tests: 71 → 753 (+682, 10.6x)
- Coverage: 12.75% → ~43% (+30pp)
- Coverage floor: 12% → 27%
- CI lint gates: 4 → 8
- Pre-commit hooks: 0 → 6 (ruff pinned)
- Mypy strict modules: 0 → 27 (~100% of "leaf" modules)
- SHA-pinned images: 1 → 5 (all production)
- **bot.py LOC: 3524 → 2253 (-1271, -36.1%)**
- **Top-level docs: README + TASK + ARCHITECTURE.md (all in sync)**
- **Features shipped: 13 → 14 (added Test Coverage Agent)**
- **Watchdogs at 100% coverage: 0 → 7 (capacity 97%, ssl 93%)**

**Production state at handoff:** 7 containers up + healthy (verified via run 26733950073). Dogfood window ~53h elapsed of 1-2 week target.

---

## 🏗️ Bot.py Refactor — TERMINAL STATE (see also ARCHITECTURE.md)

**All extractable units extracted. 9 watchdogs + 6 infra modules. Pattern proven across 7 batches + 1 feature.**

```
telegram-bot/
├── bot.py                  (2253 lines — orchestrator + handler-only code)
├── infra/                  (all 100% covered, all mypy strict)
└── watchdogs/              (all mypy strict, all 80%+ coverage, 7 at 100%)
    ├── capacity.py         (152 LOC — 97% covered)
    ├── deps.py             (66 LOC — 100% covered)
    ├── dns.py              (200 LOC — 100% covered)
    ├── drift.py            (158 LOC — 100% covered)
    ├── firewall.py         (240 LOC — 100% covered)
    ├── hygiene.py          (177 LOC — 100% covered)
    ├── morning_brief.py    (152 LOC — 100% covered)
    ├── ssl.py              (165 LOC — 93% covered, lines 52-60 in threadpool inner func)
    └── test_coverage.py    (165 LOC — 100% covered)
```

---

## 🚀 FRESH SESSION ENTRYPOINT (read this if you're a new opencode session)

**Last session ended 2026-06-01 03:46 UTC. Continuing in a new opencode session.**

### Repo state right now

```
Branch: main, working tree clean
Last 5 commits:
  f29f93b    docs: ARCHITECTURE.md + README.md reflect terminal state
  ed4d96a    test: coverage polish for capacity + deps watchdogs
  9a8a47a    ci: pin ruff to v0.15.15 (CI + pre-commit aligned)
  [handoff]  docs(TASK): handoff for sesi 2026-05-31 19:48
  9e8b14f    fix(test): drop unused json import

Production: 7 containers up + healthy (last verified run 26733950073)
Dogfood: ~53h elapsed of 1-2 week window (started 2026-05-30 23:00 UTC)
telegram-bot/: bot.py (2253) + infra/ (206 LOC, 100% covered) + watchdogs/ (1475 LOC, 7 at 100%, 1 at 97%, 1 at 93%)
langgraph-agent/: + app/test_coverage.py (290 LOC, mypy strict)
tests/: 753 passing, ~43% coverage
mypy strict: 27 modules whitelisted
ruff: pinned v0.15.15 (CI + pre-commit aligned)
```

### Verify state in <2 minutes

```bash
git status                                    # clean
git log --oneline -5                          # matches above
gh run list --workflow=deploy.yml --limit 3   # last 2 green
python3 -m pytest -q                          # 753 passed
python3 -m ruff check --select=F telegram-bot langgraph-agent tests
python3 -m mypy --config-file=mypy.ini telegram-bot langgraph-agent
python3 -m compileall -q telegram-bot langgraph-agent
python3 scripts/lint_orphan_refs.py           # 18 files, 136 functions
pre-commit run --all-files                    # 4 hooks pass
pre-commit run --all-files --hook-stage pre-push  # +mypy lenient + strict
```

### Pick your work

**If user says "lanjutkan" / "continue" without specifics, ASK FIRST.**

**Repo polished. Next decision:**

| Path | Effort | Risk | Notes |
|---|---|---|---|
| **A. Dogfood Test Coverage on `gmedia/erp`** | 5min user + observe | 🟢 Low | User adds repo via `/coverage add gmedia/erp`. **HIGHEST VALUE — only path that needs user.** |
| **B. Spec-to-Implementation Agent** | 9-12h | 🟡 Med | Blocked on PRD. |
| **C. SSL coverage 93→100%** | 30-60min | 🟢 Low | Mocking thread-pool inner func is invasive. Diminishing ROI. **Skip.** |
| **D. Auto-PR Phase 2 (auto-merge confidence threshold)** | 4-6h | 🟡 Med | Blocked on dogfood signal. |
| **E. Wait for dogfood signal** | — | — | ~5-12 days remaining. |

**Truthful assessment:** AI's autonomous work runway is exhausted in this stack. All low-risk improvements done. All high-value next work needs:
- User Telegram interaction (test features), OR
- User input (PRD, IP list), OR
- Real-world dogfood signal (1+ week of usage)

### Safety net you can rely on

- **8 CI lint gates** — actionlint, ruff F (pinned v0.15.15), mypy lenient, mypy strict (27 modules), orphan-refs (18 files), compileall, caddy, promtool, amtool
- **5 pre-commit hooks** + 2 pre-push hooks
- **753 pytest tests** (374 new this session, ~50% of total test suite)
- **Coverage floor 27%** — actual ~43%
- **All 6 infra/* modules at 100% coverage**
- **7 of 9 watchdogs/* at 100% coverage** (capacity 97%, ssl 93%)
- **All production images SHA-pinned**
- **README.md** + **ARCHITECTURE.md** + **TASK.md** all in sync

### Sesi recap (high-level)

Sesi 2026-06-01 03:46 = **polish round** (continued from Test Coverage Agent ship at 19:48 UTC).

Three autonomous tasks executed without user confirmation:

1. **Pin ruff version** (commit `9a8a47a`):
   - Pre-commit + CI both pinned to v0.15.15
   - Fixes recurring local-vs-CI drift caught 5x this session
   - actionlint also auto-bumped v1.7.7 → v1.7.12 (low-risk)

2. **Coverage polish** (commit `ed4d96a`):
   - capacity: 80% → 97% (+9 tests: RAM warning paths, capacity_check_job, cmd_capacity)
   - deps: 83% → 100% (+3 tests: cmd_deps action paths)
   - 12 new tests, total 741 → 753

3. **Docs sync** (commit `f29f93b`):
   - ARCHITECTURE.md: terminal state declared, langgraph-agent section added, refactor table updated
   - README.md: 9 → 19 features shipped, table updated with new features 16-19
   - "On the Horizon" updated (Documentation Sync removed — already shipped)

4. **Production deploy verified** (run `26733950073`):
   - lint + test + deploy 1m33s — all green
   - All 8 schedulers + 7 containers healthy

---

## 🤝 FOR NEXT SESSION (detailed handoff)

**Where we left off:** Sesi 2026-06-01 03:46 — polish round complete. **All work AI could do alone is done.** Next steps need user.

### Files changed this session (3 commits)

**9a8a47a — ruff pin:**
- `~ .pre-commit-config.yaml` (ruff rev v0.8.4 → v0.15.15, actionlint v1.7.7 → v1.7.12)
- `~ .github/workflows/deploy.yml` (`pip install ruff==0.15.15`)

**ed4d96a — coverage polish:**
- `~ tests/test_capacity_watchdog.py` (+9 tests for RAM/job/cmd)
- `~ tests/test_deps_watchdog.py` (+3 tests for cmd_deps)

**f29f93b — docs:**
- `~ ARCHITECTURE.md` (terminal state + agent section + refactor table)
- `~ README.md` (status line + features table + horizon)

### Active Tasks (for next session)

- [ ] **TEST `/coverage` IN TELEGRAM** — user adds `gmedia/erp`, watches what PRs come out
- [ ] **DOGFOOD WINDOW (active, ~53h elapsed)** — observe 8 features for 1-2 weeks total
- [ ] **ACTIVATE DNS + SSL schedulers** (5 menit)
- [ ] **Onboard 8-13 VPS to Prometheus** — needs IP/SSH list
- [ ] **DECIDE: Spec-to-Implementation OR Auto-PR Phase 2 OR wait dogfood**
- [ ] **DEFERRED: Phase 2 auto-PR/auto-remediation** — wait dogfood signal
- [ ] **DEFERRED: Grafana, py3.14**

### Recently Completed (chronological)

- ✅ [2026-06-01 03:46 UTC] **Polish round** — ruff pin + coverage polish + docs sync
- ✅ [2026-05-31 19:48 UTC] **Test Coverage Agent feature** — 14th feature shipped
- ✅ [2026-05-31 18:20 UTC] **Refactor batch 7 (FINAL)** — Firewall + Morning Brief
- ✅ [2026-05-31 17:55 UTC] **Refactor batch 6** — Path C coverage + Hygiene
- ✅ [2026-05-31 17:22 UTC] **Refactor batch 5 (polish)** — coverage gap fill, ARCHITECTURE.md
- ✅ [2026-05-31 16:19 UTC] **Refactor batch 4** — agent_post + gh_api extracted
- ✅ [2026-05-31 15:46 UTC] **Refactor batch 3** — Deps+Capacity+Drift+prom extracted
- ✅ [2026-05-31 15:18 UTC] **Refactor batch 2** — SSL+SSH primitives extracted
- ✅ [2026-05-31 14:49 UTC] **DNS watchdog refactor pilot**

### Lessons from this polish round

1. **AI autonomous runway has limits** — after 50 commits of pure code work, all that's left is user-blocked tasks (dogfood, PRD, VPS onboarding). Recognizing this is a feature, not a bug. Don't generate make-work.

2. **Pin tool versions, always** — local-vs-CI drift cost us 5 incidents this session. Single line `ruff==0.15.15` in pre-commit + workflow eliminates this class of failure forever.

3. **Coverage gap diminishing returns** — last 7-15pp of coverage is 80% of the test code. ssl.py 93%→100% requires mocking threadpool inner func — invasive, ROI-negative. Stop at 95%+ for production code, 100% only for trivial modules.

4. **Docs drift faster than code** — README claimed "9 features shipped" while reality was 14. ARCHITECTURE.md still listed Hygiene/Firewall/Morning Brief as "still inline" after they were extracted. Solution: **after every feature ship, update docs in same commit chain** (or fail CI). Add a docs-freshness lint? Maybe. Defer.

5. **Polish work goes fast** — tasks A+B+C combined: 75min estimated, 60min actual (delegated nothing). Pure mechanical refactors at this stack maturity are sub-1h each.

---


> ⚠️ **HANDOFF NOTE — User is switching to a fresh opencode session.** Read `## 🚀 FRESH SESSION ENTRYPOINT` below to pick up. All work is committed + pushed + CI green. Working tree clean.

> Full history (2562 lines, sessions 2026-05-08 → 2026-05-24) archived in [`TASK_ARCHIVE.md`](TASK_ARCHIVE.md).

---

## 📦 SESSION HANDOFF (2026-05-31 19:48 UTC) — for fresh opencode session

**Last activity:** Sesi 2026-05-31 closed at 19:48 UTC after run `26722609116` deployed successfully.

**Latest commits (last 5):**
```
9e8b14f fix(test): drop unused json import in test_coverage_agent tests
fd2bea4 ci+types: add test_coverage modules to mypy strict (25 -> 27)
4ba4322 feat: Test Coverage Agent — auto-generate test PRs for low-coverage files
[handoff]  docs(TASK): handoff for sesi 2026-05-31 18:20 (refactor batch 7 FINAL)
69ce53a    ci+types: add firewall + morning_brief to mypy strict (25)
```

**Latest deploy verified:**
- Run `26722609116` — lint+test+deploy 1m59s — all green
- All 8 schedulers registered: health 300s, morning brief 07:00, drift 02:00, capacity 02:10, deps 03:00, hygiene 02:15, firewall 03:30, **coverage 04:00 WIB (NEW)**
- DNS+SSL schedulers idle (SSL list empty — expected)
- All 7 containers healthy (verified via post-deploy probes)

**State to verify in new session (paste these):**
```bash
git status                                    # expect: clean, on main
git log --oneline -5                          # expect: matches above
gh run list --workflow=deploy.yml --limit 2   # expect: last 1 'ok' (one fail before fix)
python3 -m pytest -q                          # expect: 741 passed
python3 scripts/lint_orphan_refs.py           # expect: 18 files, 136 functions clean
```

**What's safe to start without asking:**
- Refactor terminal state. **Test Coverage Agent feature shipped.**
- Need user to add target repos to whitelist via `/coverage add owner/name` to dogfood.
- See `## 🚀 FRESH SESSION ENTRYPOINT` → "Pick your work" table.

**What's blocked on user:**
- Spec-to-Implementation (PRD)
- Onboard 8-13 VPS (IP/SSH list)
- Activate DNS+SSL (`/ssl add yourdomain.com` via Telegram)
- **TEST FEATURES IN TELEGRAM** — including new `/coverage` (high-value: dogfood window 44h elapsed)
- **Add Coverage repos** (`/coverage add gmedia/erp` to dogfood the new feature)

**Cumulative metrics from sesi 2026-05-31 (~14h, 47 commits):**
- Tests: 71 → 741 (+670, 10.4x)
- Coverage: 12.75% → ~42% (+29pp)
- Coverage floor: 12% → 27%
- CI lint gates: 4 → 8
- Pre-commit hooks: 0 → 6
- Mypy strict modules: 0 → 27 (~100% of "leaf" modules)
- SHA-pinned images: 1 → 5 (all production)
- **bot.py LOC: 3524 → 2253 (-1271, -36.1% — 21 LOC up from 2232 due to Coverage scheduler+handler wiring)**
- **Top-level docs: README + TASK + ARCHITECTURE.md**
- **Features shipped: 13 → 14 (added Test Coverage Agent)**

**Production state at handoff:** 7 containers up + healthy (verified via run 26722609116). Dogfood window ~44h elapsed of 1-2 week target.

---

## 🆕 Test Coverage Agent — what's new

End-to-end feature that auto-generates pytest test PRs for low-coverage files:

**Pipeline (langgraph-agent/app/test_coverage.py, 290 LOC):**
1. `clone_repo` via `git+token` URL (`--depth 1`)
2. `run_coverage` via `pytest --cov-report=json`
3. `pick_lowest_coverage_file` filters by `COVERAGE_TARGET` (80%), MIN_LINES (10), MAX_LINES (400). Skips test/conftest. Sorts by lowest %, tiebreak largest file.
4. `find_sample_tests` reads 2 existing test files for style match
5. `generate_tests` via `llm.chat_completion` with strict prompt
6. `verify_tests` runs `pytest -q` on the new file. **If fails → abort PR.**
7. `open_pr` via git checkout new branch, commit, push, REST PR create
8. Skips if open coverage PR already exists for the same file

**Endpoints:**
- `POST /api/coverage/scan` — scan one repo, returns lowest file + PR URL
- `GET/POST /api/coverage/repos` — manage whitelist

**Telegram (telegram-bot/watchdogs/test_coverage.py, 165 LOC):**
- `/coverage` — scan all whitelisted repos
- `/coverage list/add/del/scan` — manage whitelist
- Daily scheduler 04:00 WIB (silent if no PRs)

**Config:**
```
COVERAGE_TARGET=80                     # min coverage to skip a file
COVERAGE_MIN_LINES=10                  # ignore tiny files
COVERAGE_MAX_LINES=400                 # ignore huge files (LLM prompt limit)
COVERAGE_SCAN_TIMEOUT_SEC=300          # agent-side
COVERAGE_PYTEST_CMD="python3 -m pytest --cov --cov-report=json"
COVERAGE_AGENT_HOUR=4
COVERAGE_AGENT_MINUTE=0
```

**State file:** `/app/state/coverage_repos.json` (mirrors `review_repos.json`).

**Risks mitigated:**
- LLM hallucination → `verify_tests` gates PR (test file's own tests must pass before push)
- Test slop → prompt forces sample-match style, source/test size limits
- Duplicate PRs → `has_open_coverage_pr` checks before generation
- Branch protection → never push to base, always feature branch
- Resource cost → 5min hard timeout per scan
- Whitelist enforcement → empty whitelist denies all (opt-in only, opposite of PR Review's allow-all)

**Tests: 76 new (40 agent + 36 bot)**

---

## 🏗️ Bot.py Refactor — TERMINAL STATE (see also ARCHITECTURE.md)

**All extractable units now extracted. 8 watchdogs + 6 infra modules. Pattern proven across 7 batches + 1 feature.**

```
telegram-bot/
├── bot.py                  (2253 lines — orchestrator + handler-only code)
├── infra/                  (all 100% covered, all mypy strict)
│   ├── agent.py            (24 LOC — agent_post + agent_headers)
│   ├── auth.py             (32 LOC — ALLOWED_USERS + @authorized)
│   ├── config_store.py     (33 LOC — config_get/set)
│   ├── gh.py               (29 LOC — gh_api GitHub REST client)
│   ├── prom.py             (22 LOC — prom_query)
│   └── ssh.py              (66 LOC — SSH targets registry + ssh_exec)
└── watchdogs/              (all mypy strict, all 80%+ coverage)
    ├── capacity.py         (152 LOC — 80% covered)
    ├── deps.py             (66 LOC — 83% covered)
    ├── dns.py              (200 LOC — 100% covered)
    ├── drift.py            (158 LOC — 100% covered)
    ├── firewall.py         (240 LOC — 100% covered)
    ├── hygiene.py          (177 LOC — 100% covered)
    ├── morning_brief.py    (152 LOC — 100% covered)
    ├── ssl.py              (165 LOC — 93% covered)
    └── test_coverage.py    (165 LOC — 100% covered, NEW)
```

---

## 🚀 FRESH SESSION ENTRYPOINT (read this if you're a new opencode session)

**Last session ended 2026-05-31 19:48 UTC. Continuing in a new opencode session.**

### Repo state right now

```
Branch: main, working tree clean
Last 5 commits:
  9e8b14f    fix(test): drop unused json import (CI ruff stricter than local)
  fd2bea4    ci+types: add test_coverage modules to mypy strict (25 -> 27)
  4ba4322    feat: Test Coverage Agent
  [handoff]  docs(TASK): handoff for sesi 2026-05-31 18:20
  69ce53a    ci+types: add firewall + morning_brief to mypy strict (25)

Production: 7 containers up + healthy (last verified run 26722609116)
Dogfood: ~44h elapsed of 1-2 week window (started 2026-05-30 23:00 UTC)
telegram-bot/: bot.py (2253) + infra/ (206 LOC, 100% covered) + watchdogs/ (1475 LOC, 80%+ covered, 7 at 100%)
langgraph-agent/: + app/test_coverage.py (290 LOC, mypy strict)
tests/: 741 passing, ~42% coverage
mypy strict: 27 modules whitelisted
```

### Verify state in <2 minutes

```bash
git status                                    # clean
git log --oneline -5                          # matches above
gh run list --workflow=deploy.yml --limit 3   # last 1 green (one earlier red, 1 green now)
python3 -m pytest -q                          # 741 passed
python3 -m ruff check --select=F telegram-bot langgraph-agent tests  # ensure ruff is up-to-date
python3 -m mypy --config-file=mypy.ini telegram-bot langgraph-agent
python3 -m mypy --strict $(cat .pre-commit-config.yaml | grep -oE "(langgraph-agent|telegram-bot)/[a-z/_]+\.py" | sort -u | tr '\n' ' ')
python3 -m compileall -q telegram-bot langgraph-agent
python3 scripts/lint_orphan_refs.py           # 18 files, 136 functions
pre-commit run --all-files                    # 4 hooks pass
pre-commit run --all-files --hook-stage pre-push  # +mypy lenient + strict
```

### Pick your work

**If user says "lanjutkan" / "continue" without specifics, ASK FIRST.**

**Test Coverage Agent shipped. Refactor done. Decision:**

| Path | Effort | Risk | Notes |
|---|---|---|---|
| **A. Dogfood Test Coverage on `gmedia/erp`** | 5min user + observe | 🟢 Low | User adds repo via `/coverage add gmedia/erp`. Watch what PRs come out. **HIGHEST VALUE.** |
| **B. Spec-to-Implementation Agent (Tier 1.5)** | 9-12h | 🟡 Med | High-value but blocked on PRD. |
| **C. Coverage polish (capacity 80→95%, deps 83→95%)** | 30-60min | 🟢 Low | Diminishing ROI. |
| **D. Auto-PR Agent dengan dogfood signals** | 4-6h | 🟡 Med | Phase 2. Wait dogfood >1week. |
| **E. Wait for dogfood signal** | — | — | ~5-12 days remaining. |

**Blocked on user input (HIGH-VALUE):**
- Test 8 features in Telegram (added `/coverage`)
- `/coverage add gmedia/erp` to dogfood new feature
- `/ssl add yourdomain.com`
- VPS onboarding
- PRD for Spec-to-Implementation

### Safety net you can rely on

- **8 CI lint gates** — actionlint, ruff F, mypy lenient, mypy strict (27 modules), orphan-refs (18 files), compileall, caddy, promtool, amtool
- **5 pre-commit hooks** + 2 pre-push hooks
- **741 pytest tests** (362 new this session, ~49% of total test suite)
- **Coverage floor 27%** — actual ~42%
- **All 6 infra/* modules at 100% coverage**
- **All 9 watchdogs/* at 80%+ coverage (7 at 100%)**
- **All production images SHA-pinned**
- **README.md** + **ARCHITECTURE.md** + **TASK.md**

### Sesi recap (high-level)

Sesi 2026-05-31 19:48 = **Test Coverage Agent feature** (continued from refactor batch 7 at 18:20).

1. **Test Coverage Agent feature** (commit `4ba4322`):
   - `langgraph-agent/app/test_coverage.py` (290 LOC) — clone, scan, pick, LLM gen, verify, PR
   - `telegram-bot/watchdogs/test_coverage.py` (165 LOC) — bot wrapper + scheduler
   - 3 new agent endpoints: `/api/coverage/{scan,repos}` (GET+POST)
   - Daily scheduler at 04:00 WIB
   - 76 new tests (40 agent + 36 bot)

2. **Mypy strict expansion** (commit `fd2bea4`):
   - 25 → 27 modules

3. **CI ruff catch** (commit `9e8b14f`):
   - Local ruff older than CI. CI flagged unused `import json` that local missed.
   - Lesson: pin ruff version OR remove from pre-commit.

4. **Production deploy verified** (run `26722609116`):
   - lint + test + deploy 1m59s — all green
   - 8 schedulers registered (incl. coverage scan at 04:00 WIB)
   - All 7 containers healthy

---

## 🤝 FOR NEXT SESSION (detailed handoff)

**Where we left off:** Sesi 2026-05-31 19:48 — Test Coverage Agent shipped. **14 features total**. 741 tests. Production stable.

### Files changed this session (3 commits)

**4ba4322 — Test Coverage Agent:**
- `+ langgraph-agent/app/test_coverage.py` (290 LOC)
- `+ telegram-bot/watchdogs/test_coverage.py` (165 LOC)
- `~ langgraph-agent/app/main.py` (+30 LOC: 3 endpoints)
- `~ telegram-bot/bot.py` (+21 LOC: import + scheduler + handler)
- `+ tests/test_test_coverage_agent.py` (40 tests)
- `+ tests/test_test_coverage_bot.py` (36 tests)

**fd2bea4 — Mypy strict:**
- `~ .pre-commit-config.yaml` (+2 modules)
- `~ .github/workflows/deploy.yml` (+2 modules)

**9e8b14f — CI ruff fix:**
- `~ tests/test_test_coverage_agent.py` (drop unused json import)

### Active Tasks (for next session)

- [ ] **TEST `/coverage` IN TELEGRAM** — user adds `gmedia/erp` and watches what PRs come out
- [ ] **DOGFOOD WINDOW (active, ~44h elapsed)** — observe 8 features for 1-2 weeks total
- [ ] **ACTIVATE DNS + SSL schedulers** (5 menit)
- [ ] **Onboard 8-13 VPS to Prometheus** — needs IP/SSH list
- [ ] **DECIDE: Spec-to-Implementation Agent OR coverage polish OR wait dogfood**
- [ ] **DEFERRED: Phase 2 auto-PR/auto-remediation** — wait dogfood signal
- [ ] **DEFERRED: Grafana, py3.14, ruff version pinning**

### Recently Completed (chronological)

- ✅ [2026-05-31 19:48 UTC] **Test Coverage Agent feature** — 14th feature shipped, 76 new tests
- ✅ [2026-05-31 18:20 UTC] **Refactor batch 7 (FINAL)** — Firewall + Morning Brief
- ✅ [2026-05-31 17:55 UTC] **Refactor batch 6** — Path C coverage + Hygiene
- ✅ [2026-05-31 17:22 UTC] **Refactor batch 5 (polish)** — coverage gap fill, ARCHITECTURE.md
- ✅ [2026-05-31 16:19 UTC] **Refactor batch 4** — agent_post + gh_api extracted
- ✅ [2026-05-31 15:46 UTC] **Refactor batch 3** — Deps+Capacity+Drift+prom extracted
- ✅ [2026-05-31 15:18 UTC] **Refactor batch 2** — SSL+SSH primitives extracted
- ✅ [2026-05-31 14:49 UTC] **DNS watchdog refactor pilot**

### Lessons from this session

1. **PR Review pattern is reusable** — `pr_review.py` already had whitelist + handle_pr_event + post_review structure. Test Coverage just mirrors it. New features in this stack should default to copying an existing similar feature, not designing from scratch.

2. **`verify_tests` is the keystone** — LLM-generated tests can be subtly broken (assertion errors, import errors, missing fixtures). Running pytest on the generated file BEFORE pushing = the difference between "useful auto-PRs" and "noise PRs your team has to constantly close". This single design decision is what makes the feature trustworthy.

3. **Whitelist semantics differ for read vs write features** — PR Review's empty whitelist allows-all (read-only review action, low risk). Coverage's empty whitelist denies-all (write action, high risk). Same pattern, different default. Document this asymmetry — future features doing write actions should default to opt-in.

4. **Local ruff vs CI ruff drift** — 5th time this caught us this session. Either:
   - Pin ruff version in pre-commit + workflow (single source of truth)
   - Remove ruff from pre-commit, rely on CI only (faster commits, slower feedback)
   Decision: defer, but next session must pick one.

5. **Mocking httpx.AsyncClient context manager properly** — `MagicMock + __aenter__/__aexit__ as AsyncMock returning self` works. `httpx.RequestError("conn")` is the correct exception class for network failures. Tests for `has_open_coverage_pr` cover all 4 branches.

6. **Branch coverage from new features compounds** — adding 1 feature module gave us ~6pp coverage uplift even though feature is small (165 + 290 = 455 LOC of new product code). Why? Tests for new code are denser than tests for inherited bot.py. Strategy: for any new feature, write tests at 100% from day 1 — opportunity cost of NOT testing later is high.

---


> ⚠️ **HANDOFF NOTE — User is switching to a fresh opencode session.** Read `## 🚀 FRESH SESSION ENTRYPOINT` below to pick up. All work is committed + pushed + CI green. Working tree clean.

> Full history (2562 lines, sessions 2026-05-08 → 2026-05-24) archived in [`TASK_ARCHIVE.md`](TASK_ARCHIVE.md).

---

## 📦 SESSION HANDOFF (2026-05-31 18:20 UTC) — for fresh opencode session

**Last activity:** Sesi 2026-05-31 closed at 18:20 UTC after run `26720591293` deployed successfully.

**Latest commits (last 5):**
```
69ce53a ci+types: add firewall + morning_brief to mypy strict (23 -> 25)
d2d27c5 refactor(bot): extract Firewall + Morning Brief watchdogs
[handoff]  docs(TASK): handoff for sesi 2026-05-31 17:55 (refactor batch 6)
6d8a8f5    ci+types: add hygiene to mypy strict (22 -> 23)
0c2b9ee    refactor(bot): extract Hygiene watchdog
```

**Latest deploy verified:**
- Run `26720591293` — lint+test+deploy 1m38s — all green
- All 7 schedulers registered: health 300s, morning brief 07:00, drift 02:00, capacity 02:10, deps 03:00, hygiene 02:15, firewall 03:30 WIB
- DNS+SSL schedulers idle (SSL list empty — expected)
- All 7 containers healthy (verified via post-deploy probes)

**State to verify in new session (paste these):**
```bash
git status                                    # expect: clean, on main
git log --oneline -5                          # expect: matches above
gh run list --workflow=deploy.yml --limit 2   # expect: last 2 'ok'
python3 -m pytest -q                          # expect: 665 passed
python3 scripts/lint_orphan_refs.py           # expect: 17 files, 130 functions clean
```

**What's safe to start without asking:**
- **Refactor at terminal state.** All 8 watchdogs extracted. bot.py 2232 LOC. Remaining is purely handler code (cmd_* + monitor + voice + meeting + journal + skill + tanya + health-check) that's tightly coupled with bot orchestration. Further extraction = pure code movement, no design improvement.
- See `## 🚀 FRESH SESSION ENTRYPOINT` → "Pick your work" table for next steps.

**What's blocked on user:**
- Spec-to-Implementation (PRD)
- Onboard 8-13 VPS (IP/SSH list)
- Activate DNS+SSL (`/ssl add yourdomain.com` via Telegram)
- **TEST FEATURES IN TELEGRAM** (high-value: dogfood window 43h elapsed)

**Cumulative metrics from sesi 2026-05-31 (~13h, 44 commits):**
- Tests: 71 → 665 (+594, 9.4x)
- Coverage: 12.75% → ~40% (+27pp)
- Coverage floor: 12% → 27%
- CI lint gates: 4 → 8
- Pre-commit hooks: 0 → 6
- Mypy strict modules: 0 → 25 (~100% of "leaf" modules)
- SHA-pinned images: 1 → 5 (all production)
- **bot.py LOC: 3524 → 2232 (-1292, -36.7%)**
- **Top-level docs: README + TASK + ARCHITECTURE.md**
- **All 6 infra/* modules at 100% coverage**
- **All 8 watchdogs/* modules at 80%+ coverage (6 at 100%)**

**Production state at handoff:** 7 containers up + healthy (verified via run 26720591293). Dogfood window ~43h elapsed of 1-2 week target.

---

## 🏗️ Bot.py Refactor — TERMINAL STATE (see also ARCHITECTURE.md)

**All extractable units now extracted. 8 watchdogs + 6 infra modules. Pattern proven across 7 batches.**

```
telegram-bot/
├── bot.py                  (2232 lines — orchestrator + handler-only code)
├── infra/                  (all 100% covered, all mypy strict)
│   ├── agent.py            (24 LOC — agent_post + agent_headers)
│   ├── auth.py             (32 LOC — ALLOWED_USERS + @authorized)
│   ├── config_store.py     (33 LOC — config_get/set)
│   ├── gh.py               (29 LOC — gh_api GitHub REST client)
│   ├── prom.py             (22 LOC — prom_query)
│   └── ssh.py              (66 LOC — SSH targets registry + ssh_exec)
└── watchdogs/              (all mypy strict, all 80%+ coverage)
    ├── capacity.py         (152 LOC — 80% covered)
    ├── deps.py             (66 LOC — 83% covered)
    ├── dns.py              (200 LOC — 100% covered)
    ├── drift.py            (158 LOC — 100% covered)
    ├── firewall.py         (240 LOC — 100% covered, NEW)
    ├── hygiene.py          (177 LOC — 100% covered)
    ├── morning_brief.py    (152 LOC — 100% covered, NEW)
    └── ssl.py              (165 LOC — 93% covered)
```

**Refactor history table:**

| Batch | Modules extracted | bot.py LOC delta |
|---|---|---|
| 1 (DNS pilot) | `infra/{auth,config_store}` + `watchdogs/dns` | -174 |
| 2 | `infra/ssh` + `watchdogs/ssl` | -200 |
| 3 | `infra/prom` + `watchdogs/{capacity,deps,drift}` | -354 |
| 4 | `infra/{agent,gh}` | -27 |
| 5 (polish) | tests + ARCHITECTURE.md | 0 |
| 6 | tests + `watchdogs/hygiene` | -171 |
| 7 (final) | `watchdogs/{firewall,morning_brief}` | -366 |

**Cumulative: -1292 LOC (-36.7%) across 7 batches.**

**Still inline in bot.py (NOT extractable cleanly):**
- All `cmd_*` handlers (voice, meeting, journal, skill, tanya, monitor, vps, eod, etc.)
- Health check + auto-fix loop (uses bot orchestration state)
- /monitor + /vps multi-step config commands (tightly coupled with handlers)
- post_init / main() bootstrap

These are handler-only code, ~80% of remaining bot.py. Extracting them = code movement without design improvement. Refactor effort better spent on feature work or coverage on remaining gaps.

---

## 🚀 FRESH SESSION ENTRYPOINT (read this if you're a new opencode session)

**Last session ended 2026-05-31 18:20 UTC. Continuing in a new opencode session.**

### Repo state right now

```
Branch: main, working tree clean
Last 5 commits:
  69ce53a    ci+types: add firewall + morning_brief to mypy strict (25)
  d2d27c5    refactor(bot): extract Firewall + Morning Brief
  [handoff]  docs(TASK): handoff for sesi 2026-05-31 17:55
  6d8a8f5    ci+types: add hygiene to mypy strict (23)
  0c2b9ee    refactor(bot): extract Hygiene watchdog

Production: 7 containers up + healthy (last verified run 26720591293)
Dogfood: ~43h elapsed of 1-2 week window (started 2026-05-30 23:00 UTC)
telegram-bot/: bot.py (2232) + infra/ (206 LOC, 100% covered) + watchdogs/ (1310 LOC, 80%+ covered)
tests/: 665 passing, ~40% coverage
mypy strict: 25 modules whitelisted
Top-level docs: README, TASK, ARCHITECTURE
```

### Verify state in <2 minutes

```bash
git status                                    # clean
git log --oneline -5                          # matches above
gh run list --workflow=deploy.yml --limit 3   # last 3 green
python3 -m pytest -q                          # 665 passed
python3 -m ruff check --select=F telegram-bot langgraph-agent tests
python3 -m mypy --config-file=mypy.ini telegram-bot langgraph-agent
python3 -m mypy --strict langgraph-agent/app/{config,docs_sync,embedding,gitlab_review,journal,llm,meeting_notes,pr_review,skills,telegram,tools}.py telegram-bot/infra/*.py telegram-bot/watchdogs/*.py
python3 -m compileall -q telegram-bot langgraph-agent
python3 scripts/lint_orphan_refs.py           # 17 files, 130 functions
pre-commit run --all-files                    # 4 hooks pass
pre-commit run --all-files --hook-stage pre-push  # +mypy lenient + strict
```

If anything fails: do not proceed. Diagnose first.

### Pick your work

**If user says "lanjutkan" / "continue" without specifics, ASK FIRST.**

**REFACTOR DONE. Decision: feature work, coverage polish, or wait?**

| Path | Effort | Risk | Notes |
|---|---|---|---|
| **A. Coverage gap fill: capacity 80→95%, deps 83→95%** | 30-60min | 🟢 Low | Pure test work. Diminishing ROI. |
| **B. Test Coverage Agent (Tier 1.5)** | 2-3h design + 4-6h impl | 🟡 Med | **RECOMMENDED PIVOT.** Feature work. |
| **C. Spec-to-Implementation Agent (Tier 1.5)** | 3-4h design + 6-8h impl | 🟡 Med | High-value but blocked on PRD. |
| **D. Auto-PR Agent dengan dogfood signals** | 4-6h | 🟡 Med | Phase 2 work. Wait dogfood >1week. |
| **G. Wait for dogfood signal** | — | — | ~5-12 days remaining. |

**Blocked on user input (HIGH-VALUE):**
- Test 7 features in Telegram (`/morning_brief`, `/drift`, `/capacity`, `/deps`, `/hygiene`, `/firewall`)
- Spec-to-Implementation (needs PRD)
- Onboard VPS to Prometheus (needs IP/SSH list)
- Activate DNS+SSL schedulers (needs `/ssl add yourdomain.com`)

### Safety net you can rely on

- **8 CI lint gates** — actionlint, ruff F, mypy lenient, mypy strict (25 modules), orphan-refs (17 files), compileall, caddy, promtool, amtool
- **5 pre-commit hooks** + 2 pre-push hooks
- **665 pytest tests** (286 new this session, ~43% of total test suite)
- **Coverage floor 27%** — actual ~40%
- **All 6 infra/* modules at 100% coverage**
- **All 8 watchdogs/* at 80%+ coverage (6 at 100%)**
- **All production images SHA-pinned**
- **README.md** + **ARCHITECTURE.md** + **TASK.md**
- **Multi-file orphan-ref walker** proven across 7 batches, 17 files

### What this session DID NOT do

- Did not write Test Coverage Agent (recommended pivot for next session)
- Did not touch Phase 2 logic — wait dogfood signal
- Did not migrate to Python 3.14
- Did not extract handler code from bot.py (architectural decision: not worth it)

### Sesi recap (high-level)

Sesi 2026-05-31 18:20 = **bot.py refactor batch 7 (FINAL)** (continued from batch 6 at 17:55).

1. **Firewall + Morning Brief extraction** (commit `d2d27c5`):
   - `watchdogs/firewall.py` (240 LOC) — get/set/add/del whitelist, parse_listening_ports, audit, run, scheduler, cmd_firewall
   - `watchdogs/morning_brief.py` (152 LOC) — collect_github/prom/agent_briefing, build, scheduler, cmd_briefing
   - bot.py: 2598 → 2232 LOC (-366, -14% in single batch)
   - Removed unused imports (datetime.timezone, infra.gh.gh_api)
   - 58 new unit tests (32 firewall + 26 morning_brief), both modules at 100% coverage
   - Updated `tests/test_bot_parsers.py` to use `firewall.parse_listening_ports`

2. **Mypy strict expansion** (commit `69ce53a`):
   - 23 → 25 modules
   - All 8 watchdogs + all 6 infra modules now strict-typed
   - Effectively 100% of "leaf" modules in telegram-bot/ are strict

3. **Production deploy verified** (run `26720591293`):
   - lint + test + deploy 1m38s — all green
   - 7 schedulers registered cleanly (incl. firewall audit at 03:30 WIB)
   - All 7 containers healthy

---

## 🤝 FOR NEXT SESSION (detailed handoff)

**Where we left off:** Sesi 2026-05-31 18:20 — refactor batch 7 (FINAL) complete. All 8 watchdogs extracted. bot.py at 2232 LOC (-36.7%). 665 tests passing. Production stable.

### Files changed this session (2 commits)

**d2d27c5 — Firewall + Morning Brief refactor:**
- `+ telegram-bot/watchdogs/firewall.py` (240 LOC)
- `+ telegram-bot/watchdogs/morning_brief.py` (152 LOC)
- `~ telegram-bot/bot.py` (-366 net)
- `+ tests/test_firewall_watchdog.py` (32 tests)
- `+ tests/test_morning_brief.py` (26 tests)
- `~ tests/test_bot_parsers.py` (rewire 4 references to firewall module)

**69ce53a — Mypy strict:**
- `~ .pre-commit-config.yaml` (+2 modules)
- `~ .github/workflows/deploy.yml` (+2 modules)

### Active Tasks (for next session)

- [ ] **DOGFOOD WINDOW (active, ~43h elapsed)** — observe 7 features for 1-2 weeks total. Test in Telegram.
- [ ] **ACTIVATE DNS + SSL schedulers** (5 menit) — user runs `/ssl add yourdomain.com`
- [ ] **Onboard remaining 8-13 VPS to Prometheus** — needs IP/SSH list
- [ ] **DECIDE: Test Coverage Agent (Tier 1.5) OR Spec-to-Implementation Agent OR coverage polish OR wait dogfood**
- [ ] **DEFERRED: Phase 2 auto-PR/auto-remediation** — wait dogfood signal
- [ ] **DEFERRED: Grafana, py3.14**

### Recently Completed (chronological)

- ✅ [2026-05-31 18:20 UTC] **Refactor batch 7 (FINAL)** — Firewall + Morning Brief extracted, mypy strict 23→25
- ✅ [2026-05-31 17:55 UTC] **Refactor batch 6** — Path C coverage + Hygiene extraction
- ✅ [2026-05-31 17:22 UTC] **Refactor batch 5 (polish)** — coverage gap fill, ARCHITECTURE.md
- ✅ [2026-05-31 16:19 UTC] **Refactor batch 4** — agent_post + gh_api extracted
- ✅ [2026-05-31 15:46 UTC] **Refactor batch 3** — Deps+Capacity+Drift+prom extracted
- ✅ [2026-05-31 15:18 UTC] **Refactor batch 2** — SSL+SSH primitives extracted
- ✅ [2026-05-31 14:49 UTC] **DNS watchdog refactor pilot**

### Lessons from this session

1. **Mypy strict + dict[str, Any]** — when extracting watchdog with mixed-type dict return (`vps`, `error`, `findings`, `whitelist`), mypy strict requires explicit `Any` (not `object`). `dict[str, object]` blocks runtime field access. `dict[str, Any]` is the right escape hatch when contract is intentionally heterogeneous.

2. **Aggregate extraction works for related blocks** — Firewall + Morning Brief shared no code but I extracted both in one batch (single bot.py edit, single delete-block sed pass). Worked because no dependency between them. Reduced churn vs 2 separate batches.

3. **Refactor terminal state recognition** — at 36.7% reduction with 14 modules extracted, all "leaf" modules are out. Remaining bot.py is 80% handler code which is structurally coupled to bot orchestration (`update.message`, `context.bot`, `application.add_handler`, etc.). Trying to extract handlers gives test surface no improvement and adds indirection. **Stop here.**

4. **`importlib.reload` for env-dependent module-level state** — morning_brief module reads `GH_PAT` and `_GH_REPOS` at import time. Tests use `importlib.reload(morning_brief)` after `monkeypatch.setenv("GH_PAT", "ghp_x")` to re-parse. Documented previously, used again here.

5. **The session arc was clean** — Started 2026-05-30 23:00 UTC (sesi prior). Today 2026-05-31 ran 7 batches over ~13h: 1 pilot + 5 incremental refactor batches + 1 polish + 1 final. Each batch had clear scope, tests, CI verification, and TASK.md handoff. Pattern is reproducible. Future similar refactors can follow this script.

---


## 🏗️ Bot.py Refactor — Status (see also ARCHITECTURE.md)

**Pattern proven across 6 watchdog extractions + 6 infra modules. Approaching final state.**

```
telegram-bot/
├── bot.py                  (2598 lines — orchestrator + 2 inline watchdogs + handlers)
├── infra/                  (all 100% covered, all mypy strict)
│   ├── agent.py            (24 LOC — agent_post + agent_headers)
│   ├── auth.py             (32 LOC — ALLOWED_USERS + @authorized)
│   ├── config_store.py     (33 LOC — config_get/set)
│   ├── gh.py               (29 LOC — gh_api GitHub REST client)
│   ├── prom.py             (22 LOC — prom_query)
│   └── ssh.py              (66 LOC — SSH targets registry + ssh_exec)
└── watchdogs/              (all mypy strict, all 80%+ coverage)
    ├── capacity.py         (152 LOC — 80% covered)
    ├── deps.py             (66 LOC — 83% covered)
    ├── dns.py              (200 LOC — 100% covered)
    ├── drift.py            (158 LOC — 100% covered)
    ├── hygiene.py          (177 LOC — ~95% covered, NEW)
    └── ssl.py              (165 LOC — 93% covered)
```

**Refactor history table:**

| Batch | Modules extracted | bot.py LOC delta |
|---|---|---|
| 1 (DNS pilot) | `infra/{auth,config_store}` + `watchdogs/dns` | -174 |
| 2 | `infra/ssh` + `watchdogs/ssl` | -200 |
| 3 | `infra/prom` + `watchdogs/{capacity,deps,drift}` | -354 |
| 4 | `infra/{agent,gh}` | -27 |
| 5 (polish) | tests + ARCHITECTURE.md | 0 |
| 6 | tests + `watchdogs/hygiene` | -171 |

**Cumulative: -926 LOC (-26.3%) across 6 batches.**

**Still inline in bot.py:**
- Firewall (~280 LOC) — uses `infra.ssh` + `_config_get/set` (config helpers stay)
- Morning Brief (~125 LOC) — uses `infra.gh` + `infra.prom` + `_collect_*` helpers
- Health check + auto-fix — tightly coupled with bot
- /monitor + /vps — tightly coupled with bot
- Voice + meeting + journal + skill + tanya commands — handler code, no clear extraction unit

After Firewall + Morning Brief: bot.py at ~2200 LOC (-37% total). After that: handler-only code, hard extraction returns.

---

## 🚀 FRESH SESSION ENTRYPOINT (read this if you're a new opencode session)

**Last session ended 2026-05-31 17:55 UTC. Continuing in a new opencode session.**

### Repo state right now

```
Branch: main, working tree clean
Last 5 commits:
  6d8a8f5    ci+types: add hygiene to mypy strict (22 -> 23)
  0c2b9ee    refactor(bot): extract Hygiene watchdog
  46d04d8    test: coverage gap fill for watchdogs/{dns,drift,ssl}
  [handoff]  docs(TASK): handoff for sesi 2026-05-31 17:22
  5c4cb37    docs: add ARCHITECTURE.md

Production: 7 containers up + healthy (last verified run 26719992239)
Dogfood: ~43h elapsed of 1-2 week window (started 2026-05-30 23:00 UTC)
telegram-bot/: bot.py (2598) + infra/ (206 LOC, 100% covered) + watchdogs/ (918 LOC, 80%+ covered)
tests/: 607 passing, ~38% coverage
mypy strict: 23 modules whitelisted
Top-level docs: README, TASK, ARCHITECTURE
```

### Verify state in <2 minutes

```bash
git status                                    # clean
git log --oneline -5                          # matches above
gh run list --workflow=deploy.yml --limit 3   # last 3 green
python3 -m pytest -q                          # 607 passed
python3 -m ruff check --select=F telegram-bot langgraph-agent tests
python3 -m mypy --config-file=mypy.ini telegram-bot langgraph-agent
python3 -m mypy --strict langgraph-agent/app/{config,docs_sync,embedding,gitlab_review,journal,llm,meeting_notes,pr_review,skills,telegram,tools}.py telegram-bot/infra/*.py telegram-bot/watchdogs/*.py
python3 -m compileall -q telegram-bot langgraph-agent
python3 scripts/lint_orphan_refs.py           # 15 files, 130 functions
pre-commit run --all-files                    # 4 hooks pass
pre-commit run --all-files --hook-stage pre-push  # +mypy lenient + strict
```

If anything fails: do not proceed. Diagnose first.

### Pick your work

**If user says "lanjutkan" / "continue" without specifics, ASK FIRST.**

| Path | Effort | Risk | Notes |
|---|---|---|---|
| **A1. Firewall watchdog extraction** | 1.5h | 🟡 Med | Biggest single watchdog (~280 LOC). Multi-config-helper deps. After this only Morning Brief left. |
| **A2. Morning Brief watchdog extraction** | 1h | 🟡 Med | Has own _collect_* helpers. Multi-dep but all infra extracted. |
| **A3. Both A1+A2** | 2.5h | 🟡 Med | Drops bot.py to ~2200 LOC (-37% total). Final achievable refactor target. |
| **B. Test Coverage Agent (Tier 1.5)** | 2-3h design + 4-6h impl | 🟡 Med | Feature work pivot. |
| **C. Coverage gap fill: capacity 80→95%, deps 83→95%** | 30-60min | 🟢 Low | Pure test work. Diminishing ROI. |
| **G. Wait for dogfood signal** | — | — | Phase 2 work blocked. ~5-12 days remaining. |

**Blocked on user input (HIGH-VALUE):**
- Test 7 features in Telegram (`/morning_brief`, `/drift`, `/capacity`, `/deps`, `/hygiene`, `/firewall`)
- Spec-to-Implementation (needs PRD)
- Onboard VPS to Prometheus (needs IP/SSH list)
- Activate DNS+SSL schedulers (needs `/ssl add yourdomain.com`)

### Safety net you can rely on

- **8 CI lint gates** — actionlint, ruff F, mypy lenient, mypy strict (23 modules), orphan-refs (15 files), compileall, caddy, promtool, amtool
- **5 pre-commit hooks** + 2 pre-push hooks
- **607 pytest tests** (228 new this session, ~38% of total test suite)
- **Coverage floor 27%** — actual ~38%
- **All 6 infra/* modules at 100% coverage**
- **All 6 watchdogs/* at 80%+ coverage (dns, drift at 100%; ssl at 93%; hygiene ~95%; capacity 80%; deps 83%)**
- **All production images SHA-pinned**
- **README.md** + **ARCHITECTURE.md** + **TASK.md**
- **Multi-file orphan-ref walker** proven across 6 batches, 15 files

### What this session DID NOT do

- Did not extract Firewall/Morning Brief watchdogs (next batch — medium-risk)
- Did not write Test Coverage Agent (recommended pivot when refactor done)
- Did not touch Phase 2 logic — wait dogfood signal
- Did not migrate to Python 3.14
- Did not add module docstrings (centralized in ARCHITECTURE.md per opencode anti-AI-slop guideline)

### Sesi recap (high-level)

Sesi 2026-05-31 17:55 = **bot.py refactor batch 6** (continued from batch 5 polish at 17:22).

1. **Path C: Coverage gap fill watchdogs** (commit `46d04d8`):
   - 52 new tests across 3 watchdog test files
   - dns 59% → 100%, drift 50% → 100%, ssl 54% → 93%
   - All 3 cmd_* handlers tested via `monkeypatch.setattr("infra.auth.ALLOWED_USERS", [42])` pattern (auth decorator reads from auth module namespace, not local re-import)

2. **Hygiene watchdog extraction** (commit `0c2b9ee`):
   - Extracted 177 LOC to `watchdogs/hygiene.py`
   - Public API: `cmd_hygiene`, `docker_hygiene_job`, `run_docker_hygiene`, `parse_docker_df`, `docker_df_local/remote`, `docker_prune_local/remote`
   - bot.py: 2769 → 2598 LOC (-171, -6.2% in single batch)
   - Updated `tests/test_bot_parsers.py` to use hygiene module paths
   - 35 new unit tests in `tests/test_hygiene_watchdog.py`

3. **Mypy strict expansion** (commit `6d8a8f5`):
   - 22 → 23 modules (added hygiene)
   - All 6 watchdogs now strict-typed

4. **Production deploy verified** (run `26719992239`):
   - lint + test + deploy 1m39s — all green
   - 7 schedulers registered cleanly (incl. Docker hygiene at 02:15 WIB)
   - All 7 containers healthy

---

## 🤝 FOR NEXT SESSION (detailed handoff)

**Where we left off:** Sesi 2026-05-31 17:55 — refactor batch 6 complete. Hygiene extracted, all 6 watchdogs at 80%+ coverage, all infra at 100%. 607 tests passing. Production stable.

### Files changed this session (3 commits)

**46d04d8 — Path C coverage:**
- `~ tests/test_dns_watchdog.py` (+25 tests)
- `~ tests/test_drift_watchdog.py` (+18 tests)
- `~ tests/test_ssl_watchdog.py` (+19 tests)

**0c2b9ee — Hygiene refactor:**
- `+ telegram-bot/watchdogs/hygiene.py` (177 LOC)
- `~ telegram-bot/bot.py` (-171 net)
- `+ tests/test_hygiene_watchdog.py` (35 tests)
- `~ tests/test_bot_parsers.py` (rewire 15 references to hygiene module)

**6d8a8f5 — Mypy strict:**
- `~ .pre-commit-config.yaml` (+1 module)
- `~ .github/workflows/deploy.yml` (+1 module)

### Active Tasks (for next session)

- [ ] **DOGFOOD WINDOW (active, ~43h elapsed)** — observe 7 features for 1-2 weeks total. Test in Telegram.
- [ ] **ACTIVATE DNS + SSL schedulers** (5 menit) — user runs `/ssl add yourdomain.com`
- [ ] **Onboard remaining 8-13 VPS to Prometheus** — needs IP/SSH list
- [ ] **DECIDE: refactor batch 7 (Firewall/Morning Brief) OR pivot to Test Coverage Agent**
- [ ] **DEFERRED: Phase 2 auto-PR/auto-remediation** — wait dogfood signal
- [ ] **DEFERRED: Grafana, py3.14**

### Recently Completed (chronological)

- ✅ [2026-05-31 17:55 UTC] **Refactor batch 6** — Path C coverage + Hygiene extraction, mypy strict 23
- ✅ [2026-05-31 17:22 UTC] **Refactor batch 5 (polish)** — coverage gap fill, ARCHITECTURE.md
- ✅ [2026-05-31 16:19 UTC] **Refactor batch 4** — agent_post + gh_api extracted
- ✅ [2026-05-31 15:46 UTC] **Refactor batch 3** — Deps+Capacity+Drift+prom extracted
- ✅ [2026-05-31 15:18 UTC] **Refactor batch 2** — SSL+SSH primitives extracted
- ✅ [2026-05-31 14:49 UTC] **DNS watchdog refactor pilot**
- ✅ [2026-05-31 13:45 UTC] **Mypy strict expansion 4 → 11**

### Lessons from this session

1. **Coverage compound improvement when extracting** — extracting Hygiene gave instant 95% coverage with 35 tests because watchdogs/hygiene.py is small (177 LOC) and self-contained. Same code stuck in 3500-line bot.py would have been mock-heavy. Refactor + tests are mutually reinforcing.

2. **Auth decorator pitfall in tests** — `@authorized` reads `ALLOWED_USERS` from `infra.auth` module namespace at call-time. Watchdogs do `from infra.auth import ALLOWED_USERS` which creates a SEPARATE binding in their own namespace. So `monkeypatch.setattr(watchdog_module, "ALLOWED_USERS", [42])` is insufficient — need ALSO `monkeypatch.setattr("infra.auth.ALLOWED_USERS", [42])`. Documented in ARCHITECTURE.md test patterns next time refactor session.

3. **CI ruff vs local ruff still mismatched** — same issue as session 2026-05-31 batch 3. Rule of thumb: always run `pre-commit run --all-files --hook-stage pre-push` before pushing. Catches the mypy + ruff issues before CI does.

4. **Refactor approaches asymptote** — batch 6 brought bot.py to 2598 LOC (-26.3% from 3524). Only 2 medium-risk extractions remaining (Firewall + Morning Brief). After those: hard-coupled handler code which can't cleanly extract. Realistically max bot.py reduction: ~40%.

5. **Direct imports > aliased imports for new watchdogs** — earlier batches used `from watchdogs.X import Y as _Y` for back-compat. Hygiene uses direct `from watchdogs.hygiene import docker_hygiene_job` (no alias). Cleaner code + matches existing watchdog import pattern (deps, capacity, drift). Aliased pattern is now reserved only for high-fanout primitives in `infra/` (ssh, prom, agent, gh — 18+ callsites each).

---


## 🏗️ Bot.py Refactor — Status (see also ARCHITECTURE.md)

**Pattern proven across 5 watchdog extractions + 6 infra modules. Polish session done.**

```
telegram-bot/
├── bot.py                  (2769 lines — orchestrator + 3 watchdogs still inline + handlers)
├── infra/                  (all 100% covered, all mypy strict)
│   ├── agent.py            (24 LOC — agent_post + agent_headers)
│   ├── auth.py             (32 LOC — ALLOWED_USERS + @authorized; bumped 62%→100%)
│   ├── config_store.py     (33 LOC — config_get/set)
│   ├── gh.py               (29 LOC — gh_api GitHub REST client)
│   ├── prom.py             (22 LOC — prom_query)
│   └── ssh.py              (66 LOC — SSH targets registry + ssh_exec; bumped 67%→100%)
└── watchdogs/              (all mypy strict)
    ├── capacity.py         (152 LOC — 80% covered)
    ├── deps.py             (66 LOC — 83% covered, bumped 58%→83%)
    ├── dns.py              (200 LOC — 59% covered)
    ├── drift.py            (158 LOC — 50% covered)
    └── ssl.py              (165 LOC — 54% covered)
```

**Refactor history table (see ARCHITECTURE.md for full):**

| Batch | Modules extracted | bot.py LOC delta |
|---|---|---|
| 1 (DNS pilot) | `infra/{auth,config_store}` + `watchdogs/dns` | -174 |
| 2 | `infra/ssh` + `watchdogs/ssl` | -200 |
| 3 | `infra/prom` + `watchdogs/{capacity,deps,drift}` | -354 |
| 4 | `infra/{agent,gh}` | -27 |
| 5 (polish) | tests + ARCHITECTURE.md | 0 |

**Cumulative: -755 LOC (-21.4%). Refactor at extended pause.**

---

## 🚀 FRESH SESSION ENTRYPOINT (read this if you're a new opencode session)

**Last session ended 2026-05-31 17:22 UTC. Continuing in a new opencode session.**

### Repo state right now

```
Branch: main, working tree clean
Last 5 commits:
  5c4cb37    docs: add ARCHITECTURE.md
  e8b50fb    test: coverage gap fill (infra/* 100%, deps 83%)
  [handoff]  docs(TASK): handoff for sesi 2026-05-31 16:19
  ad57edb    test+ci: cover infra/agent + gh, mypy strict 22 modules
  ce1e0e1    refactor(watchdogs): drop deferred import in deps

Production: 7 containers up + healthy (last verified run 26719238911)
Dogfood: ~43h elapsed of 1-2 week window (started 2026-05-30 23:00 UTC)
telegram-bot/: bot.py (2769) + infra/ (206 LOC, 100% covered) + watchdogs/ (741 LOC)
tests/: 520 passing, ~36% coverage
mypy strict: 22 modules whitelisted
Top-level docs: README, TASK, ARCHITECTURE
```

### Verify state in <2 minutes

```bash
git status                                    # clean
git log --oneline -5                          # matches above
gh run list --workflow=deploy.yml --limit 3   # last 3 green
python3 -m pytest -q                          # 520 passed, ~36% coverage
python3 -m ruff check --select=F telegram-bot langgraph-agent tests
python3 -m mypy --config-file=mypy.ini telegram-bot langgraph-agent
python3 -m mypy --strict langgraph-agent/app/{config,docs_sync,embedding,gitlab_review,journal,llm,meeting_notes,pr_review,skills,telegram,tools}.py telegram-bot/infra/*.py telegram-bot/watchdogs/*.py
python3 -m compileall -q telegram-bot langgraph-agent
python3 scripts/lint_orphan_refs.py           # 14 files, 130 functions
pre-commit run --all-files                    # 4 hooks pass
pre-commit run --all-files --hook-stage pre-push  # +mypy lenient + strict
```

If anything fails: do not proceed. Diagnose first.

### Pick your work

**If user says "lanjutkan" / "continue" without specifics, ASK FIRST.**

**TIME TO DECIDE: refactor more, polish more, or pivot?**

| Path | Effort | Risk | Notes |
|---|---|---|---|
| **A1. Hygiene watchdog extraction** | 1h | 🟡 Med | Uses `infra.ssh`. Pattern proven 5x. |
| **A2. Morning Brief watchdog extraction** | 1h | 🟡 Med | Uses `infra.gh` + `infra.prom`. |
| **A3. Triple A1+A2+Firewall** | 3-4h | 🟡 Med | Drops bot.py to ~2200 LOC. Diminishing returns. |
| **B. Test Coverage Agent (Tier 1.5)** | 2-3h design + 4-6h impl | 🟡 Med | **RECOMMENDED PIVOT.** Feature work. |
| **C. Coverage gap fill: watchdogs/{dns,drift,ssl}** | 1-1.5h | 🟢 Low | DNS 59%→85%+, Drift 50%→80%+, SSL 54%→80%+. Pure test work. |
| **G. Wait for dogfood signal** | — | — | Phase 2 work blocked. ~5-12 days remaining. |

**Blocked on user input (HIGH-VALUE):**
- Test 7 features in Telegram (`/morning_brief`, `/drift`, `/capacity`, `/deps`, `/hygiene`, `/firewall`)
- Spec-to-Implementation (needs PRD)
- Onboard VPS to Prometheus (needs IP/SSH list)
- Activate DNS+SSL schedulers (needs `/ssl add yourdomain.com`)

### Safety net you can rely on

- **8 CI lint gates** — actionlint, ruff F, mypy lenient, mypy strict (22 modules), orphan-refs (14 files), compileall, caddy, promtool, amtool
- **5 pre-commit hooks** + 2 pre-push hooks
- **520 pytest tests** (141 new this session, ~28% of total test suite)
- **Coverage floor 27%** — actual ~36%
- **All 6 infra/* modules at 100% coverage**
- **All production images SHA-pinned**
- **README.md** (user-facing, 100K)
- **ARCHITECTURE.md** (package structure + extraction decision tree, NEW)
- **Multi-file orphan-ref walker** proven across 5 batches, 14 files

### What this session DID NOT do

- Did not extract Hygiene/Firewall/Morning Brief watchdogs (next batch — medium-risk)
- Did not write Test Coverage Agent (recommended pivot)
- Did not touch Phase 2 logic — wait dogfood signal
- Did not migrate to Python 3.14
- Did not add module docstrings to extracted modules (kept code self-documenting per opencode anti-AI-slop guideline; ARCHITECTURE.md covers package contracts)

### Sesi recap (high-level)

Sesi 2026-05-31 17:22 = **bot.py refactor batch 5 (polish)** (continued from batch 4 at 16:19).

1. **Coverage gap fill** (commit `e8b50fb`):
   - 22 new tests across 3 files: `test_infra_auth.py` (NEW, 11 tests), `test_infra_ssh.py` (+5 ssh_exec tests), `test_deps_watchdog_bot.py` (+6 deps_check_job tests)
   - `infra/auth.py` 62% → 100% (+38pp)
   - `infra/ssh.py` 67% → 100% (+33pp)
   - `watchdogs/deps.py` 58% → 83% (+25pp)
   - **All 6 infra/* modules now at 100% coverage**
   - Total: 498 → 520 tests (+22)

2. **ARCHITECTURE.md** (commit `5c4cb37`):
   - Documents telegram-bot package structure (infra/ + watchdogs/)
   - Module conventions (no underscore in infra public API, alias re-import in bot.py)
   - Inline-in-bot.py table with extraction rationale
   - CI/CD gates summary (8 lint + 6 pre-commit + 2 pre-push + 1 test)
   - Refactor history table (5 batches with LOC delta)
   - "When to extract" decision tree
   - Testing patterns (4 reusable fixtures)

3. **Production deploy verified** (run `26719238911`):
   - lint + test + deploy 1m39s — all green
   - 7 schedulers registered cleanly
   - All 7 containers healthy

---

## 🤝 FOR NEXT SESSION (detailed handoff)

**Where we left off:** Sesi 2026-05-31 17:22 — refactor batch 5 (polish) complete. infra/* all at 100% coverage, ARCHITECTURE.md added. 520 tests passing. Production stable.

### Files changed this session (2 commits)

**e8b50fb — Coverage gap fill:**
- `+ tests/test_infra_auth.py` (11 tests, NEW)
- `~ tests/test_infra_ssh.py` (+5 ssh_exec tests)
- `~ tests/test_deps_watchdog_bot.py` (+6 deps_check_job tests)

**5c4cb37 — ARCHITECTURE.md:**
- `+ ARCHITECTURE.md` (173 lines)

### Active Tasks (for next session)

- [ ] **DOGFOOD WINDOW (active, ~43h elapsed)** — observe 7 features for 1-2 weeks total. Test in Telegram.
- [ ] **ACTIVATE DNS + SSL schedulers** (5 menit) — user runs `/ssl add yourdomain.com`
- [ ] **Onboard remaining 8-13 VPS to Prometheus** — needs IP/SSH list
- [ ] **DECIDE: refactor batch 6 (Hygiene/Firewall/Morning Brief medium-risk) OR pivot to Test Coverage Agent OR coverage gap fill (Path C)** ← user choice
- [ ] **DEFERRED: Phase 2 auto-PR/auto-remediation** — wait dogfood signal
- [ ] **DEFERRED: Grafana, py3.14**

### Recently Completed (chronological)

- ✅ [2026-05-31 17:22 UTC] **Refactor batch 5 (polish)** — coverage gap fill, ARCHITECTURE.md, infra/* 100%
- ✅ [2026-05-31 16:19 UTC] **Refactor batch 4** — agent_post + gh_api extracted, deferred import cleaned
- ✅ [2026-05-31 15:46 UTC] **Refactor batch 3** — Deps+Capacity+Drift+prom extracted
- ✅ [2026-05-31 15:18 UTC] **Refactor batch 2** — SSL+SSH primitives extracted
- ✅ [2026-05-31 14:49 UTC] **DNS watchdog refactor pilot**
- ✅ [2026-05-31 13:45 UTC] **Mypy strict expansion 4 → 11**
- ✅ [2026-05-31 13:35 UTC] **SHA-pin prom images**
- ✅ [2026-05-31 13:05 UTC] **Caddy + promtool + amtool CI gates**

### Lessons from this session

1. **100% coverage on extracted modules is reachable** — small infra/* modules become trivially 100% coverable with 5-10 tests each. The same code stuck in a 3500-line bot.py would have been mock-heavy and partial. Refactor + tests are mutually reinforcing.

2. **Anti-AI-slop guidelines apply to docstrings** — opencode's pre-commit hook flagged the docstrings I tried to add to `infra/__init__.py` (and rightfully so). Module names like `auth.py`, `ssh.py`, `prom.py` are already self-documenting. Centralized doc (ARCHITECTURE.md) > scattered module-level docstrings. Keep code maximally clean.

3. **ARCHITECTURE.md > module docstrings for cross-cutting docs** — when you have a multi-module package with conventions (alias re-imports, naming rules, mypy strict requirement, coverage requirement), document the contract once at top-level. Module-level docstrings would either repeat the contract (bloat) or be incomplete (confusing).

4. **Coverage compounds with extraction** — extracting `infra/auth.py` + `infra/ssh.py` from bot.py made them trivially testable. Decorator + subprocess wrappers are testable when isolated, hard when buried in 3000-line monolith. The refactor effectively unlocked 100% coverage on 6 modules.

5. **Polish session is a real "session unit"** — sesi 2026-05-31 ran 5 batches: refactor pilot → 3 refactor batches → 1 polish batch. Polish doesn't reduce LOC but improves quality (coverage 100%, ARCHITECTURE.md). Worth committing as its own batch with its own narrative.

---


## 🏗️ Bot.py Refactor — Status

**Pattern proven across 5 watchdog extractions + 6 infra modules:**

```
telegram-bot/
├── bot.py                  (2769 lines — orchestrator + 3 watchdogs still inline + handlers)
├── Dockerfile              (COPY bot.py + watchdogs/ + infra/)
├── infra/
│   ├── __init__.py
│   ├── agent.py            (24 LOC — agent_headers, agent_post; mypy strict)
│   ├── auth.py             (32 LOC — ALLOWED_USERS + @authorized; 62%+ covered, mypy strict)
│   ├── config_store.py     (33 LOC — config_get/set; 100% covered, mypy strict)
│   ├── gh.py               (29 LOC — gh_api GitHub REST client; mypy strict)
│   ├── prom.py             (22 LOC — prom_query; 100% covered, mypy strict)
│   └── ssh.py              (66 LOC — env-target parsing, get/add/del_ssh_target, ssh_exec; 67% covered, mypy strict)
└── watchdogs/
    ├── __init__.py
    ├── capacity.py         (152 LOC — predict_linear forecasting; 80% covered, mypy strict)
    ├── deps.py             (66 LOC — agent /api/deps/scan client; 58% covered, mypy strict)
    ├── dns.py              (200 LOC — DNS health monitor; 59% covered, mypy strict)
    ├── drift.py            (158 LOC — config drift detector; 50% covered, mypy strict)
    └── ssl.py              (165 LOC — SSL/Domain watchdog; 54% covered, mypy strict)
```

**Still inline in bot.py (3 watchdogs + monitor + health check + brief):**
- Hygiene (~205 LOC) — uses `infra.ssh` (already extracted)
- Firewall (~280 LOC) — uses `infra.ssh` + `_config_get/set`
- Morning Brief (~125 LOC) — uses `infra.gh.gh_api` (extracted) + `infra.prom.prom_query` (extracted) + `_collect_*`
- Health check + auto-fix — tightly coupled with bot
- /monitor + /vps — tightly coupled with bot
- Voice + meeting + journal + skill + tanya commands — tightly coupled

**Key learnings (consolidated across 5 batches):**

1. **Multi-file orphan-ref walker scales** — `scripts/lint_orphan_refs.py` resolves handler/scheduler refs across 14 `.py` files in `telegram-bot/`, 130 functions.

2. **Aliased re-imports for high-fanout primitives** — `_ssh_exec` (26 callsites), `_prom_query` (18 callsites), `_agent_post` (16 callsites), `_gh_api` (3 callsites) preserved unchanged via `from infra.X import name as _name`.

3. **Deferred imports retired** — once a primitive moves to `infra/`, watchdog modules using it should switch from deferred to top-level import. Done for `watchdogs/deps.py` after `infra/agent.py` extracted. Cleaner module + simpler test setup.

4. **Stricter return types catch real bugs** — switching `dict | list | None` (raw generics) to `dict[str, Any] | list[Any] | None` made mypy lenient catch unguarded slice operations on union types in `_collect_github_summary`. Added `isinstance(x, list)` narrowing — code is now both more correct AND clearer.

5. **Ratchet-friendly mypy strict** — small extracted modules pass strict almost-by-default. Each new module adds 1-2 type fixes. 22 modules now strict (~95% of leaf modules).

6. **Test isolation patterns:**
   - `monkeypatch CONFIG_DIR/CONFIG_FILE` per-test for isolated config store
   - `monkeypatch dig_record / check_*_expiry / prom_query / agent_post / gh_api` for deterministic formatter tests
   - `importlib.reload(infra.X)` to re-parse env-dependent module-level state
   - Fake `httpx.AsyncClient` via monkeypatch for HTTP modules (no network)
   - `asyncio.run()` for async helpers (consistent with `tests/test_journal.py`)
   - `monkeypatch.setattr(module, "name", fake)` instead of `types.ModuleType` injection (preferred when target is a top-level import)

7. **CI vs local ruff version mismatch** — local pre-commit pinned to 0.8.4 doesn't flag every issue that newer CI ruff catches. Always run pre-push hook locally before pushing.

8. **Pure extraction = behavior unchanged** — 498 tests still pass without modification across 5 refactor batches. No behavioral regression in production deploys.

**Next watchdog candidates (medium-risk, diminishing returns):**

| Watchdog | Inline LOC | Dependencies | Effort | Risk |
|---|---|---|---|---|
| **Hygiene** | ~205 | `infra.ssh` (already extracted) | 1h | 🟡 Med |
| **Firewall** | ~280 | `infra.ssh` + `_config_get/set` (config helpers stay in bot.py) | 1-1.5h | 🟡 Med (biggest blast radius) |
| **Morning brief** | ~125 | `infra.gh` + `infra.prom` (both extracted) + `_collect_*` | 1h | 🟡 Med (multi-dep, has its own helpers) |

**My honest recommendation: STOP refactoring here.** Pivot to:
- **Test Coverage Agent (Tier 1.5)** — feature work, eat-own-dogfood, 6-9h effort
- **Wait for dogfood signal** — ~5-12 days remaining

After Hygiene+Firewall+Morning Brief: bot.py at ~2200 LOC, but remaining is `cmd_*` handlers + voice/meeting/journal/monitor/health-check, all tightly coupled. Extracting them = pure code movement, no design improvement.

---

## 🚀 FRESH SESSION ENTRYPOINT (read this if you're a new opencode session)

**Last session ended 2026-05-31 16:19 UTC. Continuing in a new opencode session.**

### Repo state right now

```
Branch: main, working tree clean
Last 5 commits:
  ad57edb    test+ci: cover infra/agent + infra/gh, expand mypy strict to 22 modules
  ce1e0e1    refactor(watchdogs): drop deferred import in deps watchdog
  b614c12    refactor(bot): extract agent_post + gh_api to infra/
  [handoff]  docs(TASK): handoff for sesi 2026-05-31 15:46 (refactor batch 3)
  fc04dba    fix(tests): remove unused pytest imports (CI ruff F401)

Production: 7 containers up + healthy (last verified run 26717796050)
Dogfood: ~42h elapsed of 1-2 week window (started 2026-05-30 23:00 UTC)
telegram-bot/: bot.py (2769) + infra/ (206 LOC) + watchdogs/ (741 LOC)
tests/: 498 passing, ~36% coverage
mypy strict: 22 modules whitelisted
```

### Verify state in <2 minutes

```bash
git status                                    # clean
git log --oneline -5                          # matches above
gh run list --workflow=deploy.yml --limit 3   # last 3 green
python3 -m pytest -q                          # 498 passed, ~36% coverage
python3 -m ruff check --select=F telegram-bot langgraph-agent tests
python3 -m mypy --config-file=mypy.ini telegram-bot langgraph-agent
python3 -m mypy --strict langgraph-agent/app/{config,docs_sync,embedding,gitlab_review,journal,llm,meeting_notes,pr_review,skills,telegram,tools}.py telegram-bot/infra/*.py telegram-bot/watchdogs/*.py
python3 -m compileall -q telegram-bot langgraph-agent
python3 scripts/lint_orphan_refs.py           # 14 files, 130 functions
pre-commit run --all-files                    # 4 hooks pass
pre-commit run --all-files --hook-stage pre-push  # +mypy lenient + strict
```

If anything fails: do not proceed. Diagnose first.

### Pick your work

**If user says "lanjutkan" / "continue" without specifics, ASK FIRST.**

**TIME TO DECIDE: refactor more, or pivot?**

| Path | Effort | Risk | Notes |
|---|---|---|---|
| **A1. Hygiene watchdog extraction** | 1h | 🟡 Med | Uses `infra.ssh`. Pattern proven. |
| **A2. Firewall watchdog extraction** | 1-1.5h | 🟡 Med | After A1. Biggest blast radius. |
| **A3. Morning Brief extraction** | 1h | 🟡 Med | Has own `_collect_*` helpers. Riskier. |
| **A4. Triple A1+A2+A3** | 3-4h | 🟡 Med | Drops bot.py to ~2200 LOC. Diminishing returns. |
| **B. Test Coverage Agent (Tier 1.5)** | 2-3h design + 4-6h impl | 🟡 Med | **RECOMMENDED PIVOT.** Feature work, eat-own-dogfood. |
| **D. Pytest expansion batch 5** | 3-4h+ | 🟡 Med | ROI menurun (mock-heavy). Defer. |
| **G. Wait for dogfood signal** | — | — | Phase 2 work blocked. ~5-12 days remaining. |

**Blocked on user input:**
- Spec-to-Implementation (needs PRD)
- Onboard 8-13 VPS to Prometheus (needs IP/SSH list)
- Activate DNS+SSL schedulers (needs `/ssl add yourdomain.com` via Telegram)

### Safety net you can rely on

- **8 CI lint gates** — actionlint, ruff F, mypy lenient, mypy strict (22 modules), orphan-refs (14 files), compileall, caddy, promtool, amtool
- **5 pre-commit hooks** + 2 pre-push hooks
- **498 pytest tests** (119 new this session)
- **Coverage floor 27%** — actual ~36%
- **All production images SHA-pinned**
- **README has Local Development section**

### What this session DID NOT do

- Did not extract Hygiene/Firewall/Morning Brief watchdogs (next batch — medium-risk)
- Did not write Test Coverage Agent (recommended pivot)
- Did not touch Phase 2 logic — wait dogfood signal
- Did not migrate to Python 3.14
- Did not add cmd_* docstrings (defer to refactor)

### Sesi recap (high-level)

Sesi 2026-05-31 16:19 = **bot.py refactor batch 4** (continued from batch 3 at 15:46).

1. **agent_post + gh_api extraction** (commit `b614c12`):
   - Created `infra/agent.py` (24 LOC) + `infra/gh.py` (29 LOC)
   - Aliased re-imports preserve 16 _agent_post + 3 _gh_api callsites unchanged
   - Type narrowing fix in `_collect_github_summary` (isinstance guards on dict|list union)
   - bot.py: 2796 → 2769 lines (-27)

2. **Deferred-import cleanup** (commit `ce1e0e1`):
   - `watchdogs/deps.py` switched from `from bot import _agent_post` to top-level `from infra.agent import agent_post`
   - Updated 6 tests: monkeypatch `deps.agent_post` instead of `types.ModuleType("bot")` injection
   - Cleaner module + simpler tests

3. **Tests + mypy strict expansion** (commit `ad57edb`):
   - 9 new tests: 4 for `infra/agent`, 5 for `infra/gh`
   - Mypy strict whitelist: 20 → 22 modules
   - Updated pre-commit + GitHub workflow

4. **Production deploy verified** (run `26717796050`):
   - lint + test + deploy 1m40s — all green
   - 7 schedulers registered cleanly
   - All 7 containers healthy

---

## 🤝 FOR NEXT SESSION (detailed handoff)

**Where we left off:** Sesi 2026-05-31 16:19 — 5 watchdogs + 6 infra modules extracted, 119 new unit tests this session, mypy strict 22 modules. Refactor at natural pause point. Recommended pivot: Test Coverage Agent.

### Files changed this session (3 commits)

**b614c12 — agent + gh refactor:**
- `+ telegram-bot/infra/agent.py` (24 LOC)
- `+ telegram-bot/infra/gh.py` (29 LOC)
- `~ telegram-bot/bot.py` (-27 net, +2 isinstance narrowings)

**ce1e0e1 — Deferred-import cleanup:**
- `~ telegram-bot/watchdogs/deps.py` (top-level import + dict[str, Any] type)
- `~ tests/test_deps_watchdog_bot.py` (monkeypatch.setattr instead of sys.modules injection)

**ad57edb — Tests + mypy strict:**
- `+ tests/test_infra_agent.py` (4 tests)
- `+ tests/test_infra_gh.py` (5 tests)
- `~ .pre-commit-config.yaml` (+2 modules)
- `~ .github/workflows/deploy.yml` (+2 modules)

### Active Tasks (for next session)

- [ ] **DOGFOOD WINDOW (active, ~42h elapsed)** — observe 7 features for 1-2 weeks total
- [ ] **ACTIVATE DNS + SSL schedulers** (5 menit) — user runs `/ssl add yourdomain.com`
- [ ] **Onboard remaining 8-13 VPS to Prometheus** — needs IP/SSH list
- [ ] **DECIDE: refactor batch 5 (medium-risk Hygiene/Firewall/Morning Brief) OR pivot to Test Coverage Agent** ← user needs to choose
- [ ] **DEFERRED: Phase 2 auto-PR/auto-remediation** — wait dogfood signal
- [ ] **DEFERRED: Grafana, py3.14**

### Recently Completed (chronological)

- ✅ [2026-05-31 16:19 UTC] **Refactor batch 4** — agent_post + gh_api extracted, deferred import cleaned, mypy strict 20→22
- ✅ [2026-05-31 15:46 UTC] **Refactor batch 3** — Deps+Capacity+Drift+prom extracted, mypy strict 11→20
- ✅ [2026-05-31 15:18 UTC] **Refactor batch 2** — SSL+SSH primitives extracted
- ✅ [2026-05-31 14:49 UTC] **DNS watchdog refactor pilot** — `infra/` + `watchdogs/dns.py` packages created
- ✅ [2026-05-31 13:45 UTC] **Mypy strict expansion 4 → 11**
- ✅ [2026-05-31 13:35 UTC] **SHA-pin prom images**
- ✅ [2026-05-31 13:05 UTC] **Caddy + promtool + amtool CI gates**
- ✅ [2026-05-31 12:50 UTC] **Pytest batch 4** — 129 new tests
- ✅ [2026-05-31 12:35 UTC] **README Local Development section**

### Lessons from this session

1. **Refactor curve plateau visible** — Batch 1 (DNS pilot, 180 LOC). Batch 2 (SSL+SSH, 215 LOC). Batch 3 (Deps+Capacity+Drift+prom, 398 LOC = 3 watchdogs in 1 commit). Batch 4 (agent+gh, 53 LOC). Each subsequent batch extracts smaller bounded primitives. The big watchdogs (Hygiene 205, Firewall 280, Morning Brief 125) are the last "atomic units" left — beyond that, only handler code remains, which is tightly coupled to bot orchestration.

2. **Type narrowing improvements during extraction** — moving `_gh_api` to `infra/gh.py` with explicit `dict[str, Any] | list[Any] | None` return type forced mypy to flag unguarded slicing in callers. Adding `isinstance(prs, list)` guards: code is now both type-safe AND clearer about API expectations (PR endpoint returns list, check-runs endpoint returns dict).

3. **Deferred-import retirement is a 2-step pattern:**
   - Step 1: Extract primitive to `infra/X.py` with aliased re-import in bot.py for back-compat (callsites unchanged).
   - Step 2: Update consumers (watchdogs/Y.py) to import directly from `infra/X.py` instead of `from bot import _alias`.
   The 2-step approach lets each step ship independently with zero behavior change. Tests get cleaner in step 2 (no more sys.modules injection).

4. **Time to stop refactoring** — at 21.4% reduction with 5 watchdogs + 6 infra modules, the remaining work yields diminishing returns. Hygiene, Firewall, Morning Brief are all medium-risk with multi-deps. After those, bot.py is 80% handler code which can't be cleanly extracted. Better use of time: feature work (Test Coverage Agent) or wait dogfood signal for Phase 2.

5. **monkeypatch.setattr > sys.modules injection** — when testing code that imports a name at top-level (`from infra.agent import agent_post`), use `monkeypatch.setattr(module, "agent_post", fake)`. The `types.ModuleType + sys.modules` injection trick is only needed for deferred imports inside functions. Cleaner test code, less ritual.

---


## 🏗️ Bot.py Refactor — Status

**Pattern proven across 5 watchdog extractions + 4 infra modules:**

```
telegram-bot/
├── bot.py                  (2796 lines — orchestrator + 3 watchdogs still inline + handlers)
├── Dockerfile              (COPY bot.py + watchdogs/ + infra/)
├── infra/
│   ├── __init__.py
│   ├── auth.py             (32 LOC — ALLOWED_USERS + @authorized; 62% covered, mypy strict)
│   ├── config_store.py     (33 LOC — CONFIG_DIR + config_get/set; 100% covered, mypy strict)
│   ├── prom.py             (22 LOC — prom_query; 100% covered, mypy strict)
│   └── ssh.py              (66 LOC — env-target parsing, get/add/del_ssh_target, ssh_exec; 67% covered, mypy strict)
└── watchdogs/
    ├── __init__.py
    ├── capacity.py         (152 LOC — predict_linear forecasting; 80% covered, mypy strict)
    ├── deps.py             (66 LOC — agent /api/deps/scan client; 58% covered, mypy strict)
    ├── dns.py              (200 LOC — DNS health monitor; 59% covered, mypy strict)
    ├── drift.py            (158 LOC — config drift detector; 50% covered, mypy strict)
    └── ssl.py              (165 LOC — SSL/Domain watchdog; 54% covered, mypy strict)
```

**Still inline in bot.py (3 watchdogs + monitor + health check + brief):**
- Hygiene (~205 LOC) — uses `infra.ssh` (already extracted)
- Firewall (~280 LOC) — uses `infra.ssh` + `_config_get/set`
- Morning Brief (~125 LOC) — uses `_gh_api`, `_prom_query` (extracted), `_collect_*`
- Health check + auto-fix — tightly coupled with bot
- /monitor + /vps — tightly coupled with bot
- Voice + meeting + journal + skill + tanya commands — tightly coupled

**Key learnings (consolidated across 4 batches):**

1. **Multi-file orphan-ref walker scales** — `scripts/lint_orphan_refs.py` resolves handler/scheduler refs across all `.py` files in `telegram-bot/`. Tested across 12 files, 130 functions.

2. **Aliased re-imports for high-fanout primitives** — `_ssh_exec` (26 callsites) and `_prom_query` (18 callsites) preserved unchanged via `from infra.X import name as _name`. Zero-callsite-edit refactor.

3. **Deferred imports for cross-module bot deps** — `watchdogs/deps.py` defers `_agent_post` (16 callsites in bot.py, defer extraction); `watchdogs/drift.py` defers `_ssh_docker_ps` (still tied to monitor cmd). Pattern: `from bot import X` inside the function. Also tested via `types.ModuleType("bot")` injection in unit tests.

4. **Ratchet-friendly mypy strict** — small extracted modules pass strict almost-by-default. Only minor fixes needed: `dict[str, Any]` instead of `dict`, `list[Any]` instead of `list`, explicit return type annotations on `json.loads()` results. 9 modules added to strict whitelist in 1 commit.

5. **Test isolation patterns:**
   - `monkeypatch CONFIG_DIR/CONFIG_FILE` per-test for isolated config store
   - `monkeypatch dig_record / check_*_expiry / prom_query` for deterministic formatter tests
   - `importlib.reload(infra.ssh)` to re-parse `MONITOR_SSH_TARGETS` env var
   - `types.ModuleType("bot") + sys.modules` injection for testing deferred-import code paths
   - Fake `httpx.AsyncClient` via monkeypatch for `prom_query` (no network)
   - `asyncio.run()` for async helpers (consistent with `tests/test_journal.py` pattern)

6. **CI vs local ruff version mismatch** — local ruff 0.8.4 (pre-commit-pinned) doesn't flag unused module-level `import pytest` but CI ruff (newer, installed via `pip install ruff` in deploy.yml) does. Drop unused pytest imports from test modules.

7. **Pure extraction = behavior unchanged** — 488 tests still pass without modification across 4 refactor batches. No behavioral regression in production deploys.

**Next watchdog candidates (medium-risk):**

| Watchdog | Inline LOC (approx) | Dependencies | Effort | Risk |
|---|---|---|---|---|
| **Hygiene** | ~205 | `infra.ssh` (already extracted) | 1h | 🟡 Med (heavy SSH usage) |
| **Firewall** | ~280 | `infra.ssh` + `_config_get/set` (config helpers stay in bot.py) | 1-1.5h | 🟡 Med (biggest blast radius) |
| **Morning brief** | ~125 | `_gh_api` + `_prom_query` (extracted) + `_collect_*` | 1h | 🟡 Med (multi-dep, has its own helpers) |

**My recommendation:** **Hygiene next** (uses already-extracted `infra.ssh`, no new deferred imports needed). Then Firewall (similar). Morning Brief last (has its own internal helpers like `_collect_pr_summary` that ALSO need extracting).

After all 3: bot.py drops to ~2200 LOC, ~37% from original. Diminishing returns kick in heavily after that since remaining code is `cmd_*` handlers + voice/meeting/journal/monitor/health-check, all tightly coupled.

---

## 🚀 FRESH SESSION ENTRYPOINT (read this if you're a new opencode session)

**Last session ended 2026-05-31 15:46 UTC. Continuing in a new opencode session.**

### Repo state right now

```
Branch: main, working tree clean
Last 5 commits:
  fc04dba    fix(tests): remove unused pytest imports (CI ruff F401)
  1e84673    ci+types: expand mypy strict whitelist 11 -> 20 modules
  19af3c9    test: unit tests for infra/prom + watchdogs/{deps,capacity,drift}
  4efa952    refactor(bot): extract Deps + Capacity + Drift watchdogs + infra/prom.py
  4b4f523    docs(TASK): handoff for sesi 2026-05-31 15:18 (refactor batch 2)

Production: 7 containers up + healthy (last verified run 26717013941)
Dogfood: ~41h elapsed of 1-2 week window (started 2026-05-30 23:00 UTC)
telegram-bot/: bot.py (2796) + infra/ (153 LOC) + watchdogs/ (741 LOC)
tests/: 488 passing, 35% coverage
mypy strict: 20 modules whitelisted
```

### Verify state in <2 minutes

```bash
git status                                    # clean
git log --oneline -5                          # matches above
gh run list --workflow=deploy.yml --limit 3   # last 3 green (modulo earlier failed run that was fixed)
python3 -m pytest -q                          # 488 passed, ~35% coverage
python3 -m ruff check --select=F telegram-bot langgraph-agent tests
python3 -m mypy --config-file=mypy.ini telegram-bot langgraph-agent
python3 -m mypy --strict langgraph-agent/app/{config,docs_sync,embedding,gitlab_review,journal,llm,meeting_notes,pr_review,skills,telegram,tools}.py telegram-bot/infra/*.py telegram-bot/watchdogs/*.py
python3 -m compileall -q telegram-bot langgraph-agent
python3 scripts/lint_orphan_refs.py           # 12 files, 130 functions
pre-commit run --all-files                    # 4 hooks pass
pre-commit run --all-files --hook-stage pre-push  # +mypy lenient + strict
```

If anything fails: do not proceed. Diagnose first.

### Pick your work

**If user says "lanjutkan" / "continue" without specifics, ASK FIRST.**

| Path | Effort | Risk | Notes |
|---|---|---|---|
| **A1. Hygiene watchdog extraction** | 1h | 🟡 Med | Uses `infra.ssh`. Heavy SSH-cmd usage but pattern proven. |
| **A2. Firewall watchdog extraction** | 1-1.5h | 🟡 Med | Biggest blast radius. After A1 for momentum. |
| **A3. Morning Brief extraction** | 1h | 🟡 Med | Multi-dep + own internal helpers. Riskier. |
| **A4. Triple A1+A2+A3 in 1 session** | 3-4h | 🟡 Med | Drops bot.py to ~2200 LOC. Big win but multi-deploy. |
| **B. Test Coverage Agent (Tier 1.5)** | 2-3h design + 4-6h impl | 🟡 Med | Good time now since refactor at natural pause. |
| **D. Pytest expansion batch 5** | 3-4h+ | 🟡 Med | ROI menurun (mock-heavy). Defer. |
| **G. Wait for dogfood signal** | — | — | Phase 2 work blocked. ~5-12 days remaining. |
| **H. STOP refactoring, work on Phase 2 prep** | varies | 🟢 | Refactor diminishing returns. Time to pivot? |

**Blocked on user input:**
- Spec-to-Implementation (needs PRD)
- Onboard 8-13 VPS to Prometheus (needs IP/SSH list)
- Activate DNS+SSL schedulers (needs `/ssl add yourdomain.com` via Telegram)

### How to extract the next watchdog (Hygiene example)

1. Find Hygiene block: `grep -n "^# --- Docker Image Hygiene\|^HYGIENE_CHECK\|^def cmd_hygiene\|^async def _run_hygiene_check\|^async def _hygiene_check_job" telegram-bot/bot.py`
2. Identify dependencies (likely `_ssh_exec`, `_get_ssh_targets` — both via `infra.ssh`).
3. Create `telegram-bot/watchdogs/hygiene.py` mirroring DNS/SSL/Capacity/Drift pattern:
   - Constants prefix: `HYGIENE_*`
   - Public exports: `cmd_hygiene`, `hygiene_check_job`, `HYGIENE_CHECK_ENABLED`, `HYGIENE_CHECK_HOUR`, `HYGIENE_CHECK_MINUTE`
   - Internal helpers: `run_hygiene_check`, any per-VPS helpers
   - Direct imports: `from infra.ssh import get_ssh_targets, ssh_exec`
4. Update `bot.py`:
   - Add `from watchdogs.hygiene import (...)` at top
   - Delete inline Hygiene block
   - Update scheduler registration in `post_init`
   - Update handler registration in `main()`
5. Run all CI gates locally before commit.
6. Add unit tests in `tests/test_hygiene_watchdog.py` (mock `ssh_exec` for deterministic output).
7. Add Hygiene to mypy-strict whitelist (`.pre-commit-config.yaml` + `.github/workflows/deploy.yml`).
8. Commit, push, verify CI green + scheduler registration in deploy log.

### Safety net you can rely on

- **8 CI lint gates** — actionlint, ruff F, mypy lenient (whole package), mypy strict (20-module whitelist), orphan-refs script (12 files), compileall, caddy validate, promtool, amtool
- **5 pre-commit hooks** + 2 pre-push hooks
- **488 pytest tests** — parser + module-unit + new infra/watchdogs unit tests (109 new this session)
- **Coverage floor 27%** — actual at 35%
- **Mypy strict whitelist** (20 modules: 11 agent + 9 bot infra/watchdogs)
- **All production images SHA-pinned**
- **README has Local Development section**
- **Multi-file orphan-ref walker** proven across 4 extraction batches

### What this session DID NOT do

- Did not extract Hygiene/Firewall/Morning Brief watchdogs (next batch — medium-risk)
- Did not extract `_agent_post` / `_agent_headers` to `infra/agent.py` (defer until needed)
- Did not extract `_gh_api` (Morning Brief's main dep)
- Did not write Test Coverage Agent
- Did not touch Phase 2 logic — wait dogfood signal
- Did not migrate to Python 3.14
- Did not add cmd_* docstrings (defer to refactor)

### Sesi recap (high-level)

Sesi 2026-05-31 15:46 = **bot.py refactor batch 3** (continued from batch 2 at 15:18).

1. **Deps + Capacity + Drift watchdogs extraction** (commit `4efa952`):
   - Created 4 new modules: `infra/prom.py`, `watchdogs/{deps,capacity,drift}.py` (398 LOC total)
   - Aliased re-import for `_prom_query` (18 callsites preserved)
   - Deferred imports for `_agent_post` (deps) and `_ssh_docker_ps` (drift)
   - bot.py: 3150 → 2796 lines (-354, -11.2% in single commit)

2. **Unit tests for new modules** (commit `19af3c9`):
   - 25 new tests across 4 files: prom, capacity, drift, deps_bot
   - Coverage 32% → 35% (+3pp)
   - 488 total tests passing

3. **Mypy strict expansion** (commit `1e84673`):
   - 11 → 20 modules in strict whitelist (added 9 from telegram-bot/{infra,watchdogs}/)
   - ~50% of relevant module count
   - Updated pre-commit + GitHub workflow

4. **Test fix** (commit `fc04dba`):
   - CI ruff version mismatch — dropped unused `import pytest` from 4 test modules
   - First commit failed CI lint, second push fixed it

5. **Production deploy verified** (run `26717013941`):
   - lint, test, deploy 1m34s — all green
   - 7 schedulers registered cleanly
   - All 7 containers healthy

---

## 🤝 FOR NEXT SESSION (detailed handoff)

**Where we left off:** Sesi 2026-05-31 15:46 — 5 watchdogs extracted (DNS, SSL, Deps, Capacity, Drift), 4 infra modules (auth, config_store, prom, ssh), 109 new unit tests this session, mypy strict 20 modules. Refactor pattern proven across 4 batches.

### Files changed this session (5 commits)

**4efa952 — Batch 3 refactor:**
- `+ telegram-bot/infra/prom.py` (22 LOC)
- `+ telegram-bot/watchdogs/deps.py` (66 LOC)
- `+ telegram-bot/watchdogs/capacity.py` (152 LOC)
- `+ telegram-bot/watchdogs/drift.py` (158 LOC)
- `~ telegram-bot/bot.py` (-354 net)
- `~ telegram-bot/{infra/config_store,watchdogs/dns,watchdogs/ssl}.py` (mypy strict prep)

**19af3c9 — Tests:**
- `+ tests/test_infra_prom.py` (4 tests)
- `+ tests/test_capacity_watchdog.py` (6 tests)
- `+ tests/test_drift_watchdog.py` (8 tests)
- `+ tests/test_deps_watchdog_bot.py` (6 tests, 1 mod for sync test)

**1e84673 — Mypy strict:**
- `~ .pre-commit-config.yaml` (+9 modules)
- `~ .github/workflows/deploy.yml` (+9 modules)

**fc04dba — Test fix:**
- `~ tests/test_{infra_prom,capacity_watchdog,drift_watchdog,deps_watchdog_bot}.py` (drop unused pytest import)

### Active Tasks (for next session)

- [ ] **DOGFOOD WINDOW (active, ~41h elapsed)** — observe 7 features for 1-2 weeks total
- [ ] **ACTIVATE DNS + SSL schedulers** (5 menit) — user runs `/ssl add yourdomain.com`
- [ ] **Onboard remaining 8-13 VPS to Prometheus** — needs IP/SSH list
- [ ] **CONTINUE BOT.PY REFACTOR BATCH 4 (medium-risk)** — Hygiene → Firewall → Morning Brief, ~3-4h total
- [ ] **OR PIVOT: Test Coverage Agent (Tier 1.5)** — refactor at natural pause, good time to switch focus
- [ ] **DEFERRED: Phase 2 auto-PR/auto-remediation** — wait dogfood signal
- [ ] **DEFERRED: Grafana, py3.14**

### Recently Completed (chronological)

- ✅ [2026-05-31 15:46 UTC] **Refactor batch 3** — Deps+Capacity+Drift+prom extracted, 25 new tests, mypy strict 11→20
- ✅ [2026-05-31 15:18 UTC] **Refactor batch 2** — SSL+SSH primitives extracted, 54 new tests
- ✅ [2026-05-31 14:49 UTC] **DNS watchdog refactor pilot** — `infra/` + `watchdogs/dns.py` packages created
- ✅ [2026-05-31 13:45 UTC] **Mypy strict expansion 4 → 11**
- ✅ [2026-05-31 13:35 UTC] **SHA-pin prom images**
- ✅ [2026-05-31 13:05 UTC] **Caddy + promtool + amtool CI gates**
- ✅ [2026-05-31 12:50 UTC] **Pytest batch 4** — 129 new tests
- ✅ [2026-05-31 12:35 UTC] **README Local Development section**

### Lessons from this session

1. **Refactor diminishing returns curve** — DNS pilot was 180 LOC extracted, batch 2 SSL was 165 LOC + SSH 50 LOC = 215, batch 3 Deps+Capacity+Drift+prom = 398 LOC. Each batch's bot.py reduction is bigger when extracting 3 modules at once (354 LOC in one commit). But the next 3 watchdogs (Hygiene, Firewall, Morning Brief) are ALL medium-risk and account for ~610 LOC. After that, remaining 2200 LOC is hard-coupled (handlers + monitor + health-check + voice/meeting/journal/skill/tanya commands).

2. **Mypy strict ratchet expands fast for clean modules** — 9 small modules added in 1 commit (~30 min total work). Each module needed only 1-2 type fixes (`dict` → `dict[str, Any]`, explicit return types). Don't pre-emptively type old code; do it during extraction when you're already touching the file.

3. **CI ruff > local pre-commit ruff** — local pre-commit pinned to 0.8.4 doesn't flag every issue that newer CI ruff catches. Lesson: also run `pip install ruff && ruff check` to match CI version before pushing. Or: pin CI ruff to match. (Alternative: bump pre-commit ruff version to match CI.)

4. **Aliased re-imports scale well** — 2nd time using this pattern (`_prom_query` after `_ssh_exec`). 18 callsites preserved with 1 line. Pattern: extract primitives to `infra/X.py`, alias-re-export from bot.py: `from infra.X import name as _name`. The "real" public API uses the new name.

5. **Test deferred imports with `types.ModuleType`** — to test code that does `from bot import _agent_post` inside a function, inject a fake `bot` module via `sys.modules`. Pattern:
   ```python
   fake_bot = types.ModuleType("bot")
   fake_bot._agent_post = fake_async_post
   monkeypatch.setitem(sys.modules, "bot", fake_bot)
   ```
   Allows unit-testing the deferred-import code path without actually loading bot.py.

---


## 🏗️ Bot.py Refactor — Status

**Pattern proven across 2 watchdog extractions + 3 infra modules:**

```
telegram-bot/
├── bot.py                  (3150 lines — orchestrator + 6 watchdogs still inline)
├── Dockerfile              (COPY bot.py + watchdogs/ + infra/)
├── infra/
│   ├── __init__.py
│   ├── auth.py             (32 LOC — ALLOWED_USERS + @authorized)
│   ├── config_store.py     (32 LOC — CONFIG_DIR + config_get/set, 100% covered)
│   └── ssh.py              (66 LOC — env-target parsing, get/add/del_ssh_target, ssh_exec, 67% covered)
└── watchdogs/
    ├── __init__.py
    ├── dns.py              (200 LOC — full DNS watchdog, 58% covered)
    └── ssl.py              (165 LOC — full SSL watchdog, 53% covered)
```

**Key learnings (consolidated across 3 batches):**

1. **Multi-file orphan-ref walker works perfectly** — `scripts/lint_orphan_refs.py` resolves handler/scheduler refs across all `.py` files in `telegram-bot/`. No script changes needed for the refactor across 2+ extracted modules.

2. **Cross-module imports flatten the dependency graph** — DNS pilot used deferred import for SSL seed; once SSL also extracted, the import becomes a normal top-level `from watchdogs.ssl import get_ssl_domains`. The deferred-import workaround is only needed when target is still inside bot.py.

3. **Underscore convention shift** — internal-only functions keep leading underscore inside a single module. When a function crosses module boundaries (cmd_dns, dns_check_job, get_dns_domains), drop the underscore — these are now the module's public API.

4. **Aliased re-import pattern preserves callsites** — for high-callsite primitives (e.g. `_ssh_exec` used 26 times), use `from infra.ssh import ssh_exec as _ssh_exec` in bot.py. This keeps every existing callsite working with zero edits while the underlying implementation moves to a new module.

5. **Dockerfile gotcha** — must explicitly COPY new directories. `COPY bot.py .` only copies the single file. Adding `infra/` and `watchdogs/` dirs requires separate COPY directives.

6. **Mypy lenient + `ignore_missing_imports=True` is forgiving** — don't preemptively add `# type: ignore` comments. Adding unused ignores fails strict mode in CI.

7. **Pure extraction = behavior unchanged** — 409 tests still pass without modification across all 3 commits. No new tests needed for moved code; new tests added for previously-untested helpers (config_store, dns/ssl formatters, ssh merge logic).

8. **Test patterns for the new modules:**
   - `monkeypatch CONFIG_DIR/CONFIG_FILE` per-test for isolated config store
   - `monkeypatch dig_record / check_*_expiry` for deterministic formatter tests
   - `importlib.reload(infra.ssh)` to re-parse `MONITOR_SSH_TARGETS` env var with new value
   - `asyncio.run()` for async helpers (consistent with `tests/test_journal.py` pattern)

**Next watchdog candidates (ordered by ROI):**

| Watchdog | Inline LOC (approx) | Dependencies | Effort | Risk |
|---|---|---|---|---|
| **Deps** | ~75 | `_agent_post` | 30 min | 🟢 Low |
| **Capacity** | ~145 | `_prom_query` | 45 min | 🟢 Low |
| **Drift** | ~145 | `infra.ssh` (already extracted) | 45 min | 🟢 Low |
| **Hygiene** | ~205 | `infra.ssh` | 1h | 🟡 Med |
| **Firewall** | ~280 | `infra.ssh` + `_config_get/set` | 1-1.5h | 🟡 Med |
| **Morning brief** | ~125 | `_gh_api`, `_prom_query`, `_collect_*` | 1h | 🟡 Med |

**Recommended next:** **Deps** (smallest, only 1 dependency) → **Capacity** (also small, 1 dep `_prom_query` → could extract to `infra/prom.py` first as shared dep for future) → **Drift** (deps fully extracted).

After Deps + Capacity + Drift: bot.py drops below 3000 LOC for the first time.

---

## 🚀 FRESH SESSION ENTRYPOINT (read this if you're a new opencode session)

**Last session ended 2026-05-31 15:18 UTC. Continuing in a new opencode session.**

### Repo state right now

```
Branch: main, working tree clean
Last 5 commits:
  c4ba770    test: unit tests for new infra/ + watchdogs/ packages
  7100d4c    refactor(bot): extract SSH helpers to infra/ssh.py
  ec1e561    refactor(bot): extract SSL watchdog to watchdogs/ssl.py
  1a207ed    docs(TASK): handoff for sesi 2026-05-31 14:49 (DNS refactor pilot)
  575e37f    refactor(bot): extract DNS watchdog to watchdogs/dns.py + infra/

Production: 7 containers up + healthy (last verified run 26716373477)
Dogfood: ~40h elapsed of 1-2 week window (started 2026-05-30 23:00 UTC)
telegram-bot/: bot.py (3150) + infra/ (130 LOC) + watchdogs/ (365 LOC)
tests/: 463 passing, 32% coverage
```

### Verify state in <2 minutes

```bash
git status                                    # clean
git log --oneline -5                          # matches above
gh run list --workflow=deploy.yml --limit 3   # last 3 green
python3 -m pytest -q                          # 463 passed, ~32% coverage
python3 -m ruff check --select=F telegram-bot langgraph-agent tests
python3 -m mypy --config-file=mypy.ini telegram-bot langgraph-agent
python3 -m mypy --strict langgraph-agent/app/{config,docs_sync,embedding,gitlab_review,journal,llm,meeting_notes,pr_review,skills,telegram,tools}.py
python3 -m compileall -q telegram-bot langgraph-agent
python3 scripts/lint_orphan_refs.py           # 8 files, 130 functions
pre-commit run --all-files                    # 4 hooks pass
pre-commit run --all-files --hook-stage pre-push  # +mypy lenient + strict
```

If anything fails: do not proceed. Diagnose first.

### Pick your work

**If user says "lanjutkan" / "continue" without specifics, ASK FIRST.**

| Path | Effort | Risk | Notes |
|---|---|---|---|
| **A1. Deps watchdog extraction** (smallest next) | 30 min | 🟢 Low | Only `_agent_post` dep. UNBLOCKED. |
| **A2. Capacity watchdog + extract `infra/prom.py`** | 1h | 🟢 Low | Sets up shared `_prom_query` for Morning brief later. |
| **A3. Drift watchdog (uses infra.ssh)** | 45 min | 🟢 Low | Demonstrates infra.ssh reuse from a fresh module. |
| **A4. Batch: Deps + Capacity + Drift** | 2-2.5h | 🟢 Low | 3 commits, 1 deploy. Drops bot.py below 3000 LOC. |
| **B. Test Coverage Agent (Tier 1.5)** | 2-3h design + 4-6h impl | 🟡 Med | Defer until refactor done. |
| **D. Pytest expansion batch 5** | 3-4h+ | 🟡 Med | ROI menurun (mock-heavy). Defer. |
| **I. Mypy strict expansion** | 1-2h | 🟢 Low | 11/22 modules done. Bigger modules need substantive type fixes. |
| **G. Wait for dogfood signal** | — | — | Phase 2 work blocked. ~5-12 days remaining. |

**Blocked on user input:**
- Spec-to-Implementation (needs PRD)
- Onboard 8-13 VPS to Prometheus (needs IP/SSH list)
- Activate DNS+SSL schedulers (needs `/ssl add yourdomain.com` via Telegram)

### How to extract the next watchdog (Deps example)

1. Read `telegram-bot/bot.py` — find Deps watchdog block (search for `cmd_deps`, `_run_deps_check`, `_deps_check_job`, `DEPS_CHECK_*`).
2. Identify dependencies (likely just `_agent_post` and stdlib).
3. Create `telegram-bot/watchdogs/deps.py` mirroring DNS/SSL pattern:
   - Constants prefix: `DEPS_CHECK_*`
   - Public exports: `cmd_deps`, `deps_check_job`, `DEPS_CHECK_ENABLED`
   - Internal helpers: `run_deps_check`
   - Import `_agent_post` from `bot` via deferred import OR extract `_agent_post` first to `infra/agent.py`.
4. Update `bot.py`:
   - Add `from watchdogs.deps import (...)` at top
   - Delete inline Deps block
   - Update scheduler registration in `post_init`
   - Update handler registration in `main()`
5. Run all CI gates locally before commit (see verify checklist above).
6. Add unit tests in `tests/test_deps_watchdog.py` (the agent codebase already has `tests/test_deps_watchdog.py` covering the agent-side; new tests should cover the bot-side handler + formatter).
7. Commit, push, verify CI green + scheduler registration in deploy log.

### Safety net you can rely on

- **8 CI lint gates** — actionlint, ruff F, mypy lenient (whole package), mypy strict (11-module whitelist), orphan-refs script (multi-file ready, verified working across 8 files), compileall, caddy validate, promtool, amtool
- **5 pre-commit hooks** + 2 pre-push hooks
- **463 pytest tests** — parser + module-unit + new infra/watchdogs unit tests
- **Coverage floor 27%** — actual at 32%
- **Mypy strict whitelist** (50% of agent modules)
- **All production images SHA-pinned**
- **README has Local Development section**
- **Multi-file orphan-ref walker** proven across 2 extraction batches

### What this session DID NOT do

- Did not extract Capacity/Drift/Hygiene/Firewall/Deps/MorningBrief watchdogs (next batch)
- Did not extract `_prom_query` to `infra/prom.py` (defer until 2nd Prometheus consumer)
- Did not extract `_agent_post` / `_agent_headers` to `infra/agent.py` (defer until needed)
- Did not write Test Coverage Agent
- Did not touch Phase 2 logic — wait dogfood signal
- Did not migrate to Python 3.14
- Did not add cmd_* docstrings (defer to refactor)

### Sesi recap (high-level)

Sesi 2026-05-31 15:18 = **bot.py refactor batch 2** (continued from path A pilot at 14:49).

1. **SSL watchdog extraction** (commit `ec1e561`):
   - Created `telegram-bot/watchdogs/ssl.py` (165 LOC)
   - Moved `cmd_ssl` + SSL logic block from bot.py
   - Cleaned up DNS pilot's deferred import workaround (now top-level)
   - bot.py: 3350 → 3200 lines

2. **SSH primitives extraction** (commit `7100d4c`):
   - Created `telegram-bot/infra/ssh.py` (66 LOC)
   - Aliased re-imports preserve all 26 callsites unchanged
   - Unblocks Firewall, Hygiene, Drift extraction
   - bot.py: 3200 → 3150 lines

3. **Unit tests for new modules** (commit `c4ba770`):
   - 54 new tests across 4 files: config_store, dns, ssl, ssh
   - Coverage 28.45% → 32% (+3.5pp)
   - 463 total tests passing

4. **Production deploy verified** (run `26716373477`):
   - lint 56s, test 35s, deploy 1m35s — all green
   - 7 schedulers registered cleanly
   - All 7 containers healthy

---

## 🤝 FOR NEXT SESSION (detailed handoff)

**Where we left off:** Sesi 2026-05-31 15:18 — DNS+SSL watchdogs extracted, infra/ssh.py shared, 54 new unit tests. Refactor pattern proven across 2 watchdogs + 3 infra modules. Path A unblocked for next watchdog.

### Files changed this session (3 commits)

**ec1e561 — SSL extraction:**
- `+ telegram-bot/watchdogs/ssl.py` (165 LOC)
- `~ telegram-bot/watchdogs/dns.py` (-13 LOC, simplified seed import)
- `~ telegram-bot/bot.py` (-150 LOC net)

**7100d4c — SSH primitives:**
- `+ telegram-bot/infra/ssh.py` (66 LOC)
- `~ telegram-bot/bot.py` (-50 LOC net)

**c4ba770 — Unit tests:**
- `+ tests/test_config_store.py` (7 tests)
- `+ tests/test_dns_watchdog.py` (24 tests)
- `+ tests/test_ssl_watchdog.py` (12 tests)
- `+ tests/test_infra_ssh.py` (11 tests)

### Active Tasks (for next session)

- [ ] **DOGFOOD WINDOW (active, ~40h elapsed)** — observe 7 features for 1-2 weeks total
- [ ] **ACTIVATE DNS + SSL schedulers** (5 menit) — user runs `/ssl add yourdomain.com`
- [ ] **Onboard remaining 8-13 VPS to Prometheus** — needs IP/SSH list
- [ ] **CONTINUE BOT.PY REFACTOR BATCH 3** — see "Bot.py Refactor — Status" section. Recommended: Deps → Capacity → Drift triple in 1 session (~2-2.5h).
- [ ] **DEFERRED: Phase 2 auto-PR/auto-remediation** — wait dogfood signal
- [ ] **DEFERRED: Grafana, py3.14**

### Recently Completed (chronological)

- ✅ [2026-05-31 15:18 UTC] **Refactor batch 2** — SSL watchdog + SSH primitives extracted, 54 new unit tests, coverage 28.45→32%
- ✅ [2026-05-31 14:49 UTC] **DNS watchdog refactor pilot** — `infra/` + `watchdogs/dns.py` packages created
- ✅ [2026-05-31 13:51 UTC] **boto3 version alignment** — patch-level consistency fix
- ✅ [2026-05-31 13:45 UTC] **Mypy strict expansion 4 → 11** — 7 new modules in whitelist
- ✅ [2026-05-31 13:35 UTC] **SHA-pin prom images**
- ✅ [2026-05-31 13:05 UTC] **Caddy + promtool + amtool CI gates**
- ✅ [2026-05-31 13:00 UTC] **Mypy strict +tools.py**
- ✅ [2026-05-31 12:50 UTC] **Pytest batch 4** — 129 new tests, floor 23→27
- ✅ [2026-05-31 12:35 UTC] **README Local Development section**

### Lessons from this session

1. **Aliased re-imports save callsite churn** — for high-fanout primitives like `_ssh_exec` (26 callsites in bot.py), the simplest pattern is `from infra.ssh import ssh_exec as _ssh_exec`. Zero-callsite-edit refactor. The "real" public API uses the new name; bot.py's legacy underscore name is just a backwards-compat alias until later cleanup.

2. **Once a primitive moves to a shared module, the next consumer is free** — DNS used deferred-import-from-bot to get SSL seed. After SSL itself moved to `watchdogs/ssl.py`, DNS's import became a normal top-level `from watchdogs.ssl import get_ssl_domains`. Each extraction unblocks future ones.

3. **Test the formatter, mock the I/O** — `run_dns_check` and `run_ssl_check` mix subprocess/socket I/O with formatting logic. Tests monkeypatch the I/O helper (`dig_record`, `check_ssl_expiry`) and verify the formatter handles all branches deterministically. 36 formatter tests added without any network calls.

4. **`importlib.reload` for env-dependent module state** — `infra/ssh.py` parses `MONITOR_SSH_TARGETS` at import time. To test multiple env values without polluting other tests, reload the module after `monkeypatch.setenv`. Pattern: `_reload_ssh(monkeypatch, raw_env)`.

5. **Coverage compounds with extraction** — `infra/config_store.py` reached 100% with 7 tests. Small modules are trivially testable; the same code stuck in a 3500-line bot.py would have been mock-heavy. Refactor + tests are mutually reinforcing.

---


## 📦 SESSION HANDOFF (2026-05-31 14:49 UTC) — for fresh opencode session

**Last activity:** Sesi 2026-05-31 closed at 14:49 UTC after run `26715696888` deployed successfully.

**Latest commits (last 5):**
```
575e37f refactor(bot): extract DNS watchdog to watchdogs/dns.py + infra/
317ec2e docs(TASK): add session handoff banner for fresh opencode session
0a7da22 docs(TASK): handoff for sesi 2026-05-31 13:51
3eb5750 chore: align boto3 version between agent and bot (1.43.14 → 1.43.15)
0dd6c99 ci+types: expand mypy strict whitelist 4 → 11 modules
```

**Latest deploy verified:**
- Run `26715696888` — lint 56s, deploy 1m38s
- All 7 schedulers registered: health 300s, morning brief 07:00, drift 02:00, capacity 02:10, deps 03:00, hygiene 02:15, firewall 03:30 WIB
- DNS scheduler stays idle (SSL list still empty) — expected
- All 7 containers healthy (verified via post-deploy probes)

**State to verify in new session (paste these):**
```bash
git status                                    # expect: clean, on main
git log --oneline -5                          # expect: matches above
gh run list --workflow=deploy.yml --limit 2   # expect: last 2 'ok'
python3 -m pytest -q                          # expect: 409 passed, ~28% cov
python3 scripts/lint_orphan_refs.py           # expect: 6 files, 131 functions clean
```

**What's safe to start without asking:**
- **Recommended path:** Continue bot.py refactor — extract next watchdog (Firewall, ~280 lines OR SSL, ~115 lines)
- See `## 🚀 FRESH SESSION ENTRYPOINT` → "Pick your work" table for alternatives

**What's blocked on user:**
- Spec-to-Implementation (PRD)
- Onboard 8-13 VPS (IP/SSH list)
- Activate DNS+SSL (`/ssl add yourdomain.com` via Telegram)

**Cumulative metrics from sesi 2026-05-31 (~6h15m, 20 commits):**
- Tests: 71 → 409 (+338, 5.8x)
- Coverage: 12.75% → 28.45% (+15.7pp)
- Coverage floor: 12% → 27%
- CI lint gates: 4 → 8
- Pre-commit hooks: 0 → 6
- Mypy strict modules: 0 → 11 (50% of agent codebase)
- SHA-pinned images: 1 → 5 (all production)
- **bot.py LOC: 3524 → 3350 (-174 net, DNS extracted)**
- **New packages: telegram-bot/{infra,watchdogs}/**

**Production state at handoff:** 7 containers up + healthy (verified via run 26715696888). Dogfood window ~40h elapsed of 1-2 week target.

---

## 🏗️ Bot.py Refactor — Status

**Pattern proven (DNS pilot):**

```
telegram-bot/
├── bot.py                  (3350 lines — orchestrator + remaining 7 watchdogs inline)
├── Dockerfile              (COPY bot.py + watchdogs/ + infra/)
├── infra/
│   ├── __init__.py
│   ├── auth.py             (ALLOWED_USERS + @authorized decorator)
│   └── config_store.py     (CONFIG_DIR + config_get/set)
└── watchdogs/
    ├── __init__.py
    └── dns.py              (180 lines — DNS health monitor)
```

**Key learnings from DNS pilot:**

1. **Multi-file orphan-ref walker works perfectly** — `scripts/lint_orphan_refs.py` resolves handler/scheduler refs across all `.py` files in `telegram-bot/`, no changes needed for the refactor.

2. **Circular import resolution pattern** — when extracted module needs a function still in bot.py (e.g. `_get_ssl_domains` for DNS seed), use deferred import inside a wrapper function. Not at module load.

3. **Import style** — top of bot.py:
   ```python
   from watchdogs.dns import (
       DNS_CHECK_ENABLED,
       DNS_CHECK_INTERVAL_SEC,
       cmd_dns,
       dns_check_job,
       get_dns_domains,
   )
   ```
   Public names in extracted modules drop leading underscores (cross-module = public API).

4. **Dockerfile update required** — must `COPY watchdogs ./watchdogs` and `COPY infra ./infra` alongside `COPY bot.py .`.

5. **Mypy strict trap** — `json.loads()` returns `Any`, but lenient mypy with `ignore_missing_imports=True` doesn't need the `cast`/`type: ignore`. Don't add comments unless mypy actually complains.

6. **Pure extraction = behavior unchanged** — 409 tests still pass without modification. No new tests needed for moved code (parser tests in `tests/test_bot_parsers.py` still target `bot._parse_*` functions which stayed in bot.py).

**Next watchdog candidates (ordered by ROI):**

| Watchdog | Inline LOC | Dependencies | Effort | Risk |
|---|---|---|---|---|
| **SSL** | ~115 (1198-1313) | `_config_get/set`, ssl stdlib | 30-45 min | 🟢 Low |
| **Firewall** | ~280 (1925-2148) | `_ssh_exec`, `_get_ssh_targets`, `_config_get/set` | 1-1.5h | 🟡 Med |
| **Hygiene** | ~205 (1746-1923) | `_ssh_exec`, `_get_ssh_targets` | 1h | 🟡 Med |
| **Capacity** | ~145 (1497-1632) | `_prom_query` | 45 min | 🟢 Low |
| **Drift** | ~145 (2152-2293) | `_ssh_exec`, `_get_ssh_targets` | 45 min | 🟡 Med |
| **Deps** | ~75 (1635-1685) | `_agent_post` | 30 min | 🟢 Low |
| **Morning brief** | ~125 (2296-2455) | `_gh_api`, `_prom_query`, `_collect_*` | 1h | 🟡 Med |

**Recommended next:** **SSL** — smallest, most self-contained. Only depends on `_config_get/set` (already in `infra.config_store`).

**Then Firewall + Hygiene** — share `_ssh_exec` and `_get_ssh_targets`. Extract these to `infra/ssh.py` first as shared dep.

---

## 🚀 FRESH SESSION ENTRYPOINT (read this if you're a new opencode session)

**Last session ended 2026-05-31 14:49 UTC. Continuing in a new opencode session.**

### Repo state right now

```
Branch: main, working tree clean
Last 5 commits:
  575e37f    refactor(bot): extract DNS watchdog to watchdogs/dns.py + infra/
  317ec2e    docs(TASK): add session handoff banner for fresh opencode session
  0a7da22    docs(TASK): handoff for sesi 2026-05-31 13:51
  3eb5750    chore: align boto3 version between agent and bot (1.43.14→1.43.15)
  0dd6c99    ci+types: expand mypy strict whitelist 4→11 modules

Production: 7 containers up + healthy (last verified run 26715696888)
Dogfood: ~40h elapsed of 1-2 week window (started 2026-05-30 23:00 UTC)
telegram-bot/: bot.py (3350) + infra/ (64 LOC) + watchdogs/ (200 LOC)
```

### Verify state in <2 minutes

```bash
git status                                    # clean
git log --oneline -5                          # matches above
gh run list --workflow=deploy.yml --limit 3   # last 3 green
python3 -m pytest -q                          # 409 passed, ~28% coverage
python3 -m ruff check --select=F telegram-bot langgraph-agent tests
python3 -m mypy --config-file=mypy.ini telegram-bot langgraph-agent
python3 -m mypy --strict langgraph-agent/app/{config,docs_sync,embedding,gitlab_review,journal,llm,meeting_notes,pr_review,skills,telegram,tools}.py
python3 -m compileall -q telegram-bot langgraph-agent
python3 scripts/lint_orphan_refs.py           # 6 files, 131 functions
pre-commit run --all-files                    # 4 hooks pass
pre-commit run --all-files --hook-stage pre-push  # +mypy lenient + strict
```

If anything fails: do not proceed. Diagnose first.

### Pick your work

**If user says "lanjutkan" / "continue" without specifics, ASK FIRST.**

| Path | Effort | Risk | Notes |
|---|---|---|---|
| **A1. SSL watchdog extraction** (next refactor step) | 30-45 min | 🟢 Low | Small, self-contained, only needs `infra.config_store`. UNBLOCKED. |
| **A2. Extract `infra/ssh.py` then Firewall+Hygiene watchdogs** | 1.5-2h | 🟡 Med | Shared `_ssh_exec` + `_get_ssh_targets`. 2 watchdogs in 1 deploy. |
| **A3. Continue 1 watchdog at a time** (SSL → Capacity → Deps → Drift → Morning Brief → Firewall → Hygiene) | 30min-1h each | 🟢-🟡 | Smallest blast radius per deploy. Total ~4-5h to complete. |
| **B. Test Coverage Agent (Tier 1.5)** | 2-3h design + 4-6h impl | 🟡 Med | Foundation: coverage.xml, baseline 28.45%. Defer until refactor done. |
| **D. Pytest expansion batch 5** | 3-4h+ | 🟡 Med | ROI menurun (mock-heavy). Defer. |
| **I. Mypy strict expansion** | 1-2h | 🟢 Low | 11/22 modules done. Bigger modules need substantive type fixes. |
| **G. Wait for dogfood signal** | — | — | Phase 2 work blocked. ~5-12 days remaining. |

**Blocked on user input:**
- Spec-to-Implementation (needs PRD)
- Onboard 8-13 VPS to Prometheus (needs IP/SSH list)
- Activate DNS+SSL schedulers (needs `/ssl add yourdomain.com` via Telegram)

### How to extract the next watchdog (SSL example)

1. Read `telegram-bot/bot.py` lines 1198-1313 (SSL block).
2. Identify dependencies: `_config_get`, `_config_set` (already in `infra.config_store`).
3. Create `telegram-bot/watchdogs/ssl.py` mirroring the DNS pattern:
   - Constants prefix: `SSL_CHECK_*`, `SSL_WARN_DAYS`, `_SSL_ENV_DOMAINS`
   - Public exports: `get_ssl_domains`, `cmd_ssl`, `ssl_check_job`, `SSL_CHECK_ENABLED`
   - Internal helpers: `add_ssl_domain`, `del_ssl_domain`, `check_ssl_expiry`, `run_ssl_check`
4. Update `bot.py`:
   - Add `from watchdogs.ssl import (...)` at top
   - Delete inline SSL block (lines 1198-1313)
   - Update scheduler registration in `post_init` to use new symbol names
   - Update handler registration in `main()` (cmd_ssl → already imported)
5. **DNS watchdog still uses `_get_ssl_domains` via deferred import** — update `watchdogs/dns.py:_get_ssl_seed()` to import from `watchdogs.ssl` instead of `bot`.
6. Run all CI gates locally before commit (see verify checklist above).
7. Commit, push, verify CI green + scheduler registration in deploy log.

### Safety net you can rely on

- **8 CI lint gates** — actionlint, ruff F, mypy lenient (whole package), mypy strict (11-module whitelist), orphan-refs script (multi-file ready, verified working), compileall, caddy validate, promtool, amtool
- **5 pre-commit hooks** + 2 pre-push hooks
- **409 pytest tests** — parser + module-unit regressions caught
- **Coverage floor 27%** — actual at 28.45%
- **Mypy strict whitelist** (50% of agent modules)
- **All production images SHA-pinned**
- **README has Local Development section**
- **Multi-file orphan-ref walker proven** — DNS extraction verified 6 files, 131 functions clean

### What this session DID NOT do

- Did not extract SSL/Firewall/Hygiene/Capacity/Drift/Deps/MorningBrief watchdogs (next batch's work)
- Did not extract `_ssh_exec` / `_get_ssh_targets` to `infra/ssh.py` yet (deferred until 2nd SSH-using watchdog)
- Did not extract `_agent_headers` / `_agent_post` to `infra/agent.py` (used in many places, defer)
- Did not consolidate `bot._config_get/_set` calls to use `infra.config_store.config_get/set` (intentional minimum-touch in pilot)
- Did not write Test Coverage Agent
- Did not touch Phase 2 logic — wait dogfood signal
- Did not migrate to Python 3.14
- Did not add cmd_* docstrings (defer to refactor)

### Sesi recap (high-level)

Sesi 2026-05-31 14:49 (continuation of 13:51) = **bot.py refactor pilot** (path A from previous handoff).

1. **DNS watchdog extraction** (commit `575e37f`):
   - Created `telegram-bot/{infra,watchdogs}/` packages (4 new files, 264 LOC)
   - Moved 180-line DNS block from `bot.py` to `watchdogs/dns.py`
   - Extracted shared infra: `infra/auth.py` (ALLOWED_USERS + @authorized) + `infra/config_store.py` (CONFIG_DIR + config_get/set)
   - Resolved circular import via deferred `_get_ssl_domains()` lookup
   - Updated `Dockerfile` to COPY new dirs
   - Public renames in extracted module drop leading underscores
   - All 8 CI lint gates + 409 tests + pre-commit hooks pass
   - Production deploy verified via run `26715696888` — 7 schedulers registered cleanly, all containers healthy

---

## 🤝 FOR NEXT SESSION (detailed handoff)

**Where we left off:** Sesi 2026-05-31 14:49 — DNS watchdog extracted, refactor pattern proven. Path A unblocked for next watchdog (SSL recommended next).

### Files changed this session (1 commit)

**New files:**
- `telegram-bot/infra/__init__.py` (empty)
- `telegram-bot/infra/auth.py` (32 LOC) — `ALLOWED_USERS` + `@authorized` decorator
- `telegram-bot/infra/config_store.py` (32 LOC) — `CONFIG_DIR`, `CONFIG_FILE`, `config_get`, `config_set`
- `telegram-bot/watchdogs/__init__.py` (empty)
- `telegram-bot/watchdogs/dns.py` (200 LOC) — full DNS watchdog (constants, helpers, run_dns_check, dns_check_job, cmd_dns)

**Modified files:**
- `telegram-bot/bot.py` — net -174 lines (DNS block removed, replaced with import)
- `telegram-bot/Dockerfile` — COPY watchdogs/ and infra/

**No tests, README, or other files changed.**

### Active Tasks (for next session)

- [ ] **DOGFOOD WINDOW (active, ~40h elapsed)** — observe 7 features for 1-2 weeks total
- [ ] **ACTIVATE DNS + SSL schedulers** (5 menit) — user runs `/ssl add yourdomain.com`
- [ ] **Onboard remaining 8-13 VPS to Prometheus** — needs IP/SSH list
- [ ] **CONTINUE BOT.PY REFACTOR** — see "Bot.py Refactor — Status" section above for next watchdog
- [ ] **DEFERRED: Phase 2 auto-PR/auto-remediation** — wait dogfood signal
- [ ] **DEFERRED: Grafana, py3.14**

### Recently Completed (chronological)

- ✅ [2026-05-31 14:49 UTC] **DNS watchdog refactor pilot** — `infra/` + `watchdogs/dns.py` packages created, 180 lines extracted from bot.py, multi-file orphan-ref walker verified working, deploy run 26715696888 green
- ✅ [2026-05-31 13:51 UTC] **boto3 version alignment** — patch-level consistency fix
- ✅ [2026-05-31 13:45 UTC] **Mypy strict expansion 4 → 11** — 7 new modules in whitelist, 2 tiny fixes
- ✅ [2026-05-31 13:35 UTC] **SHA-pin prom images** — manifest-list digests in 3 places
- ✅ [2026-05-31 13:05 UTC] **Caddy + promtool + amtool CI gates** — 3 new validation steps
- ✅ [2026-05-31 13:00 UTC] **Mypy strict +tools.py** — 4th module
- ✅ [2026-05-31 12:50 UTC] **Pytest batch 4** — 129 new tests, floor 23→27
- ✅ [2026-05-31 12:35 UTC] **README Local Development section** — 83 lines

### Lessons from this session

1. **Pure extraction is the safest refactor** — DNS code moved verbatim (renames + import changes only). 409 tests still pass without modification. No behavior risk.

2. **Circular imports between `bot.py` ↔ `watchdogs/X.py`** — solve with deferred (function-scope) imports. The orphan-ref walker doesn't trace runtime imports, so it doesn't complain. Module load stays clean.

3. **Underscore convention shift** — internal-only functions keep leading underscore inside a single module. When a function crosses module boundaries (cmd_dns, dns_check_job, get_dns_domains), drop the underscore — these are now the module's public API.

4. **Minimum-touch pilots reduce blast radius** — kept bot.py's inline `_config_get/_set` callsites untouched (only extracted DNS callsites moved to use `infra.config_store`). Future cleanup PR can consolidate. Tests + lint stay green throughout.

5. **Dockerfile gotcha** — must explicitly COPY new directories. `COPY bot.py .` only copies the single file. Adding `infra/` and `watchdogs/` dirs requires separate COPY directives.

6. **Mypy lenient + `ignore_missing_imports=True` is forgiving** — don't preemptively add `# type: ignore` comments; mypy will tell you if it's unhappy. Adding unused ignores fails strict mode in CI.

---


## 🚀 FRESH SESSION ENTRYPOINT (read this if you're a new opencode session)

**Last session ended 2026-05-31 13:51 UTC. Continuing in a new opencode session.**

### Repo state right now

```
Branch: main, working tree clean
Last 15 commits (sesi 2026-05-31 09:00 + 12:00 + 12:35 + 13:05 + 13:51):
  <pending>  chore: align boto3 version between agent and bot (1.43.14→1.43.15)
  <pending>  ci+types: expand mypy strict whitelist 4→11 modules
  <pending>  ci: SHA-pin prom/prometheus and prom/alertmanager images
  cf925a9    docs(TASK): handoff for sesi 2026-05-31 13:05
  bae911a    ci+types: expand mypy strict whitelist with tools.py + add config validation gates
  a0658dd    test(pytest+ci): batch 4 — tools/code_repos, floor 23→27
  5e1ef1b    docs(TASK): handoff for sesi 2026-05-31 12:35
  940e654    docs(README): add Local Development section
  ad557be    ci+types: add mypy strict gate for journal/telegram/embedding
  3d612b1    test(pytest+ci): batch 3 — meeting_notes/deps_watchdog, floor 19→23
  a845c9a    docs(TASK): handoff for sesi 2026-05-31 12:00
  3cfeeff    test(pytest+ci): batch 2 — pr_review/gitlab_review/docs_sync, floor 14→19
  376bab7    ci+refactor: extract orphan-ref AST checks to scripts/lint_orphan_refs.py
  3bfd56a    docs(TASK): handoff for sesi 2026-05-31 09:00 (Bundle 1+2)
  8e7ae93    test(pytest+ci): add 46 tests for skills/journal/telegram + bump floor 12→14

Production: 7 containers up + healthy (last verified run 26713505954, ~30min ago)
Dogfood: ~39h elapsed of 1-2 week window (started 2026-05-30 23:00 UTC)
```

### Verify state in <2 minutes

```bash
git status                                    # clean
git log --oneline -15                         # matches above
gh run list --workflow=deploy.yml --limit 3   # last 3 green
python3 -m pytest -q                          # 409 passed, ~28% coverage
python3 -m ruff check --select=F telegram-bot langgraph-agent tests
python3 -m mypy --config-file=mypy.ini telegram-bot langgraph-agent
python3 -m mypy --strict langgraph-agent/app/{config,docs_sync,embedding,gitlab_review,journal,llm,meeting_notes,pr_review,skills,telegram,tools}.py
python3 -m compileall -q telegram-bot langgraph-agent
python3 scripts/lint_orphan_refs.py
pre-commit run --all-files                    # all 4 hooks pass
pre-commit run --all-files --hook-stage pre-push  # +mypy lenient + strict
```

If anything fails: do not proceed. Diagnose first.

### Pick your work

**If user says "lanjutkan" / "continue" without specifics, ASK FIRST.** Diminishing returns warning: low-hanging fruit (pure-logic modules) mostly covered. Remaining work is mock-heavy or decision-heavy.

| Path | Effort | Risk | Notes |
|---|---|---|---|
| **A. Bot.py refactor pilot** (DNS watchdog) | 4-6h | 🟡 Med | UNBLOCKED. Single-focus session. Smallest blast radius. |
| **B. Test Coverage Agent (Tier 1.5)** | 2-3h design + 4-6h impl | 🟡 Med | Foundation: coverage.xml, baseline 28.45%. |
| **D. Pytest expansion batch 5** (qdrant_helper 24%, code_repos 58%→80%, sync 0%, vps_status 0%, etc) | 3-4h+ | 🟡 Med | ROI menurun (mock-heavy). |
| **I. Mypy strict expansion** (deps_watchdog, code_repos, qdrant_helper, sync, etc) | 1-2h | 🟢 Low | 11/22 modules done. Try remaining bigger modules. |
| **K. Pin docker images for langgraph-agent + telegram-bot Dockerfiles** | 30 menit | 🟢 Low | python:3.11-slim already SHA-pinned. Already complete. |
| **L. Add `.dockerignore` files** | 30 menit | 🟢 Low | Marginal — Dockerfiles use explicit COPY. |
| **H. Add cmd_* docstrings** | 2-3h | 🟢 Low | 29/29 cmd_* di bot.py tanpa docstring. Defer ke saat refactor (path A). |
| **G. Wait for dogfood signal** | — | — | Phase 2 work blocked. ~5-12 days remaining. |

**Blocked on user input:**
- Spec-to-Implementation (needs PRD)
- Onboard 8-13 VPS to Prometheus (needs IP/SSH list)
- Activate DNS+SSL schedulers (needs `/ssl add yourdomain.com` via Telegram)

### Bot.py refactor — UNBLOCKED 🎉

The orphan-ref walker has been extracted to `scripts/lint_orphan_refs.py` and supports multi-file packages. CI gate calls the script.

**Pattern for refactor:**
```
telegram-bot/
├── __init__.py          (new)
├── bot.py               (orchestrator + handler registration only)
├── watchdogs/
│   ├── __init__.py
│   ├── ssl.py
│   ├── dns.py           ← START HERE
│   ├── drift.py
│   ├── capacity.py
│   ├── hygiene.py
│   ├── firewall.py
│   ├── deps.py
│   └── morning_brief.py
├── infra/
│   ├── ssh.py
│   ├── prometheus.py
│   └── config_store.py
└── handlers/            (optional, extract cmd_* if useful)
```

Start with **DNS watchdog** — smallest blast radius. ~200 lines.

### Safety net you can rely on

- **8 CI lint gates** — actionlint, ruff F, mypy lenient (whole package), mypy strict (11-module whitelist), orphan-refs script, compileall, caddy validate, promtool, amtool
- **5 pre-commit hooks** + 2 pre-push hooks
- **409 pytest tests** — parser + module-unit regressions caught
- **Coverage floor 27%** — actual at 28.45%
- **Mypy strict whitelist** (50% of agent modules) — `config`, `docs_sync`, `embedding`, `gitlab_review`, `journal`, `llm`, `meeting_notes`, `pr_review`, `skills`, `telegram`, `tools`
- **All production images SHA-pinned** — caddy, prom/prometheus, prom/alertmanager, python:3.11-slim
- **Config validation in CI** — Caddyfile (caddy validate), Prometheus + alert rules (promtool), Alertmanager (amtool)
- **README has Local Development section**

### What this session DID NOT do

- Did not refactor bot.py (still unblocked, ready for path A)
- Did not write Test Coverage Agent
- Did not touch Phase 2 logic — wait dogfood signal
- Did not migrate to Python 3.14
- Did not add cmd_* docstrings
- Did not pursue mypy strict on deps_watchdog/code_repos/qdrant_helper (next batch's work)
- Did not add `.dockerignore` (marginal benefit since Dockerfiles use explicit COPY)

### Sesi recap (high-level)

Sesi 2026-05-31 13:51 (continuation of 13:05) = autonomous quality stack #4. 3 stacks shipped:
1. **SHA-pin prom images** (path J) — `prom/prometheus:v3.4.0` and `prom/alertmanager:v0.28.1` updated to manifest-list digests in 3 places (docker-compose.yml + 2 CI validation steps).
2. **Mypy strict expansion 4 → 11 modules** — 7 new modules pass strict mode (5 already clean, 2 needed tiny fixes: explicit `str()` cast in `llm.py:38` and `isinstance(list)` validation in `pr_review.py:42`).
3. **boto3 version alignment** — agent `1.43.14` → `1.43.15` to match bot's pin. Patch-level, low-risk consistency fix.

---

## 🤝 FOR NEXT SESSION (detailed handoff)

**Where we left off:** Sesi 2026-05-31 13:51 — SHA-pin prom + mypy strict 7 new modules + boto3 align. Path A still unblocked.

### Session 2026-05-31 13:51 — what shipped (3 commits)

**Stack 13 — SHA-pin remaining production images:**

1. **`ci: SHA-pin prom/prometheus and prom/alertmanager images`**
   - Both images previously tag-only pinned (`v3.4.0`, `v0.28.1`)
   - Updated to manifest-list digests in 3 places (docker-compose.yml + 2 deploy.yml validation steps)
   - Pinned: `prom/prometheus:v3.4.0@sha256:78ed1f9050eb9...`, `prom/alertmanager:v0.28.1@sha256:27c475db5fb...`
   - Caddy was the only fully SHA-pinned image; these were the remaining outliers
   - Supply chain hygiene: protects against tag re-tagging or upstream compromise
   - Dependabot already groups Docker image updates, so SHA bumps surface as PRs naturally

**Stack 14 — Mypy strict expansion 4 → 11 modules:**

2. **`ci+types: expand mypy strict whitelist 4 → 11 modules`**
   - Whitelist now: `config`, `docs_sync`, `embedding`, `gitlab_review`, `journal`, `llm`, `meeting_notes`, `pr_review`, `skills`, `telegram`, `tools`
   - 5 modules clean as-is, 2 needed tiny fixes:
     - `llm.py:38` — `return data["choices"][0]["message"]["content"].strip()` → `return str(data["choices"][0]["message"]["content"]).strip()` (json.loads returns Any, needed explicit cast)
     - `pr_review.py:42-49` — `get_whitelist()` was returning `json.loads(...)` directly; now validates `isinstance(data, list)` and coerces items to `str`
   - 50% of agent modules now pass strict mode (11/22)
   - Remaining harder modules: `deps_watchdog` (303 stmts), `code_repos` (375 stmts), `qdrant_helper` (102 stmts), `sync` (101 stmts), `main` (355 stmts), `workflow`, `vps_status`, `system_status`, `resource_alerts` — likely require more substantive type fixes
   - CI step + pre-commit pre-push hook updated in lockstep

**Stack 15 — boto3 version alignment:**

3. **`chore: align boto3 version between agent and bot (1.43.14 → 1.43.15)`**
   - Agent `langgraph-agent/requirements.txt`: `1.43.14` → `1.43.15`
   - Bot `telegram-bot/requirements.txt`: unchanged (`1.43.15`)
   - Patch-level diff, low-risk consistency fix
   - Repo housekeeping check also confirmed: no `.flake8` / `setup.cfg` / `pyproject.toml` dead config (clean), `httpx==0.28.1` already aligned across both services, `.gitignore` healthy

### Production state at handoff (NOT re-verified this session)

Last verified: 2026-05-31 ~13:13 UTC via deploy run 26713505954.

**Containers (assumed unchanged):**
```
alertmanager      Up (healthy)
caddy             Up
calcom            Up (healthy)
langgraph-agent   Up (healthy)
n8n               Up (healthy)
prometheus        Up (healthy)
telegram-bot      Up
```

**CI pipeline (after this session):**
- `lint` (~80-100s estimated, was ~70-90s) — 8 gates total
- `test` (~30s) — 409 tests, floor 27%
- `deploy` (~1m32-2m03s) — Docker compose up + post-deploy probes
- Node 24 active for all jobs

### Files changed this session

**Infrastructure:**
- `docker-compose.yml` — SHA-pin prom/prometheus + prom/alertmanager
- `.github/workflows/deploy.yml` — SHA-pin prom validation steps + extend mypy-strict file list
- `.pre-commit-config.yaml` — extend `mypy-strict` hook file list

**Application code (2 files, type-annotation only):**
- `langgraph-agent/app/llm.py` — `str()` cast on json.loads access
- `langgraph-agent/app/pr_review.py` — `isinstance(list)` validation + `str()` coerce

**Dependencies:**
- `langgraph-agent/requirements.txt` — boto3 1.43.14 → 1.43.15

**No README/docs/test changes.**

### Active Tasks (for next session)

- [ ] **DOGFOOD WINDOW (active, ~39h elapsed)** — observe 7 features for 1-2 weeks total
- [ ] **ACTIVATE DNS + SSL schedulers** (5 menit) — user runs `/ssl add yourdomain.com`. Now safe.
- [ ] **Onboard remaining 8-13 VPS to Prometheus** — needs IP/SSH list
- [ ] **DECISION POINT: pick next roadmap items** — see "Pick your work". Path A still UNBLOCKED.
- [ ] **DEFERRED: Phase 2 auto-PR/auto-remediation** — wait dogfood signal
- [ ] **DEFERRED: Grafana, py3.14**

### Recently Completed (chronological)

- ✅ [2026-05-31 13:51 UTC] **boto3 version alignment** — patch-level consistency fix
- ✅ [2026-05-31 13:45 UTC] **Mypy strict expansion 4 → 11** — 7 new modules in whitelist, 2 tiny fixes
- ✅ [2026-05-31 13:35 UTC] **SHA-pin prom images** — manifest-list digests in 3 places
- ✅ [2026-05-31 13:05 UTC] **Caddy + promtool + amtool CI gates** — 3 new validation steps
- ✅ [2026-05-31 13:00 UTC] **Mypy strict +tools.py** — 4th module
- ✅ [2026-05-31 12:50 UTC] **Pytest batch 4** — 129 new tests, floor 23→27
- ✅ [2026-05-31 12:35 UTC] **README Local Development section** — 83 lines
- ✅ [2026-05-31 12:25 UTC] **Mypy strict whitelist (3 modules)** — embedding/journal/telegram
- ✅ [2026-05-31 12:10 UTC] **Pytest batch 3** — 75 new tests, floor 19→23
- ✅ [2026-05-31 12:00 UTC] **cmd_* docstring audit** — 0/29 missing, deferred
- ✅ [2026-05-31 11:30 UTC] **Pytest batch 2** — 89 new tests, floor 14→19
- ✅ [2026-05-31 10:30 UTC] **Orphan-ref script extraction** — multi-file walker
- ✅ [2026-05-31 09:15 UTC] **Pytest batch 1** — 46 new tests, floor 12→14
- ✅ [2026-05-31 09:00 UTC] **Logging standardization** — 8 modules
- ✅ [2026-05-31 08:30 UTC] **Pre-commit hooks** — initial config
- ✅ [2026-05-31 08:15 UTC] **GHA action SHA pinning** — `run-command.yml`

### Lessons from this session

1. **Mypy strict scaling pattern** — most "small" modules (50-200 stmts) pass strict mode with 0-1 line fixes. Bigger modules (300+ stmts with deep external state) need substantial type work. Sweet spot for batch ratchet: scan all modules, add the clean ones immediately, defer the dirty ones to dedicated cleanup sessions.
2. **Manifest-list vs single-platform digests** — `docker buildx imagetools inspect` returns top-level "Digest" (manifest list, multi-arch) plus per-platform child digests. For SHA-pinning in production, always pin to manifest-list digest, not platform-specific. Caddy was already SHA-pinned to manifest-list — followed same pattern for prom images.
3. **`json.loads` Any-return is the most common strict-mode trap** — both `llm.py` and `pr_review.py` failures came from using `json.loads(...)` returns directly without isinstance/cast. Pattern: `data = json.loads(...)`, then `isinstance(data, list)` or `str(data[...])` to satisfy `no-any-return`.
4. **Repo housekeeping is fast-but-fast-evaporating-ROI** — finding `.flake8` (none), checking requirements (1 minor mismatch), checking `.gitignore` health (clean) took <30 minutes total. Worth doing once per major project shake-up. Diminishing returns after first sweep.
5. **Diminishing returns warning is real** — by stack #15, "low-hanging fruit" exhausted. Next sessions should pivot to single-focus work (path A bot.py refactor) or wait for dogfood signal. Continuing autonomous quality work past this point would mean pursuing mock-heavy tests with poor ROI.

### Verify state in <2 minutes

```bash
git status                                    # clean
git log --oneline -12                         # matches above
gh run list --workflow=deploy.yml --limit 3   # last 3 green
python3 -m pytest -q                          # 409 passed, ~28% coverage
python3 -m ruff check --select=F telegram-bot langgraph-agent tests
python3 -m mypy --config-file=mypy.ini telegram-bot langgraph-agent
python3 -m mypy --strict langgraph-agent/app/{embedding,journal,telegram,tools}.py
python3 -m compileall -q telegram-bot langgraph-agent
python3 scripts/lint_orphan_refs.py
pre-commit run --all-files                    # all 4 hooks pass
pre-commit run --all-files --hook-stage pre-push  # +mypy lenient + strict
```

If anything fails: do not proceed. Diagnose first.

### Pick your work

**If user says "lanjutkan" / "continue" without specifics, ASK FIRST.** Multiple valid directions:

| Path | Effort | Risk | Notes |
|---|---|---|---|
| **A. Bot.py refactor pilot** (DNS watchdog) | 4-6h | 🟡 Med | UNBLOCKED. Multi-file orphan walker shipped. Smallest blast radius. |
| **B. Test Coverage Agent (Tier 1.5)** | 2-3h design + 4-6h impl | 🟡 Med | Foundation: coverage.xml, baseline 28.45%. |
| **D. Pytest expansion batch 5** (sync 0%, vps_status 0%, system_status 0%, resource_alerts 0%, workflow 0%, qdrant_helper 24%, code_repos 58%→80%) | 3-4h | 🟢 Low | Continue to floor 30+. |
| **I. Mypy strict expansion** | 1-2h | 🟢 Low | Try `sync`, `qdrant_helper`. Each new module = ratchet. |
| **J. Pin image SHAs** | 1h | 🟢 Low | `prom/prometheus:v3.4.0` and `prom/alertmanager:v0.28.1` not SHA-pinned. Caddy already SHA-pinned. |
| **H. Add cmd_* docstrings** | 2-3h | 🟢 Low | 29/29 cmd_* functions di bot.py tanpa docstring. Defer ke saat refactor (path A). |
| **G. Wait for dogfood signal** | — | — | Phase 2 work blocked. ~5-12 days remaining. |

**Blocked on user input (don't start without):**
- Spec-to-Implementation (needs PRD)
- Onboard 8-13 VPS to Prometheus (needs IP/SSH list)
- Activate DNS+SSL schedulers (needs `/ssl add yourdomain.com` via Telegram)

### Bot.py refactor — UNBLOCKED 🎉

The orphan-ref walker has been extracted to `scripts/lint_orphan_refs.py` and supports multi-file packages. CI gate calls the script, pre-commit also wires it.

**Pattern for refactor:**
```
telegram-bot/
├── __init__.py          (new)
├── bot.py               (orchestrator + handler registration only)
├── watchdogs/
│   ├── __init__.py
│   ├── ssl.py
│   ├── dns.py           ← START HERE
│   ├── drift.py
│   ├── capacity.py
│   ├── hygiene.py
│   ├── firewall.py
│   ├── deps.py
│   └── morning_brief.py
├── infra/
│   ├── ssh.py
│   ├── prometheus.py
│   └── config_store.py
└── handlers/            (optional, extract cmd_* if useful)
```

Start with **DNS watchdog** — smallest blast radius. ~200 lines.

### Safety net you can rely on

- **8 CI lint gates** — actionlint, ruff F, mypy lenient (whole package), mypy strict (4-module whitelist), orphan-refs script (multi-file ready), compileall, caddy validate, promtool, amtool
- **5 pre-commit hooks** + 2 pre-push hooks
- **409 pytest tests** (was 280) — parser + module-unit regressions caught
- **Coverage floor 27%** (was 23%) — actual at 28.45%
- **Strict mypy whitelist** — `embedding`, `journal`, `telegram`, `tools`
- **Config validation** — Caddyfile (caddy validate), Prometheus + alert rules (promtool), Alertmanager (amtool)
- **Deploy gated** `needs: [lint, test]` — broken code can't reach prod
- **README has Local Development section** — full CI gate reproduction documented

### What this session DID NOT do (handoff items)

- Did not refactor bot.py (still unblocked, ready for path A)
- Did not write Test Coverage Agent
- Did not touch Phase 2 logic — wait dogfood signal
- Did not migrate to Python 3.14 (waiting for py-rust-stemmers wheels)
- Did not add cmd_* docstrings
- Did not SHA-pin prom/prometheus + prom/alertmanager (caddy SHA-pinned, but those two still use tag-only)
- Did not refactor Caddyfile to remove env-var-as-global-option workaround (CI passes stub env vars)
- Did not refactor alertmanager.yml PLACEHOLDER strings (CI sed-substitutes for validation)

### Sesi recap (high-level)

Sesi 2026-05-31 13:05 (continuation of 12:35) = autonomous quality stack #3. 4 stacks shipped:
1. **Pytest batch 4** — 129 new tests (tools 44 + code_repos 85). Coverage 24.78% → 28.45% (+3.67pp). Floor bumped 23 → 27.
2. **Mypy strict +tools.py** — 4th module added to whitelist. CI step + pre-commit hook updated. Module passes as-is, no code changes needed.
3. **Caddy + Prometheus + Alertmanager config validation** — 3 new CI gates. Catches: invalid Caddyfile syntax, malformed prometheus rules, broken alertmanager routing. Smoke-tested locally with docker pull + run.
4. **(README Local Development) — already done in 12:35 session.**

---

## 📜 PREVIOUS SESSION (2026-05-30 part 2) archived below

**Where we left off:** Sesi 2026-05-30 part 2 — shipped 3 read-only infra agents (Docker Hygiene, DNS Health, Firewall Audit) + CI infrastructure hardening (lint gate + first pytest suite) + dependabot housekeeping. Production state stabil, dogfood window aktif untuk 7 fitur Phase 1.

### Session 2026-05-30 part 2 — what shipped (8 PRs to main)

**Feature work:**
1. **PR #14** — `feat(bot): docker hygiene + DNS health + firewall audit` (commit `aa34e0b`)
   - 3 read-only infra watchdogs inline di `bot.py` (~520 lines total)
   - **Docker Image Hygiene** (Tier I.6) daily 02:15 WIB — `_run_docker_hygiene`, `_parse_docker_df`, `_docker_size_to_gb`, `cmd_hygiene`
   - **DNS Health Monitor** (Tier I.7) every 4h — multi-resolver dig (Cloudflare/Google/Quad9), `_check_domain_consistency`, `cmd_dns`
   - **Firewall Audit Agent** (Tier I.5) daily 03:30 WIB — SSH `ss -H -tlnp`, public/loopback split, per-VPS whitelist, `cmd_firewall`
   - Reuse pattern: `_ssh_exec`, `_get_ssh_targets`, `_config_get/_set`, JSON config store, silent-on-clean alert
   - Dockerfile: added `dnsutils` (dig) + `iproute2` (fallback ss)
   - 5 BotCommand entries: `/hygiene`, `/dns`, `/firewall` + add/del/list subcommands
   - All schedulers wired in `post_init`, AST orphan-ref check passed (38 handler/scheduler refs / 124 functions)
   - Phase 2 firewall auto-remediation deferred until audit data validates noise

**Operational improvements:**
2. **PR #15** — `chore(ci): capture telegram-bot startup log on deploy` (commit `7987f2d`)
   - Adds `docker logs telegram-bot --tail 80` to post-deploy block
   - Filtered grep: scheduler registration / errors
   - Validated useful 3× this session (after #14, #9+#7, #16)

3. **PR #16** — `ci: gate deploy on lint job` (commit `761836e`)
   - New `lint` job in deploy.yml runs sebelum deploy
   - Step 1: `compileall` semua .py di telegram-bot/ + langgraph-agent/
   - Step 2: AST orphan-ref check on bot.py
     - Walks all `CommandHandler(name, target)` + `run_daily/run_repeating/run_once(callback, ...)` calls
     - Verifies each target/callback resolves to function defined in same module
     - **Catches the exact failure mode** dari sesi 2026-05-30 part 1 (cmd_deps orphan)
   - `deploy` job declares `needs: lint` → deploy skipped on lint failure
   - Smoke-tested: injecting `cmd_dns_TYPO_NOT_DEFINED` caught at line 3509

4. **PR #17 + #18** — `ci: add pytest suite covering bot.py + deps_watchdog parsers` (commits `a32f824` + `ed5f211`)
   - **71 unit tests** across 2 files (`tests/test_bot_parsers.py`, `tests/test_deps_watchdog.py`)
   - bot.py coverage: `_docker_size_to_gb`, `_parse_docker_df`, `_format_hygiene_section`, `_parse_listening_ports`, `_human_bytes`, `_human_uptime`, `_container_health`, `_is_fresh_restart`
   - deps_watchdog.py coverage: `_strip_npm_range`, `_parse_package_json`, `_parse_requirements_txt`, `_parse_pyproject`, `_parse_go_mod`, `_dedupe`, `_severity_from_detail`, `_collect_manifests`
   - New `test` job in deploy.yml — `deploy` now `needs: [lint, test]`
   - PR #18 was hot-fix: initial test job failed CI (`yaml` missing transitively via `app.code_repos`); fixed by installing full langgraph-agent reqs
   - **CI gate working as designed**: caught broken state before reaching VPS, no prod regression
   - Local: 71 passed in 1.72s | CI: 71 passed in 1.72s

**Dependency housekeeping:**
5. **PR #9** — `fix(deps): langgraph-agent minor-patch batch` (commit `f1540d1`)
   - fastapi 0.136.1→0.136.3, uvicorn 0.47.0→0.48.0, langgraph 1.2.0→1.2.1
   - boto3 1.43.9→1.43.14, PyYAML 6.0.2→6.0.3
   - All within minor/patch, no breaking changes

6. **PR #7** — `fix(deps): bump boto3 to 1.43.15 in telegram-bot` (commit `a337740`)
   - Patch release, R2 upload uses stable s3 client API

7. **PR #8** — closed (py3.14 migration)
   - Deferred per existing TASK.md decision pending py-rust-stemmers wheels

8. **5 dependabot labels created** via `gh label create`:
   - `dependencies`, `python`, `docker`, `langgraph-agent`, `telegram-bot`
   - Eliminates "label not found" warning on future dependabot PRs

### Production state at handoff (verified live)

**Containers (verified via run 26698097199 post-deploy probe):**
```
alertmanager      Up (healthy)
caddy             Up
calcom            Up (healthy)
langgraph-agent   Up (healthy) — fastapi 0.136.3, uvicorn 0.48.0, langgraph 1.2.1
n8n               Up (healthy)
prometheus        Up (healthy)
telegram-bot      Up — boto3 1.43.15, dnsutils + iproute2 installed
```

**7 schedulers registered (verified via deploy log capture):**
- Health check every 300s
- Morning brief 07:00 WIB
- Drift 02:00, Capacity 02:10, **Hygiene 02:15** (NEW), Deps 03:00, **Firewall 03:30** (NEW) WIB

**Schedulers conditional pada config (currently idle):**
- SSL check — needs `SSL_CHECK_DOMAINS` env or `/ssl add domain.com`
- DNS check — auto-seeds dari SSL list, currently empty

**CI pipeline (verified end-to-end):**
- `lint` job ~10s — compileall + AST orphan-ref
- `test` job ~30s — 71 pytest unit tests
- `deploy` job ~1m — Docker compose up + post-deploy probes

### How to verify CI gate is working

```bash
# Trigger lint failure: rename a CommandHandler target to a typo
sed -i 's/cmd_dns/cmd_dns_TYPO/' telegram-bot/bot.py
git commit -am "test: trigger CI"
git push  # CI should fail at lint job, deploy skipped

# Trigger test failure: break a parser
# Edit _docker_size_to_gb to multiply GB by 1024
# CI should fail at test job, deploy skipped

# Both verified working this session
```

### Files changed this session

**Application code:**
- `telegram-bot/bot.py` — +633 lines (3 new watchdog blocks + handlers + scheduler regs)
- `telegram-bot/Dockerfile` — added `dnsutils` + `iproute2` to apt install

**Infrastructure / config:**
- `.github/workflows/deploy.yml` — added `lint` job + `test` job + post-deploy bot log capture
- `.env.example` — 3 new sections (Docker Hygiene, DNS, Firewall Audit)
- `langgraph-agent/requirements.txt` — bumped 5 deps (#9)
- `telegram-bot/requirements.txt` — bumped boto3 (#7)

**New files:**
- `tests/__init__.py`, `tests/conftest.py`
- `tests/test_bot_parsers.py` (37 tests)
- `tests/test_deps_watchdog.py` (34 tests)
- `pytest.ini`

**Documentation:**
- `AI_AGENT_ROADMAP.md` — I.5/I.6/I.7 marked done, shipped table updated
- `TASK.md` — this update

### Active Tasks (for next session)

- [ ] **DOGFOOD WINDOW (active, started 2026-05-30 23:00 UTC)** — observe 7 features on real workload for 1-2 weeks:
  - Phase 1 (since 2026-05-30 morning): `/meeting`, `/deps`, `/docsync`, Auto PR Review
  - Phase 2 (since this session): `/hygiene`, `/dns` (idle), `/firewall`
- [ ] **ACTIVATE DNS + SSL schedulers** (5 menit) — user runs `/ssl add yourdomain.com` via Telegram, DNS auto-seeds. Without this, 2 schedulers stay idle.
- [ ] **Onboard remaining 8-13 VPS to Prometheus** — needs list from user (IP, provider, SSH access)
- [ ] **DECISION POINT: pick next roadmap items** — see "Next session focus" below
- [ ] **DEFERRED: Deps Watchdog Phase 2 (auto-PR)** — wait Phase 1 dogfood data
- [ ] **DEFERRED: Docs Sync Phase 2 (auto-PR)** — wait Phase 1 dogfood data
- [ ] **DEFERRED: Firewall Audit Phase 2 (auto-remediation)** — wait audit signal data
- [ ] **DEFERRED: Grafana** — wait actual trend visualization need
- [ ] **DEFERRED: py3.14** — wait py-rust-stemmers wheels (PR #8 closed pending this)

### Next session focus (PRIORITY ORDER)

**Tier 1 — Fully autonomous AI-suitable, no blocker:**

1. **Lint check for langgraph-agent** (~1 jam) — extend the AST orphan-ref pattern from PR #16 to cover FastAPI route handlers in `app/main.py`. Same approach: walk AST, find `@app.get/post/...` decorators + their target functions. Catches missing endpoint implementations before deploy.

2. **Refactor bot.py into modules** (1-2 hari, RECOMMENDED) — `bot.py` is now **3500+ lines** with 8 watchdogs inline. Extract to `telegram-bot/watchdogs/`:
   ```
   telegram-bot/
   ├── bot.py (orchestrator + handlers registration only)
   ├── watchdogs/
   │   ├── __init__.py
   │   ├── ssl.py, dns.py, drift.py, capacity.py
   │   ├── hygiene.py, firewall.py, deps.py, morning_brief.py
   │   └── health_check.py
   └── infra/
       ├── ssh.py (shared `_ssh_exec`, `_get_ssh_targets`)
       ├── prometheus.py (shared `_prom_query`)
       └── config_store.py (shared `_config_get`/`_config_set`)
   ```
   - **Why now:** before next watchdog adds another 200+ lines. Tech debt grows quadratic with each new feature.
   - **Risk:** medium — pure code reorg, no behavior change, but PTB handler registration order matters
   - **Mitigation:** 1 PR per watchdog (8 incremental PRs), each independently verifiable via deploy log capture
   - **Coverage:** 71-test suite catches parser regressions, lint catches orphan refs

3. **Test Coverage Agent** (Tier 1.5 from roadmap, 2-3 hari) — now that test foundation exists:
   - Reuse explore agent → coverage report scan
   - Identify untested public functions
   - Generate test stub + run pytest
   - Auto-PR if test passes
   - First target: pro-secretary itself (eat own dogfood)

**Tier 2 — Blocked on user input:**

4. **Spec-to-Implementation** (2-3 hari) — needs real PRD/feature spec from user
5. **Onboard VPS to Prometheus** — needs IP/SSH list from user

**Tier 3 — Wait for dogfood signal (1-2 weeks minimum):**

6. **Deps Watchdog Phase 2 (auto-PR)** — review noise level on `/deps` reports
7. **Docs Sync Phase 2 (auto-PR)** — review false positive rate on `/docsync`
8. **Firewall Audit Phase 2 (auto-remediation)** — review audit signal accuracy

### Useful commands for next session

```bash
# Verify CI status
gh run list --workflow=deploy.yml --limit 5

# Run tests locally
python3 -m pytest -v

# Run lint check locally
python3 -m compileall -q telegram-bot langgraph-agent
# AST orphan-ref check is inline in deploy.yml, can copy-paste to local script

# Tail bot logs (requires SSH to VPS)
ssh prosec "docker logs telegram-bot --tail 100 -f"

# Trigger DNS + SSL via Telegram
/ssl add domain1.com
/ssl add domain2.com
/dns                    # auto-uses SSL list
```

### Lessons from this session (institutional memory)

1. **CI gate caught broken test** (PR #17→#18) — proved the value within hours of shipping. Without `needs: [lint, test]`, broken pyyaml import would have shipped to prod.

2. **Transitive imports in tests** — `app.deps_watchdog` imports `app.code_repos` which imports `yaml`. Test job needs full langgraph-agent reqs, not just bot's. Future: test new langgraph-agent module → must update CI install step.

3. **GitHub release CDN flakiness** — appleboy/ssh-action download via GitHub releases got 502 once (run 26697264312). Self-resolves on rerun. Not worth fixing unless recurring.

4. **Smoke-test pattern for CI gates** — always intentionally inject the bug we're trying to catch, verify CI catches it, restore. Did this for both lint orphan-ref and pytest gate.

5. **Cancelled deploy ≠ failed deploy** — when 2 PRs merge in quick succession, GitHub auto-cancels the in-flight run via `concurrency.cancel-in-progress`. Showed `[X]` icon but conclusion was `cancelled`, not `failure`. Don't panic.

### Recently Completed

- ✅ [2026-05-30 23:45 UTC] **CI pytest suite shipped** — 71 unit tests across 2 modules, deploy `needs: [lint, test]`, smoke-tested with regression injection
- ✅ [2026-05-30 23:30 UTC] **CI lint gate shipped** — AST orphan-ref check on bot.py, deploy gated on lint pass
- ✅ [2026-05-30 23:18 UTC] **3 dependabot PRs resolved** — #9 + #7 merged, #8 closed (py3.14 deferred), 5 labels created
- ✅ [2026-05-30 23:08 UTC] **Deploy log capture shipped** (PR #15) — post-deploy bot startup log filtered for scheduler/error patterns
- ✅ [2026-05-30 22:55 UTC] **3 read-only infra agents shipped** — Docker Hygiene + DNS Health + Firewall Audit (PR #14)
- ✅ [2026-05-30 10:50 UTC] Auto PR/MR Review silent-failure fixed

---

## 🧠 KEY KNOWLEDGE FOR NEXT AGENT (project-specific gotchas)

**Critical patterns that have caused bugs in the past — agent MUST know these:**

1. **n8n `update:workflow --active=true` ≠ trigger registered.** Writes DB but does NOT hot-reload schedule trigger. **MUST restart n8n after activation.** `scripts/install_n8n_workflows.sh` now auto-handles this.

2. **LLM in `/api/chat` does NOT have function calling.** Workflow is deterministic LangGraph. For destructive ops, use keyword detection in `understand()` node + dedicated node (see `delete_task_node` for pattern).

3. **n8n in container has empty `TZ` env by default.** All Date/cron expressions must be explicit `Asia/Jakarta` in workflow JSON `settings.timezone`.

4. **Vault is bind-mounted RW into agent.** `journal/` dir is created lazily on first journal write. Absent dir = no journal entries yet, NOT a bug.

5. **Internal services NOT exposed to host.** n8n + cal.com via `expose:` only. Test from container = `docker exec n8n wget localhost:5678/healthz`.

6. **Tasks have `user_id='123'` as test data leftover.** Real user is `561827493`.

7. **`n8n list:workflow` shows ALL (active+inactive).** Use `--active=true` flag explicitly.

8. **CI paths-ignore covers docs.** `**.md`, `LICENSE`, `.gitignore`, `docs/**`, `.sisyphus/**` skip Deploy. Code commits DO trigger.

9. **rtk wrapper for git/gh.** Use `rtk git ...` and `rtk gh ...` (not bare git/gh).

10. **Real-time agent test pattern.** `docker exec langgraph-agent python3 /tmp/foo.py` (with script file via `docker cp`) — JSON in shell escaping is brittle.

11. **node_exporter listens on `:19100`, NOT `:9100`.** Some ISPs silently drop SYN to `:9100` in transit. Standard: `--web.listen-address=:19100`. Pro-secretary itself still uses `:9100` (Docker bridge, no ISP transit).

12. **Docker bind-mount pins to inode at container start.** `git pull` rewrites file → new inode → container serves stale. Fix: `docker compose up -d --force-recreate <service>`. Apply to ANY config-driven service with bind-mounted YAML/JSON.

13. **cAdvisor NOT VIABLE on cgroups v2 + overlay2.** Both VPS confirmed cgroups v2 (Ubuntu 22.04+) + Docker overlay2. cAdvisor v0.49-v0.52 all fail: probes legacy `/image/overlayfs/` path, silently skips per-container metrics. Don't retry without upstream fix.

14. **Container monitoring uses SSH, not metrics.** Bot SSH → target VPS → `docker ps --format`. Config in `MONITOR_SSH_TARGETS` env (JSON). Deploy script generates ed25519 keypair if missing, injects into bot container via stdin pipe. Pubkey must be in target's `authorized_keys`.

15. **Never Docker bind-mount single files from ~/.ssh.** Docker creates empty directories instead of files when source has restrictive permissions (700 dir, 400 file). Use `docker cp` or stdin pipe instead.

---

## 📍 CURRENT CONTEXT

### What We're Building
Self-hosted AI personal secretary system - 24/7 assistant yang tahu semua pekerjaan user, berjalan lokal dengan kontrol penuh.

### Tech Stack
- **Orchestrator:** n8n (5 active workflows: Daily Briefing, Task Reminder, Cal.com Booking Indexer, EOD Summary, Personal Journal)
- **AI Engine:** LangGraph agent (custom FastAPI container)
- **Interface:** Telegram bot (PTB 22.7)
- **Scheduling:** Cal.com (webhook → n8n)
- **Knowledge:** Obsidian vault (bind-mounted RW, auto-sync 30min)
- **Memory:** Qdrant Cloud (384-dim, all-MiniLM-L6-v2 via fastembed)
- **LLM:** OpenAI-compatible provider via SSH tunnel (autossh+systemd)
- **Files:** Cloudflare R2 (S3-compatible)
- **Database:** External PostgreSQL
- **Monitoring:** Prometheus v3.4.0 + Alertmanager v0.28.1 + node_exporter (2 VPS scraped)
- **Reverse Proxy:** Caddy (Let's Encrypt auto)

### Repository
- **Location:** `/home/ubuntu/bench/pro-secretary/`
- **Remote:** `github.com:oppytut/pro-secretary.git`
- **Branch:** `main`

### Indexed repos (Q&A)
- `gmedia-erp` (github, main) — 3,365 chunks @ `63549bae`
- `dokfin-backend` (gitlab, main) — 3,591 chunks @ `7fa15fe0`

### Monitoring targets
- `pro-secretary` (`host.docker.internal:9100`) — up
- `erpstg` (`119.2.52.24:19100`) — up

---

## 🗂️ PROJECT STRUCTURE

```
pro-secretary/
├── docker-compose.yml          # 7 containers (n8n, agent, calcom, bot, prometheus, alertmanager, caddy)
├── .env.example                # Environment template
├── TASK.md                     # This file (lean handoff)
├── TASK_ARCHIVE.md             # Full history (2562 lines)
├── langgraph-agent/
│   ├── app/                    # FastAPI + LangGraph + fastembed
│   │   ├── main.py             # Endpoints (/api/chat, /api/repos/*, /api/skills/*, etc.)
│   │   ├── workflow.py         # LangGraph StateGraph (understand → retrieve → generate)
│   │   ├── code_repos.py       # Multi-repo Q&A (3-pass retrieval + citation)
│   │   ├── skills.py           # Skill logging + semantic recall
│   │   ├── resource_alerts.py  # VPS/PostgreSQL/Qdrant threshold alerts
│   │   └── ...
│   ├── repos.yml               # Configured repos (gmedia-erp, dokfin-backend)
│   └── Dockerfile
├── telegram-bot/
│   ├── bot.py                  # PTB 22.7 (commands, voice, skills, monitor)
│   └── Dockerfile
├── prometheus/
│   ├── prometheus.yml          # Scrape config (2 VPS targets)
│   ├── alert_rules.yml         # 10 alert rules
│   ├── alertmanager.yml        # Telegram receiver (placeholder-based)
│   └── alertmanager-entrypoint.sh  # sed-substitute bot_token at start
├── scripts/
│   ├── health_check.sh         # 5-min cron, resource alert trigger
│   ├── install_n8n_workflows.sh # Idempotent workflow import + activate
│   └── ...
├── n8n/workflows/              # 5 workflow JSONs
├── caddy/Caddyfile
└── .github/workflows/
    ├── deploy.yml              # Push-to-main auto-deploy
    ├── run-command.yml          # Dispatch: execute command on VPS
    ├── install-n8n-workflows.yml
    └── deactivate-n8n-workflow.yml
```

---

## 🚀 CI/CD

**Workflow:** `.github/workflows/deploy.yml`  
**Trigger:** Push to `main` (paths-ignore: `**.md`, `docs/**`, `.sisyphus/**`)  
**Flow:** SSH → git pull → docker compose build telegram-bot langgraph-agent → up -d → force-recreate prometheus alertmanager → health probes

---

## 🔄 HOW TO USE THIS FILE

### Starting New Session
```bash
"Baca /home/ubuntu/bench/pro-secretary/TASK.md dan lanjutkan pekerjaan dari situ"
```

### After Completing Work (MANDATORY)
1. Update **CURRENT WORK** section
2. Move completed items to **Recently Completed** (keep last 5)
3. Update **Last Updated** timestamp
4. Older entries → `TASK_ARCHIVE.md`

### When Stuck
1. Check **KEY KNOWLEDGE** section (12 gotchas)
2. Check `TASK_ARCHIVE.md` for historical context
3. Use `rtk gh workflow run run-command.yml` for VPS diagnostics
