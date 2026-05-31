#!/usr/bin/env python3

import logging
import os
import tempfile
from datetime import datetime, timedelta, time as _time
from pathlib import Path
from zoneinfo import ZoneInfo

import httpx
from telegram import BotCommand, InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from watchdogs.dns import (
    DNS_CHECK_ENABLED,
    DNS_CHECK_INTERVAL_SEC,
    cmd_dns,
    dns_check_job,
    get_dns_domains,
)
from watchdogs.ssl import (
    SSL_CHECK_ENABLED,
    cmd_ssl,
    get_ssl_domains,
    ssl_check_job,
)
from watchdogs.deps import (
    DEPS_CHECK_ENABLED,
    DEPS_CHECK_HOUR,
    DEPS_CHECK_MINUTE,
    cmd_deps,
    deps_check_job,
)
from watchdogs.capacity import (
    CAPACITY_CHECK_ENABLED,
    CAPACITY_CHECK_HOUR,
    CAPACITY_CHECK_MINUTE,
    capacity_check_job,
    cmd_capacity,
)
from watchdogs.drift import (
    DRIFT_CHECK_ENABLED,
    DRIFT_CHECK_HOUR,
    DRIFT_CHECK_MINUTE,
    cmd_drift,
    drift_check_job,
)
from infra.ssh import (
    add_ssh_target as _add_ssh_target,
    del_ssh_target as _del_ssh_target,
    get_ssh_targets as _get_ssh_targets,
    ssh_exec as _ssh_exec,
)
from infra.prom import prom_query as _prom_query
from infra.agent import agent_post as _agent_post
from watchdogs.hygiene import (
    DOCKER_HYGIENE_ENABLED,
    DOCKER_HYGIENE_HOUR,
    DOCKER_HYGIENE_MINUTE,
    cmd_hygiene,
    docker_hygiene_job,
)
from watchdogs.firewall import (
    FIREWALL_AUDIT_ENABLED,
    FIREWALL_AUDIT_HOUR,
    FIREWALL_AUDIT_MINUTE,
    cmd_firewall,
    firewall_audit_job,
)
from watchdogs.morning_brief import (
    MORNING_BRIEF_ENABLED,
    MORNING_BRIEF_HOUR,
    MORNING_BRIEF_MINUTE,
    cmd_briefing,
    morning_brief_job,
)
from watchdogs.test_coverage import (
    COVERAGE_AGENT_ENABLED,
    COVERAGE_AGENT_HOUR,
    COVERAGE_AGENT_MINUTE,
    cmd_coverage,
    coverage_scan_job,
)

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ALLOWED_USERS = [int(x) for x in os.getenv("ALLOWED_USER_IDS", "").split(",") if x.strip()]
AGENT_URL = os.getenv("AGENT_URL", "http://langgraph-agent:8090").rstrip("/")
AGENT_SECRET = os.getenv("AGENT_SECRET", "")
AGENT_HOST = os.getenv("AGENT_HOST", "").strip()
GH_WEBHOOK_SECRET = os.getenv("GH_WEBHOOK_SECRET", "")
GITLAB_WEBHOOK_SECRET = os.getenv("GITLAB_WEBHOOK_SECRET", "")
PROMETHEUS_URL = os.getenv("PROMETHEUS_URL", "http://prometheus:9090").rstrip("/")
LLM_MODEL_DEFAULT = os.getenv("LLM_MODEL", "gpt-4")

import asyncio
import json as _json

MAX_UPLOAD_BYTES = int(os.getenv("MAX_UPLOAD_BYTES", str(50 * 1024 * 1024)))
MAX_COMMAND_TEXT_LEN = int(os.getenv("MAX_COMMAND_TEXT_LEN", "2000"))
MAX_JOURNAL_LEN = int(os.getenv("MAX_JOURNAL_LEN", "5000"))

# Voice transcription config
WHISPER_API_BASE = os.getenv("WHISPER_API_BASE", os.getenv("LLM_BASE_URL", "")).rstrip("/")
WHISPER_API_KEY = os.getenv("WHISPER_API_KEY", os.getenv("LLM_API_KEY", ""))
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "whisper-1")
MAX_VOICE_DURATION_SEC = int(os.getenv("MAX_VOICE_DURATION_SEC", "300"))  # 5 min

REPO_NAMES: list[str] = []
REPO_ALIASES: dict[str, str] = {}
JOURNAL_PROMPT_MARKER = "📓 Personal Journal"
ALLOWED_UPLOAD_EXTS = {
    "pdf", "txt", "md", "rtf",
    "docx", "doc", "xlsx", "xls", "csv", "pptx", "ppt",
    "jpg", "jpeg", "png", "gif", "webp", "heic",
    "json", "yaml", "yml", "html", "epub",
    "zip",
}

current_model = LLM_MODEL_DEFAULT

MAX_SKILL_AUTOLOGS_PER_DAY = 5
MIN_HISTORY_FOR_SKILL_OFFER = 6  # 3 user + 3 bot messages
MIN_REPLY_LEN_FOR_SKILL = 100

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


async def _load_repo_names():
    global REPO_NAMES, REPO_ALIASES
    try:
        r = await _agent_post("/api/repos/projects", {}, timeout=10.0)
        if r.status_code == 200:
            projects = r.json().get("projects") or []
            for p in projects:
                repo_id = p.get("id", "")
                if repo_id:
                    REPO_NAMES.append(repo_id)
                    REPO_ALIASES[repo_id.lower()] = repo_id
                for alias in p.get("aliases") or []:
                    REPO_ALIASES[alias.lower()] = repo_id
            logger.info(f"Loaded repo names for voice hint: {REPO_NAMES}")
    except Exception as exc:
        logger.warning(f"Failed to load repo names: {exc}")


def _whisper_prompt() -> str:
    if not REPO_NAMES:
        return ""
    return "Project names: " + ", ".join(REPO_NAMES) + ". "


def _detect_repo_intent(text: str) -> tuple[str | None, str]:
    lower = text.lower().strip()
    if lower.startswith("di "):
        parts = lower.split(None, 2)
        if len(parts) >= 2:
            candidate = parts[1].rstrip(",.")
            if candidate in REPO_ALIASES:
                question = parts[2] if len(parts) > 2 else ""
                return REPO_ALIASES[candidate], question
    for token in lower.split():
        clean = token.rstrip(",.")
        if clean in REPO_ALIASES:
            question = text
            return REPO_ALIASES[clean], question
    return None, text


@authorized
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 AI Secretary Active\n\n"
        "Ketik /menu untuk lihat semua fitur.\n"
        "Atau kirim pesan biasa / voice note untuk chat."
    )


