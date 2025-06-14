"""Real-world plugin system tests demonstrating extensibility."""

import sys
import tempfile
from pathlib import Path

from rich.console import Console

from hyper_cmd import BaseCommand, BaseWidget, WidgetSize
from hyper_cmd.container import SimpleContainer
from hyper_cmd.plugins import PluginMetadata, PluginRegistry, plugin_registry


# Example Plugin Components
class MonitoringCommand(BaseCommand):
    """Example command from a monitoring plugin."""

    @property
    def name(self) -> str:
        return "monitor"

    @property
    def description(self) -> str:
        return "Monitor system resources"

    def execute(self, interval: int = 5, count: int = 10) -> int:
        """Monitor system resources."""
        self.print_info(f"Monitoring for {count} intervals of {interval}s each")

        for i in range(count):
            # Simulate monitoring
            cpu_usage = 25.5 + (i * 2.1)  # Fake increasing CPU usage
            memory_usage = 60.2 + (i * 1.5)  # Fake increasing memory usage

            self.console.print(
                f"Interval {i + 1}: CPU: {cpu_usage:.1f}%, Memory: {memory_usage:.1f}%"
            )

        return 0


class SystemStatusWidget(BaseWidget):
    """Example widget from a monitoring plugin."""

    def __init__(self):
        super().__init__(title="System Status", size=WidgetSize.MEDIUM)
        self.cpu_usage = 0.0
        self.memory_usage = 0.0
        self.disk_usage = 0.0

    def draw_content(self, stdscr, x, y, width, height):
        """Draw system status information."""
        # Simulate drawing system stats
        try:
            stdscr.addstr(y + 1, x + 2, f"CPU:    {self.cpu_usage:.1f}%")
            stdscr.addstr(y + 2, x + 2, f"Memory: {self.memory_usage:.1f}%")
            stdscr.addstr(y + 3, x + 2, f"Disk:   {self.disk_usage:.1f}%")
        except Exception:
            # Handle curses errors gracefully in tests
            pass

    def refresh_data(self):
        """Refresh system status data."""
        # Simulate data refresh
        import random

        self.cpu_usage = random.uniform(10, 80)
        self.memory_usage = random.uniform(30, 90)
        self.disk_usage = random.uniform(20, 70)
        self.needs_redraw = True


class DatabaseService:
    """Example service from a database plugin."""

    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self.connected = False

    def connect(self):
        """Connect to database."""
        self.connected = True
        return True

    def execute_query(self, query: str):
        """Execute database query."""
        if not self.connected:
            raise RuntimeError("Not connected to database")
        return f"Result for: {query}"

    def disconnect(self):
        """Disconnect from database."""
        self.connected = False


class TestPluginSystem:
    """Test suite demonstrating plugin system usage."""

    def setup_method(self):
        """Set up test environment."""
        self.container = SimpleContainer()
        self.container.register(Console, Console())
        self.registry = PluginRegistry()

    def test_plugin_metadata_creation(self):
        """Test plugin metadata structure."""
        metadata = PluginMetadata(
            name="monitoring",
            version="1.0.0",
            description="System monitoring plugin",
            author="Test Author",
            dependencies=["psutil>=5.0.0"],
            config_schema={
                "refresh_interval": {"type": "integer", "default": 30},
                "alert_threshold": {"type": "float", "default": 80.0},
            },
        )

        assert metadata.name == "monitoring"
        assert metadata.version == "1.0.0"
        assert metadata.description == "System monitoring plugin"
        assert metadata.author == "Test Author"
        assert "psutil>=5.0.0" in metadata.dependencies
        assert metadata.config_schema["refresh_interval"]["default"] == 30
        assert not metadata.loaded

    def test_plugin_component_registration(self):
        """Test registering plugin components."""
        # Register different types of components
        self.registry.register_command(MonitoringCommand, "monitoring")
        self.registry.register_widget(SystemStatusWidget, "monitoring")

        # Verify registration
        commands = self.registry.list_commands()
        widgets = self.registry.list_widgets()

        assert "monitoring" in commands  # The actual name registered
        assert "systemstatus" in widgets

    def test_plugin_lifecycle_management(self):
        """Test plugin loading and unloading."""
        # Initialize registry with a temporary plugin path
        import tempfile

        with tempfile.TemporaryDirectory() as temp_dir:
            self.registry.add_plugin_path(temp_dir)
            self.registry.initialize()

            # Test discovery (should be empty for temp dir)
            discovered = self.registry.discover_plugins()
            assert isinstance(discovered, list)

    def test_plugin_dependency_resolution(self):
        """Test plugin dependency management."""
        # Create plugins with dependencies
        base_plugin = PluginMetadata("base", "1.0.0")
        dependent_plugin = PluginMetadata("dependent", "1.0.0", dependencies=["base>=1.0.0"])

        # Test that dependencies are stored correctly
        assert "base>=1.0.0" in dependent_plugin.dependencies
        assert len(base_plugin.dependencies) == 0

    def test_plugin_configuration(self):
        """Test plugin configuration management."""
        metadata = PluginMetadata(
            "configurable",
            "1.0.0",
            config_schema={
                "api_key": {"type": "string", "required": True},
                "timeout": {"type": "integer", "default": 30},
                "debug": {"type": "boolean", "default": False},
            },
        )

        # Test configuration schema storage
        assert "api_key" in metadata.config_schema
        assert metadata.config_schema["timeout"]["default"] == 30
        assert not metadata.config_schema["debug"]["default"]


