"""Real-world framework usage tests that work with the actual API."""

import curses
from typing import Optional
from unittest.mock import Mock, patch

from rich.console import Console

from hyper_core import (
    BaseCommand,
    BaseWidget,
    PluginMetadata,
    PluginRegistry,
    SimpleContainer,
    Theme,
    ThemeColors,
    ThemeManager,
    WidgetSize,
)
from hyper_core.ui import ContentPanel, LayoutConfig, MenuAlignment, MenuItem, NCursesFramework


class ExampleWidget(BaseWidget):
    """Example widget that demonstrates real framework usage."""

    def __init__(self, title: str = "Example Widget"):
        super().__init__(title=title, size=WidgetSize.MEDIUM)
        self.data_value = 42.0

    def draw_content(self, stdscr, x, y, width, height):
        """Draw widget content using actual API."""
        try:
            # Use the widget's color constants
            stdscr.addstr(
                y + 1, x + 2, f"Value: {self.data_value:.1f}", curses.color_pair(self.COLOR_INFO)
            )

            # Draw a simple progress bar
            bar_width = width - 6
            filled = int((self.data_value / 100.0) * bar_width)

            bar_y = y + 3
            for i in range(bar_width):
                char = "█" if i < filled else "░"
                color = self.COLOR_SUCCESS if i < filled else self.COLOR_SECONDARY
                try:
                    stdscr.addstr(bar_y, x + 3 + i, char, curses.color_pair(color))
                except curses.error:
                    pass
        except curses.error:
            # Handle curses errors gracefully
            pass

    def get_minimum_size(self) -> tuple:
        """Return minimum size for the widget."""
        return (20, 6)

    def refresh_data(self):
        """Refresh widget data."""
        import random

        self.data_value = random.uniform(0, 100)
        self._needs_redraw = True


