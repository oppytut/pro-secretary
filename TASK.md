# 🎯 TASK HANDOFF

**Last Updated:** 2026-05-30 10:50 UTC
**Project:** AI Personal Secretary Stack
**Status:** ✅ 10 features shipped + 1 silent-failure bug fixed (Auto PR/MR Review surfaces post failures): Morning Brief, Auto-Responder, Drift Detector, SSL Watchdog, Dynamic Config, Capacity Planning, Auto PR Review (GitHub + GitLab), Meeting Notes → Action Items, Dependency Watchdog, Documentation Sync.

> Full history (2562 lines, sessions 2026-05-08 → 2026-05-24) archived in [`TASK_ARCHIVE.md`](TASK_ARCHIVE.md).

---

## 🤝 FOR NEXT SESSION (read this first)

**Where we left off:** Sesi 2026-05-30 — shipped 4 items autonom: Meeting Notes, Dependency Watchdog Phase 1, README/DEPLOYMENT cleanup, Documentation Sync Phase 1.

### What happened (this session, in order)

1. **Meeting Notes → Action Items** — 0.5 hari quick win
   - `langgraph-agent/app/meeting_notes.py` NEW (~200 lines): extraction prompt + parser + auto-task creation
   - `/api/meeting_notes` endpoint (rate-limited 6/min, max 20K chars)
   - `/meeting <transkrip>` command + reply-mode + voice auto-route (≥500 chars OR ≥2 keywords)
   - Reuses Whisper + `tools.create_task()` — zero new deps, zero new env vars

2. **Dependency Watchdog Phase 1** — 1 hari, detection-only
   - `langgraph-agent/app/deps_watchdog.py` NEW (~340 lines): 6 parsers (npm, PyPI, Packagist, Go) + OSV.dev client + report formatter
   - `/api/deps/scan` endpoint (rate-limited 4/min)
   - `/deps [repo_id]` command + daily scheduler 03:00 WIB (silent on clean)
   - OSV.dev integration verified: lodash@4.17.20 → 5 real CVEs (HIGH/MODERATE)
   - **Phase 2 (auto-PR) deferred** until dogfood data validates noise level

3. **README + DEPLOYMENT_LOW_RESOURCE cleanup** — 0.5 hari
   - Removed stale OpenFang banner claiming sections that don't exist
   - Replaced outdated bullet Roadmap with 15-feature shipped table + Horizon section
   - Fixed inconsistent container counts (5 → 7) in 2 places
   - Added Prometheus/Alertmanager rows to Hardware breakdown
   - Cleaned all internal `openfang` refs in DEPLOYMENT_LOW_RESOURCE
   - Verified: zero `openfang|OpenFang` matches in active docs (TASK_ARCHIVE retains historical)

4. **Documentation Sync Phase 1** — 1 hari, detection-only
   - `langgraph-agent/app/docs_sync.py` NEW (~250 lines): diff classifier + LLM analyzer + Telegram formatter
   - Pre-classifies diff via regex: API changes, env vars, command handlers, doc files
   - LLM output: VERDICT (NEEDS_DOCS / NO_DOCS_NEEDED) + AFFECTED_AREAS + SUGGESTIONS + SUMMARY
   - `/api/docs/suggest` endpoint (rate-limited 6/min)
   - `/docsync owner/repo#123` (GitHub) or `/docsync gitlab:project_id!iid` (GitLab)
   - Reuses `pr_review.fetch_pr_diff()` and `gitlab_review.fetch_mr_diff()`

### Bug fixed mid-session

- ⚠️ **Bot.py orphan-references** — Earlier deps watchdog code injection had silent oldString mismatch. Bot referenced `cmd_deps`, `_deps_check_job`, `_run_deps_check` without defining them → would NameError on startup. Fixed by injecting full Dependency Watchdog block before "Config Drift Detector" section.
- **Lesson:** `py_compile` catches syntax but NOT undefined module-level references. After multi-step edits, also run AST check: `python3 -c "import ast; ast.parse(open('file.py').read())"` then verify required functions exist.

### Key decisions