@authorized
async def cmd_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📅 Jadwal", callback_data="menu:jadwal"),
         InlineKeyboardButton("✅ Task", callback_data="menu:task"),
         InlineKeyboardButton("📋 Tasks", callback_data="menu:tasks")],
        [InlineKeyboardButton("📝 Catat", callback_data="menu:catat"),
         InlineKeyboardButton("📓 Journal", callback_data="menu:journal"),
         InlineKeyboardButton("🔍 Cari", callback_data="menu:cari")],
        [InlineKeyboardButton("💬 Tanya", callback_data="menu:tanya"),
         InlineKeyboardButton("📂 Projects", callback_data="menu:projects"),
         InlineKeyboardButton("🔄 Index", callback_data="menu:index")],
        [InlineKeyboardButton("🖥️ Monitor", callback_data="menu:monitor"),
         InlineKeyboardButton("📊 VPS", callback_data="menu:vps"),
         InlineKeyboardButton("🔌 Status", callback_data="menu:status")],
        [InlineKeyboardButton("☀️ Briefing", callback_data="menu:briefing"),
         InlineKeyboardButton("🌙 EOD", callback_data="menu:eod"),
         InlineKeyboardButton("🤖 Model", callback_data="menu:model")],
        [InlineKeyboardButton("🧠 Skill", callback_data="menu:skill"),
         InlineKeyboardButton("☁️ Sync", callback_data="menu:sync"),
         InlineKeyboardButton("❓ Help", callback_data="menu:help")],
        [InlineKeyboardButton("📈 Capacity", callback_data="menu:capacity"),
         InlineKeyboardButton("🔍 Review", callback_data="menu:review"),
         InlineKeyboardButton("🔒 SSL", callback_data="menu:ssl")],
    ]
    await update.message.reply_text(
        "📋 <b>Menu</b>\n\n"
        "📅 <b>Produktivitas</b> — Jadwal, Task, Tasks\n"
        "📝 <b>Catatan</b> — Catat, Journal, Cari\n"
        "💻 <b>Developer</b> — Tanya, Projects, Index, Review\n"
        "🖥️ <b>Infra</b> — Monitor, VPS, Status, Capacity, SSL\n"
        "⚙️ <b>Lainnya</b> — Briefing, EOD, Model, Skill, Sync\n\n"
        "Tap tombol di bawah atau ketik command langsung.",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML",
    )


_MENU_HANDLERS: dict[str, str] = {
    "jadwal": "cmd_jadwal", "task": "cmd_task", "tasks": "cmd_tasks",
    "catat": "cmd_catat", "journal": "cmd_journal", "cari": "cmd_cari",
    "tanya": "cmd_tanya", "projects": "cmd_projects", "index": "cmd_index",
    "monitor": "cmd_monitor", "vps": "cmd_vps", "status": "cmd_status",
    "briefing": "cmd_briefing", "eod": "cmd_eod", "model": "cmd_model",
    "skill": "cmd_skill", "sync": "cmd_sync",
}


async def handle_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    cmd_name = query.data.replace("menu:", "")

    if cmd_name in ("task", "catat", "journal", "cari", "tanya", "index", "skill", "meeting"):
        await query.message.reply_text(f"Ketik: /{cmd_name} <isi>")
        return

    if cmd_name == "review":
        await query.message.reply_text(
            "🔍 <b>Auto PR/MR Review</b>\n\n"
            "• /review list — Lihat repo yang di-review\n"
            "• /review add github:owner/repo — Tambah repo\n"
            "• /review add gitlab:owner/repo — Tambah GitLab repo\n"
            "• /review del github:owner/repo — Hapus repo\n"
            "• /review owner/repo#123 — Review on-demand",
            parse_mode="HTML",
        )
        return

    if cmd_name == "capacity":
        await query.message.reply_text("📈 Ketik: /capacity")
        return

    if cmd_name == "ssl":
        await query.message.reply_text(
            "🔒 <b>SSL Watchdog</b>\n\n"
            "• /ssl — Cek semua cert\n"
            "• /ssl list — Lihat domain\n"
            "• /ssl add domain.com — Tambah domain\n"
            "• /ssl del domain.com — Hapus domain",
            parse_mode="HTML",
        )
        return

    if cmd_name == "help":
        await query.message.reply_text(
            "❓ <b>Help</b>\n\n"
            "📅 <b>Produktivitas</b>\n"
            "• /jadwal — Lihat jadwal hari ini dari Cal.com\n"
            "• /task &lt;judul&gt; — Buat task baru\n"
            "• /tasks — Lihat semua pending tasks\n"
            "• /briefing — Ringkasan pagi (jadwal + tasks)\n"
            "• /eod — End-of-day summary\n\n"
            "📝 <b>Catatan</b>\n"
            "• /catat &lt;note&gt; — Simpan catatan cepat\n"
            "• /journal &lt;isi&gt; — Tulis journal harian\n"
            "• /meeting &lt;transkrip&gt; — Extract action items dari catatan rapat\n"
            "• /cari &lt;query&gt; — Cari di knowledge base\n\n"
            "💻 <b>Developer</b>\n"
            "• /tanya &lt;pertanyaan&gt; — Tanya tentang code di repo\n"
            "• /projects — Lihat repo yang ter-index\n"
            "• /index &lt;repo|all&gt; — Re-index repo\n"
            "• /skill &lt;query&gt; — Simpan/cari skill\n"
            "• /review — Auto PR/MR review (add/del/list)\n\n"
            "🖥️ <b>Infra</b>\n"
            "• /monitor [nama] — Monitor VPS + containers\n"
            "• /vps — Resource VPS lokal (CPU/RAM/disk)\n"
            "• /status — Status semua komponen stack\n"
            "• /capacity — Forecast disk/RAM exhaustion\n"
            "• /drift — Config drift check\n"
            "• /ssl — SSL cert expiry check\n"
            "• /dns — DNS resolver consistency check\n"
            "• /hygiene — Docker image hygiene + reclaimable size\n"
            "• /firewall — Audit unauthorized public ports\n\n"
            "⚙️ <b>Settings</b>\n"
            "• /model [nama] — Ganti/lihat model AI\n"
            "• /sync — Sync Obsidian vault\n\n"
            "💡 Tip: kirim pesan biasa atau voice note untuk chat langsung.",
            parse_mode="HTML",
        )
        return

    handler_name = _MENU_HANDLERS.get(cmd_name)
    if not handler_name:
        return
    handler_fn = globals().get(handler_name)
    if not handler_fn:
        return

    class _FakeUpdate:
        def __init__(self, msg, user):
            self.message = msg
            self.effective_user = user
    
    fake = _FakeUpdate(query.message, update.effective_user)
    context.args = []
    await handler_fn(fake, context)


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


MEETING_KEYWORDS = (
    "action item", "actionable", "deadline", "tugas", "pic ",
    "keputusan", "kita sepakat", "follow up", "follow-up",
    "next step", "diskusi", "minutes of meeting", "mom ",
    "rapat", "meeting notes",
)
MEETING_TRANSCRIPT_MIN_CHARS = 500


def _looks_like_meeting(text: str) -> bool:
    if not text:
        return False
    if len(text) >= MEETING_TRANSCRIPT_MIN_CHARS:
        return True
    lower = text.lower()
    hits = sum(1 for kw in MEETING_KEYWORDS if kw in lower)
    return hits >= 2


async def _process_meeting_transcript(
    update: Update,
    transcript: str,
    user_id: int,
    auto_create_tasks: bool = True,
) -> None:
    try:
        r = await _agent_post(
            "/api/meeting_notes",
            {
                "transcript": transcript,
                "user_id": str(user_id),
                "auto_create_tasks": auto_create_tasks,
            },
            timeout=120.0,
        )
    except httpx.RequestError as exc:
        await update.message.reply_text(f"⚠️ Gagal menghubungi agent: {exc}")
        return

    if r.status_code != 200:
        await update.message.reply_text(
            f"⚠️ Gagal extract action items (HTTP {r.status_code})."
        )
        return

    data = r.json()
    text = _format_meeting_result(data)
    await update.message.reply_text(text[:4000], parse_mode="HTML")


