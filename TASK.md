# 🎯 TASK HANDOFF

**Last Updated:** 2026-05-28 15:08 UTC  
**Project:** AI Personal Secretary Stack  
**Status:** ✅ 7 features shipped: Morning Brief, Auto-Responder, Drift Detector, SSL Watchdog, Dynamic Config, Capacity Planning, Auto PR Review (GitHub + GitLab).

> Full history (2562 lines, sessions 2026-05-08 → 2026-05-24) archived in [`TASK_ARCHIVE.md`](TASK_ARCHIVE.md).

---

## 🤝 FOR NEXT SESSION (read this first)

**Where we left off:** Sesi 2026-05-28 — shipped 7 AI Agent 24/7 features from roadmap.

### What happened (this session)

1. **Morning Standup Brief** — daily 07:00 WIB aggregated message (schedule+tasks from agent, VPS status+alerts from Prometheus, open PRs+commits+CI from GitHub API). `/briefing` on-demand.
2. **Incident Auto-Responder** — extends health check with auto-restart containers (skips restart loops) + auto-prune disk >90%. Verification re-check after each fix. Telegram audit trail.
3. **Config Drift Detector** — daily 02:00 WIB check: running images vs docker-compose.yml, container set, cron entries, remote VPS liveness. `/drift` on-demand.
4. **SSL/Domain Watchdog** — daily 02:05 WIB cert expiry check. Alert 30 days before. `/ssl` on-demand.
5. **Dynamic Config via Telegram** — `/ssl add/del/list` + `/monitor add/del/list`. JSON config store persisted in `bot_data` volume. Env vars as seed/fallback.
6. **Capacity Planning** — daily 02:10 WIB predict_linear forecast for disk and RAM exhaustion (7d lookback, 14d horizon). `/capacity` on-demand. Silent when OK, alerts when predicted exhaustion within CAPACITY_WARN_DAYS.
7. **Auto PR Review** — GitHub webhook → LangGraph agent fetches diff → LLM analyzes (bugs, security, performance) → posts review on PR (APPROVE/COMMENT/REQUEST_CHANGES) → Telegram notification.

### Key decisions

- **Bot-side aggregation** for morning brief (not agent) — bot already has Prometheus + SSH access.
- **JSON file config store** (not Qdrant) — simpler for key-value config, no agent dependency.
- **Docker CLI static binary** added to bot container for local drift check (socket mounted ro).
- **Env vars remain as seed** — dynamic config takes precedence but env is fallback.
- **Silent notifications** — drift/SSL only alert when issues found, not when clean.

### Session files changed

- `telegram-bot/bot.py` — capacity planning + /review command with config store
- `langgraph-agent/app/main.py` — GitHub/GitLab webhook endpoints + /api/review_pr + /api/review/repos
- `langgraph-agent/app/pr_review.py` — NEW: PR diff fetch, LLM analysis, review posting, whitelist
- `langgraph-agent/app/gitlab_review.py` — NEW: GitLab MR diff fetch, comment posting
- `langgraph-agent/app/config.py` — added GH_WEBHOOK_SECRET, GITLAB_WEBHOOK_SECRET
- `docker-compose.yml` — capacity + webhook env vars
- `caddy/Caddyfile` — agent webhook routes (GitHub + GitLab)
- `.env.example` — GH_WEBHOOK_SECRET, GITLAB_WEBHOOK_SECRET, AGENT_HOST

### New env vars (all have defaults, optional)

| Var | Default | Purpose |
|---|---|---|
| `GH_PAT` | (empty) | GitHub API for morning brief |
| `MORNING_BRIEF_ENABLED` | true | Enable/disable morning brief |
| `MORNING_BRIEF_HOUR` | 7 | Hour (WIB) |
| `MORNING_BRIEF_MINUTE` | 0 | Minute |
| `AUTO_FIX_ENABLED` | true | Enable/disable auto-fix |
| `DISK_AUTOFIX_THRESHOLD_PCT` | 90 | Disk % trigger for prune |
| `DRIFT_CHECK_ENABLED` | true | Enable/disable drift check |
| `DRIFT_CHECK_HOUR` | 2 | Hour (WIB) |
| `DRIFT_CHECK_MINUTE` | 0 | Minute |
| `SSL_CHECK_ENABLED` | true | Enable/disable SSL check |
| `SSL_CHECK_DOMAINS` | (empty) | Comma-separated seed domains |
| `SSL_WARN_DAYS` | 30 | Days before expiry to warn |

| `CAPACITY_CHECK_ENABLED` | true | Enable/disable capacity forecast |
| `CAPACITY_CHECK_HOUR` | 2 | Hour (WIB) |
| `CAPACITY_CHECK_MINUTE` | 10 | Minute |
| `CAPACITY_WARN_DAYS` | 14 | Days ahead to predict exhaustion |
| `GH_WEBHOOK_SECRET` | (empty) | GitHub webhook HMAC secret for PR review |
| `GITLAB_WEBHOOK_SECRET` | (empty) | GitLab webhook token for MR review |
| `AGENT_HOST` | agent.localhost | Public hostname for agent webhook endpoint |

### New commands

