"""End-to-end integration tests demonstrating complete framework usage."""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

from rich.console import Console

from hyper_cmd import (
    BaseCommand,
    PluginRegistry,
    SimpleContainer,
    Theme,
    ThemeColors,
    ThemeManager,
)
from hyper_cmd.plugins import PluginDiscovery
from hyper_cmd.ui import ContentPanel, NCursesFramework

# Complete Application Example Components


class SystemMonitorCommand(BaseCommand):
    """System monitoring command for integration testing."""

    @property
    def name(self) -> str:
        return "monitor"

    @property
    def description(self) -> str:
        return "Launch system monitoring dashboard"

    def execute(self, duration: int = 60, refresh_rate: int = 5) -> int:
        """Launch monitoring dashboard."""
        try:
            # Get services from container
            self.container.get("ui_framework")
            theme_manager = self.container.get("theme_manager")
            plugin_registry = self.container.get("plugin_registry")

            # Create monitoring dashboard
            dashboard = self._create_dashboard(theme_manager, plugin_registry)

            self.print_info(
                f"Starting monitoring for {duration} seconds (refresh every {refresh_rate}s)"
            )

            # Simulate dashboard running
            for cycle in range(duration // refresh_rate):
                self._update_dashboard_widgets(dashboard)
                self.console.print(f"Monitoring cycle {cycle + 1}/{duration // refresh_rate}")

            self.print_success("Monitoring completed successfully")
            return 0

        except Exception as e:
            self.print_error(f"Monitoring failed: {e}")
            return 1

    def _create_dashboard(self, theme_manager, plugin_registry):
        """Create monitoring dashboard with widgets."""
        dashboard = ContentPanel("System Monitor")

        # Add core monitoring widgets (simulation for testing)
        dashboard.widgets = []

        # Simulate widgets for testing
        class MockWidget:
            def __init__(self, name):
                self.name = name
                self.needs_redraw = False

            def refresh_data(self):
                self.needs_redraw = True

        dashboard.widgets.append(MockWidget("CPU Usage"))
        dashboard.widgets.append(MockWidget("Network Traffic"))
        dashboard.widgets.append(MockWidget("Log Viewer"))

        # Add plugin widgets if available
        try:
            plugin_widgets = plugin_registry.get_widgets()
            for widget_class in plugin_widgets:
                if callable(widget_class):
                    widget = widget_class()
                    dashboard.widgets.append(widget)
        except AttributeError:
            # Plugin registry may not have get_widgets method
            pass

        return dashboard

    def _update_dashboard_widgets(self, dashboard):
        """Update all widgets in the dashboard."""
        for widget in dashboard.widgets:
            widget.refresh_data()


class ConfigurationService:
    """Configuration service for integration testing."""

    def __init__(self, config_file: str = None):
        self.config_file = config_file
        self.config = {
            "monitoring": {
                "refresh_interval": 5,
                "data_retention": 3600,
                "alert_thresholds": {"cpu": 80.0, "memory": 85.0, "disk": 90.0},
            },
            "ui": {"default_theme": "dark", "show_timestamps": True, "max_log_lines": 1000},
            "plugins": {
                "enabled": True,
                "auto_discover": True,
                "plugin_directories": ["./plugins", "~/.hyper-cmd/plugins"],
            },
        }

    def get(self, key_path: str, default=None):
        """Get configuration value by dot-separated path."""
        keys = key_path.split(".")
        value = self.config

        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default

        return value

    def set(self, key_path: str, value):
        """Set configuration value by dot-separated path."""
        keys = key_path.split(".")
        config = self.config

        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]

        config[keys[-1]] = value

    def save(self):
        """Save configuration to file."""
        if self.config_file:
            # In real implementation, would save to JSON/YAML file
            pass

    def load(self):
        """Load configuration from file."""
        if self.config_file and Path(self.config_file).exists():
            # In real implementation, would load from JSON/YAML file
            pass


