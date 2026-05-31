from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock

from infra import config_store
from watchdogs import firewall


class TestFirewallWhitelistConfig:
    def test_default_whitelist_when_unset(self, tmp_path, monkeypatch):
        monkeypatch.setattr(config_store, "CONFIG_DIR", tmp_path)
        monkeypatch.setattr(config_store, "CONFIG_FILE", tmp_path / "config.json")
        assert firewall.get_firewall_whitelist("vps1") == {22, 80, 443}

    def test_get_returns_configured(self, tmp_path, monkeypatch):
        monkeypatch.setattr(config_store, "CONFIG_DIR", tmp_path)
        monkeypatch.setattr(config_store, "CONFIG_FILE", tmp_path / "config.json")
        config_store.config_set("firewall_whitelist", {"vps1": [22, 8080]})
        assert firewall.get_firewall_whitelist("vps1") == {22, 8080}

    def test_set_persists(self, tmp_path, monkeypatch):
        monkeypatch.setattr(config_store, "CONFIG_DIR", tmp_path)
        monkeypatch.setattr(config_store, "CONFIG_FILE", tmp_path / "config.json")
        firewall.set_firewall_whitelist("vps1", {22, 9090})
        assert firewall.get_firewall_whitelist("vps1") == {22, 9090}

    def test_add_new_port(self, tmp_path, monkeypatch):
        monkeypatch.setattr(config_store, "CONFIG_DIR", tmp_path)
        monkeypatch.setattr(config_store, "CONFIG_FILE", tmp_path / "config.json")
        assert firewall.add_firewall_port("vps1", 9090) is True
        assert 9090 in firewall.get_firewall_whitelist("vps1")

    def test_add_existing_port_returns_false(self, tmp_path, monkeypatch):
        monkeypatch.setattr(config_store, "CONFIG_DIR", tmp_path)
        monkeypatch.setattr(config_store, "CONFIG_FILE", tmp_path / "config.json")
        firewall.set_firewall_whitelist("vps1", {22, 80})
        assert firewall.add_firewall_port("vps1", 22) is False

    def test_del_existing_port(self, tmp_path, monkeypatch):
        monkeypatch.setattr(config_store, "CONFIG_DIR", tmp_path)
        monkeypatch.setattr(config_store, "CONFIG_FILE", tmp_path / "config.json")
        firewall.set_firewall_whitelist("vps1", {22, 8080})
        assert firewall.del_firewall_port("vps1", 8080) is True
        assert 8080 not in firewall.get_firewall_whitelist("vps1")

    def test_del_missing_port_returns_false(self, tmp_path, monkeypatch):
        monkeypatch.setattr(config_store, "CONFIG_DIR", tmp_path)
        monkeypatch.setattr(config_store, "CONFIG_FILE", tmp_path / "config.json")
        firewall.set_firewall_whitelist("vps1", {22})
        assert firewall.del_firewall_port("vps1", 9999) is False


class TestParseListeningPorts:
    def test_parses_ss_output(self):
        out = "LISTEN 0 128 0.0.0.0:22 0.0.0.0:* users:((\"sshd\",pid=1,fd=3))\n"
        result = firewall.parse_listening_ports(out)
        assert len(result) == 1
        assert result[0]["port"] == "22"
        assert result[0]["bind"] == "0.0.0.0"
        assert result[0]["public"] == "yes"
        assert "sshd" in result[0]["process"]

    def test_local_bind_marked_not_public(self):
        out = "LISTEN 0 128 127.0.0.1:5432 0.0.0.0:*\n"
        result = firewall.parse_listening_ports(out)
        assert result[0]["public"] == "no"

    def test_ipv6_unspecified_marked_public(self):
        out = "LISTEN 0 128 [::]:443 [::]:*\n"
        result = firewall.parse_listening_ports(out)
        assert result[0]["bind"] == "::"
        assert result[0]["public"] == "yes"

    def test_skips_blank_and_short_lines(self):
        out = "\n  \nLISTEN x y\nLISTEN 0 128 0.0.0.0:22 0.0.0.0:*\n"
        result = firewall.parse_listening_ports(out)
        assert len(result) == 1

    def test_skips_invalid_port(self):
        out = "LISTEN 0 128 0.0.0.0:abc 0.0.0.0:*\n"
        result = firewall.parse_listening_ports(out)
        assert result == []

    def test_skips_no_colon(self):
        out = "LISTEN 0 128 0.0.0.0 0.0.0.0:*\n"
        result = firewall.parse_listening_ports(out)
        assert result == []


