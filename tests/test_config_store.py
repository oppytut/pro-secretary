from __future__ import annotations

from infra import config_store


class TestConfigStore:
    def test_get_returns_default_when_file_missing(self, tmp_path, monkeypatch):
        monkeypatch.setattr(config_store, "CONFIG_DIR", tmp_path)
        monkeypatch.setattr(config_store, "CONFIG_FILE", tmp_path / "config.json")
        assert config_store.config_get("missing", "default") == "default"
        assert config_store.config_get("missing") is None

    def test_set_then_get_roundtrip(self, tmp_path, monkeypatch):
        monkeypatch.setattr(config_store, "CONFIG_DIR", tmp_path)
        monkeypatch.setattr(config_store, "CONFIG_FILE", tmp_path / "config.json")
        config_store.config_set("foo", "bar")
        assert config_store.config_get("foo") == "bar"

    def test_set_creates_dir_if_missing(self, tmp_path, monkeypatch):
        nested = tmp_path / "nested" / "data"
        monkeypatch.setattr(config_store, "CONFIG_DIR", nested)
        monkeypatch.setattr(config_store, "CONFIG_FILE", nested / "config.json")
        config_store.config_set("k", "v")
        assert (nested / "config.json").exists()

    def test_set_persists_complex_values(self, tmp_path, monkeypatch):
        monkeypatch.setattr(config_store, "CONFIG_DIR", tmp_path)
        monkeypatch.setattr(config_store, "CONFIG_FILE", tmp_path / "config.json")
        config_store.config_set("ssh_targets", {"vps1": {"host": "1.2.3.4", "port": "22"}})
        config_store.config_set("ssl_domains", ["example.com", "test.com"])
        assert config_store.config_get("ssh_targets") == {"vps1": {"host": "1.2.3.4", "port": "22"}}
        assert config_store.config_get("ssl_domains") == ["example.com", "test.com"]

    def test_set_overwrites_existing_key(self, tmp_path, monkeypatch):
        monkeypatch.setattr(config_store, "CONFIG_DIR", tmp_path)
        monkeypatch.setattr(config_store, "CONFIG_FILE", tmp_path / "config.json")
        config_store.config_set("k", "v1")
        config_store.config_set("k", "v2")
        assert config_store.config_get("k") == "v2"

    def test_get_returns_default_for_corrupt_file(self, tmp_path, monkeypatch):
        cf = tmp_path / "config.json"
        cf.write_text("not valid json {{{")
        monkeypatch.setattr(config_store, "CONFIG_DIR", tmp_path)
        monkeypatch.setattr(config_store, "CONFIG_FILE", cf)
        assert config_store.config_get("anything", "fallback") == "fallback"

    def test_set_does_not_lose_other_keys(self, tmp_path, monkeypatch):
        monkeypatch.setattr(config_store, "CONFIG_DIR", tmp_path)
        monkeypatch.setattr(config_store, "CONFIG_FILE", tmp_path / "config.json")
        config_store.config_set("a", 1)
        config_store.config_set("b", 2)
        config_store.config_set("c", 3)
        assert config_store.config_get("a") == 1
        assert config_store.config_get("b") == 2
        assert config_store.config_get("c") == 3
