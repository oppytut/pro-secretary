from __future__ import annotations

import logging
import os
from functools import wraps
from typing import Any, Awaitable, Callable

from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

ALLOWED_USERS: list[int] = [
    int(x) for x in os.getenv("ALLOWED_USER_IDS", "").split(",") if x.strip()
]


def authorized(
    func: Callable[[Update, ContextTypes.DEFAULT_TYPE], Awaitable[Any]],
) -> Callable[[Update, ContextTypes.DEFAULT_TYPE], Awaitable[Any]]:
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE) -> Any:
        user = update.effective_user
        if user is None or user.id not in ALLOWED_USERS:
            uid = user.id if user else "unknown"
            logger.warning(f"Unauthorized access attempt: {uid}")
            if update.message is not None:
                await update.message.reply_text("⛔ Unauthorized.")
            return None
        return await func(update, context)

    return wrapper
