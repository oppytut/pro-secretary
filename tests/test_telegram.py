from __future__ import annotations

import asyncio
from typing import Any

import httpx
import pytest

from app import telegram


def _run(coro):
    return asyncio.run(coro)


class FakeResponse:
    def __init__(self, status_code: int = 200) -> None:
        self.status_code = status_code


class FakeAsyncClient:
    def __init__(self, *, post_responses=None, post_raises=None, **_kwargs) -> None:
        self._responses = list(post_responses or [])
        self._raises = post_raises
        self.calls: list[dict[str, Any]] = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False

    async def post(self, url, json=None):
        self.calls.append({"url": url, "json": json})
        if self._raises is not None:
            raise self._raises
        if self._responses:
            return self._responses.pop(0)
        return FakeResponse(200)


@pytest.fixture
def fake_client(monkeypatch):
    holder: dict[str, Any] = {}

    def factory(**factory_kwargs):
        def make_client(*args, **kwargs):
            client = FakeAsyncClient(**factory_kwargs)
            holder["client"] = client
            return client

        monkeypatch.setattr(telegram.httpx, "AsyncClient", make_client)
        return holder

    return factory


class TestSendMessageGuards:
    def test_no_token_returns_error(self, monkeypatch):
        monkeypatch.setattr(telegram.config, "TELEGRAM_BOT_TOKEN", "")
        result = _run(telegram.send_message("hi"))
        assert result == {"ok": False, "error": "TELEGRAM_BOT_TOKEN not set"}

    def test_no_recipients_returns_error(self, monkeypatch):
        monkeypatch.setattr(telegram.config, "TELEGRAM_BOT_TOKEN", "tok")
        monkeypatch.setattr(telegram.config, "TELEGRAM_ALLOWED_USERS", [])
        result = _run(telegram.send_message("hi"))
        assert result == {"ok": False, "error": "no recipients"}


class TestSendMessageDelivery:
    def test_uses_chat_id_arg_over_config(self, monkeypatch, fake_client):
        monkeypatch.setattr(telegram.config, "TELEGRAM_BOT_TOKEN", "tok")
        monkeypatch.setattr(telegram.config, "TELEGRAM_ALLOWED_USERS", ["111", "222"])
        holder = fake_client()
        result = _run(telegram.send_message("hi", chat_id=999))
        assert result["ok"] is True
        assert result["delivered"] == 1
        assert holder["client"].calls[0]["json"]["chat_id"] == "999"

    def test_uses_allowed_users_when_no_chat_id(self, monkeypatch, fake_client):
        monkeypatch.setattr(telegram.config, "TELEGRAM_BOT_TOKEN", "tok")
        monkeypatch.setattr(telegram.config, "TELEGRAM_ALLOWED_USERS", ["111", "222"])
        holder = fake_client()
        result = _run(telegram.send_message("hi"))
        assert result["delivered"] == 2
        assert len(holder["client"].calls) == 2

    def test_url_contains_bot_token(self, monkeypatch, fake_client):
        monkeypatch.setattr(telegram.config, "TELEGRAM_BOT_TOKEN", "secret-token")
        monkeypatch.setattr(telegram.config, "TELEGRAM_ALLOWED_USERS", ["111"])
        holder = fake_client()
        _run(telegram.send_message("hi"))
        assert "/botsecret-token/sendMessage" in holder["client"].calls[0]["url"]

    def test_payload_disables_web_preview(self, monkeypatch, fake_client):
        monkeypatch.setattr(telegram.config, "TELEGRAM_BOT_TOKEN", "tok")
        monkeypatch.setattr(telegram.config, "TELEGRAM_ALLOWED_USERS", ["111"])
        holder = fake_client()
        _run(telegram.send_message("hi"))
        assert holder["client"].calls[0]["json"]["disable_web_page_preview"] is True

    def test_parse_mode_propagated(self, monkeypatch, fake_client):
        monkeypatch.setattr(telegram.config, "TELEGRAM_BOT_TOKEN", "tok")
        monkeypatch.setattr(telegram.config, "TELEGRAM_ALLOWED_USERS", ["111"])
        holder = fake_client()
        _run(telegram.send_message("<b>hi</b>", parse_mode="HTML"))
        assert holder["client"].calls[0]["json"]["parse_mode"] == "HTML"

    def test_parse_mode_omitted_when_none(self, monkeypatch, fake_client):
        monkeypatch.setattr(telegram.config, "TELEGRAM_BOT_TOKEN", "tok")
        monkeypatch.setattr(telegram.config, "TELEGRAM_ALLOWED_USERS", ["111"])
        holder = fake_client()
        _run(telegram.send_message("hi"))
        assert "parse_mode" not in holder["client"].calls[0]["json"]

    def test_reply_markup_propagated(self, monkeypatch, fake_client):
        monkeypatch.setattr(telegram.config, "TELEGRAM_BOT_TOKEN", "tok")
        monkeypatch.setattr(telegram.config, "TELEGRAM_ALLOWED_USERS", ["111"])
        holder = fake_client()
        markup = {"inline_keyboard": [[{"text": "OK", "callback_data": "ok"}]]}
        _run(telegram.send_message("hi", reply_markup=markup))
        assert holder["client"].calls[0]["json"]["reply_markup"] == markup

    def test_reply_markup_omitted_when_none(self, monkeypatch, fake_client):
        monkeypatch.setattr(telegram.config, "TELEGRAM_BOT_TOKEN", "tok")
        monkeypatch.setattr(telegram.config, "TELEGRAM_ALLOWED_USERS", ["111"])
        holder = fake_client()
        _run(telegram.send_message("hi"))
        assert "reply_markup" not in holder["client"].calls[0]["json"]


