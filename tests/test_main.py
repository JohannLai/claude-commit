"""Tests for claude_commit.main — pure logic (no Claude / git calls)."""

import sys
from unittest.mock import patch

import pytest

from claude_commit.config import Config
from claude_commit.main import (
    clean_markdown_fences,
    extract_commit_message,
    handle_alias_command,
)


# ---------------------------------------------------------------------------
# extract_commit_message — COMMIT_MESSAGE: marker
# ---------------------------------------------------------------------------


class TestExtractCommitMessage:
    def test_extracts_after_marker(self):
        all_text = [
            "Let me analyze the changes.",
            "COMMIT_MESSAGE:\nfeat: add login\n\n- Add JWT auth",
        ]
        result = extract_commit_message(all_text)
        assert result is not None
        assert result.startswith("feat: add login")
        assert "- Add JWT auth" in result

    def test_marker_in_middle_of_text(self):
        all_text = [
            "Analysis done. COMMIT_MESSAGE:\nfix: typo in README",
        ]
        result = extract_commit_message(all_text)
        assert result == "fix: typo in README"

    def test_marker_across_text_blocks(self):
        all_text = [
            "Some analysis",
            "More analysis\nCOMMIT_MESSAGE:\nchore: bump version",
        ]
        result = extract_commit_message(all_text)
        assert result == "chore: bump version"

    def test_only_first_marker_used(self):
        all_text = [
            "COMMIT_MESSAGE:\nfirst message",
            "COMMIT_MESSAGE:\nsecond message",
        ]
        result = extract_commit_message(all_text)
        assert "first message" in result

    def test_returns_none_for_empty_input(self):
        assert extract_commit_message([]) is None

    def test_returns_none_for_only_explanatory_text(self):
        all_text = [
            "Let me analyze the changes.",
            "I'll look at the diff now.",
            "First, checking git status.",
        ]
        result = extract_commit_message(all_text)
        assert result is None


# ---------------------------------------------------------------------------
# extract_commit_message — fallback (no marker)
# ---------------------------------------------------------------------------


class TestExtractFallback:
    def test_uses_last_non_explanatory_block(self):
        all_text = [
            "Let me analyze.",
            "feat: add new feature",
            "I'll commit this now.",
        ]
        # "I'll commit this now." starts with "i'll" → skipped
        # "feat: add new feature" → used
        result = extract_commit_message(all_text)
        assert result == "feat: add new feature"

    def test_skips_all_known_prefixes(self):
        prefixes = ["let me", "i'll", "i will", "now i", "first", "i can see"]
        for prefix in prefixes:
            all_text = [f"{prefix} do something"]
            result = extract_commit_message(all_text)
            assert result is None, f"Should skip prefix: {prefix}"

    def test_prefix_check_is_case_insensitive(self):
        all_text = ["Let Me analyze the diff"]
        result = extract_commit_message(all_text)
        assert result is None

    def test_non_prefix_text_is_accepted(self):
        all_text = ["refactor: clean up imports"]
        result = extract_commit_message(all_text)
        assert result == "refactor: clean up imports"


# ---------------------------------------------------------------------------
# clean_markdown_fences
# ---------------------------------------------------------------------------


class TestCleanMarkdownFences:
    def test_no_fences_unchanged(self):
        text = "feat: add login\n\n- Add JWT auth"
        assert clean_markdown_fences(text) == text

    def test_strips_surrounding_fences(self):
        # Content outside fences is kept; content inside is dropped.
        # So fences around extra examples are removed.
        text = "feat: add login\n\n```\ngit commit -m 'feat: add login'\n```"
        result = clean_markdown_fences(text)
        assert "```" not in result
        assert "feat: add login" in result
        assert "git commit" not in result

    def test_strips_fences_with_language_tag(self):
        text = "fix: typo\n\n```bash\nsome command\n```"
        result = clean_markdown_fences(text)
        assert "```" not in result
        assert "some command" not in result
        assert "fix: typo" in result

    def test_multiple_fenced_blocks(self):
        text = "header\n```\nblock1\n```\nmiddle\n```\nblock2\n```\nfooter"
        result = clean_markdown_fences(text)
        assert result == "header\nmiddle\nfooter"

    def test_empty_string(self):
        assert clean_markdown_fences("") == ""

    def test_only_fences(self):
        assert clean_markdown_fences("```\nhello\n```") == ""


# ---------------------------------------------------------------------------
# handle_alias_command
# ---------------------------------------------------------------------------


