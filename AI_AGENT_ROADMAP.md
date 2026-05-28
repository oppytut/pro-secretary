# AI Agent 24/7 Roadmap

**Created:** 2026-05-28
**Context:** AI Personal Secretary Stack — Telegram bot + LangGraph agent + Prometheus + multi-VPS Docker

---

## Current Stack

| Komponen | Fungsi |
|---|---|
| Telegram Bot (PTB 22) | Interface utama, command handler, inline keyboard |
| LangGraph Agent | AI brain, chat, Q&A, task management |
| Prometheus + Alertmanager | VPS metrics, threshold alerts (CPU/RAM/disk/swap/load) |
| Bot Health Check (5 min) | VPS up/down + container health transitions + restart loop |
| SSH-based Docker PS | Container listing on remote VPS |
| GitHub Actions | CI/CD deploy pipeline |
| 8-13 VPS (Docker) | Production infrastructure |

---

## Priority Recommendation

| # | Fitur | Tier | Effort | Impact |
|---|---|---|---|---|
| 1 | Incident Auto-Responder | Infra | 1-2 hari | Tidur tenang — auto-fix sebelum user bangun |
| 2 | Morning Standup Brief | Productivity | 0.5 hari | 5 menit saved tiap pagi, full visibility |
| 3 | Config Drift Detector | Infra | 1 hari | Prevent erpstg-style incidents |
| 4 | Auto PR Review | Code | 1-2 hari | Catch bugs sebelum merge |
| 5 | Capacity Planning | Infra | 1 hari | Proactive vs reactive scaling |
| 6 | Spec-to-Implementation | Productivity | 2-3 hari | Multiply developer output |

---

## TIER 1 — Autonomous Code Workers

### 1.1 Auto PR Review

**Deskripsi:** Setiap PR masuk di semua repo, agent otomatis review code quality, security, performance. Bisa auto-approve kalau minor change.

**Cara Kerja:**
1. GitHub webhook (push/PR event) → hit endpoint di LangGraph agent
2. Agent fetch PR diff via GitHub API (`gh pr diff`)
3. Analyze: code quality, security patterns, performance anti-patterns, test coverage
4. Post review comment di PR dengan findings
5. Kalau clean + minor change → auto-approve
6. Kalau ada issue → request changes dengan suggestion

**Komponen:**
- GitHub webhook receiver (new endpoint di LangGraph agent)
- PR analysis prompt chain (security, quality, performance)
- GitHub API integration (post review, approve/request changes)
- Config: repo whitelist, auto-approve rules

**Estimasi:** 1-2 hari

---

### 1.2 Auto Bug Triage

**Deskripsi:** Monitor error logs dari semua service. Agent diagnose root cause, buat draft fix PR, assign severity otomatis.

**Cara Kerja:**
1. Collect error logs via Docker logs / Sentry webhook
2. Agent analyze stack trace + recent commits
3. Identify root cause file + line
4. Generate fix (atau draft fix kalau complex)
5. Create branch + PR dengan fix
6. Assign severity label (critical/high/medium/low)
7. Notify via Telegram: "Bug detected in X, fix PR created: [link]"

**Komponen:**
- Log collector (Docker logs aggregation atau Sentry integration)
- Error pattern recognition prompt
- Git automation (branch, commit, PR creation)
- Severity classification model

**Estimasi:** 2-3 hari

---

### 1.3 Dependency Watchdog

**Deskripsi:** Monitor CVE database + outdated dependencies. Auto-create upgrade PR + run tests. Auto-merge kalau tests pass.

**Cara Kerja:**
1. Daily cron: scan semua repo `package.json` / `requirements.txt` / `composer.json`
2. Check against CVE databases (GitHub Advisory, NVD)
3. Check outdated versions (npm outdated, pip list --outdated)
4. Per vulnerable/outdated dep: create branch, bump version, run CI
5. Kalau CI pass + patch version → auto-merge
6. Kalau CI fail atau major version → notify user via Telegram

**Komponen:**
- Dependency scanner (per ecosystem: npm, pip, composer)
- CVE database integration (GitHub Advisory API)
- Auto-PR creation with version bump
- CI status monitoring + auto-merge logic

**Estimasi:** 1-2 hari

