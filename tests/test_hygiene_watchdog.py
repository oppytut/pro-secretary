from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock

from watchdogs import hygiene


class TestDockerSizeToGb:
    def test_empty_returns_zero(self):
        assert hygiene._docker_size_to_gb("") == 0.0

    def test_kilobytes(self):
        assert hygiene._docker_size_to_gb("1024KB") == pytest_approx(1024 / (1024 * 1024))

    def test_megabytes(self):
        assert hygiene._docker_size_to_gb("512MB") == pytest_approx(0.5)

    def test_gigabytes(self):
        assert hygiene._docker_size_to_gb("3.5GB") == 3.5

    def test_terabytes(self):
        assert hygiene._docker_size_to_gb("2TB") == 2048.0

    def test_bytes_fallback(self):
        assert hygiene._docker_size_to_gb("1073741824") == pytest_approx(1.0)

    def test_invalid_returns_zero(self):
        assert hygiene._docker_size_to_gb("garbage") == 0.0


def pytest_approx(value, rel=1e-3):
    import pytest
    return pytest.approx(value, rel=rel)


class TestParseDockerDf:
    def test_parses_full_output(self):
        out = (
            "TYPE\tTOTAL\tACTIVE\tSIZE\tRECLAIMABLE\n"
            "Images\t10\t5\t2GB\t500MB (25%)\n"
            "Containers\t5\t3\t100MB\t50MB (50%)\n"
            "Local Volumes\t3\t2\t1GB\t0B (0%)\n"
            "Build Cache\t8\t0\t512MB\t512MB (100%)\n"
        )
        parsed = hygiene.parse_docker_df(out)
        assert parsed["Images"]["total"] == 10
        assert parsed["Images"]["size_gb"] == 2.0
        assert parsed["Images"]["reclaimable_gb"] == pytest_approx(500 / 1024)
        assert parsed["Containers"]["total"] == 5
        assert parsed["Build Cache"]["reclaimable_gb"] == pytest_approx(0.5)

    def test_skips_header_and_blank(self):
        out = "TYPE\tTOTAL\tACTIVE\tSIZE\tRECLAIMABLE\n\n   \nImages\t1\t1\t1GB\t0B\n"
        parsed = hygiene.parse_docker_df(out)
        assert "Images" in parsed
        assert len(parsed) == 1

    def test_handles_invalid_total(self):
        out = "Images\tabc\t1\t1GB\t0B\n"
        parsed = hygiene.parse_docker_df(out)
        assert parsed["Images"]["total"] == 0

    def test_skips_short_lines(self):
        out = "Images\t1\t1\n"
        parsed = hygiene.parse_docker_df(out)
        assert parsed == {}


class TestDockerDfLocal:
    def _patch(self, monkeypatch, *, returncode=0, stdout=b"", raise_exc=None):
        class FakeProc:
            def __init__(self):
                self.returncode = returncode

            async def communicate(self):
                return stdout, b""

        async def fake_create(*args, **kwargs):
            if raise_exc is not None:
                raise raise_exc
            return FakeProc()

        async def fake_wait_for(coro, timeout=None):
            return await coro

        monkeypatch.setattr(asyncio, "create_subprocess_exec", fake_create)
        monkeypatch.setattr(asyncio, "wait_for", fake_wait_for)

    def test_returns_none_on_subprocess_failure(self, monkeypatch):
        self._patch(monkeypatch, raise_exc=OSError("docker missing"))
        assert asyncio.run(hygiene.docker_df_local()) is None

    def test_returns_none_on_nonzero_exit(self, monkeypatch):
        self._patch(monkeypatch, returncode=1)
        assert asyncio.run(hygiene.docker_df_local()) is None

    def test_parses_output(self, monkeypatch):
        out = b"Images\t5\t3\t1GB\t100MB\n"
        self._patch(monkeypatch, stdout=out)
        result = asyncio.run(hygiene.docker_df_local())
        assert result is not None
        assert result["Images"]["total"] == 5


class TestDockerDfRemote:
    def test_returns_none_on_ssh_failure(self, monkeypatch):
        async def fake_ssh_exec(vps, cmd):
            return False, "connection refused"

        monkeypatch.setattr(hygiene, "ssh_exec", fake_ssh_exec)
        assert asyncio.run(hygiene.docker_df_remote("vps1")) is None

    def test_returns_none_on_empty_output(self, monkeypatch):
        async def fake_ssh_exec(vps, cmd):
            return True, ""

        monkeypatch.setattr(hygiene, "ssh_exec", fake_ssh_exec)
        assert asyncio.run(hygiene.docker_df_remote("vps1")) is None

    def test_parses_output(self, monkeypatch):
        async def fake_ssh_exec(vps, cmd):
            return True, "Images\t3\t2\t500MB\t50MB\n"

        monkeypatch.setattr(hygiene, "ssh_exec", fake_ssh_exec)
        result = asyncio.run(hygiene.docker_df_remote("vps1"))
        assert result is not None
        assert result["Images"]["total"] == 3