def _format_meeting_result(data: dict) -> str:
    lines: list[str] = []
    summary = data.get("summary") or ""
    if summary:
        lines.append("📝 <b>Meeting Summary</b>")
        lines.append(summary)
        lines.append("")

    action_items = data.get("action_items") or []
    if action_items:
        lines.append(f"✅ <b>Action Items ({len(action_items)})</b>")
        for item in action_items:
            extras = []
            if item.get("owner"):
                extras.append(f"PIC: {item['owner']}")
            if item.get("deadline"):
                extras.append(f"Due: {item['deadline']}")
            tail = f" — {' · '.join(extras)}" if extras else ""
            prio = item.get("priority", "medium")
            title = item.get("title", "")
            lines.append(f"• [{prio}] {title}{tail}")
        lines.append("")

    decisions = data.get("decisions") or []
    if decisions:
        lines.append("🎯 <b>Decisions</b>")
        for d in decisions:
            lines.append(f"• {d}")
        lines.append("")

    next_steps = data.get("next_steps") or []
    if next_steps:
        lines.append("➡️ <b>Next Steps</b>")
        for s in next_steps:
            lines.append(f"• {s}")
        lines.append("")

    tasks_created = data.get("tasks_created", 0)
    if tasks_created:
        lines.append(f"💾 {tasks_created} task otomatis dibuat di pending list.")
    elif action_items:
        lines.append("ℹ️ Tasks tidak dibuat otomatis.")

    if data.get("truncated"):
        lines.append("")
        lines.append("⚠️ <i>Transkrip terlalu panjang, sebagian dipotong.</i>")

    if not lines:
        return "ℹ️ Tidak ada action item / keputusan terdeteksi dari transkrip."
    return "\n".join(lines).strip()


@authorized
async def cmd_meeting(update: Update, context: ContextTypes.DEFAULT_TYPE):
    transcript = " ".join(context.args).strip() if context.args else ""

    if not transcript and update.message.reply_to_message:
        transcript = (update.message.reply_to_message.text or "").strip()

    if not transcript:
        await update.message.reply_text(
            "Gunakan: /meeting <transkrip meeting>\n"
            "Atau reply ke pesan transkrip dengan /meeting.\n"
            "Atau kirim voice note panjang berisi catatan rapat — "
            "akan otomatis di-extract kalau >500 karakter."
        )
        return

    if len(transcript) > 20000:
        await update.message.reply_text(
            f"⚠️ Transkrip terlalu panjang ({len(transcript)} chars). Maks 20000."
        )
        return

    await update.message.reply_chat_action("typing")
    await update.message.reply_text("⏳ Extracting action items dari transkrip...")
    await _process_meeting_transcript(
        update,
        transcript,
        update.effective_user.id,
        auto_create_tasks=True,
    )


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
async def cmd_monitor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_chat_action("typing")

    args = context.args
    if args:
        action = args[0].lower()

        if action == "list":
            targets = _get_ssh_targets()
            if not targets:
                await update.message.reply_text("📋 No VPS targets configured.")
            else:
                lines = ["🖥️ <b>VPS Monitor Targets</b>", ""]
                for name, t in targets.items():
                    lines.append(f"• <b>{name}</b> — {t.get('user', 'root')}@{t.get('host', '?')}:{t.get('port', '22')}")
                await update.message.reply_text("\n".join(lines), parse_mode="HTML")
            return

        if action == "add" and len(args) >= 3:
            name = args[1]
            host = args[2]
            port = args[3] if len(args) >= 4 else "22"
            user = args[4] if len(args) >= 5 else "root"
            _add_ssh_target(name, host, port, user)
            await update.message.reply_text(
                f"✅ Added VPS <b>{name}</b> ({user}@{host}:{port})", parse_mode="HTML"
            )
            return

        if action in ("del", "remove") and len(args) >= 2:
            name = args[1]
            if _del_ssh_target(name):
                await update.message.reply_text(f"✅ Removed VPS <b>{name}</b>", parse_mode="HTML")
            else:
                await update.message.reply_text(f"ℹ️ <b>{name}</b> not found in config store (may be env-only).", parse_mode="HTML")
            return

        if action == "help":
            await update.message.reply_text(
                "Usage:\n/monitor — show all VPS status\n/monitor <name> — detail\n"
                "/monitor list — show targets\n/monitor add <name> <host> [port] [user]\n"
                "/monitor del <name>"
            )
            return

        await _monitor_detail(update, args[0])
        return

    up_results = await _prom_query('up{job="node"}')
    if up_results is None:
        await update.message.reply_text("⚠️ Prometheus tidak tersedia.")
        return

    if not up_results:
        await update.message.reply_text("Belum ada VPS target terdaftar di Prometheus.")
        return

    cpu_results = await _prom_query(
        '100 - (avg by(instance_name) (rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)'
    )
    mem_results = await _prom_query(
        '(1 - node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes) * 100'
    )
    disk_results = await _prom_query(
        '(1 - node_filesystem_avail_bytes{fstype=~"ext4|xfs",mountpoint="/"} / node_filesystem_size_bytes{fstype=~"ext4|xfs",mountpoint="/"}) * 100'
    )

    cpu_map = {r["metric"].get("instance_name", ""): float(r["value"][1]) for r in (cpu_results or [])}
    mem_map = {r["metric"].get("instance_name", ""): float(r["value"][1]) for r in (mem_results or [])}
    disk_map = {r["metric"].get("instance_name", ""): float(r["value"][1]) for r in (disk_results or [])}

    lines = ["📊 Monitor VPS (Prometheus)", ""]
    for target in up_results:
        name = target["metric"].get("instance_name", target["metric"].get("instance", "?"))
        is_up = target["value"][1] == "1"
        icon = "✅" if is_up else "❌"

        if is_up:
            cpu = cpu_map.get(name)
            mem = mem_map.get(name)
            disk = disk_map.get(name)
            cpu_str = f"CPU {cpu:.0f}%" if cpu is not None else ""
            mem_str = f"RAM {mem:.0f}%" if mem is not None else ""
            disk_str = f"Disk {disk:.0f}%" if disk is not None else ""
            ctr = await _ssh_docker_ps(name)
            ctr_str = f"📦 {len(ctr)}" if ctr else ""
            metrics = " | ".join(filter(None, [cpu_str, mem_str, disk_str, ctr_str]))
            lines.append(f"{icon} {name}: {metrics}")
        else:
            lines.append(f"{icon} {name}: DOWN")

    alerts = await _prom_query("ALERTS{alertstate=\"firing\"}")
    if alerts:
        lines.append("")
        lines.append("🚨 Active Alerts:")
        for a in alerts[:10]:
            m = a["metric"]
            lines.append(f"• [{m.get('severity', '?')}] {m.get('alertname', '?')} — {m.get('instance_name', m.get('instance', '?'))}")

    lines.append("")
    lines.append("Detail: /monitor <nama>")
    await update.message.reply_text("\n".join(lines)[:4000])



def _get_review_repos() -> list[str]:
    return _config_get("review_repos", [])


def _add_review_repo(repo: str) -> bool:
    repos = _config_get("review_repos", [])
    if repo in repos:
        return False
    repos.append(repo)
    _config_set("review_repos", repos)
    return True


def _del_review_repo(repo: str) -> bool:
    repos = _config_get("review_repos", [])
    if repo not in repos:
        return False
    repos.remove(repo)
    _config_set("review_repos", repos)
    return True


def _webhook_setup_hint(repo_key: str) -> str:
    """Generate webhook setup instructions for a repo."""
    if not AGENT_HOST:
        return ""

    parts = repo_key.split(":", 1)
    platform = parts[0] if len(parts) == 2 else "github"
    full_name = parts[1] if len(parts) == 2 else parts[0]

    if platform == "github":
        secret_display = GH_WEBHOOK_SECRET[:4] + "..." if len(GH_WEBHOOK_SECRET) > 4 else "(not set)"
        return (
            f"\n\n🔧 <b>Webhook setup:</b>\n"
            f"<pre>gh api repos/{full_name}/hooks "
            f"--method POST "
            f"-f name=web "
            f'-F config[url]=https://{AGENT_HOST}/api/webhook/github '
            f"-F config[secret]=YOUR_GH_WEBHOOK_SECRET "
            f"-F config[content_type]=json "
            f'-f "events[]=pull_request"</pre>\n'
            f"Secret starts with: <code>{secret_display}</code>\n"
            f"Or: https://github.com/{full_name}/settings/hooks/new"
        )
    elif platform == "gitlab":
        token_display = GITLAB_WEBHOOK_SECRET[:4] + "..." if len(GITLAB_WEBHOOK_SECRET) > 4 else "(not set)"
        return (
            f"\n\n🔧 <b>Webhook setup:</b>\n"
            f"<pre>glab api projects/{full_name.replace('/', '%2F')}/hooks "
            f"--method POST "
            f'-f url=https://{AGENT_HOST}/api/webhook/gitlab '
            f"-f token=YOUR_GITLAB_WEBHOOK_SECRET "
            f'-f merge_requests_events=true</pre>\n'
            f"Token starts with: <code>{token_display}</code>\n"
            f"Or: https://gitlab.com/{full_name}/-/hooks"
        )
    return ""


