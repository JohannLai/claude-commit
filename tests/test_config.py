"""Tests for claude_commit.config — Config class and resolve_alias."""

import json
from pathlib import Path

import pytest

from claude_commit.config import Config, resolve_alias


# ---------------------------------------------------------------------------
# Config – defaults
# ---------------------------------------------------------------------------


class TestConfigDefaults:
    def test_new_config_has_default_aliases(self, tmp_path):
        cfg = Config(config_path=tmp_path / "config.json")
        aliases = cfg.list_aliases()
        assert "cc" in aliases
        assert "ccc" in aliases
        assert "cca" in aliases

    def test_default_alias_values(self, tmp_path):
        cfg = Config(config_path=tmp_path / "config.json")
        assert cfg.get_alias("cc") == ""
        assert cfg.get_alias("ccc") == "--commit"
        assert cfg.get_alias("cca") == "--all"
        assert cfg.get_alias("ccac") == "--all --commit"


# ---------------------------------------------------------------------------
# Config – set / get / delete / list
# ---------------------------------------------------------------------------


class TestConfigAliasOps:
    def test_set_and_get_alias(self, tmp_path):
        cfg = Config(config_path=tmp_path / "config.json")
        cfg.set_alias("myalias", "--all --verbose")
        assert cfg.get_alias("myalias") == "--all --verbose"

    def test_get_alias_returns_none_for_unknown(self, tmp_path):
        cfg = Config(config_path=tmp_path / "config.json")
        assert cfg.get_alias("nonexistent") is None

    def test_delete_alias_existing(self, tmp_path):
        cfg = Config(config_path=tmp_path / "config.json")
        cfg.set_alias("tmp", "--verbose")
        assert cfg.delete_alias("tmp") is True
        assert cfg.get_alias("tmp") is None

    def test_delete_alias_missing(self, tmp_path):
        cfg = Config(config_path=tmp_path / "config.json")
        assert cfg.delete_alias("does_not_exist") is False

    def test_list_aliases_returns_copy(self, tmp_path):
        cfg = Config(config_path=tmp_path / "config.json")
        aliases = cfg.list_aliases()
        aliases["injected"] = "evil"
        assert cfg.get_alias("injected") is None


# ---------------------------------------------------------------------------
# Config – first run
# ---------------------------------------------------------------------------


class TestConfigFirstRun:
    def test_is_first_run_true_when_no_file(self, tmp_path):
        cfg = Config(config_path=tmp_path / "config.json")
        assert cfg.is_first_run() is True

    def test_is_first_run_false_after_save(self, tmp_path):
        path = tmp_path / "config.json"
        cfg = Config(config_path=path)
        cfg.mark_first_run_complete()
        assert cfg.is_first_run() is False

    def test_mark_first_run_creates_file(self, tmp_path):
        path = tmp_path / "subdir" / "config.json"
        cfg = Config(config_path=path)
        cfg.mark_first_run_complete()
        assert path.exists()

    def test_mark_first_run_idempotent(self, tmp_path):
        path = tmp_path / "config.json"
        cfg = Config(config_path=path)
        cfg.mark_first_run_complete()
        content1 = path.read_text()
        cfg.mark_first_run_complete()  # second call should be a no-op
        content2 = path.read_text()
        assert content1 == content2


# ---------------------------------------------------------------------------
# Config – persistence across instances
# ---------------------------------------------------------------------------


class TestConfigPersistence:
    def test_alias_persists_across_instances(self, tmp_path):
        path = tmp_path / "config.json"
        cfg1 = Config(config_path=path)
        cfg1.set_alias("persist", "--all --commit")

        cfg2 = Config(config_path=path)
        assert cfg2.get_alias("persist") == "--all --commit"

    def test_config_file_is_valid_json(self, tmp_path):
        path = tmp_path / "config.json"
        cfg = Config(config_path=path)
        cfg.set_alias("test", "--verbose")
        data = json.loads(path.read_text())
        assert "aliases" in data
        assert data["aliases"]["test"] == "--verbose"

    def test_corrupt_config_file_returns_defaults(self, tmp_path):
        path = tmp_path / "config.json"
        path.write_text("not valid json!!!")
        cfg = Config(config_path=path)
        # Should fall back to defaults without raising
        assert "cc" in cfg.list_aliases()


# ---------------------------------------------------------------------------
# resolve_alias
# ---------------------------------------------------------------------------


class TestResolveAlias:
    def test_empty_args_returns_empty(self, tmp_path, monkeypatch):
        monkeypatch.setattr(
            "claude_commit.config.Config.__init__",
            lambda self, config_path=None: Config.__init__(
                self, config_path=tmp_path / "config.json"
            ),
        )
        assert resolve_alias([]) == []

    def test_known_alias_expands(self, tmp_path, monkeypatch):
        path = tmp_path / "config.json"
        cfg = Config(config_path=path)
        cfg.set_alias("myalias", "--all --verbose")

        # Patch Config() inside resolve_alias to use our tmp config
        original_init = Config.__init__

        def patched_init(self, config_path=None):
            original_init(self, config_path=path)

        monkeypatch.setattr("claude_commit.config.Config.__init__", patched_init)

        result = resolve_alias(["myalias", "--extra"])
        assert result == ["--all", "--verbose", "--extra"]

    def test_empty_alias_drops_alias_arg(self, tmp_path, monkeypatch):
        path = tmp_path / "config.json"
        cfg = Config(config_path=path)
        cfg.set_alias("bare", "")

        original_init = Config.__init__

        def patched_init(self, config_path=None):
            original_init(self, config_path=path)

        monkeypatch.setattr("claude_commit.config.Config.__init__", patched_init)

        result = resolve_alias(["bare", "--verbose"])
        assert result == ["--verbose"]

    def test_unknown_arg_passes_through(self, tmp_path, monkeypatch):
        path = tmp_path / "config.json"
        original_init = Config.__init__

        def patched_init(self, config_path=None):
            original_init(self, config_path=path)

        monkeypatch.setattr("claude_commit.config.Config.__init__", patched_init)

        result = resolve_alias(["--all", "--verbose"])
        assert result == ["--all", "--verbose"]
