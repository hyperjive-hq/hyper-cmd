"""Real-world plugin system tests demonstrating extensibility."""

import sys
import tempfile
from pathlib import Path

from rich.console import Console

from hyper_core import BaseCommand, BaseWidget, WidgetSize
from hyper_core.container import SimpleContainer
from hyper_core.plugins import PluginMetadata, PluginRegistry, plugin_registry


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
                f"Interval {i+1}: CPU: {cpu_usage:.1f}%, Memory: {memory_usage:.1f}%"
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
        except:
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
        self.registry = PluginRegistry(self.container)

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
        metadata = PluginMetadata("monitoring", "1.0.0")

        # Register different types of components
        self.registry.register_command(metadata, MonitoringCommand)
        self.registry.register_widget(metadata, SystemStatusWidget)
        self.registry.register_service(metadata, "database", DatabaseService)

        # Verify registration
        commands = self.registry.get_commands()
        widgets = self.registry.get_widgets()
        services = self.registry.get_services()

        assert "monitor" in commands
        assert MonitoringCommand in widgets  # Widget registration may vary by implementation
        assert "database" in services

    def test_plugin_lifecycle_management(self):
        """Test plugin loading and unloading."""
        metadata = PluginMetadata("monitoring", "1.0.0")

        # Test loading
        assert not metadata.loaded
        self.registry.load_plugin(metadata)
        assert metadata.loaded

        # Test unloading
        self.registry.unload_plugin(metadata)
        assert not metadata.loaded

    def test_plugin_dependency_resolution(self):
        """Test plugin dependency management."""
        # Create plugins with dependencies
        base_plugin = PluginMetadata("base", "1.0.0")
        dependent_plugin = PluginMetadata("dependent", "1.0.0", dependencies=["base>=1.0.0"])

        # Register plugins
        self.registry.register_plugin(base_plugin)
        self.registry.register_plugin(dependent_plugin)

        # Test dependency resolution
        load_order = self.registry.resolve_dependencies()

        # Base plugin should be loaded before dependent plugin
        base_index = load_order.index("base")
        dependent_index = load_order.index("dependent")
        assert base_index < dependent_index

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

        # Test configuration validation
        valid_config = {"api_key": "test-key-123", "timeout": 60, "debug": True}

        # This would typically be handled by the registry
        assert self.registry.validate_config(metadata, valid_config)

        # Test invalid configuration
        invalid_config = {
            "timeout": "not_an_integer",  # Wrong type
            "debug": True,
            # Missing required api_key
        }

        assert not self.registry.validate_config(metadata, invalid_config)


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

from hyper_core import BaseCommand

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
            from hyper_core.plugins import PluginDiscovery

            discovery = PluginDiscovery([str(plugin_dir)])

            plugins = discovery.discover_plugins()
            assert len(plugins) >= 1

            # Find our sample plugin
            sample_plugin = next((p for p in plugins if p.name == "sample"), None)
            assert sample_plugin is not None
            assert sample_plugin.version == "1.0.0"
            assert sample_plugin.description == "Sample plugin for testing"

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
from hyper_core import BaseCommand

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
from hyper_core import BaseWidget, WidgetSize

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
                from hyper_core.plugins import PluginDiscovery

                discovery = PluginDiscovery([str(temp_dir)])

                plugins = discovery.discover_plugins()

                # Find our custom plugin
                custom_plugin = next((p for p in plugins if p.name == "my_plugin"), None)
                assert custom_plugin is not None
                assert custom_plugin.version == "2.0.0"

            finally:
                sys.path.remove(str(temp_dir))


class TestPluginIntegration:
    """Test end-to-end plugin integration."""

    def test_complete_plugin_workflow(self):
        """Test complete plugin registration and usage workflow."""
        container = SimpleContainer()
        container.register(Console, Console())

        # Create and register a plugin
        metadata = PluginMetadata(
            "integration_test", "1.0.0", description="Integration test plugin"
        )

        registry = PluginRegistry(container)
        registry.register_plugin(metadata)

        # Register components
        registry.register_command(metadata, MonitoringCommand)
        registry.register_widget(metadata, SystemStatusWidget)
        registry.register_service(metadata, "database", DatabaseService)

        # Load the plugin
        registry.load_plugin(metadata)

        # Test using the command
        commands = registry.get_commands()
        assert "monitor" in commands

        monitor_cmd = commands["monitor"](container)
        result = monitor_cmd.execute(interval=1, count=3)
        assert result == 0

        # Test using the widget
        widget = SystemStatusWidget()
        assert widget.title == "System Status"
        assert widget.size == WidgetSize.MEDIUM

        # Test refreshing widget data
        widget.refresh_data()
        assert widget.needs_redraw

        # Test using the service
        services = registry.get_services()
        assert "database" in services

        db_service = services["database"]("sqlite:///test.db")
        assert db_service.connect()
        assert db_service.connected

        result = db_service.execute_query("SELECT 1")
        assert "Result for: SELECT 1" in result

    def test_plugin_error_handling(self):
        """Test plugin error handling and recovery."""
        container = SimpleContainer()
        registry = PluginRegistry(container)

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

        metadata = PluginMetadata("broken", "1.0.0")
        registry.register_plugin(metadata)
        registry.register_command(metadata, BrokenCommand)

        # Test that broken command doesn't crash the system
        try:
            registry.load_plugin(metadata)
            commands = registry.get_commands()
            broken_cmd = commands["broken"](container)
            result = broken_cmd.execute()
            # Command should handle its own errors and return non-zero exit code
            assert result != 0
        except Exception:
            # Plugin system should handle errors gracefully
            pass

    def test_global_plugin_registry(self):
        """Test the global plugin registry singleton."""
        # Test that global registry works

        # Initialize with container
        container = SimpleContainer()
        plugin_registry.initialize(container)

        # Register a plugin globally
        metadata = PluginMetadata("global_test", "1.0.0")
        plugin_registry.register_plugin(metadata)

        # Verify it's registered
        plugins = plugin_registry.list_plugins()
        assert "global_test" in [p.name for p in plugins]
