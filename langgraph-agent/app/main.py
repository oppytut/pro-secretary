from __future__ import annotations

import hmac
import logging
from typing import Any

from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, Request, status
from pydantic import BaseModel, Field
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from . import code_repos, config, deps_watchdog, docs_sync, gitlab_review, journal, llm, meeting_notes, pr_review, resource_alerts, skills, system_status, telegram, test_coverage, tools, vps_status, workflow
from .qdrant_helper import ensure_payload_indexes
from .sync import sync_vault

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

limiter = Limiter(key_func=get_remote_address, default_limits=["120/minute"])
app = FastAPI(title="pro-secretary agent", version="1.0.0")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


@app.on_event("startup")
async def _on_startup() -> None:
    try:
        ensure_payload_indexes()
        logger.info("payload indexes ensured")
    except Exception as exc:
        logger.warning("payload index setup failed: %s", exc)


async def verify_secret(request: Request) -> None:
    if not config.AGENT_SECRET:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, detail="agent secret not configured")
    header = request.headers.get("x-agent-secret") or request.headers.get("authorization", "")
    token = header.removeprefix("Bearer ").strip()
    if not hmac.compare_digest(token, config.AGENT_SECRET):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="invalid agent secret")


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    user_id: str = ""
    model: str | None = None


class ChatResponse(BaseModel):
    response: str


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1)
    collection: str = "knowledge"
    limit: int = Field(5, ge=1, le=20)


class SearchResult(BaseModel):
    results: list[dict[str, Any]]


class RepoIndexRequest(BaseModel):
    repo: str = Field(..., min_length=1)


class RepoSearchRequest(BaseModel):
    query: str = Field(..., min_length=1)
    repo: str | None = None
    limit: int = Field(8, ge=1, le=20)


class RepoAskRequest(BaseModel):
    question: str = Field(..., min_length=1)
    repo: str | None = None


class TaskCreateRequest(BaseModel):
    title: str = Field(..., min_length=1)
    priority: str = "medium"
    due_date: str | None = None
    user_id: str | int | None = None


class TaskListRequest(BaseModel):
    limit: int = Field(20, ge=1, le=100)


class TaskDeleteRequest(BaseModel):
    task_ids: list[str] = Field(..., min_length=1, max_length=50)


class NoteRequest(BaseModel):
    content: str = Field(..., min_length=1)
    source: str = "telegram"
    user_id: str | int | None = None


class BriefingRequest(BaseModel):
    user_id: str | int | None = None


class SyncVaultRequest(BaseModel):
    vault_path: str | None = None


class NotifyRequest(BaseModel):
    text: str = Field(..., min_length=1)
    chat_id: str | int | None = None


class MeetingNotesRequest(BaseModel):
    transcript: str = Field(..., min_length=1, max_length=20000)
    user_id: str | int | None = None
    auto_create_tasks: bool = True


class DepsScanRequest(BaseModel):
    repo_id: str | None = None


class DocsSyncRequest(BaseModel):
    platform: str = Field(..., pattern="^(github|gitlab)$")
    owner: str | None = None
    repo: str | None = None
    pr_number: int | None = None
    project_id: str | None = None
    mr_iid: int | None = None
    title: str = ""
    body: str | None = None


JOURNAL_PROMPT_MARKER = "📓 Personal Journal"

JOURNAL_PROMPT_TEXT = (
    f"{JOURNAL_PROMPT_MARKER}\n\n"
    "Apa yang kamu kerjakan hari ini? Reply pesan ini untuk mencatat — "
    "akan otomatis masuk ke knowledge base."
)


class JournalEntry(BaseModel):
    text: str = Field(..., min_length=1, max_length=5000)
    user_id: str | int | None = None


class JournalPromptRequest(BaseModel):
    chat_id: str | int | None = None
    text: str | None = None


@app.get("/health")
async def health() -> dict[str, Any]:
    missing = config.assert_ready()
    return {
        "status": "ok" if not missing else "degraded",
        "missing_env": missing,
        "embedding_model": config.EMBEDDING_MODEL,
        "embedding_dim": config.EMBEDDING_DIM,
    }


