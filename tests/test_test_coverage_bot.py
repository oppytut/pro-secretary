from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock

import httpx

from watchdogs import test_coverage as cov


def _run(coro):
    return asyncio.run(coro)


def _make_response(status_code: int, json_data=None, text: str = "") -> MagicMock:
    r = MagicMock()
    r.status_code = status_code
    r.json = lambda: (json_data if json_data is not None else {})
    r.text = text
    return r


class TestListRepos:
    def test_returns_empty_on_http_error(self, monkeypatch):
        async def fake_post(path, payload, timeout=10.0):
            return _make_response(500, text="server error")

        monkeypatch.setattr(cov, "agent_post", fake_post)
        assert _run(cov._list_repos()) == []

    def test_returns_empty_on_request_error(self, monkeypatch):
        async def fake_post(path, payload, timeout=10.0):
            raise httpx.RequestError("conn refused")

        monkeypatch.setattr(cov, "agent_post", fake_post)
        assert _run(cov._list_repos()) == []

    def test_returns_repos_on_success(self, monkeypatch):
        async def fake_post(path, payload, timeout=10.0):
            return _make_response(200, {"repos": ["foo/bar", "baz/qux"]})

        monkeypatch.setattr(cov, "agent_post", fake_post)
        assert _run(cov._list_repos()) == ["foo/bar", "baz/qux"]


class TestSetRepos:
    def test_returns_true_on_success(self, monkeypatch):
        async def fake_post(path, payload, timeout=10.0):
            return _make_response(200, {"ok": True})

        monkeypatch.setattr(cov, "agent_post", fake_post)
        assert _run(cov._set_repos(["foo/bar"])) is True

    def test_returns_false_on_error(self, monkeypatch):
        async def fake_post(path, payload, timeout=10.0):
            return _make_response(500)

        monkeypatch.setattr(cov, "agent_post", fake_post)
        assert _run(cov._set_repos(["foo/bar"])) is False

    def test_returns_false_on_request_error(self, monkeypatch):
        async def fake_post(path, payload, timeout=10.0):
            raise httpx.RequestError("conn refused")

        monkeypatch.setattr(cov, "agent_post", fake_post)
        assert _run(cov._set_repos(["foo/bar"])) is False


class TestScanRepo:
    def test_returns_data_on_success(self, monkeypatch):
        async def fake_post(path, payload, timeout=10.0):
            return _make_response(200, {"ok": True, "lowest": "x.py", "coverage": 30.0})

        monkeypatch.setattr(cov, "agent_post", fake_post)
        result = _run(cov._scan_repo("foo/bar"))
        assert result["ok"] is True
        assert result["lowest"] == "x.py"

    def test_returns_error_on_http_failure(self, monkeypatch):
        async def fake_post(path, payload, timeout=10.0):
            return _make_response(500, text="boom")

        monkeypatch.setattr(cov, "agent_post", fake_post)
        result = _run(cov._scan_repo("foo/bar"))
        assert result["ok"] is False
        assert "HTTP 500" in result["error"]

    def test_returns_error_on_request_error(self, monkeypatch):
        async def fake_post(path, payload, timeout=10.0):
            raise httpx.RequestError("conn refused")

        monkeypatch.setattr(cov, "agent_post", fake_post)
        result = _run(cov._scan_repo("foo/bar"))
        assert result["ok"] is False
        assert "request error" in result["error"]


class TestFormatScanResult:
    def test_error_format(self):
        out = cov._format_scan_result("foo/bar", {"ok": False, "error": "boom"})
        assert "⚠️" in out
        assert "boom" in out

    def test_skipped_format(self):
        out = cov._format_scan_result("foo/bar", {"ok": True, "skipped": True, "reason": "no files below threshold"})
        assert "ℹ️" in out
        assert "no files" in out

    def test_success_format(self):
        out = cov._format_scan_result(
            "foo/bar",
            {"ok": True, "lowest": "src/x.py", "coverage": 25.5, "pr_url": "https://gh/pr/3", "pr_number": 3},
        )
        assert "✅" in out
        assert "src/x.py" in out
        assert "25.5" in out
        assert "PR #3" in out


