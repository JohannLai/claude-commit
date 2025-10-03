#!/usr/bin/env python3
"""
Configuration management for claude-commit
Handles user aliases and preferences
"""

import json
from pathlib import Path
from typing import Dict, Optional


class Config:
    """Manages configuration and aliases for claude-commit"""

    def __init__(self, config_path: Optional[Path] = None):
        """Initialize config manager

        Args:
            config_path: Path to config file. Defaults to ~/.claude-commit/config.json
        """
        if config_path is None:
            config_path = Path.home() / ".claude-commit" / "config.json"

        self.config_path = config_path
        self._config = self._load_config()

    def _load_config(self) -> dict:
        """Load configuration from file"""
        if not self.config_path.exists():
            return {"aliases": self._default_aliases()}

        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
                # Ensure aliases key exists
                if "aliases" not in config:
                    config["aliases"] = self._default_aliases()
                return config
        except Exception:
            return {"aliases": self._default_aliases()}

    def _save_config(self):
        """Save configuration to file"""
        # Ensure directory exists
        self.config_path.parent.mkdir(parents=True, exist_ok=True)

        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(self._config, f, indent=2, ensure_ascii=False)

    def _default_aliases(self) -> Dict[str, str]:
        """Get default command aliases (like git aliases)"""
        return {
            "cc": "",  # just claude-commit
            "cca": "--all",  # analyze all changes
            "ccv": "--verbose",  # verbose mode
            "ccc": "--commit",  # auto-commit
            "ccp": "--preview",  # preview only
            "ccac": "--all --commit",  # all changes + commit
            "ccav": "--all --verbose",  # all changes + verbose
            "ccvc": "--verbose --commit",  # verbose + commit
            "ccopy": "--copy",  # copy to clipboard
        }

    @property
    def aliases(self) -> Dict[str, str]:
        """Get all aliases"""
        return self._config.get("aliases", {})

    def get_alias(self, alias: str) -> Optional[str]:
        """Get command for an alias

        Args:
            alias: The alias name

        Returns:
            Command string or None if alias doesn't exist
        """
        return self.aliases.get(alias)

    def set_alias(self, alias: str, command: str):
        """Set or update an alias

        Args:
            alias: The alias name
            command: The command arguments (without 'claude-commit')
        """
        self._config["aliases"][alias] = command
        self._save_config()

    def delete_alias(self, alias: str) -> bool:
        """Delete an alias

        Args:
            alias: The alias name

        Returns:
            True if alias was deleted, False if it didn't exist
        """
        if alias in self._config["aliases"]:
            del self._config["aliases"][alias]
            self._save_config()
            return True
        return False

    def list_aliases(self) -> Dict[str, str]:
        """List all aliases"""
        return self.aliases.copy()

    def is_first_run(self) -> bool:
        """Check if this is the first run"""
        return not self.config_path.exists()

    def mark_first_run_complete(self):
        """Mark that first run is complete"""
        if not self.config_path.exists():
            self._save_config()


def resolve_alias(args: list) -> list:
    """Resolve alias if first argument is an alias

    Args:
        args: Command line arguments

    Returns:
        Resolved arguments (with alias expanded)
    """
    if not args:
        return args

    config = Config()
    first_arg = args[0]

    # Check if first argument is an alias
    alias_cmd = config.get_alias(first_arg)
    if alias_cmd is not None:
        # Replace alias with its command
        if alias_cmd:
            # Parse the alias command into arguments
            import shlex

            expanded_args = shlex.split(alias_cmd)
            # Combine expanded args with remaining original args
            return expanded_args + args[1:]
        else:
            # Empty alias (just the base command)
            return args[1:]

    return args