- **All Phase 1 detection-only, no auto-PR yet** — risk of N repos × M issues = PR spam. Dogfood first.
- **Reuse existing infra everywhere** — Whisper, `tools.create_task()`, `code_repos._sync_repo()`, `pr_review.fetch_pr_diff()`. Zero new dependencies, zero new env vars.
- **Silent on clean (matches capacity/SSL pattern)** — only notify when issues found
- **OSV.dev over Snyk/GitHub Advisory** — free, no API key, comprehensive coverage
- **Lockfile preferred over manifest for npm** — drops `package.json` if `package-lock.json` exists (avoids version-range guesswork)
- **Severity enrichment limited to 30 vulns/scan** — avoid OSV detail-endpoint rate limit

### Files changed this session

**NEW modules:**
- `langgraph-agent/app/meeting_notes.py` (~200 lines)
- `langgraph-agent/app/deps_watchdog.py` (~340 lines)
- `langgraph-agent/app/docs_sync.py` (~250 lines)

**Modified:**
- `langgraph-agent/app/main.py` — 3 imports + 3 request models + 3 endpoints (`/api/meeting_notes`, `/api/deps/scan`, `/api/docs/suggest`)
- `telegram-bot/bot.py` — `cmd_meeting`, `cmd_deps`, `cmd_docsync` + `_run_deps_check`, `_deps_check_job`, `_looks_like_meeting`, `_process_meeting_transcript` + voice routing + scheduler block + 3 BotCommand entries + menu/help text
- `README.md` — Status banner, AI Agent Engine section, Roadmap (table + Horizon), Hardware breakdown, container counts
- `DEPLOYMENT_LOW_RESOURCE.md` — Banner refocused, openfang refs replaced (mkdir, restart, resource table)
- `AI_AGENT_ROADMAP.md` — Tier 1.3 + 3.3 + 3.4 marked done, Shipped Features table updated
- `TASK.md` — this update

### Verification done

- ✅ Syntax (`py_compile`) clean on all changed files
- ✅ AST verification: all required functions present (after orphan-ref bug)
- ✅ LSP diagnostics: no new errors (only pre-existing slowapi/Telegram Optional warnings)
- ✅ Meeting parser smoke test: 5 action items + edge cases (empty sections, malformed priority, bare title)
- ✅ Deps parsers smoke test: npm/pip/composer/go.mod with synthetic manifests
- ✅ OSV.dev integration test: lodash@4.17.20 returned 5 real CVEs with severity
- ✅ Docs_sync diff parser + classifier + LLM response parser tested with multi-file diff

### NOT verified (need real-world dogfood)

- ⚠️ `/meeting` accuracy on actual voice rapat (heuristic false-positive on long monologue?)
- ⚠️ `/deps` real repo timing (gmedia-erp, dokfin-backend) — could OSV batch take >300s?
- ⚠️ `/docsync` LLM output quality on real PRs
- ⚠️ Daily schedulers fire correctly at 03:00 WIB

### Deferred (wait dogfood data)

- **Auto-PR for deps** (Phase 2) — after Phase 1 validates noise level
- **Auto-PR with doc updates** (docs_sync Phase 2) — same reason
- Grafana (tunggu actual trend visualization need)
- Embedding model upgrade / Hybrid search BM25
- Skills Phase 2C (executable skills)
- py3.14 migration (wait wheels)
- `/repo add/del/list` — dynamic project management via Telegram

### Next session focus (PRIORITY ORDER)

1. **Dogfood the 4 new features** — passive ongoing, real workload signal
   - `/meeting` — test voice rapat real
   - `/deps` — run on `gmedia-erp` + `dokfin-backend`, verify scheduler
   - `/docsync` — test on actual PR
   - Auto PR Review (still open from previous session) — webhook on real repo
2. **Onboard remaining 8-13 VPS to Prometheus** (high priority, monitoring scope completion)
   - Butuh dari user: list IP/hostname + provider + SSH access
   - `/monitor add <name> <host> <port> <user>` via Telegram
3. **Next roadmap items** (AI-suitable, recommended order):
   - **Firewall Audit Agent** (1 hari) — nightly UFW scan via SSH, alert-only, read-only by default
   - **Docker Image Hygiene** (0.5 hari) — track image size growth, prune dangling only
   - **DNS Health Monitor** (0.5 hari) — hourly multi-resolver dig, alert anomaly
   - **Spec-to-Implementation** (2-3 hari) — needs real spec from user
   - **Deps Watchdog Phase 2: auto-PR** (1 hari) — after dogfood Phase 1
   - **Docs Sync Phase 2: auto-PR** (1 hari) — after dogfood Phase 1

### Critical patterns (read before onboarding next VPS)

