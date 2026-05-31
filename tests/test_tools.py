from __future__ import annotations

import asyncio
from typing import Any

import httpx
import pytest

from app import tools


def _run(coro):
    return asyncio.run(coro)


@pytest.fixture
def stub_qdrant(monkeypatch):
    state: dict[str, Any] = {
        "search_calls": [],
        "search_returns": [],
        "upsert_calls": [],
        "upsert_id": "point-99",
        "scroll_calls": [],
        "scroll_returns": [],
        "set_payload_calls": [],
        "delete_calls": [],
        "delete_count": 0,
    }

    def fake_search(coll, query, limit=5):
        state["search_calls"].append({"coll": coll, "query": query, "limit": limit})
        return state["search_returns"]

    def fake_upsert(coll, text, payload):
        state["upsert_calls"].append({"coll": coll, "text": text, "payload": payload})
        return state["upsert_id"]

    def fake_scroll(coll, filters=None, limit=20):
        state["scroll_calls"].append({"coll": coll, "filters": filters, "limit": limit})
        return state["scroll_returns"]

    def fake_set_payload(coll, point_id, payload):
        state["set_payload_calls"].append({"coll": coll, "id": point_id, "payload": payload})

    def fake_delete(coll, ids):
        state["delete_calls"].append({"coll": coll, "ids": ids})
        return state["delete_count"]

    monkeypatch.setattr(tools.qdrant_helper, "search", fake_search)
    monkeypatch.setattr(tools.qdrant_helper, "upsert", fake_upsert)
    monkeypatch.setattr(tools.qdrant_helper, "scroll", fake_scroll)
    monkeypatch.setattr(tools.qdrant_helper, "set_payload", fake_set_payload)
    monkeypatch.setattr(tools.qdrant_helper, "delete_points", fake_delete)
    return state


class TestSearchKnowledge:
    def test_returns_qdrant_hits(self, stub_qdrant):
        stub_qdrant["search_returns"] = [{"id": "1", "score": 0.9}]
        result = tools.search_knowledge("query")
        assert result == [{"id": "1", "score": 0.9}]

    def test_uses_knowledge_collection(self, stub_qdrant):
        tools.search_knowledge("q")
        assert stub_qdrant["search_calls"][0]["coll"] == tools.config.COLL_KNOWLEDGE

    def test_limit_propagated(self, stub_qdrant):
        tools.search_knowledge("q", limit=10)
        assert stub_qdrant["search_calls"][0]["limit"] == 10

    def test_default_limit_5(self, stub_qdrant):
        tools.search_knowledge("q")
        assert stub_qdrant["search_calls"][0]["limit"] == 5


class TestSearchMemory:
    def test_uses_memory_collection(self, stub_qdrant):
        tools.search_memory("q")
        assert stub_qdrant["search_calls"][0]["coll"] == tools.config.COLL_MEMORY

    def test_returns_results(self, stub_qdrant):
        stub_qdrant["search_returns"] = [{"id": "x"}]
        assert tools.search_memory("q") == [{"id": "x"}]


class TestStoreMemory:
    def test_returns_point_id(self, stub_qdrant):
        assert tools.store_memory("text") == "point-99"

    def test_payload_has_type_conversation(self, stub_qdrant):
        tools.store_memory("body")
        payload = stub_qdrant["upsert_calls"][0]["payload"]
        assert payload["type"] == "conversation"
        assert payload["content"] == "body"

    def test_meta_merged_into_payload(self, stub_qdrant):
        tools.store_memory("body", meta={"user_id": "42", "extra": "yes"})
        payload = stub_qdrant["upsert_calls"][0]["payload"]
        assert payload["user_id"] == "42"
        assert payload["extra"] == "yes"
        assert payload["type"] == "conversation"

    def test_uses_memory_collection(self, stub_qdrant):
        tools.store_memory("body")
        assert stub_qdrant["upsert_calls"][0]["coll"] == tools.config.COLL_MEMORY


