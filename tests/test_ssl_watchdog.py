from __future__ import annotations

import asyncio

import pytest

from infra import config_store
from watchdogs import ssl as ssl_mod


@pytest.fixture
def store(tmp_path, monkeypatch):
    monkeypatch.setattr(config_store, "CONFIG_DIR", tmp_path)
    monkeypatch.setattr(config_store, "CONFIG_FILE", tmp_path / "config.json")
    return tmp_path


class TestSslDomainHelpers:
    def test_get_returns_env_domains_when_no_config(self, store, monkeypatch):
        monkeypatch.setattr(ssl_mod, "_SSL_ENV_DOMAINS", ["env1.com", "env2.com"])
        assert ssl_mod.get_ssl_domains() == ["env1.com", "env2.com"]

    def test_get_dedupes_env_and_config(self, store, monkeypatch):
        monkeypatch.setattr(ssl_mod, "_SSL_ENV_DOMAINS", ["shared.com", "env-only.com"])
        config_store.config_set("ssl_domains", ["shared.com", "cfg-only.com"])
        result = ssl_mod.get_ssl_domains()
        assert result.count("shared.com") == 1
        assert "env-only.com" in result
        assert "cfg-only.com" in result

    def test_get_preserves_order_config_first(self, store, monkeypatch):
        monkeypatch.setattr(ssl_mod, "_SSL_ENV_DOMAINS", ["env.com"])
        config_store.config_set("ssl_domains", ["cfg.com"])
        result = ssl_mod.get_ssl_domains()
        assert result.index("cfg.com") < result.index("env.com")

    def test_add_returns_true_for_new(self, store, monkeypatch):
        monkeypatch.setattr(ssl_mod, "_SSL_ENV_DOMAINS", [])
        assert ssl_mod.add_ssl_domain("foo.com") is True
        assert "foo.com" in ssl_mod.get_ssl_domains()

    def test_add_returns_false_for_duplicate_in_config(self, store, monkeypatch):
        monkeypatch.setattr(ssl_mod, "_SSL_ENV_DOMAINS", [])
        ssl_mod.add_ssl_domain("foo.com")
        assert ssl_mod.add_ssl_domain("foo.com") is False

    def test_del_returns_true_for_existing(self, store, monkeypatch):
        monkeypatch.setattr(ssl_mod, "_SSL_ENV_DOMAINS", [])
        ssl_mod.add_ssl_domain("foo.com")
        assert ssl_mod.del_ssl_domain("foo.com") is True
        assert "foo.com" not in ssl_mod.get_ssl_domains()

    def test_del_returns_false_for_missing(self, store, monkeypatch):
        monkeypatch.setattr(ssl_mod, "_SSL_ENV_DOMAINS", [])
        assert ssl_mod.del_ssl_domain("missing.com") is False

    def test_del_does_not_remove_env_only(self, store, monkeypatch):
        monkeypatch.setattr(ssl_mod, "_SSL_ENV_DOMAINS", ["env-only.com"])
        assert ssl_mod.del_ssl_domain("env-only.com") is False
        assert "env-only.com" in ssl_mod.get_ssl_domains()