@app.post("/api/chat", response_model=ChatResponse, dependencies=[Depends(verify_secret)])
@limiter.limit("20/minute")
async def chat(request: Request, req: ChatRequest) -> ChatResponse:
    reply = await workflow.run_chat(req.message, req.user_id, req.model)
    return ChatResponse(response=reply)


@app.post("/api/search", response_model=SearchResult, dependencies=[Depends(verify_secret)])
async def search(req: SearchRequest) -> SearchResult:
    hits = tools.qdrant_helper.search(req.collection, req.query, limit=req.limit)
    results = []
    for h in hits:
        payload = h["payload"]
        results.append(
            {
                "id": h["id"],
                "score": h["score"],
                "content": payload.get("content", ""),
                "source_file": payload.get("source_file") or payload.get("source") or "",
                "payload": payload,
            }
        )
    return SearchResult(results=results)


@app.post("/api/task", dependencies=[Depends(verify_secret)])
async def task_create(req: TaskCreateRequest) -> dict[str, Any]:
    task_id = tools.create_task(
        title=req.title,
        priority=req.priority,
        due_date=req.due_date,
        user_id=req.user_id,
    )
    return {"id": task_id, "title": req.title, "status": "pending"}


@app.post("/api/tasks", dependencies=[Depends(verify_secret)])
async def task_list(req: TaskListRequest) -> dict[str, Any]:
    items = tools.list_pending_tasks(limit=req.limit)
    return {"count": len(items), "tasks": items}


@app.post("/api/task/delete", dependencies=[Depends(verify_secret)])
async def task_delete(req: TaskDeleteRequest) -> dict[str, Any]:
    deleted = tools.delete_tasks(req.task_ids)
    return {"deleted": deleted, "task_ids": req.task_ids}


@app.post("/api/note", dependencies=[Depends(verify_secret)])
async def note_create(req: NoteRequest) -> dict[str, Any]:
    note_id = tools.store_note(req.content, source=req.source, user_id=req.user_id)
    return {"id": note_id, "content": req.content}


@app.post("/api/meeting_notes", dependencies=[Depends(verify_secret)])
@limiter.limit("6/minute")
async def meeting_notes_extract(request: Request, req: MeetingNotesRequest) -> dict[str, Any]:
    try:
        result = await meeting_notes.process_meeting(
            transcript=req.transcript,
            user_id=req.user_id,
            auto_create_tasks=req.auto_create_tasks,
        )
    except Exception:
        logger.exception("meeting_notes extraction failed")
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, detail="extraction failed")
    return result


@app.post("/api/deps/scan", dependencies=[Depends(verify_secret)])
@limiter.limit("4/minute")
async def deps_scan(request: Request, req: DepsScanRequest) -> dict[str, Any]:
    try:
        if req.repo_id:
            result = await deps_watchdog.scan_repo(req.repo_id)
            return {"results": [result], "report": deps_watchdog.format_report([result])}
        results = await deps_watchdog.scan_all_repos()
        return {"results": results, "report": deps_watchdog.format_report(results)}
    except Exception:
        logger.exception("deps scan failed")
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, detail="scan failed")


@app.post("/api/docs/suggest", dependencies=[Depends(verify_secret)])
@limiter.limit("6/minute")
async def docs_suggest(request: Request, req: DocsSyncRequest) -> dict[str, Any]:
    try:
        if req.platform == "github":
            if not req.owner or not req.repo or not req.pr_number:
                raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="github requires owner, repo, pr_number")
            result = await docs_sync.analyze_github_pr(req.owner, req.repo, req.pr_number, req.title, req.body)
        else:
            if not req.project_id or not req.mr_iid:
                raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="gitlab requires project_id, mr_iid")
            result = await docs_sync.analyze_gitlab_mr(req.project_id, req.mr_iid, req.title, req.body)
        result["report"] = docs_sync.format_for_telegram(result)
        return result
    except HTTPException:
        raise
    except Exception:
        logger.exception("docs suggest failed")
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, detail="docs suggest failed")


