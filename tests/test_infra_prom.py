from __future__ import annotations

import asyncio

import httpx
import pytest

from infra import prom


class TestPromQuery:
    def test_returns_results_on_200(self, monkeypatch):
        class FakeResponse:
            status_code = 200

            def json(self):
                return {"data": {"result": [{"metric": {}, "value": [123, "1"]}]}}

        class FakeClient:
            def __init__(self, *args, **kwargs):
                pass

            async def __aenter__(self):
                return self

            async def __aexit__(self, *args):
                return None

            async def get(self, url, params):
                return FakeResponse()

        monkeypatch.setattr(httpx, "AsyncClient", FakeClient)
        result = asyncio.run(prom.prom_query('up{job="node"}'))
        assert result == [{"metric": {}, "value": [123, "1"]}]

    def test_returns_none_on_non_200(self, monkeypatch):
        class FakeResponse:
            status_code = 500

            def json(self):
                return {}

        class FakeClient:
            def __init__(self, *args, **kwargs):
                pass

            async def __aenter__(self):
                return self

            async def __aexit__(self, *args):
                return None

            async def get(self, url, params):
                return FakeResponse()

        monkeypatch.setattr(httpx, "AsyncClient", FakeClient)
        assert asyncio.run(prom.prom_query("query")) is None

    def test_returns_none_on_request_error(self, monkeypatch):
        class FakeClient:
            def __init__(self, *args, **kwargs):
                pass

            async def __aenter__(self):
                return self

            async def __aexit__(self, *args):
                return None

            async def get(self, url, params):
                raise httpx.RequestError("connection refused")

        monkeypatch.setattr(httpx, "AsyncClient", FakeClient)
        assert asyncio.run(prom.prom_query("query")) is None

    def test_returns_empty_list_when_data_missing(self, monkeypatch):
        class FakeResponse:
            status_code = 200

            def json(self):
                return {}

        class FakeClient:
            def __init__(self, *args, **kwargs):
                pass

            async def __aenter__(self):
                return self

            async def __aexit__(self, *args):
                return None

            async def get(self, url, params):
                return FakeResponse()

        monkeypatch.setattr(httpx, "AsyncClient", FakeClient)
        assert asyncio.run(prom.prom_query("query")) == []
