from __future__ import annotations

import logging
from typing import Any

from fastapi import Depends, FastAPI, HTTPException, Request, status
from pydantic import BaseModel, Field

from . import config, llm, system_status, telegram, tools, vps_status, workflow
from .qdrant_helper import ensure_payload_indexes
from .sync import sync_vault

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("agent")

app = FastAPI(title="pro-secretary agent", version="1.0.0")


@app.on_event("startup")
async def _on_startup() -> None:
    try:
        ensure_payload_indexes()
        logger.info("payload indexes ensured")
    except Exception as exc:
        logger.warning("payload index setup failed: %s", exc)


async def verify_secret(request: Request) -> None:
    if not config.AGENT_SECRET:
        return
    header = request.headers.get("x-agent-secret") or request.headers.get("authorization", "")
    token = header.removeprefix("Bearer ").strip()
    if token != config.AGENT_SECRET:
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


class TaskCreateRequest(BaseModel):
    title: str = Field(..., min_length=1)
    priority: str = "medium"
    due_date: str | None = None
    user_id: str | int | None = None


class TaskListRequest(BaseModel):
    limit: int = Field(20, ge=1, le=100)


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
async def chat(req: ChatRequest) -> ChatResponse:
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


@app.post("/api/note", dependencies=[Depends(verify_secret)])
async def note_create(req: NoteRequest) -> dict[str, Any]:
    note_id = tools.store_note(req.content, source=req.source, user_id=req.user_id)
    return {"id": note_id, "content": req.content}


@app.post("/api/schedule", dependencies=[Depends(verify_secret)])
async def schedule_today() -> dict[str, Any]:
    events = await tools.get_today_schedule()
    return {"count": len(events), "events": events}


@app.post("/api/sync_vault", dependencies=[Depends(verify_secret)])
async def sync_vault_endpoint(req: SyncVaultRequest) -> dict[str, Any]:
    try:
        result = sync_vault(req.vault_path)
    except Exception as exc:
        logger.exception("sync_vault failed")
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))
    return result


@app.post("/api/notify", dependencies=[Depends(verify_secret)])
async def notify_endpoint(req: NotifyRequest) -> dict[str, Any]:
    result = await telegram.send_message(req.text, chat_id=req.chat_id)
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
async def briefing(req: BriefingRequest) -> ChatResponse:
    return ChatResponse(response=await _build_summary(mode="morning"))


@app.post("/api/eod_summary", response_model=ChatResponse, dependencies=[Depends(verify_secret)])
async def eod_summary(req: BriefingRequest) -> ChatResponse:
    return ChatResponse(response=await _build_summary(mode="eod"))


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
