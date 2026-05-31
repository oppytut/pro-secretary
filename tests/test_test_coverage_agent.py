from __future__ import annotations

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest

from app import test_coverage


def _run(coro):
    return asyncio.run(coro)


@pytest.fixture
def whitelist_file(tmp_path, monkeypatch):
    path = tmp_path / "coverage_repos.json"
    monkeypatch.setattr(test_coverage, "_WHITELIST_FILE", path)
    return path


class TestWhitelist:
    def test_get_empty_when_no_file(self, whitelist_file):
        assert test_coverage.get_whitelist() == []

    def test_set_creates_parent_dir(self, tmp_path, monkeypatch):
        nested = tmp_path / "deep" / "coverage_repos.json"
        monkeypatch.setattr(test_coverage, "_WHITELIST_FILE", nested)
        test_coverage.set_whitelist(["foo/bar"])
        assert nested.exists()

    def test_roundtrip(self, whitelist_file):
        test_coverage.set_whitelist(["foo/bar", "baz/qux"])
        assert test_coverage.get_whitelist() == ["foo/bar", "baz/qux"]

    def test_corrupt_returns_empty(self, whitelist_file):
        whitelist_file.write_text("not-json{")
        assert test_coverage.get_whitelist() == []

    def test_non_list_returns_empty(self, whitelist_file):
        whitelist_file.write_text('{"not": "list"}')
        assert test_coverage.get_whitelist() == []


class TestIsRepoAllowed:
    def test_empty_whitelist_denies(self, whitelist_file):
        assert test_coverage.is_repo_allowed("foo/bar") is False

    def test_match_allows(self, whitelist_file):
        test_coverage.set_whitelist(["foo/bar"])
        assert test_coverage.is_repo_allowed("foo/bar") is True

    def test_no_match_denies(self, whitelist_file):
        test_coverage.set_whitelist(["foo/bar"])
        assert test_coverage.is_repo_allowed("baz/qux") is False


class TestRun:
    def test_completes_normally(self, monkeypatch):
        class FakeProc:
            returncode = 0

            async def communicate(self):
                return b"hello", b""

        async def fake_create(*args, **kwargs):
            return FakeProc()

        monkeypatch.setattr(asyncio, "create_subprocess_exec", fake_create)
        rc, out, err = _run(test_coverage._run(["echo", "hello"]))
        assert rc == 0
        assert out == "hello"

    def test_timeout_kills_process(self, monkeypatch):
        class FakeProc:
            returncode = 0
            killed = False

            async def communicate(self):
                await asyncio.sleep(10)

            def kill(self):
                self.killed = True

            async def wait(self):
                pass

        proc = FakeProc()

        async def fake_create(*args, **kwargs):
            return proc

        monkeypatch.setattr(asyncio, "create_subprocess_exec", fake_create)
        rc, out, err = _run(test_coverage._run(["sleep", "10"], timeout=0))
        assert rc == 124
        assert "timeout" in err
        assert proc.killed


class TestCloneRepo:
    def test_returns_false_without_pat(self, monkeypatch, tmp_path):
        from app import config
        monkeypatch.setattr(config, "GH_PAT", "")
        assert _run(test_coverage.clone_repo("foo/bar", str(tmp_path))) is False

    def test_returns_false_on_clone_failure(self, monkeypatch, tmp_path):
        from app import config
        monkeypatch.setattr(config, "GH_PAT", "ghp_x")

        async def fake_run(cmd, cwd=None, timeout=60):
            return 128, "", "fatal: not found"

        monkeypatch.setattr(test_coverage, "_run", fake_run)
        assert _run(test_coverage.clone_repo("foo/bar", str(tmp_path))) is False

    def test_returns_true_on_success(self, monkeypatch, tmp_path):
        from app import config
        monkeypatch.setattr(config, "GH_PAT", "ghp_x")

        async def fake_run(cmd, cwd=None, timeout=60):
            return 0, "", ""

        monkeypatch.setattr(test_coverage, "_run", fake_run)
        assert _run(test_coverage.clone_repo("foo/bar", str(tmp_path))) is True


