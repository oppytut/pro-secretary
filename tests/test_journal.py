from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from app import journal


@pytest.fixture
def vault(tmp_path, monkeypatch):
    monkeypatch.setattr(journal, "VAULT_PATH", tmp_path)
    return tmp_path


@pytest.fixture
def jakarta_now():
    return datetime(2026, 5, 31, 14, 30, tzinfo=ZoneInfo("Asia/Jakarta"))


class TestAppendEntryValidation:
    def test_empty_string_rejected(self, vault):
        result = journal.append_entry("")
        assert result == {"status_code": 400, "error": "empty entry"}

    def test_whitespace_only_rejected(self, vault):
        assert journal.append_entry("   \n\t  ")["status_code"] == 400

    def test_oversized_entry_rejected(self, vault):
        result = journal.append_entry("x" * (journal.MAX_ENTRY_LEN + 1))
        assert result["status_code"] == 400
        assert "too long" in result["error"]

    def test_at_max_length_accepted(self, vault, jakarta_now):
        result = journal.append_entry("x" * journal.MAX_ENTRY_LEN, now=jakarta_now)
        assert result["status_code"] == 200
        assert result["chars"] == journal.MAX_ENTRY_LEN

    def test_missing_vault_returns_404(self, monkeypatch, tmp_path):
        monkeypatch.setattr(journal, "VAULT_PATH", tmp_path / "nonexistent")
        result = journal.append_entry("hello")
        assert result["status_code"] == 404


class TestAppendEntryWriting:
    def test_creates_journal_subdir(self, vault, jakarta_now):
        journal.append_entry("first entry", now=jakarta_now)
        assert (vault / "journal").is_dir()

    def test_filename_uses_year_month(self, vault, jakarta_now):
        result = journal.append_entry("hello", now=jakarta_now)
        assert result["file"] == "journal/2026-05.md"

    def test_header_written_on_first_entry(self, vault, jakarta_now):
        journal.append_entry("hello", now=jakarta_now)
        content = (vault / "journal" / "2026-05.md").read_text()
        assert content.startswith("# Journal May 2026\n\n")

    def test_header_not_duplicated_on_second_entry(self, vault, jakarta_now):
        journal.append_entry("first", now=jakarta_now)
        journal.append_entry("second", now=jakarta_now)
        content = (vault / "journal" / "2026-05.md").read_text()
        assert content.count("# Journal May 2026") == 1

    def test_timestamp_block_in_jakarta_tz(self, vault, jakarta_now):
        journal.append_entry("body text", now=jakarta_now)
        content = (vault / "journal" / "2026-05.md").read_text()
        assert "## 2026-05-31 14:30" in content
        assert "body text" in content

    def test_two_entries_appended_separately(self, vault, jakarta_now):
        journal.append_entry("alpha", now=jakarta_now)
        journal.append_entry("beta", now=jakarta_now)
        content = (vault / "journal" / "2026-05.md").read_text()
        assert "alpha" in content
        assert "beta" in content
        assert content.index("alpha") < content.index("beta")

    def test_different_months_different_files(self, vault):
        tz = ZoneInfo("Asia/Jakarta")
        journal.append_entry("may", now=datetime(2026, 5, 15, 10, 0, tzinfo=tz))
        journal.append_entry("june", now=datetime(2026, 6, 15, 10, 0, tzinfo=tz))
        assert (vault / "journal" / "2026-05.md").exists()
        assert (vault / "journal" / "2026-06.md").exists()

    def test_returns_chars_count(self, vault, jakarta_now):
        result = journal.append_entry("hello world", now=jakarta_now)
        assert result["chars"] == len("hello world")

    def test_text_stripped_before_count(self, vault, jakarta_now):
        result = journal.append_entry("  spaced  ", now=jakarta_now)
        assert result["chars"] == len("spaced")

    def test_iso_timestamp_returned(self, vault, jakarta_now):
        result = journal.append_entry("hi", now=jakarta_now)
        assert result["timestamp"].startswith("2026-05-31T14:30")

    def test_naive_datetime_localized(self, vault):
        naive = datetime(2026, 5, 31, 14, 30)
        result = journal.append_entry("hi", now=naive.replace(tzinfo=ZoneInfo("UTC")))
        assert result["status_code"] == 200
