from __future__ import annotations

import asyncio
import sys
import types


from watchdogs import drift


class TestRunDriftCheck:
    def test_no_findings_renders_clean_report(self, monkeypatch):
        async def fake_docker():
            return []

        async def fake_cron():
            return []

        monkeypatch.setattr(drift, "check_docker_drift", fake_docker)
        monkeypatch.setattr(drift, "check_cron_drift", fake_cron)
        monkeypatch.setattr(drift, "get_ssh_targets", lambda: {})

        report = asyncio.run(drift.run_drift_check())
        assert "No drift detected" in report
        assert "Config Drift Report" in report

    def test_docker_findings_rendered(self, monkeypatch):
        async def fake_docker():
            return ["🔴 <b>n8n</b> NOT RUNNING (expected)"]

        async def fake_cron():
            return []

        monkeypatch.setattr(drift, "check_docker_drift", fake_docker)
        monkeypatch.setattr(drift, "check_cron_drift", fake_cron)
        monkeypatch.setattr(drift, "get_ssh_targets", lambda: {})

        report = asyncio.run(drift.run_drift_check())
        assert "1 finding(s)" in report
        assert "n8n" in report

    def test_cron_findings_rendered(self, monkeypatch):
        async def fake_docker():
            return []

        async def fake_cron():
            return ["⚠️ Cron entry missing: <code>backup</code>"]

        monkeypatch.setattr(drift, "check_docker_drift", fake_docker)
        monkeypatch.setattr(drift, "check_cron_drift", fake_cron)
        monkeypatch.setattr(drift, "get_ssh_targets", lambda: {})

        report = asyncio.run(drift.run_drift_check())
        assert "Cron entry missing" in report
        assert "backup" in report

    def test_remote_findings_iterate_all_vps(self, monkeypatch):
        async def fake_docker():
            return []

        async def fake_cron():
            return []

        async def fake_remote(vps_name):
            return [f"🔴 <b>{vps_name}/redis</b> not running"]

        monkeypatch.setattr(drift, "check_docker_drift", fake_docker)
        monkeypatch.setattr(drift, "check_cron_drift", fake_cron)
        monkeypatch.setattr(drift, "check_remote_docker_drift", fake_remote)
        monkeypatch.setattr(drift, "get_ssh_targets", lambda: {"vps1": {}, "vps2": {}})

        report = asyncio.run(drift.run_drift_check())
        assert "vps1/redis" in report
        assert "vps2/redis" in report
        assert "2 finding(s)" in report

    def test_combined_findings(self, monkeypatch):
        async def fake_docker():
            return ["🔴 <b>n8n</b> NOT RUNNING"]

        async def fake_cron():
            return ["⚠️ Cron missing"]

        async def fake_remote(vps_name):
            return [f"❌ SSH to <b>{vps_name}</b> failed"]

        monkeypatch.setattr(drift, "check_docker_drift", fake_docker)
        monkeypatch.setattr(drift, "check_cron_drift", fake_cron)
        monkeypatch.setattr(drift, "check_remote_docker_drift", fake_remote)
        monkeypatch.setattr(drift, "get_ssh_targets", lambda: {"vps1": {}})

        report = asyncio.run(drift.run_drift_check())
        assert "3 finding(s)" in report


class TestCheckRemoteDockerDrift:
    def _stub_bot_with_docker_ps(self, monkeypatch, return_value):
        async def fake_ssh_docker_ps(name):
            if isinstance(return_value, Exception):
                raise return_value
            return return_value

        fake_bot = types.ModuleType("bot")
        fake_bot._ssh_docker_ps = fake_ssh_docker_ps
        monkeypatch.setitem(sys.modules, "bot", fake_bot)

    def test_ssh_failure_rendered(self, monkeypatch):
        self._stub_bot_with_docker_ps(monkeypatch, None)
        result = asyncio.run(drift.check_remote_docker_drift("vps1"))
        assert any("SSH to" in line and "vps1" in line for line in result)

    def test_zero_containers_warned(self, monkeypatch):
        self._stub_bot_with_docker_ps(monkeypatch, [])
        result = asyncio.run(drift.check_remote_docker_drift("vps1"))
        assert any("0 containers" in line for line in result)

    def test_down_containers_listed(self, monkeypatch):
        self._stub_bot_with_docker_ps(
            monkeypatch,
            [
                {"name": "good", "status": "Up 3 days", "image": "x"},
                {"name": "bad", "status": "Exited (1) 5 minutes ago", "image": "y"},
            ],
        )
        result = asyncio.run(drift.check_remote_docker_drift("vps1"))
        assert any("bad" in line and "vps1" in line for line in result)
        assert not any("good" in line for line in result)

    def test_all_up_returns_empty(self, monkeypatch):
        self._stub_bot_with_docker_ps(
            monkeypatch,
            [
                {"name": "n8n", "status": "Up 3 days (healthy)", "image": "x"},
                {"name": "redis", "status": "Up 5 hours", "image": "y"},
            ],
        )
        assert asyncio.run(drift.check_remote_docker_drift("vps1")) == []