---

### 1.4 Scheduled Refactor

**Deskripsi:** Tiap malam agent scan codebase, identify code smells, dead code, type safety gaps. Create refactor PRs.

**Cara Kerja:**
1. Nightly cron (02:00): clone/pull semua repo
2. Run static analysis: complexity, duplication, dead code, type coverage
3. Rank findings by impact (high complexity + frequently changed = priority)
4. Per top-3 finding: create branch, refactor, verify tests pass
5. Create PR dengan explanation: "Reduced cyclomatic complexity in X from 15 to 6"
6. Morning summary: "3 refactor PRs created overnight"

**Komponen:**
- Static analysis tools (radon/pylint for Python, eslint for JS/TS, phpstan for PHP)
- Refactoring prompt chain (understand context → safe refactor → verify)
- Nightly cron job in bot
- PR creation automation

**Estimasi:** 2-3 hari

---

### 1.5 Test Coverage Agent

**Deskripsi:** Detect untested code paths, auto-generate unit/integration tests, submit as PR.

**Cara Kerja:**
1. Run coverage report per repo (pytest-cov, jest --coverage, phpunit)
2. Identify uncovered functions/methods (priority: public APIs, critical paths)
3. Agent read function + surrounding context
4. Generate meaningful tests (not just coverage padding)
5. Run tests locally to verify they pass
6. Create PR: "Add tests for UserService.createUser (was 0% → 85%)"

**Komponen:**
- Coverage report parser (lcov, coverage.py, phpunit XML)
- Test generation prompt (context-aware, not generic)
- Test runner integration (verify before PR)
- Coverage threshold config per repo

**Estimasi:** 2-3 hari

---

## TIER 2 — Proactive Monitoring & Response

### 2.1 Incident Auto-Responder

**Deskripsi:** Extend health check yang sudah ada. Bukan cuma alert, tapi AUTO-FIX: restart container, rollback deploy, prune disk.

**Cara Kerja:**
1. Health check detect issue (container down, disk full, OOM)
2. Agent evaluate severity + determine action
3. Execute fix via SSH:
   - Container unhealthy/down -> docker restart
   - Deploy broke (error spike after deploy) -> git revert + redeploy
   - Disk full -> docker system prune + clear old logs
   - OOM -> identify top consumer + restart
4. Verify fix worked (re-check after 60s)
5. Report action taken via Telegram
6. Kalau auto-fix gagal -> escalate ke user dengan full context

**Komponen:**
- Action executor (SSH commands per fix type)
- Rollback logic (track last good deploy SHA)
- Fix verification loop
- Escalation path (auto-fix failed -> human)
- Audit log (semua auto-fix actions logged)

**Estimasi:** 1-2 hari

---

### 2.2 Performance Regression Detector

**Deskripsi:** Compare response times per-deploy. Kalau degrade >10%, bisect commit yang cause regression.

**Cara Kerja:**
1. Per deploy: run lightweight benchmark (curl endpoints, measure p95)
2. Compare against baseline (rolling average last 5 deploys)
3. Kalau regression >10%: git bisect between last good and current
4. Identify commit yang introduce regression
5. Notify: "Performance regression +15% on /api/checkout. Caused by commit abc123 (added N+1 query)"

**Komponen:**
- Benchmark runner (curl + timing per endpoint)
- Baseline storage (SQLite/JSON per deploy SHA)
- Git bisect automation
- Prometheus query for historical response times

**Estimasi:** 1-2 hari

---

### 2.3 Cost Optimizer

**Deskripsi:** Analyze cloud spend daily. Suggest right-sizing, unused resources, spot instances.

**Cara Kerja:**
1. Daily: collect resource usage per VPS (CPU avg, RAM avg, disk used)
2. Compare against VPS spec (allocated vs actual used)
3. Identify: over-provisioned (paying for unused), under-provisioned (risk)
4. Suggest: downgrade VPS X from 4GB to 2GB (avg usage 800MB)
5. Detect unused: containers running but no traffic, idle databases

**Komponen:**
- Resource usage aggregator (Prometheus historical data)
- VPS spec registry (what we pay for vs what we use)
- Cost calculation (provider pricing)
- Recommendation engine