class TestAuditVpsFirewall:
    def test_ssh_failure(self, monkeypatch):
        async def fake_ssh(vps, cmd):
            return False, "connection refused"

        monkeypatch.setattr(firewall, "ssh_exec", fake_ssh)
        result = asyncio.run(firewall.audit_vps_firewall("vps1"))
        assert result["error"] == "connection refused"
        assert result["findings"] == []

    def test_clean_no_findings(self, tmp_path, monkeypatch):
        monkeypatch.setattr(config_store, "CONFIG_DIR", tmp_path)
        monkeypatch.setattr(config_store, "CONFIG_FILE", tmp_path / "config.json")

        async def fake_ssh(vps, cmd):
            return True, "LISTEN 0 128 0.0.0.0:22 0.0.0.0:*\n"

        monkeypatch.setattr(firewall, "ssh_exec", fake_ssh)
        result = asyncio.run(firewall.audit_vps_firewall("vps1"))
        assert result["error"] is None
        assert result["findings"] == []

    def test_unauthorized_port_flagged(self, tmp_path, monkeypatch):
        monkeypatch.setattr(config_store, "CONFIG_DIR", tmp_path)
        monkeypatch.setattr(config_store, "CONFIG_FILE", tmp_path / "config.json")

        async def fake_ssh(vps, cmd):
            return True, "LISTEN 0 128 0.0.0.0:8080 0.0.0.0:*\n"

        monkeypatch.setattr(firewall, "ssh_exec", fake_ssh)
        result = asyncio.run(firewall.audit_vps_firewall("vps1"))
        assert len(result["findings"]) == 1
        assert result["findings"][0]["port"] == "8080"

    def test_local_bind_skipped(self, tmp_path, monkeypatch):
        monkeypatch.setattr(config_store, "CONFIG_DIR", tmp_path)
        monkeypatch.setattr(config_store, "CONFIG_FILE", tmp_path / "config.json")

        async def fake_ssh(vps, cmd):
            return True, "LISTEN 0 128 127.0.0.1:5432 0.0.0.0:*\n"

        monkeypatch.setattr(firewall, "ssh_exec", fake_ssh)
        result = asyncio.run(firewall.audit_vps_firewall("vps1"))
        assert result["findings"] == []


class TestRunFirewallAudit:
    def test_no_targets(self, monkeypatch):
        monkeypatch.setattr(firewall, "get_ssh_targets", lambda: {})
        report, has_warning = asyncio.run(firewall.run_firewall_audit())
        assert "No VPS targets configured" in report
        assert has_warning is False

    def test_clean_report(self, tmp_path, monkeypatch):
        monkeypatch.setattr(config_store, "CONFIG_DIR", tmp_path)
        monkeypatch.setattr(config_store, "CONFIG_FILE", tmp_path / "config.json")
        monkeypatch.setattr(firewall, "get_ssh_targets", lambda: {"vps1": {}})

        async def fake_audit(vps):
            return {"vps": vps, "error": None, "findings": [], "whitelist": [22, 80, 443]}

        monkeypatch.setattr(firewall, "audit_vps_firewall", fake_audit)
        report, has_warning = asyncio.run(firewall.run_firewall_audit())
        assert "✅" in report
        assert has_warning is False

    def test_findings_flagged(self, tmp_path, monkeypatch):
        monkeypatch.setattr(config_store, "CONFIG_DIR", tmp_path)
        monkeypatch.setattr(config_store, "CONFIG_FILE", tmp_path / "config.json")
        monkeypatch.setattr(firewall, "get_ssh_targets", lambda: {"vps1": {}})

        async def fake_audit(vps):
            return {
                "vps": vps,
                "error": None,
                "findings": [{"port": "8080", "bind": "0.0.0.0", "public": "yes", "process": ""}],
                "whitelist": [22, 80, 443],
            }

        monkeypatch.setattr(firewall, "audit_vps_firewall", fake_audit)
        report, has_warning = asyncio.run(firewall.run_firewall_audit())
        assert "🔴" in report
        assert "8080" in report
        assert has_warning is True

    def test_error_marks_warning(self, tmp_path, monkeypatch):
        monkeypatch.setattr(firewall, "get_ssh_targets", lambda: {"vps1": {}})

        async def fake_audit(vps):
            return {"vps": vps, "error": "ssh down", "findings": []}

        monkeypatch.setattr(firewall, "audit_vps_firewall", fake_audit)
        report, has_warning = asyncio.run(firewall.run_firewall_audit())
        assert "❌" in report
        assert "ssh down" in report
        assert has_warning is True