class TestRunCoverage:
    def test_returns_none_when_no_json(self, tmp_path, monkeypatch):
        async def fake_run(cmd, cwd=None, timeout=60):
            return 0, "", ""

        monkeypatch.setattr(test_coverage, "_run", fake_run)
        assert _run(test_coverage.run_coverage(str(tmp_path))) is None

    def test_returns_parsed_json(self, tmp_path, monkeypatch):
        (tmp_path / "coverage.json").write_text('{"files": {"a.py": {"summary": {}}}}')

        async def fake_run(cmd, cwd=None, timeout=60):
            return 0, "", ""

        monkeypatch.setattr(test_coverage, "_run", fake_run)
        data = _run(test_coverage.run_coverage(str(tmp_path)))
        assert data == {"files": {"a.py": {"summary": {}}}}

    def test_returns_none_on_corrupt_json(self, tmp_path, monkeypatch):
        (tmp_path / "coverage.json").write_text("not-json{")

        async def fake_run(cmd, cwd=None, timeout=60):
            return 0, "", ""

        monkeypatch.setattr(test_coverage, "_run", fake_run)
        assert _run(test_coverage.run_coverage(str(tmp_path))) is None


class TestPickLowestCoverageFile:
    def test_returns_none_when_no_files(self):
        assert test_coverage.pick_lowest_coverage_file({"files": {}}) is None

    def test_skips_high_coverage(self, monkeypatch):
        monkeypatch.setattr(test_coverage, "COVERAGE_TARGET", 80.0)
        data = {
            "files": {
                "a.py": {"summary": {"num_statements": 50, "percent_covered": 95.0}, "missing_lines": []}
            }
        }
        assert test_coverage.pick_lowest_coverage_file(data) is None

    def test_skips_too_small(self, monkeypatch):
        monkeypatch.setattr(test_coverage, "COVERAGE_TARGET", 80.0)
        monkeypatch.setattr(test_coverage, "COVERAGE_MIN_LINES", 10)
        data = {
            "files": {
                "a.py": {"summary": {"num_statements": 5, "percent_covered": 0.0}, "missing_lines": [1, 2]}
            }
        }
        assert test_coverage.pick_lowest_coverage_file(data) is None

    def test_skips_too_large(self, monkeypatch):
        monkeypatch.setattr(test_coverage, "COVERAGE_TARGET", 80.0)
        monkeypatch.setattr(test_coverage, "COVERAGE_MAX_LINES", 100)
        data = {
            "files": {
                "a.py": {"summary": {"num_statements": 500, "percent_covered": 0.0}, "missing_lines": []}
            }
        }
        assert test_coverage.pick_lowest_coverage_file(data) is None

    def test_skips_test_files(self, monkeypatch):
        monkeypatch.setattr(test_coverage, "COVERAGE_TARGET", 80.0)
        data = {
            "files": {
                "tests/test_a.py": {"summary": {"num_statements": 50, "percent_covered": 0.0}, "missing_lines": []},
                "src/test_helper.py": {"summary": {"num_statements": 50, "percent_covered": 0.0}, "missing_lines": []},
                "conftest.py": {"summary": {"num_statements": 50, "percent_covered": 0.0}, "missing_lines": []},
            }
        }
        assert test_coverage.pick_lowest_coverage_file(data) is None

    def test_picks_lowest_percent(self, monkeypatch):
        monkeypatch.setattr(test_coverage, "COVERAGE_TARGET", 80.0)
        data = {
            "files": {
                "a.py": {"summary": {"num_statements": 50, "percent_covered": 70.0}, "missing_lines": [10]},
                "b.py": {"summary": {"num_statements": 50, "percent_covered": 30.0}, "missing_lines": [20]},
                "c.py": {"summary": {"num_statements": 50, "percent_covered": 50.0}, "missing_lines": [30]},
            }
        }
        result = test_coverage.pick_lowest_coverage_file(data)
        assert result is not None
        assert result["path"] == "b.py"
        assert result["percent"] == 30.0

    def test_tiebreak_by_largest_file(self, monkeypatch):
        monkeypatch.setattr(test_coverage, "COVERAGE_TARGET", 80.0)
        data = {
            "files": {
                "a.py": {"summary": {"num_statements": 30, "percent_covered": 50.0}, "missing_lines": []},
                "b.py": {"summary": {"num_statements": 80, "percent_covered": 50.0}, "missing_lines": []},
            }
        }
        result = test_coverage.pick_lowest_coverage_file(data)
        assert result is not None
        assert result["path"] == "b.py"