@app.post("/api/schedule", dependencies=[Depends(verify_secret)])
async def schedule_today() -> dict[str, Any]:
    events = await tools.get_today_schedule()
    return {"count": len(events), "events": events}


@app.post("/api/sync_vault", dependencies=[Depends(verify_secret)])
async def sync_vault_endpoint(req: SyncVaultRequest) -> dict[str, Any]:
    try:
        result = sync_vault(req.vault_path)
    except Exception:
        logger.exception("sync_vault failed")
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, detail="sync failed")
    return result


@app.post("/api/notify", dependencies=[Depends(verify_secret)])
@limiter.limit("60/minute")
async def notify_endpoint(request: Request, req: NotifyRequest) -> dict[str, Any]:
    result = await telegram.send_message(req.text, chat_id=req.chat_id)
    if not result.get("ok"):
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, detail=result.get("error") or result)
    return result


@app.post("/api/journal", dependencies=[Depends(verify_secret)])
@limiter.limit("30/minute")
async def journal_append(request: Request, req: JournalEntry) -> dict[str, Any]:
    result = journal.append_entry(req.text)
    if result.get("status_code") != 200:
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR
            if result["status_code"] >= 500
            else status.HTTP_400_BAD_REQUEST,
            detail=result.get("error") or "journal write failed",
        )
    try:
        sync = sync_vault()
        result["sync"] = {
            "files": sync.get("files"),
            "chunks_upserted": sync.get("chunks_upserted"),
        }
    except Exception:
        logger.exception("journal post-write sync failed")
        result["sync"] = {"error": "sync failed (entry persisted)"}
    return result


@app.post("/api/journal_prompt", dependencies=[Depends(verify_secret)])
@limiter.limit("10/minute")
async def journal_prompt(request: Request, req: JournalPromptRequest) -> dict[str, Any]:
    text = req.text or JOURNAL_PROMPT_TEXT
    if JOURNAL_PROMPT_MARKER not in text:
        text = f"{JOURNAL_PROMPT_MARKER}\n\n{text}"
    result = await telegram.send_message(
        text,
        chat_id=req.chat_id,
        reply_markup={"force_reply": True, "input_field_placeholder": "Tulis catatan hari ini…"},
    )
    if not result.get("ok"):
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, detail=result.get("error") or result)
    return result


@app.post("/api/system_status", dependencies=[Depends(verify_secret)])
async def system_status_endpoint() -> dict[str, Any]:
    return await system_status.collect_all()


@app.post("/api/vps_status", dependencies=[Depends(verify_secret)])
async def vps_status_endpoint() -> dict[str, Any]:
    return await vps_status.collect_all()


@app.post("/api/briefing", response_model=ChatResponse, dependencies=[Depends(verify_secret)])
@limiter.limit("10/minute")
async def briefing(request: Request, req: BriefingRequest | None = None) -> ChatResponse:
    return ChatResponse(response=await _build_summary(mode="morning"))


@app.post("/api/eod_summary", response_model=ChatResponse, dependencies=[Depends(verify_secret)])
@limiter.limit("10/minute")
async def eod_summary(request: Request, req: BriefingRequest | None = None) -> ChatResponse:
    return ChatResponse(response=await _build_summary(mode="eod"))


@app.post("/api/repos/projects", dependencies=[Depends(verify_secret)])
async def repo_projects() -> dict[str, Any]:
    return {"projects": code_repos.list_projects()}


@app.post("/api/repos/index", dependencies=[Depends(verify_secret)])
@limiter.limit("4/minute")
async def repo_index(request: Request, req: RepoIndexRequest) -> dict[str, Any]:
    import asyncio

    if req.repo == "all":
        results: list[dict[str, Any]] = []
        for project in code_repos.list_projects():
            if not project.get("enabled"):
                continue
            results.append(await asyncio.to_thread(code_repos.index_repo, project["id"]))
        return {"ok": all(r.get("ok") for r in results), "results": results}
    result = await asyncio.to_thread(code_repos.index_repo, req.repo)
    if not result.get("ok"):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=result)
    return result