class TestDockerPruneLocal:
    def _patch(self, monkeypatch, *, returncode=0, stdout=b"", stderr=b"", raise_exc=None):
        class FakeProc:
            def __init__(self):
                self.returncode = returncode

            async def communicate(self):
                return stdout, stderr

        async def fake_create(*args, **kwargs):
            if raise_exc is not None:
                raise raise_exc
            return FakeProc()

        async def fake_wait_for(coro, timeout=None):
            return await coro

        monkeypatch.setattr(asyncio, "create_subprocess_exec", fake_create)
        monkeypatch.setattr(asyncio, "wait_for", fake_wait_for)

    def test_subprocess_failure(self, monkeypatch):
        self._patch(monkeypatch, raise_exc=OSError("docker not found"))
        ok, msg = asyncio.run(hygiene.docker_prune_local())
        assert ok is False
        assert "docker not found" in msg

    def test_nonzero_exit(self, monkeypatch):
        self._patch(monkeypatch, returncode=1, stderr=b"permission denied")
        ok, msg = asyncio.run(hygiene.docker_prune_local())
        assert ok is False
        assert "permission denied" in msg

    def test_success(self, monkeypatch):
        self._patch(monkeypatch, returncode=0, stdout=b"Deleted: sha256:abc\nTotal reclaimed space: 1.2GB\n")
        ok, msg = asyncio.run(hygiene.docker_prune_local())
        assert ok is True
        assert "1.2GB" in msg


class TestDockerPruneRemote:
    def test_ssh_failure(self, monkeypatch):
        async def fake_ssh(vps, cmd):
            return False, "no auth"

        monkeypatch.setattr(hygiene, "ssh_exec", fake_ssh)
        ok, msg = asyncio.run(hygiene.docker_prune_remote("vps1"))
        assert ok is False
        assert "no auth" in msg

    def test_success_returns_last_line(self, monkeypatch):
        async def fake_ssh(vps, cmd):
            return True, "Deleted x\nDeleted y\nTotal reclaimed space: 800MB\n"

        monkeypatch.setattr(hygiene, "ssh_exec", fake_ssh)
        ok, msg = asyncio.run(hygiene.docker_prune_remote("vps1"))
        assert ok is True
        assert "800MB" in msg

    def test_success_blank_output(self, monkeypatch):
        async def fake_ssh(vps, cmd):
            return True, ""

        monkeypatch.setattr(hygiene, "ssh_exec", fake_ssh)
        ok, msg = asyncio.run(hygiene.docker_prune_remote("vps1"))
        assert ok is True
        assert msg == ""


class TestRunDockerHygiene:
    def test_local_only_clean(self, monkeypatch):
        async def fake_local():
            return {"Images": {"total": 1, "size_gb": 0.5, "reclaimable_gb": 0.1}}

        monkeypatch.setattr(hygiene, "docker_df_local", fake_local)
        monkeypatch.setattr(hygiene, "get_ssh_targets", lambda: {})
        report, has_warning = asyncio.run(hygiene.run_docker_hygiene())
        assert has_warning is False
        assert "✅" in report
        assert "pro-secretary" in report

    def test_local_threshold_breached(self, monkeypatch):
        async def fake_local():
            return {"Images": {"total": 10, "size_gb": 20.0, "reclaimable_gb": 10.0}}

        monkeypatch.setattr(hygiene, "docker_df_local", fake_local)
        monkeypatch.setattr(hygiene, "get_ssh_targets", lambda: {})
        report, has_warning = asyncio.run(hygiene.run_docker_hygiene())
        assert has_warning is True
        assert "⚠️" in report

    def test_local_df_failure(self, monkeypatch):
        async def fake_local():
            return None

        monkeypatch.setattr(hygiene, "docker_df_local", fake_local)
        monkeypatch.setattr(hygiene, "get_ssh_targets", lambda: {})
        report, has_warning = asyncio.run(hygiene.run_docker_hygiene())
        assert has_warning is True
        assert "❌" in report
        assert "cannot read docker system df" in report

    def test_includes_remote_targets(self, monkeypatch):
        async def fake_local():
            return {"Images": {"total": 1, "size_gb": 0.5, "reclaimable_gb": 0.1}}

        async def fake_remote(vps):
            return {"Images": {"total": 2, "size_gb": 1.0, "reclaimable_gb": 0.2}}

        monkeypatch.setattr(hygiene, "docker_df_local", fake_local)
        monkeypatch.setattr(hygiene, "docker_df_remote", fake_remote)
        monkeypatch.setattr(hygiene, "get_ssh_targets", lambda: {"vps1": {}, "vps2": {}})
        report, _ = asyncio.run(hygiene.run_docker_hygiene())
        assert "vps1" in report
        assert "vps2" in report
        assert "pro-secretary" in report

    def test_auto_prune_when_threshold_breached(self, monkeypatch):
        async def fake_local():
            return {"Images": {"total": 10, "size_gb": 20.0, "reclaimable_gb": 10.0}}

        prune_called = []

        async def fake_prune():
            prune_called.append(True)
            return True, "freed 8GB"

        monkeypatch.setattr(hygiene, "docker_df_local", fake_local)
        monkeypatch.setattr(hygiene, "docker_prune_local", fake_prune)
        monkeypatch.setattr(hygiene, "get_ssh_targets", lambda: {})
        monkeypatch.setattr(hygiene, "DOCKER_HYGIENE_AUTO_PRUNE", True)
        report, _ = asyncio.run(hygiene.run_docker_hygiene(auto_prune=True))
        assert prune_called == [True]
        assert "Pruned dangling images" in report

    def test_auto_prune_failure_reported(self, monkeypatch):
        async def fake_local():
            return {"Images": {"total": 10, "size_gb": 20.0, "reclaimable_gb": 10.0}}

        async def fake_prune():
            return False, "permission denied"

        monkeypatch.setattr(hygiene, "docker_df_local", fake_local)
        monkeypatch.setattr(hygiene, "docker_prune_local", fake_prune)
        monkeypatch.setattr(hygiene, "get_ssh_targets", lambda: {})
        monkeypatch.setattr(hygiene, "DOCKER_HYGIENE_AUTO_PRUNE", True)
        report, _ = asyncio.run(hygiene.run_docker_hygiene(auto_prune=True))
        assert "Prune failed" in report