**Estimasi:** 1 hari

---

### 2.4 SSL/Domain Watchdog

**Deskripsi:** Monitor cert expiry, DNS propagation, domain renewal. Auto-renew atau alert 30 hari sebelum.

**Cara Kerja:**
1. Daily: check SSL cert expiry semua domain (openssl s_client)
2. Alert 30 hari sebelum expiry
3. Auto-renew via certbot/acme.sh kalau configured
4. Monitor DNS: check A/CNAME records match expected
5. Domain expiry check via WHOIS

**Komponen:**
- SSL checker (openssl s_client per domain)
- DNS verifier (dig/nslookup)
- Domain registry (list semua domain + expected records)
- Auto-renewal trigger (certbot renew)

**Estimasi:** 0.5 hari

---

### 2.5 Backup Verifier

**Deskripsi:** Nightly restore backup ke temp environment, verify data integrity. Bukan cuma "backup ran" tapi "backup actually works".

**Cara Kerja:**
1. Nightly: download latest backup (DB dump, file backup)
2. Restore ke temp container (isolated, auto-destroy after)
3. Run integrity checks: row counts, critical data exists, no corruption
4. Compare against production (sample rows match)
5. Report: "Backup verified OK: 150k rows, 3 tables, restore time 45s"
6. Alert kalau: backup missing, restore fails, data mismatch

**Komponen:**
- Backup download automation
- Temp container orchestration (docker run, restore, verify, destroy)
- Integrity check queries
- Comparison logic (production vs backup sample)

**Estimasi:** 1 hari

---

## TIER 3 — Developer Productivity

### 3.1 Morning Standup Brief

**Deskripsi:** 07:00 tiap hari, satu Telegram message konsolidasi: semua repo activity, open PRs, failing CI, overnight alerts, jadwal hari ini, weather.

**Cara Kerja:**
1. Cron 07:00 trigger di bot
2. Parallel collect:
   - GitHub: open PRs, failing CI, commits semalam
   - Cal.com: jadwal hari ini
   - Prometheus: alerts last 12h
   - Health check log: containers/VPS issues semalam
   - Weather API
3. Aggregate jadi single message
4. Format: priority order (urgent first), grouped by category
5. Send ke Telegram

**Komponen:**
- Cron scheduler (existing JobQueue)
- Multi-source aggregator (GitHub API, Cal.com, Prometheus, weather)
- Message template (prioritized, scannable)

**Estimasi:** 0.5 hari

---

### 3.2 Spec-to-Implementation

**Deskripsi:** Kirim spec/PRD via Telegram. Agent breakdown jadi tasks, implement satu-satu, create PRs, request review.

**Cara Kerja:**
1. User kirim spec (text atau voice) ke bot
2. Agent parse spec -> identify: scope, components affected, acceptance criteria
3. Generate task breakdown (atomic, ordered by dependency)
4. Per task: create branch, implement, run tests, create PR
5. Notify: "Implementing spec X. Task 1/5 done: PR #123. Task 2/5 in progress..."
6. User can interrupt/redirect via Telegram

**Komponen:**
- Spec parser (LLM understands intent)
- Task decomposition prompt
- Code generation per task
- PR automation
- Progress tracking + Telegram updates

**Estimasi:** 2-3 hari

---

### 3.3 Meeting Notes -> Action Items

**Deskripsi:** Upload meeting recording/transcript ke bot. Agent extract action items, auto-create tasks, assign owner.

**Cara Kerja:**
1. User kirim audio file atau transcript ke bot
2. Bot transcribe (existing Whisper integration)
3. Agent analyze: identify decisions, action items, deadlines, owners
4. Per action item: create task via existing /task flow
5. Notify summary: "5 action items extracted, 3 assigned to you, 2 to team"

**Komponen:**
- Audio upload handler (existing)
- Whisper transcription (existing)
- Action item extraction prompt
- Task creation integration

**Estimasi:** 0.5 hari

---

### 3.4 Documentation Sync

**Deskripsi:** Code berubah -> agent auto-update API docs, README, changelog. Detect stale docs.

**Cara Kerja:**
1. PR merge trigger -> agent compare diff
2. Identify changes that affect docs:
   - New API endpoint -> update OpenAPI spec
   - Function signature change -> update docstrings
   - New feature -> update README usage section
   - Version bump -> update CHANGELOG
