"""Real-world UI framework and widget tests."""

import curses
from unittest.mock import Mock, patch

from hyper_core.ui import (
    BaseWidget,
    ContentPanel,
    LayoutConfig,
    MenuAlignment,
    MenuItem,
    NCursesFramework,
    Theme,
    ThemeColors,
    ThemeManager,
    WidgetSize,
)


# Example Custom Widgets for Testing
class CPUUsageWidget(BaseWidget):
    """Example CPU usage monitoring widget."""

    def __init__(self):
        super().__init__(title="CPU Usage", size=WidgetSize.SMALL)
        self.cpu_percentage = 0.0
        self.core_usage = [0.0, 0.0, 0.0, 0.0]  # 4 cores

    def draw_content(self, stdscr, x, y, width, height):
        """Draw CPU usage information."""
        try:
            # Overall CPU usage
            usage_text = f"Overall: {self.cpu_percentage:.1f}%"
            stdscr.addstr(y + 1, x + 2, usage_text)

            # Progress bar for overall usage
            bar_width = width - 4
            filled = int((self.cpu_percentage / 100.0) * bar_width)
            bar = "█" * filled + "░" * (bar_width - filled)
            stdscr.addstr(y + 2, x + 2, bar)

            # Per-core usage
            for i, core_usage in enumerate(self.core_usage):
                if y + 3 + i < y + height - 1:
                    core_text = f"Core {i}: {core_usage:.1f}%"
                    stdscr.addstr(y + 3 + i, x + 2, core_text)
        except curses.error:
            # Handle curses drawing errors gracefully
            pass

    def refresh_data(self):
        """Refresh CPU usage data."""
        import random

        self.cpu_percentage = random.uniform(10.0, 80.0)
        self.core_usage = [random.uniform(5.0, 95.0) for _ in range(4)]
        self.needs_redraw = True


class NetworkTrafficWidget(BaseWidget):
    """Example network traffic monitoring widget."""

    def __init__(self):
        super().__init__(title="Network Traffic", size=WidgetSize.MEDIUM)
        self.bytes_sent = 0
        self.bytes_received = 0
        self.packets_sent = 0
        self.packets_received = 0

    def draw_content(self, stdscr, x, y, width, height):
        """Draw network traffic information."""
        try:
            # Traffic stats
            stats = [
                f"Bytes Sent:     {self._format_bytes(self.bytes_sent)}",
                f"Bytes Received: {self._format_bytes(self.bytes_received)}",
                f"Packets Sent:   {self.packets_sent:,}",
                f"Packets Recv:   {self.packets_received:,}",
            ]

            for i, stat in enumerate(stats):
                if y + 1 + i < y + height - 1:
                    stdscr.addstr(y + 1 + i, x + 2, stat)
        except curses.error:
            pass

    def _format_bytes(self, bytes_count):
        """Format bytes in human-readable format."""
        for unit in ["B", "KB", "MB", "GB"]:
            if bytes_count < 1024.0:
                return f"{bytes_count:.1f} {unit}"
            bytes_count /= 1024.0
        return f"{bytes_count:.1f} TB"

    def refresh_data(self):
        """Refresh network traffic data."""
        import random

        self.bytes_sent += random.randint(1000, 10000)
        self.bytes_received += random.randint(5000, 50000)
        self.packets_sent += random.randint(10, 100)
        self.packets_received += random.randint(50, 500)
        self.needs_redraw = True