class TestCreateTask:
    def test_default_priority_medium(self, stub_qdrant):
        tools.create_task("write doc")
        payload = stub_qdrant["upsert_calls"][0]["payload"]
        assert payload["priority"] == "medium"
        assert payload["status"] == "pending"

    def test_user_id_stringified(self, stub_qdrant):
        tools.create_task("title", user_id=42)
        assert stub_qdrant["upsert_calls"][0]["payload"]["user_id"] == "42"

    def test_user_id_none_kept_none(self, stub_qdrant):
        tools.create_task("title")
        assert stub_qdrant["upsert_calls"][0]["payload"]["user_id"] is None

    def test_due_date_propagated(self, stub_qdrant):
        tools.create_task("title", due_date="2026-06-01")
        assert stub_qdrant["upsert_calls"][0]["payload"]["due_date"] == "2026-06-01"

    def test_uses_tasks_collection(self, stub_qdrant):
        tools.create_task("title")
        assert stub_qdrant["upsert_calls"][0]["coll"] == tools.config.COLL_TASKS

    def test_text_field_is_title(self, stub_qdrant):
        tools.create_task("ship it")
        assert stub_qdrant["upsert_calls"][0]["text"] == "ship it"

    def test_returns_point_id(self, stub_qdrant):
        assert tools.create_task("x") == "point-99"


class TestListPendingTasks:
    def test_filters_by_pending_status(self, stub_qdrant):
        tools.list_pending_tasks()
        assert stub_qdrant["scroll_calls"][0]["filters"] == {"status": "pending"}

    def test_default_limit_20(self, stub_qdrant):
        tools.list_pending_tasks()
        assert stub_qdrant["scroll_calls"][0]["limit"] == 20

    def test_returns_results(self, stub_qdrant):
        stub_qdrant["scroll_returns"] = [{"id": "t1"}]
        assert tools.list_pending_tasks() == [{"id": "t1"}]


class TestCompleteTask:
    def test_sets_status_done(self, stub_qdrant):
        tools.complete_task("task-7")
        call = stub_qdrant["set_payload_calls"][0]
        assert call["id"] == "task-7"
        assert call["payload"]["status"] == "done"

    def test_sets_completed_at_iso(self, stub_qdrant):
        tools.complete_task("task-7")
        completed_at = stub_qdrant["set_payload_calls"][0]["payload"]["completed_at"]
        assert "T" in completed_at
        assert completed_at.endswith("+00:00")

    def test_uses_tasks_collection(self, stub_qdrant):
        tools.complete_task("task-7")
        assert stub_qdrant["set_payload_calls"][0]["coll"] == tools.config.COLL_TASKS


class TestDeleteTasks:
    def test_returns_delete_count(self, stub_qdrant):
        stub_qdrant["delete_count"] = 3
        assert tools.delete_tasks(["a", "b", "c"]) == 3

    def test_passes_ids(self, stub_qdrant):
        tools.delete_tasks(["x", "y"])
        assert stub_qdrant["delete_calls"][0]["ids"] == ["x", "y"]

    def test_uses_tasks_collection(self, stub_qdrant):
        tools.delete_tasks(["x"])
        assert stub_qdrant["delete_calls"][0]["coll"] == tools.config.COLL_TASKS