3. Create follow-up PR with doc updates
4. Detect stale: docs reference functions yang sudah dihapus/renamed

**Komponen:**
- Diff analyzer (what changed semantically)
- Doc location mapping (which docs cover which code)
- LLM doc generator (context-aware)
- Stale detection (cross-reference docs vs current code)

**Estimasi:** 1-2 hari

---

### 3.5 Learning Digest

**Deskripsi:** Track tech stack -> curate relevant articles, new releases, breaking changes weekly.

**Cara Kerja:**
1. Registry: tech stack per project (PHP/Laravel, Python/FastAPI, React, etc)
2. Weekly cron: search latest articles, releases, CVE
3. Filter by relevance to user stack
4. Summarize top 5-10 items
5. Send Friday afternoon: "Weekly digest: 3 Laravel 12 features, 2 Python security patches, 1 React 19 RC"

**Komponen:**
- Stack registry (tracked per project)
- Source aggregator (Hacker News, Reddit, Twitter, RSS, GitHub releases)
- Relevance filter (LLM ranks by stack match)
- Summary generator

**Estimasi:** 1 hari

---

## TIER 4 — Multi-Agent Orchestration

### 4.1 Deploy Pipeline Agent

**Deskripsi:** "Deploy feature X" -> agent: run tests, check staging, deploy, smoke test, monitor 30 min, rollback kalau error.

**Cara Kerja:**
1. User: "deploy main ke production" via Telegram
2. Agent verify: CI green, no open blockers
3. Deploy ke staging first (docker compose up)
4. Run smoke tests (health endpoints, critical flows)
5. Kalau pass -> deploy production
6. Monitor 30 menit: error rate, response time, container health
7. Kalau anomaly -> auto-rollback + notify
8. Kalau clean -> "Deploy complete. 30 min monitoring clean."

**Komponen:**
- Deploy orchestrator (staging -> production pipeline)
- Smoke test runner (configurable per project)
- Post-deploy monitor (error rate baseline comparison)
- Rollback automation (git revert + redeploy)

**Estimasi:** 2-3 hari

---

### 4.2 Cross-Repo Impact Analysis

**Deskripsi:** Before merge, agent trace dependencies across semua repo. Predict breaking changes.

**Cara Kerja:**
1. PR opened -> agent analyze: which functions/APIs changed
2. Search all other repos: who calls these functions/APIs
3. Identify potential breaks: "Repo B calls endpoint /api/users which you changed response format"
4. Post warning on PR: "Impact: 2 repos affected. Repo B line 45, Repo C line 120"
5. Suggest: update consumers first, or add backward compat

**Komponen:**
- API/function dependency graph (built from code analysis)
- Cross-repo search (existing /tanya infrastructure)
- Impact assessment prompt
- PR comment automation

**Estimasi:** 2-3 hari

---

### 4.3 Client Communication Agent

**Deskripsi:** Monitor project progress. Auto-draft weekly client updates, flag blockers, suggest timeline adjustments.

**Cara Kerja:**
1. Weekly cron: collect progress per project
   - Commits, PRs merged, features completed
   - Blockers (failing CI, open issues)
   - Timeline vs plan
2. Generate client-friendly update (non-technical language)
3. Draft email/message, send ke user for review
4. User approve -> send, atau edit dulu

**Komponen:**
- Progress tracker (GitHub commits/PRs per project per week)
- Client template (professional, non-technical)
- Draft + approval flow via Telegram
- Email sender (existing SMTP integration)

**Estimasi:** 1 hari

---

### 4.4 Database Migration Agent

**Deskripsi:** Schema change request -> agent generate migration, test on clone, verify rollback works, schedule deploy window.

**Cara Kerja:**
1. User: "tambah kolom phone ke users table"
2. Agent generate migration file (Laravel/Prisma/raw SQL)
3. Clone production DB ke temp (pg_dump + restore)
4. Run migration on clone -> verify success
5. Run rollback on clone -> verify clean rollback
6. Create PR with migration file
7. Suggest deploy window (low traffic period)