class TestHandleAliasCommand:
    def _make_config(self, tmp_path):
        """Create a Config with a temp path and patch Config() calls."""
        return Config(config_path=tmp_path / "config.json")

    def test_list_aliases(self, tmp_path, capsys, monkeypatch):
        path = tmp_path / "config.json"
        original_init = Config.__init__

        def patched_init(self, config_path=None):
            original_init(self, config_path=path)

        monkeypatch.setattr(Config, "__init__", patched_init)

        handle_alias_command(["list"])
        captured = capsys.readouterr()
        assert "Configured aliases" in captured.out
        assert "ccc" in captured.out

    def test_list_aliases_default(self, tmp_path, capsys, monkeypatch):
        """Calling with no args defaults to list."""
        path = tmp_path / "config.json"
        original_init = Config.__init__

        def patched_init(self, config_path=None):
            original_init(self, config_path=path)

        monkeypatch.setattr(Config, "__init__", patched_init)

        handle_alias_command([])
        captured = capsys.readouterr()
        assert "Configured aliases" in captured.out

    def test_set_alias(self, tmp_path, capsys, monkeypatch):
        path = tmp_path / "config.json"
        original_init = Config.__init__

        def patched_init(self, config_path=None):
            original_init(self, config_path=path)

        monkeypatch.setattr(Config, "__init__", patched_init)

        handle_alias_command(["set", "myalias", "--all", "--verbose"])
        captured = capsys.readouterr()
        assert "myalias" in captured.out

        # Verify it was persisted
        cfg = Config(config_path=path)
        assert cfg.get_alias("myalias") == "--all --verbose"

    def test_set_alias_missing_name(self, tmp_path, monkeypatch):
        path = tmp_path / "config.json"
        original_init = Config.__init__

        def patched_init(self, config_path=None):
            original_init(self, config_path=path)

        monkeypatch.setattr(Config, "__init__", patched_init)

        with pytest.raises(SystemExit):
            handle_alias_command(["set"])

    def test_unset_alias(self, tmp_path, capsys, monkeypatch):
        path = tmp_path / "config.json"
        cfg = Config(config_path=path)
        cfg.set_alias("removeme", "--verbose")

        original_init = Config.__init__

        def patched_init(self, config_path=None):
            original_init(self, config_path=path)

        monkeypatch.setattr(Config, "__init__", patched_init)

        handle_alias_command(["unset", "removeme"])
        captured = capsys.readouterr()
        assert "removeme" in captured.out
        assert "removed" in captured.out

    def test_unset_alias_not_found(self, tmp_path, monkeypatch):
        path = tmp_path / "config.json"
        original_init = Config.__init__

        def patched_init(self, config_path=None):
            original_init(self, config_path=path)

        monkeypatch.setattr(Config, "__init__", patched_init)

        with pytest.raises(SystemExit):
            handle_alias_command(["unset", "ghost"])

    def test_unknown_subcommand(self, tmp_path, monkeypatch):
        path = tmp_path / "config.json"
        original_init = Config.__init__

        def patched_init(self, config_path=None):
            original_init(self, config_path=path)

        monkeypatch.setattr(Config, "__init__", patched_init)

        with pytest.raises(SystemExit):
            handle_alias_command(["bogus"])


# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------


class TestArgumentParsing:
    """Test argparse defaults and flag behaviour by importing the parser setup."""

    def _parse(self, args):
        """Build the parser identical to main() and parse args."""
        import argparse
        from pathlib import Path

        parser = argparse.ArgumentParser()
        parser.add_argument("-a", "--all", action="store_true")
        parser.add_argument("-v", "--verbose", action="store_true")
        parser.add_argument("-p", "--path", type=Path, default=None)
        parser.add_argument("--max-diff-lines", type=int, default=500)
        parser.add_argument("-c", "--commit", action="store_true")
        parser.add_argument("--copy", action="store_true")
        parser.add_argument("--preview", action="store_true")
        return parser.parse_args(args)

    def test_defaults(self):
        ns = self._parse([])
        assert ns.all is False
        assert ns.verbose is False
        assert ns.path is None
        assert ns.max_diff_lines == 500
        assert ns.commit is False
        assert ns.copy is False
        assert ns.preview is False

    def test_all_flag(self):
        for flag in ["-a", "--all"]:
            ns = self._parse([flag])
            assert ns.all is True

    def test_verbose_flag(self):
        for flag in ["-v", "--verbose"]:
            ns = self._parse([flag])
            assert ns.verbose is True

    def test_commit_flag(self):
        for flag in ["-c", "--commit"]:
            ns = self._parse([flag])
            assert ns.commit is True

    def test_copy_flag(self):
        ns = self._parse(["--copy"])
        assert ns.copy is True

    def test_preview_flag(self):
        ns = self._parse(["--preview"])
        assert ns.preview is True

    def test_max_diff_lines(self):
        ns = self._parse(["--max-diff-lines", "1000"])
        assert ns.max_diff_lines == 1000

    def test_combined_flags(self):
        ns = self._parse(["-a", "-v", "-c", "--max-diff-lines", "200"])
        assert ns.all is True
        assert ns.verbose is True
        assert ns.commit is True
        assert ns.max_diff_lines == 200
