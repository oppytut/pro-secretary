from __future__ import annotations

import os

os.environ.setdefault("AGENT_SECRET", "test-secret-12345")
os.environ.setdefault("LLM_API_KEY", "test-llm-key")
os.environ.setdefault("LLM_BASE_URL", "https://example.test/v1")
os.environ.setdefault("LLM_MODEL", "test-model")
os.environ.setdefault("QDRANT_URL", "https://qdrant.test")
os.environ.setdefault("QDRANT_API_KEY", "test-qdrant-key")
os.environ.setdefault("TELEGRAM_BOT_TOKEN", "test:bot-token")
os.environ.setdefault("TELEGRAM_ALLOWED_USERS", "42")
os.environ.setdefault("GH_PAT", "ghp_test_token")

import pytest
from fastapi.testclient import TestClient

from app import main, pr_review, test_coverage


@pytest.fixture
def client():
    return TestClient(main.app)


@pytest.fixture
def auth_headers():
    return {"X-Agent-Secret": "test-secret-12345"}


class TestAuth:
    def test_health_no_auth_required(self, client):
        r = client.get("/health")
        assert r.status_code == 200

    def test_endpoint_rejects_no_secret(self, client):
        r = client.post("/api/coverage/repos", json={"repos": []})
        assert r.status_code == 401

    def test_endpoint_rejects_wrong_secret(self, client):
        r = client.post(
            "/api/coverage/repos",
            json={"repos": []},
            headers={"X-Agent-Secret": "wrong"},
        )
        assert r.status_code == 401

    def test_endpoint_accepts_bearer_format(self, client, tmp_path, monkeypatch):
        monkeypatch.setattr(test_coverage, "_WHITELIST_FILE", tmp_path / "coverage_repos.json")
        r = client.post(
            "/api/coverage/repos",
            json={"repos": []},
            headers={"Authorization": "Bearer test-secret-12345"},
        )
        assert r.status_code == 200


class TestCoverageReposEndpoints:
    def test_get_initial_empty(self, client, auth_headers, tmp_path, monkeypatch):
        monkeypatch.setattr(test_coverage, "_WHITELIST_FILE", tmp_path / "coverage_repos.json")
        r = client.get("/api/coverage/repos", headers=auth_headers)
        assert r.status_code == 200
        assert r.json() == {"repos": []}

    def test_set_then_get(self, client, auth_headers, tmp_path, monkeypatch):
        monkeypatch.setattr(test_coverage, "_WHITELIST_FILE", tmp_path / "coverage_repos.json")
        r = client.post(
            "/api/coverage/repos",
            json={"repos": ["foo/bar"]},
            headers=auth_headers,
        )
        assert r.status_code == 200
        assert r.json()["ok"] is True
        r = client.get("/api/coverage/repos", headers=auth_headers)
        assert r.json() == {"repos": ["foo/bar"]}

    def test_invalid_payload_returns_422(self, client, auth_headers):
        r = client.post(
            "/api/coverage/repos",
            json={"not_repos": "wrong"},
            headers=auth_headers,
        )
        assert r.status_code == 422


class TestCoverageScanEndpoint:
    def test_rejects_unwhitelisted_repo(self, client, auth_headers, tmp_path, monkeypatch):
        monkeypatch.setattr(test_coverage, "_WHITELIST_FILE", tmp_path / "coverage_repos.json")
        r = client.post(
            "/api/coverage/scan",
            json={"repo": "ghost/repo"},
            headers=auth_headers,
        )
        assert r.status_code == 200
        body = r.json()
        assert body["ok"] is False
        assert "not in coverage whitelist" in body["error"]

    def test_validates_min_coverage_range(self, client, auth_headers):
        r = client.post(
            "/api/coverage/scan",
            json={"repo": "foo/bar", "min_coverage": 200},
            headers=auth_headers,
        )
        assert r.status_code == 422

    def test_validates_repo_required(self, client, auth_headers):
        r = client.post("/api/coverage/scan", json={}, headers=auth_headers)
        assert r.status_code == 422