class TestCoverageScanJob:
    def _make_context(self):
        ctx = MagicMock()
        ctx.bot = MagicMock()
        ctx.bot.send_message = AsyncMock()
        return ctx

    def test_skips_when_no_allowed_users(self, monkeypatch):
        monkeypatch.setattr(cov, "ALLOWED_USERS", [])
        monkeypatch.setattr("infra.auth.ALLOWED_USERS", [])
        ctx = self._make_context()
        _run(cov.coverage_scan_job(ctx))
        ctx.bot.send_message.assert_not_awaited()

    def test_silent_when_no_repos(self, monkeypatch):
        monkeypatch.setattr(cov, "ALLOWED_USERS", [42])
        monkeypatch.setattr("infra.auth.ALLOWED_USERS", [42])

        async def fake_list():
            return []

        monkeypatch.setattr(cov, "_list_repos", fake_list)
        ctx = self._make_context()
        _run(cov.coverage_scan_job(ctx))
        ctx.bot.send_message.assert_not_awaited()

    def test_silent_when_no_pr_created(self, monkeypatch):
        monkeypatch.setattr(cov, "ALLOWED_USERS", [42])
        monkeypatch.setattr("infra.auth.ALLOWED_USERS", [42])

        async def fake_list():
            return ["foo/bar"]

        async def fake_scan(repo, branch="main"):
            return {"ok": True, "skipped": True, "reason": "no files below threshold"}

        monkeypatch.setattr(cov, "_list_repos", fake_list)
        monkeypatch.setattr(cov, "_scan_repo", fake_scan)
        ctx = self._make_context()
        _run(cov.coverage_scan_job(ctx))
        ctx.bot.send_message.assert_not_awaited()

    def test_sends_when_pr_created(self, monkeypatch):
        monkeypatch.setattr(cov, "ALLOWED_USERS", [42])
        monkeypatch.setattr("infra.auth.ALLOWED_USERS", [42])

        async def fake_list():
            return ["foo/bar"]

        async def fake_scan(repo, branch="main"):
            return {"ok": True, "lowest": "x.py", "coverage": 30.0, "pr_url": "https://gh/pr/1", "pr_number": 1}

        monkeypatch.setattr(cov, "_list_repos", fake_list)
        monkeypatch.setattr(cov, "_scan_repo", fake_scan)
        ctx = self._make_context()
        _run(cov.coverage_scan_job(ctx))
        ctx.bot.send_message.assert_awaited_once()

    def test_swallows_scan_exceptions(self, monkeypatch):
        monkeypatch.setattr(cov, "ALLOWED_USERS", [42])
        monkeypatch.setattr("infra.auth.ALLOWED_USERS", [42])

        async def fake_list():
            return ["foo/bar"]

        async def fake_scan(repo, branch="main"):
            raise RuntimeError("boom")

        monkeypatch.setattr(cov, "_list_repos", fake_list)
        monkeypatch.setattr(cov, "_scan_repo", fake_scan)
        ctx = self._make_context()
        _run(cov.coverage_scan_job(ctx))
        ctx.bot.send_message.assert_not_awaited()


