from __future__ import annotations

import asyncio


from watchdogs import capacity


def _disk_metric(name: str, predicted_avail_bytes: float):
    return {
        "metric": {"instance_name": name},
        "value": [123, str(predicted_avail_bytes)],
    }


class TestRunCapacityCheck:
    def test_no_data_returns_warning(self, monkeypatch):
        async def fake_prom(query):
            return None

        monkeypatch.setattr(capacity, "prom_query", fake_prom)
        report = asyncio.run(capacity.run_capacity_check())
        assert "No Prometheus data available" in report

    def test_disk_predicted_full_renders_red_warning(self, monkeypatch):
        async def fake_prom(query):
            if "predict_linear" in query and "filesystem" in query:
                return [_disk_metric("vps1", -100 * 1024**3)]
            if "node_filesystem_avail_bytes" in query and "instance_name" in query:
                return [{"metric": {}, "value": [0, str(2 * 1024**3)]}]
            if "rate(" in query and "filesystem" in query:
                return [{"metric": {}, "value": [0, "-1.0"]}]
            return None

        monkeypatch.setattr(capacity, "prom_query", fake_prom)
        report = asyncio.run(capacity.run_capacity_check())
        assert "🔴" in report
        assert "vps1" in report
        assert "disk exhaustion" in report

    def test_disk_healthy_renders_ok_line(self, monkeypatch):
        async def fake_prom(query):
            if "predict_linear" in query and "filesystem" in query:
                return [_disk_metric("vps1", 50 * 1024**3)]
            return None

        monkeypatch.setattr(capacity, "prom_query", fake_prom)
        report = asyncio.run(capacity.run_capacity_check())
        assert "✅" in report
        assert "vps1" in report
        assert "disk OK" in report

    def test_ram_predicted_full_renders_warning(self, monkeypatch):
        async def fake_prom(query):
            if "predict_linear" in query and "MemAvailable" in query:
                return [_disk_metric("vps1", -1 * 1024**3)]
            if "MemAvailable_bytes{instance_name" in query:
                return [{"metric": {}, "value": [0, str(512 * 1024**2)]}]
            if "MemTotal_bytes" in query:
                return [{"metric": {}, "value": [0, str(8 * 1024**3)]}]
            if "rate(" in query and "MemAvailable" in query:
                return [{"metric": {}, "value": [0, "-100"]}]
            return None

        monkeypatch.setattr(capacity, "prom_query", fake_prom)
        report = asyncio.run(capacity.run_capacity_check())
        assert "⚠️" in report
        assert "RAM exhaustion" in report

    def test_current_usage_summary_rendered(self, monkeypatch):
        async def fake_prom(query):
            if "predict_linear" in query and "filesystem" in query:
                return [_disk_metric("vps1", 50 * 1024**3)]
            if "(1 - node_filesystem_avail_bytes" in query:
                return [{"metric": {"instance_name": "vps1"}, "value": [0, "45.5"]}]
            if "(1 - node_memory_MemAvailable_bytes" in query:
                return [{"metric": {"instance_name": "vps1"}, "value": [0, "62.3"]}]
            return None

        monkeypatch.setattr(capacity, "prom_query", fake_prom)
        report = asyncio.run(capacity.run_capacity_check())
        assert "Current Usage" in report
        assert "45.5%" in report
        assert "62.3%" in report

    def test_forecast_window_in_footer(self, monkeypatch):
        async def fake_prom(query):
            return None

        monkeypatch.setattr(capacity, "prom_query", fake_prom)
        monkeypatch.setattr(capacity, "CAPACITY_WARN_DAYS", 7)
        report = asyncio.run(capacity.run_capacity_check())
        assert "Forecast window: 7 days" in report


from unittest.mock import AsyncMock, MagicMock


def _ram_metric(name: str, predicted_avail_bytes: float):
    return {
        "metric": {"instance_name": name},
        "value": [123, str(predicted_avail_bytes)],
    }