class TestReviewReposEndpoints:
    def test_get_initial_empty(self, client, auth_headers, tmp_path, monkeypatch):
        monkeypatch.setattr(pr_review, "_WHITELIST_FILE", tmp_path / "review_repos.json")
        r = client.get("/api/review/repos", headers=auth_headers)
        assert r.status_code == 200
        assert r.json() == {"repos": []}

    def test_set_then_get(self, client, auth_headers, tmp_path, monkeypatch):
        monkeypatch.setattr(pr_review, "_WHITELIST_FILE", tmp_path / "review_repos.json")
        r = client.post(
            "/api/review/repos",
            json={"repos": ["github:foo/bar"]},
            headers=auth_headers,
        )
        assert r.status_code == 200
        r = client.get("/api/review/repos", headers=auth_headers)
        assert r.json() == {"repos": ["github:foo/bar"]}


class TestReviewPrEndpoint:
    def test_validates_pr_number(self, client, auth_headers):
        r = client.post(
            "/api/review_pr",
            json={"repo": "foo/bar", "pr_number": 0},
            headers=auth_headers,
        )
        assert r.status_code == 422

    def test_validates_repo(self, client, auth_headers):
        r = client.post(
            "/api/review_pr",
            json={"repo": "", "pr_number": 1},
            headers=auth_headers,
        )
        assert r.status_code == 422

    def test_calls_review_pr_on_demand(self, client, auth_headers, monkeypatch):
        captured = {}

        async def fake_review(platform, full_name, pr_number):
            captured["platform"] = platform
            captured["full_name"] = full_name
            captured["pr_number"] = pr_number
            return {"reviewed": True, "verdict": "APPROVE"}

        monkeypatch.setattr(pr_review, "review_pr_on_demand", fake_review)
        r = client.post(
            "/api/review_pr",
            json={"repo": "foo/bar", "pr_number": 42},
            headers=auth_headers,
        )
        assert r.status_code == 200
        assert r.json()["verdict"] == "APPROVE"
        assert captured == {"platform": "github", "full_name": "foo/bar", "pr_number": 42}

    def test_parses_platform_prefix(self, client, auth_headers, monkeypatch):
        captured = {}

        async def fake_review(platform, full_name, pr_number):
            captured["platform"] = platform
            captured["full_name"] = full_name
            return {"reviewed": True}

        monkeypatch.setattr(pr_review, "review_pr_on_demand", fake_review)
        r = client.post(
            "/api/review_pr",
            json={"repo": "gitlab:owner/proj", "pr_number": 1},
            headers=auth_headers,
        )
        assert r.status_code == 200
        assert captured["platform"] == "gitlab"
        assert captured["full_name"] == "owner/proj"


class TestGitHubWebhook:
    def test_rejects_non_pull_request_event(self, client):
        r = client.post(
            "/api/webhook/github",
            json={"action": "opened"},
            headers={
                "X-GitHub-Event": "push",
                "X-Hub-Signature-256": "sha256=fake",
            },
        )
        assert r.status_code in (200, 401)

    def test_rejects_invalid_signature(self, client, monkeypatch):
        from app import config

        monkeypatch.setattr(config, "GH_WEBHOOK_SECRET", "real-secret")
        r = client.post(
            "/api/webhook/github",
            json={"action": "opened"},
            headers={
                "X-GitHub-Event": "pull_request",
                "X-Hub-Signature-256": "sha256=wrong",
            },
        )
        assert r.status_code == 401


class TestGitLabWebhook:
    def test_rejects_non_mr_event(self, client, monkeypatch):
        from app import config

        monkeypatch.setattr(config, "GITLAB_WEBHOOK_SECRET", "real-secret")
        r = client.post(
            "/api/webhook/gitlab",
            json={},
            headers={
                "X-Gitlab-Event": "Push Hook",
                "X-Gitlab-Token": "real-secret",
            },
        )
        assert r.status_code == 200
        assert r.json().get("skipped") is True

    def test_rejects_invalid_token(self, client, monkeypatch):
        from app import config

        monkeypatch.setattr(config, "GITLAB_WEBHOOK_SECRET", "real-secret")
        r = client.post(
            "/api/webhook/gitlab",
            json={},
            headers={
                "X-Gitlab-Event": "Merge Request Hook",
                "X-Gitlab-Token": "wrong",
            },
        )
        assert r.status_code == 401


class TestHealthEndpoint:
    def test_returns_status_ok(self, client):
        r = client.get("/health")
        assert r.status_code == 200
        body = r.json()
        assert body.get("status") == "ok" or body.get("ok") is True or "version" in body
