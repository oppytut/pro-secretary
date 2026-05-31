from __future__ import annotations

import asyncio

import pytest

from app import docs_sync


def _run(coro):
    return asyncio.run(coro)


class TestDiffChangedFiles:
    def test_extracts_from_diff_git_lines(self):
        diff = "diff --git a/foo.py b/foo.py\n+++ b/foo.py\n@@ -1 +1 @@\n-x\n+y\n"
        assert docs_sync._diff_changed_files(diff) == ["foo.py"]

    def test_multiple_files(self):
        diff = (
            "diff --git a/a.py b/a.py\n+++ b/a.py\n"
            "diff --git a/b.md b/b.md\n+++ b/b.md\n"
        )
        assert docs_sync._diff_changed_files(diff) == ["a.py", "b.md"]

    def test_dedup(self):
        diff = (
            "diff --git a/foo.py b/foo.py\n+++ b/foo.py\n"
            "diff --git a/foo.py b/foo.py\n+++ b/foo.py\n"
        )
        assert docs_sync._diff_changed_files(diff) == ["foo.py"]

    def test_empty_diff(self):
        assert docs_sync._diff_changed_files("") == []

    def test_falls_back_to_plus_plus_plus(self):
        diff = "+++ b/just_plus.py\n@@ -1 +1 @@\n"
        assert "just_plus.py" in docs_sync._diff_changed_files(diff)


class TestIsDocFile:
    def test_readme_root(self):
        assert docs_sync._is_doc_file("README.md") is True

    def test_readme_no_ext(self):
        assert docs_sync._is_doc_file("README") is True

    def test_changelog(self):
        assert docs_sync._is_doc_file("CHANGELOG.md") is True

    def test_changelog_lowercase(self):
        assert docs_sync._is_doc_file("changelog.md") is True

    def test_docs_dir(self):
        assert docs_sync._is_doc_file("docs/api.md") is True

    def test_doc_dir_singular(self):
        assert docs_sync._is_doc_file("doc/setup.rst") is True

    def test_github_dir(self):
        assert docs_sync._is_doc_file(".github/PULL_REQUEST_TEMPLATE.md") is True

    def test_md_extension(self):
        assert docs_sync._is_doc_file("notes.md") is True

    def test_rst_extension(self):
        assert docs_sync._is_doc_file("guide.rst") is True

    def test_python_file_not_doc(self):
        assert docs_sync._is_doc_file("src/foo.py") is False

    def test_yaml_outside_github_not_doc(self):
        assert docs_sync._is_doc_file("config/app.yml") is False


class TestClassifyDiff:
    def test_separates_code_and_doc_files(self):
        diff = (
            "diff --git a/src/foo.py b/src/foo.py\n+++ b/src/foo.py\n"
            "diff --git a/README.md b/README.md\n+++ b/README.md\n"
        )
        result = docs_sync._classify_diff(diff)
        assert result["code_files"] == ["src/foo.py"]
        assert result["doc_files"] == ["README.md"]

    def test_detects_api_change(self):
        diff = (
            "diff --git a/api.py b/api.py\n+++ b/api.py\n"
            "+@app.get('/users')\n"
        )
        signals = docs_sync._classify_diff(diff)["signals"]
        assert signals["has_api_change"] is True

    def test_detects_router_post_as_api(self):
        diff = "+++ b/x.py\n+router.post('/foo', handler)\n"
        assert docs_sync._classify_diff(diff)["signals"]["has_api_change"] is True

    def test_detects_env_change(self):
        diff = "+++ b/cfg.py\n+os.getenv('NEW_VAR')\n"
        assert docs_sync._classify_diff(diff)["signals"]["has_env_change"] is True

    def test_detects_command_change(self):
        diff = '+++ b/bot.py\n+app.add_handler(CommandHandler("new", h))\n'
        assert docs_sync._classify_diff(diff)["signals"]["has_command_change"] is True

    def test_no_signals_for_pure_doc_change(self):
        diff = "+++ b/README.md\n+New section\n"
        signals = docs_sync._classify_diff(diff)["signals"]
        assert signals == {
            "has_api_change": False,
            "has_env_change": False,
            "has_command_change": False,
        }

    def test_files_changed_includes_all(self):
        diff = (
            "diff --git a/a.py b/a.py\n+++ b/a.py\n"
            "diff --git a/README.md b/README.md\n+++ b/README.md\n"
        )
        result = docs_sync._classify_diff(diff)
        assert result["files_changed"] == ["a.py", "README.md"]