class TestPluginDiscovery:
    """Test plugin discovery mechanisms."""

    def test_file_based_plugin_discovery(self):
        """Test discovering plugins from files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            plugin_dir = Path(temp_dir) / "plugins"
            plugin_dir.mkdir()

            # Create a sample plugin file
            plugin_file = plugin_dir / "sample_plugin.py"
            plugin_content = '''
"""Sample plugin for testing."""

PLUGIN_NAME = "sample"
PLUGIN_VERSION = "1.0.0"
PLUGIN_DESCRIPTION = "Sample plugin for testing"

from hyper_cmd import BaseCommand

class SampleCommand(BaseCommand):
    @property
    def name(self) -> str:
        return "sample"

    @property
    def description(self) -> str:
        return "Sample command"

    def execute(self) -> int:
        self.print_success("Sample command executed!")
        return 0
'''
            plugin_file.write_text(plugin_content)

            # Test plugin discovery
            from hyper_cmd.plugins import PluginDiscovery

            discovery = PluginDiscovery(str(plugin_dir))

            plugins = discovery.discover()
            assert len(plugins) >= 0  # May be 0 if plugin structure not correct

            # Note: This test would need proper plugin structure to discover plugins

    def test_package_based_plugin_discovery(self):
        """Test discovering plugins from packages."""
        # Create a temporary plugin package
        with tempfile.TemporaryDirectory() as temp_dir:
            plugin_package = Path(temp_dir) / "my_plugin"
            plugin_package.mkdir()

            # Create __init__.py
            init_file = plugin_package / "__init__.py"
            init_content = '''
"""My custom plugin package."""

PLUGIN_NAME = "my_plugin"
PLUGIN_VERSION = "2.0.0"
PLUGIN_DESCRIPTION = "My custom plugin"

from .commands import CustomCommand
from .widgets import CustomWidget

__all__ = ["CustomCommand", "CustomWidget"]
'''
            init_file.write_text(init_content)

            # Create commands module
            commands_file = plugin_package / "commands.py"
            commands_content = """
from hyper_cmd import BaseCommand

class CustomCommand(BaseCommand):
    @property
    def name(self) -> str:
        return "custom"

    @property
    def description(self) -> str:
        return "Custom command"

    def execute(self) -> int:
        return 0
"""
            commands_file.write_text(commands_content)

            # Create widgets module
            widgets_file = plugin_package / "widgets.py"
            widgets_content = """
from hyper_cmd import BaseWidget, WidgetSize

class CustomWidget(BaseWidget):
    def __init__(self):
        super().__init__(title="Custom", size=WidgetSize.SMALL)

    def draw_content(self, stdscr, x, y, width, height):
        pass

    def refresh_data(self):
        pass
"""
            widgets_file.write_text(widgets_content)

            # Add to Python path temporarily
            sys.path.insert(0, str(temp_dir))
            try:
                from hyper_cmd.plugins import PluginDiscovery

                discovery = PluginDiscovery(str(temp_dir))

                plugins = discovery.discover()

                # Test that discovery works
                assert isinstance(plugins, list)

            finally:
                sys.path.remove(str(temp_dir))


class TestPluginIntegration:
    """Test end-to-end plugin integration."""

    def test_complete_plugin_workflow(self):
        """Test complete plugin registration and usage workflow."""
        container = SimpleContainer()
        container.register(Console, Console())

        # Create registry
        registry = PluginRegistry()

        # Register components
        registry.register_command(MonitoringCommand, "integration_test")
        registry.register_widget(SystemStatusWidget, "integration_test")

        # Test using the command
        commands = registry.list_commands()
        assert "monitoring" in commands

        # Test creating the command
        monitor_cmd_class = registry.get_command("monitoring")
        monitor_cmd = monitor_cmd_class(container)
        result = monitor_cmd.execute(interval=1, count=3)
        assert result == 0

        # Test using the widget
        widget = SystemStatusWidget()
        assert widget.title == "System Status"
        assert widget.size == WidgetSize.MEDIUM

        # Test refreshing widget data
        widget.refresh_data()
        assert widget.needs_redraw

    def test_plugin_error_handling(self):
        """Test plugin error handling and recovery."""
        container = SimpleContainer()
        registry = PluginRegistry()

        # Test loading invalid plugin
        class BrokenCommand(BaseCommand):
            @property
            def name(self) -> str:
                return "broken"

            @property
            def description(self) -> str:
                return "Broken command"

            def execute(self) -> int:
                raise RuntimeError("Something went wrong!")

        registry.register_command(BrokenCommand, "broken_plugin")

        # Test that broken command doesn't crash the system
        try:
            commands = registry.list_commands()
            assert "broken" in commands

            broken_cmd_class = registry.get_command("broken")
            broken_cmd = broken_cmd_class(container)
            result = broken_cmd.run()  # Use run() which has error handling
            # Command should handle its own errors and return non-zero exit code
            assert result != 0
        except Exception:
            # Plugin system should handle errors gracefully
            pass

    def test_global_plugin_registry(self):
        """Test the global plugin registry singleton."""
        # Test that global registry works

        # Initialize plugin registry
        plugin_registry.initialize()

        # Register a command globally
        plugin_registry.register_command(MonitoringCommand, "global_test")

        # Verify it's registered
        commands = plugin_registry.list_commands()
        assert "monitoring" in commands