class TestRunSslCheckFormatter:
    def test_no_domains_returns_help(self, store, monkeypatch):
        monkeypatch.setattr(ssl_mod, "_SSL_ENV_DOMAINS", [])
        report = asyncio.run(ssl_mod.run_ssl_check())
        assert "No domains configured" in report
        assert "/ssl add" in report

    def test_healthy_cert_renders_ok_line(self, store, monkeypatch):
        config_store.config_set("ssl_domains", ["good.com"])
        monkeypatch.setattr(ssl_mod, "_SSL_ENV_DOMAINS", [])

        async def fake_check(domain):
            return {"domain": domain, "days_left": 90, "expiry": "2026-08-29", "error": None}

        monkeypatch.setattr(ssl_mod, "check_ssl_expiry", fake_check)
        report = asyncio.run(ssl_mod.run_ssl_check())
        assert "✅" in report
        assert "good.com" in report
        assert "90d left" in report

    def test_expiring_soon_renders_warning(self, store, monkeypatch):
        config_store.config_set("ssl_domains", ["soon.com"])
        monkeypatch.setattr(ssl_mod, "_SSL_ENV_DOMAINS", [])
        monkeypatch.setattr(ssl_mod, "SSL_WARN_DAYS", 30)

        async def fake_check(domain):
            return {"domain": domain, "days_left": 7, "expiry": "2026-06-07", "error": None}

        monkeypatch.setattr(ssl_mod, "check_ssl_expiry", fake_check)
        report = asyncio.run(ssl_mod.run_ssl_check())
        assert "⚠️" in report
        assert "expires in 7d" in report

    def test_expired_renders_red(self, store, monkeypatch):
        config_store.config_set("ssl_domains", ["dead.com"])
        monkeypatch.setattr(ssl_mod, "_SSL_ENV_DOMAINS", [])

        async def fake_check(domain):
            return {"domain": domain, "days_left": -5, "expiry": "2026-05-26", "error": None}

        monkeypatch.setattr(ssl_mod, "check_ssl_expiry", fake_check)
        report = asyncio.run(ssl_mod.run_ssl_check())
        assert "🔴" in report
        assert "EXPIRED" in report

    def test_check_error_renders_x(self, store, monkeypatch):
        config_store.config_set("ssl_domains", ["err.com"])
        monkeypatch.setattr(ssl_mod, "_SSL_ENV_DOMAINS", [])

        async def fake_check(domain):
            return {"domain": domain, "days_left": -1, "expiry": None, "error": "DNS lookup failed"}

        monkeypatch.setattr(ssl_mod, "check_ssl_expiry", fake_check)
        report = asyncio.run(ssl_mod.run_ssl_check())
        assert "❌" in report
        assert "DNS lookup failed" in report

    def test_warn_threshold_boundary(self, store, monkeypatch):
        config_store.config_set("ssl_domains", ["edge.com"])
        monkeypatch.setattr(ssl_mod, "_SSL_ENV_DOMAINS", [])
        monkeypatch.setattr(ssl_mod, "SSL_WARN_DAYS", 30)

        async def fake_check(domain):
            return {"domain": domain, "days_left": 30, "expiry": "2026-06-30", "error": None}

        monkeypatch.setattr(ssl_mod, "check_ssl_expiry", fake_check)
        report = asyncio.run(ssl_mod.run_ssl_check())
        assert "⚠️" in report

    def test_warn_threshold_just_above(self, store, monkeypatch):
        config_store.config_set("ssl_domains", ["safe.com"])
        monkeypatch.setattr(ssl_mod, "_SSL_ENV_DOMAINS", [])
        monkeypatch.setattr(ssl_mod, "SSL_WARN_DAYS", 30)

        async def fake_check(domain):
            return {"domain": domain, "days_left": 31, "expiry": "2026-07-01", "error": None}

        monkeypatch.setattr(ssl_mod, "check_ssl_expiry", fake_check)
        report = asyncio.run(ssl_mod.run_ssl_check())
        assert "⚠️" not in report
        assert "✅" in report


class TestCheckSslExpiry:
    def test_returns_days_and_expiry_on_success(self, monkeypatch):
        async def fake_to_thread(func, host):
            return 60, "2026-07-30"

        monkeypatch.setattr(asyncio, "to_thread", fake_to_thread)
        result = asyncio.run(ssl_mod.check_ssl_expiry("example.com"))
        assert result == {
            "domain": "example.com",
            "days_left": 60,
            "expiry": "2026-07-30",
            "error": None,
        }

    def test_returns_error_on_exception(self, monkeypatch):
        async def fake_to_thread(func, host):
            raise ConnectionRefusedError("port 443 closed")

        monkeypatch.setattr(asyncio, "to_thread", fake_to_thread)
        result = asyncio.run(ssl_mod.check_ssl_expiry("bad.com"))
        assert result["days_left"] == -1
        assert result["expiry"] is None
        assert "port 443 closed" in result["error"]