class TestHygieneJob:
    def _make_context(self):
        ctx = MagicMock()
        ctx.bot = MagicMock()
        ctx.bot.send_message = AsyncMock()
        return ctx

    def test_skips_when_no_allowed_users(self, monkeypatch):
        monkeypatch.setattr(hygiene, "ALLOWED_USERS", [])
        monkeypatch.setattr("infra.auth.ALLOWED_USERS", [])
        ctx = self._make_context()
        asyncio.run(hygiene.docker_hygiene_job(ctx))
        ctx.bot.send_message.assert_not_awaited()

    def test_sends_when_warnings(self, monkeypatch):
        monkeypatch.setattr(hygiene, "ALLOWED_USERS", [42])
        monkeypatch.setattr("infra.auth.ALLOWED_USERS", [42])

        async def fake_run(auto_prune):
            return "⚠️ Warnings", True

        monkeypatch.setattr(hygiene, "run_docker_hygiene", fake_run)
        ctx = self._make_context()
        asyncio.run(hygiene.docker_hygiene_job(ctx))
        ctx.bot.send_message.assert_awaited_once()

    def test_silent_when_clean(self, monkeypatch):
        monkeypatch.setattr(hygiene, "ALLOWED_USERS", [42])
        monkeypatch.setattr("infra.auth.ALLOWED_USERS", [42])

        async def fake_run(auto_prune):
            return "✅ Clean", False

        monkeypatch.setattr(hygiene, "run_docker_hygiene", fake_run)
        ctx = self._make_context()
        asyncio.run(hygiene.docker_hygiene_job(ctx))
        ctx.bot.send_message.assert_not_awaited()

    def test_swallows_exceptions(self, monkeypatch, caplog):
        import logging
        monkeypatch.setattr(hygiene, "ALLOWED_USERS", [42])
        monkeypatch.setattr("infra.auth.ALLOWED_USERS", [42])

        async def fake_run(auto_prune):
            raise RuntimeError("docker daemon down")

        monkeypatch.setattr(hygiene, "run_docker_hygiene", fake_run)
        ctx = self._make_context()
        with caplog.at_level(logging.ERROR):
            asyncio.run(hygiene.docker_hygiene_job(ctx))
        assert "Docker hygiene job failed" in caplog.text


class TestCmdHygiene:
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

    def test_runs_check_and_replies(self, monkeypatch):
        monkeypatch.setattr(hygiene, "ALLOWED_USERS", [42])
        monkeypatch.setattr("infra.auth.ALLOWED_USERS", [42])

        async def fake_run(auto_prune):
            return "✅ Clean", False

        monkeypatch.setattr(hygiene, "run_docker_hygiene", fake_run)
        update = self._make_update()
        asyncio.run(hygiene.cmd_hygiene(update, self._make_context()))
        assert update.message.reply_text.await_count == 2

    def test_failure_reports_error(self, monkeypatch):
        monkeypatch.setattr(hygiene, "ALLOWED_USERS", [42])
        monkeypatch.setattr("infra.auth.ALLOWED_USERS", [42])

        async def fake_run(auto_prune):
            raise RuntimeError("docker dead")

        monkeypatch.setattr(hygiene, "run_docker_hygiene", fake_run)
        update = self._make_update()
        asyncio.run(hygiene.cmd_hygiene(update, self._make_context()))
        last = update.message.reply_text.await_args_list[-1].args[0]
        assert "Hygiene check failed" in last
        assert "docker dead" in last
