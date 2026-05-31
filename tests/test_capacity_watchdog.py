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