**Komponen:**
- Migration generator (per ORM: Laravel, Prisma, raw SQL)
- DB clone automation (pg_dump/restore to temp)
- Migration test runner (up + down verification)
- Traffic analyzer (identify low-traffic windows)

**Estimasi:** 1-2 hari

---

### 4.5 Load Test on Demand

**Deskripsi:** "Load test /api/checkout" -> agent spin up k6/locust, run scenarios, analyze bottlenecks, suggest optimizations.

**Cara Kerja:**
1. User: "load test /api/checkout 100 concurrent 5 menit"
2. Agent generate k6 script (endpoint, headers, payload)
3. Run load test from VPS (isolated, not from production)
4. Collect results: p50, p95, p99, error rate, throughput
5. Analyze bottlenecks: slow queries, memory spikes, connection pool exhaustion
6. Report: "p95=450ms, bottleneck: N+1 query in OrderService.getItems"
7. Suggest fix

**Komponen:**
- k6/locust script generator
- Load test runner (dedicated VPS atau container)
- Results analyzer (identify bottlenecks from metrics)
- Optimization suggestion prompt

**Estimasi:** 1-2 hari

---

## TIER 5 — Long-running Autonomous

### 5.1 Feature Branch Autopilot

**Deskripsi:** Assign feature ke agent. Agent implement end-to-end (frontend + backend + tests + docs), iterate on review feedback sampai merged.

**Cara Kerja:**
1. User: "implement user registration with email verification"
2. Agent decompose: API endpoint, DB migration, email service, frontend form, tests
3. Create feature branch, implement step-by-step
4. Per step: commit, run tests, verify
5. Create PR when complete
6. User review -> agent address feedback (fix, refactor)
7. Loop sampai approved + merged

**Komponen:**
- Feature decomposition engine
- Multi-file code generation (frontend + backend coherent)
- Review feedback parser (understand what reviewer wants)
- Iterative fix loop (address comments, push, re-request review)

**Estimasi:** 3-5 hari

---

### 5.2 Codebase Migration

**Deskripsi:** "Migrate from Express to Fastify" -> agent plan, execute file-by-file, maintain backward compat, run tests each step.

**Cara Kerja:**
1. Agent analyze current codebase: routes, middleware, plugins
2. Generate migration plan (ordered by dependency, least-risk first)
3. Per file: rewrite, run tests, commit
4. Maintain backward compat during migration (both old + new work)
5. Final: remove old code, update docs
6. Progress updates via Telegram: "Migration 45% complete. 12/27 files done."

**Komponen:**
- Codebase analyzer (understand current patterns)
- Migration planner (dependency-ordered)
- File-by-file rewriter (context-aware)
- Backward compat layer generator
- Progress tracker

**Estimasi:** 3-5 hari (framework), ongoing per migration

---

### 5.3 Security Audit Loop

**Deskripsi:** Continuous: scan for OWASP top 10, check auth flows, test for injection. Report + auto-fix.

**Cara Kerja:**
1. Weekly full scan: semua repo
2. Check: SQL injection, XSS, CSRF, auth bypass, secrets in code, insecure deps
3. Per finding: severity + exploitability assessment
4. Auto-fix kalau straightforward (parameterize query, escape output)
5. Report: "2 high, 5 medium findings. 3 auto-fixed (PR #45). 4 need manual review."
6. Track: findings over time, mean-time-to-fix

**Komponen:**
- Static security scanner (semgrep, bandit, phpstan security rules)
- Dynamic testing (basic fuzzing on endpoints)
- Auto-fix patterns (common vulnerability -> fix template)
- Finding tracker (history, trends)

**Estimasi:** 2-3 hari

---

### 5.4 A/B Test Lifecycle

**Deskripsi:** Define hypothesis -> agent implement variants, deploy, monitor metrics, declare winner, clean up loser.

**Cara Kerja:**
1. User: "A/B test: new checkout flow vs current. Metric: conversion rate"
2. Agent implement variant B (new flow)
3. Add feature flag + traffic split logic
4. Deploy both variants
5. Monitor metric for N days (statistical significance)
6. Declare winner when p-value < 0.05
7. Remove loser code, clean up feature flag
8. Report: "Variant B wins: +12% conversion (p=0.02). Cleaned up."

