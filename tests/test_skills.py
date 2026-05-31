from __future__ import annotations

from typing import Any

import pytest

from app import skills


@pytest.fixture
def mocked(monkeypatch):
    state: dict[str, Any] = {
        "ensure_calls": [],
        "search_results": [],
        "upserted": [],
        "next_id": "abc-123",
    }

    def fake_ensure(name):
        state["ensure_calls"].append(name)

    def fake_search(coll, query, limit=5):
        return state["search_results"]

    def fake_upsert(coll, embed_text, payload):
        state["upserted"].append({"coll": coll, "text": embed_text, "payload": payload})
        return state["next_id"]

    monkeypatch.setattr(skills, "ensure_collection", fake_ensure)
    monkeypatch.setattr(skills, "search", fake_search)
    monkeypatch.setattr(skills, "upsert", fake_upsert)
    return state


class TestLogSkill:
    def test_returns_logged_status_when_no_match(self, mocked):
        point_id, status = skills.log_skill("deploy-bot", "build and push")
        assert status == "logged"
        assert point_id == "abc-123"

    def test_calls_ensure_collection(self, mocked):
        skills.log_skill("name", "desc")
        assert "skills" in mocked["ensure_calls"]

    def test_low_score_match_does_not_dedup(self, mocked):
        mocked["search_results"] = [{"id": "old-id", "score": 0.50}]
        point_id, status = skills.log_skill("name", "desc")
        assert status == "logged"
        assert point_id == "abc-123"

    def test_threshold_boundary_below_does_not_dedup(self, mocked):
        mocked["search_results"] = [{"id": "old-id", "score": 0.85}]
        _, status = skills.log_skill("name", "desc")
        assert status == "logged"

    def test_threshold_boundary_above_dedups(self, mocked):
        mocked["search_results"] = [{"id": "old-id", "score": 0.851}]
        point_id, status = skills.log_skill("name", "desc")
        assert status == "dedup"
        assert point_id == "old-id"

    def test_high_score_dedups(self, mocked):
        mocked["search_results"] = [{"id": "existing-9", "score": 0.95}]
        point_id, status = skills.log_skill("name", "desc")
        assert status == "dedup"
        assert point_id == "existing-9"
        assert mocked["upserted"] == []

    def test_payload_includes_steps_tags(self, mocked):
        skills.log_skill(
            "deploy",
            "ship it",
            steps=["git push", "verify"],
            tags=["ops"],
            user_id=123,
        )
        payload = mocked["upserted"][0]["payload"]
        assert payload["name"] == "deploy"
        assert payload["description"] == "ship it"
        assert payload["steps"] == ["git push", "verify"]
        assert payload["tags"] == ["ops"]
        assert payload["user_id"] == "123"

    def test_payload_user_id_empty_when_none(self, mocked):
        skills.log_skill("name", "desc")
        payload = mocked["upserted"][0]["payload"]
        assert payload["user_id"] == ""
        assert payload["steps"] == []
        assert payload["tags"] == []

    def test_payload_user_id_zero_treated_as_falsy(self, mocked):
        skills.log_skill("name", "desc", user_id=0)
        assert mocked["upserted"][0]["payload"]["user_id"] == ""

    def test_embed_text_includes_steps(self, mocked):
        skills.log_skill("deploy", "desc", steps=["a", "b"])
        text = mocked["upserted"][0]["text"]
        assert "deploy" in text
        assert "desc" in text
        assert "a b" in text

    def test_embed_text_no_steps(self, mocked):
        skills.log_skill("deploy", "desc")
        text = mocked["upserted"][0]["text"]
        assert text == "deploy | desc"

    def test_trigger_passed_to_payload(self, mocked):
        skills.log_skill("name", "desc", trigger="manual-log")
        assert mocked["upserted"][0]["payload"]["trigger"] == "manual-log"

    def test_default_trigger_empty(self, mocked):
        skills.log_skill("name", "desc")
        assert mocked["upserted"][0]["payload"]["trigger"] == ""


class TestSearchSkills:
    def test_returns_qdrant_hits(self, mocked):
        mocked["search_results"] = [
            {"id": "1", "score": 0.9, "payload": {"name": "deploy"}},
            {"id": "2", "score": 0.7, "payload": {"name": "rollback"}},
        ]
        results = skills.search_skills("deploy", limit=5)
        assert len(results) == 2
        assert results[0]["payload"]["name"] == "deploy"

    def test_ensure_collection_called(self, mocked):
        skills.search_skills("query")
        assert "skills" in mocked["ensure_calls"]

    def test_empty_results(self, mocked):
        mocked["search_results"] = []
        assert skills.search_skills("nothing") == []
