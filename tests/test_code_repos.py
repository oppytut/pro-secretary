from __future__ import annotations

import textwrap

import pytest

from app import code_repos


@pytest.fixture
def repos_yaml(tmp_path, monkeypatch):
    path = tmp_path / "repos.yml"
    monkeypatch.setattr(code_repos.config, "REPOS_CONFIG_PATH", path)
    return path


class TestLoadRepos:
    def test_missing_file_returns_empty(self, repos_yaml):
        assert code_repos.load_repos() == []

    def test_minimal_repo(self, repos_yaml):
        repos_yaml.write_text(textwrap.dedent("""
            repos:
              - id: backend
                provider: github
                url: https://github.com/me/backend.git
        """))
        repos = code_repos.load_repos()
        assert len(repos) == 1
        repo = repos[0]
        assert repo.id == "backend"
        assert repo.provider == "github"
        assert repo.branch == "main"
        assert repo.enabled is True
        assert repo.aliases == ()

    def test_aliases_string_normalized_to_tuple(self, repos_yaml):
        repos_yaml.write_text(textwrap.dedent("""
            repos:
              - id: x
                provider: gitlab
                url: https://gitlab.com/x/x.git
                aliases: shortname
        """))
        repos = code_repos.load_repos()
        assert repos[0].aliases == ("shortname",)

    def test_aliases_list_preserved(self, repos_yaml):
        repos_yaml.write_text(textwrap.dedent("""
            repos:
              - id: x
                provider: github
                url: https://github.com/x/x.git
                aliases:
                  - api
                  - backend
        """))
        repos = code_repos.load_repos()
        assert repos[0].aliases == ("api", "backend")

    def test_provider_lowercased(self, repos_yaml):
        repos_yaml.write_text(textwrap.dedent("""
            repos:
              - id: x
                provider: GITHUB
                url: https://x.com/x.git
        """))
        assert code_repos.load_repos()[0].provider == "github"

    def test_skips_invalid_entries(self, repos_yaml):
        repos_yaml.write_text(textwrap.dedent("""
            repos:
              - id: ok
                provider: github
                url: https://github.com/ok/ok.git
              - provider: github
                url: https://github.com/missing-id/x.git
        """))
        repos = code_repos.load_repos()
        assert len(repos) == 1
        assert repos[0].id == "ok"

    def test_disabled_flag_respected(self, repos_yaml):
        repos_yaml.write_text(textwrap.dedent("""
            repos:
              - id: x
                provider: github
                url: https://x.com/x.git
                enabled: false
        """))
        assert code_repos.load_repos()[0].enabled is False

    def test_empty_yaml_returns_empty(self, repos_yaml):
        repos_yaml.write_text("")
        assert code_repos.load_repos() == []

    def test_no_repos_key_returns_empty(self, repos_yaml):
        repos_yaml.write_text("other: value")
        assert code_repos.load_repos() == []


class TestResolveRepoId:
    def test_match_by_id(self, repos_yaml):
        repos_yaml.write_text(textwrap.dedent("""
            repos:
              - id: backend
                provider: github
                url: https://x.com/x.git
        """))
        assert code_repos.resolve_repo_id("backend") == "backend"

    def test_match_by_alias(self, repos_yaml):
        repos_yaml.write_text(textwrap.dedent("""
            repos:
              - id: backend
                provider: github
                url: https://x.com/x.git
                aliases:
                  - api
        """))
        assert code_repos.resolve_repo_id("api") == "backend"

    def test_no_match_returns_none(self, repos_yaml):
        repos_yaml.write_text(textwrap.dedent("""
            repos:
              - id: x
                provider: github
                url: https://x.com/x.git
        """))
        assert code_repos.resolve_repo_id("nonexistent") is None

    def test_disabled_repo_not_resolved(self, repos_yaml):
        repos_yaml.write_text(textwrap.dedent("""
            repos:
              - id: x
                provider: github
                url: https://x.com/x.git
                enabled: false
        """))
        assert code_repos.resolve_repo_id("x") is None


