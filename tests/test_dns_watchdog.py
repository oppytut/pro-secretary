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