async def _sync_review_repos_to_agent(update: "Update | None" = None) -> None:
    repos = _get_review_repos()
    try:
        r = await _agent_post("/api/review/repos", {"repos": repos}, timeout=10.0)
        if r.status_code != 200:
            logger.warning("Review whitelist sync failed: %d %s", r.status_code, r.text[:200])
            if update:
                await update.message.reply_text("⚠️ Whitelist saved locally but agent sync failed. Will retry next change.")
    except Exception as exc:
        logger.warning("Review whitelist sync error: %s", exc)
        if update:
            await update.message.reply_text("⚠️ Whitelist saved locally but agent sync failed. Will retry next change.")


@authorized
async def cmd_review(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args or []

    if not args:
        await update.message.reply_text(
            "Usage:\n"
            "/review list — show monitored repos\n"
            "/review add github:owner/repo — add repo\n"
            "/review add gitlab:owner/repo — add GitLab repo\n"
            "/review del github:owner/repo — remove repo\n"
            "/review owner/repo#123 — review PR on-demand"
        )
        return

    action = args[0].lower()

    if action == "list":
        repos = _get_review_repos()
        if not repos:
            await update.message.reply_text("📋 No repos configured for auto-review.")
        else:
            lines = ["🔍 <b>Auto PR Review Repos</b>", ""]
            for repo_item in repos:
                lines.append(f"• <code>{repo_item}</code>")
            await update.message.reply_text("\n".join(lines), parse_mode="HTML")
        return

    if action == "add" and len(args) >= 2:
        repo = args[1].strip()
        if ":" not in repo:
            repo = f"github:{repo}"
        if _add_review_repo(repo):
            await _sync_review_repos_to_agent(update)
            hint = _webhook_setup_hint(repo)
            await update.message.reply_text(
                f"✅ Added <code>{repo}</code> to auto-review.{hint}",
                parse_mode="HTML",
                disable_web_page_preview=True,
            )
        else:
            await update.message.reply_text(f"ℹ️ <code>{repo}</code> already in list.", parse_mode="HTML")
        return

    if action in ("del", "remove") and len(args) >= 2:
        repo = args[1].strip()
        if ":" not in repo:
            repo = f"github:{repo}"
        if _del_review_repo(repo):
            await _sync_review_repos_to_agent(update)
            await update.message.reply_text(f"✅ Removed <code>{repo}</code> from auto-review.", parse_mode="HTML")
        else:
            await update.message.reply_text(f"ℹ️ <code>{repo}</code> not in list.", parse_mode="HTML")
        return

    # On-demand: /review owner/repo#123
    target = args[0]
    if "#" in target:
        repo_part, pr_str = target.rsplit("#", 1)
        if ":" not in repo_part:
            repo_part = f"github:{repo_part}"
        try:
            pr_number = int(pr_str)
        except ValueError:
            await update.message.reply_text("⚠️ Invalid PR number. Use: /review owner/repo#123")
            return
        await update.message.reply_text(f"🔍 Reviewing {repo_part}#{pr_number}...")
        try:
            r = await _agent_post("/api/review_pr", {
                "repo": repo_part,
                "pr_number": pr_number,
            }, timeout=90.0)
            if r.status_code == 200:
                data = r.json()
                verdict = data.get("verdict", "?")
                await update.message.reply_text(
                    f"✅ Review posted: <b>{verdict}</b>", parse_mode="HTML"
                )
            else:
                await update.message.reply_text(f"⚠️ Review failed: {r.status_code} {r.text[:200]}")
        except Exception as exc:
            await update.message.reply_text(f"⚠️ Review failed: {exc}")
    else:
        await update.message.reply_text(
            "Usage: /review owner/repo#123 or /review add/del/list"
        )


async def _ssh_docker_ps(name: str) -> list[dict] | None:
    target = _get_ssh_targets().get(name)
    if not target:
        return None
    host = target.get("host", "")
    port = str(target.get("port", 22))
    user = target.get("user", "root")
    fmt = '{{.Names}}\t{{.Status}}\t{{.Image}}'
    cmd = ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=5",
           "-o", "StrictHostKeyChecking=accept-new", "-p", port,
           f"{user}@{host}", f"docker ps --format '{fmt}'"]
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=15)
        if proc.returncode != 0:
            return None
        containers = []
        for line in stdout.decode().strip().splitlines():
            parts = line.split("\t")
            if len(parts) >= 2:
                containers.append({"name": parts[0], "status": parts[1], "image": parts[2] if len(parts) > 2 else ""})
        return containers
    except Exception:
        return None


# --- Dynamic Config Store (JSON file, persistent via volume) ---
_CONFIG_DIR = Path("/app/data")
_CONFIG_FILE = _CONFIG_DIR / "config.json"


def _load_config() -> dict:
    if _CONFIG_FILE.exists():
        try:
            return _json.loads(_CONFIG_FILE.read_text())
        except Exception:
            pass
    return {}


def _save_config(cfg: dict) -> None:
    _CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    _CONFIG_FILE.write_text(_json.dumps(cfg, indent=2))


def _config_get(key: str, default=None):
    return _load_config().get(key, default)


def _config_set(key: str, value) -> None:
    cfg = _load_config()
    cfg[key] = value
    _save_config(cfg)






@authorized
async def cmd_docsync(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "Usage:\n"
            "/docsync owner/repo#123 — analyze GitHub PR\n"
            "/docsync gitlab:project_id!iid — analyze GitLab MR"
        )
        return

    arg = context.args[0].strip()
    payload: dict = {}

    if arg.startswith("gitlab:") and "!" in arg:
        ref = arg.removeprefix("gitlab:")
        try:
            project_id, iid_str = ref.split("!", 1)
            mr_iid = int(iid_str)
        except ValueError:
            await update.message.reply_text("⚠️ Invalid GitLab ref. Use: /docsync gitlab:123!45")
            return
        payload = {"platform": "gitlab", "project_id": project_id.strip(), "mr_iid": mr_iid}
    elif "#" in arg:
        repo_part, pr_str = arg.rsplit("#", 1)
        repo_part = repo_part.removeprefix("github:")
        if "/" not in repo_part:
            await update.message.reply_text("⚠️ Invalid repo. Use: /docsync owner/repo#123")
            return
        owner, repo = repo_part.split("/", 1)
        try:
            pr_number = int(pr_str)
        except ValueError:
            await update.message.reply_text("⚠️ Invalid PR number. Use: /docsync owner/repo#123")
            return
        payload = {"platform": "github", "owner": owner.strip(), "repo": repo.strip(), "pr_number": pr_number}
    else:
        await update.message.reply_text(
            "⚠️ Format tidak dikenal. Use: /docsync owner/repo#123 atau /docsync gitlab:project_id!iid"
        )
        return

    await update.message.reply_text(f"📝 Checking docs sync untuk {arg}...")
    try:
        r = await _agent_post("/api/docs/suggest", payload, timeout=120.0)
    except httpx.RequestError as exc:
        await update.message.reply_text(f"⚠️ Gagal menghubungi agent: {exc}")
        return

    if r.status_code != 200:
        await update.message.reply_text(f"⚠️ Docs suggest failed (HTTP {r.status_code}).")
        return

    data = r.json()
    report = data.get("report") or "ℹ️ No report."
    await update.message.reply_text(report[:4000], parse_mode="HTML")




