from __future__ import annotations

import asyncio

import pytest

from infra import config_store
from watchdogs import dns


@pytest.fixture
def store(tmp_path, monkeypatch):
    monkeypatch.setattr(config_store, "CONFIG_DIR", tmp_path)
    monkeypatch.setattr(config_store, "CONFIG_FILE", tmp_path / "config.json")
    return tmp_path


class TestDomainListHelpers:
    def test_get_dns_domains_empty_when_no_config_no_ssl(self, store, monkeypatch):
        monkeypatch.setattr(dns, "get_ssl_domains", lambda: [])
        assert dns.get_dns_domains() == []

    def test_get_dns_domains_falls_back_to_ssl_seed(self, store, monkeypatch):
        monkeypatch.setattr(dns, "get_ssl_domains", lambda: ["a.com", "b.com"])
        assert dns.get_dns_domains() == ["a.com", "b.com"]

    def test_explicit_dns_config_overrides_ssl_seed(self, store, monkeypatch):
        monkeypatch.setattr(dns, "get_ssl_domains", lambda: ["from-ssl.com"])
        config_store.config_set("dns_domains", ["explicit.com"])
        assert dns.get_dns_domains() == ["explicit.com"]

    def test_explicit_empty_list_is_respected(self, store, monkeypatch):
        monkeypatch.setattr(dns, "get_ssl_domains", lambda: ["seed.com"])
        config_store.config_set("dns_domains", [])
        assert dns.get_dns_domains() == []

    def test_add_returns_true_for_new_domain(self, store, monkeypatch):
        monkeypatch.setattr(dns, "get_ssl_domains", lambda: [])
        assert dns.add_dns_domain("foo.com") is True
        assert dns.get_dns_domains() == ["foo.com"]

    def test_add_returns_false_for_duplicate(self, store, monkeypatch):
        monkeypatch.setattr(dns, "get_ssl_domains", lambda: [])
        dns.add_dns_domain("foo.com")
        assert dns.add_dns_domain("foo.com") is False
        assert dns.get_dns_domains() == ["foo.com"]

    def test_add_seeds_from_ssl_on_first_use(self, store, monkeypatch):
        monkeypatch.setattr(dns, "get_ssl_domains", lambda: ["a.com", "b.com"])
        assert dns.add_dns_domain("c.com") is True
        assert dns.get_dns_domains() == ["a.com", "b.com", "c.com"]

    def test_del_returns_true_for_existing(self, store, monkeypatch):
        monkeypatch.setattr(dns, "get_ssl_domains", lambda: [])
        dns.add_dns_domain("foo.com")
        assert dns.del_dns_domain("foo.com") is True
        assert dns.get_dns_domains() == []

    def test_del_returns_false_for_missing(self, store, monkeypatch):
        monkeypatch.setattr(dns, "get_ssl_domains", lambda: [])
        assert dns.del_dns_domain("missing.com") is False

    def test_del_seeds_from_ssl_on_first_use(self, store, monkeypatch):
        monkeypatch.setattr(dns, "get_ssl_domains", lambda: ["a.com", "b.com"])
        assert dns.del_dns_domain("a.com") is True
        assert dns.get_dns_domains() == ["b.com"]


class TestCheckDomainConsistency:
    def test_all_resolvers_agree(self, monkeypatch):
        async def fake_dig(domain, resolver, rtype="A"):
            return ["1.2.3.4"], None

        monkeypatch.setattr(dns, "dig_record", fake_dig)
        result = asyncio.run(dns.check_domain_consistency("example.com"))
        assert result["domain"] == "example.com"
        assert result["consistent"] is True
        assert result["any_error"] is False
        assert result["any_empty"] is False
        assert len(result["record_sets"]) == 1

    def test_resolvers_diverge(self, monkeypatch):
        async def fake_dig(domain, resolver, rtype="A"):
            if resolver == "1.1.1.1":
                return ["1.2.3.4"], None
            return ["5.6.7.8"], None

        monkeypatch.setattr(dns, "dig_record", fake_dig)
        result = asyncio.run(dns.check_domain_consistency("example.com"))
        assert result["consistent"] is False
        assert len(result["record_sets"]) == 2

    def test_resolver_error_flagged(self, monkeypatch):
        async def fake_dig(domain, resolver, rtype="A"):
            if resolver == "1.1.1.1":
                return [], "timeout"
            return ["1.2.3.4"], None

        monkeypatch.setattr(dns, "dig_record", fake_dig)
        result = asyncio.run(dns.check_domain_consistency("example.com"))
        assert result["any_error"] is True
        assert result["results"]["Cloudflare"]["error"] == "timeout"
        assert result["results"]["Google"]["error"] is None

    def test_empty_response_flagged(self, monkeypatch):
        async def fake_dig(domain, resolver, rtype="A"):
            if resolver == "9.9.9.9":
                return [], None
            return ["1.2.3.4"], None

        monkeypatch.setattr(dns, "dig_record", fake_dig)
        result = asyncio.run(dns.check_domain_consistency("example.com"))
        assert result["any_empty"] is True
        assert result["results"]["Quad9"]["records"] == []

    def test_multiple_records_sorted_consistently(self, monkeypatch):
        async def fake_dig(domain, resolver, rtype="A"):
            return ["1.2.3.4", "5.6.7.8"], None

        monkeypatch.setattr(dns, "dig_record", fake_dig)
        result = asyncio.run(dns.check_domain_consistency("example.com"))
        assert result["consistent"] is True


