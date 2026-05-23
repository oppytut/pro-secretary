#!/usr/bin/env python3

import logging
import os
import tempfile
from pathlib import Path

import httpx
from telegram import BotCommand, Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ALLOWED_USERS = [int(x) for x in os.getenv("ALLOWED_USER_IDS", "").split(",") if x.strip()]
AGENT_URL = os.getenv("AGENT_URL", "http://langgraph-agent:8090").rstrip("/")
AGENT_SECRET = os.getenv("AGENT_SECRET", "")
LLM_MODEL_DEFAULT = os.getenv("LLM_MODEL", "gpt-4")

MAX_UPLOAD_BYTES = int(os.getenv("MAX_UPLOAD_BYTES", str(50 * 1024 * 1024)))
MAX_COMMAND_TEXT_LEN = int(os.getenv("MAX_COMMAND_TEXT_LEN", "2000"))
MAX_JOURNAL_LEN = int(os.getenv("MAX_JOURNAL_LEN", "5000"))

# Voice transcription config
WHISPER_API_BASE = os.getenv("WHISPER_API_BASE", os.getenv("LLM_BASE_URL", "")).rstrip("/")
WHISPER_API_KEY = os.getenv("WHISPER_API_KEY", os.getenv("LLM_API_KEY", ""))
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "whisper-1")
MAX_VOICE_DURATION_SEC = int(os.getenv("MAX_VOICE_DURATION_SEC", "300"))  # 5 min
JOURNAL_PROMPT_MARKER = "📓 Personal Journal"
ALLOWED_UPLOAD_EXTS = {
    "pdf", "txt", "md", "rtf",
    "docx", "doc", "xlsx", "xls", "csv", "pptx", "ppt",
    "jpg", "jpeg", "png", "gif", "webp", "heic",
    "json", "yaml", "yml", "html", "epub",
    "zip",
}

current_model = LLM_MODEL_DEFAULT

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def authorized(func):
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.effective_user.id not in ALLOWED_USERS:
            logger.warning(f"Unauthorized access attempt: {update.effective_user.id}")
            await update.message.reply_text("⛔ Unauthorized.")
            return
        return await func(update, context)

    return wrapper


def _agent_headers() -> dict[str, str]:
    if AGENT_SECRET:
        return {"x-agent-secret": AGENT_SECRET}
    return {}


async def _agent_post(path: str, payload: dict, timeout: float = 60.0) -> httpx.Response:
    async with httpx.AsyncClient(timeout=timeout) as client:
        return await client.post(
            f"{AGENT_URL}{path}",
            headers=_agent_headers(),
            json=payload,
        )


@authorized
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 AI Secretary Active\n\n"
        "Perintah tersedia:\n"
        "/jadwal - Lihat jadwal hari ini\n"
        "/task <judul> - Buat task baru\n"
        "/tasks - Lihat pending tasks\n"
        "/cari <query> - Cari di indexed code repos\n"
        "/cari di <repo> <query> - Cari di repo tertentu\n"
        "/catat <note> - Catat sesuatu\n"
        "/briefing - Daily briefing\n"
        "/eod - End-of-day summary\n"
        "/sync - Sync Obsidian vault\n"
        "/status - Cek status semua komponen\n"
        "/vps - Cek resource VPS\n"
        "/model - Ganti/lihat model AI\n"
        "/journal <isi> - Catat journal (atau reply pesan 21:30)\n"
        "/projects - Lihat repo yang ter-index\n"
        "/index <repo|all> - Re-index repo\n"
        "/tanya <pertanyaan> - Tanya tentang code di repo\n\n"
        "Atau kirim pesan biasa atau voice note untuk chat."
    )


@authorized
async def cmd_jadwal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_chat_action("typing")
    try:
        r = await _agent_post("/api/schedule", {}, timeout=30.0)
    except httpx.RequestError as exc:
        await update.message.reply_text(f"⚠️ Gagal menghubungi agent: {exc}")
        return

    if r.status_code != 200:
        await update.message.reply_text(f"⚠️ Gagal mengambil jadwal (HTTP {r.status_code}).")
        return

    data = r.json()
    events = data.get("events") or []
    if not events:
        await update.message.reply_text("📅 Tidak ada jadwal hari ini.")
        return

    lines = ["📅 Jadwal hari ini:"]
    for e in events:
        lines.append(f"• {e.get('start', '?')} — {e.get('title', 'Untitled')}")
    await update.message.reply_text("\n".join(lines))


