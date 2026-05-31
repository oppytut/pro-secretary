from __future__ import annotations

import asyncio
import importlib
from unittest.mock import AsyncMock, MagicMock

import httpx

from watchdogs import morning_brief


class _FakeResponse:
    def __init__(self, status_code: int, payload: dict):
        self.status_code = status_code
        self._payload = payload

    def json(self):
        return self._payload


class TestCollectGithubSummary:
    def test_empty_when_no_pat(self, monkeypatch):
        monkeypatch.setenv("GH_PAT", "")
        mod = importlib.reload(morning_brief)
        result = asyncio.run(mod.collect_github_summary())
        assert result == []

    def test_collects_prs_commits_failed_checks(self, monkeypatch):
        monkeypatch.setenv("GH_PAT", "ghp_x")
        mod = importlib.reload(morning_brief)
        mod._GH_REPOS[:] = ["owner/repo"]

        async def fake_gh(path):
            if "/pulls" in path:
                return [{"number": 1, "title": "fix bug", "draft": False}]
            if "/commits?" in path:
                return [
                    {"commit": {"message": "feat: x\nbody", "author": {"name": "alice"}}},
                ]
            if "/check-runs" in path:
                return {"check_runs": [{"name": "lint", "conclusion": "failure"}]}
            return None

        monkeypatch.setattr(mod, "gh_api", fake_gh)
        result = asyncio.run(mod.collect_github_summary())
        text = "\n".join(result)
        assert "owner/repo" in text
        assert "fix bug" in text
        assert "alice" in text
        assert "lint" in text

    def test_skips_empty_responses(self, monkeypatch):
        monkeypatch.setenv("GH_PAT", "ghp_x")
        mod = importlib.reload(morning_brief)
        mod._GH_REPOS[:] = ["owner/repo"]

        async def fake_gh(path):
            return None

        monkeypatch.setattr(mod, "gh_api", fake_gh)
        result = asyncio.run(mod.collect_github_summary())
        assert result == []

    def test_skips_drafts_marker(self, monkeypatch):
        monkeypatch.setenv("GH_PAT", "ghp_x")
        mod = importlib.reload(morning_brief)
        mod._GH_REPOS[:] = ["owner/repo"]

        async def fake_gh(path):
            if "/pulls" in path:
                return [{"number": 5, "title": "wip", "draft": True}]
            return None

        monkeypatch.setattr(mod, "gh_api", fake_gh)
        result = asyncio.run(mod.collect_github_summary())
        assert any("[draft]" in line for line in result)

    def test_no_failing_checks_skips_section(self, monkeypatch):
        monkeypatch.setenv("GH_PAT", "ghp_x")
        mod = importlib.reload(morning_brief)
        mod._GH_REPOS[:] = ["owner/repo"]

        async def fake_gh(path):
            if "/check-runs" in path:
                return {"check_runs": [{"name": "lint", "conclusion": "success"}]}
            return None

        monkeypatch.setattr(mod, "gh_api", fake_gh)
        result = asyncio.run(mod.collect_github_summary())
        assert not any("failing CI" in line for line in result)


class TestCollectPromSummary:
    def test_returns_warning_when_prom_unavailable(self, monkeypatch):
        async def fake_query(q):
            return []

        monkeypatch.setattr(morning_brief, "prom_query", fake_query)
        result = asyncio.run(morning_brief.collect_prom_summary())
        assert "Prometheus tidak tersedia" in result[0]

    def test_all_up_no_alerts(self, monkeypatch):
        async def fake_query(q):
            if 'up{' in q:
                return [
                    {"metric": {"instance_name": "v1"}, "value": [0, "1"]},
                    {"metric": {"instance_name": "v2"}, "value": [0, "1"]},
                ]
            if "ALERTS" in q:
                return []
            return []

        monkeypatch.setattr(morning_brief, "prom_query", fake_query)
        result = asyncio.run(morning_brief.collect_prom_summary())
        text = "\n".join(result)
        assert "Semua VPS UP" in text
        assert "No active alerts" in text

    def test_some_down(self, monkeypatch):
        async def fake_query(q):
            if 'up{' in q:
                return [
                    {"metric": {"instance_name": "v1"}, "value": [0, "1"]},
                    {"metric": {"instance_name": "v2"}, "value": [0, "0"]},
                ]
            return []

        monkeypatch.setattr(morning_brief, "prom_query", fake_query)
        result = asyncio.run(morning_brief.collect_prom_summary())
        text = "\n".join(result)
        assert "v2" in text
        assert "DOWN" in text

    def test_active_alerts_listed(self, monkeypatch):
        async def fake_query(q):
            if 'up{' in q:
                return [{"metric": {"instance_name": "v1"}, "value": [0, "1"]}]
            if "ALERTS" in q:
                return [
                    {"metric": {"alertname": "HighCPU", "severity": "warning", "instance_name": "v1"}},
                ]
            return []

        monkeypatch.setattr(morning_brief, "prom_query", fake_query)
        result = asyncio.run(morning_brief.collect_prom_summary())
        text = "\n".join(result)
        assert "HighCPU" in text
        assert "warning" in text


class TestCollectAgentBriefing:
    def test_returns_response_on_success(self, monkeypatch):
        async def fake_post(path, payload, timeout=60.0):
            return _FakeResponse(200, {"response": "Today: meeting at 10"})

        monkeypatch.setattr(morning_brief, "agent_post", fake_post)
        result = asyncio.run(morning_brief.collect_agent_briefing())
        assert result == "Today: meeting at 10"

    def test_returns_empty_on_non_200(self, monkeypatch):
        async def fake_post(path, payload, timeout=60.0):
            return _FakeResponse(503, {})

        monkeypatch.setattr(morning_brief, "agent_post", fake_post)
        result = asyncio.run(morning_brief.collect_agent_briefing())
        assert result == ""

    def test_returns_empty_on_request_error(self, monkeypatch):
        async def fake_post(path, payload, timeout=60.0):
            raise httpx.RequestError("conn refused")

        monkeypatch.setattr(morning_brief, "agent_post", fake_post)
        result = asyncio.run(morning_brief.collect_agent_briefing())
        assert result == ""


