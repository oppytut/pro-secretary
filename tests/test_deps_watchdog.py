"""Tests for parser functions in langgraph-agent/app/deps_watchdog.py.

Scope: file-based parsers only. Network calls (OSV API) are out of scope.
Manifests are written to tmp_path fixtures.
"""
from __future__ import annotations

import json

from app import deps_watchdog as dw


class TestStripNpmRange:
    def test_caret_range(self):
        assert dw._strip_npm_range("^1.2.3") == "1.2.3"

    def test_tilde_range(self):
        assert dw._strip_npm_range("~1.2.3") == "1.2.3"

    def test_gte_range(self):
        assert dw._strip_npm_range(">=1.2.3") == "1.2.3"

    def test_exact_version(self):
        assert dw._strip_npm_range("1.2.3") == "1.2.3"

    def test_two_segment_version(self):
        assert dw._strip_npm_range("1.2") == "1.2"

    def test_or_range_rejected(self):
        assert dw._strip_npm_range("1.0.0 || 2.0.0") is None

    def test_dash_range_rejected(self):
        assert dw._strip_npm_range("1.0.0 - 2.0.0") is None

    def test_git_url_rejected(self):
        assert dw._strip_npm_range("git+https://example.com/repo.git") is None

    def test_workspace_rejected(self):
        assert dw._strip_npm_range("workspace:^1.0.0") is None

    def test_empty_returns_none(self):
        assert dw._strip_npm_range("") is None

    def test_non_string_returns_none(self):
        assert dw._strip_npm_range(None) is None
        assert dw._strip_npm_range(123) is None

    def test_garbage_returns_none(self):
        assert dw._strip_npm_range("latest") is None


class TestParsePackageJson:
    def test_basic_dependencies(self, tmp_path):
        path = tmp_path / "package.json"
        path.write_text(json.dumps({
            "dependencies": {"react": "^18.2.0", "lodash": "~4.17.21"},
            "devDependencies": {"jest": "29.7.0"},
        }))
        pkgs = dw._parse_package_json(path)
        names = {p["name"]: p["version"] for p in pkgs}
        assert names["react"] == "18.2.0"
        assert names["lodash"] == "4.17.21"
        assert names["jest"] == "29.7.0"
        assert all(p["ecosystem"] == "npm" for p in pkgs)

    def test_optional_deps_included(self, tmp_path):
        path = tmp_path / "package.json"
        path.write_text(json.dumps({"optionalDependencies": {"fsevents": "2.3.3"}}))
        pkgs = dw._parse_package_json(path)
        assert any(p["name"] == "fsevents" for p in pkgs)

    def test_skips_unparseable_specs(self, tmp_path):
        path = tmp_path / "package.json"
        path.write_text(json.dumps({
            "dependencies": {
                "good": "1.0.0",
                "git-pkg": "git+https://example.com/x.git",
                "workspace-pkg": "workspace:*",
            },
        }))
        pkgs = dw._parse_package_json(path)
        names = {p["name"] for p in pkgs}
        assert names == {"good"}

    def test_invalid_json_returns_empty(self, tmp_path):
        path = tmp_path / "package.json"
        path.write_text("{not valid json")
        assert dw._parse_package_json(path) == []

    def test_missing_file_returns_empty(self, tmp_path):
        assert dw._parse_package_json(tmp_path / "missing.json") == []


class TestParseRequirementsTxt:
    def test_pinned_versions(self, tmp_path):
        path = tmp_path / "requirements.txt"
        path.write_text("fastapi==0.136.1\nhttpx==0.28.1\npydantic==2.13.4\n")
        pkgs = dw._parse_requirements_txt(path)
        names = {p["name"]: p["version"] for p in pkgs}
        assert names == {"fastapi": "0.136.1", "httpx": "0.28.1", "pydantic": "2.13.4"}
        assert all(p["ecosystem"] == "PyPI" for p in pkgs)

    def test_extras_stripped(self, tmp_path):
        path = tmp_path / "requirements.txt"
        path.write_text("uvicorn[standard]==0.47.0\n")
        pkgs = dw._parse_requirements_txt(path)
        assert pkgs[0]["name"] == "uvicorn"
        assert pkgs[0]["version"] == "0.47.0"

    def test_comments_skipped(self, tmp_path):
        path = tmp_path / "requirements.txt"
        path.write_text("# top comment\nfastapi==0.136.1  # inline comment\n")
        pkgs = dw._parse_requirements_txt(path)
        assert len(pkgs) == 1
        assert pkgs[0]["name"] == "fastapi"

    def test_pip_flags_skipped(self, tmp_path):
        path = tmp_path / "requirements.txt"
        path.write_text("-r other.txt\n--index-url https://pypi.org/simple\nfastapi==0.136.1\n")
        pkgs = dw._parse_requirements_txt(path)
        assert len(pkgs) == 1

    def test_unpinned_skipped(self, tmp_path):
        path = tmp_path / "requirements.txt"
        path.write_text("fastapi\nhttpx>=0.28\n")
        pkgs = dw._parse_requirements_txt(path)
        assert pkgs == []


