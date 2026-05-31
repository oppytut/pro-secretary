from __future__ import annotations

import asyncio
import hashlib
import hmac

import httpx
import pytest

from app import pr_review


def _run(coro):
    return asyncio.run(coro)


@pytest.fixture
def whitelist_file(tmp_path, monkeypatch):
    path = tmp_path / "review_repos.json"
    monkeypatch.setattr(pr_review, "_WHITELIST_FILE", path)
    return path


class TestWhitelist:
    def test_get_empty_when_no_file(self, whitelist_file):
        assert pr_review.get_whitelist() == []

    def test_set_creates_parent_dir(self, tmp_path, monkeypatch):
        nested = tmp_path / "deep" / "review_repos.json"
        monkeypatch.setattr(pr_review, "_WHITELIST_FILE", nested)
        pr_review.set_whitelist(["github:foo/bar"])
        assert nested.exists()

    def test_roundtrip(self, whitelist_file):
        pr_review.set_whitelist(["github:foo/bar", "gitlab:baz/qux"])
        assert pr_review.get_whitelist() == ["github:foo/bar", "gitlab:baz/qux"]

    def test_corrupt_json_returns_empty(self, whitelist_file):
        whitelist_file.write_text("not-json{{{")
        assert pr_review.get_whitelist() == []


class TestIsRepoAllowed:
    def test_empty_whitelist_allows_all(self, whitelist_file):
        assert pr_review.is_repo_allowed("github", "foo/bar") is True

    def test_match_allows(self, whitelist_file):
        pr_review.set_whitelist(["github:foo/bar"])
        assert pr_review.is_repo_allowed("github", "foo/bar") is True

    def test_no_match_denies(self, whitelist_file):
        pr_review.set_whitelist(["github:foo/bar"])
        assert pr_review.is_repo_allowed("github", "baz/qux") is False

    def test_platform_isolation(self, whitelist_file):
        pr_review.set_whitelist(["github:foo/bar"])
        assert pr_review.is_repo_allowed("gitlab", "foo/bar") is False


class TestVerifyWebhookSignature:
    def test_no_secret_passes(self, monkeypatch):
        monkeypatch.setattr(pr_review.config, "GH_WEBHOOK_SECRET", "")
        assert pr_review.verify_webhook_signature(b"body", "any") is True

    def test_no_signature_fails(self, monkeypatch):
        monkeypatch.setattr(pr_review.config, "GH_WEBHOOK_SECRET", "topsecret")
        assert pr_review.verify_webhook_signature(b"body", "") is False

    def test_correct_signature_passes(self, monkeypatch):
        monkeypatch.setattr(pr_review.config, "GH_WEBHOOK_SECRET", "topsecret")
        body = b'{"action":"opened"}'
        sig = "sha256=" + hmac.new(b"topsecret", body, hashlib.sha256).hexdigest()
        assert pr_review.verify_webhook_signature(body, sig) is True

    def test_wrong_signature_fails(self, monkeypatch):
        monkeypatch.setattr(pr_review.config, "GH_WEBHOOK_SECRET", "topsecret")
        assert pr_review.verify_webhook_signature(b"body", "sha256=deadbeef") is False

    def test_tampered_body_fails(self, monkeypatch):
        monkeypatch.setattr(pr_review.config, "GH_WEBHOOK_SECRET", "topsecret")
        body = b"original"
        sig = "sha256=" + hmac.new(b"topsecret", body, hashlib.sha256).hexdigest()
        assert pr_review.verify_webhook_signature(b"tampered", sig) is False


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
        monkeypatch.setattr(pr_review.httpx, "AsyncClient", lambda **_: client)
        return holder

    return install


class TestFetchPrDiff:
    def test_returns_diff_on_200(self, patch_client, monkeypatch):
        monkeypatch.setattr(pr_review.config, "GH_PAT", "token")
        patch_client(get_responses=[FakeResp(200, text="diff text")])
        result = _run(pr_review.fetch_pr_diff("owner", "repo", 7))
        assert result == "diff text"

    def test_returns_none_on_404(self, patch_client, monkeypatch):
        monkeypatch.setattr(pr_review.config, "GH_PAT", "token")
        patch_client(get_responses=[FakeResp(404)])
        assert _run(pr_review.fetch_pr_diff("o", "r", 1)) is None

    def test_403_not_retried(self, patch_client, monkeypatch):
        monkeypatch.setattr(pr_review.config, "GH_PAT", "token")
        holder = patch_client(get_responses=[FakeResp(403)])
        assert _run(pr_review.fetch_pr_diff("o", "r", 1)) is None
        assert len(holder["client"].get_calls) == 1

    def test_500_retried_then_succeeds(self, patch_client, monkeypatch):
        monkeypatch.setattr(pr_review.config, "GH_PAT", "token")
        monkeypatch.setattr(pr_review.asyncio, "sleep", lambda _: asyncio.sleep(0)) if hasattr(pr_review, "asyncio") else None
        holder = patch_client(get_responses=[FakeResp(500), FakeResp(200, text="diff")])
        result = _run(pr_review.fetch_pr_diff("o", "r", 1))
        assert result == "diff"
        assert len(holder["client"].get_calls) == 2

    def test_url_format(self, patch_client, monkeypatch):
        monkeypatch.setattr(pr_review.config, "GH_PAT", "token")
        holder = patch_client(get_responses=[FakeResp(200, text="x")])
        _run(pr_review.fetch_pr_diff("foo", "bar", 42))
        assert "/repos/foo/bar/pulls/42" in holder["client"].get_calls[0]["url"]