**Komponen:**
- Feature flag system (or integrate existing: LaunchDarkly, Unleash)
- Variant implementation automation
- Statistical significance calculator
- Auto-cleanup (remove losing variant code)

**Estimasi:** 3-5 hari

---

## TIER INFRA-SPECIFIC

### I.1 IaC Drift Detector

**Deskripsi:** Periodic compare actual state (VPS, DNS, firewall rules, Docker configs) vs git-tracked config. Alert + auto-fix kalau drift.

**Cara Kerja:**
1. Hourly scan: collect actual state per VPS via SSH
   - Docker compose ps + image versions
   - UFW rules
   - Nginx/Caddy config
   - Cron jobs
2. Compare against git-tracked source-of-truth
3. Drift detection: file diff, version mismatch, manual changes
4. Alert: "VPS X has drift: docker-compose.yml different from git"
5. Optional auto-fix: re-deploy from git

**Komponen:**
- State collector (SSH commands per resource type)
- Diff engine (git vs actual)
- Drift classifier (intentional vs accidental)
- Auto-remediation (re-apply git state)

**Estimasi:** 1-2 hari

---

### I.2 Auto-Scaling Agent

**Deskripsi:** Monitor traffic patterns. Predict load. Scale up sebelum peak, down saat idle.

**Cara Kerja:**
1. Collect traffic metrics: requests/sec, response time, queue depth
2. Pattern recognition: identify daily/weekly cycles
3. Predict next 1h load (time-series forecast)
4. Trigger scale: docker compose up -d --scale app=N
5. Alert when scaled, log decision for audit

**Komponen:**
- Traffic metrics collector (Prometheus integration)
- Time-series forecast model
- Scaling executor (compose scale, K8s replicas)
- Decision audit log

**Estimasi:** 2 hari

---

### I.3 Nginx/Caddy Config Agent

**Deskripsi:** "Tambah subdomain staging.app.com" -> agent generate config, request SSL, test, deploy.

**Cara Kerja:**
1. User: "add subdomain staging.app.com pointing to port 8080"
2. Agent generate Caddy/Nginx config block
3. Validate config syntax (caddy validate / nginx -t)
4. DNS check: A record exists?
5. Reload web server
6. Verify cert obtained + site reachable
7. Commit config to git

**Komponen:**
- Config template engine
- DNS verifier
- SSL trigger (Caddy auto, Nginx + certbot)
- Reload + verification

**Estimasi:** 1 hari

---

### I.4 Log Aggregation + Anomaly Detection

**Deskripsi:** Collect logs semua VPS. Detect anomaly patterns. Alert + diagnose.

**Cara Kerja:**
1. Centralize logs: Loki/Promtail per VPS, atau rsyslog forward
2. Real-time scan: error rate baseline, unusual access patterns
3. Anomaly detection: spike error rate, new error types, suspicious IPs
4. Alert with context: "Error rate +500% on payment-service. Top error: TimeoutException on Stripe API."
5. Diagnose: correlate with recent deploys, traffic, dependencies

**Komponen:**
- Log shipper (Promtail per VPS)
- Loki/ELK aggregator
- Anomaly detection (statistical baseline + LLM pattern recognition)
- Diagnosis prompt (correlate signals)

**Estimasi:** 2-3 hari

---

### I.5 Firewall Audit Agent

**Deskripsi:** Nightly scan: open ports vs expected, UFW rules consistency across VPS, detect unauthorized exposure.

**Cara Kerja:**
1. Nightly: SSH ke setiap VPS
2. Run: ufw status, ss -tlnp, iptables -L
3. Compare against expected (config in git)
4. Detect: unexpected open port, missing rule, exposed service
5. Alert: "VPS X has port 5432 (PostgreSQL) exposed to 0.0.0.0"
6. Optional auto-fix: apply expected rules

**Komponen:**
- SSH command runner per VPS
- Expected state config (per VPS port whitelist)
- Diff + alert
- Auto-remediation (ufw reload from config)

**Estimasi:** 1 hari

---

### I.6 Docker Image Hygiene

**Deskripsi:** Monitor image sizes, unused layers, dangling volumes. Auto-prune + alert kalau disk usage naik.