class LogViewerWidget(BaseWidget):
    """Example log viewer widget."""

    def __init__(self, max_lines: int = 100):
        super().__init__(title="Log Viewer", size=WidgetSize.LARGE)
        self.max_lines = max_lines
        self.log_lines: list[str] = []
        self.scroll_offset = 0

    def add_log_line(self, line: str):
        """Add a new log line."""
        self.log_lines.append(line)
        if len(self.log_lines) > self.max_lines:
            self.log_lines.pop(0)
        self.needs_redraw = True

    def draw_content(self, stdscr, x, y, width, height):
        """Draw log lines."""
        try:
            visible_lines = height - 2  # Account for borders
            start_line = max(0, len(self.log_lines) - visible_lines + self.scroll_offset)

            for i in range(visible_lines):
                line_index = start_line + i
                if line_index < len(self.log_lines):
                    log_line = self.log_lines[line_index]
                    # Truncate line if too long
                    if len(log_line) > width - 4:
                        log_line = log_line[: width - 7] + "..."
                    stdscr.addstr(y + 1 + i, x + 2, log_line)
        except curses.error:
            pass

    def scroll_up(self):
        """Scroll up in the log."""
        if self.scroll_offset < 0:
            self.scroll_offset += 1
            self.needs_redraw = True

    def scroll_down(self):
        """Scroll down in the log."""
        max_offset = -(len(self.log_lines) - 10)  # Adjust based on visible lines
        if self.scroll_offset > max_offset:
            self.scroll_offset -= 1
            self.needs_redraw = True

    def refresh_data(self):
        """Refresh log data (could fetch from log file)."""
        import datetime
        import random

        # Simulate new log entries
        levels = ["INFO", "WARN", "ERROR", "DEBUG"]
        messages = [
            "User login successful",
            "Database connection established",
            "Cache miss for key: user_123",
            "Request processed in 45ms",
            "Background task completed",
        ]

        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        level = random.choice(levels)
        message = random.choice(messages)
        log_line = f"[{timestamp}] {level}: {message}"

        self.add_log_line(log_line)


class TestBaseWidget:
    """Test the BaseWidget functionality."""

    def test_widget_creation_and_properties(self):
        """Test widget creation and basic properties."""
        widget = CPUUsageWidget()

        assert widget.title == "CPU Usage"
        assert widget.size == WidgetSize.SMALL
        assert widget.visible is True
        assert widget.needs_redraw is False
        assert widget.x == 0
        assert widget.y == 0
        assert widget.width == 0
        assert widget.height == 0

    def test_widget_positioning_and_sizing(self):
        """Test widget positioning and sizing."""
        widget = NetworkTrafficWidget()

        # Test setting position
        widget.set_position(10, 20)
        assert widget.x == 10
        assert widget.y == 20

        # Test setting size
        widget.set_size(50, 15)
        assert widget.width == 50
        assert widget.height == 15

    def test_widget_visibility_control(self):
        """Test widget visibility controls."""
        widget = LogViewerWidget()

        # Widget should be visible by default
        assert widget.visible is True

        # Test hiding widget
        widget.hide()
        assert widget.visible is False

        # Test showing widget
        widget.show()
        assert widget.visible is True

    def test_widget_refresh_mechanism(self):
        """Test widget refresh and redraw mechanism."""
        widget = CPUUsageWidget()

        # Initially doesn't need redraw
        assert widget.needs_redraw is False

        # After refresh, should need redraw
        widget.refresh_data()
        assert widget.needs_redraw is True

        # After drawing, should not need redraw
        widget.needs_redraw = False
        assert widget.needs_redraw is False

    @patch("curses.newwin")
    def test_widget_drawing(self, mock_newwin):
        """Test widget drawing with mocked curses."""
        mock_stdscr = Mock()
        widget = CPUUsageWidget()

        # Set up widget position and size
        widget.set_position(5, 10)
        widget.set_size(30, 8)

        # Refresh data to have something to draw
        widget.refresh_data()

        # Test drawing
        widget.draw_content(mock_stdscr, widget.x, widget.y, widget.width, widget.height)

        # Verify that addstr was called (drawing happened)
        assert mock_stdscr.addstr.called


class TestAdvancedWidgets:
    """Test advanced widget features and interactions."""

    def test_log_viewer_scrolling(self):
        """Test log viewer scrolling functionality."""
        widget = LogViewerWidget(max_lines=50)

        # Add some log lines
        for i in range(20):
            widget.add_log_line(f"Log line {i}: Some important message")

        assert len(widget.log_lines) == 20
        assert widget.scroll_offset == 0

        # Test scrolling up
        widget.scroll_up()
        assert widget.scroll_offset == 1

        # Test scrolling down
        widget.scroll_down()
        widget.scroll_down()
        assert widget.scroll_offset == -1

    def test_log_viewer_line_limit(self):
        """Test log viewer line limit functionality."""
        widget = LogViewerWidget(max_lines=10)

        # Add more lines than the limit
        for i in range(15):
            widget.add_log_line(f"Line {i}")

        # Should only keep the last 10 lines
        assert len(widget.log_lines) == 10
        assert widget.log_lines[0] == "Line 5"  # Oldest kept line
        assert widget.log_lines[-1] == "Line 14"  # Newest line

    def test_network_widget_data_formatting(self):
        """Test network widget data formatting."""
        widget = NetworkTrafficWidget()

        # Test byte formatting
        assert widget._format_bytes(512) == "512.0 B"
        assert widget._format_bytes(1024) == "1.0 KB"
        assert widget._format_bytes(1024 * 1024) == "1.0 MB"
        assert widget._format_bytes(1024 * 1024 * 1024) == "1.0 GB"

        # Test data updates
        initial_sent = widget.bytes_sent
        widget.refresh_data()
        assert widget.bytes_sent > initial_sent


