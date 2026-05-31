from __future__ import annotations

import asyncio
import importlib
import logging
from unittest.mock import AsyncMock, MagicMock

from infra import auth as auth_module


def _reload_auth(monkeypatch, allowed: str = ""):
    monkeypatch.setenv("ALLOWED_USER_IDS", allowed)
    return importlib.reload(auth_module)


class TestAllowedUsers:
    def test_empty_list_when_no_env(self, monkeypatch):
        auth = _reload_auth(monkeypatch, "")
        assert auth.ALLOWED_USERS == []

    def test_parses_single_id(self, monkeypatch):
        auth = _reload_auth(monkeypatch, "12345")
        assert auth.ALLOWED_USERS == [12345]

    def test_parses_multiple_ids(self, monkeypatch):
        auth = _reload_auth(monkeypatch, "111,222,333")
        assert auth.ALLOWED_USERS == [111, 222, 333]

    def test_skips_empty_segments(self, monkeypatch):
        auth = _reload_auth(monkeypatch, "111,,222")
        assert auth.ALLOWED_USERS == [111, 222]

    def test_strips_whitespace(self, monkeypatch):
        auth = _reload_auth(monkeypatch, " 111 , 222 ")
        assert auth.ALLOWED_USERS == [111, 222]


class TestAuthorizedDecorator:
    def _make_update(self, user_id: int | None = 100):
        update = MagicMock()
        if user_id is None:
            update.effective_user = None
        else:
            update.effective_user = MagicMock()
            update.effective_user.id = user_id
        update.message = MagicMock()
        update.message.reply_text = AsyncMock()
        return update

    def test_authorized_user_passes_through(self, monkeypatch):
        auth = _reload_auth(monkeypatch, "100")
        called_with = []

        @auth.authorized
        async def handler(update, context):
            called_with.append((update, context))
            return "result"

        update = self._make_update(user_id=100)
        result = asyncio.run(handler(update, "ctx"))
        assert result == "result"
        assert len(called_with) == 1

    def test_unauthorized_user_blocked(self, monkeypatch, caplog):
        auth = _reload_auth(monkeypatch, "100")
        called = []

        @auth.authorized
        async def handler(update, context):
            called.append(1)

        update = self._make_update(user_id=999)
        with caplog.at_level(logging.WARNING):
            result = asyncio.run(handler(update, "ctx"))
        assert result is None
        assert called == []
        update.message.reply_text.assert_awaited_once_with("⛔ Unauthorized.")
        assert "Unauthorized access attempt: 999" in caplog.text

    def test_no_user_blocked(self, monkeypatch, caplog):
        auth = _reload_auth(monkeypatch, "100")
        called = []

        @auth.authorized
        async def handler(update, context):
            called.append(1)

        update = self._make_update(user_id=None)
        with caplog.at_level(logging.WARNING):
            result = asyncio.run(handler(update, "ctx"))
        assert result is None
        assert called == []
        assert "Unauthorized access attempt: unknown" in caplog.text

    def test_unauthorized_with_no_message(self, monkeypatch):
        auth = _reload_auth(monkeypatch, "100")

        @auth.authorized
        async def handler(update, context):
            return "ok"

        update = MagicMock()
        update.effective_user = MagicMock()
        update.effective_user.id = 999
        update.message = None
        result = asyncio.run(handler(update, "ctx"))
        assert result is None

    def test_decorator_preserves_function_name(self, monkeypatch):
        auth = _reload_auth(monkeypatch, "100")

        @auth.authorized
        async def my_handler(update, context):
            return None

        assert my_handler.__name__ == "my_handler"

    def test_empty_allowed_users_blocks_everyone(self, monkeypatch):
        auth = _reload_auth(monkeypatch, "")

        @auth.authorized
        async def handler(update, context):
            return "ok"

        update = self._make_update(user_id=100)
        result = asyncio.run(handler(update, "ctx"))
        assert result is None
        update.message.reply_text.assert_awaited()