# --- Periodic Health Check ---
HEALTH_CHECK_INTERVAL = int(os.getenv("HEALTH_CHECK_INTERVAL_SEC", "300"))  # 5 min
_prev_vps_state: dict[str, bool] = {}
_prev_container_state: dict[str, dict[str, str]] = {}
_container_restarts: dict[str, list[float]] = {}  # "vps/container" -> [timestamp, ...]
RESTART_LOOP_THRESHOLD = int(os.getenv("RESTART_LOOP_THRESHOLD", "3"))
RESTART_LOOP_WINDOW = int(os.getenv("RESTART_LOOP_WINDOW_SEC", "900"))  # 15 min
AUTO_FIX_ENABLED = os.getenv("AUTO_FIX_ENABLED", "true").lower() in ("1", "true", "yes")
DISK_CRITICAL_PCT = float(os.getenv("DISK_AUTOFIX_THRESHOLD_PCT", "90"))


def _container_health(status: str) -> str:
    if "(healthy)" in status:
        return "healthy"
    if "(unhealthy)" in status:
        return "unhealthy"
    if "Up" in status:
        return "up"
    return "down"


def _is_fresh_restart(status: str) -> bool:
    s = status.lower()
    if "up" not in s:
        return False
    return ("second" in s or "less than a minute" in s) and "hour" not in s and "day" not in s


def _record_restart(key: str) -> int:
    import time
    now = time.time()
    _container_restarts.setdefault(key, [])
    _container_restarts[key].append(now)
    cutoff = now - RESTART_LOOP_WINDOW
    _container_restarts[key] = [t for t in _container_restarts[key] if t > cutoff]
    return len(_container_restarts[key])



async def _autofix_restart_container(vps_name: str, container_name: str) -> tuple[bool, str]:
    """Auto-restart a down/unhealthy container."""
    ok, output = await _ssh_exec(vps_name, f"docker restart {container_name}")
    if not ok:
        return False, f"restart failed: {output}"
    await asyncio.sleep(10)
    ok2, output2 = await _ssh_exec(vps_name, f"docker inspect --format='{{{{.State.Status}}}}' {container_name}")
    if ok2 and "running" in output2.lower():
        return True, "restarted successfully"
    return False, f"restarted but state={output2}"


async def _autofix_disk_prune(vps_name: str) -> tuple[bool, str]:
    """Auto-prune Docker resources when disk is critical."""
    ok, output = await _ssh_exec(vps_name, "docker system prune -f --volumes=false")
    if not ok:
        return False, f"prune failed: {output}"
    return True, output


async def _verify_disk_after_prune(vps_name: str) -> float | None:
    """Re-check disk usage via Prometheus after prune."""
    await asyncio.sleep(35)
    result = await _prom_query(
        f'(1 - node_filesystem_avail_bytes{{fstype=~"ext4|xfs",mountpoint="/",instance_name="{vps_name}"}} '
        f'/ node_filesystem_size_bytes{{fstype=~"ext4|xfs",mountpoint="/",instance_name="{vps_name}"}}) * 100'
    )
    if result:
        return float(result[0]["value"][1])
    return None


async def _run_auto_fixes(
    alerts: list[str],
    context: ContextTypes.DEFAULT_TYPE,
) -> list[str]:
    """Execute auto-fix actions based on detected issues. Returns action log."""
    if not AUTO_FIX_ENABLED:
        return []

    actions: list[str] = []
    chat_id = ALLOWED_USERS[0] if ALLOWED_USERS else None

    # Auto-restart down/unhealthy containers (skip if in restart loop)
    for vps_name, containers in _prev_container_state.items():
        for cname, health in containers.items():
            if health not in ("down", "unhealthy"):
                continue
            key = f"{vps_name}/{cname}"
            restart_count = len(_container_restarts.get(key, []))
            if restart_count >= RESTART_LOOP_THRESHOLD:
                actions.append(f"⏭️ Skip restart <b>{cname}</b> ({vps_name}) — restart loop ({restart_count}x)")
                continue

            logger.info(f"Auto-fix: restarting {cname} on {vps_name}")
            ok, msg = await _autofix_restart_container(vps_name, cname)
            if ok:
                actions.append(f"🔧 Auto-restart <b>{cname}</b> ({vps_name}) → ✅ {msg}")
            else:
                actions.append(f"🔧 Auto-restart <b>{cname}</b> ({vps_name}) → ❌ {msg}")

    # Auto-prune when disk critical
    disk_results = await _prom_query(
        '(1 - node_filesystem_avail_bytes{fstype=~"ext4|xfs",mountpoint="/"} '
        '/ node_filesystem_size_bytes{fstype=~"ext4|xfs",mountpoint="/"}) * 100'
    )
    if disk_results:
        for d in disk_results:
            name = d["metric"].get("instance_name", d["metric"].get("instance", "?"))
            pct = float(d["value"][1])
            if pct < DISK_CRITICAL_PCT:
                continue
            if name not in _get_ssh_targets():
                actions.append(f"⚠️ Disk {name} {pct:.0f}% — no SSH target, cannot auto-prune")
                continue

            logger.info(f"Auto-fix: pruning Docker on {name} (disk {pct:.0f}%)")
            ok, msg = await _autofix_disk_prune(name)
            if ok:
                new_pct = await _verify_disk_after_prune(name)
                if new_pct is not None and new_pct < DISK_CRITICAL_PCT:
                    actions.append(f"🧹 Auto-prune <b>{name}</b> (disk {pct:.0f}% → {new_pct:.0f}%) → ✅")
                elif new_pct is not None:
                    actions.append(f"🧹 Auto-prune <b>{name}</b> (disk {pct:.0f}% → {new_pct:.0f}%) → ⚠️ still critical")
                else:
                    actions.append(f"🧹 Auto-prune <b>{name}</b> (disk {pct:.0f}%) → ✅ pruned, verify pending")
            else:
                actions.append(f"🧹 Auto-prune <b>{name}</b> (disk {pct:.0f}%) → ❌ {msg}")

    # Report actions
    if actions and chat_id:
        lines = ["🤖 <b>Auto-Fix Actions</b>", ""]
        lines.extend(actions)
        now = datetime.now(ZoneInfo("Asia/Jakarta"))
        lines.append(f"\n<i>{now.strftime('%H:%M:%S')} WIB</i>")
        try:
            await context.bot.send_message(
                chat_id=chat_id,
                text="\n".join(lines)[:4000],
                parse_mode="HTML",
            )
        except Exception as e:
            logger.error(f"Failed to send auto-fix report: {e}")

    return actions