@app.post("/api/repos/search", dependencies=[Depends(verify_secret)])
@limiter.limit("30/minute")
async def repo_search(request: Request, req: RepoSearchRequest) -> dict[str, Any]:
    hits = code_repos.search_code(req.query, repo_id=req.repo, limit=req.limit)
    return {"query": req.query, "repo": req.repo, "results": hits}


@app.post("/api/repos/ask", dependencies=[Depends(verify_secret)])
@limiter.limit("10/minute")
async def repo_ask(request: Request, req: RepoAskRequest) -> ChatResponse:
    answer = await code_repos.answer_code_question(req.question, repo_id=req.repo)
    return ChatResponse(response=answer)


@app.post("/api/resource_alert_check", dependencies=[Depends(verify_secret)])
@limiter.limit("12/minute")
async def resource_alert_check(request: Request) -> dict[str, Any]:
    return await resource_alerts.run_check()


class SkillLogRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1, max_length=2000)
    steps: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    trigger: str = ""
    user_id: str | int | None = None


class SkillSearchRequest(BaseModel):
    query: str = Field(..., min_length=1)
    limit: int = Field(5, ge=1, le=20)


@app.post("/api/skills/log", dependencies=[Depends(verify_secret)])
async def skill_log(req: SkillLogRequest) -> dict[str, Any]:
    point_id, status = skills.log_skill(
        name=req.name,
        description=req.description,
        steps=req.steps,
        tags=req.tags,
        trigger=req.trigger,
        user_id=req.user_id,
    )
    return {"id": point_id, "name": req.name, "status": status}


@app.post("/api/skills/search", dependencies=[Depends(verify_secret)])
async def skill_search(req: SkillSearchRequest) -> dict[str, Any]:
    hits = skills.search_skills(req.query, limit=req.limit)
    results = []
    for h in hits:
        p = h["payload"]
        results.append({
            "id": h["id"],
            "score": h["score"],
            "name": p.get("name", ""),
            "description": p.get("description", ""),
            "steps": p.get("steps", []),
            "tags": p.get("tags", []),
            "trigger": p.get("trigger", ""),
        })
    return {"query": req.query, "count": len(results), "results": results}


async def _build_summary(mode: str) -> str:
    events = await tools.get_today_schedule()
    pending = tools.list_pending_tasks(limit=10)

    lines: list[str] = []
    if mode == "morning":
        if events:
            lines.append("JADWAL HARI INI:")
            for e in events:
                lines.append(f"- {e.get('start', '?')} — {e.get('title', 'Untitled')}")
        else:
            lines.append("JADWAL HARI INI: (kosong)")
    else:
        if events:
            lines.append("JADWAL TADI:")
            for e in events:
                lines.append(f"- {e.get('start', '?')} — {e.get('title', 'Untitled')}")
        else:
            lines.append("JADWAL TADI: (tidak ada meeting)")

    lines.append("")
    if pending:
        lines.append("PENDING TASKS:")
        for t in pending:
            p = t["payload"]
            lines.append(f"- [{p.get('priority', 'medium')}] {p.get('title', 'Untitled')}")
    else:
        lines.append("PENDING TASKS: (kosong)")

    facts = "\n".join(lines)
    if mode == "morning":
        system_prompt = (
            "Kamu sekretaris pribadi yang efisien. Buat morning briefing dalam Bahasa Indonesia "
            "dari fakta yang diberikan. Format wajib:\n"
            "1. Greeting singkat (1 kalimat).\n"
            "2. Highlight jadwal hari ini — sebutkan jam paling penting.\n"
            "3. Maks 3 task yang harus diprioritaskan, dengan alasan singkat.\n"
            "4. Saran fokus utama hari ini (1 kalimat).\n"
            "Total maks 6-8 kalimat. Gunakan bullet untuk schedule + tasks. "
            "Jangan tambahkan disclaimer atau penjelasan tentang apa yang kamu lakukan."
        )
    else:
        system_prompt = (
            "Kamu sekretaris pribadi yang reflektif. Buat end-of-day summary dalam Bahasa Indonesia "
            "dari fakta yang diberikan. Format wajib:\n"
            "1. Refleksi singkat dari jadwal yang ada (1-2 kalimat, tanpa asumsi yang tidak ada datanya).\n"
            "2. Tasks yang masih pending — kelompokkan jika lebih dari 5.\n"
            "3. Saran prioritas untuk besok pagi (maks 2 item, dengan alasan).\n"
            "Total maks 6-8 kalimat. Tone tenang, tidak menggurui. "
            "Jangan menambahkan disclaimer."
        )

    try:
        reply = await llm.chat_completion(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": facts},
            ]
        )
    except Exception as exc:
        logger.warning("%s LLM error: %s", mode, exc)
        reply = facts

    return reply


