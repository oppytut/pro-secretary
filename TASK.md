# 🎯 TASK HANDOFF

**Last Updated:** 2026-05-25 08:40 UTC  
**Project:** AI Personal Secretary Stack  
**Status:** ✅ Monitoring MVP shipped. Q&A retrieval pipeline improved (D1/D3/D4 resolved). Skills/voice/Q&A in dogfood phase. erpstg healthcheck fixed.

> Full history (2562 lines, sessions 2026-05-08 → 2026-05-24) archived in [`TASK_ARCHIVE.md`](TASK_ARCHIVE.md).

---

## 🤝 FOR NEXT SESSION (read this first)

**Where we left off:** Sesi 2026-05-25 — 2 tracks ter-deliver:

1. **Investigate erpstg unhealthy (priority #0):** Resolved with 2 commits ke `gmd/erp-deployment/erp-l11` (`stg`). Surfaced latent app-level bug (Inspector APM 4.19 incompatible Laravel 12 view engine) — flagged untuk dev team, workaround active.
2. **Audit Q&A retrieval partial-miss patterns (D1/D3/D4):** 2 commits ke pro-secretary main. **All 3 dogfood partial-misses resolved** without embedding upgrade.

Container monitoring (#2) decision **reinforced defer** — failure mode di erpstg = config drift, not runtime issue.

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

1. **Onboard remaining 8-13 VPS to Prometheus** (high priority, monitoring scope completion):
   - User punya 10-15 VPS total. Saat ini ter-scrape: `pro-secretary` + `erpstg`.
   - **STANDARD: port 19100, bukan 9100.** See "Why port 19100" in KEY KNOWLEDGE #11.
   - Per-VPS: install `prometheus-node-exporter`, UFW allow pro-secretary IP only, append target.
   - Butuh dari user: list IP/hostname + provider + SSH access.

2. **Container monitoring (cAdvisor) — DEFERRED:**
   - Decision reinforced 2026-05-25: real failure mode = config drift, not runtime.
   - Wait for real container runtime failure (OOMKilled, RestartLoop) sebelum invest.

3. **Tune alert thresholds** setelah 3-5 hari data (data-driven, bukan tebakan).

4. **DOGFOOD existing features** (1-2 minggu, passive):
   - Pakai bot daily — voice, Q&A, skills
   - Track: inline button noise, retrieval miss rate, alert noise

5. **Adjustments (hanya jika data menunjukkan):**
   - Inline button terlalu sering → naikkan threshold
   - Retrieval miss > 30% → evaluate code-aware embedding
   - Skills Phase 2B (LLM summarization for auto-logged skill names)

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
- [ ] **PRIORITY: Onboard remaining 8-13 VPS to Prometheus** — needs list from user (IP, provider, SSH access)
- [ ] **DEFERRED: Container monitoring (cAdvisor)** — reinforced defer 2026-05-25
- [ ] **DOGFOOD: Q&A + voice + skills** — passive 1-2 minggu
- [ ] **DECISION POINT: Personal Journal** — wait 1 minggu regular usage data
- [ ] **DEFERRED: Grafana** — wait actual trend visualization need
- [ ] **DEFERRED: py3.14** — wait py-rust-stemmers wheels
- [ ] **MONITOR: Inspector APM bug** — workaround active, dev team scope

### Blocked/Waiting
- VPS list from user (blocks Prometheus onboarding)

### Recently Completed

- ✅ [2026-05-25 08:00 UTC] Q&A retrieval audit — D1/D3/D4 all resolved
  - 2 commits: `5bdf3c8` (ID→EN map, plurals, path priority expansion) + `999f0a7` (exact create_<entity>_table rank -3)
  - Production verified: `create_materials_table.php` ranks #0, Facade/Traits/Scopes prioritized
  - User dogfood confirmed: bot now retrieves correct migration + articulates columns

- ✅ [2026-05-25 04:30 UTC] Investigate erpstg unhealthy — resolved
  - 2 commits to `gmd/erp-deployment/erp-l11` stg: `34aa240` + `cbb00a8`
  - Root cause: healthcheck config drift (`/status` 404) + latent Inspector APM bug (`/up` 500 on fresh cache)
  - Final state: `erp-stg-app-1` `Up (healthy)` FailingStreak 0

- ✅ [2026-05-24 09:00 UTC] Onboard erpstg to Prometheus — deployed
  - node_exporter `:19100`, UFW restricted, CI force-recreate pattern adopted
  - Discovered ISP transit drop on `:9100` → standard port 19100

- ✅ [2026-05-24 06:00 UTC] Monitoring MVP — Prometheus + Alertmanager + `/monitor` shipped
  - 10 alert rules, Telegram receiver, bot `/monitor` command

- ✅ [2026-05-24 00:17 UTC] Self-improving Skills Phase 1 — deployed
  - `/skill log <name> | <desc>` to save, `/skill <query>` to recall

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