async def _health_check_job(context: ContextTypes.DEFAULT_TYPE) -> None:
    global _prev_vps_state, _prev_container_state
    alerts: list[str] = []
    recoveries: list[str] = []

    # 1. VPS up/down via Prometheus
    up_results = await _prom_query('up{job="node"}')
    if up_results:
        for target in up_results:
            name = target["metric"].get("instance_name", target["metric"].get("instance", "?"))
            is_up = target["value"][1] == "1"
            prev = _prev_vps_state.get(name)

            if prev is not None:
                if prev and not is_up:
                    alerts.append(f"🔴 VPS <b>{name}</b> DOWN")
                elif not prev and is_up:
                    recoveries.append(f"🟢 VPS <b>{name}</b> kembali UP")

            _prev_vps_state[name] = is_up

    # 2. Container health via SSH
    for vps_name in _get_ssh_targets():
        containers = await _ssh_docker_ps(vps_name)
        if containers is None:
            # SSH failed — if VPS is up per Prometheus, flag SSH issue
            if _prev_vps_state.get(vps_name, True):
                prev_ctrs = _prev_container_state.get(vps_name)
                if prev_ctrs is not None:
                    alerts.append(f"⚠️ SSH ke <b>{vps_name}</b> gagal (VPS up tapi SSH unreachable)")
            _prev_container_state.pop(vps_name, None)
            continue

        current: dict[str, str] = {}
        for c in containers:
            current[c["name"]] = _container_health(c["status"])
            if _is_fresh_restart(c["status"]):
                key = f"{vps_name}/{c['name']}"
                count = _record_restart(key)
                if count == RESTART_LOOP_THRESHOLD:
                    alerts.append(
                        f"🔁 Container <b>{c['name']}</b> ({vps_name}) restart loop "
                        f"({count}x dalam {RESTART_LOOP_WINDOW // 60} menit)"
                    )

        prev_ctrs = _prev_container_state.get(vps_name, {})
        if prev_ctrs:
            # Detect containers that disappeared or went unhealthy/down
            for cname, prev_health in prev_ctrs.items():
                cur_health = current.get(cname)
                if cur_health is None:
                    alerts.append(f"🔴 Container <b>{cname}</b> ({vps_name}) HILANG")
                elif prev_health in ("healthy", "up") and cur_health == "unhealthy":
                    alerts.append(f"🟡 Container <b>{cname}</b> ({vps_name}) UNHEALTHY")
                elif prev_health in ("healthy", "up") and cur_health == "down":
                    alerts.append(f"🔴 Container <b>{cname}</b> ({vps_name}) DOWN")

            # Detect recoveries
            for cname, cur_health in current.items():
                prev_health = prev_ctrs.get(cname)
                if prev_health in ("unhealthy", "down") and cur_health in ("healthy", "up"):
                    recoveries.append(f"🟢 Container <b>{cname}</b> ({vps_name}) recovered → {cur_health}")
                elif prev_health is None and cur_health in ("healthy", "up"):
                    recoveries.append(f"🟢 Container <b>{cname}</b> ({vps_name}) baru muncul")

        _prev_container_state[vps_name] = current

    # Send alerts
    if alerts or recoveries:
        lines = []
        if alerts:
            lines.append("🚨 <b>Health Alert</b>")
            lines.extend(alerts)
        if recoveries:
            if lines:
                lines.append("")
            lines.append("✅ <b>Recovery</b>")
            lines.extend(recoveries)

        chat_id = ALLOWED_USERS[0] if ALLOWED_USERS else None
        if chat_id:
            try:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text="\n".join(lines),
                    parse_mode="HTML",
                )
            except Exception as e:
                logger.error(f"Failed to send health alert: {e}")

    # Auto-fix: attempt remediation for detected issues
    if alerts and AUTO_FIX_ENABLED:
        try:
            await _run_auto_fixes(alerts, context)
        except Exception as e:
            logger.error(f"Auto-fix execution error: {e}")


async def _monitor_detail(update: Update, name: str):
    up = await _prom_query(f'up{{job="node",instance_name="{name}"}}')
    if not up:
        await update.message.reply_text(f"VPS '{name}' tidak ditemukan di Prometheus.")
        return

    is_up = up[0]["value"][1] == "1"
    if not is_up:
        await update.message.reply_text(f"❌ {name}: DOWN — tidak merespons.")
        return

    cpu = await _prom_query(
        f'100 - (avg by(instance_name) (rate(node_cpu_seconds_total{{mode="idle",instance_name="{name}"}}[5m])) * 100)'
    )
    mem = await _prom_query(
        f'(1 - node_memory_MemAvailable_bytes{{instance_name="{name}"}} / node_memory_MemTotal_bytes{{instance_name="{name}"}}) * 100'
    )
    mem_total = await _prom_query(f'node_memory_MemTotal_bytes{{instance_name="{name}"}}')
    disk = await _prom_query(
        f'(1 - node_filesystem_avail_bytes{{instance_name="{name}",fstype=~"ext4|xfs",mountpoint="/"}} / node_filesystem_size_bytes{{instance_name="{name}",fstype=~"ext4|xfs",mountpoint="/"}}) * 100'
    )
    disk_total = await _prom_query(
        f'node_filesystem_size_bytes{{instance_name="{name}",fstype=~"ext4|xfs",mountpoint="/"}}'
    )
    load5 = await _prom_query(f'node_load5{{instance_name="{name}"}}')
    uptime = await _prom_query(f'node_time_seconds{{instance_name="{name}"}} - node_boot_time_seconds{{instance_name="{name}"}}')
    swap_used = await _prom_query(
        f'(node_memory_SwapTotal_bytes{{instance_name="{name}"}} - node_memory_SwapFree_bytes{{instance_name="{name}"}}) / node_memory_SwapTotal_bytes{{instance_name="{name}"}} * 100'
    )

    lines = [f"🖥️ {name} (detail)", ""]

    if cpu:
        lines.append(f"CPU: {float(cpu[0]['value'][1]):.1f}%")
    if load5:
        lines.append(f"Load 5m: {float(load5[0]['value'][1]):.2f}")
    if mem and mem_total:
        mem_pct = float(mem[0]["value"][1])
        total_gb = float(mem_total[0]["value"][1]) / (1024**3)
        lines.append(f"RAM: {mem_pct:.1f}% of {total_gb:.1f}GB")
    if swap_used:
        val = float(swap_used[0]["value"][1])
        if val > 0:
            lines.append(f"Swap: {val:.1f}%")
    if disk and disk_total:
        disk_pct = float(disk[0]["value"][1])
        total_gb = float(disk_total[0]["value"][1]) / (1024**3)
        lines.append(f"Disk /: {disk_pct:.1f}% of {total_gb:.0f}GB")
    if uptime:
        lines.append(f"Uptime: {_human_uptime(float(uptime[0]['value'][1]))}")

    alerts = await _prom_query(f'ALERTS{{alertstate="firing",instance_name="{name}"}}')
    if alerts:
        lines.append("")
        lines.append("🚨 Alerts:")
        for a in alerts:
            m = a["metric"]
            lines.append(f"• [{m.get('severity')}] {m.get('alertname')}")

    containers = await _ssh_docker_ps(name)
    if containers is not None:
        lines.append("")
        lines.append(f"📦 Containers ({len(containers)}):")
        for c in containers:
            status = c["status"]
            icon = "✅" if "Up" in status else "❌"
            health = ""
            if "(healthy)" in status:
                health = " ♥"
            elif "(unhealthy)" in status:
                health = " ⚠️"
            lines.append(f"  {icon} {c['name']}{health}: {status}")

    await update.message.reply_text("\n".join(lines)[:4000])


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