# --- GitHub Webhook (Auto PR Review) ---


@app.post("/api/webhook/github")
async def github_webhook(request: Request, background_tasks: BackgroundTasks) -> dict[str, Any]:
    body = await request.body()
    signature = request.headers.get("X-Hub-Signature-256", "")

    if not pr_review.verify_webhook_signature(body, signature):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="invalid signature")

    event = request.headers.get("X-GitHub-Event", "")
    if event != "pull_request":
        return {"skipped": True, "reason": f"event={event} not handled"}

    import json
    payload = json.loads(body)
    background_tasks.add_task(pr_review.handle_pr_event, payload)
    return {"queued": True, "event": event}


@app.post("/api/webhook/gitlab")
async def gitlab_webhook(request: Request, background_tasks: BackgroundTasks) -> dict[str, Any]:
    token = request.headers.get("X-Gitlab-Token", "")

    if not gitlab_review.verify_webhook_token(token):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="invalid token")

    event = request.headers.get("X-Gitlab-Event", "")
    if event != "Merge Request Hook":
        return {"skipped": True, "reason": f"event={event} not handled"}

    import json
    body = await request.body()
    payload = json.loads(body)
    background_tasks.add_task(gitlab_review.handle_mr_event, payload)
    return {"queued": True, "event": event}


class ReviewPRRequest(BaseModel):
    repo: str = Field(..., min_length=1)
    pr_number: int = Field(..., ge=1)


@app.post("/api/review_pr", dependencies=[Depends(verify_secret)])
async def review_pr_on_demand(req: ReviewPRRequest) -> dict[str, Any]:
    repo = req.repo
    if ":" in repo:
        platform, full_name = repo.split(":", 1)
    else:
        platform, full_name = "github", repo
    return await pr_review.review_pr_on_demand(platform, full_name, req.pr_number)


class ReviewReposRequest(BaseModel):
    repos: list[str]


@app.get("/api/review/repos", dependencies=[Depends(verify_secret)])
async def get_review_repos() -> dict[str, Any]:
    return {"repos": pr_review.get_whitelist()}


@app.post("/api/review/repos", dependencies=[Depends(verify_secret)])
async def set_review_repos(req: ReviewReposRequest) -> dict[str, Any]:
    pr_review.set_whitelist(req.repos)
    return {"ok": True, "repos": req.repos}


# --- Test Coverage Agent ---


class CoverageScanRequest(BaseModel):
    repo: str = Field(..., min_length=1)
    branch: str = Field(default="main", min_length=1)
    min_coverage: float | None = Field(default=None, ge=0, le=100)


@app.post("/api/coverage/scan", dependencies=[Depends(verify_secret)])
async def coverage_scan(req: CoverageScanRequest) -> dict[str, Any]:
    return await test_coverage.scan_and_pr(req.repo, branch=req.branch, min_coverage=req.min_coverage)


class CoverageReposRequest(BaseModel):
    repos: list[str]


@app.get("/api/coverage/repos", dependencies=[Depends(verify_secret)])
async def get_coverage_repos() -> dict[str, Any]:
    return {"repos": test_coverage.get_whitelist()}


@app.post("/api/coverage/repos", dependencies=[Depends(verify_secret)])
async def set_coverage_repos(req: CoverageReposRequest) -> dict[str, Any]:
    test_coverage.set_whitelist(req.repos)
    return {"ok": True, "repos": req.repos}