class TestFindSampleTests:
    def test_returns_empty_when_no_tests(self, tmp_path):
        assert test_coverage.find_sample_tests(str(tmp_path)) == ""

    def test_picks_test_files_under_limit(self, tmp_path):
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        good = "x = 1\n" * 100
        (tests_dir / "test_a.py").write_text(good)
        (tests_dir / "test_b.py").write_text(good)
        result = test_coverage.find_sample_tests(str(tmp_path), limit=2)
        assert "test_a.py" in result
        assert "test_b.py" in result

    def test_skips_huge_files(self, tmp_path):
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        huge = "x = 1\n" * 5000
        (tests_dir / "test_huge.py").write_text(huge)
        result = test_coverage.find_sample_tests(str(tmp_path))
        assert "test_huge.py" not in result

    def test_respects_limit(self, tmp_path):
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        good = "x = 1\n" * 100
        for i in range(5):
            (tests_dir / f"test_{i}.py").write_text(good)
        result = test_coverage.find_sample_tests(str(tmp_path), limit=2)
        assert result.count("# ---") == 2


class TestStripCodeFences:
    def test_strips_python_fence(self):
        text = "```python\ndef foo():\n    pass\n```"
        assert "def foo()" in test_coverage._strip_code_fences(text)
        assert "```" not in test_coverage._strip_code_fences(text)

    def test_strips_plain_fence(self):
        text = "```\ndef foo():\n    pass\n```"
        result = test_coverage._strip_code_fences(text)
        assert "def foo()" in result
        assert "```" not in result

    def test_passes_through_no_fence(self):
        text = "def foo():\n    pass"
        assert test_coverage._strip_code_fences(text) == text


class TestGenerateTests:
    def test_calls_llm_and_strips_fences(self, monkeypatch):
        async def fake_chat(messages, **kwargs):
            return "```python\ndef test_x():\n    assert True\n```"

        from app import llm
        monkeypatch.setattr(llm, "chat_completion", fake_chat)
        result = _run(
            test_coverage.generate_tests("a.py", "x = 1", [1, 2], "sample")
        )
        assert "def test_x()" in result
        assert "```" not in result

    def test_passes_missing_lines(self, monkeypatch):
        captured = {}

        async def fake_chat(messages, **kwargs):
            captured["msgs"] = messages
            return "def test_x(): pass"

        from app import llm
        monkeypatch.setattr(llm, "chat_completion", fake_chat)
        _run(test_coverage.generate_tests("a.py", "x = 1", [10, 20, 30], "sample"))
        user_msg = captured["msgs"][-1]["content"]
        assert "[10, 20, 30]" in user_msg


class TestVerifyTests:
    def test_returns_true_on_success(self, tmp_path, monkeypatch):
        async def fake_run(cmd, cwd=None, timeout=60):
            return 0, "1 passed", ""

        monkeypatch.setattr(test_coverage, "_run", fake_run)
        ok, output = _run(test_coverage.verify_tests(str(tmp_path), "tests/test_a.py"))
        assert ok is True
        assert "1 passed" in output

    def test_returns_false_on_failure(self, tmp_path, monkeypatch):
        async def fake_run(cmd, cwd=None, timeout=60):
            return 1, "FAILED test_a", "error"

        monkeypatch.setattr(test_coverage, "_run", fake_run)
        ok, output = _run(test_coverage.verify_tests(str(tmp_path), "tests/test_a.py"))
        assert ok is False