class TestParsePyproject:
    def test_poetry_dependencies(self, tmp_path):
        path = tmp_path / "pyproject.toml"
        path.write_text(
            "[tool.poetry]\nname = \"test\"\n\n"
            "[tool.poetry.dependencies]\n"
            "python = \"^3.11\"\n"
            "fastapi = \"^0.136.1\"\n"
            "httpx = {version = \"^0.28.1\"}\n"
        )
        pkgs = dw._parse_pyproject(path)
        names = {p["name"]: p["version"] for p in pkgs}
        assert "python" not in names
        assert names["fastapi"] == "0.136.1"
        assert names["httpx"] == "0.28.1"

    def test_invalid_toml_returns_empty(self, tmp_path):
        path = tmp_path / "pyproject.toml"
        path.write_text("not valid [[[ toml")
        assert dw._parse_pyproject(path) == []


class TestParseGoMod:
    def test_basic_requires(self, tmp_path):
        path = tmp_path / "go.mod"
        path.write_text(
            "module example.com/foo\n\n"
            "go 1.21\n\n"
            "require (\n"
            "\tgithub.com/gin-gonic/gin v1.9.1\n"
            "\tgolang.org/x/crypto v0.17.0\n"
            ")\n"
        )
        pkgs = dw._parse_go_mod(path)
        names = {p["name"]: p["version"] for p in pkgs}
        assert names["github.com/gin-gonic/gin"] == "1.9.1"
        assert names["golang.org/x/crypto"] == "0.17.0"
        assert all(p["ecosystem"] == "Go" for p in pkgs)


class TestDedupe:
    def test_removes_exact_duplicates(self):
        pkgs = [
            {"ecosystem": "npm", "name": "react", "version": "18.2.0"},
            {"ecosystem": "npm", "name": "react", "version": "18.2.0"},
            {"ecosystem": "PyPI", "name": "react", "version": "18.2.0"},
        ]
        out = dw._dedupe(pkgs)
        assert len(out) == 2

    def test_keeps_different_versions(self):
        pkgs = [
            {"ecosystem": "npm", "name": "react", "version": "17.0.0"},
            {"ecosystem": "npm", "name": "react", "version": "18.2.0"},
        ]
        assert len(dw._dedupe(pkgs)) == 2

    def test_empty_input(self):
        assert dw._dedupe([]) == []


class TestSeverityFromDetail:
    def test_database_specific_wins(self):
        detail = {
            "database_specific": {"severity": "high"},
            "severity": [{"score": "MODERATE"}],
        }
        assert dw._severity_from_detail(detail) == "HIGH"

    def test_severity_list_score(self):
        detail = {"severity": [{"score": "MODERATE"}]}
        assert dw._severity_from_detail(detail) == "MODERATE"

    def test_cvss_string_scores_high(self):
        detail = {"severity": [{"score": "CVSS:3.1/AV:N/AC:L"}]}
        assert dw._severity_from_detail(detail) == "HIGH"

    def test_unknown_when_no_data(self):
        assert dw._severity_from_detail({}) == "UNKNOWN"
        assert dw._severity_from_detail({"severity": []}) == "UNKNOWN"


class TestCollectManifests:
    def test_finds_known_manifests(self, tmp_path):
        (tmp_path / "package.json").write_text("{}")
        (tmp_path / "requirements.txt").write_text("")
        (tmp_path / "go.mod").write_text("module foo")
        (tmp_path / "ignored.md").write_text("# README")
        results = dw._collect_manifests(tmp_path)
        names = {path.name for _, path in results}
        assert "package.json" in names
        assert "requirements.txt" in names
        assert "go.mod" in names
        assert "ignored.md" not in names

    def test_recurses_into_subdirs(self, tmp_path):
        sub = tmp_path / "subproject"
        sub.mkdir()
        (sub / "package.json").write_text("{}")
        results = dw._collect_manifests(tmp_path)
        assert any(path.name == "package.json" for _, path in results)