class TestCmdCoverage:
    def _make_update(self):
        update = MagicMock()
        update.effective_user = MagicMock()
        update.effective_user.id = 42
        update.message = MagicMock()
        update.message.reply_text = AsyncMock()
        return update

    def _make_context(self, args):
        ctx = MagicMock()
        ctx.args = args
        return ctx

    def test_no_args_no_repos(self, monkeypatch):
        monkeypatch.setattr(cov, "ALLOWED_USERS", [42])
        monkeypatch.setattr("infra.auth.ALLOWED_USERS", [42])

        async def fake_list():
            return []

        monkeypatch.setattr(cov, "_list_repos", fake_list)
        update = self._make_update()
        _run(cov.cmd_coverage(update, self._make_context([])))
        text = update.message.reply_text.await_args.args[0]
        assert "No coverage repos" in text

    def test_no_args_runs_scan(self, monkeypatch):
        monkeypatch.setattr(cov, "ALLOWED_USERS", [42])
        monkeypatch.setattr("infra.auth.ALLOWED_USERS", [42])

        async def fake_list():
            return ["foo/bar"]

        async def fake_scan(repo, branch="main"):
            return {"ok": True, "skipped": True, "reason": "no low coverage"}

        monkeypatch.setattr(cov, "_list_repos", fake_list)
        monkeypatch.setattr(cov, "_scan_repo", fake_scan)
        update = self._make_update()
        _run(cov.cmd_coverage(update, self._make_context([])))
        assert update.message.reply_text.await_count == 2

    def test_list_empty(self, monkeypatch):
        monkeypatch.setattr(cov, "ALLOWED_USERS", [42])
        monkeypatch.setattr("infra.auth.ALLOWED_USERS", [42])

        async def fake_list():
            return []

        monkeypatch.setattr(cov, "_list_repos", fake_list)
        update = self._make_update()
        _run(cov.cmd_coverage(update, self._make_context(["list"])))
        update.message.reply_text.assert_awaited_with("📋 No coverage repos configured.")

    def test_list_shows_repos(self, monkeypatch):
        monkeypatch.setattr(cov, "ALLOWED_USERS", [42])
        monkeypatch.setattr("infra.auth.ALLOWED_USERS", [42])

        async def fake_list():
            return ["foo/bar", "baz/qux"]

        monkeypatch.setattr(cov, "_list_repos", fake_list)
        update = self._make_update()
        _run(cov.cmd_coverage(update, self._make_context(["list"])))
        text = update.message.reply_text.await_args.args[0]
        assert "foo/bar" in text
        assert "baz/qux" in text

    def test_add_new_repo(self, monkeypatch):
        monkeypatch.setattr(cov, "ALLOWED_USERS", [42])
        monkeypatch.setattr("infra.auth.ALLOWED_USERS", [42])

        async def fake_list():
            return []

        async def fake_set(repos):
            return True

        monkeypatch.setattr(cov, "_list_repos", fake_list)
        monkeypatch.setattr(cov, "_set_repos", fake_set)
        update = self._make_update()
        _run(cov.cmd_coverage(update, self._make_context(["add", "foo/bar"])))
        text = update.message.reply_text.await_args.args[0]
        assert "Added" in text

    def test_add_duplicate(self, monkeypatch):
        monkeypatch.setattr(cov, "ALLOWED_USERS", [42])
        monkeypatch.setattr("infra.auth.ALLOWED_USERS", [42])

        async def fake_list():
            return ["foo/bar"]

        monkeypatch.setattr(cov, "_list_repos", fake_list)
        update = self._make_update()
        _run(cov.cmd_coverage(update, self._make_context(["add", "foo/bar"])))
        text = update.message.reply_text.await_args.args[0]
        assert "already" in text

    def test_add_set_failure(self, monkeypatch):
        monkeypatch.setattr(cov, "ALLOWED_USERS", [42])
        monkeypatch.setattr("infra.auth.ALLOWED_USERS", [42])

        async def fake_list():
            return []

        async def fake_set(repos):
            return False

        monkeypatch.setattr(cov, "_list_repos", fake_list)
        monkeypatch.setattr(cov, "_set_repos", fake_set)
        update = self._make_update()
        _run(cov.cmd_coverage(update, self._make_context(["add", "foo/bar"])))
        text = update.message.reply_text.await_args.args[0]
        assert "Failed" in text

    def test_del_existing(self, monkeypatch):
        monkeypatch.setattr(cov, "ALLOWED_USERS", [42])
        monkeypatch.setattr("infra.auth.ALLOWED_USERS", [42])

        async def fake_list():
            return ["foo/bar"]

        async def fake_set(repos):
            return True

        monkeypatch.setattr(cov, "_list_repos", fake_list)
        monkeypatch.setattr(cov, "_set_repos", fake_set)
        update = self._make_update()
        _run(cov.cmd_coverage(update, self._make_context(["del", "foo/bar"])))
        text = update.message.reply_text.await_args.args[0]
        assert "Removed" in text

    def test_del_missing(self, monkeypatch):
        monkeypatch.setattr(cov, "ALLOWED_USERS", [42])
        monkeypatch.setattr("infra.auth.ALLOWED_USERS", [42])

        async def fake_list():
            return []

        monkeypatch.setattr(cov, "_list_repos", fake_list)
        update = self._make_update()
        _run(cov.cmd_coverage(update, self._make_context(["del", "foo/bar"])))
        text = update.message.reply_text.await_args.args[0]
        assert "not in" in text

    def test_scan_action(self, monkeypatch):
        monkeypatch.setattr(cov, "ALLOWED_USERS", [42])
        monkeypatch.setattr("infra.auth.ALLOWED_USERS", [42])

        async def fake_scan(repo, branch="main"):
            return {"ok": True, "skipped": True, "reason": "clean"}

        monkeypatch.setattr(cov, "_scan_repo", fake_scan)
        update = self._make_update()
        _run(cov.cmd_coverage(update, self._make_context(["scan", "foo/bar"])))
        assert update.message.reply_text.await_count == 2

    def test_scan_with_branch(self, monkeypatch):
        monkeypatch.setattr(cov, "ALLOWED_USERS", [42])
        monkeypatch.setattr("infra.auth.ALLOWED_USERS", [42])

        captured = {}

        async def fake_scan(repo, branch="main"):
            captured["repo"] = repo
            captured["branch"] = branch
            return {"ok": True, "skipped": True, "reason": "clean"}

        monkeypatch.setattr(cov, "_scan_repo", fake_scan)
        update = self._make_update()
        _run(cov.cmd_coverage(update, self._make_context(["scan", "foo/bar", "develop"])))
        assert captured["branch"] == "develop"

    def test_unknown_action_shows_usage(self, monkeypatch):
        monkeypatch.setattr(cov, "ALLOWED_USERS", [42])
        monkeypatch.setattr("infra.auth.ALLOWED_USERS", [42])
        update = self._make_update()
        _run(cov.cmd_coverage(update, self._make_context(["wat"])))
        text = update.message.reply_text.await_args.args[0]
        assert "Usage" in text
