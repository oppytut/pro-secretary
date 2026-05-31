from __future__ import annotations

import asyncio
import sys
import types

import pytest

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