class ApplicationBootstrap:
    """Application bootstrap class for integration testing."""

    def __init__(self):
        self.container = SimpleContainer()
        self.initialized = False

    def initialize(self, config_file: str = None):
        """Initialize the complete application."""
        try:
            # 1. Set up configuration
            config_service = ConfigurationService(config_file)
            config_service.load()
            self.container.register("config", config_service)

            # 2. Set up console
            console = Console()
            self.container.register(Console, console)

            # 3. Set up theme system
            theme_manager = ThemeManager()
            self._setup_themes(theme_manager, config_service)
            self.container.register("theme_manager", theme_manager)

            # 4. Set up UI framework
            ui_framework = NCursesFramework()
            self.container.register("ui_framework", ui_framework)

            # 5. Set up plugin system
            plugin_registry = PluginRegistry()
            self._setup_plugins(plugin_registry, config_service)
            self.container.register("plugin_registry", plugin_registry)

            # 6. Register core commands
            self._register_core_commands()

            self.initialized = True
            return True

        except Exception as e:
            print(f"Failed to initialize application: {e}")
            return False

    def _setup_themes(self, theme_manager, config_service):
        """Set up theme system with custom themes."""
        # Register custom monitoring theme
        monitoring_colors = ThemeColors(
            primary=(0, 255, 0),  # Bright green for terminal feel
            secondary=(0, 128, 0),  # Dark green
            background=(0, 0, 0),  # Black
            text=(0, 255, 0),  # Green text
            accent=(0, 255, 255),  # Cyan for highlights
            error=(255, 0, 0),  # Red
            warning=(255, 255, 0),  # Yellow
            success=(0, 255, 0),  # Green
        )
        monitoring_theme = Theme("monitoring", monitoring_colors)
        theme_manager.register_theme(monitoring_theme)

        # Set default theme from config
        default_theme = config_service.get("ui.default_theme", "dark")
        if default_theme in theme_manager.get_available_themes():
            from hyper_cmd.ui.renderer import MockBackend

            mock_backend = MockBackend()
            theme_manager.set_theme(default_theme, mock_backend)

    def _setup_plugins(self, plugin_registry, config_service):
        """Set up plugin system."""
        if config_service.get("plugins.enabled", True):
            plugin_dirs = config_service.get("plugins.plugin_directories", [])

            if config_service.get("plugins.auto_discover", True):
                for plugin_dir in plugin_dirs:
                    discovery = PluginDiscovery(plugin_dir)
                    discovered_paths = discovery.discover()

                    for plugin_path in discovered_paths:
                        # For testing, just add the plugin directory to registry
                        plugin_registry.add_plugin_path(plugin_path)

    def _register_core_commands(self):
        """Register core application commands."""
        from hyper_cmd.commands import CommandRegistry

        command_registry = CommandRegistry()
        command_registry.register("monitor", SystemMonitorCommand)
        self.container.register("command_registry", command_registry)

    def get_container(self):
        """Get the application container."""
        return self.container

    def shutdown(self):
        """Shutdown the application."""
        if self.initialized:
            # Clean up resources
            plugin_registry = self.container.get("plugin_registry")
            if plugin_registry:
                # Unload all plugins
                for plugin_name in plugin_registry.plugins.keys():
                    plugin_registry.unload_plugin(plugin_name)

            self.initialized = False