**Port 19100, NOT 9100:** ISP-level filter on well-known Prometheus port discovered onboarding erpstg (Biznet → DO Singapore). Use `:19100` for ALL future VPS.

**`--force-recreate prometheus alertmanager` di CI deploy:** Bind-mount Docker pins to inode at container start. `git pull` rewrites config → new inode → running container serves stale. Fix: force-recreate after `up -d --remove-orphans`.

**Adding a new VPS target:**
1. Install `prometheus-node-exporter`, override listen to `:19100`, enable+start
2. Firewall: allow 19100 only from pro-secretary IP (`159.223.40.74`)
3. Append target to `prometheus/prometheus.yml`
4. Push → CI auto-deploys with force-recreate

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

## 🚧 CURRENT WORK

### Active Tasks
- [ ] **DOGFOOD 4 new features** — `/meeting`, `/deps`, `/docsync`, plus existing Auto PR Review on real workload (passive 1-2 minggu)
- [ ] **Onboard remaining 8-13 VPS to Prometheus** — needs list from user (IP, provider, SSH access)
- [ ] **DECISION POINT: Pick next roadmap items** — user decides from `AI_AGENT_ROADMAP.md`
- [ ] **DEFERRED: Deps Watchdog Phase 2 (auto-PR)** — wait Phase 1 dogfood data
- [ ] **DEFERRED: Docs Sync Phase 2 (auto-PR)** — wait Phase 1 dogfood data
- [ ] **DEFERRED: Grafana** — wait actual trend visualization need
- [ ] **DEFERRED: py3.14** — wait py-rust-stemmers wheels

### Blocked/Waiting
- VPS list from user (blocks Prometheus onboarding)
- Real PR/MR + voice rapat for Phase 1 dogfood validation

### Recently Completed

- ✅ [2026-05-30 10:50 UTC] Auto PR/MR Review silent-failure fixed
  - **Bug:** Bot mengirim Telegram notif "Verdict: COMMENT" + summary, tapi review TIDAK pernah muncul di GitHub/GitLab. User report: oppytut/jeevatix#10/11/12 dapat Telegram tapi PR comment kosong.
  - **Root cause:** `post_review()` / `post_mr_comment()` returns `None` on HTTP error (logged but swallowed). Caller IGNORE failure dan tetap kirim Telegram dengan summary seolah berhasil.
  - **Fix:** `post_review()` / `post_mr_comment()` sekarang return `{"ok": bool, "status": int, "data": dict, "error": str}`. Telegram message includes ✅/⚠️ post status + HTTP code + error snippet kalau gagal.
  - Files: `langgraph-agent/app/pr_review.py` (handle_pr_event, review_pr_on_demand, post_review), `langgraph-agent/app/gitlab_review.py` (handle_mr_event, review_mr_on_demand, post_mr_comment)
  - **Diagnostic next time:** kalau Telegram say `⚠️ NOT posted (HTTP 403)`, cek PAT scope (`pull_requests: write` for fine-grained) atau collaborator access ke repo.

- ✅ [2026-05-30 10:40 UTC] TASK.md handoff cleanup
  - `langgraph-agent/app/docs_sync.py` (~250 lines) — diff classifier + LLM analyzer + Telegram formatter
  - Pre-classifies diff with regex: API changes, env vars, command handlers, doc files
  - LLM analyzer: VERDICT (NEEDS_DOCS / NO_DOCS_NEEDED) + AFFECTED_AREAS + SUGGESTIONS + SUMMARY
  - Endpoint `/api/docs/suggest` (rate-limited 6/min)
  - `/docsync owner/repo#123` (GitHub) or `/docsync gitlab:project_id!iid` (GitLab)
  - Reuses `pr_review.fetch_pr_diff()` and `gitlab_review.fetch_mr_diff()`
  - Smoke tests passed: diff parser + classifier + LLM response parser + edge cases
  - Phase 2 (auto-PR with doc updates) deferred until dogfood

- ✅ [2026-05-30 10:32 UTC] Bot.py orphan-references bug fixed
  - Earlier deps watchdog code injection had silent oldString mismatch
  - Bot.py referenced `cmd_deps`, `_deps_check_job`, `_run_deps_check` without defining them — would NameError on startup
  - Fixed by injecting full Dependency Watchdog block + cmd_docsync before "Config Drift Detector" section
  - Verified via AST: all required functions present