class TestFindPendingTasksByTitle:
    def test_empty_query_returns_empty(self, stub_qdrant):
        assert tools.find_pending_tasks_by_title("") == []
        assert tools.find_pending_tasks_by_title("   ") == []

    def test_substring_match_case_insensitive(self, stub_qdrant):
        stub_qdrant["scroll_returns"] = [
            {"id": "1", "payload": {"title": "Deploy bot to prod"}},
            {"id": "2", "payload": {"title": "Review PR"}},
            {"id": "3", "payload": {"title": "deploy hotfix"}},
        ]
        results = tools.find_pending_tasks_by_title("DEPLOY")
        ids = {r["id"] for r in results}
        assert ids == {"1", "3"}

    def test_no_match_returns_empty(self, stub_qdrant):
        stub_qdrant["scroll_returns"] = [
            {"id": "1", "payload": {"title": "unrelated"}},
        ]
        assert tools.find_pending_tasks_by_title("xyz") == []

    def test_handles_missing_payload(self, stub_qdrant):
        stub_qdrant["scroll_returns"] = [
            {"id": "1"},
            {"id": "2", "payload": {}},
            {"id": "3", "payload": {"title": "match here"}},
        ]
        results = tools.find_pending_tasks_by_title("match")
        assert {r["id"] for r in results} == {"3"}

    def test_filters_pending_only(self, stub_qdrant):
        tools.find_pending_tasks_by_title("anything")
        assert stub_qdrant["scroll_calls"][0]["filters"] == {"status": "pending"}


class TestStoreNote:
    def test_default_source_telegram(self, stub_qdrant):
        tools.store_note("hello")
        payload = stub_qdrant["upsert_calls"][0]["payload"]
        assert payload["source"] == "telegram"
        assert payload["type"] == "note"

    def test_user_id_stringified(self, stub_qdrant):
        tools.store_note("hello", user_id=99)
        assert stub_qdrant["upsert_calls"][0]["payload"]["user_id"] == "99"

    def test_uses_knowledge_collection(self, stub_qdrant):
        tools.store_note("body")
        assert stub_qdrant["upsert_calls"][0]["coll"] == tools.config.COLL_KNOWLEDGE


class FakeResp:
    def __init__(self, status_code, json_data=None):
        self.status_code = status_code
        self._json = json_data or {}

    def json(self):
        return self._json


class FakeClient:
    def __init__(self, *, get_response=None, raises=None, json_raises=False):
        self._response = get_response
        self._raises = raises
        self._json_raises = json_raises
        self.calls = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False

    async def get(self, url, headers=None, params=None):
        self.calls.append({"url": url, "headers": headers, "params": params})
        if self._raises:
            raise self._raises
        if self._json_raises:
            class BadResp:
                status_code = 200
                def json(self):
                    raise ValueError("bad json")
            return BadResp()
        return self._response


@pytest.fixture
def patch_httpx(monkeypatch):
    holder = {}

    def install(**kwargs):
        client = FakeClient(**kwargs)
        holder["client"] = client
        monkeypatch.setattr(tools.httpx, "AsyncClient", lambda **_: client)
        return holder

    return install