class TestAnalyzeDiff:
    def test_extracts_approve_verdict(self, monkeypatch):
        async def fake_chat(messages, temperature, max_tokens):
            return "FINDINGS:\n- nothing.\nVERDICT: APPROVE\nSUMMARY: clean change"
        monkeypatch.setattr(pr_review.llm, "chat_completion", fake_chat)
        result = _run(pr_review.analyze_diff("diff", "title"))
        assert result["verdict"] == "APPROVE"
        assert result["summary"] == "clean change"

    def test_extracts_request_changes_verdict(self, monkeypatch):
        async def fake_chat(messages, temperature, max_tokens):
            return "FINDINGS:\n- bug\nVERDICT: REQUEST_CHANGES\nSUMMARY: SQL injection"
        monkeypatch.setattr(pr_review.llm, "chat_completion", fake_chat)
        result = _run(pr_review.analyze_diff("diff", "title"))
        assert result["verdict"] == "REQUEST_CHANGES"

    def test_default_verdict_comment(self, monkeypatch):
        async def fake_chat(messages, temperature, max_tokens):
            return "FINDINGS:\n- nit\nSUMMARY: minor"
        monkeypatch.setattr(pr_review.llm, "chat_completion", fake_chat)
        result = _run(pr_review.analyze_diff("diff", "title"))
        assert result["verdict"] == "COMMENT"

    def test_unknown_verdict_falls_back_to_comment(self, monkeypatch):
        async def fake_chat(messages, temperature, max_tokens):
            return "VERDICT: WAFFLE\nSUMMARY: idk"
        monkeypatch.setattr(pr_review.llm, "chat_completion", fake_chat)
        result = _run(pr_review.analyze_diff("diff", "title"))
        assert result["verdict"] == "COMMENT"

    def test_truncation_threshold(self, monkeypatch):
        captured = {}

        async def fake_chat(messages, temperature, max_tokens):
            captured["user_content"] = messages[1]["content"]
            return "VERDICT: APPROVE\nSUMMARY: ok"

        monkeypatch.setattr(pr_review.llm, "chat_completion", fake_chat)
        big_diff = "x" * (pr_review._MAX_DIFF_CHARS + 5000)
        result = _run(pr_review.analyze_diff(big_diff, "title"))
        assert "truncated" in result["body"]
        assert str(len(big_diff)) in result["body"]
        assert "truncated" in captured["user_content"]

    def test_no_truncation_below_threshold(self, monkeypatch):
        async def fake_chat(messages, temperature, max_tokens):
            return "VERDICT: APPROVE\nSUMMARY: ok"
        monkeypatch.setattr(pr_review.llm, "chat_completion", fake_chat)
        result = _run(pr_review.analyze_diff("small diff", "title"))
        assert "truncated" not in result["body"]

    def test_pr_body_clipped_to_500(self, monkeypatch):
        captured = {}

        async def fake_chat(messages, temperature, max_tokens):
            captured["user_content"] = messages[1]["content"]
            return "VERDICT: APPROVE\nSUMMARY: ok"

        monkeypatch.setattr(pr_review.llm, "chat_completion", fake_chat)
        big_body = "y" * 800
        _run(pr_review.analyze_diff("diff", "title", pr_body=big_body))
        body_section = captured["user_content"].split("PR Description:")[1].split("\n")[0]
        assert len(body_section.strip()) <= 500


class TestPostReview:
    def test_201_returns_ok(self, patch_client):
        patch_client(post_responses=[FakeResp(201, json_data={"id": 99})])
        result = _run(pr_review.post_review("o", "r", 1, "abc", "body", "APPROVE"))
        assert result["ok"] is True
        assert result["data"] == {"id": 99}

    def test_422_returns_error(self, patch_client):
        patch_client(post_responses=[FakeResp(422, text="Validation failed")])
        result = _run(pr_review.post_review("o", "r", 1, "abc", "body", "APPROVE"))
        assert result["ok"] is False
        assert result["status"] == 422
        assert "Validation" in result["error"]

    def test_request_error(self, patch_client):
        patch_client(raises=httpx.ConnectError("boom"))
        result = _run(pr_review.post_review("o", "r", 1, "abc", "body", "APPROVE"))
        assert result["ok"] is False
        assert result["status"] == 0
        assert "boom" in result["error"]

    def test_payload_shape(self, patch_client):
        holder = patch_client(post_responses=[FakeResp(201, json_data={})])
        _run(pr_review.post_review("o", "r", 5, "deadbeef", "review body", "REQUEST_CHANGES"))
        sent = holder["client"].post_calls[0]["json"]
        assert sent["commit_id"] == "deadbeef"
        assert sent["body"] == "review body"
        assert sent["event"] == "REQUEST_CHANGES"


class TestHandlePrEventFilters:
    def test_skips_closed_action(self):
        result = _run(pr_review.handle_pr_event({"action": "closed"}))
        assert result["skipped"] is True

    def test_skips_labeled_action(self):
        result = _run(pr_review.handle_pr_event({"action": "labeled"}))
        assert result["skipped"] is True

    def test_skips_draft(self):
        result = _run(pr_review.handle_pr_event({
            "action": "opened",
            "pull_request": {"draft": True},
            "repository": {"full_name": "o/r"},
        }))
        assert result["skipped"] is True
        assert "draft" in result["reason"]