class TestFirewallAuditJob:
    def _make_context(self):
        ctx = MagicMock()
        ctx.bot = MagicMock()
        ctx.bot.send_message = AsyncMock()
        return ctx

    def test_skips_when_no_allowed_users(self, monkeypatch):
        monkeypatch.setattr(firewall, "ALLOWED_USERS", [])
        monkeypatch.setattr("infra.auth.ALLOWED_USERS", [])
        monkeypatch.setattr(firewall, "get_ssh_targets", lambda: {"v": {}})
        ctx = self._make_context()
        asyncio.run(firewall.firewall_audit_job(ctx))
        ctx.bot.send_message.assert_not_awaited()

    def test_skips_when_no_targets(self, monkeypatch):
        monkeypatch.setattr(firewall, "ALLOWED_USERS", [42])
        monkeypatch.setattr("infra.auth.ALLOWED_USERS", [42])
        monkeypatch.setattr(firewall, "get_ssh_targets", lambda: {})
        ctx = self._make_context()
        asyncio.run(firewall.firewall_audit_job(ctx))
        ctx.bot.send_message.assert_not_awaited()

    def test_sends_when_findings(self, monkeypatch):
        monkeypatch.setattr(firewall, "ALLOWED_USERS", [42])
        monkeypatch.setattr("infra.auth.ALLOWED_USERS", [42])
        monkeypatch.setattr(firewall, "get_ssh_targets", lambda: {"v": {}})

        async def fake_run():
            return "🔴 Findings", True

        monkeypatch.setattr(firewall, "run_firewall_audit", fake_run)
        ctx = self._make_context()
        asyncio.run(firewall.firewall_audit_job(ctx))
        ctx.bot.send_message.assert_awaited_once()

    def test_silent_when_clean(self, monkeypatch):
        monkeypatch.setattr(firewall, "ALLOWED_USERS", [42])
        monkeypatch.setattr("infra.auth.ALLOWED_USERS", [42])
        monkeypatch.setattr(firewall, "get_ssh_targets", lambda: {"v": {}})

        async def fake_run():
            return "✅ Clean", False

        monkeypatch.setattr(firewall, "run_firewall_audit", fake_run)
        ctx = self._make_context()
        asyncio.run(firewall.firewall_audit_job(ctx))
        ctx.bot.send_message.assert_not_awaited()

    def test_swallows_exceptions(self, monkeypatch, caplog):
        import logging
        monkeypatch.setattr(firewall, "ALLOWED_USERS", [42])
        monkeypatch.setattr("infra.auth.ALLOWED_USERS", [42])
        monkeypatch.setattr(firewall, "get_ssh_targets", lambda: {"v": {}})

        async def fake_run():
            raise RuntimeError("boom")

        monkeypatch.setattr(firewall, "run_firewall_audit", fake_run)
        ctx = self._make_context()
        with caplog.at_level(logging.ERROR):
            asyncio.run(firewall.firewall_audit_job(ctx))
        assert "Firewall audit job failed" in caplog.text


