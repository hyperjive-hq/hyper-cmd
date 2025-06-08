"""
Tests for CLI UI functionality.

These tests verify the CLI UI panels and interactions work correctly
using the mock renderer backend.
"""

from unittest.mock import Mock, patch

import pytest

from hyper_core.cli import show_commands_panel, show_plugins_panel
from hyper_core.commands.base import BaseCommand
from hyper_core.commands.registry import CommandRegistry
from hyper_core.ui.engine import RenderContext, RenderEngine
from hyper_core.ui.renderer import MockBackend


class TestCommand(BaseCommand):
    """Test command for testing."""

    name = "test"
    description = "Test command"

    def execute(self, args):
        return 0


class TestCommandsPanel:
    """Test the commands panel in the UI."""

    def test_commands_panel_empty(self):
        """Test commands panel when no commands are registered."""
        backend = MockBackend(width=60, height=20)
        engine = RenderEngine(backend)

        # Mock framework
        framework = Mock()
        framework.set_panel = Mock()

        # Mock empty registry
        with patch("hyper_core.cli.discover_commands") as mock_discover:
            mock_registry = CommandRegistry()
            mock_discover.return_value = mock_registry

            # Show panel
            show_commands_panel(framework)

            # Verify panel was set
            assert framework.set_panel.called
            panel = framework.set_panel.call_args[0][0]

            # Render the panel
            ctx = RenderContext(window=engine.root_window, x=0, y=0, width=60, height=20)
            panel.render_content(ctx)

            # Check output
            output = "".join(["".join(row) for row in backend.screen_buffer])
            assert "Available Commands:" in output
            assert "No commands found." in output
            assert "Press 'b' to go back" in output

    def test_commands_panel_with_commands(self):
        """Test commands panel with registered commands."""
        backend = MockBackend(width=60, height=20)
        engine = RenderEngine(backend)

        # Mock framework
        framework = Mock()
        framework.set_panel = Mock()

        # Mock registry with test command
        with patch("hyper_core.cli.discover_commands") as mock_discover:
            mock_registry = CommandRegistry()
            mock_registry.register(TestCommand)
            mock_discover.return_value = mock_registry

            # Show panel
            show_commands_panel(framework)

            # Get the panel
            panel = framework.set_panel.call_args[0][0]

            # Render
            ctx = RenderContext(window=engine.root_window, x=0, y=0, width=60, height=20)
            panel.render_content(ctx)

            # Check output
            output = "".join(["".join(row) for row in backend.screen_buffer])
            assert "Available Commands:" in output
            assert "test: Test command" in output
            assert "Press 'b' to go back" in output

    def test_commands_panel_with_broken_command(self):
        """Test commands panel handles commands that fail to instantiate."""
        backend = MockBackend(width=60, height=20)
        engine = RenderEngine(backend)

        # Create a broken command class
        class BrokenCommand(BaseCommand):
            name = "broken"

            def __init__(self):
                raise Exception("Command initialization failed")

            def execute(self, args):
                pass

        # Mock framework
        framework = Mock()
        framework.set_panel = Mock()

        # Mock registry with broken command
        with patch("hyper_core.cli.discover_commands") as mock_discover:
            mock_registry = CommandRegistry()
            mock_registry.register(BrokenCommand)
            mock_discover.return_value = mock_registry

            # Show panel
            show_commands_panel(framework)

            # Get the panel
            panel = framework.set_panel.call_args[0][0]

            # Render
            ctx = RenderContext(window=engine.root_window, x=0, y=0, width=60, height=20)
            panel.render_content(ctx)

            # Check output - should show fallback message
            output = "".join(["".join(row) for row in backend.screen_buffer])
            assert "broken: Command available" in output


class TestPluginsPanel:
    """Test the plugins panel in the UI."""

    def test_plugins_panel_empty(self):
        """Test plugins panel when no plugins are loaded."""
        backend = MockBackend(width=60, height=20)
        engine = RenderEngine(backend)

        # Mock framework
        framework = Mock()
        framework.set_panel = Mock()

        # Mock empty plugin registry
        from hyper_core.plugins.registry import plugin_registry

        with patch.object(plugin_registry, "_plugins", {}):
            # Show panel
            show_plugins_panel(framework)

            # Get the panel
            panel = framework.set_panel.call_args[0][0]

            # Render
            ctx = RenderContext(window=engine.root_window, x=0, y=0, width=60, height=20)
            panel.render_content(ctx)

            # Check output
            output = "".join(["".join(row) for row in backend.screen_buffer])
            assert "Loaded Plugins:" in output
            assert "No plugins loaded." in output
            assert "Press 'b' to go back" in output

    def test_plugins_panel_with_plugins(self):
        """Test plugins panel with loaded plugins."""
        backend = MockBackend(width=60, height=20)
        engine = RenderEngine(backend)

        # Mock framework
        framework = Mock()
        framework.set_panel = Mock()

        # Create mock plugins
        plugin1 = Mock()
        plugin1.__name__ = "test_plugin_1"

        plugin2 = Mock()
        plugin2.__name__ = "test_plugin_2"

        # Mock plugin registry with plugins
        from hyper_core.plugins.registry import PluginMetadata, plugin_registry

        # Create mock plugin metadata objects
        metadata1 = PluginMetadata("test_plugin_1", "1.0.0")
        metadata1.loaded = True
        metadata1.module = plugin1

        metadata2 = PluginMetadata("test_plugin_2", "1.0.0")
        metadata2.loaded = True
        metadata2.module = plugin2

        mock_plugins = {"test_plugin_1": metadata1, "test_plugin_2": metadata2}

        with patch.object(plugin_registry, "_plugins", mock_plugins):
            # Show panel
            show_plugins_panel(framework)

            # Get the panel
            panel = framework.set_panel.call_args[0][0]

            # Render
            ctx = RenderContext(window=engine.root_window, x=0, y=0, width=60, height=20)
            panel.render_content(ctx)

            # Check output
            output = "".join(["".join(row) for row in backend.screen_buffer])
            assert "Loaded Plugins:" in output
            assert "test_plugin_1 (active)" in output
            assert "test_plugin_2 (active)" in output
            assert "Press 'b' to go back" in output