class TestSendMessageOutcome:
    def test_ok_when_all_200(self, monkeypatch, fake_client):
        monkeypatch.setattr(telegram.config, "TELEGRAM_BOT_TOKEN", "tok")
        monkeypatch.setattr(telegram.config, "TELEGRAM_ALLOWED_USERS", ["111", "222"])
        fake_client(post_responses=[FakeResponse(200), FakeResponse(200)])
        result = _run(telegram.send_message("hi"))
        assert result["ok"] is True
        assert result["delivered"] == 2

    def test_not_ok_when_any_non_200(self, monkeypatch, fake_client):
        monkeypatch.setattr(telegram.config, "TELEGRAM_BOT_TOKEN", "tok")
        monkeypatch.setattr(telegram.config, "TELEGRAM_ALLOWED_USERS", ["111", "222"])
        fake_client(post_responses=[FakeResponse(200), FakeResponse(429)])
        result = _run(telegram.send_message("hi"))
        assert result["ok"] is False
        assert any(r["status_code"] == 429 for r in result["results"])

    def test_request_error_recorded_per_recipient(self, monkeypatch, fake_client):
        monkeypatch.setattr(telegram.config, "TELEGRAM_BOT_TOKEN", "tok")
        monkeypatch.setattr(telegram.config, "TELEGRAM_ALLOWED_USERS", ["111"])
        fake_client(post_raises=httpx.ConnectError("boom"))
        result = _run(telegram.send_message("hi"))
        assert result["ok"] is False
        assert result["results"][0]["status_code"] == 0
        assert "boom" in result["results"][0]["error"]

    def test_one_failure_does_not_block_others(self, monkeypatch):
        monkeypatch.setattr(telegram.config, "TELEGRAM_BOT_TOKEN", "tok")
        monkeypatch.setattr(telegram.config, "TELEGRAM_ALLOWED_USERS", ["111", "222"])

        class MixedClient:
            def __init__(self, **_):
                self.count = 0

            async def __aenter__(self):
                return self

            async def __aexit__(self, *exc):
                return False

            async def post(self, url, json=None):
                self.count += 1
                if self.count == 1:
                    raise httpx.ConnectError("first failed")
                return FakeResponse(200)

        monkeypatch.setattr(telegram.httpx, "AsyncClient", lambda **kw: MixedClient())
        result = _run(telegram.send_message("hi"))
        assert len(result["results"]) == 2
        assert result["results"][0]["status_code"] == 0
        assert result["results"][1]["status_code"] == 200