class TestHasOpenCoveragePr:
    def test_returns_false_on_http_error(self, monkeypatch):
        async def fake_get(*args, **kwargs):
            return MagicMock(status_code=500, json=lambda: [], text="err")

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return None

        client_mock = MagicMock()
        client_mock.__aenter__ = AsyncMock(return_value=client_mock)
        client_mock.__aexit__ = AsyncMock(return_value=None)
        client_mock.get = AsyncMock(return_value=MagicMock(status_code=500, json=lambda: []))

        monkeypatch.setattr(httpx, "AsyncClient", lambda timeout=20.0: client_mock)
        result = _run(test_coverage.has_open_coverage_pr("foo/bar", "src/x.py"))
        assert result is False

    def test_returns_true_when_title_matches(self, monkeypatch):
        client_mock = MagicMock()
        client_mock.__aenter__ = AsyncMock(return_value=client_mock)
        client_mock.__aexit__ = AsyncMock(return_value=None)
        response = MagicMock(
            status_code=200,
            json=lambda: [{"title": "test: coverage tests for src/x.py", "head": {"ref": "coverage/x"}}],
        )
        client_mock.get = AsyncMock(return_value=response)
        monkeypatch.setattr(httpx, "AsyncClient", lambda timeout=20.0: client_mock)
        result = _run(test_coverage.has_open_coverage_pr("foo/bar", "src/x.py"))
        assert result is True

    def test_returns_false_when_no_match(self, monkeypatch):
        client_mock = MagicMock()
        client_mock.__aenter__ = AsyncMock(return_value=client_mock)
        client_mock.__aexit__ = AsyncMock(return_value=None)
        response = MagicMock(
            status_code=200,
            json=lambda: [{"title": "feat: unrelated", "head": {"ref": "feature/x"}}],
        )
        client_mock.get = AsyncMock(return_value=response)
        monkeypatch.setattr(httpx, "AsyncClient", lambda timeout=20.0: client_mock)
        result = _run(test_coverage.has_open_coverage_pr("foo/bar", "src/x.py"))
        assert result is False

    def test_returns_false_on_request_error(self, monkeypatch):
        client_mock = MagicMock()
        client_mock.__aenter__ = AsyncMock(return_value=client_mock)
        client_mock.__aexit__ = AsyncMock(return_value=None)
        client_mock.get = AsyncMock(side_effect=httpx.RequestError("conn"))
        monkeypatch.setattr(httpx, "AsyncClient", lambda timeout=20.0: client_mock)
        result = _run(test_coverage.has_open_coverage_pr("foo/bar", "src/x.py"))
        assert result is False