class TestParseLlmResponse:
    def test_needs_docs_verdict(self):
        response = (
            "VERDICT: NEEDS_DOCS\n"
            "AFFECTED_AREAS:\n"
            "- README\n"
            "- CHANGELOG\n"
            "SUGGESTIONS:\n"
            "- [README] add new section\n"
            "- [CHANGELOG] note breaking change\n"
            "SUMMARY: needs README + changelog updates"
        )
        result = docs_sync._parse_llm_response(response)
        assert result["verdict"] == "NEEDS_DOCS"
        assert result["affected_areas"] == ["README", "CHANGELOG"]
        assert result["suggestions"] == [
            "[README] add new section",
            "[CHANGELOG] note breaking change",
        ]
        assert result["summary"] == "needs README + changelog updates"

    def test_no_docs_needed_verdict(self):
        response = "VERDICT: NO_DOCS_NEEDED\nSUMMARY: pure refactor"
        result = docs_sync._parse_llm_response(response)
        assert result["verdict"] == "NO_DOCS_NEEDED"
        assert result["affected_areas"] == []
        assert result["suggestions"] == []
        assert result["summary"] == "pure refactor"

    def test_default_no_docs_when_no_verdict(self):
        result = docs_sync._parse_llm_response("just some text")
        assert result["verdict"] == "NO_DOCS_NEEDED"

    def test_unknown_verdict_falls_back_to_no_docs(self):
        result = docs_sync._parse_llm_response("VERDICT: WAFFLE\nSUMMARY: x")
        assert result["verdict"] == "NO_DOCS_NEEDED"

    def test_skips_none_marker_in_areas(self):
        response = "VERDICT: NEEDS_DOCS\nAFFECTED_AREAS:\n- (none)\n- README\n"
        result = docs_sync._parse_llm_response(response)
        assert result["affected_areas"] == ["README"]

    def test_skips_dash_only_lines(self):
        response = "VERDICT: NEEDS_DOCS\nSUGGESTIONS:\n- \n- real one\n"
        result = docs_sync._parse_llm_response(response)
        assert result["suggestions"] == ["real one"]

    def test_summary_resets_section(self):
        response = (
            "VERDICT: NEEDS_DOCS\n"
            "AFFECTED_AREAS:\n- README\n"
            "SUMMARY: done\n"
            "- stray line that should be ignored\n"
        )
        result = docs_sync._parse_llm_response(response)
        assert result["affected_areas"] == ["README"]
        assert result["summary"] == "done"


class TestAnalyzeShortCircuit:
    def test_empty_diff_returns_no_docs(self):
        result = _run(docs_sync.analyze("", "title"))
        assert result["verdict"] == "NO_DOCS_NEEDED"
        assert result["summary"] == "diff kosong"
        assert result["affected_areas"] == []

    def test_whitespace_diff_returns_no_docs(self):
        result = _run(docs_sync.analyze("   \n  \t  ", "title"))
        assert result["verdict"] == "NO_DOCS_NEEDED"

    def test_short_circuit_does_not_call_llm(self, monkeypatch):
        called = {"count": 0}

        async def fake_chat(messages, temperature, max_tokens):
            called["count"] += 1
            return "VERDICT: NEEDS_DOCS"

        monkeypatch.setattr(docs_sync.llm, "chat_completion", fake_chat)
        _run(docs_sync.analyze("", "title"))
        assert called["count"] == 0


class TestAnalyzeWithLlm:
    @pytest.fixture
    def captured(self, monkeypatch):
        store = {"messages": None, "user_content": None}

        async def fake_chat(messages, temperature, max_tokens):
            store["messages"] = messages
            store["user_content"] = messages[1]["content"]
            return "VERDICT: NEEDS_DOCS\nSUGGESTIONS:\n- [README] update\nSUMMARY: ok"

        monkeypatch.setattr(docs_sync.llm, "chat_completion", fake_chat)
        return store

    def test_llm_called_for_real_diff(self, captured):
        diff = "diff --git a/foo.py b/foo.py\n+++ b/foo.py\n+@app.get('/x')\n"
        result = _run(docs_sync.analyze(diff, "title"))
        assert captured["messages"] is not None
        assert result["verdict"] == "NEEDS_DOCS"

    def test_signal_hints_appended_when_api_changes(self, captured):
        diff = "diff --git a/api.py b/api.py\n+++ b/api.py\n+@app.get('/x')\n"
        _run(docs_sync.analyze(diff, "title"))
        assert "API endpoints changed" in captured["user_content"]

    def test_signal_hints_appended_when_env_changes(self, captured):
        diff = "diff --git a/cfg.py b/cfg.py\n+++ b/cfg.py\n+os.getenv('FOO')\n"
        _run(docs_sync.analyze(diff, "title"))
        assert "env vars referenced" in captured["user_content"]

    def test_doc_files_already_updated_hint(self, captured):
        diff = "diff --git a/README.md b/README.md\n+++ b/README.md\n+section\n"
        _run(docs_sync.analyze(diff, "title"))
        assert "doc files already updated" in captured["user_content"]

    def test_pr_body_clipped_to_500(self, captured):
        diff = "diff --git a/x.py b/x.py\n+++ b/x.py\n+x = 1\n"
        big = "y" * 800
        _run(docs_sync.analyze(diff, "title", pr_body=big))
        section = captured["user_content"].split("PR Description:")[1].split("\n")[0]
        assert len(section.strip()) <= 500

    def test_truncation_marker_in_user_content(self, captured):
        big = "diff --git a/x.py b/x.py\n+++ b/x.py\n" + ("+x\n" * 5000)
        result = _run(docs_sync.analyze(big, "title"))
        assert "truncated" in captured["user_content"]
        assert "classification" in result