@authorized
async def cmd_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_chat_action("typing")
    try:
        r = await _agent_post("/api/tasks", {"limit": 20}, timeout=30.0)
    except httpx.RequestError as exc:
        await update.message.reply_text(f"⚠️ Gagal menghubungi agent: {exc}")
        return

    if r.status_code != 200:
        await update.message.reply_text("⚠️ Gagal mengambil tasks.")
        return

    data = r.json()
    tasks = data.get("tasks") or []
    if not tasks:
        await update.message.reply_text("✅ Tidak ada pending tasks.")
        return

    lines = ["📋 Pending tasks:"]
    for t in tasks:
        p = t.get("payload", {})
        prio = p.get("priority", "medium")
        title = p.get("title", "Untitled")
        lines.append(f"• [{prio}] {title}")
    await update.message.reply_text("\n".join(lines))


@authorized
async def cmd_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Gunakan: /task <judul task>")
        return

    task_text = " ".join(context.args)
    if len(task_text) > MAX_COMMAND_TEXT_LEN:
        await update.message.reply_text(
            f"⚠️ Terlalu panjang ({len(task_text)} karakter). Maks {MAX_COMMAND_TEXT_LEN}."
        )
        return
    await update.message.reply_chat_action("typing")
    try:
        r = await _agent_post(
            "/api/task",
            {"title": task_text, "user_id": update.effective_user.id},
            timeout=30.0,
        )
    except httpx.RequestError as exc:
        await update.message.reply_text(f"⚠️ Gagal menghubungi agent: {exc}")
        return

    if r.status_code == 200:
        await update.message.reply_text(f"✅ Task ditambahkan: {task_text}")
    else:
        await update.message.reply_text(f"⚠️ Gagal membuat task (HTTP {r.status_code}).")