class TestScanAndPr:
    def test_rejects_non_whitelisted(self, whitelist_file):
        result = _run(test_coverage.scan_and_pr("foo/bar"))
        assert result["ok"] is False
        assert "not in coverage whitelist" in result["error"]

    def test_handles_clone_failure(self, whitelist_file, monkeypatch):
        test_coverage.set_whitelist(["foo/bar"])

        async def fake_clone(name, dest, branch="main"):
            return False

        monkeypatch.setattr(test_coverage, "clone_repo", fake_clone)
        result = _run(test_coverage.scan_and_pr("foo/bar"))
        assert result["ok"] is False
        assert "clone failed" in result["error"]

    def test_handles_coverage_failure(self, whitelist_file, monkeypatch):
        test_coverage.set_whitelist(["foo/bar"])

        async def fake_clone(name, dest, branch="main"):
            return True

        async def fake_cov(repo_dir):
            return None

        monkeypatch.setattr(test_coverage, "clone_repo", fake_clone)
        monkeypatch.setattr(test_coverage, "run_coverage", fake_cov)
        result = _run(test_coverage.scan_and_pr("foo/bar"))
        assert result["ok"] is False
        assert "coverage scan failed" in result["error"]

    def test_skips_when_no_low_coverage(self, whitelist_file, monkeypatch):
        test_coverage.set_whitelist(["foo/bar"])

        async def fake_clone(name, dest, branch="main"):
            return True

        async def fake_cov(repo_dir):
            return {"files": {}}

        monkeypatch.setattr(test_coverage, "clone_repo", fake_clone)
        monkeypatch.setattr(test_coverage, "run_coverage", fake_cov)
        result = _run(test_coverage.scan_and_pr("foo/bar"))
        assert result["ok"] is True
        assert result["skipped"] is True

    def test_skips_when_open_pr_exists(self, whitelist_file, monkeypatch, tmp_path):
        test_coverage.set_whitelist(["foo/bar"])

        async def fake_clone(name, dest, branch="main"):
            return True

        async def fake_cov(repo_dir):
            return {
                "files": {
                    "a.py": {
                        "summary": {"num_statements": 50, "percent_covered": 30.0},
                        "missing_lines": [1, 2],
                    }
                }
            }

        async def fake_has_pr(name, target):
            return True

        monkeypatch.setattr(test_coverage, "clone_repo", fake_clone)
        monkeypatch.setattr(test_coverage, "run_coverage", fake_cov)
        monkeypatch.setattr(test_coverage, "has_open_coverage_pr", fake_has_pr)
        monkeypatch.setattr(test_coverage, "COVERAGE_TARGET", 80.0)
        result = _run(test_coverage.scan_and_pr("foo/bar"))
        assert result["skipped"] is True
        assert "already exists" in result["reason"]

    def test_aborts_when_llm_produces_no_test(self, whitelist_file, monkeypatch, tmp_path):
        test_coverage.set_whitelist(["foo/bar"])

        async def fake_clone(name, dest, branch="main"):
            (Path(dest) / "a.py").write_text("def foo(): pass\n")
            return True

        async def fake_cov(repo_dir):
            return {
                "files": {
                    "a.py": {
                        "summary": {"num_statements": 50, "percent_covered": 30.0},
                        "missing_lines": [1],
                    }
                }
            }

        async def fake_has_pr(name, target):
            return False

        async def fake_gen(*args, **kwargs):
            return "no actual test here"

        from pathlib import Path
        monkeypatch.setattr(test_coverage, "clone_repo", fake_clone)
        monkeypatch.setattr(test_coverage, "run_coverage", fake_cov)
        monkeypatch.setattr(test_coverage, "has_open_coverage_pr", fake_has_pr)
        monkeypatch.setattr(test_coverage, "generate_tests", fake_gen)
        monkeypatch.setattr(test_coverage, "COVERAGE_TARGET", 80.0)
        result = _run(test_coverage.scan_and_pr("foo/bar"))
        assert result["ok"] is False
        assert "no valid test code" in result["error"]


class TestOpenPr:
    def test_returns_error_on_checkout_failure(self, tmp_path, monkeypatch):
        async def fake_run(cmd, cwd=None, timeout=60):
            if cmd[1] == "checkout":
                return 1, "", "branch exists"
            return 0, "", ""

        monkeypatch.setattr(test_coverage, "_run", fake_run)
        result = _run(test_coverage.open_pr("foo/bar", str(tmp_path), "tests/x.py", "src/x.py", 30.0))
        assert result["ok"] is False
        assert "checkout failed" in result["error"]

    def test_returns_error_on_push_failure(self, tmp_path, monkeypatch):
        async def fake_run(cmd, cwd=None, timeout=60):
            if cmd[1] == "push":
                return 1, "", "permission denied"
            return 0, "", ""

        monkeypatch.setattr(test_coverage, "_run", fake_run)
        result = _run(test_coverage.open_pr("foo/bar", str(tmp_path), "tests/x.py", "src/x.py", 30.0))
        assert result["ok"] is False
        assert "push failed" in result["error"]

    def test_creates_pr_on_success(self, tmp_path, monkeypatch):
        async def fake_run(cmd, cwd=None, timeout=60):
            return 0, "", ""

        async def fake_post(path, payload):
            return 201, {"html_url": "https://gh/pr/1", "number": 1}

        monkeypatch.setattr(test_coverage, "_run", fake_run)
        monkeypatch.setattr(test_coverage, "_gh_post", fake_post)
        result = _run(test_coverage.open_pr("foo/bar", str(tmp_path), "tests/x.py", "src/x.py", 30.0))
        assert result["ok"] is True
        assert result["pr_number"] == 1
