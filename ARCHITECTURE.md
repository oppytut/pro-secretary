# Architecture

Quick reference for the telegram-bot + langgraph-agent package structure after the bot.py decomposition refactor (sesi 2026-05-31).

## Repository layout

```
pro-secretary/
├── telegram-bot/          # User-facing bot, schedulers, watchdogs
├── langgraph-agent/       # FastAPI agent (LLM, embeddings, journal, code review, test coverage)
├── caddy/                 # Reverse proxy
├── prometheus/            # Metrics
├── alertmanager/          # Alert routing
├── n8n/                   # Workflow automation
├── tests/                 # Unit tests for both bot + agent
├── scripts/               # CI helpers (lint_orphan_refs.py, install_n8n_workflows.sh)
├── docker-compose.yml
└── .github/workflows/deploy.yml
```

## telegram-bot package

```
telegram-bot/
├── bot.py                 # Orchestrator + handlers (handler-only code, hard-coupled to PTB)
├── infra/                 # Shared low-level primitives
│   ├── agent.py           # agent_post, agent_headers (HTTP client to langgraph-agent)
│   ├── auth.py            # ALLOWED_USERS env parsing + @authorized decorator
│   ├── config_store.py    # Persistent JSON config (CONFIG_DIR/CONFIG_FILE, config_get/set)
│   ├── gh.py              # gh_api (GitHub REST API client with GH_PAT)
│   ├── prom.py            # prom_query (Prometheus PromQL HTTP client)
│   └── ssh.py             # SSH targets registry + ssh_exec subprocess wrapper
└── watchdogs/             # Self-contained scheduled checks
    ├── capacity.py        # predict_linear forecasting (CAPACITY_*)
    ├── deps.py            # Deps vulnerability scanner (DEPS_*) → calls agent /api/deps/scan
    ├── dns.py             # Multi-resolver DNS consistency check (DNS_*)
    ├── drift.py           # Container/cron drift detector (DRIFT_*)
    ├── firewall.py        # Public port whitelist audit (FIREWALL_AUDIT_*)
    ├── hygiene.py         # Docker image hygiene (DOCKER_HYGIENE_*)
    ├── morning_brief.py   # Daily standup brief (MORNING_BRIEF_*)
    ├── ssl.py             # SSL cert expiry check (SSL_*)
    └── test_coverage.py   # Auto-PR test coverage agent (COVERAGE_AGENT_*)
```

## Module conventions

### `infra/` — shared primitives

- **No dependency on bot.py.** infra modules can be imported anywhere without circular import risk.
- **Public API uses no leading underscore** (`agent_post`, `prom_query`, `ssh_exec`, etc.).
- **bot.py re-exports with leading underscore** for back-compat with existing callsites:
  ```python
  from infra.ssh import ssh_exec as _ssh_exec
  from infra.prom import prom_query as _prom_query
  from infra.agent import agent_post as _agent_post
  from infra.gh import gh_api as _gh_api
  ```
- **Module-level state** (e.g. `ALLOWED_USERS`, `_env_targets`) is parsed from `os.environ` at import time. Tests use `importlib.reload(infra.X)` after `monkeypatch.setenv()` to re-parse with new env.
- **All `infra/*` modules pass mypy strict** and have 100% test coverage.

### `watchdogs/` — scheduled checks

Each watchdog module follows a uniform shape:

```python
# Module-level constants from env
WATCHDOG_CHECK_ENABLED = os.getenv(...)
WATCHDOG_CHECK_HOUR = int(os.getenv(...))
WATCHDOG_CHECK_MINUTE = int(os.getenv(...))

# Pure logic helpers (no I/O if possible)
async def run_watchdog_check() -> str: ...

# Scheduler entrypoint (called by JobQueue)
async def watchdog_check_job(context) -> None: ...

# Manual trigger (Telegram command handler)
@authorized
async def cmd_watchdog(update, context) -> None: ...
```

- Watchdogs depend only on `infra/`, `telegram` (PTB), and stdlib.
- bot.py registers `cmd_*` handlers + `*_check_job` schedulers in `main()` and `post_init()`.
- All watchdogs pass mypy strict.

### Inline in bot.py (intentionally not extracted)

| Code | LOC | Reason |
|---|---|---|
| Health check + auto-fix loop | ~250 | Tightly coupled with bot orchestration state (`_prev_vps_state`, `_container_restarts`) |
| /monitor + /vps multi-step | ~300 | Conversation handler state, hard-coupled to PTB |
| Voice + meeting + journal + skill + tanya cmd | ~500 | Pure handler code, no clear extraction unit |
| post_init / main bootstrap | ~200 | App lifecycle, not extractable |

**Refactor terminal state reached:** all "leaf" units extracted. Remaining bot.py is handler code structurally coupled with PTB and bot orchestration. Further extraction would be code movement without design improvement.

## langgraph-agent package

FastAPI service that exposes LLM-backed endpoints to telegram-bot and external webhooks.