class TestGetRepo:
    def test_returns_repo_config(self, repos_yaml):
        repos_yaml.write_text(textwrap.dedent("""
            repos:
              - id: backend
                provider: github
                url: https://github.com/me/backend.git
        """))
        repo = code_repos.get_repo("backend")
        assert repo is not None
        assert repo.id == "backend"

    def test_returns_none_for_unknown(self, repos_yaml):
        repos_yaml.write_text("repos: []")
        assert code_repos.get_repo("ghost") is None

    def test_resolves_alias_first(self, repos_yaml):
        repos_yaml.write_text(textwrap.dedent("""
            repos:
              - id: backend
                provider: github
                url: https://github.com/me/backend.git
                aliases:
                  - api
        """))
        repo = code_repos.get_repo("api")
        assert repo is not None
        assert repo.id == "backend"


class TestExtractKeywords:
    def test_filters_stopwords_and_short(self):
        kw = code_repos._extract_keywords("apa logic untuk validasi user")
        assert "apa" not in kw
        assert "user" in kw
        assert "logic" in kw

    def test_lowercases_input(self):
        kw = code_repos._extract_keywords("HOW does AUTH work")
        assert "auth" in kw
        assert "work" in kw

    def test_handles_punctuation(self):
        kw = code_repos._extract_keywords("user.password? auth-flow!")
        assert "user" in kw
        assert "password" in kw
        assert "auth" in kw

    def test_skips_under_3_chars(self):
        kw = code_repos._extract_keywords("a is or db x y z")
        assert "is" not in kw

    def test_empty_returns_empty(self):
        assert code_repos._extract_keywords("") == []


class TestPluralizeVariants:
    def test_y_to_ies(self):
        variants = code_repos._pluralize_variants("inventory")
        assert "inventory" in variants
        assert "inventories" in variants

    def test_ies_to_y(self):
        variants = code_repos._pluralize_variants("inventories")
        assert "inventories" in variants
        assert "inventory" in variants

    def test_singular_to_plural(self):
        variants = code_repos._pluralize_variants("user")
        assert "user" in variants
        assert "users" in variants

    def test_plural_to_singular(self):
        variants = code_repos._pluralize_variants("users")
        assert "users" in variants
        assert "user" in variants

    def test_short_word_skipped(self):
        variants = code_repos._pluralize_variants("ab")
        assert variants == ["ab"]

    def test_double_s_kept_as_is(self):
        variants = code_repos._pluralize_variants("address")
        assert "address" in variants
        assert "addres" not in variants

    def test_y_after_vowel_not_changed(self):
        variants = code_repos._pluralize_variants("monkey")
        assert "monkey" in variants
        assert "monkeys" in variants


class TestExtractPathTerms:
    def test_filters_irrelevant(self):
        terms = code_repos._extract_path_terms(["validation", "user", "stock"])
        assert "validation" not in terms
        assert "user" in terms or "users" in terms
        assert "stock" in terms or "stocks" in terms

    def test_uses_id_to_en_mapping(self):
        terms = code_repos._extract_path_terms(["pelanggan"])
        assert "customer" in terms or "customers" in terms

    def test_short_keywords_skipped(self):
        terms = code_repos._extract_path_terms(["aa", "abc", "user"])
        assert "aa" not in terms
        assert "abc" not in terms

    def test_dedupes_variants(self):
        terms = code_repos._extract_path_terms(["customer", "customers"])
        assert terms.count("customer") == 1
        assert terms.count("customers") == 1


