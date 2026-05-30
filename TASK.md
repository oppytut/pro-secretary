# 🎯 TASK HANDOFF

**Last Updated:** 2026-05-30 00:21 UTC  
**Project:** AI Personal Secretary Stack  
**Status:** ✅ 7 features shipped + deployed: Morning Brief, Auto-Responder, Drift Detector, SSL Watchdog, Dynamic Config, Capacity Planning, Auto PR Review (GitHub + GitLab).

> Full history (2562 lines, sessions 2026-05-08 → 2026-05-24) archived in [`TASK_ARCHIVE.md`](TASK_ARCHIVE.md).

---

## 🤝 FOR NEXT SESSION (read this first)

**Where we left off:** Sesi 2026-05-30 — hardened Auto PR Review + deploy.yml secrets audit.

### What happened (this session)

1. **Auto PR Review hardening** — 4 fixes:
   - `parse_mode=HTML` for Telegram notifications (was showing raw `<b>` tags)
   - Whitelist sync error handling (log + notify user instead of silent `pass`)
   - Diff truncation notice appended to review body when >12K chars
   - Single retry with 2s backoff on diff fetch failure (skip on 403/404/422)
2. **Webhook setup helper** — `/review add` now replies with `gh`/`glab` CLI command to create webhook + link to manual settings page. Requires `AGENT_HOST` env.
3. **deploy.yml secrets audit & fix** — added `AGENT_HOST`, `GH_WEBHOOK_SECRET`, `GITLAB_WEBHOOK_SECRET` to CI deploy pipeline. Removed deprecated `OPENFANG_SECRET`.
4. **`.env.example` updated** — documented `GITLAB_PAT` scope (`api`), `GH_PAT` PR write permission, webhook secret descriptions.

### Key decisions

- **Webhook setup helper (Option A)** over auto-create webhook — avoids PAT scope escalation (`admin:repo_hook`). Bot generates CLI snippet instead.
- **`parse_mode` default None** (not HTML) — backward compat for plain-text callers (resource alerts, notify, journal). HTML callers pass explicitly.
- **Retry only on transient failures** — 403/404/422 are permanent, no retry. 5xx/network errors get 1 retry with 2s backoff.

### Session files changed

- `langgraph-agent/app/telegram.py` — added `parse_mode` parameter
- `langgraph-agent/app/pr_review.py` — parse_mode=HTML, truncation notice, retry logic
- `langgraph-agent/app/gitlab_review.py` — parse_mode=HTML, retry logic
- `telegram-bot/bot.py` — webhook setup helper, sync error handling, AGENT_HOST/secrets env
- `docker-compose.yml` — AGENT_HOST + webhook secrets for bot container
- `.env.example` — PAT scope docs, webhook secret descriptions
- `.github/workflows/deploy.yml` — 3 new secrets, removed OPENFANG_SECRET

### New env vars added to bot container

| Var | Default | Purpose |
|---|---|---|
| `AGENT_HOST` | (empty) | Public hostname for webhook URL in setup hints |
| `GH_WEBHOOK_SECRET` | (empty) | Passed to bot for secret prefix display in hints |
| `GITLAB_WEBHOOK_SECRET` | (empty) | Passed to bot for token prefix display in hints |

### GitHub Secrets audit result

**Added by user (this session):**
- `AGENT_HOST` — domain pointing to VPS for webhook endpoint
- `GH_WEBHOOK_SECRET` — HMAC secret for GitHub webhook verification
- `GITLAB_WEBHOOK_SECRET` — token for GitLab webhook verification

**Still missing (non-blocking):**
- `DOMAIN` — base domain (deploy script has fallback)
- `CALCOM_API_KEY` — needed for Cal.com API calls (from Cal.com dashboard)
- `N8N_USER` / `N8N_PASSWORD` — deploy uses defaults `admin`/`changeme`

### Deferred (wait 1-2 minggu data)

- Grafana (tunggu actual trend visualization need)
- Embedding model upgrade / Hybrid search BM25
- Skills Phase 2C (executable skills)
- py3.14 migration (wait wheels)
- `/repo add/del/list` — dynamic project management via Telegram

### Next session focus (PRIORITY ORDER)

1. **Dogfood Auto PR Review** — configure webhook on a real repo, test with real PR. Verify:
   - Webhook arrives → review posted → Telegram notified
   - `/review owner/repo#123` on-demand works
   - Truncation notice appears on large PRs
2. **Dogfood other 6 features** (passive, ongoing):
   - `/briefing` — is the morning brief informative enough?
   - Auto-fix — any false positives?
   - `/drift` — noisy or useful?
   - `/ssl add` + `/monitor add` — test dynamic config
   - `/capacity` — needs 7d Prometheus history for meaningful predictions
3. **Onboard remaining 8-13 VPS to Prometheus** (high priority, monitoring scope completion):
   - Butuh dari user: list IP/hostname + provider + SSH access.
   - `/monitor add <name> <host> <port> <user>` via Telegram.
4. **Next roadmap items** (AI-suitable, recommended order):
   - Meeting Notes → Action Items (0.5 hari) — quick win, all building blocks exist
   - Dependency Watchdog (1-2 hari) — fully automatable, no user judgment needed
   - Spec-to-Implementation (2-3 hari) — highest leverage multiplier

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
