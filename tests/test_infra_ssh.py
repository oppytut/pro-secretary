from __future__ import annotations

import importlib

from infra import config_store
from infra import ssh as ssh_module


def _reload_ssh(monkeypatch, raw_env: str = ""):
    monkeypatch.setenv("MONITOR_SSH_TARGETS", raw_env)
    return importlib.reload(ssh_module)


class TestSshTargetMerge:
    def test_get_targets_empty_when_nothing_configured(self, tmp_path, monkeypatch):
        monkeypatch.setattr(config_store, "CONFIG_DIR", tmp_path)
        monkeypatch.setattr(config_store, "CONFIG_FILE", tmp_path / "config.json")
        ssh = _reload_ssh(monkeypatch, "")
        assert ssh.get_ssh_targets() == {}

    def test_env_targets_parsed_from_json(self, tmp_path, monkeypatch):
        monkeypatch.setattr(config_store, "CONFIG_DIR", tmp_path)
        monkeypatch.setattr(config_store, "CONFIG_FILE", tmp_path / "config.json")
        ssh = _reload_ssh(monkeypatch, '{"vps1": {"host": "1.2.3.4", "port": "22", "user": "ubuntu"}}')
        targets = ssh.get_ssh_targets()
        assert "vps1" in targets
        assert targets["vps1"]["host"] == "1.2.3.4"

    def test_invalid_env_json_falls_back_to_empty(self, tmp_path, monkeypatch):
        monkeypatch.setattr(config_store, "CONFIG_DIR", tmp_path)
        monkeypatch.setattr(config_store, "CONFIG_FILE", tmp_path / "config.json")
        ssh = _reload_ssh(monkeypatch, "not-json {{{")
        assert ssh.get_ssh_targets() == {}

    def test_config_targets_merged_with_env(self, tmp_path, monkeypatch):
        monkeypatch.setattr(config_store, "CONFIG_DIR", tmp_path)
        monkeypatch.setattr(config_store, "CONFIG_FILE", tmp_path / "config.json")
        ssh = _reload_ssh(monkeypatch, '{"env-vps": {"host": "1.1.1.1", "port": "22", "user": "root"}}')
        config_store.config_set("ssh_targets", {"cfg-vps": {"host": "2.2.2.2", "port": "22", "user": "ubuntu"}})
        targets = ssh.get_ssh_targets()
        assert "env-vps" in targets
        assert "cfg-vps" in targets

    def test_config_target_overrides_env_on_conflict(self, tmp_path, monkeypatch):
        monkeypatch.setattr(config_store, "CONFIG_DIR", tmp_path)
        monkeypatch.setattr(config_store, "CONFIG_FILE", tmp_path / "config.json")
        ssh = _reload_ssh(monkeypatch, '{"shared": {"host": "ENV", "port": "22", "user": "root"}}')
        config_store.config_set("ssh_targets", {"shared": {"host": "CFG", "port": "22", "user": "root"}})
        assert ssh.get_ssh_targets()["shared"]["host"] == "CFG"


class TestAddDelTargets:
    def test_add_persists_target(self, tmp_path, monkeypatch):
        monkeypatch.setattr(config_store, "CONFIG_DIR", tmp_path)
        monkeypatch.setattr(config_store, "CONFIG_FILE", tmp_path / "config.json")
        ssh = _reload_ssh(monkeypatch, "")
        assert ssh.add_ssh_target("v1", "1.2.3.4", "2222", "ubuntu") is True
        assert ssh.get_ssh_targets()["v1"] == {"host": "1.2.3.4", "port": "2222", "user": "ubuntu"}

    def test_add_with_default_port_and_user(self, tmp_path, monkeypatch):
        monkeypatch.setattr(config_store, "CONFIG_DIR", tmp_path)
        monkeypatch.setattr(config_store, "CONFIG_FILE", tmp_path / "config.json")
        ssh = _reload_ssh(monkeypatch, "")
        ssh.add_ssh_target("v1", "1.2.3.4")
        target = ssh.get_ssh_targets()["v1"]
        assert target["port"] == "22"
        assert target["user"] == "root"

    def test_add_overwrites_existing(self, tmp_path, monkeypatch):
        monkeypatch.setattr(config_store, "CONFIG_DIR", tmp_path)
        monkeypatch.setattr(config_store, "CONFIG_FILE", tmp_path / "config.json")
        ssh = _reload_ssh(monkeypatch, "")
        ssh.add_ssh_target("v1", "1.1.1.1")
        ssh.add_ssh_target("v1", "2.2.2.2")
        assert ssh.get_ssh_targets()["v1"]["host"] == "2.2.2.2"

    def test_del_returns_true_for_existing(self, tmp_path, monkeypatch):
        monkeypatch.setattr(config_store, "CONFIG_DIR", tmp_path)
        monkeypatch.setattr(config_store, "CONFIG_FILE", tmp_path / "config.json")
        ssh = _reload_ssh(monkeypatch, "")
        ssh.add_ssh_target("v1", "1.2.3.4")
        assert ssh.del_ssh_target("v1") is True
        assert "v1" not in ssh.get_ssh_targets()

    def test_del_returns_false_for_missing(self, tmp_path, monkeypatch):
        monkeypatch.setattr(config_store, "CONFIG_DIR", tmp_path)
        monkeypatch.setattr(config_store, "CONFIG_FILE", tmp_path / "config.json")
        ssh = _reload_ssh(monkeypatch, "")
        assert ssh.del_ssh_target("missing") is False

    def test_del_does_not_remove_env_only_target(self, tmp_path, monkeypatch):
        monkeypatch.setattr(config_store, "CONFIG_DIR", tmp_path)
        monkeypatch.setattr(config_store, "CONFIG_FILE", tmp_path / "config.json")
        ssh = _reload_ssh(monkeypatch, '{"env-only": {"host": "1.1.1.1", "port": "22", "user": "root"}}')
        assert ssh.del_ssh_target("env-only") is False
        assert "env-only" in ssh.get_ssh_targets()