class TestRunCapacityCheckMore:
    def test_ram_predicted_full_renders_warning(self, monkeypatch):
        async def fake_prom(query):
            if "predict_linear" in query and "MemAvailable" in query:
                return [_ram_metric("vps1", -100 * 1024**3)]
            if "node_memory_MemAvailable_bytes{instance_name=" in query:
                return [{"metric": {}, "value": [0, str(2 * 1024**3)]}]
            if "node_memory_MemTotal_bytes" in query:
                return [{"metric": {}, "value": [0, str(8 * 1024**3)]}]
            if "rate(" in query and "MemAvailable" in query:
                return [{"metric": {}, "value": [0, "-1.0"]}]
            return None

        monkeypatch.setattr(capacity, "prom_query", fake_prom)
        report = asyncio.run(capacity.run_capacity_check())
        assert "⚠️" in report
        assert "vps1" in report
        assert "RAM exhaustion" in report

    def test_ram_healthy(self, monkeypatch):
        async def fake_prom(query):
            if "predict_linear" in query and "MemAvailable" in query:
                return [_ram_metric("vps1", 4 * 1024**3)]
            return None

        monkeypatch.setattr(capacity, "prom_query", fake_prom)
        report = asyncio.run(capacity.run_capacity_check())
        assert "RAM OK" in report

    def test_disk_warning_zero_rate(self, monkeypatch):
        async def fake_prom(query):
            if "predict_linear" in query and "filesystem" in query:
                return [_disk_metric("vps1", -1 * 1024**3)]
            if "node_filesystem_avail_bytes" in query and "instance_name" in query:
                return [{"metric": {}, "value": [0, str(2 * 1024**3)]}]
            if "rate(" in query and "filesystem" in query:
                return [{"metric": {}, "value": [0, "0.0"]}]
            return None

        monkeypatch.setattr(capacity, "prom_query", fake_prom)
        report = asyncio.run(capacity.run_capacity_check())
        assert "?" in report
        assert "vps1" in report


class TestCapacityJob:
    def _ctx(self):
        ctx = MagicMock()
        ctx.bot = MagicMock()
        ctx.bot.send_message = AsyncMock()
        return ctx

    def test_no_users(self, monkeypatch):
        monkeypatch.setattr(capacity, "ALLOWED_USERS", [])
        ctx = self._ctx()
        asyncio.run(capacity.capacity_check_job(ctx))
        ctx.bot.send_message.assert_not_awaited()

    def test_warning_sends(self, monkeypatch):
        monkeypatch.setattr(capacity, "ALLOWED_USERS", [42])

        async def fake_run():
            return "🔴 disk full"

        monkeypatch.setattr(capacity, "run_capacity_check", fake_run)
        ctx = self._ctx()
        asyncio.run(capacity.capacity_check_job(ctx))
        ctx.bot.send_message.assert_awaited_once()

    def test_clean_silent(self, monkeypatch):
        monkeypatch.setattr(capacity, "ALLOWED_USERS", [42])

        async def fake_run():
            return "✅ all good"

        monkeypatch.setattr(capacity, "run_capacity_check", fake_run)
        ctx = self._ctx()
        asyncio.run(capacity.capacity_check_job(ctx))
        ctx.bot.send_message.assert_not_awaited()

    def test_swallows_exceptions(self, monkeypatch, caplog):
        import logging
        monkeypatch.setattr(capacity, "ALLOWED_USERS", [42])

        async def fake_run():
            raise RuntimeError("boom")

        monkeypatch.setattr(capacity, "run_capacity_check", fake_run)
        ctx = self._ctx()
        with caplog.at_level(logging.ERROR):
            asyncio.run(capacity.capacity_check_job(ctx))
        assert "Capacity check job failed" in caplog.text


class TestCmdCapacity:
    def _update(self):
        u = MagicMock()
        u.effective_user = MagicMock()
        u.effective_user.id = 42
        u.message = MagicMock()
        u.message.reply_text = AsyncMock()
        return u

    def test_runs_and_replies(self, monkeypatch):
        monkeypatch.setattr(capacity, "ALLOWED_USERS", [42])
        monkeypatch.setattr("infra.auth.ALLOWED_USERS", [42])

        async def fake_run():
            return "✅ clean"

        monkeypatch.setattr(capacity, "run_capacity_check", fake_run)
        u = self._update()
        ctx = MagicMock()
        asyncio.run(capacity.cmd_capacity(u, ctx))
        assert u.message.reply_text.await_count == 2

    def test_failure(self, monkeypatch):
        monkeypatch.setattr(capacity, "ALLOWED_USERS", [42])
        monkeypatch.setattr("infra.auth.ALLOWED_USERS", [42])

        async def fake_run():
            raise RuntimeError("boom")

        monkeypatch.setattr(capacity, "run_capacity_check", fake_run)
        u = self._update()
        ctx = MagicMock()
        asyncio.run(capacity.cmd_capacity(u, ctx))
        last = u.message.reply_text.await_args_list[-1].args[0]
        assert "Capacity check failed" in last