@authorized
async def cmd_skill(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "Gunakan:\n"
            "/skill <query> — cari skill\n"
            "/skill log <nama> | <deskripsi> — simpan skill baru"
        )
        return

    args = list(context.args)

    if args[0].lower() == "log":
        raw = " ".join(args[1:])
        if "|" not in raw:
            await update.message.reply_text(
                "Format: /skill log <nama> | <deskripsi>\n"
                "Contoh: /skill log deploy-bot | Build image, push, restart container"
            )
            return
        parts = raw.split("|", 1)
        name = parts[0].strip()
        description = parts[1].strip()
        if not name or not description:
            await update.message.reply_text("Nama dan deskripsi tidak boleh kosong.")
            return

        await update.message.reply_chat_action("typing")
        try:
            r = await _agent_post(
                "/api/skills/log",
                {
                    "name": name,
                    "description": description,
                    "user_id": update.effective_user.id,
                },
                timeout=30.0,
            )
        except httpx.RequestError as exc:
            await update.message.reply_text(f"⚠️ Gagal menghubungi agent: {exc}")
            return
        if r.status_code == 200:
            await update.message.reply_text(f"🧠 Skill disimpan: {name}")
        else:
            await update.message.reply_text(f"⚠️ Gagal menyimpan skill (HTTP {r.status_code}).")
        return

    query = " ".join(args)
    if len(query) > 500:
        await update.message.reply_text("⚠️ Query terlalu panjang.")
        return
    await update.message.reply_chat_action("typing")
    try:
        r = await _agent_post(
            "/api/skills/search",
            {"query": query, "limit": 5},
            timeout=30.0,
        )
    except httpx.RequestError as exc:
        await update.message.reply_text(f"⚠️ Gagal menghubungi agent: {exc}")
        return
    if r.status_code != 200:
        await update.message.reply_text(f"⚠️ Gagal mencari skill (HTTP {r.status_code}).")
        return

    data = r.json()
    results = data.get("results") or []
    if not results:
        await update.message.reply_text(f"Tidak ditemukan skill untuk: {query}")
        return

    lines = [f"🧠 Skills matching \"{query}\":", ""]
    for i, s in enumerate(results, 1):
        score = f"{s['score']:.2f}" if s.get("score") else "-"
        lines.append(f"{i}. {s['name']} (score: {score})")
        if s.get("description"):
            lines.append(f"   {s['description'][:150]}")
        if s.get("steps"):
            for step in s["steps"][:5]:
                lines.append(f"   • {step}")
        lines.append("")
    await update.message.reply_text("\n".join(lines)[:4000])


@authorized
async def handle_skill_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    history = context.chat_data.get("history", [])
    if len(history) < 4:
        await query.edit_message_reply_markup(None)
        return

    user_msgs = [m["text"] for m in history if m["role"] == "user"]
    bot_msgs = [m["text"] for m in history if m["role"] == "assistant"]

    name = (user_msgs[0][:80] if user_msgs else "unnamed").strip()
    description = (bot_msgs[-1][:500] if bot_msgs else "").strip()
    steps = [m[:200] for m in user_msgs[1:5]] if len(user_msgs) > 1 else []

    if not name or not description:
        await query.edit_message_reply_markup(None)
        return

    try:
        r = await _agent_post(
            "/api/skills/log",
            {
                "name": name,
                "description": description,
                "steps": steps,
                "tags": ["auto"],
                "user_id": str(update.effective_user.id),
            },
            timeout=30.0,
        )
    except httpx.RequestError:
        await query.edit_message_reply_markup(None)
        return

    await query.edit_message_reply_markup(None)
    if r.status_code == 200:
        data = r.json()
        status = data.get("status", "logged")
        if status == "dedup":
            await query.message.reply_text("🧠 Skill serupa sudah ada, tidak disimpan ulang.")
        else:
            await query.message.reply_text(f"🧠 Skill disimpan: {name[:50]}")
        today = datetime.now().strftime("%Y-%m-%d")
        logs = context.chat_data.setdefault("skill_logs_today", {"date": today, "count": 0})
        if logs.get("date") != today:
            logs["date"] = today
            logs["count"] = 0
        logs["count"] += 1

    context.chat_data["history"] = []
    context.chat_data["skill_offered_this_thread"] = False


def _is_journal_reply(update: Update) -> bool:
    reply = update.message.reply_to_message if update.message else None
    if not reply or not reply.text:
        return False
    return JOURNAL_PROMPT_MARKER in reply.text


def _should_offer_skill(context: ContextTypes.DEFAULT_TYPE, reply: str) -> bool:
    if len(reply) < MIN_REPLY_LEN_FOR_SKILL:
        return False
    if reply.startswith("⚠️"):
        return False
    history = context.chat_data.get("history", [])
    if len(history) < MIN_HISTORY_FOR_SKILL_OFFER:
        return False
    today = datetime.now().strftime("%Y-%m-%d")
    logs_today = context.chat_data.get("skill_logs_today", {})
    if logs_today.get("date") != today:
        return True
    if logs_today.get("count", 0) >= MAX_SKILL_AUTOLOGS_PER_DAY:
        return False
    if context.chat_data.get("skill_offered_this_thread"):
        return False
    return True


def _record_history(context: ContextTypes.DEFAULT_TYPE, role: str, text: str) -> None:
    history = context.chat_data.setdefault("history", [])
    history.append({"role": role, "text": text})
    if len(history) > 10:
        context.chat_data["history"] = history[-10:]