class TestSslCheckJob:
    def _make_context(self):
        from unittest.mock import AsyncMock, MagicMock
        ctx = MagicMock()
        ctx.bot = MagicMock()
        ctx.bot.send_message = AsyncMock()
        return ctx

    def test_skips_when_no_allowed_users(self, store, monkeypatch):
        monkeypatch.setattr(ssl_mod, "ALLOWED_USERS", [])
        monkeypatch.setattr("infra.auth.ALLOWED_USERS", [])
        ctx = self._make_context()
        asyncio.run(ssl_mod.ssl_check_job(ctx))
        ctx.bot.send_message.assert_not_awaited()

    def test_skips_when_no_domains(self, store, monkeypatch):
        monkeypatch.setattr(ssl_mod, "ALLOWED_USERS", [42])
        monkeypatch.setattr("infra.auth.ALLOWED_USERS", [42])
        ctx = self._make_context()
        asyncio.run(ssl_mod.ssl_check_job(ctx))
        ctx.bot.send_message.assert_not_awaited()

    def test_sends_when_warnings(self, store, monkeypatch):
        monkeypatch.setattr(ssl_mod, "ALLOWED_USERS", [42])
        monkeypatch.setattr("infra.auth.ALLOWED_USERS", [42])
        config_store.config_set("ssl_domains", ["expiring.com"])

        async def fake_run():
            return "⚠️ expiring.com expires in 5 days"

        monkeypatch.setattr(ssl_mod, "run_ssl_check", fake_run)
        ctx = self._make_context()
        asyncio.run(ssl_mod.ssl_check_job(ctx))
        ctx.bot.send_message.assert_awaited_once()

    def test_silent_when_clean(self, store, monkeypatch):
        monkeypatch.setattr(ssl_mod, "ALLOWED_USERS", [42])
        monkeypatch.setattr("infra.auth.ALLOWED_USERS", [42])
        config_store.config_set("ssl_domains", ["good.com"])

        async def fake_run():
            return "✅ All certs OK"

        monkeypatch.setattr(ssl_mod, "run_ssl_check", fake_run)
        ctx = self._make_context()
        asyncio.run(ssl_mod.ssl_check_job(ctx))
        ctx.bot.send_message.assert_not_awaited()

    def test_swallows_exceptions(self, store, monkeypatch, caplog):
        import logging
        monkeypatch.setattr(ssl_mod, "ALLOWED_USERS", [42])
        monkeypatch.setattr("infra.auth.ALLOWED_USERS", [42])
        config_store.config_set("ssl_domains", ["x.com"])

        async def fake_run():
            raise RuntimeError("openssl missing")

        monkeypatch.setattr(ssl_mod, "run_ssl_check", fake_run)
        ctx = self._make_context()
        with caplog.at_level(logging.ERROR):
            asyncio.run(ssl_mod.ssl_check_job(ctx))
        assert "SSL check job failed" in caplog.text


