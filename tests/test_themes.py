"""Theme system tests demonstrating customization and theming."""

from unittest.mock import Mock

from hyper_core.ui import BaseWidget, Theme, ThemeColors, ThemeManager, WidgetSize
from hyper_core.ui.renderer import MockBackend


class ThemedWidget(BaseWidget):
    """Example widget that demonstrates theme usage."""

    def __init__(self, theme_manager: ThemeManager):
        super().__init__(title="Themed Widget", size=WidgetSize.MEDIUM)
        self.theme_manager = theme_manager
        self.data_value = 75.5

    def draw_content(self, stdscr, x, y, width, height):
        """Draw content using current theme colors."""
        theme = self.theme_manager.get_current_theme()

        try:
            # Use theme colors for different elements
            # Title in accent color
            title_color = self._get_color_pair(theme.colors.accent)
            stdscr.addstr(y + 1, x + 2, f"Value: {self.data_value:.1f}", title_color)

            # Status based on value
            if self.data_value > 80:
                status = "HIGH"
                status_color = self._get_color_pair(theme.colors.error)
            elif self.data_value > 60:
                status = "MEDIUM"
                status_color = self._get_color_pair(theme.colors.warning)
            else:
                status = "LOW"
                status_color = self._get_color_pair(theme.colors.success)

            stdscr.addstr(y + 2, x + 2, f"Status: {status}", status_color)

            # Progress bar using theme colors
            bar_width = width - 6
            filled = int((self.data_value / 100.0) * bar_width)

            # Use primary color for filled portion
            filled_color = self._get_color_pair(theme.colors.primary)
            empty_color = self._get_color_pair(theme.colors.secondary)

            bar_y = y + 4
            for i in range(bar_width):
                char = "█" if i < filled else "░"
                color = filled_color if i < filled else empty_color
                stdscr.addstr(bar_y, x + 3 + i, char, color)

        except curses.error:
            # Handle curses errors gracefully
            pass

    def _get_color_pair(self, rgb_color: tuple[int, int, int]) -> int:
        """Convert RGB color to curses color pair (simplified)."""
        # In real implementation, would map RGB to curses color pairs
        return 1  # Default color pair for testing

    def refresh_data(self):
        """Refresh widget data."""
        import random

        self.data_value = random.uniform(0, 100)
        self.needs_redraw = True


class TestThemeColors:
    """Test theme color definitions and management."""

    def test_theme_colors_creation(self):
        """Test creating theme color definitions."""
        colors = ThemeColors(
            primary=(0, 120, 215),  # Blue
            secondary=(108, 117, 125),  # Gray
            background=(33, 37, 41),  # Dark gray
            text=(248, 249, 250),  # Light gray
            accent=(40, 167, 69),  # Green
            error=(220, 53, 69),  # Red
            warning=(255, 193, 7),  # Yellow
            success=(25, 135, 84),  # Dark green
        )

        assert colors.primary == (0, 120, 215)
        assert colors.secondary == (108, 117, 125)
        assert colors.background == (33, 37, 41)
        assert colors.text == (248, 249, 250)
        assert colors.accent == (40, 167, 69)
        assert colors.error == (220, 53, 69)
        assert colors.warning == (255, 193, 7)
        assert colors.success == (25, 135, 84)

    def test_theme_colors_validation(self):
        """Test theme color validation."""
        # Valid RGB values
        valid_colors = ThemeColors(
            primary=(255, 255, 255),
            secondary=(0, 0, 0),
            background=(128, 128, 128),
            text=(200, 200, 200),
            accent=(100, 150, 200),
            error=(255, 0, 0),
            warning=(255, 255, 0),
            success=(0, 255, 0),
        )

        # All values should be in valid RGB range
        for color_name in [
            "primary",
            "secondary",
            "background",
            "text",
            "accent",
            "error",
            "warning",
            "success",
        ]:
            color_value = getattr(valid_colors, color_name)
            assert isinstance(color_value, tuple)
            assert len(color_value) == 3
            for component in color_value:
                assert 0 <= component <= 255

    def test_predefined_color_schemes(self):
        """Test predefined color schemes for different use cases."""
        # High contrast theme for accessibility
        high_contrast = ThemeColors(
            primary=(255, 255, 255),  # Pure white
            secondary=(192, 192, 192),  # Light gray
            background=(0, 0, 0),  # Pure black
            text=(255, 255, 255),  # Pure white
            accent=(255, 255, 0),  # Bright yellow
            error=(255, 0, 0),  # Bright red
            warning=(255, 165, 0),  # Orange
            success=(0, 255, 0),  # Bright green
        )

        # Verify high contrast ratios
        assert high_contrast.primary == (255, 255, 255)
        assert high_contrast.background == (0, 0, 0)

        # Solarized-inspired theme
        solarized = ThemeColors(
            primary=(131, 148, 150),  # Base0
            secondary=(88, 110, 117),  # Base01
            background=(0, 43, 54),  # Base03
            text=(238, 232, 213),  # Base2
            accent=(42, 161, 152),  # Cyan
            error=(220, 50, 47),  # Red
            warning=(181, 137, 0),  # Yellow
            success=(133, 153, 0),  # Green
        )

        assert solarized.background == (0, 43, 54)
        assert solarized.accent == (42, 161, 152)