**Cara Kerja:**
1. Daily per VPS: docker system df
2. Track trends: image size growth, dangling images, unused volumes
3. Auto-prune kalau aman: docker image prune (no force, only dangling)
4. Alert kalau disk pressure: "VPS X /var/lib/docker = 80% used"
5. Suggest: rebuild image (smaller base, multi-stage)

**Komponen:**
- Disk usage tracker (Prometheus + Docker API)
- Auto-prune (safe defaults)
- Image size analyzer (suggest optimization)

**Estimasi:** 0.5 hari

---

### I.7 DNS Health Monitor

**Deskripsi:** Check propagation, TTL consistency, detect hijacking, monitor semua domain/subdomain.

**Cara Kerja:**
1. Hourly: dig semua domain dari multiple resolvers (Google, Cloudflare, ISP)
2. Compare results: detect inconsistency (propagation issue or hijack)
3. Verify: A/AAAA matches expected, MX records intact
4. Alert anomaly: "Domain X resolves to unexpected IP from Cloudflare DNS"
5. Track TTL changes (low TTL = recent change, audit it)

**Komponen:**
- Multi-resolver query (dig with @resolver)
- Expected DNS state (config in git)
- Anomaly detection (cross-resolver comparison)

**Estimasi:** 0.5 hari

---

### I.8 Automated Disaster Recovery Drill

**Deskripsi:** Weekly: simulate failure scenario, verify recovery procedure works, report time-to-recover.

**Cara Kerja:**
1. Weekly cron (Sunday 03:00):
2. Pick scenario: kill random container, block port, fill disk
3. Execute: actually trigger failure
4. Measure: how long until alerts fire, auto-fix executes, system recovers
5. Report: "DR drill: container kill -> auto-restart in 4m 12s. Pass."
6. Identify regression: kalau slower than baseline, investigate

**Komponen:**
- Scenario library (failure types)
- Chaos injector (controlled failure trigger)
- Recovery time measurement
- Trend tracking (baseline + regression alerts)

**Estimasi:** 2 hari

---

### I.9 Config Sync Agent

**Deskripsi:** Satu source-of-truth (git). Agent ensure semua VPS punya config yang sama.

**Cara Kerja:**
1. Git push to config repo -> webhook trigger
2. Agent SSH ke setiap VPS dalam target group
3. Pull latest config
4. Apply (reload service, restart container)
5. Verify success per VPS
6. Report: "Config synced to 8/8 VPS in 2m 15s"
7. Detect manual SSH changes -> alert + offer commit-back

**Komponen:**
- Git webhook receiver
- Multi-VPS deploy orchestrator
- Verification per target
- Drift back-detection

**Estimasi:** 1-2 hari

---

### I.10 Capacity Planning

**Deskripsi:** Track growth trends (disk, RAM, connections). Predict kapan perlu upgrade. Alert 2 minggu sebelum limit.

**Cara Kerja:**
1. Collect trend data via Prometheus (last 30 days)
2. Linear regression / time-series forecast
3. Predict: kapan disk full, RAM exhaust, connection limit hit
4. Alert 2 minggu sebelum: "VPS X disk akan penuh dalam 15 hari (current trend +500MB/day)"
5. Suggest: upgrade plan, cleanup, archival

**Komponen:**
- Historical metrics query (Prometheus range queries)
- Trend analysis (linear/seasonal forecast)
- Threshold-based alerting (predictive, not reactive)

**Estimasi:** 1 hari

---

### I.11 Network Topology Map

**Deskripsi:** Auto-discover: which VPS talks to which, port dependencies, single points of failure. Update tiap deploy.

**Cara Kerja:**
1. Collect network connections per VPS (ss -tunap)
2. Build graph: nodes = VPS/services, edges = connections
3. Identify: dependencies (A talks to B), single points of failure
4. Update visualization (Mermaid diagram in repo)
5. Alert when topology changes unexpectedly

**Komponen:**
- Network connection scanner per VPS
- Graph builder (services + dependencies)
- Visualization generator (Mermaid/Graphviz)
- Change detection

**Estimasi:** 1-2 hari

---

### I.12 Compliance Checker

**Deskripsi:** Verify: SSH key rotation, no root login, fail2ban active, unattended-upgrades enabled, no default passwords.