class TestRunDnsCheckFormatter:
    def test_no_domains_returns_help_message(self, store, monkeypatch):
        monkeypatch.setattr(dns, "get_ssl_domains", lambda: [])
        report = asyncio.run(dns.run_dns_check())
        assert "No DNS domains configured" in report
        assert "/dns add" in report

    def test_all_consistent_renders_ok_lines(self, store, monkeypatch):
        config_store.config_set("dns_domains", ["example.com"])
        monkeypatch.setattr(dns, "get_ssl_domains", lambda: [])

        async def fake_check(domain):
            return {
                "domain": domain,
                "consistent": True,
                "results": {
                    "Cloudflare": {"records": ["1.2.3.4"], "error": None},
                    "Google": {"records": ["1.2.3.4"], "error": None},
                    "Quad9": {"records": ["1.2.3.4"], "error": None},
                },
                "any_error": False,
                "any_empty": False,
                "record_sets": [["1.2.3.4"]],
            }

        monkeypatch.setattr(dns, "check_domain_consistency", fake_check)
        report = asyncio.run(dns.run_dns_check())
        assert "DNS Health Monitor" in report
        assert "✅" in report
        assert "1.2.3.4" in report
        assert "🔴" not in report
        assert "❌" not in report

    def test_divergence_renders_red_warning(self, store, monkeypatch):
        config_store.config_set("dns_domains", ["bad.com"])
        monkeypatch.setattr(dns, "get_ssl_domains", lambda: [])

        async def fake_check(domain):
            return {
                "domain": domain,
                "consistent": False,
                "results": {
                    "Cloudflare": {"records": ["1.2.3.4"], "error": None},
                    "Google": {"records": ["5.6.7.8"], "error": None},
                    "Quad9": {"records": ["1.2.3.4"], "error": None},
                },
                "any_error": False,
                "any_empty": False,
                "record_sets": [["1.2.3.4"], ["5.6.7.8"]],
            }

        monkeypatch.setattr(dns, "check_domain_consistency", fake_check)
        report = asyncio.run(dns.run_dns_check())
        assert "🔴" in report
        assert "divergent" in report
        assert "bad.com" in report

    def test_resolver_error_renders_x_warning(self, store, monkeypatch):
        config_store.config_set("dns_domains", ["err.com"])
        monkeypatch.setattr(dns, "get_ssl_domains", lambda: [])

        async def fake_check(domain):
            return {
                "domain": domain,
                "consistent": True,
                "results": {
                    "Cloudflare": {"records": [], "error": "timeout"},
                    "Google": {"records": ["1.2.3.4"], "error": None},
                    "Quad9": {"records": ["1.2.3.4"], "error": None},
                },
                "any_error": True,
                "any_empty": False,
                "record_sets": [["1.2.3.4"]],
            }

        monkeypatch.setattr(dns, "check_domain_consistency", fake_check)
        report = asyncio.run(dns.run_dns_check())
        assert "❌" in report
        assert "Cloudflare=timeout" in report
        assert "err.com" in report

    def test_empty_response_renders_warning(self, store, monkeypatch):
        config_store.config_set("dns_domains", ["empty.com"])
        monkeypatch.setattr(dns, "get_ssl_domains", lambda: [])

        async def fake_check(domain):
            return {
                "domain": domain,
                "consistent": True,
                "results": {
                    "Cloudflare": {"records": [], "error": None},
                    "Google": {"records": ["1.2.3.4"], "error": None},
                    "Quad9": {"records": ["1.2.3.4"], "error": None},
                },
                "any_error": False,
                "any_empty": True,
                "record_sets": [["1.2.3.4"]],
            }

        monkeypatch.setattr(dns, "check_domain_consistency", fake_check)
        report = asyncio.run(dns.run_dns_check())
        assert "⚠️" in report
        assert "empty response" in report
        assert "Cloudflare" in report

    def test_mixed_ok_and_warnings(self, store, monkeypatch):
        config_store.config_set("dns_domains", ["good.com", "bad.com"])
        monkeypatch.setattr(dns, "get_ssl_domains", lambda: [])

        async def fake_check(domain):
            if domain == "good.com":
                return {
                    "domain": domain,
                    "consistent": True,
                    "results": {
                        "Cloudflare": {"records": ["1.1.1.1"], "error": None},
                        "Google": {"records": ["1.1.1.1"], "error": None},
                        "Quad9": {"records": ["1.1.1.1"], "error": None},
                    },
                    "any_error": False,
                    "any_empty": False,
                    "record_sets": [["1.1.1.1"]],
                }
            return {
                "domain": domain,
                "consistent": False,
                "results": {
                    "Cloudflare": {"records": ["2.2.2.2"], "error": None},
                    "Google": {"records": ["3.3.3.3"], "error": None},
                    "Quad9": {"records": ["2.2.2.2"], "error": None},
                },
                "any_error": False,
                "any_empty": False,
                "record_sets": [["2.2.2.2"], ["3.3.3.3"]],
            }

        monkeypatch.setattr(dns, "check_domain_consistency", fake_check)
        report = asyncio.run(dns.run_dns_check())
        assert "good.com" in report
        assert "bad.com" in report
        assert "✅" in report
        assert "🔴" in report


