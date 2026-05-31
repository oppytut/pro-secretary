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

    def test_skip_dirs_excluded(self, tmp_path):
        ignored = tmp_path / "node_modules"
        ignored.mkdir()
        (ignored / "package.json").write_text("{}")
        kept = tmp_path / "src"
        kept.mkdir()
        (kept / "package.json").write_text("{}")
        results = dw._collect_manifests(tmp_path)
        paths = [path for _, path in results]
        assert all("node_modules" not in p.parts for p in paths)
        assert any(p.parent == kept for p in paths)

    def test_lockfile_replaces_sibling_package_json(self, tmp_path):
        (tmp_path / "package.json").write_text("{}")
        (tmp_path / "package-lock.json").write_text("{}")
        results = dw._collect_manifests(tmp_path)
        names = [n for n, _ in results]
        assert "package-lock.json" in names
        assert "package.json" not in names

    def test_package_json_kept_if_lock_in_different_dir(self, tmp_path):
        (tmp_path / "package.json").write_text("{}")
        sub = tmp_path / "sub"
        sub.mkdir()
        (sub / "package-lock.json").write_text("{}")
        results = dw._collect_manifests(tmp_path)
        kept_pkg = any(n == "package.json" and p.parent == tmp_path for n, p in results)
        kept_lock = any(n == "package-lock.json" for n, _ in results)
        assert kept_pkg
        assert kept_lock


class TestParsePackageLock:
    def test_v2_v3_packages_format(self, tmp_path):
        path = tmp_path / "package-lock.json"
        path.write_text(json.dumps({
            "lockfileVersion": 3,
            "packages": {
                "": {"name": "root"},
                "node_modules/react": {"version": "18.2.0"},
                "node_modules/lodash": {"version": "4.17.21"},
            },
        }))
        pkgs = dw._parse_package_lock(path)
        names = {p["name"]: p["version"] for p in pkgs}
        assert names["react"] == "18.2.0"
        assert names["lodash"] == "4.17.21"
        assert all(p["ecosystem"] == "npm" for p in pkgs)

    def test_v1_dependencies_format(self, tmp_path):
        path = tmp_path / "package-lock.json"
        path.write_text(json.dumps({
            "lockfileVersion": 1,
            "dependencies": {
                "react": {"version": "17.0.2"},
                "lodash": {"version": "4.17.21"},
            },
        }))
        pkgs = dw._parse_package_lock(path)
        names = {p["name"]: p["version"] for p in pkgs}
        assert names["react"] == "17.0.2"
        assert names["lodash"] == "4.17.21"

    def test_explicit_name_field_preferred(self, tmp_path):
        path = tmp_path / "package-lock.json"
        path.write_text(json.dumps({
            "packages": {
                "": {"name": "root"},
                "some/path": {"name": "explicit-name", "version": "1.2.3"},
            },
        }))
        pkgs = dw._parse_package_lock(path)
        assert {"name": "explicit-name", "version": "1.2.3", "ecosystem": "npm"} in pkgs

    def test_invalid_json_returns_empty(self, tmp_path):
        path = tmp_path / "package-lock.json"
        path.write_text("not json {")
        assert dw._parse_package_lock(path) == []

    def test_empty_returns_empty(self, tmp_path):
        path = tmp_path / "package-lock.json"
        path.write_text("{}")
        assert dw._parse_package_lock(path) == []


class TestParseComposerLock:
    def test_packages_extracted(self, tmp_path):
        path = tmp_path / "composer.lock"
        path.write_text(json.dumps({
            "packages": [
                {"name": "symfony/console", "version": "v6.4.0"},
                {"name": "monolog/monolog", "version": "3.5.0"},
            ],
            "packages-dev": [
                {"name": "phpunit/phpunit", "version": "v10.5.0"},
            ],
        }))
        pkgs = dw._parse_composer_lock(path)
        names = {p["name"]: p["version"] for p in pkgs}
        assert names["symfony/console"] == "6.4.0"
        assert names["monolog/monolog"] == "3.5.0"
        assert names["phpunit/phpunit"] == "10.5.0"
        assert all(p["ecosystem"] == "Packagist" for p in pkgs)

    def test_v_prefix_stripped(self, tmp_path):
        path = tmp_path / "composer.lock"
        path.write_text(json.dumps({"packages": [{"name": "x", "version": "v1.2.3"}]}))
        pkgs = dw._parse_composer_lock(path)
        assert pkgs[0]["version"] == "1.2.3"

    def test_invalid_json_returns_empty(self, tmp_path):
        path = tmp_path / "composer.lock"
        path.write_text("not valid")
        assert dw._parse_composer_lock(path) == []

    def test_skips_malformed_entries(self, tmp_path):
        path = tmp_path / "composer.lock"
        path.write_text(json.dumps({
            "packages": [
                {"name": "ok", "version": "1.0.0"},
                {"name": "no-version"},
                "not-a-dict",
                {"version": "no-name"},
            ],
        }))
        pkgs = dw._parse_composer_lock(path)
        assert len(pkgs) == 1
        assert pkgs[0]["name"] == "ok"


