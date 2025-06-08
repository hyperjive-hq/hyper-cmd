"""Plugin loader with filesystem-based discovery.

This module provides functionality to discover and load plugins from the filesystem.
Plugins are Python packages that follow a specific structure and can extend
Hyper applications with new commands, widgets, and other components.

Plugin Structure:
    my_plugin/
        __init__.py      # Required: Makes it a Python package
        plugin.py        # Required: Main plugin module
        plugin.yaml      # Optional: Plugin metadata (can be .yml or .json)

Example Plugin:
    # my_plugin/plugin.py
    PLUGIN_NAME = "my_plugin"
    PLUGIN_VERSION = "1.0.0"
    PLUGIN_DESCRIPTION = "My awesome plugin"

    from hyper_core.commands import BaseCommand

    class MyCommand(BaseCommand):
        @property
        def name(self):
            return "my-command"

        def execute(self):
            self.print_success("Hello from my plugin!")
            return 0
"""

import importlib.util
import json
import logging
import sys
from pathlib import Path
from typing import Any, Optional

import yaml

from ..config import get_config

logger = logging.getLogger(__name__)


class PluginDiscovery:
    """Discovers plugins from filesystem locations.

    This class handles the discovery of plugins by scanning directories
    for valid plugin packages. A valid plugin must have:
    - An __init__.py file (Python package requirement)
    - A plugin.py file (main plugin module)
    - Optionally, a plugin manifest (YAML or JSON)
    """

    # Supported manifest file names in order of preference
    MANIFEST_NAMES = ["plugin.yaml", "plugin.yml", "plugin.json"]

    def __init__(self, base_path: str):
        """Initialize plugin discovery with a base search path.

        Args:
            base_path: Directory to search for plugins
        """
        self.base_path = Path(base_path)

    def discover(self) -> list[Path]:
        """Discover all plugins in the base path.

        Returns:
            List of paths to valid plugin directories
        """
        if not self._is_valid_search_path():
            return []

        plugins = []
        for entry in self.base_path.iterdir():
            if self._is_potential_plugin(entry) and self._is_valid_plugin(entry):
                plugins.append(entry)
                logger.debug(f"Discovered plugin: {entry.name}")

        return plugins

    def _is_valid_search_path(self) -> bool:
        """Check if the base path is valid for searching."""
        return self.base_path.exists() and self.base_path.is_dir()

    def _is_potential_plugin(self, path: Path) -> bool:
        """Check if a path could potentially be a plugin."""
        return (
            path.is_dir()
            and not path.name.startswith(".")  # Skip hidden directories
            and not path.name.startswith("_")  # Skip private directories
        )

    @staticmethod
    def _is_valid_plugin(path: Path) -> bool:
        """Validate that a directory contains a valid plugin.

        Args:
            path: Directory to check

        Returns:
            True if the directory contains a valid plugin structure
        """
        return (path / "__init__.py").exists() and (  # Must be a Python package
            path / "plugin.py"
        ).exists()  # Must have main plugin module

    @staticmethod
    def discover_from_path(path: Path) -> list[tuple[str, Path]]:
        """Discover plugins from a given path (static method for registry).

        Args:
            path: Directory to search for plugins

        Returns:
            List of (plugin_name, plugin_path) tuples
        """
        discovery = PluginDiscovery(str(path))
        return [(p.name, p) for p in discovery.discover()]

    @staticmethod
    def load_manifest(plugin_path: Path) -> Optional[dict[str, Any]]:
        """Load plugin metadata from a manifest file.

        Tries to load plugin metadata from YAML or JSON manifest files.
        Falls back gracefully if no manifest is found.

        Args:
            plugin_path: Path to the plugin directory

        Returns:
            Dictionary containing plugin metadata, or None if no manifest found
        """
        # Try each supported manifest format
        for manifest_name in PluginDiscovery.MANIFEST_NAMES:
            manifest_path = plugin_path / manifest_name
            if manifest_path.exists():
                try:
                    return PluginDiscovery._load_manifest_file(manifest_path)
                except Exception as e:
                    logger.warning(f"Failed to load manifest {manifest_path}: {e}")

        return None

    @staticmethod
    def _load_manifest_file(manifest_path: Path) -> dict[str, Any]:
        """Load a specific manifest file."""
        with open(manifest_path, encoding="utf-8") as f:
            if manifest_path.suffix == ".json":
                return json.load(f)
            else:  # YAML files (.yaml, .yml)
                return yaml.safe_load(f)