class TestCheckDockerDrift:
    def _patch_subprocess(self, monkeypatch, *, stdout=b"", returncode=0, raise_exc=None):
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

    def test_subprocess_failure_returns_error(self, monkeypatch):
        self._patch_subprocess(monkeypatch, raise_exc=OSError("docker not found"))
        result = asyncio.run(drift.check_docker_drift())
        assert result == ["❌ Cannot run docker ps locally"]

    def test_all_expected_running_no_drift(self, monkeypatch):
        lines = [
            "n8n\tn8nio/n8n:2.20.7\tUp",
            "langgraph-agent\tcustom\tUp",
            "calcom\tcalcom/cal.com:latest\tUp",
            "telegram-bot\tcustom\tUp",
            "prometheus\tprom/prometheus:v3.4.0\tUp",
            "alertmanager\tprom/alertmanager:v0.28.1\tUp",
            "caddy\tcaddy:2-alpine\tUp",
        ]
        self._patch_subprocess(monkeypatch, stdout=("\n".join(lines)).encode())
        result = asyncio.run(drift.check_docker_drift())
        assert result == []

    def test_missing_container_flagged(self, monkeypatch):
        lines = ["n8n\tn8nio/n8n:2.20.7\tUp"]
        self._patch_subprocess(monkeypatch, stdout=("\n".join(lines)).encode())
        result = asyncio.run(drift.check_docker_drift())
        assert any("calcom" in f and "NOT RUNNING" in f for f in result)
        assert any("prometheus" in f and "NOT RUNNING" in f for f in result)

    def test_image_drift_flagged(self, monkeypatch):
        lines = [
            "n8n\tn8nio/n8n:1.0.0\tUp",
            "langgraph-agent\tcustom\tUp",
            "calcom\tcalcom/cal.com:latest\tUp",
            "telegram-bot\tcustom\tUp",
            "prometheus\tprom/prometheus:v3.4.0\tUp",
            "alertmanager\tprom/alertmanager:v0.28.1\tUp",
            "caddy\tcaddy:2-alpine\tUp",
        ]
        self._patch_subprocess(monkeypatch, stdout=("\n".join(lines)).encode())
        result = asyncio.run(drift.check_docker_drift())
        assert any("n8n" in f and "image drift" in f for f in result)

    def test_unexpected_container_flagged(self, monkeypatch):
        lines = [
            "n8n\tn8nio/n8n:2.20.7\tUp",
            "langgraph-agent\tcustom\tUp",
            "calcom\tcalcom/cal.com:latest\tUp",
            "telegram-bot\tcustom\tUp",
            "prometheus\tprom/prometheus:v3.4.0\tUp",
            "alertmanager\tprom/alertmanager:v0.28.1\tUp",
            "caddy\tcaddy:2-alpine\tUp",
            "rogue\trogue:latest\tUp",
        ]
        self._patch_subprocess(monkeypatch, stdout=("\n".join(lines)).encode())
        result = asyncio.run(drift.check_docker_drift())
        assert any("rogue" in f and "unexpected" in f for f in result)