class TestTheme:
    """Test theme creation and properties."""

    def test_theme_creation(self):
        """Test creating custom themes."""
        colors = ThemeColors(
            primary=(70, 130, 180),  # Steel blue
            secondary=(119, 136, 153),  # Light slate gray
            background=(25, 25, 112),  # Midnight blue
            text=(255, 255, 255),  # White
            accent=(255, 215, 0),  # Gold
            error=(178, 34, 34),  # Fire brick
            warning=(255, 140, 0),  # Dark orange
            success=(34, 139, 34),  # Forest green
        )

        theme = Theme("ocean", colors)

        assert theme.name == "ocean"
        assert theme.colors.primary == (70, 130, 180)
        assert theme.colors.background == (25, 25, 112)
        assert theme.colors.accent == (255, 215, 0)

    def test_theme_metadata(self):
        """Test theme metadata and descriptions."""
        colors = ThemeColors(
            primary=(139, 69, 19),  # Saddle brown
            secondary=(160, 82, 45),  # Saddle brown
            background=(101, 67, 33),  # Dark brown
            text=(245, 245, 220),  # Beige
            accent=(255, 140, 0),  # Dark orange
            error=(220, 20, 60),  # Crimson
            warning=(255, 215, 0),  # Gold
            success=(154, 205, 50),  # Yellow green
        )

        theme = Theme(
            "earth",
            colors,
            description="Earthy, warm color scheme inspired by nature",
            author="Theme Designer",
            version="1.0.0",
        )

        assert theme.name == "earth"
        assert theme.description == "Earthy, warm color scheme inspired by nature"
        assert theme.author == "Theme Designer"
        assert theme.version == "1.0.0"


