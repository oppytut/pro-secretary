from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock

import httpx

from watchdogs import deps


class _FakeResponse:
    def __init__(self, status_code: int, payload: dict):
        self.status_code = status_code
        self._payload = payload

    def json(self) -> dict:
        return self._payload


def _patch_agent_post(monkeypatch, fake_response):
    async def fake_agent_post(path, payload, timeout=60.0):
        if isinstance(fake_response, Exception):
            raise fake_response
        return fake_response

    monkeypatch.setattr(deps, "agent_post", fake_agent_post)


class TestRunDepsCheck:
    def test_returns_report_on_success(self, monkeypatch):
        _patch_agent_post(
            monkeypatch,
            _FakeResponse(200, {"report": "🟢 No vulnerabilities found"}),
        )
        report = asyncio.run(deps.run_deps_check())
        assert "No vulnerabilities" in report

    def test_returns_no_report_message_when_empty(self, monkeypatch):
        _patch_agent_post(
            monkeypatch,
            _FakeResponse(200, {}),
        )
        report = asyncio.run(deps.run_deps_check())
        assert report == "ℹ️ No report."

    def test_handles_non_200(self, monkeypatch):
        _patch_agent_post(
            monkeypatch,
            _FakeResponse(503, {}),
        )
        report = asyncio.run(deps.run_deps_check())
        assert "HTTP 503" in report

    def test_handles_request_error(self, monkeypatch):
        _patch_agent_post(
            monkeypatch,
            httpx.RequestError("connection refused"),
        )
        report = asyncio.run(deps.run_deps_check())
        assert "Gagal menghubungi agent" in report
        assert "connection refused" in report

    def test_passes_repo_id_in_payload(self, monkeypatch):
        captured = {}

        async def fake_agent_post(path, payload, timeout=60.0):
            captured["payload"] = payload
            captured["path"] = path
            return _FakeResponse(200, {"report": "ok"})

        monkeypatch.setattr(deps, "agent_post", fake_agent_post)

        asyncio.run(deps.run_deps_check(repo_id="myrepo"))
        assert captured["path"] == "/api/deps/scan"
        assert captured["payload"] == {"repo_id": "myrepo"}

    def test_no_repo_id_sends_empty_payload(self, monkeypatch):
        captured = {}

        async def fake_agent_post(path, payload, timeout=60.0):
            captured["payload"] = payload
            return _FakeResponse(200, {"report": "ok"})

        monkeypatch.setattr(deps, "agent_post", fake_agent_post)

        asyncio.run(deps.run_deps_check())
        assert captured["payload"] == {}


class TestDepsCheckJob:
    def _make_context(self):
        ctx = MagicMock()
        ctx.bot = MagicMock()
        ctx.bot.send_message = AsyncMock()
        return ctx

    def test_skips_when_no_allowed_users(self, monkeypatch):
        monkeypatch.setattr(deps, "ALLOWED_USERS", [])
        ctx = self._make_context()
        asyncio.run(deps.deps_check_job(ctx))
        ctx.bot.send_message.assert_not_awaited()

    def test_sends_message_when_vulns_found(self, monkeypatch):
        monkeypatch.setattr(deps, "ALLOWED_USERS", [42])

        async def fake_run(repo_id=None):
            return "🔴 Critical vuln found"

        monkeypatch.setattr(deps, "run_deps_check", fake_run)
        ctx = self._make_context()
        asyncio.run(deps.deps_check_job(ctx))
        ctx.bot.send_message.assert_awaited_once()
        kwargs = ctx.bot.send_message.await_args.kwargs
        assert kwargs["chat_id"] == 42
        assert "🔴" in kwargs["text"]

    def test_silent_when_no_vulns(self, monkeypatch):
        monkeypatch.setattr(deps, "ALLOWED_USERS", [42])

        async def fake_run(repo_id=None):
            return "✅ All clean"

        monkeypatch.setattr(deps, "run_deps_check", fake_run)
        ctx = self._make_context()
        asyncio.run(deps.deps_check_job(ctx))
        ctx.bot.send_message.assert_not_awaited()

    def test_handles_orange_yellow_severity(self, monkeypatch):
        monkeypatch.setattr(deps, "ALLOWED_USERS", [42])

        async def fake_run(repo_id=None):
            return "🟠 Medium severity vuln"

        monkeypatch.setattr(deps, "run_deps_check", fake_run)
        ctx = self._make_context()
        asyncio.run(deps.deps_check_job(ctx))
        ctx.bot.send_message.assert_awaited_once()

    def test_swallows_exceptions(self, monkeypatch, caplog):
        import logging

        monkeypatch.setattr(deps, "ALLOWED_USERS", [42])

        async def fake_run(repo_id=None):
            raise RuntimeError("agent down")

        monkeypatch.setattr(deps, "run_deps_check", fake_run)
        ctx = self._make_context()
        with caplog.at_level(logging.ERROR):
            asyncio.run(deps.deps_check_job(ctx))
        assert "Deps check job failed: agent down" in caplog.text
        ctx.bot.send_message.assert_not_awaited()

    def test_truncates_long_report(self, monkeypatch):
        monkeypatch.setattr(deps, "ALLOWED_USERS", [42])

        async def fake_run(repo_id=None):
            return "🔴 " + ("x" * 5000)

        monkeypatch.setattr(deps, "run_deps_check", fake_run)
        ctx = self._make_context()
        asyncio.run(deps.deps_check_job(ctx))
        kwargs = ctx.bot.send_message.await_args.kwargs
        assert len(kwargs["text"]) <= 4000