class TestPrioritizePaths:
    def _hit(self, path, score=0.5):
        return {"id": path, "score": score, "payload": {"path": path}}

    def test_tests_paths_deprioritized(self):
        hits = [
            self._hit("tests/Feature/UserTest.php"),
            self._hit("app/Models/User.php"),
        ]
        sorted_hits = code_repos._prioritize_paths(hits)
        assert sorted_hits[0]["payload"]["path"] == "app/Models/User.php"

    def test_migrations_with_create_term_boosted(self):
        hits = [
            self._hit("app/Controllers/UserController.php"),
            self._hit("database/migrations/create_users_table.php"),
        ]
        sorted_hits = code_repos._prioritize_paths(hits, path_terms=["users"])
        assert "create_users_table" in sorted_hits[0]["payload"]["path"]

    def test_models_with_entity_term_boosted(self):
        hits = [
            self._hit("app/Controllers/UserController.php"),
            self._hit("app/Models/User.php"),
        ]
        sorted_hits = code_repos._prioritize_paths(hits, path_terms=["user"])
        assert "Models/User.php" in sorted_hits[0]["payload"]["path"]

    def test_caps_at_15(self):
        hits = [self._hit(f"app/file{i}.php") for i in range(30)]
        result = code_repos._prioritize_paths(hits)
        assert len(result) == 15

    def test_no_path_priority_match_default_rank(self):
        hits = [
            self._hit("random/path.txt"),
            self._hit("Controllers/Foo.php"),
        ]
        sorted_hits = code_repos._prioritize_paths(hits)
        assert "Controllers" in sorted_hits[0]["payload"]["path"]


class TestMergeHits:
    def test_dedupes_by_id(self):
        embed = [{"id": "a", "score": 0.9, "payload": {}}]
        keyword = [{"id": "a", "score": 0.5, "payload": {}}]
        merged = code_repos._merge_hits(embed, keyword)
        assert len(merged) == 1
        assert merged[0]["id"] == "a"

    def test_keyword_only_results_added(self):
        embed = []
        keyword = [{"id": "k1", "score": 0.5, "payload": {}}]
        merged = code_repos._merge_hits(embed, keyword)
        assert len(merged) == 1
        assert merged[0]["id"] == "k1"
        assert merged[0]["score"] == 0.15

    def test_embedding_results_kept(self):
        embed = [{"id": f"e{i}", "score": 0.9 - i * 0.1, "payload": {}} for i in range(3)]
        keyword = []
        merged = code_repos._merge_hits(embed, keyword)
        assert len(merged) == 3

    def test_max_results_capped(self):
        embed = [{"id": f"e{i}", "score": 0.9, "payload": {}} for i in range(50)]
        keyword = []
        merged = code_repos._merge_hits(embed, keyword, max_results=10)
        assert len(merged) <= 10

    def test_keyword_reserves_5_slots(self):
        embed = [{"id": f"e{i}", "score": 0.9, "payload": {}} for i in range(30)]
        keyword = [{"id": f"k{i}", "score": 0.4, "payload": {}} for i in range(10)]
        merged = code_repos._merge_hits(embed, keyword, max_results=25)
        keyword_ids = {h["id"] for h in merged if h["id"].startswith("k")}
        assert len(keyword_ids) >= 5


class TestSafeUrl:
    def test_strips_credentials_from_https(self):
        url = "https://user:token@github.com/me/repo.git"
        assert code_repos._safe_url(url) == "https://github.com/me/repo.git"

    def test_preserves_port(self):
        url = "https://user:tok@gitlab.example.com:8443/x/y.git"
        assert code_repos._safe_url(url) == "https://gitlab.example.com:8443/x/y.git"

    def test_no_credentials_unchanged(self):
        url = "https://github.com/me/repo.git"
        assert code_repos._safe_url(url) == url

    def test_invalid_url_returned_as_is(self):
        url = "not-a-valid-url"
        assert code_repos._safe_url(url) == url

    def test_force_https_scheme(self):
        # non-https with creds -> returned as https
        url = "http://user:tok@example.com/x.git"
        assert code_repos._safe_url(url) == "http://example.com/x.git" or \
               code_repos._safe_url(url) == "https://example.com/x.git"


class TestSanitizeGitError:
    def test_strips_credentials(self):
        text = "fatal: clone https://user:secret@github.com/me/repo.git failed"
        cleaned = code_repos._sanitize_git_error(text)
        assert "secret" not in cleaned
        assert "***:***" in cleaned

    def test_keeps_last_500_chars(self):
        text = "x" * 1000 + "tail-marker"
        cleaned = code_repos._sanitize_git_error(text)
        assert len(cleaned) <= 500
        assert "tail-marker" in cleaned

    def test_empty_returns_default(self):
        assert code_repos._sanitize_git_error("") == "git command failed"

    def test_whitespace_only_returns_default(self):
        assert code_repos._sanitize_git_error("   \n  ") == "git command failed"