- ✅ [2026-05-30 10:20 UTC] README + DEPLOYMENT_LOW_RESOURCE cleanup
  - README banner — removed stale "OpenFang vs LangGraph" reference (no such section exists)
  - README Roadmap section — replaced outdated bullet list with shipped table + Horizon section
  - README "AI Agent Engine" — cleaned defensive justification, focused on LangGraph rationale
  - README Quick Start — fixed inconsistent container count (5 → 7)
  - README Hardware Requirements — fixed container count + added Prometheus/Alertmanager rows
  - DEPLOYMENT_LOW_RESOURCE banner — refocused warning on CI-driven deploy
  - DEPLOYMENT_LOW_RESOURCE — removed all internal `openfang` references
  - Verified: zero `openfang|OpenFang` matches in active docs

- ✅ [2026-05-30 10:13 UTC] Dependency Watchdog Phase 1 shipped
  - `langgraph-agent/app/deps_watchdog.py` (~340 lines) — multi-ecosystem scanner
  - Parsers: npm (`package.json` + `package-lock.json` v1/v2/v3), PyPI (`requirements.txt` + `pyproject.toml`), Packagist (`composer.lock`), Go (`go.mod`)
  - OSV.dev integration — batch query, severity enrichment, free no API key
  - Endpoint `/api/deps/scan` (rate-limited 4/min)
  - `/deps [repo_id]` command + daily scheduler at 03:00 WIB (silent on clean)
  - Reuses `code_repos._sync_repo()` for git clone with PAT auth
  - Smoke tests passed: parsers + OSV (lodash@4.17.20 → 5 CVEs detected)
  - Phase 2 (auto-PR) deferred until dogfood data validates noise level

- ✅ [2026-05-30 09:58 UTC] Meeting Notes → Action Items shipped
  - New module `langgraph-agent/app/meeting_notes.py` (198 lines)
  - Endpoint `/api/meeting_notes` (rate-limited 6/min, 20K char transcript max)
  - `/meeting <transkrip>` command + reply-mode + voice auto-route (≥500 chars OR ≥2 keywords)
  - Output: action items (priority + owner + deadline), decisions, next steps, summary
  - Auto-creates tasks via existing `tools.create_task()` — reuse Whisper + task infra existing
  - Parser smoke-test passed: 5 action items + edge cases (empty sections, malformed priority, bare title)
  - Files: `meeting_notes.py` (new), `main.py`, `bot.py`, `AI_AGENT_ROADMAP.md`

- ✅ [2026-05-30 00:22 UTC] Auto PR Review hardening + deploy.yml audit
  - `parse_mode=HTML` fix for Telegram notifications
  - Whitelist sync error handling (log + notify instead of silent pass)
  - Diff truncation notice in review body when >12K chars
  - Single retry with 2s backoff on diff fetch failure
  - Webhook setup helper: `/review add` shows `gh`/`glab` CLI snippet
  - deploy.yml: added AGENT_HOST, GH_WEBHOOK_SECRET, GITLAB_WEBHOOK_SECRET
  - deploy.yml: removed deprecated OPENFANG_SECRET
  - `.env.example`: documented PAT scopes + webhook secrets

- ✅ [2026-05-28 14:36 UTC] Auto PR Review deployed
  - GitHub webhook → agent `/api/webhook/github` endpoint
  - GitLab webhook → agent `/api/webhook/gitlab` endpoint
  - Signature verification (HMAC SHA-256 for GitHub, token for GitLab)
  - Fetches PR/MR diff, LLM analyzes (bugs, security, performance, error handling)
  - GitHub: posts review (APPROVE/COMMENT/REQUEST_CHANGES)
  - GitLab: posts comment on MR
  - `/review add github:owner/repo` or `/review add gitlab:owner/repo` — manage whitelist via Telegram
  - `/review del`, `/review list` — remove/list monitored repos
  - `/review owner/repo#123` — on-demand review trigger
  - Whitelist synced from bot → agent on every add/del
  - Empty whitelist = review all (backward compat)
  - Telegram notification on every review posted
  - Caddy route exposes only webhook paths
  - New files: `langgraph-agent/app/pr_review.py`, `langgraph-agent/app/gitlab_review.py`
  - Env: `GH_WEBHOOK_SECRET`, `GITLAB_WEBHOOK_SECRET`, `AGENT_HOST`
  - Setup: configure repo webhook → `https://{AGENT_HOST}/api/webhook/github` or `/api/webhook/gitlab`