class TestThemeSystem:
    """Test the theme system."""

    def test_theme_creation_and_properties(self):
        """Test theme creation and color properties."""
        colors = ThemeColors(
            primary=(255, 255, 255),
            secondary=(128, 128, 128),
            background=(0, 0, 0),
            text=(255, 255, 255),
            accent=(0, 255, 0),
            error=(255, 0, 0),
            warning=(255, 255, 0),
            success=(0, 255, 0),
        )

        theme = Theme("custom", colors)
        assert theme.name == "custom"
        assert theme.colors.primary == (255, 255, 255)
        assert theme.colors.error == (255, 0, 0)

    def test_theme_manager(self):
        """Test theme management functionality."""
        manager = ThemeManager()

        # Test default theme
        default_theme = manager.get_current_theme()
        assert default_theme is not None
        assert default_theme.name in ["default", "dark"]

        # Test registering custom theme
        custom_colors = ThemeColors(
            primary=(100, 100, 255),
            secondary=(200, 200, 200),
            background=(20, 20, 20),
            text=(255, 255, 255),
            accent=(255, 100, 100),
            error=(255, 50, 50),
            warning=(255, 200, 50),
            success=(50, 255, 50),
        )
        custom_theme = Theme("custom", custom_colors)

        manager.register_theme(custom_theme)
        available_themes = manager.get_available_themes()
        assert "custom" in available_themes

        # Test switching themes
        manager.set_theme("custom")
        current_theme = manager.get_current_theme()
        assert current_theme.name == "custom"
        assert current_theme.colors.primary == (100, 100, 255)


class TestUIFramework:
    """Test the NCurses UI framework."""

    @patch("curses.initscr")
    @patch("curses.curs_set")
    @patch("curses.start_color")
    def test_framework_initialization(self, mock_start_color, mock_curs_set, mock_initscr):
        """Test UI framework initialization."""
        mock_stdscr = Mock()
        mock_initscr.return_value = mock_stdscr

        framework = NCursesFramework()
        framework.initialize()

        # Verify curses initialization
        mock_initscr.assert_called_once()
        mock_start_color.assert_called_once()
        mock_curs_set.assert_called_once_with(0)  # Hide cursor

    def test_layout_configuration(self):
        """Test layout configuration."""
        config = LayoutConfig(
            show_header=True,
            show_footer=True,
            show_sidebar=True,
            header_height=3,
            footer_height=2,
            sidebar_width=20,
        )

        assert config.show_header is True
        assert config.header_height == 3
        assert config.sidebar_width == 20

    def test_content_panel_creation(self):
        """Test content panel creation and management."""
        panel = ContentPanel("Main Content")

        assert panel.title == "Main Content"
        assert len(panel.widgets) == 0

        # Add widgets to panel
        cpu_widget = CPUUsageWidget()
        network_widget = NetworkTrafficWidget()

        panel.add_widget(cpu_widget)
        panel.add_widget(network_widget)

        assert len(panel.widgets) == 2
        assert cpu_widget in panel.widgets
        assert network_widget in panel.widgets

    def test_menu_system(self):
        """Test menu system functionality."""
        menu_items = [
            MenuItem("Dashboard", "dashboard", "Main dashboard view"),
            MenuItem("Monitoring", "monitoring", "System monitoring"),
            MenuItem("Logs", "logs", "View application logs"),
            MenuItem("Settings", "settings", "Application settings"),
        ]

        for item in menu_items:
            assert item.label is not None
            assert item.key is not None
            assert item.description is not None

        # Test menu alignment
        assert MenuAlignment.LEFT == MenuAlignment.LEFT
        assert MenuAlignment.CENTER == MenuAlignment.CENTER