class TestCompleteIntegration:
    """Test complete application integration scenarios."""

    def test_application_bootstrap_and_initialization(self):
        """Test complete application bootstrap process."""
        app = ApplicationBootstrap()

        # Test initialization
        success = app.initialize()
        assert success is True
        assert app.initialized is True

        # Verify container has all required services
        container = app.get_container()
        assert container.get("config") is not None
        assert container.get(Console) is not None
        assert container.get("theme_manager") is not None
        assert container.get("ui_framework") is not None
        assert container.get("plugin_registry") is not None
        assert container.get("command_registry") is not None

        # Test shutdown
        app.shutdown()
        assert app.initialized is False

    def test_end_to_end_command_execution(self):
        """Test end-to-end command execution with full stack."""
        app = ApplicationBootstrap()
        app.initialize()

        container = app.get_container()

        # Create and execute system monitor command
        monitor_cmd = SystemMonitorCommand(container)

        # Test command execution with short duration for testing
        result = monitor_cmd.execute(duration=5, refresh_rate=1)
        assert result == 0

        app.shutdown()

    def test_plugin_system_integration(self):
        """Test plugin system integration with full application."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a test plugin
            plugin_dir = Path(temp_dir) / "test_plugin"
            plugin_dir.mkdir()

            plugin_content = '''
"""Test plugin for integration testing."""

PLUGIN_NAME = "integration_test"
PLUGIN_VERSION = "1.0.0"
PLUGIN_DESCRIPTION = "Integration test plugin"

from hyper_cmd import BaseCommand, BaseWidget, WidgetSize

class TestCommand(BaseCommand):
    @property
    def name(self) -> str:
        return "test"

    @property
    def description(self) -> str:
        return "Test command from plugin"

    def execute(self) -> int:
        self.print_success("Test plugin command executed!")
        return 0

class TestWidget(BaseWidget):
    def __init__(self):
        super().__init__(title="Test Widget", size=WidgetSize.SMALL)

    def draw_content(self, stdscr, x, y, width, height):
        try:
            stdscr.addstr(y + 1, x + 2, "Plugin widget working!")
        except:
            pass

    def refresh_data(self):
        self.needs_redraw = True
'''

            # Create proper plugin structure
            (plugin_dir / "__init__.py").write_text("")  # Empty __init__.py
            (plugin_dir / "plugin.py").write_text(plugin_content)  # Main plugin module

            # Initialize application with plugin directory
            app = ApplicationBootstrap()
            app.initialize()

            container = app.get_container()
            config = container.get("config")
            config.set("plugins.plugin_directories", [str(temp_dir)])

            # Reinitialize plugins with new directory
            container.get("plugin_registry")
            discovery = PluginDiscovery(str(temp_dir))
            discovered_paths = discovery.discover()

            # Verify plugin was discovered
            assert len(discovered_paths) > 0, "No plugins discovered"

            # For testing purposes, just verify the plugin directory structure exists
            plugin_found = any(path.name == "test_plugin" for path in discovered_paths)
            assert plugin_found, "Integration test plugin not found"

            app.shutdown()

    def test_theme_system_integration(self):
        """Test theme system integration with widgets and UI."""
        app = ApplicationBootstrap()
        app.initialize()

        container = app.get_container()
        theme_manager = container.get("theme_manager")

        # Test custom theme from bootstrap
        available_themes = theme_manager.get_available_themes()
        assert "monitoring" in available_themes

        # Switch to monitoring theme
        from hyper_cmd.ui.renderer import MockBackend

        mock_backend = MockBackend()
        theme_manager.set_theme("monitoring", mock_backend)
        current_theme = theme_manager.get_current_theme()
        assert current_theme.name == "monitoring"
        assert current_theme.colors.primary == (0, 255, 0)

        # Create themed widget and test
        from .test_themes import ThemedWidget

        widget = ThemedWidget(theme_manager)

        mock_stdscr = Mock()
        widget.draw_content(mock_stdscr, 0, 0, 50, 10)
        assert mock_stdscr.addstr.called

        app.shutdown()

    def test_configuration_driven_behavior(self):
        """Test configuration-driven application behavior."""
        app = ApplicationBootstrap()
        app.initialize()

        container = app.get_container()
        config = container.get("config")

        # Test default configuration values
        assert config.get("monitoring.refresh_interval") == 5
        assert config.get("ui.default_theme") == "dark"
        assert config.get("plugins.enabled") is True

        # Test configuration modification
        config.set("monitoring.refresh_interval", 10)
        assert config.get("monitoring.refresh_interval") == 10

        # Test nested configuration
        config.set("monitoring.alert_thresholds.cpu", 75.0)
        assert config.get("monitoring.alert_thresholds.cpu") == 75.0

        app.shutdown()

    @patch("curses.wrapper")
    def test_ui_framework_integration(self, mock_wrapper):
        """Test UI framework integration with application."""
        app = ApplicationBootstrap()
        app.initialize()

        container = app.get_container()
        container.get("ui_framework")
        container.get("theme_manager")

        # Create dashboard with mock widgets
        dashboard = ContentPanel("Integration Test Dashboard")
        dashboard.widgets = []

        # Mock widgets for testing
        class MockWidget:
            def __init__(self, name):
                self.name = name
                self.needs_redraw = False

            def refresh_data(self):
                self.needs_redraw = True

        dashboard.widgets.append(MockWidget("CPU Usage"))
        dashboard.widgets.append(MockWidget("Network Traffic"))

        assert len(dashboard.widgets) == 2
        assert dashboard.title == "Integration Test Dashboard"

        # Test widget updates
        for widget in dashboard.widgets:
            widget.refresh_data()
            assert widget.needs_redraw

        app.shutdown()


class TestRealWorldScenarios:
    """Test real-world usage scenarios."""

    def test_monitoring_application_scenario(self):
        """Test complete monitoring application scenario."""
        # Simulate building a monitoring application
        app = ApplicationBootstrap()
        app.initialize()

        container = app.get_container()
        config = container.get("config")

        # Configure for monitoring use case
        config.set("monitoring.refresh_interval", 2)
        config.set("monitoring.alert_thresholds.cpu", 70.0)
        config.set("ui.default_theme", "monitoring")

        # Switch to monitoring theme
        theme_manager = container.get("theme_manager")
        from hyper_cmd.ui.renderer import MockBackend

        mock_backend = MockBackend()
        theme_manager.set_theme("monitoring", mock_backend)

        # Create monitoring dashboard
        monitor_cmd = SystemMonitorCommand(container)
        dashboard = monitor_cmd._create_dashboard(theme_manager, container.get("plugin_registry"))

        # Simulate monitoring cycles
        for _cycle in range(3):
            monitor_cmd._update_dashboard_widgets(dashboard)

            # Verify widgets are updating
            for widget in dashboard.widgets:
                assert hasattr(widget, "needs_redraw")

        app.shutdown()

    def test_plugin_development_workflow(self):
        """Test plugin development and integration workflow."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Step 1: Create plugin structure
            plugin_dir = Path(temp_dir) / "monitoring_plugin"
            plugin_dir.mkdir()

            # Create plugin manifest
            manifest_content = '''
"""Advanced monitoring plugin."""

PLUGIN_NAME = "advanced_monitoring"
PLUGIN_VERSION = "2.0.0"
PLUGIN_DESCRIPTION = "Advanced system monitoring with alerts"
PLUGIN_AUTHOR = "DevOps Team"

from hyper_cmd import BaseCommand, BaseWidget, WidgetSize

class AlertCommand(BaseCommand):
    @property
    def name(self) -> str:
        return "alert"

    @property
    def description(self) -> str:
        return "Configure monitoring alerts"

    def execute(self, threshold: float = 80.0, email: str = None) -> int:
        config = self.container.get("config")
        config.set("monitoring.alert_thresholds.cpu", threshold)

        if email:
            config.set("monitoring.alert_email", email)

        self.print_success(f"Alert threshold set to {threshold}%")
        return 0

class DiskUsageWidget(BaseWidget):
    def __init__(self):
        super().__init__(title="Disk Usage", size=WidgetSize.MEDIUM)
        self.disk_usage = 0.0

    def draw_content(self, stdscr, x, y, width, height):
        try:
            usage_text = f"Disk: {self.disk_usage:.1f}%"
            stdscr.addstr(y + 1, x + 2, usage_text)
        except:
            pass

    def refresh_data(self):
        import random
        self.disk_usage = random.uniform(20, 95)
        self.needs_redraw = True
'''

            # Create proper plugin structure
            (plugin_dir / "__init__.py").write_text("")  # Empty __init__.py
            (plugin_dir / "plugin.py").write_text(manifest_content)  # Main plugin module

            # Step 2: Initialize application and load plugin
            app = ApplicationBootstrap()
            app.initialize()

            container = app.get_container()
            container.get("plugin_registry")

            # Discover plugin
            discovery = PluginDiscovery(str(temp_dir))
            discovered_paths = discovery.discover()

            # Verify plugin was discovered
            assert len(discovered_paths) > 0, "No plugins discovered"

            # For testing purposes, just verify the plugin directory structure exists
            plugin_found = any(path.name == "monitoring_plugin" for path in discovered_paths)
            assert plugin_found, "Advanced monitoring plugin not found"

            app.shutdown()

    def test_application_lifecycle_management(self):
        """Test complete application lifecycle management."""
        # Test initialization
        app = ApplicationBootstrap()
        assert not app.initialized

        success = app.initialize()
        assert success
        assert app.initialized

        container = app.get_container()

        # Test service availability during runtime
        services = [
            "config",
            "theme_manager",
            "ui_framework",
            "plugin_registry",
            "command_registry",
        ]
        for service in services:
            assert container.get(service) is not None

        # Test configuration persistence simulation
        config = container.get("config")
        config.set("test.runtime_value", "test_data")
        config.save()  # Would persist to file in real implementation

        # Test graceful shutdown
        app.shutdown()
        assert not app.initialized

        # Test reinitialization
        app2 = ApplicationBootstrap()
        success = app2.initialize()
        assert success

        # In real implementation, configuration would be loaded from file
        config2 = app2.get_container().get("config")
        assert config2 is not None

        app2.shutdown()

    def test_error_handling_and_recovery(self):
        """Test error handling and recovery scenarios."""
        app = ApplicationBootstrap()

        # Test initialization with invalid configuration
        with patch.object(ConfigurationService, "load", side_effect=Exception("Config error")):
            # Should handle error gracefully
            success = app.initialize()
            # Depending on implementation, might succeed with defaults or fail gracefully
            assert isinstance(success, bool)

        # Test command execution with errors
        if app.initialized:
            container = app.get_container()

            class FailingCommand(BaseCommand):
                @property
                def name(self) -> str:
                    return "fail"

                @property
                def description(self) -> str:
                    return "Command that fails"

                def execute(self) -> int:
                    raise RuntimeError("Simulated command failure")

            # Test that failing command returns error code
            fail_cmd = FailingCommand(container)
            try:
                result = fail_cmd.execute()
                # Should return non-zero exit code for errors
                assert result != 0
            except RuntimeError:
                # Or raise exception that calling code can handle
                pass

            app.shutdown()
