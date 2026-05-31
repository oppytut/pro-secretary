from __future__ import annotations

import asyncio
from typing import Any

import pytest

from app import meeting_notes


def _run(coro):
    return asyncio.run(coro)


class TestParseActionItem:
    def test_full_format(self):
        result = meeting_notes._parse_action_item(
            "- [urgent] Deploy fix | alice | 2026-06-01"
        )
        assert result == {
            "title": "Deploy fix",
            "priority": "urgent",
            "owner": "alice",
            "deadline": "2026-06-01",
        }

    def test_priority_lowercased(self):
        result = meeting_notes._parse_action_item("- [HIGH] task")
        assert result["priority"] == "high"

    def test_default_priority_medium_when_missing(self):
        result = meeting_notes._parse_action_item("- some task | bob")
        assert result["priority"] == "medium"
        assert result["owner"] == "bob"

    def test_dash_owner_treated_as_empty(self):
        result = meeting_notes._parse_action_item("- task | - | -")
        assert result["owner"] == ""
        assert result["deadline"] == ""

    def test_blank_owner_empty(self):
        result = meeting_notes._parse_action_item("- task |  |  ")
        assert result["owner"] == ""

    def test_none_marker_returns_none(self):
        assert meeting_notes._parse_action_item("- (none)") is None

    def test_empty_returns_none(self):
        assert meeting_notes._parse_action_item("") is None
        assert meeting_notes._parse_action_item("-") is None

    def test_no_title_returns_none(self):
        assert meeting_notes._parse_action_item("- [high] |alice") is None

    def test_strips_dash_prefix(self):
        result = meeting_notes._parse_action_item("- task")
        assert result["title"] == "task"

    def test_only_title_no_pipes(self):
        result = meeting_notes._parse_action_item("- finish report")
        assert result["title"] == "finish report"
        assert result["owner"] == ""
        assert result["deadline"] == ""


class TestParseExtraction:
    def test_full_response(self):
        response = (
            "ACTION_ITEMS:\n"
            "- [urgent] Deploy hotfix | alice | today\n"
            "- [medium] Update docs | bob | next week\n"
            "DECISIONS:\n"
            "- adopt new framework\n"
            "- migrate database\n"
            "NEXT_STEPS:\n"
            "- schedule followup\n"
            "SUMMARY: hotfix urgent, framework decided"
        )
        result = meeting_notes._parse_extraction(response)
        assert len(result["action_items"]) == 2
        assert result["action_items"][0]["title"] == "Deploy hotfix"
        assert result["action_items"][0]["priority"] == "urgent"
        assert result["decisions"] == ["adopt new framework", "migrate database"]
        assert result["next_steps"] == ["schedule followup"]
        assert result["summary"] == "hotfix urgent, framework decided"

    def test_empty_response(self):
        result = meeting_notes._parse_extraction("")
        assert result == {
            "action_items": [],
            "decisions": [],
            "next_steps": [],
            "summary": "",
        }

    def test_only_summary(self):
        result = meeting_notes._parse_extraction("SUMMARY: bukan catatan meeting")
        assert result["summary"] == "bukan catatan meeting"
        assert result["action_items"] == []

    def test_max_action_items_capped(self):
        items = "\n".join(f"- [low] task{i} | x" for i in range(15))
        response = f"ACTION_ITEMS:\n{items}\nSUMMARY: too many"
        result = meeting_notes._parse_extraction(response)
        assert len(result["action_items"]) == meeting_notes._MAX_ACTION_ITEMS

    def test_none_marker_skipped_in_decisions(self):
        response = "DECISIONS:\n- (none)\n- real decision\nSUMMARY: x"
        result = meeting_notes._parse_extraction(response)
        assert result["decisions"] == ["real decision"]

    def test_summary_ends_section(self):
        response = (
            "ACTION_ITEMS:\n"
            "- [low] one\n"
            "SUMMARY: end\n"
            "- stray bullet should not be parsed\n"
        )
        result = meeting_notes._parse_extraction(response)
        assert len(result["action_items"]) == 1

    def test_blank_lines_skipped(self):
        response = (
            "ACTION_ITEMS:\n"
            "\n"
            "- [high] task1\n"
            "\n"
            "DECISIONS:\n"
            "- decided\n"
            "SUMMARY: s"
        )
        result = meeting_notes._parse_extraction(response)
        assert len(result["action_items"]) == 1
        assert result["decisions"] == ["decided"]