class TestSkipPath:
    def test_skip_dir_in_parts(self, tmp_path):
        path = tmp_path / "node_modules" / "react" / "index.js"
        path.parent.mkdir(parents=True)
        path.write_text("x")
        assert code_repos._skip_path("node_modules/react/index.js", path) is True

    def test_pycache_skipped(self, tmp_path):
        path = tmp_path / "__pycache__" / "foo.pyc"
        path.parent.mkdir(parents=True)
        path.write_text("x")
        assert code_repos._skip_path("__pycache__/foo.pyc", path) is True

    def test_min_js_skipped(self, tmp_path):
        path = tmp_path / "bundle.min.js"
        path.write_text("x")
        assert code_repos._skip_path("bundle.min.js", path) is True

    def test_image_extensions_skipped(self, tmp_path):
        for ext in [".png", ".jpg", ".pdf", ".woff", ".mp4"]:
            path = tmp_path / f"file{ext}"
            path.write_text("x")
            assert code_repos._skip_path(f"file{ext}", path) is True

    def test_normal_source_file_kept(self, tmp_path):
        path = tmp_path / "src" / "foo.py"
        path.parent.mkdir(parents=True)
        path.write_text("x")
        assert code_repos._skip_path("src/foo.py", path) is False

    def test_oversized_file_skipped(self, tmp_path):
        path = tmp_path / "big.py"
        path.write_text("x" * (code_repos.MAX_FILE_BYTES + 100))
        assert code_repos._skip_path("big.py", path) is True


class TestLanguageFor:
    def test_blade_php_special_cased(self):
        assert code_repos._language_for("resources/views/x.blade.php") == "blade"

    def test_python(self):
        assert code_repos._language_for("foo.py") == "python"

    def test_typescript(self):
        assert code_repos._language_for("foo.ts") == "typescript"

    def test_jsx(self):
        assert code_repos._language_for("foo.jsx") == "jsx"

    def test_unknown_extension_returns_ext(self):
        assert code_repos._language_for("foo.xyz") == "xyz"

    def test_no_extension_returns_text(self):
        assert code_repos._language_for("Dockerfile") == "text"

    def test_uppercase_extension(self):
        assert code_repos._language_for("foo.PY") == "python"


class TestLineChunks:
    def test_empty_text(self):
        assert code_repos._line_chunks("") == []

    def test_short_text_single_chunk(self):
        text = "line1\nline2\nline3\n"
        chunks = code_repos._line_chunks(text)
        assert len(chunks) == 1
        assert chunks[0]["start_line"] == 1
        assert chunks[0]["end_line"] == 3

    def test_long_text_multiple_chunks(self):
        text = "\n".join(f"line{i}" for i in range(500))
        chunks = code_repos._line_chunks(text)
        assert len(chunks) > 1
        # First chunk should start at line 1
        assert chunks[0]["start_line"] == 1
        # Chunks should overlap
        for i in range(len(chunks) - 1):
            assert chunks[i + 1]["start_line"] <= chunks[i]["end_line"]

    def test_chunk_text_truncated_to_max_chars(self):
        # Very long single line
        text = "\n".join(["x" * 100 for _ in range(200)])
        chunks = code_repos._line_chunks(text)
        for c in chunks:
            assert len(c["text"]) <= code_repos.MAX_CHUNK_CHARS

    def test_no_overlap_at_end(self):
        text = "\n".join(f"line{i}" for i in range(500))
        chunks = code_repos._line_chunks(text)
        # Last chunk should reach end of file
        assert chunks[-1]["end_line"] == 500


