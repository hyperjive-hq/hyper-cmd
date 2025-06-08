"""Tests for the CLI module."""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from hyper_core.cli import discover_commands, main
from hyper_core.commands.base import BaseCommand


class TestCommandForCLI(BaseCommand):
    """Test command for CLI testing."""

    @property
    def name(self) -> str:
        return "test"

    @property
    def description(self) -> str:
        return "Test command"

    def execute(self) -> int:
        self.print_success("Test command executed!")
        return 0


class TestCLI:
    """Test suite for CLI functionality."""

    def setup_method(self):
        """Set up test environment."""
        self.runner = CliRunner()

    def test_cli_main_without_commands(self):
        """Test CLI main function without any commands."""
        with patch("hyper_core.cli.discover_commands") as mock_discover:
            mock_registry = MagicMock()
            mock_registry.list_commands.return_value = []
            mock_discover.return_value = mock_registry

            result = self.runner.invoke(main, [])

            assert result.exit_code == 0
            assert "Hyper CLI" in result.output
            assert "No commands found" in result.output

    def test_cli_main_with_commands(self):
        """Test CLI main function with discovered commands."""
        with patch("hyper_core.cli.discover_commands") as mock_discover:
            mock_registry = MagicMock()
            mock_registry.list_commands.return_value = ["test"]
            mock_registry.get.return_value = TestCommandForCLI
            mock_discover.return_value = mock_registry

            result = self.runner.invoke(main, [])

            assert result.exit_code == 0
            assert "Hyper CLI" in result.output
            assert "test" in result.output

    def test_cli_ui_flag(self):
        """Test CLI with --ui flag."""
        with patch("hyper_core.cli.launch_ui") as mock_launch_ui:
            result = self.runner.invoke(main, ["--ui"])

            assert result.exit_code == 0
            mock_launch_ui.assert_called_once()

    def test_discover_commands(self):
        """Test command discovery functionality."""
        registry = discover_commands()

        # Should return a CommandRegistry, not PluginRegistry
        from hyper_core.commands.registry import CommandRegistry

        assert isinstance(registry, CommandRegistry)
        assert hasattr(registry, "list_commands")

    def test_discover_commands_with_plugin(self):
        """Test command discovery with plugins."""
        with tempfile.TemporaryDirectory() as temp_dir:
            plugin_dir = Path(temp_dir) / "test_plugin"
            plugin_dir.mkdir()

            # Create __init__.py
            (plugin_dir / "__init__.py").write_text("")

            # Create plugin.py
            plugin_content = '''
"""Test plugin."""

PLUGIN_NAME = "test_plugin"
PLUGIN_VERSION = "1.0.0"

from hyper_core.commands.base import BaseCommand

class TestPluginCommand(BaseCommand):
    @property
    def name(self):
        return "test-plugin"

    @property
    def description(self):
        return "Test plugin command"

    def execute(self):
        return 0

def register_commands(registry):
    """Register commands with the registry."""
    registry.register(TestPluginCommand)
'''
            (plugin_dir / "plugin.py").write_text(plugin_content)

            # Test discovery with custom plugin path
            from hyper_core.commands.registry import CommandRegistry

            registry = discover_commands()
            # Should work without errors even if no plugins found
            assert isinstance(registry, CommandRegistry)


class TestCLIIntegration:
    """Integration tests for CLI with actual plugin system."""

    def test_cli_with_registered_commands(self):
        """Test CLI integration with registered commands."""
        runner = CliRunner()

        # Register a test command directly
        from hyper_core.commands.registry import CommandRegistry

        registry = CommandRegistry()
        registry.register(TestCommandForCLI)

        # Mock the discover_commands to return our test registry
        with patch("hyper_core.cli.discover_commands", return_value=registry):
            result = runner.invoke(main, [])

            assert result.exit_code == 0
            assert "test" in result.output

    def test_cli_help_messages(self):
        """Test CLI help messages."""
        runner = CliRunner()

        result = runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "Hyper framework CLI tool" in result.output
        assert "--ui" in result.output

    def test_cli_error_handling(self):
        """Test CLI error handling."""
        # Test that CLI handles launch_ui properly
        with patch("hyper_core.cli.launch_ui") as mock_launch_ui:
            runner = CliRunner()
            result = runner.invoke(main, ["--ui"])

            # Should call launch_ui
            assert result.exit_code == 0
            mock_launch_ui.assert_called_once()


class TestLaunchUI:
    """Test UI launching functionality."""

    def test_launch_ui_import_error(self):
        """Test UI launch with missing dependencies."""
        from hyper_core.cli import launch_ui

        # Mock the import to fail inside the try block
        with patch(
            "hyper_core.ui.framework.NCursesFramework", side_effect=ImportError("No ncurses")
        ):
            with pytest.raises(SystemExit):
                launch_ui()

    def test_launch_ui_success(self):
        """Test successful UI launch."""
        from hyper_core.cli import launch_ui

        # Mock the framework and its methods
        mock_framework = MagicMock()

        with patch("hyper_core.ui.framework.NCursesFramework", return_value=mock_framework):
            with patch("hyper_core.ui.framework.LayoutConfig"):
                with patch("hyper_core.ui.framework.MenuItem"):
                    # Should not raise any errors
                    launch_ui()

                    # Verify framework was configured and run
                    mock_framework.add_menu_item.assert_called()
                    mock_framework.run.assert_called_once()
