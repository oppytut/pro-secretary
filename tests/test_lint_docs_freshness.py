from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import lint_docs_freshness as ldf


class TestExtractTreeBlock:
    def test_extracts_infra_files(self):
        text = """
├── infra/                 # Shared low-level primitives
│   ├── agent.py           # comment
│   ├── auth.py            # comment
│   └── ssh.py             # comment
└── watchdogs/             # Self-contained
    └── dns.py             # comment
"""
        assert ldf._extract_tree_block(text, "infra") == ["agent.py", "auth.py", "ssh.py"]

    def test_extracts_watchdogs_files(self):
        text = """
└── watchdogs/             # Self-contained
    ├── capacity.py        # comment
    ├── deps.py            # comment
    └── ssl.py             # comment
"""
        assert ldf._extract_tree_block(text, "watchdogs") == ["capacity.py", "deps.py", "ssl.py"]

    def test_returns_empty_when_header_missing(self):
        assert ldf._extract_tree_block("nothing here", "infra") == []


class TestArchCheckDir:
    def test_clean_when_match(self, tmp_path, monkeypatch):
        d = tmp_path / "module"
        d.mkdir()
        (d / "a.py").write_text("")
        (d / "b.py").write_text("")
        (d / "__init__.py").write_text("")
        monkeypatch.setattr(ldf, "ROOT", tmp_path)
        text = """
├── module/         # comment
│   ├── a.py        # comment
│   └── b.py        # comment
"""
        assert ldf._arch_check_dir(text, "module", "module") == []

    def test_flags_missing_in_docs(self, tmp_path, monkeypatch):
        d = tmp_path / "module"
        d.mkdir()
        (d / "a.py").write_text("")
        (d / "b.py").write_text("")
        monkeypatch.setattr(ldf, "ROOT", tmp_path)
        text = """
├── module/         # comment
│   └── a.py        # comment
"""
        errors = ldf._arch_check_dir(text, "module", "module")
        assert any("missing in docs" in e and "b.py" in e for e in errors)

    def test_flags_extra_in_docs(self, tmp_path, monkeypatch):
        d = tmp_path / "module"
        d.mkdir()
        (d / "a.py").write_text("")
        monkeypatch.setattr(ldf, "ROOT", tmp_path)
        text = """
├── module/         # comment
│   ├── a.py        # comment
│   └── ghost.py    # comment
"""
        errors = ldf._arch_check_dir(text, "module", "module")
        assert any("extra in docs" in e and "ghost.py" in e for e in errors)


class TestReadmeCheckFeatureCount:
    def test_clean_when_count_matches(self):
        text = """
> 3 features shipped.

### Shipped Features

| # | Feature | Trigger | Command |
|---|---|---|---|
| 1 | Foo | trigger | /foo |
| 2 | Bar | trigger | /bar |
| 3 | Baz | trigger | /baz |
"""
        assert ldf._readme_check_feature_count(text) == []

    def test_flags_count_mismatch(self):
        text = """
> 5 features shipped.

### Shipped Features

| # | Feature | Trigger | Command |
|---|---|---|---|
| 1 | Foo | trigger | /foo |
| 2 | Bar | trigger | /bar |
"""
        errors = ldf._readme_check_feature_count(text)
        assert any("declares '5 features shipped' but table has 2 rows" in e for e in errors)

    def test_flags_missing_status_line(self):
        text = """
### Shipped Features

| # | Feature | Trigger | Command |
|---|---|---|---|
| 1 | Foo | trigger | /foo |
"""
        errors = ldf._readme_check_feature_count(text)
        assert any("cannot find" in e for e in errors)

    def test_flags_missing_table(self):
        text = "> 5 features shipped.\n\nNo table here."
        errors = ldf._readme_check_feature_count(text)
        assert any("cannot find Shipped Features table" in e for e in errors)


class TestMain:
    def test_returns_0_when_clean(self, tmp_path, monkeypatch, capsys):
        infra = tmp_path / "telegram-bot" / "infra"
        wd = tmp_path / "telegram-bot" / "watchdogs"
        infra.mkdir(parents=True)
        wd.mkdir(parents=True)
        (infra / "a.py").write_text("")
        (wd / "x.py").write_text("")

        arch = tmp_path / "ARCHITECTURE.md"
        arch.write_text("""
├── infra/         # comment
│   └── a.py       # comment
└── watchdogs/     # comment
    └── x.py       # comment
""")
        readme = tmp_path / "README.md"
        readme.write_text("""
> 1 features shipped.

### Shipped Features

| # | Feature | Trigger | Command |
|---|---|---|---|
| 1 | Foo | trigger | /foo |
""")
        monkeypatch.setattr(ldf, "ROOT", tmp_path)
        rc = ldf.main()
        assert rc == 0

    def test_returns_1_when_missing_arch(self, tmp_path, monkeypatch):
        monkeypatch.setattr(ldf, "ROOT", tmp_path)
        rc = ldf.main()
        assert rc == 1

    def test_returns_1_when_missing_readme(self, tmp_path, monkeypatch):
        (tmp_path / "ARCHITECTURE.md").write_text("ok")
        monkeypatch.setattr(ldf, "ROOT", tmp_path)
        rc = ldf.main()
        assert rc == 1

    def test_returns_1_when_drift(self, tmp_path, monkeypatch):
        infra = tmp_path / "telegram-bot" / "infra"
        infra.mkdir(parents=True)
        (infra / "a.py").write_text("")
        (infra / "b.py").write_text("")

        (tmp_path / "telegram-bot" / "watchdogs").mkdir()
        (tmp_path / "telegram-bot" / "watchdogs" / "x.py").write_text("")

        arch = tmp_path / "ARCHITECTURE.md"
        arch.write_text("""
├── infra/         # comment
│   └── a.py       # comment
└── watchdogs/     # comment
    └── x.py       # comment
""")
        readme = tmp_path / "README.md"
        readme.write_text("""
> 1 features shipped.

### Shipped Features

| # | Feature | Trigger | Command |
|---|---|---|---|
| 1 | Foo | trigger | /foo |
""")
        monkeypatch.setattr(ldf, "ROOT", tmp_path)
        rc = ldf.main()
        assert rc == 1