class TestDigRecord:
    def _patch_subprocess(self, monkeypatch, *, returncode=0, stdout=b"", stderr=b"", timeout_flag=False, file_not_found=False, generic_exc=None):
        class FakeProc:
            def __init__(self):
                self.returncode = returncode

            async def communicate(self):
                return stdout, stderr

        async def fake_create(*args, **kwargs):
            if file_not_found:
                raise FileNotFoundError("dig not found")
            if generic_exc is not None:
                raise generic_exc
            return FakeProc()

        async def fake_wait_for(coro, timeout=None):
            if timeout_flag:
                raise asyncio.TimeoutError()
            return await coro

        monkeypatch.setattr(asyncio, "create_subprocess_exec", fake_create)
        monkeypatch.setattr(asyncio, "wait_for", fake_wait_for)

    def test_returns_records_on_success(self, monkeypatch):
        self._patch_subprocess(monkeypatch, returncode=0, stdout=b"1.2.3.4\n5.6.7.8\n")
        records, err = asyncio.run(dns.dig_record("example.com", "1.1.1.1"))
        assert records == ["1.2.3.4", "5.6.7.8"]
        assert err is None

    def test_filters_comment_lines(self, monkeypatch):
        self._patch_subprocess(monkeypatch, returncode=0, stdout=b";comment\n1.2.3.4\n; another\n")
        records, err = asyncio.run(dns.dig_record("x.com", "8.8.8.8"))
        assert records == ["1.2.3.4"]
        assert err is None

    def test_filters_blank_lines(self, monkeypatch):
        self._patch_subprocess(monkeypatch, returncode=0, stdout=b"1.2.3.4\n\n  \n5.6.7.8\n")
        records, err = asyncio.run(dns.dig_record("x.com", "8.8.8.8"))
        assert records == ["1.2.3.4", "5.6.7.8"]

    def test_timeout(self, monkeypatch):
        self._patch_subprocess(monkeypatch, timeout_flag=True)
        records, err = asyncio.run(dns.dig_record("x.com", "8.8.8.8"))
        assert records == []
        assert err == "timeout"

    def test_file_not_found(self, monkeypatch):
        self._patch_subprocess(monkeypatch, file_not_found=True)
        records, err = asyncio.run(dns.dig_record("x.com", "8.8.8.8"))
        assert records == []
        assert err == "dig binary not installed"

    def test_generic_exception(self, monkeypatch):
        self._patch_subprocess(monkeypatch, generic_exc=PermissionError("denied"))
        records, err = asyncio.run(dns.dig_record("x.com", "8.8.8.8"))
        assert records == []
        assert err == "PermissionError"

    def test_nonzero_exit(self, monkeypatch):
        self._patch_subprocess(monkeypatch, returncode=2, stdout=b"", stderr=b"resolver error\n")
        records, err = asyncio.run(dns.dig_record("x.com", "1.1.1.1"))
        assert records == []
        assert err == "resolver error"

    def test_nonzero_exit_blank_stderr(self, monkeypatch):
        self._patch_subprocess(monkeypatch, returncode=5, stdout=b"", stderr=b"")
        records, err = asyncio.run(dns.dig_record("x.com", "1.1.1.1"))
        assert records == []
        assert err == "exit 5"


