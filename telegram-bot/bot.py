#!/usr/bin/env python3

import logging
import os

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
        "/cari <query> - Cari di knowledge base\n"
        "/catat <note> - Catat sesuatu\n"
        "/briefing - Daily briefing\n"
        "/eod - End-of-day summary\n"
        "/sync - Sync Obsidian vault\n"
        "/status - Cek status semua komponen\n"
        "/vps - Cek resource VPS\n"
        "/model - Ganti/lihat model AI\n\n"
        "Atau kirim pesan biasa untuk chat."
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

    query = " ".join(context.args)
    await update.message.reply_chat_action("typing")
    try:
        r = await _agent_post(
            "/api/search",
            {"query": query, "collection": "knowledge", "limit": 5},
            timeout=30.0,
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
        content = (item.get("content") or "")[:200]
        source = item.get("source_file") or "unknown"
        text += f"{i}. {content}...\n   📎 {source}\n\n"
    await update.message.reply_text(text)


@authorized
async def cmd_catat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Gunakan: /catat <isi catatan>")
        return

    note = " ".join(context.args)
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
            f"🤖 Model aktif: `{current_model}`\n\n"
            f"Gunakan: /model <nama_model>\n\n"
            f"Contoh:\n"
            f"/model gpt-4o\n"
            f"/model gpt-3.5-turbo\n"
            f"/model claude-3.5-sonnet\n"
            f"/model llama-3.1-70b-versatile",
            parse_mode="Markdown",
        )
        return

    new_model = " ".join(context.args)
    current_model = new_model
    await update.message.reply_text(f"✅ Model diganti ke: `{current_model}`", parse_mode="Markdown")
    logger.info(f"Model switched to: {current_model}")


@authorized
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
    import boto3
    from io import BytesIO

    document = update.message.document
    file = await context.bot.get_file(document.file_id)
    file_bytes = await file.download_as_bytearray()

    s3 = boto3.client(
        "s3",
        endpoint_url=os.getenv("R2_ENDPOINT"),
        aws_access_key_id=os.getenv("R2_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("R2_SECRET_ACCESS_KEY"),
        region_name="auto",
    )

    key = f"telegram-uploads/{document.file_name}"
    s3.upload_fileobj(
        BytesIO(file_bytes),
        os.getenv("R2_BUCKET", "secretary-files"),
        key,
    )

    await update.message.reply_text(f"📁 File '{document.file_name}' disimpan ke storage.")


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
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))

    logger.info(
        f"Secretary Bot starting (agent={AGENT_URL}, allowed={ALLOWED_USERS})"
    )
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