class TestCheckCronDrift:
    def _patch_subprocess(self, monkeypatch, *, stdout=b"", raise_exc=None):
        class FakeProc:
            returncode = 0

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

    def test_subprocess_failure(self, monkeypatch):
        self._patch_subprocess(monkeypatch, raise_exc=OSError("crontab missing"))
        result = asyncio.run(drift.check_cron_drift())
        assert result == ["⚠️ Cannot read crontab"]

    def test_all_present_no_drift(self, monkeypatch):
        cron = b"0 * * * * /usr/bin/health_check\n0 2 * * * /usr/bin/backup\n0 4 * * * /usr/bin/sync_vault\n"
        self._patch_subprocess(monkeypatch, stdout=cron)
        result = asyncio.run(drift.check_cron_drift())
        assert result == []

    def test_missing_entry_flagged(self, monkeypatch):
        cron = b"0 * * * * /usr/bin/health_check\n"
        self._patch_subprocess(monkeypatch, stdout=cron)
        result = asyncio.run(drift.check_cron_drift())
        assert any("backup" in f for f in result)
        assert any("sync_vault" in f for f in result)


class TestDriftCheckJob:
    def _make_context(self):
        from unittest.mock import AsyncMock, MagicMock
        ctx = MagicMock()
        ctx.bot = MagicMock()
        ctx.bot.send_message = AsyncMock()
        return ctx

    def test_skips_when_no_allowed_users(self, monkeypatch):
        monkeypatch.setattr(drift, "ALLOWED_USERS", [])
        monkeypatch.setattr("infra.auth.ALLOWED_USERS", [])
        ctx = self._make_context()
        asyncio.run(drift.drift_check_job(ctx))
        ctx.bot.send_message.assert_not_awaited()

    def test_sends_when_findings(self, monkeypatch):
        monkeypatch.setattr(drift, "ALLOWED_USERS", [42])
        monkeypatch.setattr("infra.auth.ALLOWED_USERS", [42])

        async def fake_run():
            return "🔴 1 finding(s):\nbroken"

        monkeypatch.setattr(drift, "run_drift_check", fake_run)
        ctx = self._make_context()
        asyncio.run(drift.drift_check_job(ctx))
        ctx.bot.send_message.assert_awaited_once()

    def test_silent_when_clean(self, monkeypatch):
        monkeypatch.setattr(drift, "ALLOWED_USERS", [42])
        monkeypatch.setattr("infra.auth.ALLOWED_USERS", [42])

        async def fake_run():
            return "✅ No drift detected"

        monkeypatch.setattr(drift, "run_drift_check", fake_run)
        ctx = self._make_context()
        asyncio.run(drift.drift_check_job(ctx))
        ctx.bot.send_message.assert_not_awaited()

    def test_swallows_exceptions(self, monkeypatch, caplog):
        import logging
        monkeypatch.setattr(drift, "ALLOWED_USERS", [42])
        monkeypatch.setattr("infra.auth.ALLOWED_USERS", [42])

        async def fake_run():
            raise RuntimeError("docker daemon down")

        monkeypatch.setattr(drift, "run_drift_check", fake_run)
        ctx = self._make_context()
        with caplog.at_level(logging.ERROR):
            asyncio.run(drift.drift_check_job(ctx))
        assert "Drift check job failed" in caplog.text


class TestCmdDrift:
    def _make_update(self):
        from unittest.mock import AsyncMock, MagicMock
        update = MagicMock()
        update.effective_user = MagicMock()
        update.effective_user.id = 42
        update.message = MagicMock()
        update.message.reply_text = AsyncMock()
        return update

    def _make_context(self):
        from unittest.mock import MagicMock
        ctx = MagicMock()
        ctx.args = []
        return ctx

    def test_runs_check_and_replies(self, monkeypatch):
        monkeypatch.setattr(drift, "ALLOWED_USERS", [42])
        monkeypatch.setattr("infra.auth.ALLOWED_USERS", [42])

        async def fake_run():
            return "✅ Clean"

        monkeypatch.setattr(drift, "run_drift_check", fake_run)
        update = self._make_update()
        asyncio.run(drift.cmd_drift(update, self._make_context()))
        assert update.message.reply_text.await_count == 2

    def test_failure_reports_error(self, monkeypatch):
        monkeypatch.setattr(drift, "ALLOWED_USERS", [42])
        monkeypatch.setattr("infra.auth.ALLOWED_USERS", [42])

        async def fake_run():
            raise RuntimeError("docker dead")

        monkeypatch.setattr(drift, "run_drift_check", fake_run)
        update = self._make_update()
        asyncio.run(drift.cmd_drift(update, self._make_context()))
        last = update.message.reply_text.await_args_list[-1].args[0]
        assert "Drift check failed" in last
        assert "docker dead" in last