class TestCmdSsl:
    def _make_update(self):
        from unittest.mock import AsyncMock, MagicMock
        update = MagicMock()
        update.effective_user = MagicMock()
        update.effective_user.id = 42
        update.message = MagicMock()
        update.message.reply_text = AsyncMock()
        return update

    def _make_context(self, args):
        from unittest.mock import MagicMock
        ctx = MagicMock()
        ctx.args = args
        return ctx

    def test_no_args_runs_check(self, store, monkeypatch):
        monkeypatch.setattr(ssl_mod, "ALLOWED_USERS", [42])
        monkeypatch.setattr("infra.auth.ALLOWED_USERS", [42])

        async def fake_run():
            return "✅ All OK"

        monkeypatch.setattr(ssl_mod, "run_ssl_check", fake_run)
        update = self._make_update()
        asyncio.run(ssl_mod.cmd_ssl(update, self._make_context([])))
        assert update.message.reply_text.await_count == 2

    def test_check_failure_reports_error(self, store, monkeypatch):
        monkeypatch.setattr(ssl_mod, "ALLOWED_USERS", [42])
        monkeypatch.setattr("infra.auth.ALLOWED_USERS", [42])

        async def fake_run():
            raise RuntimeError("openssl missing")

        monkeypatch.setattr(ssl_mod, "run_ssl_check", fake_run)
        update = self._make_update()
        asyncio.run(ssl_mod.cmd_ssl(update, self._make_context([])))
        last = update.message.reply_text.await_args_list[-1].args[0]
        assert "SSL check failed" in last
        assert "openssl missing" in last

    def test_list_empty(self, store, monkeypatch):
        monkeypatch.setattr(ssl_mod, "ALLOWED_USERS", [42])
        monkeypatch.setattr("infra.auth.ALLOWED_USERS", [42])
        update = self._make_update()
        asyncio.run(ssl_mod.cmd_ssl(update, self._make_context(["list"])))
        update.message.reply_text.assert_awaited_with("📋 No SSL domains configured.")

    def test_list_shows_domains(self, store, monkeypatch):
        monkeypatch.setattr(ssl_mod, "ALLOWED_USERS", [42])
        monkeypatch.setattr("infra.auth.ALLOWED_USERS", [42])
        config_store.config_set("ssl_domains", ["a.com", "b.com"])
        update = self._make_update()
        asyncio.run(ssl_mod.cmd_ssl(update, self._make_context(["list"])))
        text = update.message.reply_text.await_args.args[0]
        assert "a.com" in text and "b.com" in text

    def test_add_new(self, store, monkeypatch):
        monkeypatch.setattr(ssl_mod, "ALLOWED_USERS", [42])
        monkeypatch.setattr("infra.auth.ALLOWED_USERS", [42])
        update = self._make_update()
        asyncio.run(ssl_mod.cmd_ssl(update, self._make_context(["add", "new.com"])))
        text = update.message.reply_text.await_args.args[0]
        assert "Added" in text
        assert "new.com" in ssl_mod.get_ssl_domains()

    def test_add_duplicate(self, store, monkeypatch):
        monkeypatch.setattr(ssl_mod, "ALLOWED_USERS", [42])
        monkeypatch.setattr("infra.auth.ALLOWED_USERS", [42])
        config_store.config_set("ssl_domains", ["dup.com"])
        update = self._make_update()
        asyncio.run(ssl_mod.cmd_ssl(update, self._make_context(["add", "dup.com"])))
        text = update.message.reply_text.await_args.args[0]
        assert "already in watchlist" in text

    def test_del_existing(self, store, monkeypatch):
        monkeypatch.setattr(ssl_mod, "ALLOWED_USERS", [42])
        monkeypatch.setattr("infra.auth.ALLOWED_USERS", [42])
        config_store.config_set("ssl_domains", ["gone.com"])
        update = self._make_update()
        asyncio.run(ssl_mod.cmd_ssl(update, self._make_context(["del", "gone.com"])))
        text = update.message.reply_text.await_args.args[0]
        assert "Removed" in text

    def test_del_missing(self, store, monkeypatch):
        monkeypatch.setattr(ssl_mod, "ALLOWED_USERS", [42])
        monkeypatch.setattr("infra.auth.ALLOWED_USERS", [42])
        update = self._make_update()
        asyncio.run(ssl_mod.cmd_ssl(update, self._make_context(["del", "absent.com"])))
        text = update.message.reply_text.await_args.args[0]
        assert "not in watchlist" in text

    def test_unknown_action_shows_usage(self, store, monkeypatch):
        monkeypatch.setattr(ssl_mod, "ALLOWED_USERS", [42])
        monkeypatch.setattr("infra.auth.ALLOWED_USERS", [42])
        update = self._make_update()
        asyncio.run(ssl_mod.cmd_ssl(update, self._make_context(["wat"])))
        text = update.message.reply_text.await_args.args[0]
        assert "Usage" in text
