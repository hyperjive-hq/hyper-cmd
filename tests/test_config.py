"""Tests for Hyper Core configuration system."""

from unittest import mock

import pytest
import yaml

from hyper_core.config import HyperConfig, find_hyper_directory, get_config, reset_config


class TestHyperConfig:
    """Test HyperConfig class functionality."""

    def setup_method(self):
        """Reset global config before each test."""
        reset_config()

    def test_no_hyper_directory_found(self, tmp_path):
        """Test behavior when no .hyper directory exists."""
        config = HyperConfig(tmp_path)

        assert not config.has_hyper_directory()
        assert config.get_hyper_directory() is None
        assert config.get_plugins_directory() is None
        assert config.get_project_root() is None

    def test_hyper_directory_discovery(self, tmp_path):
        """Test .hyper directory discovery walking up from subdirectory."""
        # Create directory structure: tmp_path/.hyper and tmp_path/subdir/deep
        hyper_dir = tmp_path / ".hyper"
        hyper_dir.mkdir()

        deep_dir = tmp_path / "subdir" / "deep"
        deep_dir.mkdir(parents=True)

        # Start search from deep directory
        config = HyperConfig(deep_dir)

        assert config.has_hyper_directory()
        assert config.get_hyper_directory() == hyper_dir
        assert config.get_project_root() == tmp_path

    def test_plugins_directory_access(self, tmp_path):
        """Test plugins directory access and creation."""
        hyper_dir = tmp_path / ".hyper"
        hyper_dir.mkdir()

        config = HyperConfig(tmp_path)

        # Plugins directory doesn't exist yet
        plugins_dir = config.get_plugins_directory()
        assert plugins_dir == hyper_dir / "plugins"
        assert not plugins_dir.exists()

        # Ensure plugins directory creates it
        ensured_dir = config.ensure_plugins_directory()
        assert ensured_dir == plugins_dir
        assert plugins_dir.exists()

    def test_config_file_loading_yaml(self, tmp_path):
        """Test loading YAML config file from .hyper directory."""
        hyper_dir = tmp_path / ".hyper"
        hyper_dir.mkdir()

        config_file = hyper_dir / "config.yaml"
        config_data = {"version": "1.0", "plugins": {"enabled": True}, "ui": {"theme": "dark"}}

        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        config = HyperConfig(tmp_path)

        assert config.get_config_value("version") == "1.0"
        assert config.get_config_value("plugins.enabled") is True
        assert config.get_config_value("ui.theme") == "dark"
        assert config.get_config_value("nonexistent", "default") == "default"

    def test_config_file_loading_json(self, tmp_path):
        """Test loading JSON config file from .hyper directory."""
        hyper_dir = tmp_path / ".hyper"
        hyper_dir.mkdir()

        config_file = hyper_dir / "config.json"
        config_data = {"version": "1.0", "plugins": {"enabled": False}}

        with open(config_file, "w") as f:
            import json

            json.dump(config_data, f)

        config = HyperConfig(tmp_path)

        assert config.get_config_value("version") == "1.0"
        assert config.get_config_value("plugins.enabled") is False

    def test_config_file_priority(self, tmp_path):
        """Test config file priority (config.yaml should be loaded first)."""
        hyper_dir = tmp_path / ".hyper"
        hyper_dir.mkdir()

        # Create multiple config files
        yaml_config = hyper_dir / "config.yaml"
        json_config = hyper_dir / "config.json"

        with open(yaml_config, "w") as f:
            yaml.dump({"source": "yaml"}, f)

        with open(json_config, "w") as f:
            import json

            json.dump({"source": "json"}, f)

        config = HyperConfig(tmp_path)

        # YAML should take priority
        assert config.get_config_value("source") == "yaml"

    def test_create_hyper_directory(self, tmp_path):
        """Test creating a new .hyper directory with default structure."""
        hyper_dir = HyperConfig.create_hyper_directory(tmp_path)

        assert hyper_dir == tmp_path / ".hyper"
        assert hyper_dir.exists()
        assert (hyper_dir / "plugins").exists()
        assert (hyper_dir / "config.yaml").exists()
        assert (hyper_dir / ".gitignore").exists()

        # Verify default config content
        config = HyperConfig(tmp_path)
        assert config.get_config_value("version") == "1.0"
        assert config.get_config_value("plugins.enabled") is True


class TestGlobalConfig:
    """Test global configuration functions."""

    def setup_method(self):
        """Reset global config before each test."""
        reset_config()

    def test_get_config_singleton(self, tmp_path):
        """Test that get_config returns the same instance."""
        # Create .hyper directory
        hyper_dir = tmp_path / ".hyper"
        hyper_dir.mkdir()

        with mock.patch("pathlib.Path.cwd", return_value=tmp_path):
            config1 = get_config()
            config2 = get_config()

            assert config1 is config2
            assert config1.has_hyper_directory()

    def test_reset_config(self, tmp_path):
        """Test resetting global configuration."""
        hyper_dir = tmp_path / ".hyper"
        hyper_dir.mkdir()

        with mock.patch("pathlib.Path.cwd", return_value=tmp_path):
            config1 = get_config()
            assert config1.has_hyper_directory()

            reset_config()

            config2 = get_config()
            assert config2 is not config1
            assert config2.has_hyper_directory()

    def test_find_hyper_directory_function(self, tmp_path):
        """Test standalone find_hyper_directory function."""
        hyper_dir = tmp_path / ".hyper"
        hyper_dir.mkdir()

        deep_dir = tmp_path / "a" / "b" / "c"
        deep_dir.mkdir(parents=True)

        found_dir = find_hyper_directory(deep_dir)
        assert found_dir == hyper_dir


class TestPluginIntegration:
    """Test integration with plugin system."""

    def setup_method(self):
        """Reset global config before each test."""
        reset_config()

    def test_plugin_loader_uses_hyper_plugins(self, tmp_path):
        """Test that PluginLoader includes .hyper/plugins in search paths."""
        from hyper_core.plugins.loader import PluginLoader

        # Create .hyper directory with plugins
        hyper_dir = tmp_path / ".hyper"
        hyper_dir.mkdir()
        plugins_dir = hyper_dir / "plugins"
        plugins_dir.mkdir()

        with mock.patch("pathlib.Path.cwd", return_value=tmp_path):
            reset_config()  # Force reload
            loader = PluginLoader()

            # Check that .hyper/plugins is in search paths
            search_paths = [str(path) for path in loader._search_paths]
            assert str(plugins_dir) in search_paths

    def test_plugin_registry_initialization(self, tmp_path):
        """Test that PluginRegistry initializes with .hyper/plugins."""
        from hyper_core.plugins.registry import PluginRegistry

        # Create .hyper directory
        hyper_dir = tmp_path / ".hyper"
        hyper_dir.mkdir()
        plugins_dir = hyper_dir / "plugins"
        plugins_dir.mkdir()

        with mock.patch("pathlib.Path.cwd", return_value=tmp_path):
            reset_config()  # Force reload
            registry = PluginRegistry()
            registry.initialize()

            # Check that .hyper/plugins is in plugin paths
            plugin_paths = [str(path) for path in registry._plugin_paths]
            assert str(plugins_dir) in plugin_paths


if __name__ == "__main__":
    pytest.main([__file__])