```
langgraph-agent/app/
├── main.py                 # FastAPI app + 26 endpoint registrations
├── config.py               # All env-driven config (LLM_*, GH_*, AGENT_SECRET, etc.)
├── llm.py                  # chat_completion + chat_with_persona (OpenAI-compatible client)
├── telegram.py             # send_message helper (used by webhooks for proactive notifs)
├── pr_review.py            # GitHub PR auto-review (webhook + on-demand)
├── gitlab_review.py        # GitLab MR auto-review (webhook)
├── test_coverage.py        # Coverage scan + LLM test generation + auto-PR
├── deps_watchdog.py        # Server-side deps scan
├── docs_sync.py            # Docs/spec PR analyzer
├── meeting_notes.py        # Meeting note summarizer + action items
├── journal.py              # Daily journal prompt + embedding store
├── skills.py               # Skill log + search via Qdrant
├── code_repos.py           # Repo registry (whitelist for review/coverage features)
├── tools.py                # Knowledge search + memory + task ops
├── workflow.py             # n8n trigger / fallback workflow handlers
├── system_status.py        # / vps_status                Container/VPS health snapshot
├── resource_alerts.py      # Resource threshold alerts
├── embedding.py            # Embedding wrappers
├── qdrant_helper.py        # Qdrant payload index ensure
└── sync.py                 # Vault sync (Obsidian → embeddings)
```

**Endpoint patterns:**
- All `POST /api/*` endpoints (except webhooks) use `dependencies=[Depends(verify_secret)]` for `X-Agent-Secret` header validation.
- Webhooks (`/api/webhook/{github,gitlab}`) verify HMAC signatures (GitHub) or shared token (GitLab) before processing.
- Background-heavy work uses FastAPI `BackgroundTasks` to return 202 quickly while processing async.

**Auto-PR features (PR Review + Test Coverage) follow the same pattern:**
1. Whitelist file at `/app/state/{review,coverage}_repos.json`
2. `is_repo_allowed` enforcement
3. Background processing with telegram notification
4. State held in `/app/state/` (mounted volume), not in-memory

**Empty-whitelist semantics differ:**
- PR Review: empty whitelist allows-all (read-only review action, low risk)
- Test Coverage: empty whitelist denies-all (write action — opens PRs, opt-in only)

## CI/CD gates

Pre-commit (4 hooks, run on commit):
1. ruff (pyflakes-class)
2. actionlint (workflow lint)
3. compileall (syntax check)
4. orphan-reference checks (`scripts/lint_orphan_refs.py`)

Pre-push (+2 hooks):
5. mypy lenient (whole package)
6. mypy strict (22-module whitelist: 11 agent + 6 infra + 5 watchdogs)

CI (`deploy.yml` lint job, +2 gates):
7. Caddy validate
8. promtool + amtool config checks

Test gate (CI test job):
- pytest 743+ tests, coverage floor 27% (actual ~42%)

## Refactor history

| Batch | Date (UTC) | Modules extracted | bot.py LOC delta |
|---|---|---|---|
| 1 (DNS pilot) | 2026-05-31 14:49 | `infra/{auth,config_store}` + `watchdogs/dns` | 3524→3350 (-174) |
| 2 | 2026-05-31 15:18 | `infra/ssh` + `watchdogs/ssl` | 3350→3150 (-200) |
| 3 | 2026-05-31 15:46 | `infra/prom` + `watchdogs/{capacity,deps,drift}` | 3150→2796 (-354) |
| 4 | 2026-05-31 16:19 | `infra/{agent,gh}` | 2796→2769 (-27) |
| 5 (polish) | 2026-05-31 17:00 | tests + ARCHITECTURE.md (no production code change) | 2769 |
| 6 | 2026-05-31 17:55 | Path C coverage tests + `watchdogs/hygiene` | 2769→2598 (-171) |
| 7 (FINAL) | 2026-05-31 18:20 | `watchdogs/{firewall,morning_brief}` | 2598→2232 (-366) |
| feat | 2026-05-31 19:48 | `watchdogs/test_coverage` (new feature, not extraction) | 2232→2253 (+21) |

**Cumulative: -1271 LOC (-36.1%) across 7 refactor batches + 1 feature batch.**

## When to extract a new helper

**Extract to `infra/` when:**
- Used by 2+ modules (or has clear potential to be reused)
- Has no Telegram-specific I/O (no `update.message.reply_text`)
- Can pass mypy strict
- Can be unit-tested with mocked I/O

**Extract to `watchdogs/` when:**
- Has a scheduled job entrypoint (`*_check_job`)
- Has a Telegram command handler (`cmd_*`)
- Can be tested in isolation with monkeypatched dependencies

**Keep inline in bot.py when:**
- Tightly coupled with bot orchestration (e.g. `post_init`, application setup)
- Single-use helper for one cmd handler
- Touches global bot state (e.g. `application.bot`)

## Testing patterns

```python
# Pattern 1: Isolated config store
def test_X(self, tmp_path, monkeypatch):
    monkeypatch.setattr(config_store, "CONFIG_DIR", tmp_path)
    monkeypatch.setattr(config_store, "CONFIG_FILE", tmp_path / "config.json")
    ...

# Pattern 2: Re-parse env-dependent module state
def test_Y(self, monkeypatch):
    monkeypatch.setenv("MY_ENV", "value")
    module = importlib.reload(my_module)
    ...

# Pattern 3: Fake httpx.AsyncClient (no network)
def test_Z(self, monkeypatch):
    class FakeClient:
        async def __aenter__(self): return self
        async def __aexit__(self, *args): return None
        async def get(self, url, headers): return FakeResponse()
    monkeypatch.setattr(httpx, "AsyncClient", FakeClient)
    ...

# Pattern 4: Replace top-level imported name
def test_W(self, monkeypatch):
    async def fake(*args, **kw): ...
    monkeypatch.setattr(deps, "agent_post", fake)
    ...
```

For deeper context on individual feature design, see `README.md` (which covers user-facing commands + setup).
