from __future__ import annotations

import asyncio
import importlib

import httpx

from infra import agent as agent_module


def _reload_agent(monkeypatch, secret: str = "", url: str = "http://test:8090"):
    monkeypatch.setenv("AGENT_SECRET", secret)
    monkeypatch.setenv("AGENT_URL", url)
    return importlib.reload(agent_module)


class TestAgentHeaders:
    def test_empty_when_no_secret(self, monkeypatch):
        agent = _reload_agent(monkeypatch, secret="")
        assert agent.agent_headers() == {}

    def test_includes_secret_when_set(self, monkeypatch):
        agent = _reload_agent(monkeypatch, secret="topsecret")
        assert agent.agent_headers() == {"x-agent-secret": "topsecret"}


class TestAgentPost:
    def test_posts_to_correct_url(self, monkeypatch):
        agent = _reload_agent(monkeypatch, secret="", url="http://agent:8090")
        captured = {}

        class FakeResponse:
            status_code = 200

        class FakeClient:
            def __init__(self, *args, **kwargs):
                pass

            async def __aenter__(self):
                return self

            async def __aexit__(self, *args):
                return None

            async def post(self, url, headers, json):
                captured["url"] = url
                captured["headers"] = headers
                captured["json"] = json
                return FakeResponse()

        monkeypatch.setattr(httpx, "AsyncClient", FakeClient)
        result = asyncio.run(agent.agent_post("/api/foo", {"key": "value"}))
        assert result.status_code == 200
        assert captured["url"] == "http://agent:8090/api/foo"
        assert captured["json"] == {"key": "value"}
        assert captured["headers"] == {}

    def test_includes_secret_header_when_set(self, monkeypatch):
        agent = _reload_agent(monkeypatch, secret="abc123", url="http://agent:8090")
        captured = {}

        class FakeResponse:
            status_code = 200

        class FakeClient:
            def __init__(self, *args, **kwargs):
                pass

            async def __aenter__(self):
                return self

            async def __aexit__(self, *args):
                return None

            async def post(self, url, headers, json):
                captured["headers"] = headers
                return FakeResponse()

        monkeypatch.setattr(httpx, "AsyncClient", FakeClient)
        asyncio.run(agent.agent_post("/x", {}))
        assert captured["headers"] == {"x-agent-secret": "abc123"}

    def test_strips_trailing_slash_from_url(self, monkeypatch):
        agent = _reload_agent(monkeypatch, secret="", url="http://agent:8090/")
        captured = {}

        class FakeResponse:
            status_code = 200

        class FakeClient:
            def __init__(self, *args, **kwargs):
                pass

            async def __aenter__(self):
                return self

            async def __aexit__(self, *args):
                return None

            async def post(self, url, headers, json):
                captured["url"] = url
                return FakeResponse()

        monkeypatch.setattr(httpx, "AsyncClient", FakeClient)
        asyncio.run(agent.agent_post("/api/foo", {}))
        assert captured["url"] == "http://agent:8090/api/foo"