class TestBuildMorningBrief:
    def test_builds_full_brief(self, monkeypatch):
        async def fake_agent():
            return "Agent says hi"

        async def fake_prom():
            return ["✅ Semua VPS UP"]

        async def fake_gh():
            return ["📌 PR #1"]

        monkeypatch.setattr(morning_brief, "collect_agent_briefing", fake_agent)
        monkeypatch.setattr(morning_brief, "collect_prom_summary", fake_prom)
        monkeypatch.setattr(morning_brief, "collect_github_summary", fake_gh)
        text = asyncio.run(morning_brief.build_morning_brief())
        assert "Morning Standup Brief" in text
        assert "Agent says hi" in text
        assert "Semua VPS UP" in text
        assert "PR #1" in text
        assert "WIB" in text

    def test_skips_empty_sections(self, monkeypatch):
        async def fake_agent():
            return ""

        async def fake_prom():
            return []

        async def fake_gh():
            return []

        monkeypatch.setattr(morning_brief, "collect_agent_briefing", fake_agent)
        monkeypatch.setattr(morning_brief, "collect_prom_summary", fake_prom)
        monkeypatch.setattr(morning_brief, "collect_github_summary", fake_gh)
        text = asyncio.run(morning_brief.build_morning_brief())
        assert "Morning Standup Brief" in text
        assert "Infra Status" not in text
        assert "Code Activity" not in text


class TestMorningBriefJob:
    def _make_context(self):
        ctx = MagicMock()
        ctx.bot = MagicMock()
        ctx.bot.send_message = AsyncMock()
        return ctx

    def test_skips_when_no_allowed_users(self, monkeypatch):
        monkeypatch.setattr(morning_brief, "ALLOWED_USERS", [])
        monkeypatch.setattr("infra.auth.ALLOWED_USERS", [])
        ctx = self._make_context()
        asyncio.run(morning_brief.morning_brief_job(ctx))
        ctx.bot.send_message.assert_not_awaited()

    def test_sends_brief(self, monkeypatch):
        monkeypatch.setattr(morning_brief, "ALLOWED_USERS", [42])
        monkeypatch.setattr("infra.auth.ALLOWED_USERS", [42])

        async def fake_build():
            return "✨ Morning brief content"

        monkeypatch.setattr(morning_brief, "build_morning_brief", fake_build)
        ctx = self._make_context()
        asyncio.run(morning_brief.morning_brief_job(ctx))
        ctx.bot.send_message.assert_awaited_once()
        kwargs = ctx.bot.send_message.await_args.kwargs
        assert kwargs["chat_id"] == 42
        assert "Morning brief content" in kwargs["text"]

    def test_truncates_long_output(self, monkeypatch):
        monkeypatch.setattr(morning_brief, "ALLOWED_USERS", [42])
        monkeypatch.setattr("infra.auth.ALLOWED_USERS", [42])

        async def fake_build():
            return "x" * 5000

        monkeypatch.setattr(morning_brief, "build_morning_brief", fake_build)
        ctx = self._make_context()
        asyncio.run(morning_brief.morning_brief_job(ctx))
        kwargs = ctx.bot.send_message.await_args.kwargs
        assert len(kwargs["text"]) <= 4000

    def test_swallows_exceptions(self, monkeypatch, caplog):
        import logging
        monkeypatch.setattr(morning_brief, "ALLOWED_USERS", [42])
        monkeypatch.setattr("infra.auth.ALLOWED_USERS", [42])

        async def fake_build():
            raise RuntimeError("fail")

        monkeypatch.setattr(morning_brief, "build_morning_brief", fake_build)
        ctx = self._make_context()
        with caplog.at_level(logging.ERROR):
            asyncio.run(morning_brief.morning_brief_job(ctx))
        assert "Morning brief job failed" in caplog.text


class TestCmdBriefing:
    def _make_update(self):
        update = MagicMock()
        update.effective_user = MagicMock()
        update.effective_user.id = 42
        update.message = MagicMock()
        update.message.reply_text = AsyncMock()
        return update

    def _make_context(self):
        ctx = MagicMock()
        return ctx

    def test_runs_and_replies(self, monkeypatch):
        monkeypatch.setattr(morning_brief, "ALLOWED_USERS", [42])
        monkeypatch.setattr("infra.auth.ALLOWED_USERS", [42])

        async def fake_build():
            return "✨ Brief"

        monkeypatch.setattr(morning_brief, "build_morning_brief", fake_build)
        update = self._make_update()
        asyncio.run(morning_brief.cmd_briefing(update, self._make_context()))
        assert update.message.reply_text.await_count == 2

    def test_failure_reports(self, monkeypatch):
        monkeypatch.setattr(morning_brief, "ALLOWED_USERS", [42])
        monkeypatch.setattr("infra.auth.ALLOWED_USERS", [42])

        async def fake_build():
            raise RuntimeError("agent down")

        monkeypatch.setattr(morning_brief, "build_morning_brief", fake_build)
        update = self._make_update()
        asyncio.run(morning_brief.cmd_briefing(update, self._make_context()))
        last = update.message.reply_text.await_args_list[-1].args[0]
        assert "Gagal membuat briefing" in last
