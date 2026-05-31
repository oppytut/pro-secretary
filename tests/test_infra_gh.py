from __future__ import annotations

import asyncio
import importlib

import httpx

from infra import gh as gh_module


def _reload_gh(monkeypatch, pat: str = ""):
    monkeypatch.setenv("GH_PAT", pat)
    return importlib.reload(gh_module)


class TestGhApi:
    def test_returns_none_when_no_pat(self, monkeypatch):
        gh = _reload_gh(monkeypatch, pat="")
        result = asyncio.run(gh.gh_api("/repos/owner/repo/pulls"))
        assert result is None

    def test_returns_data_on_200(self, monkeypatch):
        gh = _reload_gh(monkeypatch, pat="ghp_test")

        class FakeResponse:
            status_code = 200

            def json(self):
                return [{"number": 1, "title": "test"}]

        class FakeClient:
            def __init__(self, *args, **kwargs):
                pass

            async def __aenter__(self):
                return self

            async def __aexit__(self, *args):
                return None

            async def get(self, url, headers):
                return FakeResponse()

        monkeypatch.setattr(httpx, "AsyncClient", FakeClient)
        result = asyncio.run(gh.gh_api("/repos/owner/repo/pulls"))
        assert result == [{"number": 1, "title": "test"}]

    def test_returns_none_on_non_200(self, monkeypatch):
        gh = _reload_gh(monkeypatch, pat="ghp_test")

        class FakeResponse:
            status_code = 404

            def json(self):
                return {}

        class FakeClient:
            def __init__(self, *args, **kwargs):
                pass

            async def __aenter__(self):
                return self

            async def __aexit__(self, *args):
                return None

            async def get(self, url, headers):
                return FakeResponse()

        monkeypatch.setattr(httpx, "AsyncClient", FakeClient)
        assert asyncio.run(gh.gh_api("/missing")) is None

    def test_returns_none_on_request_error(self, monkeypatch):
        gh = _reload_gh(monkeypatch, pat="ghp_test")

        class FakeClient:
            def __init__(self, *args, **kwargs):
                pass

            async def __aenter__(self):
                return self

            async def __aexit__(self, *args):
                return None

            async def get(self, url, headers):
                raise httpx.RequestError("DNS failure")

        monkeypatch.setattr(httpx, "AsyncClient", FakeClient)
        assert asyncio.run(gh.gh_api("/x")) is None

    def test_uses_correct_headers(self, monkeypatch):
        gh = _reload_gh(monkeypatch, pat="ghp_xyz")
        captured = {}

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

            async def get(self, url, headers):
                captured["url"] = url
                captured["headers"] = headers
                return FakeResponse()

        monkeypatch.setattr(httpx, "AsyncClient", FakeClient)
        asyncio.run(gh.gh_api("/repos/foo"))
        assert captured["url"] == "https://api.github.com/repos/foo"
        assert captured["headers"]["Authorization"] == "Bearer ghp_xyz"
        assert captured["headers"]["Accept"] == "application/vnd.github+json"
        assert captured["headers"]["X-GitHub-Api-Version"] == "2022-11-28"