@authorized
async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    voice = update.message.voice

    duration_sec = voice.duration.total_seconds() if isinstance(voice.duration, timedelta) else (voice.duration or 0)
    if duration_sec and duration_sec > MAX_VOICE_DURATION_SEC:
        await update.message.reply_text(
            f"⚠️ Voice terlalu panjang ({int(duration_sec)}s). Maks {MAX_VOICE_DURATION_SEC}s."
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

        if _looks_like_meeting(transcript):
            preview = transcript[:120] + ("…" if len(transcript) > 120 else "")
            await update.message.reply_text(
                f"🎙️ \"{preview}\"\n\n"
                f"📋 Transkrip terdeteksi sebagai catatan meeting "
                f"({len(transcript)} chars). Extracting action items..."
            )
            _record_history(context, "user", transcript)
            await _process_meeting_transcript(
                update,
                transcript,
                update.effective_user.id,
                auto_create_tasks=True,
            )
            return

        repo, question = _detect_repo_intent(transcript)

        if repo and question:
            r = await _agent_post(
                "/api/repos/ask",
                {"question": question, "repo": repo},
                timeout=120.0,
            )
        else:
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

        route_info = f" → 📦 {repo}" if repo else ""
        prefix = f"🎙️ \"{transcript[:120]}{'…' if len(transcript) > 120 else ''}\"{route_info}\n\n"

        _record_history(context, "user", transcript)
        _record_history(context, "assistant", reply)

        full_reply = prefix + reply
        if _should_offer_skill(context, reply):
            kb = InlineKeyboardMarkup([[
                InlineKeyboardButton("💾 Simpan sebagai skill?", callback_data="autoskill")
            ]])
            await update.message.reply_text(full_reply[:4000], reply_markup=kb)
            context.chat_data["skill_offered_this_thread"] = True
        else:
            await update.message.reply_text(full_reply[:4000])

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
    prompt = _whisper_prompt()
    async with httpx.AsyncClient(timeout=60.0) as client:
        with open(path, "rb") as f:
            data = {"model": WHISPER_MODEL, "response_format": "json"}
            if prompt:
                data["prompt"] = prompt
            resp = await client.post(
                url,
                headers={"Authorization": f"Bearer {WHISPER_API_KEY}"},
                data=data,
                files={"file": (path.name, f, "audio/ogg")},
            )
    resp.raise_for_status()
    return (resp.json().get("text") or "").strip()


@authorized
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if _is_journal_reply(update):
        await _submit_journal(update, update.message.text or "")
        return

    user_message = update.message.text or ""
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

    _record_history(context, "user", user_message)
    _record_history(context, "assistant", reply)

    if _should_offer_skill(context, reply):
        kb = InlineKeyboardMarkup([[
            InlineKeyboardButton("💾 Simpan sebagai skill?", callback_data="autoskill")
        ]])
        await update.message.reply_text(reply[:4000], reply_markup=kb)
        context.chat_data["skill_offered_this_thread"] = True
    else:
        await update.message.reply_text(reply[:4000])


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
    await _load_repo_names()
    commands = [
        BotCommand("menu", "Lihat semua fitur"),
        BotCommand("monitor", "Monitor VPS + containers"),
        BotCommand("tanya", "Tanya tentang code di repo"),
        BotCommand("task", "Buat task baru"),
        BotCommand("meeting", "Extract action items dari transkrip"),
        BotCommand("journal", "Catat journal harian"),
        BotCommand("briefing", "Daily briefing"),
        BotCommand("capacity", "Capacity forecast disk/RAM"),
        BotCommand("review", "Auto PR/MR review"),
        BotCommand("docsync", "Check if docs need updating for PR"),
        BotCommand("deps", "Dependency vulnerability scan"),
        BotCommand("ssl", "SSL cert check"),
        BotCommand("dns", "DNS health check"),
        BotCommand("hygiene", "Docker image hygiene"),
        BotCommand("firewall", "Firewall audit"),
        BotCommand("drift", "Config drift check"),
    ]
    await application.bot.set_my_commands(commands)
    logger.info("Bot commands registered.")

    if HEALTH_CHECK_INTERVAL > 0:
        application.job_queue.run_repeating(
            _health_check_job,
            interval=HEALTH_CHECK_INTERVAL,
            first=60,
            name="health_check",
        )
        logger.info(f"Health check job scheduled every {HEALTH_CHECK_INTERVAL}s.")

    if MORNING_BRIEF_ENABLED:
        brief_time = _time(
            hour=MORNING_BRIEF_HOUR,
            minute=MORNING_BRIEF_MINUTE,
            tzinfo=ZoneInfo("Asia/Jakarta"),
        )
        application.job_queue.run_daily(
            morning_brief_job,
            time=brief_time,
            name="morning_brief",
        )
        logger.info(f"Morning brief scheduled daily at {MORNING_BRIEF_HOUR:02d}:{MORNING_BRIEF_MINUTE:02d} WIB.")

    if DRIFT_CHECK_ENABLED:
        drift_time = _time(
            hour=DRIFT_CHECK_HOUR,
            minute=DRIFT_CHECK_MINUTE,
            tzinfo=ZoneInfo("Asia/Jakarta"),
        )
        application.job_queue.run_daily(
            drift_check_job,
            time=drift_time,
            name="drift_check",
        )
        logger.info(f"Drift check scheduled daily at {DRIFT_CHECK_HOUR:02d}:{DRIFT_CHECK_MINUTE:02d} WIB.")

    if SSL_CHECK_ENABLED and get_ssl_domains():
        ssl_time = _time(
            hour=DRIFT_CHECK_HOUR,
            minute=DRIFT_CHECK_MINUTE + 5,
            tzinfo=ZoneInfo("Asia/Jakarta"),
        )
        application.job_queue.run_daily(
            ssl_check_job,
            time=ssl_time,
            name="ssl_check",
        )
        logger.info(f"SSL check scheduled daily at {DRIFT_CHECK_HOUR:02d}:{DRIFT_CHECK_MINUTE + 5:02d} WIB for {len(get_ssl_domains())} domain(s).")

    if CAPACITY_CHECK_ENABLED:
        capacity_time = _time(
            hour=CAPACITY_CHECK_HOUR,
            minute=CAPACITY_CHECK_MINUTE,
            tzinfo=ZoneInfo("Asia/Jakarta"),
        )
        application.job_queue.run_daily(
            capacity_check_job,
            time=capacity_time,
            name="capacity_check",
        )
        logger.info(f"Capacity check scheduled daily at {CAPACITY_CHECK_HOUR:02d}:{CAPACITY_CHECK_MINUTE:02d} WIB.")

    if DEPS_CHECK_ENABLED:
        deps_time = _time(
            hour=DEPS_CHECK_HOUR,
            minute=DEPS_CHECK_MINUTE,
            tzinfo=ZoneInfo("Asia/Jakarta"),
        )
        application.job_queue.run_daily(
            deps_check_job,
            time=deps_time,
            name="deps_check",
        )
        logger.info(f"Deps check scheduled daily at {DEPS_CHECK_HOUR:02d}:{DEPS_CHECK_MINUTE:02d} WIB.")

    if DOCKER_HYGIENE_ENABLED:
        hygiene_time = _time(
            hour=DOCKER_HYGIENE_HOUR,
            minute=DOCKER_HYGIENE_MINUTE,
            tzinfo=ZoneInfo("Asia/Jakarta"),
        )
        application.job_queue.run_daily(
            docker_hygiene_job,
            time=hygiene_time,
            name="docker_hygiene",
        )
        logger.info(f"Docker hygiene scheduled daily at {DOCKER_HYGIENE_HOUR:02d}:{DOCKER_HYGIENE_MINUTE:02d} WIB.")

    if FIREWALL_AUDIT_ENABLED:
        firewall_time = _time(
            hour=FIREWALL_AUDIT_HOUR,
            minute=FIREWALL_AUDIT_MINUTE,
            tzinfo=ZoneInfo("Asia/Jakarta"),
        )
        application.job_queue.run_daily(
            firewall_audit_job,
            time=firewall_time,
            name="firewall_audit",
        )
        logger.info(f"Firewall audit scheduled daily at {FIREWALL_AUDIT_HOUR:02d}:{FIREWALL_AUDIT_MINUTE:02d} WIB.")

    if COVERAGE_AGENT_ENABLED:
        coverage_time = _time(
            hour=COVERAGE_AGENT_HOUR,
            minute=COVERAGE_AGENT_MINUTE,
            tzinfo=ZoneInfo("Asia/Jakarta"),
        )
        application.job_queue.run_daily(
            coverage_scan_job,
            time=coverage_time,
            name="coverage_scan",
        )
        logger.info(f"Coverage scan scheduled daily at {COVERAGE_AGENT_HOUR:02d}:{COVERAGE_AGENT_MINUTE:02d} WIB.")

    if DNS_CHECK_ENABLED and get_dns_domains():
        application.job_queue.run_repeating(
            dns_check_job,
            interval=DNS_CHECK_INTERVAL_SEC,
            first=120,
            name="dns_check",
        )
        logger.info(f"DNS check scheduled every {DNS_CHECK_INTERVAL_SEC}s for {len(get_dns_domains())} domain(s).")


def main():
    if not BOT_TOKEN:
        raise RuntimeError("TELEGRAM_BOT_TOKEN not set")
    if not ALLOWED_USERS:
        raise RuntimeError("ALLOWED_USER_IDS not set")

    app = Application.builder().token(BOT_TOKEN).post_init(post_init).build()

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("menu", cmd_menu))
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
    app.add_handler(CommandHandler("monitor", cmd_monitor))
    app.add_handler(CommandHandler("drift", cmd_drift))
    app.add_handler(CommandHandler("ssl", cmd_ssl))
    app.add_handler(CommandHandler("capacity", cmd_capacity))
    app.add_handler(CommandHandler("review", cmd_review))
    app.add_handler(CommandHandler("model", cmd_model))
    app.add_handler(CommandHandler("journal", cmd_journal))
    app.add_handler(CommandHandler("projects", cmd_projects))
    app.add_handler(CommandHandler("index", cmd_index))
    app.add_handler(CommandHandler("tanya", cmd_tanya))
    app.add_handler(CommandHandler("skill", cmd_skill))
    app.add_handler(CommandHandler("meeting", cmd_meeting))
    app.add_handler(CommandHandler("deps", cmd_deps))
    app.add_handler(CommandHandler("docsync", cmd_docsync))
    app.add_handler(CommandHandler("hygiene", cmd_hygiene))
    app.add_handler(CommandHandler("firewall", cmd_firewall))
    app.add_handler(CommandHandler("coverage", cmd_coverage))
    app.add_handler(CommandHandler("dns", cmd_dns))
    app.add_handler(CallbackQueryHandler(handle_skill_callback, pattern="^autoskill$"))
    app.add_handler(CallbackQueryHandler(handle_menu_callback, pattern="^menu:"))
    app.add_handler(MessageHandler(filters.VOICE, handle_voice))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))

    logger.info(
        f"Secretary Bot starting (agent={AGENT_URL}, allowed={ALLOWED_USERS})"
    )
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
