from __future__ import annotations

import asyncio

import httpx
import pytest

from app import gitlab_review


def _run(coro):
    return asyncio.run(coro)


class FakeResp:
    def __init__(self, status_code, text="", json_data=None):
        self.status_code = status_code
        self.text = text
        self._json = json_data

    def json(self):
        return self._json


class FakeClient:
    def __init__(self, *, get_responses=None, post_responses=None, raises=None):
        self._get = list(get_responses or [])
        self._post = list(post_responses or [])
        self._raises = raises
        self.get_calls = []
        self.post_calls = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False

    async def get(self, url, headers=None):
        self.get_calls.append({"url": url, "headers": headers})
        if self._raises:
            raise self._raises
        return self._get.pop(0)

    async def post(self, url, headers=None, json=None):
        self.post_calls.append({"url": url, "headers": headers, "json": json})
        if self._raises:
            raise self._raises
        return self._post.pop(0)


@pytest.fixture
def patch_client(monkeypatch):
    holder = {}

    def install(**factory_kwargs):
        client = FakeClient(**factory_kwargs)
        holder["client"] = client
        monkeypatch.setattr(gitlab_review.httpx, "AsyncClient", lambda **_: client)
        return holder

    return install


class TestVerifyWebhookToken:
    def test_no_secret_passes(self, monkeypatch):
        monkeypatch.setattr(gitlab_review.config, "GITLAB_WEBHOOK_SECRET", "")
        assert gitlab_review.verify_webhook_token("anything") is True

    def test_no_token_fails(self, monkeypatch):
        monkeypatch.setattr(gitlab_review.config, "GITLAB_WEBHOOK_SECRET", "secret")
        assert gitlab_review.verify_webhook_token("") is False

    def test_correct_token_passes(self, monkeypatch):
        monkeypatch.setattr(gitlab_review.config, "GITLAB_WEBHOOK_SECRET", "secret")
        assert gitlab_review.verify_webhook_token("secret") is True

    def test_wrong_token_fails(self, monkeypatch):
        monkeypatch.setattr(gitlab_review.config, "GITLAB_WEBHOOK_SECRET", "secret")
        assert gitlab_review.verify_webhook_token("nope") is False


class TestFetchMrDiff:
    def test_assembles_unified_diff(self, patch_client, monkeypatch):
        monkeypatch.setattr(gitlab_review.config, "GITLAB_PAT", "tok")
        patch_client(get_responses=[FakeResp(200, json_data={
            "changes": [
                {"old_path": "a.py", "new_path": "a.py", "diff": "@@ line @@"},
                {"old_path": "b.py", "new_path": "b.py", "diff": "@@ other @@"},
            ]
        })])
        result = _run(gitlab_review.fetch_mr_diff(42, 7))
        assert "--- a/a.py" in result
        assert "+++ b/a.py" in result
        assert "@@ line @@" in result
        assert "--- a/b.py" in result

    def test_404_not_retried(self, patch_client, monkeypatch):
        monkeypatch.setattr(gitlab_review.config, "GITLAB_PAT", "tok")
        holder = patch_client(get_responses=[FakeResp(404)])
        assert _run(gitlab_review.fetch_mr_diff(1, 1)) is None
        assert len(holder["client"].get_calls) == 1

    def test_403_not_retried(self, patch_client, monkeypatch):
        monkeypatch.setattr(gitlab_review.config, "GITLAB_PAT", "tok")
        holder = patch_client(get_responses=[FakeResp(403)])
        assert _run(gitlab_review.fetch_mr_diff(1, 1)) is None
        assert len(holder["client"].get_calls) == 1

    def test_500_retried_then_succeeds(self, patch_client, monkeypatch):
        monkeypatch.setattr(gitlab_review.config, "GITLAB_PAT", "tok")
        holder = patch_client(get_responses=[
            FakeResp(500),
            FakeResp(200, json_data={"changes": []}),
        ])
        result = _run(gitlab_review.fetch_mr_diff(1, 1))
        assert result == ""
        assert len(holder["client"].get_calls) == 2

    def test_url_format(self, patch_client, monkeypatch):
        monkeypatch.setattr(gitlab_review.config, "GITLAB_PAT", "tok")
        holder = patch_client(get_responses=[FakeResp(200, json_data={"changes": []})])
        _run(gitlab_review.fetch_mr_diff(99, 88))
        assert "/projects/99/merge_requests/88/changes" in holder["client"].get_calls[0]["url"]

    def test_uses_private_token_header(self, patch_client, monkeypatch):
        monkeypatch.setattr(gitlab_review.config, "GITLAB_PAT", "my-pat")
        holder = patch_client(get_responses=[FakeResp(200, json_data={"changes": []})])
        _run(gitlab_review.fetch_mr_diff(1, 1))
        assert holder["client"].get_calls[0]["headers"]["PRIVATE-TOKEN"] == "my-pat"


class TestPostMrComment:
    def test_201_returns_ok(self, patch_client):
        patch_client(post_responses=[FakeResp(201, json_data={"id": 7})])
        result = _run(gitlab_review.post_mr_comment(1, 2, "review body"))
        assert result["ok"] is True
        assert result["data"] == {"id": 7}

    def test_payload_shape(self, patch_client):
        holder = patch_client(post_responses=[FakeResp(201, json_data={})])
        _run(gitlab_review.post_mr_comment(99, 88, "the body"))
        sent = holder["client"].post_calls[0]
        assert sent["json"] == {"body": "the body"}
        assert "/projects/99/merge_requests/88/notes" in sent["url"]

    def test_422_returns_error(self, patch_client):
        patch_client(post_responses=[FakeResp(422, text="bad")])
        result = _run(gitlab_review.post_mr_comment(1, 2, "body"))
        assert result["ok"] is False
        assert result["status"] == 422

    def test_request_error(self, patch_client):
        patch_client(raises=httpx.ConnectError("net"))
        result = _run(gitlab_review.post_mr_comment(1, 2, "body"))
        assert result["ok"] is False
        assert result["status"] == 0


class TestHandleMrEventFilters:
    def test_skips_close_action(self):
        result = _run(gitlab_review.handle_mr_event({"object_attributes": {"action": "close"}}))
        assert result["skipped"] is True

    def test_skips_merge_action(self):
        result = _run(gitlab_review.handle_mr_event({"object_attributes": {"action": "merge"}}))
        assert result["skipped"] is True

    def test_skips_wip(self):
        result = _run(gitlab_review.handle_mr_event({
            "object_attributes": {"action": "open", "work_in_progress": True},
            "project": {"path_with_namespace": "foo/bar"},
        }))
        assert result["skipped"] is True
        assert "draft" in result["reason"]

    def test_skips_draft(self):
        result = _run(gitlab_review.handle_mr_event({
            "object_attributes": {"action": "open", "draft": True},
            "project": {"path_with_namespace": "foo/bar"},
        }))
        assert result["skipped"] is True
        assert "draft" in result["reason"]