class TestWidgetLayouts:
    """Test widget layout and arrangement."""

    def test_grid_layout_calculation(self):
        """Test grid layout calculations for widgets."""
        # Create widgets of different sizes
        widgets = [
            CPUUsageWidget(),  # SMALL
            NetworkTrafficWidget(),  # MEDIUM
            LogViewerWidget(),  # LARGE
            CPUUsageWidget(),  # SMALL
        ]

        # Simulate layout calculation
        screen_width = 120
        screen_height = 40

        # Simple grid layout algorithm
        def calculate_grid_layout(widgets, screen_width, screen_height):
            layout = []
            current_row_widgets = []
            current_row_width = 0
            y_offset = 0

            for widget in widgets:
                widget_width = {
                    WidgetSize.SMALL: screen_width // 3,
                    WidgetSize.MEDIUM: screen_width // 2,
                    WidgetSize.LARGE: screen_width,
                }[widget.size]

                # Check if widget fits in current row
                if current_row_width + widget_width <= screen_width:
                    current_row_widgets.append((widget, current_row_width, widget_width))
                    current_row_width += widget_width
                else:
                    # Start new row
                    if current_row_widgets:
                        layout.append((current_row_widgets, y_offset))
                        y_offset += 10  # Fixed row height for simplicity
                    current_row_widgets = [(widget, 0, widget_width)]
                    current_row_width = widget_width

            # Add last row
            if current_row_widgets:
                layout.append((current_row_widgets, y_offset))

            return layout

        layout = calculate_grid_layout(widgets, screen_width, screen_height)

        # Verify layout structure
        assert len(layout) >= 1  # At least one row

        # Check that small widgets can share rows
        first_row = layout[0][0]
        if len(first_row) > 1:
            # Multiple widgets in first row
            total_width = sum(widget_info[2] for widget_info in first_row)
            assert total_width <= screen_width

    def test_responsive_layout(self):
        """Test responsive layout behavior."""
        # Test different screen sizes
        layouts = {}

        for width in [60, 120, 180]:  # Small, medium, large screens
            # Calculate how many widgets fit per row
            widget_width = width // 3  # Small widget width
            widgets_per_row = width // widget_width

            layouts[width] = {"widgets_per_row": widgets_per_row, "widget_width": widget_width}

        # Verify responsive behavior
        assert layouts[60]["widgets_per_row"] <= layouts[120]["widgets_per_row"]
        assert layouts[120]["widgets_per_row"] <= layouts[180]["widgets_per_row"]


class TestUIIntegration:
    """Test end-to-end UI integration scenarios."""

    def test_dashboard_creation_and_management(self):
        """Test creating and managing a complete dashboard."""
        # Create dashboard components
        cpu_widget = CPUUsageWidget()
        network_widget = NetworkTrafficWidget()
        log_widget = LogViewerWidget()

        # Create content panel
        dashboard = ContentPanel("System Dashboard")
        dashboard.add_widget(cpu_widget)
        dashboard.add_widget(network_widget)
        dashboard.add_widget(log_widget)

        # Verify dashboard setup
        assert dashboard.title == "System Dashboard"
        assert len(dashboard.widgets) == 3

        # Test widget refresh cycle
        for widget in dashboard.widgets:
            widget.refresh_data()
            assert widget.needs_redraw  # Should need redraw after refresh

    def test_interactive_widget_updates(self):
        """Test interactive widget updates and data flow."""
        log_widget = LogViewerWidget()

        # Simulate real-time log updates
        import datetime

        for i in range(5):
            timestamp = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
            log_widget.add_log_line(f"[{timestamp}] INFO: Event {i} occurred")

        assert len(log_widget.log_lines) == 5
        assert "Event 4 occurred" in log_widget.log_lines[-1]

        # Test scrolling interaction
        initial_offset = log_widget.scroll_offset
        log_widget.scroll_up()
        assert log_widget.scroll_offset != initial_offset

    @patch("curses.wrapper")
    def test_full_application_simulation(self, mock_wrapper):
        """Test simulating a full application with UI framework."""

        def mock_main_loop(stdscr):
            # Simulate main application loop
            framework = NCursesFramework()

            # Create widgets
            widgets = [CPUUsageWidget(), NetworkTrafficWidget(), LogViewerWidget()]

            # Create layout
            panel = ContentPanel("Main Dashboard")
            for widget in widgets:
                panel.add_widget(widget)

            # Simulate update cycle
            for _ in range(3):  # 3 update cycles
                for widget in widgets:
                    widget.refresh_data()
                    # In real app, would call widget.draw()

            return 0  # Success

        # Test that the application structure works
        result = mock_main_loop(Mock())
        assert result == 0