class TestDnsCheckJob:
    def _make_context(self):
        from unittest.mock import AsyncMock, MagicMock
        ctx = MagicMock()
        ctx.bot = MagicMock()
        ctx.bot.send_message = AsyncMock()
        return ctx

    def test_skips_when_no_allowed_users(self, store, monkeypatch):
        monkeypatch.setattr(dns, "ALLOWED_USERS", [])
        monkeypatch.setattr("infra.auth.ALLOWED_USERS", [])
        ctx = self._make_context()
        asyncio.run(dns.dns_check_job(ctx))
        ctx.bot.send_message.assert_not_awaited()

    def test_skips_when_no_domains(self, store, monkeypatch):
        monkeypatch.setattr(dns, "ALLOWED_USERS", [42])
        monkeypatch.setattr("infra.auth.ALLOWED_USERS", [42])
        monkeypatch.setattr(dns, "get_ssl_domains", lambda: [])
        ctx = self._make_context()
        asyncio.run(dns.dns_check_job(ctx))
        ctx.bot.send_message.assert_not_awaited()

    def test_sends_when_warnings(self, store, monkeypatch):
        monkeypatch.setattr(dns, "ALLOWED_USERS", [42])
        monkeypatch.setattr("infra.auth.ALLOWED_USERS", [42])
        monkeypatch.setattr(dns, "get_ssl_domains", lambda: [])
        config_store.config_set("dns_domains", ["bad.com"])

        async def fake_run():
            return "🔴 Divergent records detected"

        monkeypatch.setattr(dns, "run_dns_check", fake_run)
        ctx = self._make_context()
        asyncio.run(dns.dns_check_job(ctx))
        ctx.bot.send_message.assert_awaited_once()

    def test_silent_when_clean(self, store, monkeypatch):
        monkeypatch.setattr(dns, "ALLOWED_USERS", [42])
        monkeypatch.setattr("infra.auth.ALLOWED_USERS", [42])
        monkeypatch.setattr(dns, "get_ssl_domains", lambda: [])
        config_store.config_set("dns_domains", ["good.com"])

        async def fake_run():
            return "✅ All consistent"

        monkeypatch.setattr(dns, "run_dns_check", fake_run)
        ctx = self._make_context()
        asyncio.run(dns.dns_check_job(ctx))
        ctx.bot.send_message.assert_not_awaited()

    def test_swallows_exceptions(self, store, monkeypatch, caplog):
        import logging
        monkeypatch.setattr(dns, "ALLOWED_USERS", [42])
        monkeypatch.setattr("infra.auth.ALLOWED_USERS", [42])
        monkeypatch.setattr(dns, "get_ssl_domains", lambda: [])
        config_store.config_set("dns_domains", ["x.com"])

        async def fake_run():
            raise RuntimeError("dig down")

        monkeypatch.setattr(dns, "run_dns_check", fake_run)
        ctx = self._make_context()
        with caplog.at_level(logging.ERROR):
            asyncio.run(dns.dns_check_job(ctx))
        assert "DNS check job failed" in caplog.text