class TestParseGoModEdgeCases:
    def test_skips_comments_in_require_block(self, tmp_path):
        path = tmp_path / "go.mod"
        path.write_text(
            "module example.com/foo\n"
            "go 1.21\n"
            "require (\n"
            "\t// commented out\n"
            "\tgithub.com/x/y v1.0.0\n"
            ")\n"
        )
        pkgs = dw._parse_go_mod(path)
        assert len(pkgs) == 1
        assert pkgs[0]["name"] == "github.com/x/y"

    def test_single_line_require(self, tmp_path):
        path = tmp_path / "go.mod"
        path.write_text(
            "module example.com/foo\n"
            "go 1.21\n"
            "require github.com/single v2.0.0\n"
        )
        pkgs = dw._parse_go_mod(path)
        assert pkgs[0]["name"] == "github.com/single"
        assert pkgs[0]["version"] == "2.0.0"

    def test_missing_file_returns_empty(self, tmp_path):
        assert dw._parse_go_mod(tmp_path / "missing.mod") == []


class TestParseRequirementsEdge:
    def test_quoted_versions(self, tmp_path):
        path = tmp_path / "requirements.txt"
        path.write_text("PACKAGE-Name_v2 == 1.2.3+local.tag\n")
        pkgs = dw._parse_requirements_txt(path)
        assert pkgs[0]["name"] == "PACKAGE-Name_v2"
        assert pkgs[0]["version"] == "1.2.3+local.tag"

    def test_blank_lines_skipped(self, tmp_path):
        path = tmp_path / "requirements.txt"
        path.write_text("\nfastapi==0.1.0\n\n\nrequests==2.31.0\n\n")
        pkgs = dw._parse_requirements_txt(path)
        assert len(pkgs) == 2

    def test_missing_file_returns_empty(self, tmp_path):
        assert dw._parse_requirements_txt(tmp_path / "missing.txt") == []


class TestParsePyprojectEdge:
    def test_pep621_dependencies_not_parsed(self, tmp_path):
        path = tmp_path / "pyproject.toml"
        path.write_text(
            '[project]\n'
            'name = "test"\n'
            'dependencies = ["fastapi==0.1.0", "httpx>=0.27"]\n'
        )
        pkgs = dw._parse_pyproject(path)
        assert pkgs == []

    def test_dev_dependencies_section(self, tmp_path):
        path = tmp_path / "pyproject.toml"
        path.write_text(
            '[tool.poetry]\nname = "test"\n\n'
            '[tool.poetry.dev-dependencies]\n'
            'pytest = "^7.0"\n'
        )
        pkgs = dw._parse_pyproject(path)
        names = {p["name"] for p in pkgs}
        assert "pytest" in names

    def test_missing_file_returns_empty(self, tmp_path):
        assert dw._parse_pyproject(tmp_path / "missing.toml") == []


class TestSeverityFromDetailEdge:
    def test_high_normalized_uppercase(self):
        assert dw._severity_from_detail({"database_specific": {"severity": "high"}}) == "HIGH"

    def test_severity_list_skips_non_dict(self):
        detail = {"severity": [None, {"score": "LOW"}]}
        assert dw._severity_from_detail(detail) == "LOW"

    def test_first_score_used(self):
        detail = {"severity": [{"score": "MEDIUM"}, {"score": "HIGH"}]}
        assert dw._severity_from_detail(detail) == "MEDIUM"