| Command | Purpose |
|---|---|
| `/briefing` | Full morning brief on-demand |
| `/drift` | Config drift check on-demand |
| `/ssl` | SSL cert check on-demand |
| `/ssl add/del/list` | Manage SSL watchlist via Telegram |
| `/monitor add/del/list` | Manage VPS targets via Telegram |
| `/capacity` | Disk/RAM exhaustion forecast on-demand |
| `/review add/del/list` | Manage auto-review repo whitelist |
| `/review owner/repo#123` | On-demand PR/MR review |

### Session deliverables (5 commits across 2 repos)

| # | Commit | Repo | Outcome |
|---|---|---|---|
| 1 | `34aa240 fix(healthcheck): use /up endpoint` | erp-l11 stg | First fix — surfaced Inspector APM bug |
| 2 | `cbb00a8 fix(healthcheck): probe / instead of /up` | erp-l11 stg | Final healthcheck fix — `Up (healthy)` |
| 3 | `da39cfd docs: TASK.md handoff erpstg resolved` | pro-secretary main | Investigation context |
| 4 | `5bdf3c8 fix(agent): improve Q&A path-term extraction` | pro-secretary main | _ID_TO_EN map, y→ies plurals, Facade/Traits priority |
| 5 | `999f0a7 fix(agent): prioritize exact create_<entity>_table` | pro-secretary main | Distinguish main entity migration from related-entity |

### Q&A retrieval — dogfood verdict (3/3 resolved)

| Case | Original verdict | After session | Citation source |
|---|---|---|---|
| D1: tabel material kolom | ⚠️ PARTIAL — main migration miss | ✅ FULL — 6 columns + types + FK | `create_materials_table.php:1-30` |
| D3: alur transaksi receipt stok | ⚠️ PARTIAL — POS confusion | ✅ FULL — material_transactions flow | `create_material_transactions_table.php:1-41` |
| D4: scope business_id di inventory | ⚠️ PARTIAL — interface only | ✅ FULL — Facade impl + middleware | `app/Facades/Inventory/Inventory.php:1-140` |

### Q&A retrieval changes (technical detail for next agent)

1. **`_ID_TO_EN` Indonesian→English entity mapping (24 mappings):** `stok→stock`, `transaksi→transaction`, `pegawai→employee`, etc. Both forms searched in path retrieval.
2. **`_pluralize_variants` proper English morphology:** `y→ies` (inventory→inventories), `ies→y` (reverse), `ss` exception, default add/strip s.
3. **`_PATH_PRIORITY` expanded:** +Services/, Repositories/, Facades/, Traits/, Concerns/, Scopes/, Providers/ (covers dokfin Facade pattern).
4. **Exact `create_<entity>_table` priority (rank -3):** Distinguishes main entity migration from related-entity migrations (stocks, issues, units, etc.).
5. **`_PATH_IRRELEVANT` expanded:** +`saja`, `siapa`, `scope`, `relasi`, `relation`, `harus`.

### Inspector APM bug (erpstg, dev team scope)

- `inspector-apm/inspector-laravel: ^4.19` incompatible with Laravel 12 view engine
- `/up` returns 500 on fresh view cache: `Property Inspector\Laravel\Views\ViewEngineDecorator::$lastCompiled does not exist`
- Workaround active: healthcheck pakai `/` (homepage)
- **Permanent fix options for dev team:**
  - (a) Upgrade Inspector APM to Laravel 12 compatible version
  - (b) Remove from composer.json (config currently `inspector=off`)
  - (c) Conditionally register service provider only when `INSPECTOR_ENABLE=true`

### Next session focus (PRIORITY ORDER)

1. **Dogfood 5 new features** (3-5 hari, passive):
   - `/briefing` — is the morning brief informative enough?
   - Auto-fix — any false positives?
   - `/drift` — noisy or useful?
   - `/ssl add` + `/monitor add` — test dynamic config
   - Tune if needed

2. **Onboard remaining 8-13 VPS to Prometheus** (high priority, monitoring scope completion):
   - User punya 10-15 VPS total. Saat ini ter-scrape: `pro-secretary` + `erpstg`.
   - **STANDARD: port 19100, bukan 9100.** See "Why port 19100" in KEY KNOWLEDGE #11.
   - Per-VPS: install `prometheus-node-exporter`, UFW allow pro-secretary IP only, append target.
   - Butuh dari user: list IP/hostname + provider + SSH access.
   - **NEW:** Bisa juga `/monitor add <name> <host> <port> <user>` via Telegram.
3. **`/repo add/del/list`** — dynamic project management via Telegram (needs agent endpoint for re-indexing).

6. **Jangan lakukan sebelum 1-2 minggu data:**
   - Grafana (tunggu actual trend visualization need)
   - Embedding model upgrade
   - Hybrid search BM25
   - Skills Phase 2C (executable skills)
   - py3.14 migration (wait wheels)

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
- [ ] **Onboard remaining 8-13 VPS to Prometheus** — needs list from user (IP, provider, SSH access)
- [ ] **DOGFOOD: Q&A + voice + skills + /monitor + /menu + /briefing** — passive 1-2 minggu
- [ ] **DECISION POINT: Pick next roadmap items** — user decides from `AI_AGENT_ROADMAP.md`
- [ ] **DEFERRED: Grafana** — wait actual trend visualization need
- [ ] **DEFERRED: py3.14** — wait py-rust-stemmers wheels

### Blocked/Waiting
- VPS list from user (blocks Prometheus onboarding)

### Recently Completed

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