class TestCmdDns:
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
        monkeypatch.setattr(dns, "ALLOWED_USERS", [42])
        monkeypatch.setattr("infra.auth.ALLOWED_USERS", [42])

        async def fake_run():
            return "✅ Check complete"

        monkeypatch.setattr(dns, "run_dns_check", fake_run)
        update = self._make_update()
        asyncio.run(dns.cmd_dns(update, self._make_context([])))
        assert update.message.reply_text.await_count == 2

    def test_check_failure_reports_error(self, store, monkeypatch):
        monkeypatch.setattr(dns, "ALLOWED_USERS", [42])
        monkeypatch.setattr("infra.auth.ALLOWED_USERS", [42])

        async def fake_run():
            raise RuntimeError("kaboom")

        monkeypatch.setattr(dns, "run_dns_check", fake_run)
        update = self._make_update()
        asyncio.run(dns.cmd_dns(update, self._make_context([])))
        last_call = update.message.reply_text.await_args_list[-1]
        assert "DNS check failed" in last_call.args[0]
        assert "kaboom" in last_call.args[0]

    def test_list_empty(self, store, monkeypatch):
        monkeypatch.setattr(dns, "ALLOWED_USERS", [42])
        monkeypatch.setattr("infra.auth.ALLOWED_USERS", [42])
        monkeypatch.setattr(dns, "get_ssl_domains", lambda: [])
        update = self._make_update()
        asyncio.run(dns.cmd_dns(update, self._make_context(["list"])))
        update.message.reply_text.assert_awaited_with("📋 No DNS domains configured.")

    def test_list_shows_domains(self, store, monkeypatch):
        monkeypatch.setattr(dns, "ALLOWED_USERS", [42])
        monkeypatch.setattr("infra.auth.ALLOWED_USERS", [42])
        monkeypatch.setattr(dns, "get_ssl_domains", lambda: [])
        config_store.config_set("dns_domains", ["a.com", "b.com"])
        update = self._make_update()
        asyncio.run(dns.cmd_dns(update, self._make_context(["list"])))
        text = update.message.reply_text.await_args.args[0]
        assert "a.com" in text and "b.com" in text

    def test_add_new_domain(self, store, monkeypatch):
        monkeypatch.setattr(dns, "ALLOWED_USERS", [42])
        monkeypatch.setattr("infra.auth.ALLOWED_USERS", [42])
        monkeypatch.setattr(dns, "get_ssl_domains", lambda: [])
        update = self._make_update()
        asyncio.run(dns.cmd_dns(update, self._make_context(["add", "new.com"])))
        text = update.message.reply_text.await_args.args[0]
        assert "Added" in text
        assert "new.com" in dns.get_dns_domains()

    def test_add_duplicate(self, store, monkeypatch):
        monkeypatch.setattr(dns, "ALLOWED_USERS", [42])
        monkeypatch.setattr("infra.auth.ALLOWED_USERS", [42])
        monkeypatch.setattr(dns, "get_ssl_domains", lambda: [])
        config_store.config_set("dns_domains", ["dup.com"])
        update = self._make_update()
        asyncio.run(dns.cmd_dns(update, self._make_context(["add", "dup.com"])))
        text = update.message.reply_text.await_args.args[0]
        assert "already in watchlist" in text

    def test_del_existing(self, store, monkeypatch):
        monkeypatch.setattr(dns, "ALLOWED_USERS", [42])
        monkeypatch.setattr("infra.auth.ALLOWED_USERS", [42])
        monkeypatch.setattr(dns, "get_ssl_domains", lambda: [])
        config_store.config_set("dns_domains", ["gone.com"])
        update = self._make_update()
        asyncio.run(dns.cmd_dns(update, self._make_context(["del", "gone.com"])))
        text = update.message.reply_text.await_args.args[0]
        assert "Removed" in text

    def test_del_missing(self, store, monkeypatch):
        monkeypatch.setattr(dns, "ALLOWED_USERS", [42])
        monkeypatch.setattr("infra.auth.ALLOWED_USERS", [42])
        monkeypatch.setattr(dns, "get_ssl_domains", lambda: [])
        update = self._make_update()
        asyncio.run(dns.cmd_dns(update, self._make_context(["del", "absent.com"])))
        text = update.message.reply_text.await_args.args[0]
        assert "not in watchlist" in text

    def test_unknown_action_shows_usage(self, store, monkeypatch):
        monkeypatch.setattr(dns, "ALLOWED_USERS", [42])
        monkeypatch.setattr("infra.auth.ALLOWED_USERS", [42])
        update = self._make_update()
        asyncio.run(dns.cmd_dns(update, self._make_context(["wat"])))
        text = update.message.reply_text.await_args.args[0]
        assert "Usage" in text