class TestGetTodaySchedule:
    def test_no_api_key_returns_empty(self, monkeypatch):
        monkeypatch.setattr(tools.config, "CALCOM_API_KEY", "")
        result = _run(tools.get_today_schedule())
        assert result == []

    def test_4xx_response_returns_empty(self, monkeypatch, patch_httpx):
        monkeypatch.setattr(tools.config, "CALCOM_API_KEY", "key")
        monkeypatch.setattr(tools.config, "CALCOM_BASE_URL", "https://cal.example.com")
        monkeypatch.setattr(tools.config, "TIMEZONE", "Asia/Jakarta")
        patch_httpx(get_response=FakeResp(401))
        assert _run(tools.get_today_schedule()) == []

    def test_request_error_returns_empty(self, monkeypatch, patch_httpx):
        monkeypatch.setattr(tools.config, "CALCOM_API_KEY", "key")
        monkeypatch.setattr(tools.config, "CALCOM_BASE_URL", "https://cal.example.com")
        monkeypatch.setattr(tools.config, "TIMEZONE", "Asia/Jakarta")
        patch_httpx(raises=httpx.ConnectError("net"))
        assert _run(tools.get_today_schedule()) == []

    def test_invalid_json_returns_empty(self, monkeypatch, patch_httpx):
        monkeypatch.setattr(tools.config, "CALCOM_API_KEY", "key")
        monkeypatch.setattr(tools.config, "CALCOM_BASE_URL", "https://cal.example.com")
        monkeypatch.setattr(tools.config, "TIMEZONE", "Asia/Jakarta")
        patch_httpx(json_raises=True)
        assert _run(tools.get_today_schedule()) == []

    def test_normalizes_bookings_field(self, monkeypatch, patch_httpx):
        monkeypatch.setattr(tools.config, "CALCOM_API_KEY", "key")
        monkeypatch.setattr(tools.config, "CALCOM_BASE_URL", "https://cal.example.com")
        monkeypatch.setattr(tools.config, "TIMEZONE", "Asia/Jakarta")
        patch_httpx(get_response=FakeResp(200, {
            "bookings": [
                {"title": "1on1", "startTime": "10:00", "endTime": "10:30", "status": "ACCEPTED"},
            ]
        }))
        result = _run(tools.get_today_schedule())
        assert result == [{
            "title": "1on1", "start": "10:00", "end": "10:30", "status": "ACCEPTED",
        }]

    def test_normalizes_data_field(self, monkeypatch, patch_httpx):
        monkeypatch.setattr(tools.config, "CALCOM_API_KEY", "key")
        monkeypatch.setattr(tools.config, "CALCOM_BASE_URL", "https://cal.example.com")
        monkeypatch.setattr(tools.config, "TIMEZONE", "Asia/Jakarta")
        patch_httpx(get_response=FakeResp(200, {
            "data": [
                {"eventType": {"title": "standup"}, "start": "09:00", "end": "09:15"},
            ]
        }))
        result = _run(tools.get_today_schedule())
        assert result[0]["title"] == "standup"
        assert result[0]["start"] == "09:00"

    def test_authorization_header_set(self, monkeypatch, patch_httpx):
        monkeypatch.setattr(tools.config, "CALCOM_API_KEY", "secret-key")
        monkeypatch.setattr(tools.config, "CALCOM_BASE_URL", "https://cal.example.com")
        monkeypatch.setattr(tools.config, "TIMEZONE", "Asia/Jakarta")
        holder = patch_httpx(get_response=FakeResp(200, {"bookings": []}))
        _run(tools.get_today_schedule())
        assert holder["client"].calls[0]["headers"]["Authorization"] == "Bearer secret-key"

    def test_request_uses_bookings_endpoint(self, monkeypatch, patch_httpx):
        monkeypatch.setattr(tools.config, "CALCOM_API_KEY", "key")
        monkeypatch.setattr(tools.config, "CALCOM_BASE_URL", "https://cal.example.com")
        monkeypatch.setattr(tools.config, "TIMEZONE", "Asia/Jakarta")
        holder = patch_httpx(get_response=FakeResp(200, {"bookings": []}))
        _run(tools.get_today_schedule())
        assert "/api/v1/bookings" in holder["client"].calls[0]["url"]

    def test_query_params_include_window(self, monkeypatch, patch_httpx):
        monkeypatch.setattr(tools.config, "CALCOM_API_KEY", "key")
        monkeypatch.setattr(tools.config, "CALCOM_BASE_URL", "https://cal.example.com")
        monkeypatch.setattr(tools.config, "TIMEZONE", "Asia/Jakarta")
        holder = patch_httpx(get_response=FakeResp(200, {"bookings": []}))
        _run(tools.get_today_schedule())
        params = holder["client"].calls[0]["params"]
        assert "afterStart" in params
        assert "beforeEnd" in params

    def test_empty_bookings_returns_empty_list(self, monkeypatch, patch_httpx):
        monkeypatch.setattr(tools.config, "CALCOM_API_KEY", "key")
        monkeypatch.setattr(tools.config, "CALCOM_BASE_URL", "https://cal.example.com")
        monkeypatch.setattr(tools.config, "TIMEZONE", "Asia/Jakarta")
        patch_httpx(get_response=FakeResp(200, {"bookings": []}))
        assert _run(tools.get_today_schedule()) == []