class TestThemeManager:
    """Test theme manager functionality."""

    def setup_method(self):
        """Set up test environment."""
        self.theme_manager = ThemeManager()
        self.mock_backend = MockBackend()

    def test_default_themes_available(self):
        """Test that default themes are available."""
        available_themes = self.theme_manager.get_available_themes()

        # Should have at least default and dark themes
        assert len(available_themes) >= 2
        assert "default" in available_themes or "light" in available_themes
        assert "dark" in available_themes

    def test_current_theme_management(self):
        """Test current theme getter and setter."""
        # Get initial theme
        initial_theme = self.theme_manager.get_current_theme()
        assert initial_theme is not None
        assert initial_theme.name is not None

        # Try to switch to dark theme
        available_themes = self.theme_manager.get_available_themes()
        if "dark" in available_themes:
            self.theme_manager.set_theme("dark", self.mock_backend)
            current_theme = self.theme_manager.get_current_theme()
            assert current_theme.name == "dark"

    def test_custom_theme_registration(self):
        """Test registering custom themes."""
        # Create custom theme
        custom_colors = ThemeColors(
            primary=(255, 20, 147),  # Deep pink
            secondary=(219, 112, 147),  # Pale violet red
            background=(72, 61, 139),  # Dark slate blue
            text=(255, 255, 255),  # White
            accent=(0, 255, 255),  # Cyan
            error=(255, 69, 0),  # Red orange
            warning=(255, 215, 0),  # Gold
            success=(50, 205, 50),  # Lime green
        )

        custom_theme = Theme("neon", custom_colors)

        # Register theme
        self.theme_manager.register_theme(custom_theme)

        # Verify registration
        available_themes = self.theme_manager.get_available_themes()
        assert "neon" in available_themes

        # Switch to custom theme
        self.theme_manager.set_theme("neon", self.mock_backend)
        current_theme = self.theme_manager.get_current_theme()
        assert current_theme.name == "neon"
        assert current_theme.colors.primary == (255, 20, 147)

    def test_theme_switching_with_callbacks(self):
        """Test theme switching with callback notifications."""
        callback_called = False
        old_theme_name = None
        new_theme_name = None

        def theme_change_callback(old_theme, new_theme):
            nonlocal callback_called, old_theme_name, new_theme_name
            callback_called = True
            old_theme_name = old_theme.name if old_theme else None
            new_theme_name = new_theme.name if new_theme else None

        # Register callback
        self.theme_manager.add_theme_change_callback(theme_change_callback)

        # Create and register a test theme
        test_colors = ThemeColors(
            primary=(100, 100, 100),
            secondary=(150, 150, 150),
            background=(50, 50, 50),
            text=(255, 255, 255),
            accent=(200, 200, 0),
            error=(255, 0, 0),
            warning=(255, 255, 0),
            success=(0, 255, 0),
        )
        test_theme = Theme("test", test_colors)
        self.theme_manager.register_theme(test_theme)

        # Switch theme
        self.theme_manager.set_theme("test", self.mock_backend)

        # Verify callback was called
        assert callback_called
        assert new_theme_name == "test"

    def test_theme_persistence_preferences(self):
        """Test theme preference persistence simulation."""
        # Simulate saving theme preferences
        preferences = {}

        def save_theme_preference(theme_name):
            preferences["current_theme"] = theme_name

        def load_theme_preference():
            return preferences.get("current_theme", "default")

        # Register custom theme
        custom_colors = ThemeColors(
            primary=(128, 0, 128),  # Purple
            secondary=(147, 112, 219),  # Medium purple
            background=(25, 25, 25),  # Very dark gray
            text=(255, 255, 255),  # White
            accent=(255, 0, 255),  # Magenta
            error=(255, 0, 0),  # Red
            warning=(255, 255, 0),  # Yellow
            success=(0, 255, 0),  # Green
        )
        custom_theme = Theme("purple", custom_colors)
        self.theme_manager.register_theme(custom_theme)

        # Set theme and save preference
        self.theme_manager.set_theme("purple", self.mock_backend)
        save_theme_preference("purple")

        # Simulate loading preferences in new session
        preferred_theme = load_theme_preference()
        assert preferred_theme == "purple"

        # Apply loaded preference
        self.theme_manager.set_theme(preferred_theme, self.mock_backend)
        current_theme = self.theme_manager.get_current_theme()
        assert current_theme.name == "purple"