class TestExtractShortCircuit:
    def test_empty_transcript(self):
        result = _run(meeting_notes.extract(""))
        assert result["summary"] == "transkrip kosong"
        assert result["action_items"] == []

    def test_whitespace_only_transcript(self):
        result = _run(meeting_notes.extract("   \n\t  "))
        assert result["summary"] == "transkrip kosong"

    def test_short_circuit_does_not_call_llm(self, monkeypatch):
        called = {"count": 0}

        async def fake_chat(messages, temperature, max_tokens):
            called["count"] += 1
            return "SUMMARY: x"

        monkeypatch.setattr(meeting_notes.llm, "chat_completion", fake_chat)
        _run(meeting_notes.extract(""))
        assert called["count"] == 0


class TestExtractWithLlm:
    @pytest.fixture
    def captured(self, monkeypatch):
        store = {"user_content": None}

        async def fake_chat(messages, temperature, max_tokens):
            store["user_content"] = messages[1]["content"]
            return (
                "ACTION_ITEMS:\n"
                "- [high] follow up | charlie\n"
                "DECISIONS:\n"
                "- (none)\n"
                "SUMMARY: short meeting"
            )

        monkeypatch.setattr(meeting_notes.llm, "chat_completion", fake_chat)
        return store

    def test_llm_called_for_real_transcript(self, captured):
        result = _run(meeting_notes.extract("alice: deploy on friday"))
        assert result["action_items"][0]["title"] == "follow up"
        assert result["truncated"] is False
        assert result["summary"] == "short meeting"

    def test_user_content_includes_transcript(self, captured):
        _run(meeting_notes.extract("hello world meeting"))
        assert "hello world meeting" in captured["user_content"]

    def test_truncation_marker_when_long(self, captured):
        big = "x" * (meeting_notes._MAX_TRANSCRIPT_CHARS + 500)
        result = _run(meeting_notes.extract(big))
        assert result["truncated"] is True
        assert "terpotong" in captured["user_content"]
        assert str(len(big)) in captured["user_content"]

    def test_no_truncation_under_threshold(self, captured):
        result = _run(meeting_notes.extract("short"))
        assert result["truncated"] is False
        assert "terpotong" not in captured["user_content"]

    def test_raw_response_preserved(self, captured):
        result = _run(meeting_notes.extract("transcript"))
        assert "ACTION_ITEMS" in result["raw"]


class TestProcessMeeting:
    @pytest.fixture
    def patches(self, monkeypatch):
        store: dict[str, Any] = {"created": [], "create_raises": False}

        async def fake_extract(transcript):
            return {
                "action_items": [
                    {"title": "deploy", "priority": "urgent", "owner": "alice", "deadline": "today"},
                    {"title": "review", "priority": "low", "owner": "", "deadline": ""},
                ],
                "decisions": ["ship it"],
                "next_steps": ["pair on tests"],
                "summary": "fast meeting",
                "truncated": False,
                "raw": "raw-text",
            }

        def fake_create_task(title, priority, due_date, user_id):
            if store["create_raises"]:
                raise RuntimeError("qdrant down")
            tid = f"task-{len(store['created'])}"
            store["created"].append({
                "id": tid, "title": title, "priority": priority,
                "due_date": due_date, "user_id": user_id,
            })
            return tid

        monkeypatch.setattr(meeting_notes, "extract", fake_extract)
        monkeypatch.setattr(meeting_notes.tools, "create_task", fake_create_task)
        return store

    def test_creates_tasks_by_default(self, patches):
        result = _run(meeting_notes.process_meeting("blah", user_id=42))
        assert result["tasks_created"] == 2
        assert len(result["task_ids"]) == 2

    def test_skip_task_creation_when_disabled(self, patches):
        result = _run(meeting_notes.process_meeting("blah", auto_create_tasks=False))
        assert result["tasks_created"] == 0
        assert patches["created"] == []

    def test_owner_appended_to_title(self, patches):
        _run(meeting_notes.process_meeting("blah", user_id=42))
        deploy_call = next(t for t in patches["created"] if "deploy" in t["title"])
        assert "PIC: alice" in deploy_call["title"]

    def test_no_owner_no_pic_suffix(self, patches):
        _run(meeting_notes.process_meeting("blah", user_id=42))
        review_call = next(t for t in patches["created"] if "review" in t["title"])
        assert "PIC" not in review_call["title"]

    def test_priority_mapped(self, patches):
        _run(meeting_notes.process_meeting("blah", user_id=42))
        priorities = [t["priority"] for t in patches["created"]]
        assert "urgent" in priorities
        assert "low" in priorities

    def test_unknown_priority_falls_back_to_medium(self, monkeypatch):
        async def fake_extract(transcript):
            return {
                "action_items": [
                    {"title": "x", "priority": "WAFFLE", "owner": "", "deadline": ""},
                ],
                "decisions": [], "next_steps": [], "summary": "",
                "truncated": False, "raw": "",
            }
        captured = {}
        def fake_create_task(title, priority, due_date, user_id):
            captured["priority"] = priority
            return "tid-1"
        monkeypatch.setattr(meeting_notes, "extract", fake_extract)
        monkeypatch.setattr(meeting_notes.tools, "create_task", fake_create_task)
        _run(meeting_notes.process_meeting("blah", user_id=1))
        assert captured["priority"] == "medium"

    def test_create_task_failure_continues(self, patches):
        patches["create_raises"] = True
        result = _run(meeting_notes.process_meeting("blah", user_id=42))
        assert result["tasks_created"] == 0
        assert result["task_ids"] == []
        assert result["action_items"]