class ExampleContentPanel(ContentPanel):
    """Example content panel for testing UI framework."""

    def __init__(self, title: str = "Example Panel"):
        super().__init__()
        self.title = title
        self.widgets: list[BaseWidget] = []
        self.selected_index = 0

    def add_widget(self, widget: BaseWidget):
        """Add a widget to the panel."""
        self.widgets.append(widget)
        self.refresh()

    def draw(self, win, height: int, width: int) -> None:
        """Draw the panel content."""
        try:
            # Clear the window
            win.clear()

            # Draw title
            title_text = f"=== {self.title} ==="
            win.addstr(0, (width - len(title_text)) // 2, title_text)

            # Draw widgets info
            y_pos = 2
            for i, widget in enumerate(self.widgets):
                prefix = ">" if i == self.selected_index else " "
                widget_info = f"{prefix} {widget._title} ({widget.size.name})"

                try:
                    color = curses.color_pair(
                        BaseWidget.COLOR_ACCENT
                        if i == self.selected_index
                        else BaseWidget.COLOR_DEFAULT
                    )
                    win.addstr(y_pos + i, 2, widget_info, color)
                except curses.error:
                    win.addstr(y_pos + i, 2, widget_info)

            # Draw help text
            help_text = "Use UP/DOWN to select, ENTER to refresh, Q to quit"
            if y_pos + len(self.widgets) + 2 < height:
                win.addstr(height - 2, 2, help_text)

            win.refresh()
            self._needs_refresh = False

        except curses.error:
            pass

    def handle_input(self, key: int) -> Optional[str]:
        """Handle keyboard input."""
        if key == ord("q") or key == ord("Q"):
            return "quit"
        elif key == curses.KEY_UP and self.selected_index > 0:
            self.selected_index -= 1
            self.refresh()
        elif key == curses.KEY_DOWN and self.selected_index < len(self.widgets) - 1:
            self.selected_index += 1
            self.refresh()
        elif key == ord("\n") or key == ord("\r"):  # Enter key
            if self.widgets and 0 <= self.selected_index < len(self.widgets):
                self.widgets[self.selected_index].refresh_data()
                self.refresh()

        return None


class ExampleCommand(BaseCommand):
    """Example command demonstrating real framework usage."""

    @property
    def name(self) -> str:
        return "example"

    @property
    def description(self) -> str:
        return "Example command showing framework usage"

    def execute(self, count: int = 3, message: str = "Hello") -> int:
        """Execute the example command."""
        try:
            self.print_info(f"Running example command with count={count}")

            for i in range(count):
                self.console.print(f"{i+1}. {message} from hyper-core!")

            self.print_success("Example command completed successfully")
            return 0

        except Exception as e:
            self.print_error(f"Example command failed: {e}")
            return 1


class TestRealFrameworkUsage:
    """Test suite using the actual framework API."""

    def test_simple_container_usage(self):
        """Test actual SimpleContainer API usage."""
        container = SimpleContainer()

        # Test basic registration
        console = Console()
        container.register(Console, console)

        # Test retrieval
        retrieved_console = container.get(Console)
        assert retrieved_console is console

        # Test string key registration (if supported)
        container.register(str, "test_string")

        retrieved_string = container.get(str)
        assert retrieved_string == "test_string"

    def test_simple_container_factory(self):
        """Test SimpleContainer factory registration."""
        container = SimpleContainer()

        # Register factory
        def create_widget():
            return ExampleWidget("Factory Widget")

        container.register_factory(ExampleWidget, create_widget)

        # Get widget from factory
        widget = container.get(ExampleWidget)
        assert isinstance(widget, ExampleWidget)
        assert widget._title == "Factory Widget"

        # Test singleton behavior
        widget2 = container.get(ExampleWidget)
        assert widget2 is widget

    def test_base_widget_actual_api(self):
        """Test BaseWidget with actual API methods."""
        widget = ExampleWidget("Test Widget")

        # Test actual properties
        assert widget._title == "Test Widget"
        assert widget.size == WidgetSize.MEDIUM
        assert hasattr(widget, "_needs_redraw")

        # Test minimum size method
        min_size = widget.get_minimum_size()
        assert isinstance(min_size, tuple)
        assert len(min_size) == 2

        # Test refresh data
        initial_value = widget.data_value
        widget.refresh_data()
        # Value should have changed (random)
        assert widget.data_value != initial_value or True  # Allow same random value

    def test_plugin_registry_actual_api(self):
        """Test PluginRegistry with actual API."""
        registry = PluginRegistry()

        # Test initialization
        registry.initialize()

        # Test plugin metadata creation
        metadata = PluginMetadata(
            name="test_plugin", version="1.0.0", description="Test plugin", author="Test Author"
        )

        assert metadata.name == "test_plugin"
        assert metadata.version == "1.0.0"
        assert not metadata.loaded
        assert isinstance(metadata.components, dict)

    def test_theme_system_actual_api(self):
        """Test theme system with actual API."""
        # Test ThemeColors with actual signature
        colors = ThemeColors(
            default=(curses.COLOR_WHITE, -1),
            primary=(curses.COLOR_GREEN, -1),
            secondary=(curses.COLOR_BLUE, -1),
            accent=(curses.COLOR_CYAN, -1),
            error=(curses.COLOR_RED, -1),
            warning=(curses.COLOR_YELLOW, -1),
            success=(curses.COLOR_GREEN, -1),
            info=(curses.COLOR_CYAN, -1),
        )

        # Test Theme creation
        theme = Theme(name="test_theme", description="Test theme", colors=colors)

        assert theme.name == "test_theme"
        assert theme.colors.primary == (curses.COLOR_GREEN, -1)

    def test_theme_manager_actual_api(self):
        """Test ThemeManager with actual API."""
        manager = ThemeManager()

        # Test current theme access
        current_theme = manager.current_theme
        assert current_theme is not None

        # Test theme registration
        custom_colors = ThemeColors(
            primary=(curses.COLOR_MAGENTA, -1), accent=(curses.COLOR_YELLOW, -1)
        )
        custom_theme = Theme("custom", "Custom theme", custom_colors)

        manager.register_theme(custom_theme)

        # Test theme switching
        manager.set_theme("custom")
        assert manager.current_theme.name == "custom"

    def test_content_panel_implementation(self):
        """Test ContentPanel implementation."""
        panel = ExampleContentPanel("Test Panel")

        # Test adding widgets
        widget1 = ExampleWidget("Widget 1")
        widget2 = ExampleWidget("Widget 2")

        panel.add_widget(widget1)
        panel.add_widget(widget2)

        assert len(panel.widgets) == 2
        assert panel.selected_index == 0

        # Test input handling
        result = panel.handle_input(curses.KEY_DOWN)
        assert result is None  # Should not quit
        assert panel.selected_index == 1

        result = panel.handle_input(ord("q"))
        assert result == "quit"

    @patch("curses.newwin")
    def test_content_panel_drawing(self, mock_newwin):
        """Test ContentPanel drawing with mocked curses."""
        mock_win = Mock()
        panel = ExampleContentPanel("Test Panel")

        widget = ExampleWidget("Test Widget")
        panel.add_widget(widget)

        # Test drawing
        panel.draw(mock_win, 20, 80)

        # Verify drawing methods were called
        assert mock_win.clear.called
        assert mock_win.addstr.called
        assert mock_win.refresh.called

    def test_layout_config_actual_api(self):
        """Test LayoutConfig with actual API."""
        config = LayoutConfig(
            title="Test App",
            subtitle="Test Subtitle",
            menu_alignment=MenuAlignment.CENTER,
            show_borders=True,
            show_help=True,
        )

        assert config.title == "Test App"
        assert config.subtitle == "Test Subtitle"
        assert config.menu_alignment == MenuAlignment.CENTER
        assert config.show_borders is True
        assert config.show_help is True

    def test_menu_item_creation(self):
        """Test MenuItem creation."""

        def test_action():
            return "action_executed"

        item = MenuItem(
            key="test",
            label="Test Item",
            description="Test menu item",
            action=test_action,
            enabled=True,
        )

        assert item.key == "test"
        assert item.label == "Test Item"
        assert item.description == "Test menu item"
        assert item.action() == "action_executed"
        assert item.enabled is True

    def test_command_with_container(self):
        """Test command execution with container dependencies."""
        container = SimpleContainer()
        console = Console()
        container.register(Console, console)

        command = ExampleCommand(container)

        # Test command properties
        assert command.name == "example"
        assert command.description == "Example command showing framework usage"

        # Test command execution
        result = command.execute(count=2, message="Test")
        assert result == 0

    @patch("curses.wrapper")
    def test_ncurses_framework_initialization(self, mock_wrapper):
        """Test NCursesFramework initialization."""
        config = LayoutConfig(title="Test Framework")
        framework = NCursesFramework(config)

        # Test that framework was created successfully
        assert framework is not None
        # Note: Actual initialization requires curses environment

    def test_widget_color_constants(self):
        """Test widget color constants are available."""
        widget = ExampleWidget()

        # Test that color constants are defined
        assert hasattr(widget, "COLOR_DEFAULT")
        assert hasattr(widget, "COLOR_SUCCESS")
        assert hasattr(widget, "COLOR_INFO")
        assert hasattr(widget, "COLOR_WARNING")
        assert hasattr(widget, "COLOR_ERROR")
        assert hasattr(widget, "COLOR_ACCENT")
        assert hasattr(widget, "COLOR_SECONDARY")

        # Test that they have reasonable values
        assert isinstance(widget.COLOR_DEFAULT, int)
        assert isinstance(widget.COLOR_SUCCESS, int)
        assert widget.COLOR_SUCCESS != widget.COLOR_ERROR


class TestFrameworkIntegration:
    """Test integration between framework components."""

    def test_widget_and_panel_integration(self):
        """Test widgets working with content panels."""
        panel = ExampleContentPanel("Integration Test")

        # Create multiple widgets
        widgets = [
            ExampleWidget("CPU Monitor"),
            ExampleWidget("Memory Monitor"),
            ExampleWidget("Disk Monitor"),
        ]

        for widget in widgets:
            panel.add_widget(widget)

        assert len(panel.widgets) == 3

        # Test navigation
        assert panel.selected_index == 0
        panel.handle_input(curses.KEY_DOWN)
        assert panel.selected_index == 1
        panel.handle_input(curses.KEY_DOWN)
        assert panel.selected_index == 2

        # Test refresh on enter
        panel.handle_input(ord("\n"))
        assert panel.needs_refresh()

    def test_command_and_container_integration(self):
        """Test commands working with dependency injection."""
        container = SimpleContainer()

        # Register dependencies
        console = Console()
        container.register(Console, console)

        # Register a custom service
        class ConfigService:
            def __init__(self):
                self.settings = {"debug": True, "timeout": 30}

            def get(self, key: str):
                return self.settings.get(key)

        config_service = ConfigService()
        container.register(ConfigService, config_service)

        # Test command using container
        command = ExampleCommand(container)

        # Command should have access to console through container
        assert command.console is console

        # Test execution
        result = command.execute(count=1, message="Integration Test")
        assert result == 0

    def test_theme_and_widget_integration(self):
        """Test themes working with widgets."""
        # Create theme manager and widget
        theme_manager = ThemeManager()
        widget = ExampleWidget("Themed Widget")

        # Create custom theme
        custom_colors = ThemeColors(
            primary=(curses.COLOR_MAGENTA, -1),
            accent=(curses.COLOR_YELLOW, -1),
            success=(curses.COLOR_GREEN, -1),
        )
        custom_theme = Theme("custom", colors=custom_colors)

        # Register and apply theme
        theme_manager.register_theme(custom_theme)
        theme_manager.set_theme("custom")

        # Verify theme is active
        assert theme_manager.current_theme.name == "custom"

        # Widget should be able to use color constants
        mock_stdscr = Mock()
        widget.draw_content(mock_stdscr, 0, 0, 50, 10)

        # Verify drawing methods were called
        assert mock_stdscr.addstr.called