class TestThemedWidgets:
    """Test widgets using theme system."""

    def test_widget_theme_integration(self):
        """Test widget integration with theme system."""
        theme_manager = ThemeManager()
        widget = ThemedWidget(theme_manager)

        # Test with default theme
        default_theme = theme_manager.get_current_theme()
        assert default_theme is not None

        # Mock drawing with theme
        mock_stdscr = Mock()
        widget.draw_content(mock_stdscr, 0, 0, 50, 10)

        # Verify drawing methods were called
        assert mock_stdscr.addstr.called

    def test_theme_switching_affects_widgets(self):
        """Test that theme switching affects widget appearance."""
        theme_manager = ThemeManager()
        widget = ThemedWidget(theme_manager)

        # Register contrasting themes
        light_colors = ThemeColors(
            primary=(0, 0, 0),  # Black
            secondary=(128, 128, 128),  # Gray
            background=(255, 255, 255),  # White
            text=(0, 0, 0),  # Black
            accent=(0, 0, 255),  # Blue
            error=(255, 0, 0),  # Red
            warning=(255, 165, 0),  # Orange
            success=(0, 128, 0),  # Green
        )

        dark_colors = ThemeColors(
            primary=(255, 255, 255),  # White
            secondary=(128, 128, 128),  # Gray
            background=(0, 0, 0),  # Black
            text=(255, 255, 255),  # White
            accent=(100, 149, 237),  # Cornflower blue
            error=(255, 99, 71),  # Tomato
            warning=(255, 215, 0),  # Gold
            success=(144, 238, 144),  # Light green
        )

        light_theme = Theme("light_custom", light_colors)
        dark_theme = Theme("dark_custom", dark_colors)

        theme_manager.register_theme(light_theme)
        theme_manager.register_theme(dark_theme)
        mock_backend = MockBackend()

        # Test with light theme
        theme_manager.set_theme("light_custom", mock_backend)
        light_current = theme_manager.get_current_theme()
        assert light_current.colors.background == (255, 255, 255)

        # Test with dark theme
        theme_manager.set_theme("dark_custom", mock_backend)
        dark_current = theme_manager.get_current_theme()
        assert dark_current.colors.background == (0, 0, 0)

        # Widget should use current theme colors
        mock_stdscr = Mock()
        widget.draw_content(mock_stdscr, 0, 0, 50, 10)
        assert mock_stdscr.addstr.called

    def test_theme_responsive_widget_colors(self):
        """Test widgets responding to theme color changes."""
        theme_manager = ThemeManager()
        widget = ThemedWidget(theme_manager)

        # Set different data values to test color responses
        test_values = [25.0, 65.0, 85.0]  # Low, medium, high

        for value in test_values:
            widget.data_value = value
            mock_stdscr = Mock()
            widget.draw_content(mock_stdscr, 0, 0, 50, 10)

            # Verify that drawing occurred (color selection logic is internal)
            assert mock_stdscr.addstr.call_count >= 2  # At least value and status


class TestThemeCompatibility:
    """Test theme compatibility and edge cases."""

    def test_invalid_theme_handling(self):
        """Test handling of invalid theme requests."""
        theme_manager = ThemeManager()

        # Try to set non-existent theme  
        mock_backend = MockBackend()
        try:
            theme_manager.set_theme("nonexistent", mock_backend)
        except KeyError:
            pass  # Expected behavior

        # Should still have a valid theme (likely unchanged)
        current_theme = theme_manager.get_current_theme()
        assert current_theme is not None

    def test_theme_color_fallbacks(self):
        """Test theme color fallback mechanisms."""
        # Create theme with minimal color definition
        minimal_colors = ThemeColors(
            primary=(255, 255, 255),
            secondary=(128, 128, 128),
            background=(0, 0, 0),
            text=(255, 255, 255),
            accent=(0, 255, 0),
            error=(255, 0, 0),
            warning=(255, 255, 0),
            success=(0, 255, 0),
        )

        minimal_theme = Theme("minimal", minimal_colors)

        # Verify all required colors are present
        assert minimal_theme.colors.primary is not None
        assert minimal_theme.colors.background is not None
        assert minimal_theme.colors.text is not None
        assert minimal_theme.colors.error is not None

    def test_theme_performance(self):
        """Test theme switching performance."""
        theme_manager = ThemeManager()

        # Create multiple themes
        themes = []
        for i in range(10):
            colors = ThemeColors(
                primary=(i * 25, i * 25, i * 25),
                secondary=(128, 128, 128),
                background=(i * 10, i * 10, i * 10),
                text=(255, 255, 255),
                accent=(255 - i * 25, 128, i * 25),
                error=(255, 0, 0),
                warning=(255, 255, 0),
                success=(0, 255, 0),
            )
            theme = Theme(f"test_theme_{i}", colors)
            themes.append(theme)
            theme_manager.register_theme(theme)

        # Test rapid theme switching
        import time
        mock_backend = MockBackend()

        start_time = time.time()

        for theme in themes:
            theme_manager.set_theme(theme.name, mock_backend)

        end_time = time.time()

        # Theme switching should be fast (less than 1 second for 10 switches)
        assert (end_time - start_time) < 1.0