**Cara Kerja:**
1. Weekly per VPS: run compliance checks
   - SSH key age (warn > 1 year)
   - sshd_config: PermitRootLogin, PasswordAuthentication
   - fail2ban service status
   - unattended-upgrades enabled
   - No default user passwords
2. Score per VPS: pass/fail
3. Report: "VPS X: 8/10 pass. Failing: SSH key 18 months old, fail2ban not running."
4. Auto-fix safe items (enable fail2ban)
5. Track over time: compliance trend

**Komponen:**
- Compliance check library (per item: command + expected output)
- Scoring engine
- Auto-remediation (safe items only)
- Trend tracking

**Estimasi:** 1-2 hari

---

## Recommended Implementation Order

### Top 6 — Start Here

**1. Incident Auto-Responder** (Tier 2.1) — 1-2 hari
- Extend health check yang sudah ada
- Immediate ROI: tidur tenang, auto-fix sebelum user bangun
- Risk: rendah (start with safe actions: restart, prune)

**2. Morning Standup Brief** (Tier 3.1) — 0.5 hari
- Quick win, low effort
- Visibility: full picture pagi hari
- Reuse existing: GitHub API, Cal.com, Prometheus

**3. Config Drift Detector** (Tier I.1) — 1-2 hari
- Prevent erpstg-style incidents (config drift)
- Foundational: needed before #4 makes sense
- Source-of-truth enforcement

**4. Auto PR Review** (Tier 1.1) — 1-2 hari
- Catch bugs sebelum merge
- Multiplier: every push gets reviewed
- Foundation for Tier 5 features

**5. Capacity Planning** (Tier I.10) — 1 hari
- Proactive vs reactive
- Prevent future incidents
- Reuse existing Prometheus data

**6. Spec-to-Implementation** (Tier 3.2) — 2-3 hari
- Multiplier: input -> code automation
- Highest leverage feature
- Foundation for Tier 5.1 (Feature Branch Autopilot)

---

## Implementation Notes

### Architecture Pattern

Semua fitur baru harus fit ke existing pattern:

1. **Telegram bot** = user interface (commands, notifications, approvals)
2. **LangGraph agent** = AI brain (analysis, code gen, decision making)
3. **Bot JobQueue** = scheduling (cron jobs, periodic checks)
4. **SSH executor** = remote action (multi-VPS operations)
5. **Prometheus** = metrics + alerts
6. **GitHub API** = PR/repo operations
7. **PostgreSQL + Qdrant** = state + knowledge

### Approval Flow

Untuk fitur yang execute action (auto-fix, auto-merge, auto-deploy):

- **Tier safe**: execute langsung, log + notify (restart, prune)
- **Tier medium**: execute + can be reverted (auto-merge minor PRs)
- **Tier risky**: require approval via Telegram inline keyboard (deploy production)

### Audit Log

Setiap auto-action MUST log:
- Trigger (what caused it)
- Action taken (what was done)
- Result (success/failure)
- Reversibility (how to undo)

Stored di PostgreSQL audit_log table. Queryable via /history command.

### Failure Mode

Setiap auto-fix MUST have:
- Pre-condition check (is it safe to act?)
- Action with timeout
- Verification (did it actually fix?)
- Rollback (if action made things worse)
- Escalation (if cannot recover, alert human)

---

## Cost Considerations

User said "tidak usah memikirkan biaya token" — but masih ada considerations:

- **API rate limits** (GitHub API, OpenAI): batch operations, cache aggressively
- **VPS cost**: jangan spawn VPS baru tanpa approval, gunakan existing
- **Time cost**: prefer fast-feedback loops, fail-fast on errors

---

## Out of Scope (NOT in this roadmap)

- Multi-tenant features (only personal use)
- Public APIs (internal use only)
- Complex ML training (use existing LLMs)
- New programming languages (stick with current stack)

---

## Next Session Action Items

User decides:
1. **Pick top priority** dari 6 recommended
2. **Or pick custom subset** based on current pain points
3. **Or modify scope** based on time constraints

Then next session:
- Implement chosen feature(s)
- Test end-to-end (similar to health check verification done this session)
- Update TASK.md with progress