class TestCmdFirewall:
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

    def test_no_args_runs_audit(self, monkeypatch):
        monkeypatch.setattr(firewall, "ALLOWED_USERS", [42])
        monkeypatch.setattr("infra.auth.ALLOWED_USERS", [42])

        async def fake_run():
            return "✅ Clean", False

        monkeypatch.setattr(firewall, "run_firewall_audit", fake_run)
        update = self._make_update()
        asyncio.run(firewall.cmd_firewall(update, self._make_context([])))
        assert update.message.reply_text.await_count == 2

    def test_audit_failure_reports(self, monkeypatch):
        monkeypatch.setattr(firewall, "ALLOWED_USERS", [42])
        monkeypatch.setattr("infra.auth.ALLOWED_USERS", [42])

        async def fake_run():
            raise RuntimeError("ssh dead")

        monkeypatch.setattr(firewall, "run_firewall_audit", fake_run)
        update = self._make_update()
        asyncio.run(firewall.cmd_firewall(update, self._make_context([])))
        last = update.message.reply_text.await_args_list[-1].args[0]
        assert "Firewall audit failed" in last

    def test_list_no_targets(self, monkeypatch):
        monkeypatch.setattr(firewall, "ALLOWED_USERS", [42])
        monkeypatch.setattr("infra.auth.ALLOWED_USERS", [42])
        monkeypatch.setattr(firewall, "get_ssh_targets", lambda: {})
        update = self._make_update()
        asyncio.run(firewall.cmd_firewall(update, self._make_context(["list"])))
        update.message.reply_text.assert_awaited_with("📋 No VPS targets configured.")

    def test_list_shows_whitelist(self, tmp_path, monkeypatch):
        monkeypatch.setattr(firewall, "ALLOWED_USERS", [42])
        monkeypatch.setattr("infra.auth.ALLOWED_USERS", [42])
        monkeypatch.setattr(config_store, "CONFIG_DIR", tmp_path)
        monkeypatch.setattr(config_store, "CONFIG_FILE", tmp_path / "config.json")
        monkeypatch.setattr(firewall, "get_ssh_targets", lambda: {"vps1": {}})
        update = self._make_update()
        asyncio.run(firewall.cmd_firewall(update, self._make_context(["list"])))
        text = update.message.reply_text.await_args.args[0]
        assert "vps1" in text

    def test_add_invalid_port(self, monkeypatch):
        monkeypatch.setattr(firewall, "ALLOWED_USERS", [42])
        monkeypatch.setattr("infra.auth.ALLOWED_USERS", [42])
        update = self._make_update()
        asyncio.run(firewall.cmd_firewall(update, self._make_context(["add", "vps1", "abc"])))
        update.message.reply_text.assert_awaited_with("⚠️ Port must be a number.")

    def test_add_unknown_vps(self, monkeypatch):
        monkeypatch.setattr(firewall, "ALLOWED_USERS", [42])
        monkeypatch.setattr("infra.auth.ALLOWED_USERS", [42])
        monkeypatch.setattr(firewall, "get_ssh_targets", lambda: {})
        update = self._make_update()
        asyncio.run(firewall.cmd_firewall(update, self._make_context(["add", "ghost", "9090"])))
        text = update.message.reply_text.await_args.args[0]
        assert "Unknown VPS" in text

    def test_add_new_port(self, tmp_path, monkeypatch):
        monkeypatch.setattr(firewall, "ALLOWED_USERS", [42])
        monkeypatch.setattr("infra.auth.ALLOWED_USERS", [42])
        monkeypatch.setattr(config_store, "CONFIG_DIR", tmp_path)
        monkeypatch.setattr(config_store, "CONFIG_FILE", tmp_path / "config.json")
        monkeypatch.setattr(firewall, "get_ssh_targets", lambda: {"vps1": {}})
        update = self._make_update()
        asyncio.run(firewall.cmd_firewall(update, self._make_context(["add", "vps1", "9090"])))
        text = update.message.reply_text.await_args.args[0]
        assert "Added" in text
        assert 9090 in firewall.get_firewall_whitelist("vps1")

    def test_add_existing_port(self, tmp_path, monkeypatch):
        monkeypatch.setattr(firewall, "ALLOWED_USERS", [42])
        monkeypatch.setattr("infra.auth.ALLOWED_USERS", [42])
        monkeypatch.setattr(config_store, "CONFIG_DIR", tmp_path)
        monkeypatch.setattr(config_store, "CONFIG_FILE", tmp_path / "config.json")
        firewall.set_firewall_whitelist("vps1", {22})
        monkeypatch.setattr(firewall, "get_ssh_targets", lambda: {"vps1": {}})
        update = self._make_update()
        asyncio.run(firewall.cmd_firewall(update, self._make_context(["add", "vps1", "22"])))
        text = update.message.reply_text.await_args.args[0]
        assert "already in" in text

    def test_del_invalid_port(self, monkeypatch):
        monkeypatch.setattr(firewall, "ALLOWED_USERS", [42])
        monkeypatch.setattr("infra.auth.ALLOWED_USERS", [42])
        update = self._make_update()
        asyncio.run(firewall.cmd_firewall(update, self._make_context(["del", "vps1", "abc"])))
        update.message.reply_text.assert_awaited_with("⚠️ Port must be a number.")

    def test_del_existing_port(self, tmp_path, monkeypatch):
        monkeypatch.setattr(firewall, "ALLOWED_USERS", [42])
        monkeypatch.setattr("infra.auth.ALLOWED_USERS", [42])
        monkeypatch.setattr(config_store, "CONFIG_DIR", tmp_path)
        monkeypatch.setattr(config_store, "CONFIG_FILE", tmp_path / "config.json")
        firewall.set_firewall_whitelist("vps1", {22, 9090})
        update = self._make_update()
        asyncio.run(firewall.cmd_firewall(update, self._make_context(["del", "vps1", "9090"])))
        text = update.message.reply_text.await_args.args[0]
        assert "Removed" in text

    def test_del_missing_port(self, tmp_path, monkeypatch):
        monkeypatch.setattr(firewall, "ALLOWED_USERS", [42])
        monkeypatch.setattr("infra.auth.ALLOWED_USERS", [42])
        monkeypatch.setattr(config_store, "CONFIG_DIR", tmp_path)
        monkeypatch.setattr(config_store, "CONFIG_FILE", tmp_path / "config.json")
        update = self._make_update()
        asyncio.run(firewall.cmd_firewall(update, self._make_context(["del", "vps1", "9999"])))
        text = update.message.reply_text.await_args.args[0]
        assert "not in" in text

    def test_unknown_action_shows_usage(self, monkeypatch):
        monkeypatch.setattr(firewall, "ALLOWED_USERS", [42])
        monkeypatch.setattr("infra.auth.ALLOWED_USERS", [42])
        update = self._make_update()
        asyncio.run(firewall.cmd_firewall(update, self._make_context(["wat"])))
        text = update.message.reply_text.await_args.args[0]
        assert "Usage" in text