class TestCollectPackagesFromRepo:
    def test_assembles_from_multiple_manifests(self, tmp_path):
        (tmp_path / "package.json").write_text(json.dumps({
            "dependencies": {"a": "1.0.0"},
        }))
        (tmp_path / "requirements.txt").write_text("b==2.0.0\n")
        pkgs = dw.collect_packages_from_repo(tmp_path)
        names = {p["name"] for p in pkgs}
        assert names >= {"a", "b"}

    def test_dedupes_across_manifests(self, tmp_path):
        (tmp_path / "package.json").write_text(json.dumps({
            "dependencies": {"shared": "1.0.0"},
        }))
        sub = tmp_path / "sub"
        sub.mkdir()
        (sub / "package.json").write_text(json.dumps({
            "dependencies": {"shared": "1.0.0"},
        }))
        pkgs = dw.collect_packages_from_repo(tmp_path)
        shared_count = sum(1 for p in pkgs if p["name"] == "shared")
        assert shared_count == 1

    def test_caps_at_max_packages(self, tmp_path, monkeypatch):
        monkeypatch.setattr(dw, "_MAX_PACKAGES_PER_REPO", 5)
        deps = {f"pkg{i}": f"{i}.0.0" for i in range(20)}
        (tmp_path / "package.json").write_text(json.dumps({"dependencies": deps}))
        pkgs = dw.collect_packages_from_repo(tmp_path)
        assert len(pkgs) <= 5

    def test_parser_failure_does_not_abort(self, tmp_path, monkeypatch):
        (tmp_path / "package.json").write_text(json.dumps({
            "dependencies": {"a": "1.0.0"},
        }))
        (tmp_path / "requirements.txt").write_text("b==2.0.0\n")

        original = dw._parse_package_json

        def boom(_path):
            raise RuntimeError("parser broke")

        monkeypatch.setattr(dw, "_parse_package_json", boom)
        monkeypatch.setitem(dw._PARSERS, "package.json", boom)
        try:
            pkgs = dw.collect_packages_from_repo(tmp_path)
        finally:
            monkeypatch.setattr(dw, "_parse_package_json", original)
            monkeypatch.setitem(dw._PARSERS, "package.json", original)
        assert any(p["name"] == "b" for p in pkgs)


class TestScanPackages:
    def _run(self, coro):
        import asyncio
        return asyncio.run(coro)

    def test_empty_input_returns_empty(self):
        result = self._run(dw.scan_packages([]))
        assert result == []

    def test_aggregates_findings_from_batch(self, monkeypatch):
        async def fake_batch(packages):
            return [
                [{"id": "GHSA-aaaa"}],
                [{"id": "GHSA-bbbb"}, {"id": "GHSA-cccc"}],
            ]

        async def fake_detail(vid):
            return {
                "summary": f"summary for {vid}",
                "database_specific": {"severity": "HIGH"},
            }

        monkeypatch.setattr(dw, "_query_osv_batch", fake_batch)
        monkeypatch.setattr(dw, "_fetch_vuln_detail", fake_detail)
        pkgs = [
            {"name": "react", "version": "18.0.0", "ecosystem": "npm"},
            {"name": "lodash", "version": "4.0.0", "ecosystem": "npm"},
        ]
        findings = self._run(dw.scan_packages(pkgs))
        assert len(findings) == 3
        ids = {f["vuln_id"] for f in findings}
        assert ids == {"GHSA-aaaa", "GHSA-bbbb", "GHSA-cccc"}

    def test_dedupes_vuln_ids_across_packages(self, monkeypatch):
        async def fake_batch(packages):
            return [[{"id": "GHSA-shared"}]] * len(packages)

        async def fake_detail(vid):
            return {}

        monkeypatch.setattr(dw, "_query_osv_batch", fake_batch)
        monkeypatch.setattr(dw, "_fetch_vuln_detail", fake_detail)
        pkgs = [
            {"name": "a", "version": "1", "ecosystem": "npm"},
            {"name": "b", "version": "2", "ecosystem": "npm"},
        ]
        findings = self._run(dw.scan_packages(pkgs))
        assert len(findings) == 1

    def test_batch_failure_does_not_abort(self, monkeypatch):
        calls = {"count": 0}

        async def fake_batch(packages):
            calls["count"] += 1
            if calls["count"] == 1:
                raise RuntimeError("network down")
            return [[{"id": "GHSA-good"}]] * len(packages)

        async def fake_detail(vid):
            return {}

        monkeypatch.setattr(dw, "_query_osv_batch", fake_batch)
        monkeypatch.setattr(dw, "_fetch_vuln_detail", fake_detail)
        monkeypatch.setattr(dw, "_BATCH_SIZE", 1)
        pkgs = [
            {"name": "a", "version": "1", "ecosystem": "npm"},
            {"name": "b", "version": "2", "ecosystem": "npm"},
        ]
        findings = self._run(dw.scan_packages(pkgs))
        assert len(findings) == 1
        assert findings[0]["package"] == "b"

    def test_sort_by_severity_desc(self, monkeypatch):
        async def fake_batch(packages):
            return [[{"id": "GHSA-low"}], [{"id": "GHSA-crit"}]]

        async def fake_detail(vid):
            sev = "CRITICAL" if "crit" in vid else "LOW"
            return {"database_specific": {"severity": sev}}

        monkeypatch.setattr(dw, "_query_osv_batch", fake_batch)
        monkeypatch.setattr(dw, "_fetch_vuln_detail", fake_detail)
        pkgs = [
            {"name": "low-pkg", "version": "1", "ecosystem": "npm"},
            {"name": "crit-pkg", "version": "1", "ecosystem": "npm"},
        ]
        findings = self._run(dw.scan_packages(pkgs))
        assert findings[0]["severity"] == "CRITICAL"
        assert findings[-1]["severity"] == "LOW"
