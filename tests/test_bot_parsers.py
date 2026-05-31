"""Tests for pure parser/helper functions in telegram-bot/bot.py.

Scope: side-effect-free helpers that don't require network, SSH, or Docker.
Importing bot.py is safe (no side effects beyond reading env vars at module level).
"""
from __future__ import annotations

import bot
from watchdogs import hygiene


class TestDockerSizeToGb:
    def test_megabytes(self):
        assert abs(hygiene._docker_size_to_gb("100MB") - 100 / 1024) < 0.001

    def test_gigabytes(self):
        assert hygiene._docker_size_to_gb("5GB") == 5.0
        assert hygiene._docker_size_to_gb("1.5GB") == 1.5

    def test_kilobytes(self):
        assert abs(hygiene._docker_size_to_gb("512KB") - 512 / (1024 * 1024)) < 1e-6

    def test_terabytes(self):
        assert hygiene._docker_size_to_gb("2TB") == 2048.0

    def test_zero_bytes(self):
        assert hygiene._docker_size_to_gb("0B") == 0.0

    def test_empty_string(self):
        assert hygiene._docker_size_to_gb("") == 0.0

    def test_lowercase_handled(self):
        assert hygiene._docker_size_to_gb("5gb") == 5.0

    def test_invalid_returns_zero(self):
        assert hygiene._docker_size_to_gb("not-a-size") == 0.0


class TestParseDockerDf:
    def test_full_sample(self):
        sample = (
            "TYPE\tTOTAL\tACTIVE\tSIZE\tRECLAIMABLE\n"
            "Images\t12\t8\t3.5GB\t1.2GB (34%)\n"
            "Containers\t8\t8\t150MB\t0B (0%)\n"
            "Local Volumes\t5\t3\t800MB\t300MB (37%)\n"
            "Build Cache\t40\t0\t6GB\t6GB (100%)"
        )
        parsed = hygiene.parse_docker_df(sample)
        assert set(parsed.keys()) == {"Images", "Containers", "Local Volumes", "Build Cache"}
        assert parsed["Images"]["total"] == 12
        assert parsed["Images"]["size_gb"] == 3.5
        assert abs(parsed["Build Cache"]["reclaimable_gb"] - 6.0) < 0.01

    def test_empty_input(self):
        assert hygiene.parse_docker_df("") == {}

    def test_skips_header_only(self):
        assert hygiene.parse_docker_df("TYPE\tTOTAL\tACTIVE\tSIZE\tRECLAIMABLE") == {}

    def test_malformed_line_skipped(self):
        sample = "Images\t12\t8\t3.5GB\t1.2GB"
        parsed = hygiene.parse_docker_df(sample)
        assert "Images" in parsed


class TestFormatHygieneSection:
    def test_aggregates_reclaimable(self):
        parsed = {
            "Images": {"total": 12, "size_gb": 3.5, "reclaimable_gb": 1.2},
            "Build Cache": {"total": 40, "size_gb": 6.0, "reclaimable_gb": 6.0},
        }
        lines, total = hygiene._format_hygiene_section("test", parsed)
        assert abs(total - 7.2) < 0.01
        assert any("Images" in line for line in lines)
        assert any("Build Cache" in line for line in lines)

    def test_empty_input(self):
        lines, total = hygiene._format_hygiene_section("test", {})
        assert lines == []
        assert total == 0.0


class TestParseListeningPorts:
    def test_public_vs_loopback_classification(self):
        sample = (
            'LISTEN 0      4096   0.0.0.0:22         0.0.0.0:*    users:(("sshd",pid=1,fd=3))\n'
            'LISTEN 0      511    127.0.0.1:9090     0.0.0.0:*    users:(("prom",pid=5,fd=11))\n'
            'LISTEN 0      511    [::]:443           [::]:*       users:(("caddy",pid=99,fd=8))\n'
            'LISTEN 0      4096   *:8080             *:*'
        )
        listeners = bot._parse_listening_ports(sample)
        public = {l["port"] for l in listeners if l["public"] == "yes"}
        private = {l["port"] for l in listeners if l["public"] == "no"}
        assert "22" in public
        assert "443" in public
        assert "8080" in public
        assert "9090" in private

    def test_empty_input(self):
        assert bot._parse_listening_ports("") == []

    def test_skips_lines_without_colon(self):
        assert bot._parse_listening_ports("LISTEN 0 4096 garbage") == []

    def test_extracts_process_when_present(self):
        sample = 'LISTEN 0 4096 0.0.0.0:22 0.0.0.0:* users:(("sshd",pid=1,fd=3))'
        listeners = bot._parse_listening_ports(sample)
        assert len(listeners) == 1
        assert "sshd" in listeners[0]["process"]


class TestHumanBytes:
    def test_none(self):
        assert bot._human_bytes(None) == "-"

    def test_bytes(self):
        assert bot._human_bytes(512) == "512B"

    def test_kilobytes(self):
        assert bot._human_bytes(2048) == "2.0KB"

    def test_megabytes(self):
        assert bot._human_bytes(5 * 1024 * 1024) == "5.0MB"

    def test_gigabytes(self):
        assert bot._human_bytes(3 * 1024**3) == "3.0GB"


class TestHumanUptime:
    def test_none(self):
        assert bot._human_uptime(None) == "-"

    def test_zero(self):
        assert bot._human_uptime(0) == "-"

    def test_minutes_only(self):
        assert bot._human_uptime(120) == "2m"

    def test_hours_minutes(self):
        assert bot._human_uptime(3600 + 600) == "1h 10m"

    def test_days_hours(self):
        assert bot._human_uptime(86400 * 2 + 3600 * 5) == "2d 5h"


class TestContainerHealth:
    def test_healthy(self):
        assert bot._container_health("Up 5 minutes (healthy)") == "healthy"

    def test_unhealthy(self):
        assert bot._container_health("Up 5 minutes (unhealthy)") == "unhealthy"

    def test_up_no_health(self):
        assert bot._container_health("Up 5 minutes") == "up"

    def test_down(self):
        assert bot._container_health("Exited (0) 2 minutes ago") == "down"


class TestIsFreshRestart:
    def test_seconds_ago(self):
        assert bot._is_fresh_restart("Up 5 seconds") is True

    def test_less_than_minute(self):
        assert bot._is_fresh_restart("Up Less than a minute") is True

    def test_hours_ago_not_fresh(self):
        assert bot._is_fresh_restart("Up 2 hours") is False

    def test_days_ago_not_fresh(self):
        assert bot._is_fresh_restart("Up 3 days") is False

    def test_down_not_fresh(self):
        assert bot._is_fresh_restart("Exited (0) 5 seconds ago") is False