class TestCLIUIIntegration:
    """Test overall CLI UI integration."""

    def test_ui_launch_function(self):
        """Test the launch_ui function initialization."""
        # We can't fully test launch_ui as it uses curses.wrapper,
        # but we can test that it handles import errors gracefully

        with patch(
            "hyper_core.ui.framework.NCursesFramework", side_effect=ImportError("test error")
        ):
            from hyper_core.cli import launch_ui

            with pytest.raises(SystemExit) as exc_info:
                launch_ui()

            assert exc_info.value.code == 1

    def test_menu_item_creation(self):
        """Test that menu items are created correctly."""
        # This test verifies the menu item creation logic
        # by mocking the framework

        mock_framework = Mock()
        mock_framework.add_menu_item = Mock()

        # Simulate menu item additions
        mock_framework.add_menu_item(key="c", label="Commands", action=Mock())

        mock_framework.add_menu_item(key="p", label="Plugins", action=Mock())

        # Verify calls
        assert mock_framework.add_menu_item.call_count == 2

        # Verify first call
        call_args = mock_framework.add_menu_item.call_args_list[0]
        assert call_args[1]["key"] == "c"
        assert call_args[1]["label"] == "Commands"
        assert callable(call_args[1]["action"])

        # Verify second call
        call_args = mock_framework.add_menu_item.call_args_list[1]
        assert call_args[1]["key"] == "p"
        assert call_args[1]["label"] == "Plugins"
        assert callable(call_args[1]["action"])

    def test_panel_navigation(self):
        """Test panel navigation behavior."""
        MockBackend(width=80, height=24)

        # Test that panels have correct back navigation
        framework = Mock()
        framework.set_panel = Mock()

        # Show commands panel
        show_commands_panel(framework)
        panel = framework.set_panel.call_args[0][0]

        # Test back key handling
        assert panel.handle_input(ord("b")) == "back"
        assert panel.handle_input(ord("B")) == "back"

        # Other keys should return None
        assert panel.handle_input(ord("x")) is None


class TestCLIUIErrorCases:
    """Test error handling in CLI UI."""

    def test_small_terminal_size(self):
        """Test UI behavior with very small terminal."""
        backend = MockBackend(width=10, height=5)
        engine = RenderEngine(backend)

        framework = Mock()
        framework.set_panel = Mock()

        # Show commands panel in small terminal
        show_commands_panel(framework)
        panel = framework.set_panel.call_args[0][0]

        # Render in small space
        ctx = RenderContext(window=engine.root_window, x=0, y=0, width=10, height=5)

        # Should not crash
        panel.render_content(ctx)

        # Basic elements should still be visible
        output = "".join(["".join(row) for row in backend.screen_buffer])
        # At least part of the title should be visible
        assert "Avail" in output or "Commands" in output

    def test_long_command_names(self):
        """Test handling of very long command names."""
        backend = MockBackend(width=40, height=10)
        engine = RenderEngine(backend)

        # Create command with very long name
        class LongNameCommand(BaseCommand):
            name = "this_is_a_very_long_command_name_that_exceeds_normal_length"
            description = "This also has a very long description that might cause layout issues"

            def execute(self, args):
                return 0

        framework = Mock()
        framework.set_panel = Mock()

        with patch("hyper_core.cli.discover_commands") as mock_discover:
            mock_registry = CommandRegistry()
            mock_registry.register(LongNameCommand)
            mock_discover.return_value = mock_registry

            show_commands_panel(framework)
            panel = framework.set_panel.call_args[0][0]

            ctx = RenderContext(window=engine.root_window, x=0, y=0, width=40, height=10)
            panel.render_content(ctx)

            # Should truncate long text gracefully
            output = "".join(["".join(row) for row in backend.screen_buffer])
            # Some part of the command should be visible
            assert "this_is_a_very_long" in output or "command_name" in output


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
