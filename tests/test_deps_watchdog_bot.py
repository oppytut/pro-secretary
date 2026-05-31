from __future__ import annotations

import asyncio
import sys
import types

import httpx

from watchdogs import deps


class _FakeResponse:
    def __init__(self, status_code: int, payload: dict):
        self.status_code = status_code
        self._payload = payload

    def json(self) -> dict:
        return self._payload


def _stub_bot_with_agent_post(monkeypatch, fake_response):
    async def fake_agent_post(path, payload, timeout=60.0):
        if isinstance(fake_response, Exception):
            raise fake_response
        return fake_response

    fake_bot = types.ModuleType("bot")
    fake_bot._agent_post = fake_agent_post
    monkeypatch.setitem(sys.modules, "bot", fake_bot)


class TestRunDepsCheck:
    def test_returns_report_on_success(self, monkeypatch):
        _stub_bot_with_agent_post(
            monkeypatch,
            _FakeResponse(200, {"report": "🟢 No vulnerabilities found"}),
        )
        report = asyncio.run(deps.run_deps_check())
        assert "No vulnerabilities" in report

    def test_returns_no_report_message_when_empty(self, monkeypatch):
        _stub_bot_with_agent_post(
            monkeypatch,
            _FakeResponse(200, {}),
        )
        report = asyncio.run(deps.run_deps_check())
        assert report == "ℹ️ No report."

    def test_handles_non_200(self, monkeypatch):
        _stub_bot_with_agent_post(
            monkeypatch,
            _FakeResponse(503, {}),
        )
        report = asyncio.run(deps.run_deps_check())
        assert "HTTP 503" in report

    def test_handles_request_error(self, monkeypatch):
        _stub_bot_with_agent_post(
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

        fake_bot = types.ModuleType("bot")
        fake_bot._agent_post = fake_agent_post
        monkeypatch.setitem(sys.modules, "bot", fake_bot)

        asyncio.run(deps.run_deps_check(repo_id="myrepo"))
        assert captured["path"] == "/api/deps/scan"
        assert captured["payload"] == {"repo_id": "myrepo"}

    def test_no_repo_id_sends_empty_payload(self, monkeypatch):
        captured = {}

        async def fake_agent_post(path, payload, timeout=60.0):
            captured["payload"] = payload
            return _FakeResponse(200, {"report": "ok"})

        fake_bot = types.ModuleType("bot")
        fake_bot._agent_post = fake_agent_post
        monkeypatch.setitem(sys.modules, "bot", fake_bot)

        asyncio.run(deps.run_deps_check())
        assert captured["payload"] == {}
