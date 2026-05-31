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