@authorized
async def cmd_cari(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Gunakan: /cari <kata kunci>")
        return

    raw = " ".join(context.args)
    repo = None
    query = raw
    if len(context.args) >= 3 and context.args[0].lower() == "di":
        repo = context.args[1]
        query = " ".join(context.args[2:])
    if len(query) > MAX_COMMAND_TEXT_LEN:
        await update.message.reply_text(
            f"⚠️ Query terlalu panjang ({len(query)}). Maks {MAX_COMMAND_TEXT_LEN}."
        )
        return
    await update.message.reply_chat_action("typing")
    try:
        r = await _agent_post(
            "/api/repos/search",
            {"query": query, "repo": repo, "limit": 8},
            timeout=45.0,
        )
    except httpx.RequestError as exc:
        await update.message.reply_text(f"⚠️ Gagal menghubungi agent: {exc}")
        return

    if r.status_code != 200:
        await update.message.reply_text(f"⚠️ Gagal mencari (HTTP {r.status_code}).")
        return

    results = r.json().get("results") or []
    if not results:
        await update.message.reply_text(f"Tidak ditemukan hasil untuk: {query}")
        return

    text = f"🔍 Hasil pencarian: {query}\n\n"
    for i, item in enumerate(results, 1):
        payload = item.get("payload", {})
        content = (item.get("content") or payload.get("text") or "")[:220]
        source = item.get("source_file") or payload.get("path") or "unknown"
        if payload.get("repo_id"):
            source = (
                f"{payload.get('repo_id')}:{source}:"
                f"{payload.get('start_line')}-{payload.get('end_line')}@"
                f"{str(payload.get('commit') or '')[:8]}"
            )
        text += f"{i}. {content}...\n   📎 {source}\n\n"
    await update.message.reply_text(text[:4000])


@authorized
async def cmd_catat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Gunakan: /catat <isi catatan>")
        return

    note = " ".join(context.args)
    if len(note) > MAX_COMMAND_TEXT_LEN:
        await update.message.reply_text(
            f"⚠️ Catatan terlalu panjang ({len(note)}). Maks {MAX_COMMAND_TEXT_LEN}."
        )
        return
    await update.message.reply_chat_action("typing")
    try:
        r = await _agent_post(
            "/api/note",
            {
                "content": note,
                "source": "telegram",
                "user_id": update.effective_user.id,
            },
            timeout=30.0,
        )
    except httpx.RequestError as exc:
        await update.message.reply_text(f"⚠️ Gagal menghubungi agent: {exc}")
        return

    if r.status_code == 200:
        await update.message.reply_text(f"📝 Dicatat: {note}")
    else:
        await update.message.reply_text(f"⚠️ Gagal mencatat (HTTP {r.status_code}).")


@authorized
async def cmd_briefing(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⏳ Menyiapkan briefing...")
    try:
        r = await _agent_post(
            "/api/briefing",
            {"user_id": update.effective_user.id},
            timeout=90.0,
        )
    except httpx.RequestError as exc:
        await update.message.reply_text(f"⚠️ Gagal menghubungi agent: {exc}")
        return

    if r.status_code == 200:
        await update.message.reply_text(r.json().get("response", "Briefing kosong."))
    else:
        await update.message.reply_text(f"⚠️ Gagal membuat briefing (HTTP {r.status_code}).")


@authorized
async def cmd_eod(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⏳ Menyiapkan EOD summary...")
    try:
        r = await _agent_post(
            "/api/eod_summary",
            {"user_id": update.effective_user.id},
            timeout=90.0,
        )
    except httpx.RequestError as exc:
        await update.message.reply_text(f"⚠️ Gagal menghubungi agent: {exc}")
        return

    if r.status_code == 200:
        await update.message.reply_text(r.json().get("response", "EOD summary kosong."))
    else:
        await update.message.reply_text(f"⚠️ Gagal membuat EOD summary (HTTP {r.status_code}).")


@authorized
async def cmd_sync(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⏳ Sync Obsidian vault...")
    try:
        r = await _agent_post("/api/sync_vault", {}, timeout=120.0)
    except httpx.RequestError as exc:
        await update.message.reply_text(f"⚠️ Gagal menghubungi agent: {exc}")
        return

    if r.status_code != 200:
        await update.message.reply_text(f"⚠️ Sync gagal (HTTP {r.status_code}).")
        return

    data = r.json()
    files = data.get("files", 0)
    upserted = data.get("chunks_upserted", 0)
    deleted = data.get("chunks_deleted", 0)
    await update.message.reply_text(
        f"✅ Sync selesai\n"
        f"• Files: {files}\n"
        f"• Chunks upserted: {upserted}\n"
        f"• Chunks deleted (orphans): {deleted}"
    )


@authorized
async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_chat_action("typing")
    try:
        r = await _agent_post("/api/system_status", {}, timeout=30.0)
    except httpx.RequestError as exc:
        await update.message.reply_text(f"⚠️ Gagal menghubungi agent: {exc}")
        return

    if r.status_code != 200:
        await update.message.reply_text(f"⚠️ Status check gagal (HTTP {r.status_code}).")
        return

    data = r.json()
    checks = data.get("checks", [])
    failed = data.get("failed", 0)
    total = data.get("total", 0)

    lines = ["🏥 System Status", ""]
    for c in checks:
        icon = "✅" if c["ok"] else "❌"
        lat = f"{c['latency_ms']}ms"
        detail = c.get("detail", "")
        lines.append(f"{icon} {c['name']} ({lat}) — {detail}")

    if failed == 0:
        lines.append("")
        lines.append("✅ Semua sistem operasional")
    else:
        lines.append("")
        lines.append(f"⚠️ {failed}/{total} system bermasalah")

    await update.message.reply_text("\n".join(lines))


def _human_bytes(n: int | None) -> str:
    if n is None:
        return "-"
    units = ["B", "KB", "MB", "GB", "TB"]
    f = float(n)
    for u in units:
        if f < 1024 or u == "TB":
            return f"{f:.1f}{u}" if u != "B" else f"{int(f)}B"
        f /= 1024
    return f"{f:.1f}TB"


def _human_uptime(seconds: float | None) -> str:
    if not seconds:
        return "-"
    s = int(seconds)
    d, s = divmod(s, 86400)
    h, s = divmod(s, 3600)
    m, _ = divmod(s, 60)
    if d > 0:
        return f"{d}d {h}h"
    if h > 0:
        return f"{h}h {m}m"
    return f"{m}m"


@authorized
async def cmd_vps(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_chat_action("typing")
    try:
        r = await _agent_post("/api/vps_status", {}, timeout=30.0)
    except httpx.RequestError as exc:
        await update.message.reply_text(f"⚠️ Gagal menghubungi agent: {exc}")
        return

    if r.status_code != 200:
        await update.message.reply_text(f"⚠️ VPS status gagal (HTTP {r.status_code}).")
        return

    data = r.json()
    host = data.get("host", {})
    disks = data.get("disks", [])
    containers = data.get("containers", [])

    lines = ["🖥️ VPS Resources", ""]

    cpu = host.get("cpu_pct")
    load = host.get("load") or [None, None, None]
    cpu_str = f"{cpu}%" if cpu is not None else "-"
    load_str = " / ".join(f"{x:.2f}" if x is not None else "-" for x in load)
    lines.append(f"CPU: {cpu_str}  (load {load_str})")

    mem_used = host.get("mem_used_bytes")
    mem_total = host.get("mem_total_bytes")
    mem_pct = host.get("mem_pct")
    swap_used = host.get("swap_used_bytes")
    swap_total = host.get("swap_total_bytes")
    lines.append(
        f"RAM: {_human_bytes(mem_used)} / {_human_bytes(mem_total)} "
        f"({mem_pct}%, swap {_human_bytes(swap_used)} / {_human_bytes(swap_total)})"
    )

    for d in disks:
        if not d.get("ok"):
            continue
        path = d["path"].replace("/host", "")
        lines.append(
            f"Disk {path}: {_human_bytes(d['used_bytes'])} / {_human_bytes(d['total_bytes'])} ({d['pct']}%)"
        )

    lines.append(f"Uptime: {_human_uptime(host.get('uptime_seconds'))}")

    if containers:
        lines.append("")
        lines.append("Per Container:")
        for c in containers:
            if not c.get("ok"):
                continue
            cpu_c = c.get("cpu_pct")
            cpu_str = f"{cpu_c}%" if cpu_c is not None else "-"
            mem_str = f"{_human_bytes(c.get('mem_used_bytes'))}"
            limit = c.get("mem_limit_bytes")
            if limit:
                mem_str += f" / {_human_bytes(limit)} ({c.get('mem_pct')}%)"
            lines.append(f"• {c['name']}: CPU {cpu_str}, RAM {mem_str}")

    await update.message.reply_text("\n".join(lines))


@authorized
async def cmd_model(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global current_model
    if not context.args:
        await update.message.reply_text(
            f"🤖 Model aktif: {current_model}\n\n"
            f"Gunakan: /model <nama_model>\n\n"
            f"Contoh:\n"
            f"/model gpt-4o\n"
            f"/model gpt-3.5-turbo\n"
            f"/model claude-3.5-sonnet\n"
            f"/model llama-3.1-70b-versatile"
        )
        return

    new_model = " ".join(context.args)
    current_model = new_model
    await update.message.reply_text(f"✅ Model diganti ke: {current_model}")
    logger.info(f"Model switched to: {current_model}")


async def _submit_journal(update: Update, text: str) -> None:
    text = text.strip()
    if not text:
        await update.message.reply_text("Gunakan: /journal <isi catatan>")
        return
    if len(text) > MAX_JOURNAL_LEN:
        await update.message.reply_text(
            f"⚠️ Catatan terlalu panjang ({len(text)} karakter). Maks {MAX_JOURNAL_LEN}."
        )
        return

    await update.message.reply_chat_action("typing")
    try:
        r = await _agent_post(
            "/api/journal",
            {"text": text, "user_id": update.effective_user.id},
            timeout=120.0,
        )
    except httpx.RequestError as exc:
        await update.message.reply_text(f"⚠️ Gagal menghubungi agent: {exc}")
        return

    if r.status_code != 200:
        await update.message.reply_text(f"⚠️ Gagal menyimpan journal (HTTP {r.status_code}).")
        return

    data = r.json()
    file_path = data.get("file", "journal")
    sync = data.get("sync") or {}
    chunks = sync.get("chunks_upserted")
    suffix = f" · indexed ({chunks} chunks)" if chunks else ""
    await update.message.reply_text(f"📓 Tercatat di {file_path}{suffix}.")


@authorized
async def cmd_journal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = " ".join(context.args) if context.args else ""
    await _submit_journal(update, text)


@authorized
async def cmd_projects(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_chat_action("typing")
    try:
        r = await _agent_post("/api/repos/projects", {}, timeout=20.0)
    except httpx.RequestError as exc:
        await update.message.reply_text(f"⚠️ Gagal menghubungi agent: {exc}")
        return
    if r.status_code != 200:
        await update.message.reply_text(f"⚠️ Gagal mengambil projects (HTTP {r.status_code}).")
        return
    projects = r.json().get("projects") or []
    if not projects:
        await update.message.reply_text("Belum ada repo terdaftar di repos.yml.")
        return
    lines = ["📦 Projects:", ""]
    for p in projects:
        sha = (p.get("indexed_commit") or "-")[:8]
        chunks = p.get("chunks", 0)
        flag = "✅" if p.get("enabled") else "⏸️"
        aliases = p.get("aliases") or []
        alias_text = f" alias: {', '.join(aliases)}" if aliases else ""
        lines.append(
            f"{flag} {p['id']} ({p.get('provider')}/{p.get('branch')}) — {chunks} chunks @ {sha}{alias_text}"
        )
    await update.message.reply_text("\n".join(lines))


@authorized
async def cmd_index(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Gunakan: /index <repo|all>")
        return
    repo = context.args[0]
    await update.message.reply_text(f"⏳ Indexing {repo}...")
    try:
        r = await _agent_post("/api/repos/index", {"repo": repo}, timeout=900.0)
    except httpx.RequestError as exc:
        await update.message.reply_text(f"⚠️ Gagal menghubungi agent: {exc}")
        return
    if r.status_code != 200:
        await update.message.reply_text(
            f"⚠️ Index gagal (HTTP {r.status_code}): {r.text[:300]}"
        )
        return
    data = r.json()
    if "results" in data:
        lines = ["📦 Index all selesai:"]
        for item in data["results"]:
            if item.get("ok"):
                lines.append(
                    f"• {item['repo_id']}: {item['chunks']} chunks @ {item['short_commit']} ({item['duration_seconds']}s)"
                )
            else:
                lines.append(f"• {item.get('repo_id', '?')}: ❌ {item.get('error', 'failed')}")
        await update.message.reply_text("\n".join(lines))
        return
    if not data.get("ok"):
        await update.message.reply_text(f"⚠️ Index gagal: {data.get('error', 'unknown')}")
        return
    await update.message.reply_text(
        f"✅ {data['repo_id']}: {data['chunks']} chunks dari {data['files']} file "
        f"@ {data['short_commit']} ({data['duration_seconds']}s)"
    )


@authorized
async def cmd_tanya(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "Gunakan: /tanya <pertanyaan>\nAtau: /tanya di <repo> <pertanyaan>"
        )
        return
    repo = None
    args = list(context.args)
    if len(args) >= 3 and args[0].lower() == "di":
        repo = args[1]
        args = args[2:]
    question = " ".join(args)
    if len(question) > MAX_COMMAND_TEXT_LEN:
        await update.message.reply_text(
            f"⚠️ Pertanyaan terlalu panjang ({len(question)}). Maks {MAX_COMMAND_TEXT_LEN}."
        )
        return
    await update.message.reply_chat_action("typing")
    try:
        r = await _agent_post(
            "/api/repos/ask",
            {"question": question, "repo": repo},
            timeout=120.0,
        )
    except httpx.RequestError as exc:
        await update.message.reply_text(f"⚠️ Gagal menghubungi agent: {exc}")
        return
    if r.status_code != 200:
        await update.message.reply_text(f"⚠️ Tanya gagal (HTTP {r.status_code}).")
        return
    answer = r.json().get("response", "(jawaban kosong)")
    await update.message.reply_text(answer[:4000])


def _is_journal_reply(update: Update) -> bool:
    reply = update.message.reply_to_message if update.message else None
    if not reply or not reply.text:
        return False
    return JOURNAL_PROMPT_MARKER in reply.text


@authorized
async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    voice = update.message.voice

    if voice.duration and voice.duration > MAX_VOICE_DURATION_SEC:
        await update.message.reply_text(
            f"⚠️ Voice terlalu panjang ({voice.duration}s). Maks {MAX_VOICE_DURATION_SEC}s."
        )
        return

    if not WHISPER_API_BASE or not WHISPER_API_KEY:
        await update.message.reply_text("⚠️ Transcription belum dikonfigurasi (WHISPER_API_BASE/KEY).")
        return

    await update.message.reply_chat_action("typing")

    tmp_path: Path | None = None
    try:
        tg_file = await voice.get_file()
        with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as tmp:
            tmp_path = Path(tmp.name)
        await tg_file.download_to_drive(custom_path=tmp_path)

        transcript = await _transcribe_voice(tmp_path)
        if not transcript:
            await update.message.reply_text("⚠️ Tidak dapat mentranskrip voice (kosong).")
            return

        r = await _agent_post(
            "/api/chat",
            {
                "message": transcript,
                "user_id": str(update.effective_user.id),
                "model": current_model,
            },
            timeout=90.0,
        )

        if r.status_code == 200:
            reply = r.json().get("response") or "(respons kosong)"
        else:
            reply = f"⚠️ Error dari agent (HTTP {r.status_code})."

        prefix = f"🎙️ \"{transcript[:120]}{'…' if len(transcript) > 120 else ''}\"\n\n"
        await update.message.reply_text(prefix + reply)

    except httpx.RequestError as exc:
        await update.message.reply_text(f"⚠️ Gagal menghubungi agent: {exc}")
    except Exception as exc:
        logger.exception("Voice handler error")
        await update.message.reply_text(f"⚠️ Gagal memproses voice: {type(exc).__name__}")
    finally:
        if tmp_path and tmp_path.exists():
            tmp_path.unlink(missing_ok=True)


async def _transcribe_voice(path: Path) -> str:
    url = f"{WHISPER_API_BASE}/v1/audio/transcriptions"
    async with httpx.AsyncClient(timeout=60.0) as client:
        with open(path, "rb") as f:
            resp = await client.post(
                url,
                headers={"Authorization": f"Bearer {WHISPER_API_KEY}"},
                data={"model": WHISPER_MODEL, "response_format": "json"},
                files={"file": (path.name, f, "audio/ogg")},
            )
    resp.raise_for_status()
    return (resp.json().get("text") or "").strip()


@authorized
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if _is_journal_reply(update):
        await _submit_journal(update, update.message.text or "")
        return

    user_message = update.message.text
    await update.message.reply_chat_action("typing")

    try:
        r = await _agent_post(
            "/api/chat",
            {
                "message": user_message,
                "user_id": str(update.effective_user.id),
                "model": current_model,
            },
            timeout=90.0,
        )
    except httpx.RequestError as exc:
        await update.message.reply_text(f"⚠️ Gagal menghubungi agent: {exc}")
        return

    if r.status_code == 200:
        reply = r.json().get("response") or "(respons kosong)"
    else:
        reply = f"⚠️ Error dari agent (HTTP {r.status_code})."
    await update.message.reply_text(reply)


@authorized
async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    import re
    import boto3
    from io import BytesIO

    document = update.message.document

    if document.file_size and document.file_size > MAX_UPLOAD_BYTES:
        await update.message.reply_text(
            f"⚠️ File terlalu besar ({document.file_size // 1024 // 1024} MB). "
            f"Maks {MAX_UPLOAD_BYTES // 1024 // 1024} MB."
        )
        return

    raw_name = document.file_name or f"upload-{document.file_unique_id}"
    safe_name = re.sub(r"[^A-Za-z0-9._-]", "_", raw_name).strip("._")[:120] or "upload"

    ext = safe_name.rsplit(".", 1)[-1].lower() if "." in safe_name else ""
    if ext and ext not in ALLOWED_UPLOAD_EXTS:
        await update.message.reply_text(
            f"⚠️ Ekstensi .{ext} tidak diizinkan. "
            f"Diizinkan: {', '.join(sorted(ALLOWED_UPLOAD_EXTS))}"
        )
        return

    file = await context.bot.get_file(document.file_id)
    file_bytes = await file.download_as_bytearray()

    if len(file_bytes) > MAX_UPLOAD_BYTES:
        await update.message.reply_text("⚠️ File melebihi limit setelah download.")
        return

    s3 = boto3.client(
        "s3",
        endpoint_url=os.getenv("R2_ENDPOINT"),
        aws_access_key_id=os.getenv("R2_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("R2_SECRET_ACCESS_KEY"),
        region_name="auto",
    )

    key = f"telegram-uploads/{safe_name}"
    s3.upload_fileobj(
        BytesIO(file_bytes),
        os.getenv("R2_BUCKET", "secretary-files"),
        key,
    )

    await update.message.reply_text(f"📁 File '{safe_name}' disimpan ke storage.")


async def post_init(application: Application):
    commands = [
        BotCommand("start", "Mulai bot"),
        BotCommand("jadwal", "Lihat jadwal hari ini"),
        BotCommand("task", "Buat task baru"),
        BotCommand("tasks", "Lihat pending tasks"),
        BotCommand("cari", "Cari di knowledge base"),
        BotCommand("catat", "Catat sesuatu"),
        BotCommand("briefing", "Daily briefing"),
        BotCommand("eod", "End-of-day summary"),
        BotCommand("sync", "Sync Obsidian vault → knowledge"),
        BotCommand("status", "Cek status semua komponen"),
        BotCommand("vps", "Cek resource VPS"),
        BotCommand("model", "Ganti/lihat model AI"),
        BotCommand("journal", "Catat journal harian"),
        BotCommand("projects", "Lihat repo terdaftar"),
        BotCommand("index", "Re-index repo (atau all)"),
        BotCommand("tanya", "Tanya tentang code di repo"),
    ]
    await application.bot.set_my_commands(commands)
    logger.info("Bot commands registered.")


def main():
    if not BOT_TOKEN:
        raise RuntimeError("TELEGRAM_BOT_TOKEN not set")
    if not ALLOWED_USERS:
        raise RuntimeError("ALLOWED_USER_IDS not set")

    app = Application.builder().token(BOT_TOKEN).post_init(post_init).build()

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("jadwal", cmd_jadwal))
    app.add_handler(CommandHandler("task", cmd_task))
    app.add_handler(CommandHandler("tasks", cmd_tasks))
    app.add_handler(CommandHandler("cari", cmd_cari))
    app.add_handler(CommandHandler("catat", cmd_catat))
    app.add_handler(CommandHandler("briefing", cmd_briefing))
    app.add_handler(CommandHandler("eod", cmd_eod))
    app.add_handler(CommandHandler("sync", cmd_sync))
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(CommandHandler("vps", cmd_vps))
    app.add_handler(CommandHandler("model", cmd_model))
    app.add_handler(CommandHandler("journal", cmd_journal))
    app.add_handler(CommandHandler("projects", cmd_projects))
    app.add_handler(CommandHandler("index", cmd_index))
    app.add_handler(CommandHandler("tanya", cmd_tanya))
    app.add_handler(MessageHandler(filters.VOICE, handle_voice))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))

    logger.info(
        f"Secretary Bot starting (agent={AGENT_URL}, allowed={ALLOWED_USERS})"
    )
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