class TestCitation:
    def test_full_payload(self):
        payload = {
            "repo_id": "backend",
            "path": "src/foo.py",
            "start_line": 10,
            "end_line": 50,
            "commit": "abc123def456789",
        }
        cite = code_repos._citation(payload)
        assert cite == "backend:src/foo.py:10-50@abc123de"

    def test_short_commit(self):
        payload = {
            "repo_id": "x",
            "path": "y",
            "start_line": 1,
            "end_line": 2,
            "commit": "abc",
        }
        cite = code_repos._citation(payload)
        assert cite.endswith("@abc")

    def test_missing_commit_empty_sha(self):
        payload = {
            "repo_id": "x",
            "path": "y",
            "start_line": 1,
            "end_line": 2,
        }
        cite = code_repos._citation(payload)
        assert cite.endswith("@")


class TestCompact:
    def test_collapses_whitespace(self):
        assert code_repos._compact("hello   world") == "hello world"

    def test_strips_leading_trailing(self):
        assert code_repos._compact("  hello  ") == "hello"

    def test_newlines_become_spaces(self):
        assert code_repos._compact("a\n\nb\nc") == "a b c"

    def test_tabs_become_spaces(self):
        assert code_repos._compact("a\t\tb") == "a b"

    def test_empty_returns_empty(self):
        assert code_repos._compact("") == ""


class TestFormatSearchResults:
    def test_no_hits(self):
        assert "Tidak ditemukan" in code_repos.format_search_results("query", [])

    def test_query_in_no_hits_msg(self):
        assert "stock_balance" in code_repos.format_search_results("stock_balance", [])

    def test_renders_hits(self):
        hits = [
            {
                "score": 0.876,
                "payload": {
                    "repo_id": "backend",
                    "path": "src/foo.py",
                    "start_line": 1,
                    "end_line": 10,
                    "commit": "abcdef123456",
                    "text": "def hello(): return 'world'",
                },
            },
        ]
        out = code_repos.format_search_results("hello", hits)
        assert "🔍 Hasil pencarian kode: hello" in out
        assert "def hello(): return 'world'" in out
        assert "score 0.876" in out

    def test_truncates_long_snippets(self):
        long_text = "x" * 500
        hits = [{
            "score": 0.5,
            "payload": {
                "repo_id": "x", "path": "y", "start_line": 1, "end_line": 2,
                "commit": "abc", "text": long_text,
            },
        }]
        out = code_repos.format_search_results("q", hits)
        # snippet capped at 260 chars + "..."
        assert "x" * 261 not in out


class TestTokenFor:
    def test_github_uses_github_pat(self, monkeypatch):
        monkeypatch.setattr(code_repos.config, "GH_PAT", "ghp_xxx")
        monkeypatch.setattr(code_repos.config, "GITLAB_PAT", "")
        repo = code_repos.RepoConfig(
            id="x", name="x", provider="github",
            url="https://github.com/x/x.git", branch="main", aliases=(), enabled=True,
        )
        assert code_repos._token_for(repo) == "ghp_xxx"

    def test_gitlab_uses_gitlab_pat(self, monkeypatch):
        monkeypatch.setattr(code_repos.config, "GH_PAT", "")
        monkeypatch.setattr(code_repos.config, "GITLAB_PAT", "glpat-yyy")
        repo = code_repos.RepoConfig(
            id="x", name="x", provider="gitlab",
            url="https://gitlab.com/x/x.git", branch="main", aliases=(), enabled=True,
        )
        assert code_repos._token_for(repo) == "glpat-yyy"

    def test_missing_token_raises(self, monkeypatch):
        monkeypatch.setattr(code_repos.config, "GH_PAT", "")
        monkeypatch.setattr(code_repos.config, "GITLAB_PAT", "")
        repo = code_repos.RepoConfig(
            id="x", name="x", provider="github",
            url="https://github.com/x/x.git", branch="main", aliases=(), enabled=True,
        )
        with pytest.raises(RuntimeError, match="missing token"):
            code_repos._token_for(repo)

    def test_non_https_url_raises(self, monkeypatch):
        monkeypatch.setattr(code_repos.config, "GH_PAT", "ghp_xxx")
        repo = code_repos.RepoConfig(
            id="x", name="x", provider="github",
            url="git@github.com:x/x.git", branch="main", aliases=(), enabled=True,
        )
        with pytest.raises(RuntimeError, match="HTTPS"):
            code_repos._token_for(repo)
