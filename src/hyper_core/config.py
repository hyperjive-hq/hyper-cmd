"""Configuration management for Hyper Core framework.

This module provides functionality to discover .hyper directories and manage
configuration files within them, similar to how Git uses .git directories.
"""

import json
import logging
from pathlib import Path
from typing import Any, Optional, Union

import yaml

logger = logging.getLogger(__name__)


class HyperConfig:
    """Configuration manager for Hyper Core framework.

    Discovers .hyper directories by walking up from the current working directory
    and manages configuration within them.
    """

    # Supported config file names within .hyper directory
    CONFIG_NAMES = ["config.yaml", "config.yml", "config.json", "config"]

    def __init__(self, start_path: Optional[Union[str, Path]] = None):
        """Initialize configuration manager.

        Args:
            start_path: Path to start searching for .hyper directory.
                       If None, starts from current working directory.
        """
        self.hyper_dir: Optional[Path] = None
        self.config_file: Optional[Path] = None
        self.config_data: dict[str, Any] = {}

        start = Path(start_path) if start_path else Path.cwd()
        self._discover_hyper_directory(start)

        if self.hyper_dir:
            self._load_config()

    def _discover_hyper_directory(self, start_path: Path) -> None:
        """Discover .hyper directory by walking up from start_path.

        Args:
            start_path: Directory to start searching from
        """
        current = start_path.resolve()

        # Walk up the directory tree
        for path in [current] + list(current.parents):
            hyper_dir = path / ".hyper"
            if hyper_dir.exists() and hyper_dir.is_dir():
                self.hyper_dir = hyper_dir
                logger.info(f"Found .hyper directory: {hyper_dir}")
                return

        logger.debug("No .hyper directory found")

    def _load_config(self) -> None:
        """Load configuration file from .hyper directory."""
        if not self.hyper_dir:
            return

        # Try each config file name
        for config_name in self.CONFIG_NAMES:
            config_path = self.hyper_dir / config_name
            if config_path.exists() and config_path.is_file():
                self._load_config_file(config_path)
                return

        logger.debug(f"No config file found in {self.hyper_dir}")

    def _load_config_file(self, config_path: Path) -> None:
        """Load and parse a specific config file.

        Args:
            config_path: Path to the config file
        """
        try:
            self.config_file = config_path

            with open(config_path, encoding="utf-8") as f:
                if config_path.suffix in [".yaml", ".yml"]:
                    self.config_data = yaml.safe_load(f) or {}
                elif config_path.suffix == ".json":
                    self.config_data = json.load(f)
                else:
                    # Default to YAML for files without extension
                    self.config_data = yaml.safe_load(f) or {}

            logger.info(f"Loaded config from: {config_path}")

        except Exception as e:
            logger.error(f"Failed to load config from {config_path}: {e}")
            self.config_data = {}

    def has_hyper_directory(self) -> bool:
        """Check if a .hyper directory was found.

        Returns:
            True if .hyper directory exists, False otherwise
        """
        return self.hyper_dir is not None

    def get_hyper_directory(self) -> Optional[Path]:
        """Get the path to the .hyper directory.

        Returns:
            Path to .hyper directory or None if not found
        """
        return self.hyper_dir

    def get_plugins_directory(self) -> Optional[Path]:
        """Get the plugins directory within .hyper.

        Returns:
            Path to .hyper/plugins directory or None if .hyper not found
        """
        if self.hyper_dir:
            return self.hyper_dir / "plugins"
        return None

    def ensure_plugins_directory(self) -> Optional[Path]:
        """Ensure the plugins directory exists within .hyper.

        Returns:
            Path to .hyper/plugins directory or None if .hyper not found
        """
        plugins_dir = self.get_plugins_directory()
        if plugins_dir:
            plugins_dir.mkdir(exist_ok=True)
            return plugins_dir
        return None

    def get_config_value(self, key: str, default: Any = None) -> Any:
        """Get a configuration value by key.

        Args:
            key: Configuration key (supports dot notation, e.g., 'ui.theme')
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        keys = key.split(".")
        value = self.config_data

        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default

    def get_project_root(self) -> Optional[Path]:
        """Get the project root directory (parent of .hyper).

        Returns:
            Path to project root or None if .hyper not found
        """
        if self.hyper_dir:
            return self.hyper_dir.parent
        return None

    @classmethod
    def create_hyper_directory(cls, project_root: Path) -> Path:
        """Create a new .hyper directory with default structure.

        Args:
            project_root: Directory to create .hyper directory in

        Returns:
            Path to created .hyper directory
        """
        hyper_dir = project_root / ".hyper"
        hyper_dir.mkdir(exist_ok=True)

        # Create plugins subdirectory
        plugins_dir = hyper_dir / "plugins"
        plugins_dir.mkdir(exist_ok=True)

        # Create default config file
        config_file = hyper_dir / "config.yaml"
        if not config_file.exists():
            default_config = {
                "version": "1.0",
                "plugins": {"enabled": True, "auto_discover": True},
                "ui": {"theme": "default"},
            }

            with open(config_file, "w", encoding="utf-8") as f:
                yaml.dump(default_config, f, default_flow_style=False, indent=2)

        # Create .gitignore for plugins directory if it doesn't exist
        gitignore_file = hyper_dir / ".gitignore"
        if not gitignore_file.exists():
            gitignore_content = """# Hyper Core generated files
*.log
*.cache

# Local plugin development
plugins/*/venv/
plugins/*/.env
"""
            with open(gitignore_file, "w", encoding="utf-8") as f:
                f.write(gitignore_content)

        logger.info(f"Created .hyper directory: {hyper_dir}")
        return hyper_dir


# Global config instance for framework use
_global_config: Optional[HyperConfig] = None


def get_config(start_path: Optional[Union[str, Path]] = None) -> HyperConfig:
    """Get the global configuration instance.

    Args:
        start_path: Optional path to start searching for .hyper directory
                   (only used on first call)

    Returns:
        Global HyperConfig instance
    """
    global _global_config

    if _global_config is None:
        _global_config = HyperConfig(start_path)

    return _global_config


def reset_config() -> None:
    """Reset the global configuration instance.

    Useful for testing or when config needs to be reloaded.
    """
    global _global_config
    _global_config = None


def find_hyper_directory(start_path: Optional[Union[str, Path]] = None) -> Optional[Path]:
    """Find .hyper directory by walking up from start_path.

    Args:
        start_path: Directory to start searching from (defaults to cwd)

    Returns:
        Path to .hyper directory or None if not found
    """
    config = HyperConfig(start_path)
    return config.get_hyper_directory()
