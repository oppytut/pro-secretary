# 🎯 TASK HANDOFF

**Last Updated:** 2026-05-31 05:21 UTC
**Project:** AI Personal Secretary Stack
**Status:** ✅ 13 features shipped + CI hardened (3 lint gates: bot.py orphan + main.py cross-module orphan + ruff F401, 71 unit tests, coverage baseline 12.8%, Node 24 active). Sesi 2026-05-31 closed dengan 4 PR ke main.

> Full history (2562 lines, sessions 2026-05-08 → 2026-05-24) archived in [`TASK_ARCHIVE.md`](TASK_ARCHIVE.md).

---

## 🤝 FOR NEXT SESSION (read this first)

**Where we left off:** Sesi 2026-05-31 — extended lint gate ke langgraph-agent main.py + autonomous stack (Node 24 + pytest-cov + ruff F401). Dogfood window terus berjalan (7 fitur Phase 1, sejak 2026-05-30 23:00 UTC, ~30h elapsed).

### Session 2026-05-31 — what shipped (4 commits ke main)

**Feature work:**

1. **`ci: extend lint gate to langgraph-agent main.py orphan-refs`** (early sesi)
   - New step di `lint` job: parses `langgraph-agent/app/main.py` AST, extracts `module.attr` references where `module` is from `from . import ...`, verifies each `attr` is a top-level name in sibling `.py` file
   - Catches same failure mode as bot.py gate (PR #16) but for cross-module calls (e.g. `pr_review.handle_pr_event` typo)
   - Local: 44 cross-module refs across 16 modules clean
   - Live smoke test: run 26703689068 caught injected typo, run 26703708905 restored green

2. **`ci: opt into Node 24 for GHA actions`** (autonomous stack #1)
   - Added `FORCE_JAVASCRIPT_ACTIONS_TO_NODE24: "true"` di workflow-level `env`
   - Eliminates Node 20 deprecation noise; verified live in run 26703894545
   - GitHub deprecates Node 20 di June 16, 2026

3. **`ci: add pytest-cov + coverage baseline summary`** (autonomous stack #2)
   - Foundation untuk Test Coverage Agent (Tier 1.5)
   - `pytest.ini`: `--cov=bot --cov=app --cov-report=term --cov-report=xml`
   - New step parses `coverage.xml`, writes per-package breakdown ke `GITHUB_STEP_SUMMARY` (markdown table, sorted ascending by coverage)
   - **Baseline (verified):** Line 12.8% (634/4973), `langgraph-agent.app` 11.0%, `telegram-bot` 14.9%
   - No threshold enforced — pure measurement

4. **`ci: gate unused imports via ruff F401 + cleanup existing`** (autonomous stack #3)
   - New step di `lint` job: `ruff check --select=F401`
   - Cleanup 4 existing violations:
     - `deps_watchdog.py`: removed unused `config` import
     - `gitlab_review.py`: removed unused `hashlib` + `llm` imports
     - `system_status.py`: removed unused `subprocess` import
   - Verified each not re-exported (no `__all__` in `app/`)

### Production state at handoff (verified live)

**Containers (verified via run 26704109680 post-deploy probe):**
```
alertmanager      Up (healthy)
caddy             Up
calcom            Up (healthy)
langgraph-agent   Up (healthy)
n8n               Up (healthy)
prometheus        Up (healthy)
telegram-bot      Up
```

**CI pipeline now covers (4 lint gates + coverage):**
- `lint` (~6s) — compileall + **ruff F401 (NEW)** + bot.py orphan-ref + **main.py cross-module orphan-ref (NEW)**
- `test` (~33s) — 71 pytest tests + **coverage baseline summary (NEW)**
- `deploy` (~1m32-2m03s) — Docker compose up + post-deploy probes
- **Node 24** active for all jobs

### Files changed this session

**Infrastructure (4 PRs):**
- `.github/workflows/deploy.yml` — +124 lines net (3 new steps in lint, 2 new steps in test, env block, lint step ordering)
- `pytest.ini` — coverage flags
- `.gitignore` — `.coverage`, `coverage.xml`, `htmlcov/`

**Application code (cleanup only):**
- `langgraph-agent/app/deps_watchdog.py` — -1 line
- `langgraph-agent/app/gitlab_review.py` — -2 lines
- `langgraph-agent/app/system_status.py` — -1 line

**Documentation:**
- `TASK.md` — this update

### Active Tasks (for next session)

- [ ] **DOGFOOD WINDOW (active, started 2026-05-30 23:00 UTC, ~30h elapsed)** — observe 7 features on real workload for 1-2 weeks total:
  - Phase 1 (since 2026-05-30 morning): `/meeting`, `/deps`, `/docsync`, Auto PR Review
  - Phase 2 (since 2026-05-30 part 2): `/hygiene`, `/dns` (idle), `/firewall`
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

1. **Refactor bot.py into modules** (1-2 hari, RECOMMENDED) — `bot.py` 3500+ lines dengan 8 watchdog inline. Extract to `telegram-bot/watchdogs/`:
   ```
   telegram-bot/
   ├── bot.py (orchestrator + handlers registration only)
   ├── watchdogs/
   │   ├── ssl.py, dns.py, drift.py, capacity.py
   │   ├── hygiene.py, firewall.py, deps.py, morning_brief.py
   │   └── health_check.py
   └── infra/
       ├── ssh.py, prometheus.py, config_store.py
   ```
   - **Why now:** before next watchdog adds another 200+ lines. Tech debt grows quadratic.
   - **Risk:** medium — pure code reorg, no behavior change, but PTB handler registration order matters
   - **Mitigation:** 1 PR per watchdog (start with DNS or Hygiene, smallest blast radius), verifiable via deploy log capture
   - **Coverage:** 71-test suite + 3 lint gates + ruff F401 sebagai safety net
   - **Heads-up:** orphan-ref check in deploy.yml currently parses `bot.py` as single file. Refactor will need to update the AST walker to handle multi-file or follow imports.

2. **Test Coverage Agent** (Tier 1.5 from roadmap, 2-3 hari) — coverage baseline already shipped:
   - Reuse explore agent → coverage.xml parser
   - Identify untested public functions (start dengan files showing 0% in baseline: `docs_sync`, `gitlab_review`, `journal`, `meeting_notes`, `pr_review`, `resource_alerts`, `skills`, `sync`, `system_status`, `telegram`, `tools`, `vps_status`, `workflow`)
   - Generate test stub + run pytest
   - Auto-PR if test passes
   - First target: pro-secretary itself (eat own dogfood)

3. **Quick wins backlog (autonomous-suitable, low risk):**
   - Pin remaining GHA actions ke SHA (audit + fix any miss)
   - Standardize logging format (`logging.getLogger(__name__)` everywhere)
   - Pytest expansion untuk modul belum ter-cover (`docs_sync`, `meeting_notes`, `pr_review` parsers, `gitlab_review`)
   - Mypy strict gate for public API (Pydantic models di main.py sudah typed, gap di bot.py)

**Tier 2 — Blocked on user input:**

4. **Spec-to-Implementation** (2-3 hari) — needs real PRD/feature spec from user
5. **Onboard VPS to Prometheus** — needs IP/SSH list from user

**Tier 3 — Wait for dogfood signal (1-2 weeks minimum from 2026-05-30):**

6. **Deps Watchdog Phase 2 (auto-PR)** — review noise level on `/deps` reports
7. **Docs Sync Phase 2 (auto-PR)** — review false positive rate on `/docsync`
8. **Firewall Audit Phase 2 (auto-remediation)** — review audit signal accuracy

### Useful commands for next session

```bash
# Verify CI status
gh run list --workflow=deploy.yml --limit 5

# Run full local lint pipeline
python3 -m compileall -q telegram-bot langgraph-agent
python3 -m ruff check --select=F401 telegram-bot langgraph-agent tests
# AST orphan-ref checks live in deploy.yml inline (extract heredoc if needed)

# Run tests with coverage
python3 -m pytest -v
# Reads pytest.ini, generates coverage.xml + term report

# View latest coverage delta
gh run view --log --job=<test_job_id> | grep -A 30 "Coverage summary"

# Tail bot logs (requires SSH to VPS)
ssh prosec "docker logs telegram-bot --tail 100 -f"

# Trigger DNS + SSL via Telegram
/ssl add domain1.com
/dns                    # auto-uses SSL list
```

### Lessons from this session (institutional memory)

1. **Stack 3 micro-PRs > 1 mega-PR** — Node 24 + pytest-cov + ruff F401 shipped sequentially in <1 jam total. Each PR independently verifiable via CI run, easy to revert.

2. **Coverage baseline first, threshold later** — measuring without enforcing creates buy-in for Test Coverage Agent. Threshold without baseline = arbitrary number. Baseline = 12.8% gives concrete starting point.

3. **textwrap.dedent dies on mixed indentation** — markdown tables generated with f-string + leading whitespace need explicit `\n.join` of pre-built parts. Faster + clearer than wrestling with dedent edge cases.

4. **Ruff F401 = high signal, zero noise** — current codebase had 4 violations, all true positives. F401 alone catches the most common dead-code accumulator without false positives from other F-class rules (`F811`, `F841`).

5. **`FORCE_JAVASCRIPT_ACTIONS_TO_NODE24` opt-in is cleaner than version bumps** — single env line vs N action version bumps. Annotation still appears (warning becomes informational), but Node 24 actually runs.

### Recently Completed

- ✅ [2026-05-31 05:20 UTC] **Ruff F401 gate + cleanup** — 4 unused imports removed, gate active in lint job
- ✅ [2026-05-31 05:15 UTC] **Coverage baseline** — pytest-cov + GITHUB_STEP_SUMMARY breakdown, 12.8% baseline
- ✅ [2026-05-31 05:08 UTC] **Node 24 migration** — `FORCE_JAVASCRIPT_ACTIONS_TO_NODE24=true` opt-in
- ✅ [2026-05-31 05:00 UTC] **CI lint gate extended to langgraph-agent main.py** — cross-module orphan-ref, smoke-tested live (run 26703689068 caught typo, run 26703708905 restored green)
- ✅ [2026-05-30 23:45 UTC] **CI pytest suite shipped** — 71 unit tests across 2 modules, deploy `needs: [lint, test]`

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
