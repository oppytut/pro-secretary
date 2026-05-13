#!/usr/bin/env python3

import os
import logging
import httpx
from telegram import Update, BotCommand
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    filters, ContextTypes
)

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ALLOWED_USERS = [int(x) for x in os.getenv("ALLOWED_USER_IDS", "").split(",") if x.strip()]
N8N_WEBHOOK = os.getenv("N8N_WEBHOOK_URL", "http://n8n:5678/webhook/telegram")
OPENFANG_URL = os.getenv("OPENFANG_URL", "http://openfang:8090")
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4")

current_model = LLM_MODEL

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
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
        "/model - Ganti/lihat model AI\n\n"
        "Atau kirim pesan biasa untuk chat."
    )


@authorized
async def cmd_jadwal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_chat_action("typing")
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{N8N_WEBHOOK}/schedule",
            json={"user_id": update.effective_user.id, "action": "today"}
        )
    if response.status_code == 200:
        await update.message.reply_text(response.json().get("message", "Tidak ada jadwal hari ini."))
    else:
        await update.message.reply_text("⚠️ Gagal mengambil jadwal. Coba lagi nanti.")


@authorized
async def cmd_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_chat_action("typing")
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{N8N_WEBHOOK}/tasks",
            json={"action": "list", "status": "pending"}
        )
    if response.status_code == 200:
        await update.message.reply_text(response.json().get("message", "Tidak ada pending tasks."))
    else:
        await update.message.reply_text("⚠️ Gagal mengambil tasks.")


@authorized
async def cmd_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Gunakan: /task <judul task>")
        return

    task_text = " ".join(context.args)
    await update.message.reply_chat_action("typing")
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{N8N_WEBHOOK}/tasks",
            json={"action": "create", "title": task_text}
        )
    if response.status_code == 200:
        await update.message.reply_text(f"✅ Task ditambahkan: {task_text}")
    else:
        await update.message.reply_text("⚠️ Gagal membuat task.")


@authorized
async def cmd_cari(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Gunakan: /cari <kata kunci>")
        return

    query = " ".join(context.args)
    await update.message.reply_chat_action("typing")
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{OPENFANG_URL}/api/search",
            json={"query": query, "collection": "knowledge", "limit": 5}
        )

    if response.status_code != 200:
        await update.message.reply_text("⚠️ Gagal mencari. Coba lagi nanti.")
        return

    results = response.json().get("results", [])
    if not results:
        await update.message.reply_text(f"Tidak ditemukan hasil untuk: {query}")
        return

    text = f"🔍 Hasil pencarian: {query}\n\n"
    for i, r in enumerate(results, 1):
        text += f"{i}. {r['content'][:200]}...\n"
        text += f"   📎 {r.get('source_file', 'unknown')}\n\n"
    await update.message.reply_text(text)


@authorized
async def cmd_catat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Gunakan: /catat <isi catatan>")
        return

    note = " ".join(context.args)
    await update.message.reply_chat_action("typing")
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{N8N_WEBHOOK}/note",
            json={"content": note, "source": "telegram", "user_id": update.effective_user.id}
        )
    if response.status_code == 200:
        await update.message.reply_text(f"📝 Dicatat: {note}")
    else:
        await update.message.reply_text("⚠️ Gagal mencatat.")


@authorized
async def cmd_briefing(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⏳ Menyiapkan briefing...")
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            f"{N8N_WEBHOOK}/briefing",
            json={"user_id": update.effective_user.id}
        )
    if response.status_code == 200:
        await update.message.reply_text(response.json().get("message", "Briefing tidak tersedia."))
    else:
        await update.message.reply_text("⚠️ Gagal membuat briefing.")


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
    global current_model
    user_message = update.message.text
    await update.message.reply_chat_action("typing")

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            f"{LLM_BASE_URL}/chat/completions",
            headers={"Authorization": f"Bearer {LLM_API_KEY}"},
            json={
                "model": current_model,
                "messages": [
                    {"role": "system", "content": "Kamu adalah sekretaris pribadi AI yang efisien. Jawab dalam Bahasa Indonesia yang natural."},
                    {"role": "user", "content": user_message},
                ],
                "temperature": 0.7,
                "max_tokens": 1024,
            },
        )

    if response.status_code == 200:
        reply = response.json()["choices"][0]["message"]["content"]
    else:
        reply = f"⚠️ Error dari LLM (HTTP {response.status_code}). Cek /model atau API key."

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
    app.add_handler(CommandHandler("model", cmd_model))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))

    logger.info(f"Secretary Bot starting (allowed users: {ALLOWED_USERS})")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