class TestFormatForTelegram:
    def test_summary_only(self):
        result = {"summary": "hi", "action_items": [], "decisions": [], "next_steps": []}
        out = meeting_notes.format_for_telegram(result)
        assert "Meeting Summary" in out
        assert "hi" in out

    def test_action_items_with_priority_and_owner(self):
        result = {
            "summary": "",
            "action_items": [
                {"title": "deploy", "priority": "urgent", "owner": "alice", "deadline": "today"},
            ],
            "decisions": [],
            "next_steps": [],
        }
        out = meeting_notes.format_for_telegram(result)
        assert "Action Items (1)" in out
        assert "[urgent]" in out
        assert "deploy" in out
        assert "PIC: alice" in out
        assert "Due: today" in out

    def test_action_item_no_owner_no_due(self):
        result = {
            "summary": "",
            "action_items": [
                {"title": "task", "priority": "low", "owner": "", "deadline": ""},
            ],
            "decisions": [],
            "next_steps": [],
        }
        out = meeting_notes.format_for_telegram(result)
        assert "PIC:" not in out
        assert "Due:" not in out

    def test_decisions_section(self):
        result = {
            "summary": "",
            "action_items": [],
            "decisions": ["adopted X"],
            "next_steps": [],
        }
        out = meeting_notes.format_for_telegram(result)
        assert "Decisions" in out
        assert "adopted X" in out

    def test_next_steps_section(self):
        result = {
            "summary": "",
            "action_items": [],
            "decisions": [],
            "next_steps": ["plan sprint"],
        }
        out = meeting_notes.format_for_telegram(result)
        assert "Next Steps" in out
        assert "plan sprint" in out

    def test_tasks_created_message(self):
        result = {
            "summary": "x",
            "action_items": [{"title": "t", "priority": "low", "owner": "", "deadline": ""}],
            "decisions": [],
            "next_steps": [],
            "tasks_created": 3,
        }
        out = meeting_notes.format_for_telegram(result)
        assert "3 task otomatis" in out

    def test_no_tasks_disabled_message(self):
        result = {
            "summary": "",
            "action_items": [{"title": "t", "priority": "low", "owner": "", "deadline": ""}],
            "decisions": [],
            "next_steps": [],
            "tasks_created": 0,
        }
        out = meeting_notes.format_for_telegram(result)
        assert "auto_create_tasks=false" in out

    def test_truncation_warning(self):
        result = {
            "summary": "x",
            "action_items": [],
            "decisions": [],
            "next_steps": [],
            "truncated": True,
        }
        out = meeting_notes.format_for_telegram(result)
        assert "terlalu panjang" in out

    def test_empty_result_fallback_message(self):
        result = {
            "summary": "",
            "action_items": [],
            "decisions": [],
            "next_steps": [],
        }
        out = meeting_notes.format_for_telegram(result)
        assert "Tidak ada action item" in out