class PluginLoader:
    """Handles the loading and initialization of plugins.

    This class is responsible for:
    - Loading plugin modules into Python's module system
    - Extracting plugin metadata from modules and manifests
    - Managing the plugin namespace (hyper_plugins.*)
    """

    def __init__(self):
        """Initialize the plugin loader."""
        self._loaded_plugins = []
        self._search_paths = self._get_default_search_paths()

    def _get_default_search_paths(self) -> list[Path]:
        """Get default plugin search paths including .hyper directory."""
        paths = []

        # Get .hyper/plugins if it exists - only use the first .hyper directory found
        config = get_config()
        if config.has_hyper_directory():
            hyper_plugins = config.get_plugins_directory()
            if hyper_plugins:
                paths.append(hyper_plugins)
                logger.debug(f"Added .hyper/plugins search path: {hyper_plugins}")
                # Return early - only use the first .hyper directory found
                return paths

        # Add traditional search paths only if no .hyper directory found
        paths.extend(
            [
                Path.cwd() / "plugins",  # ./plugins
                Path.home() / ".hyper" / "plugins",  # ~/.hyper/plugins (global)
            ]
        )

        return paths

    def add_search_path(self, path: str) -> None:
        """Add a directory to search for plugins."""
        self._search_paths.append(Path(path))

    def discover_plugins(self) -> None:
        """Discover and load plugins from all search paths."""
        # Clear previously loaded plugins to ensure replacement
        self._loaded_plugins.clear()

        for search_path in self._search_paths:
            if search_path.exists() and search_path.is_dir():
                discovery = PluginDiscovery(str(search_path))
                for plugin_path in discovery.discover():
                    plugin_info = self.load_plugin(str(plugin_path))
                    if plugin_info:
                        self._loaded_plugins.append(plugin_info)

    def get_loaded_plugins(self) -> list[Any]:
        """Get all loaded plugin modules."""
        return [plugin.get("module") for plugin in self._loaded_plugins if plugin.get("module")]

    def load_plugin(self, plugin_path: str) -> Optional[dict[str, Any]]:
        """Load a plugin from a directory path.

        Args:
            plugin_path: Path to the plugin directory

        Returns:
            Dictionary containing plugin information, or None if loading failed
        """
        plugin_dir = Path(plugin_path)
        plugin_name = plugin_dir.name

        # Load the plugin module
        module = self._load_plugin_module(plugin_dir, plugin_name)
        if not module:
            return None

        # Load optional manifest
        manifest = PluginDiscovery.load_manifest(plugin_dir)

        # Extract and merge plugin information
        plugin_info = self._extract_plugin_info(module, manifest)
        plugin_info["module"] = module  # Store the module reference

        # Ensure module is registered in sys.modules
        self._register_module(plugin_name, module)

        return plugin_info

    def _load_plugin_module(self, plugin_dir: Path, plugin_name: str) -> Optional[Any]:
        """Load the plugin.py module from a plugin directory."""
        plugin_file = plugin_dir / "plugin.py"
        if not plugin_file.exists():
            logger.error(f"Plugin file not found: {plugin_file}")
            return None

        try:
            # Create module spec with proper namespacing
            module_name = f"hyper_plugins.{plugin_name}"
            spec = importlib.util.spec_from_file_location(module_name, plugin_file)

            if not spec or not spec.loader:
                logger.error(f"Failed to create module spec for {plugin_file}")
                return None

            # Load and execute the module
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            return module

        except Exception as e:
            logger.error(f"Failed to load plugin from {plugin_file}: {e}")
            return None

    def _extract_plugin_info(
        self, module: Any, manifest: Optional[dict[str, Any]]
    ) -> dict[str, Any]:
        """Extract plugin information from module and manifest.

        Module attributes take precedence over manifest values.
        """
        # Start with defaults
        info = {
            "name": getattr(module, "PLUGIN_NAME", module.__name__.split(".")[-1]),
            "version": getattr(module, "PLUGIN_VERSION", "0.0.1"),
            "description": getattr(module, "PLUGIN_DESCRIPTION", ""),
            "author": getattr(module, "PLUGIN_AUTHOR", ""),
            "dependencies": getattr(module, "PLUGIN_DEPENDENCIES", []),
        }

        # Override with manifest values if present
        if manifest:
            info.update(manifest)

        return info

    def _register_module(self, plugin_name: str, module: Any) -> None:
        """Register the plugin module in sys.modules."""
        module_name = f"hyper_plugins.{plugin_name}"
        if module_name not in sys.modules:
            sys.modules[module_name] = module

    @staticmethod
    def load_plugin_module(plugin_path: Path, plugin_name: str) -> Optional[Any]:
        """Static method for loading a plugin module (used by registry)."""
        loader = PluginLoader()
        return loader._load_plugin_module(plugin_path, plugin_name)

    @staticmethod
    def extract_plugin_info(
        module: Any, manifest: Optional[dict[str, Any]] = None
    ) -> dict[str, Any]:
        """Static method for extracting plugin info (used by registry)."""
        loader = PluginLoader()
        return loader._extract_plugin_info(module, manifest)
