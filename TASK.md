# 🎯 TASK HANDOFF

**Last Updated:** 2026-05-31 15:46 UTC
**Project:** AI Personal Secretary Stack
**Status:** ✅ 13 features shipped + bot.py refactor batch 3 complete (5 watchdogs + 4 infra modules extracted, 488 tests, 35% coverage, mypy strict 20 modules). Sesi 2026-05-31 closed dengan 28 commits autonomous (~9h45m).

> ⚠️ **HANDOFF NOTE — User is switching to a fresh opencode session.** Read `## 🚀 FRESH SESSION ENTRYPOINT` below to pick up. All work is committed + pushed + CI green. Working tree clean.

> Full history (2562 lines, sessions 2026-05-08 → 2026-05-24) archived in [`TASK_ARCHIVE.md`](TASK_ARCHIVE.md).

---

## 📦 SESSION HANDOFF (2026-05-31 15:46 UTC) — for fresh opencode session

**Last activity:** Sesi 2026-05-31 closed at 15:46 UTC after run `26717013941` deployed successfully.

**Latest commits (last 5):**
```
fc04dba fix(tests): remove unused pytest imports (CI ruff F401)
1e84673 ci+types: expand mypy strict whitelist 11 -> 20 modules
19af3c9 test: unit tests for infra/prom + watchdogs/{deps,capacity,drift}
4efa952 refactor(bot): extract Deps + Capacity + Drift watchdogs + infra/prom.py
4b4f523 docs(TASK): handoff for sesi 2026-05-31 15:18 (refactor batch 2)
```

**Latest deploy verified:**
- Run `26717013941` — lint+test+deploy 1m34s — all green
- All 7 schedulers registered: health 300s, morning brief 07:00, drift 02:00, capacity 02:10, deps 03:00, hygiene 02:15, firewall 03:30 WIB
- DNS+SSL schedulers idle (SSL list empty — expected)
- All 7 containers healthy (verified via post-deploy probes)

**State to verify in new session (paste these):**
```bash
git status                                    # expect: clean, on main
git log --oneline -5                          # expect: matches above
gh run list --workflow=deploy.yml --limit 2   # expect: last 2 'ok'
python3 -m pytest -q                          # expect: 488 passed, ~35% cov
python3 scripts/lint_orphan_refs.py           # expect: 12 files, 130 functions clean
```

**What's safe to start without asking:**
- Refactor diminishing — bot.py at 2796 LOC. Remaining: Hygiene (~205 LOC, 🟡), Firewall (~280 LOC, 🟡), Morning Brief (~125 LOC, 🟡 multi-dep). All medium-risk now.
- Better next: Mypy strict expansion to remaining `bot.py` SHOULD WAIT — bot.py too large + many `attr-defined` patterns. Defer.
- See `## 🚀 FRESH SESSION ENTRYPOINT` → "Pick your work" table

**What's blocked on user:**
- Spec-to-Implementation (PRD)
- Onboard 8-13 VPS (IP/SSH list)
- Activate DNS+SSL (`/ssl add yourdomain.com` via Telegram)

**Cumulative metrics from sesi 2026-05-31 (~9h45m, 28 commits):**
- Tests: 71 → 488 (+417, 6.9x)
- Coverage: 12.75% → 35% (+22.25pp)
- Coverage floor: 12% → 27%
- CI lint gates: 4 → 8
- Pre-commit hooks: 0 → 6
- Mypy strict modules: 0 → 20 (~85% of "leaf" modules)
- SHA-pinned images: 1 → 5 (all production)
- **bot.py LOC: 3524 → 2796 (-728, -20.7%)**
- **New packages: telegram-bot/{infra,watchdogs}/** — 5 watchdogs + 4 infra modules extracted

**Production state at handoff:** 7 containers up + healthy (verified via run 26717013941). Dogfood window ~41h elapsed of 1-2 week target.

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