- ✅ [2026-05-28 14:24 UTC] Capacity Planning deployed
  - predict_linear forecast: disk + RAM exhaustion (7d lookback, 14d horizon)
  - Daily 02:10 WIB scheduled (silent when OK, alerts on predicted exhaustion)
  - `/capacity` command for on-demand forecast
  - Current usage snapshot included in report
  - Env: `CAPACITY_CHECK_ENABLED`, `CAPACITY_CHECK_HOUR`, `CAPACITY_CHECK_MINUTE`, `CAPACITY_WARN_DAYS`

- ✅ [2026-05-28 14:12 UTC] Dynamic Config via Telegram
  - `/ssl add/del/list` — manage SSL watchlist domains
  - `/monitor add/del/list` — manage VPS SSH targets
  - JSON config store persisted in `bot_data` volume
  - Env vars remain as seed/fallback, config store takes precedence
  - All existing code refactored to use dynamic config

- ✅ [2026-05-28 11:36 UTC] SSL/Domain Watchdog deployed
  - Check SSL cert expiry for all configured domains via TLS connection
  - Alert 30 days before expiry (configurable via `SSL_WARN_DAYS`)
  - Daily scheduled at 02:05 WIB (silent when OK, alerts on warnings)
  - `/ssl` command for on-demand check
  - Env: `SSL_CHECK_ENABLED`, `SSL_CHECK_DOMAINS`, `SSL_WARN_DAYS`
  - Requires: set `SSL_CHECK_DOMAINS=domain1.com,domain2.com` in `.env`

- ✅ [2026-05-28 10:56 UTC] Config Drift Detector deployed
  - Docker image version drift check (running vs expected from docker-compose.yml)
  - Container set check (missing/unexpected containers)
  - Cron entry verification (health_check, backup, sync_vault)
  - Remote VPS container liveness via SSH
  - Daily 02:00 WIB scheduled (silent when clean, alerts on drift)
  - `/drift` command for on-demand check
  - Docker CLI added to bot container (static binary + socket mount)
  - Env: `DRIFT_CHECK_ENABLED`, `DRIFT_CHECK_HOUR`, `DRIFT_CHECK_MINUTE`

- ✅ [2026-05-28 10:35 UTC] Incident Auto-Responder deployed
  - Auto-restart down/unhealthy containers via SSH (skips restart loops)
  - Auto-prune Docker when disk >90% (Prometheus-triggered)
  - Verification re-check after each fix (10s restart, 35s prune)
  - Separate Telegram audit message for all auto-fix actions
  - Env: `AUTO_FIX_ENABLED`, `DISK_AUTOFIX_THRESHOLD_PCT`

- ✅ [2026-05-28 08:56 UTC] Morning Standup Brief implemented
  - Bot-side aggregation: schedule+tasks (agent), VPS status+alerts (Prometheus), open PRs+commits+CI (GitHub API)
  - `run_daily` at 07:00 WIB via PTB JobQueue with `Asia/Jakarta` timezone
  - `/briefing` command now triggers full morning brief on-demand
  - Env vars: `GH_PAT`, `MORNING_BRIEF_ENABLED`, `MORNING_BRIEF_HOUR`, `MORNING_BRIEF_MINUTE`

- ✅ [2026-05-28 03:26 UTC] AI Agent 24/7 Roadmap documented
  - `AI_AGENT_ROADMAP.md` — 30+ features across 6 tiers with technical how-it-works

- ✅ [2026-05-28 02:45 UTC] `/menu` UX overhaul
  - Grouped inline keyboard buttons (6 categories)
  - Help button with full command reference
  - BotCommand list reduced to 6 most-used

- ✅ [2026-05-28 02:30 UTC] Restart loop detection + Alertmanager dedup
  - Track restart count in rolling window (3x in 15 min = alert)
  - Removed InstanceDown from Prometheus (bot covers it)

- ✅ [2026-05-28 02:10 UTC] Periodic health check verified end-to-end
  - Stop meilisearch → alert fired → restart → recovery alert fired
  - Both sendMessage returned 200 OK

- ✅ [2026-05-27 09:52 UTC] Container monitoring via SSH — deployed
  - SSH-based approach: bot SSH → docker ps. erpstg 3 containers visible.

- ✅ [2026-05-27 08:40 UTC] TASK.md condensed (2562→266 lines)

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
