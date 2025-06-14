"""
Renderer abstraction layer for UI components.

This module provides an abstract interface for rendering backends,
allowing the UI framework to work with different rendering systems
(ncurses, mock for testing, etc).
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class WindowSpec:
    """Specification for a window/drawing surface."""

    width: int
    height: int
    x: int = 0
    y: int = 0


class RenderingBackend(ABC):
    """Abstract base class for rendering backends."""

    @abstractmethod
    def init(self) -> None:
        """Initialize the rendering backend."""
        pass

    @abstractmethod
    def cleanup(self) -> None:
        """Clean up resources used by the backend."""
        pass

    @abstractmethod
    def get_screen_size(self) -> tuple[int, int]:
        """Get the current screen size (height, width)."""
        pass

    @abstractmethod
    def create_window(self, spec: WindowSpec) -> "Window":
        """Create a new window/drawing surface."""
        pass

    @abstractmethod
    def refresh(self) -> None:
        """Refresh/update the display."""
        pass

    @abstractmethod
    def get_input(self, timeout: int = -1) -> int:
        """Get keyboard input. Returns -1 if no input available."""
        pass

    @abstractmethod
    def set_cursor_visible(self, visible: bool) -> None:
        """Set cursor visibility."""
        pass

    @abstractmethod
    def has_colors(self) -> bool:
        """Check if the backend supports colors."""
        pass

    @abstractmethod
    def init_colors(self) -> None:
        """Initialize color support if available."""
        pass

    @abstractmethod
    def init_theme_colors(self, theme: Any) -> None:
        """Initialize all theme colors at once."""
        pass


class Window(ABC):
    """Abstract base class for windows/drawing surfaces."""

    @abstractmethod
    def clear(self) -> None:
        """Clear the window."""
        pass

    @abstractmethod
    def refresh(self) -> None:
        """Refresh this specific window."""
        pass

    @abstractmethod
    def get_size(self) -> tuple[int, int]:
        """Get window size (height, width)."""
        pass

    @abstractmethod
    def add_str(self, y: int, x: int, text: str, attrs: int = 0) -> None:
        """Add a string at the specified position with optional attributes."""
        pass

    @abstractmethod
    def add_ch(self, y: int, x: int, ch: Any, attrs: int = 0) -> None:
        """Add a character at the specified position with optional attributes."""
        pass

    @abstractmethod
    def get_max_yx(self) -> tuple[int, int]:
        """Get the maximum y,x coordinates for this window."""
        pass


# Style constants that match curses attributes
class TextStyle:
    """Text style constants matching curses attributes."""

    NORMAL = 0
    BOLD = 1 << 0
    UNDERLINE = 1 << 1
    REVERSE = 1 << 2
    BLINK = 1 << 3
    DIM = 1 << 4
    STANDOUT = 1 << 5


# Character constants for box drawing
class BoxChars:
    """Box drawing character constants."""

    # Unicode box drawing characters as defaults
    HLINE = "─"
    VLINE = "│"
    ULCORNER = "┌"
    URCORNER = "┐"
    LLCORNER = "└"
    LRCORNER = "┘"

    # These will be set by the backend if special chars are available
    ACS_HLINE: Optional[Any] = None
    ACS_VLINE: Optional[Any] = None
    ACS_ULCORNER: Optional[Any] = None
    ACS_URCORNER: Optional[Any] = None
    ACS_LLCORNER: Optional[Any] = None
    ACS_LRCORNER: Optional[Any] = None


class NCursesBackend(RenderingBackend):
    """NCurses implementation of the rendering backend."""

    def __init__(self) -> None:
        self._stdscr: Optional[Any] = None
        self._windows: dict[int, Any] = {}
        self._next_window_id: int = 0
        self._curses: Optional[Any] = None

    def init(self) -> None:
        """Initialize ncurses."""
        import curses

        self._curses = curses

    def setup(self, stdscr: Any) -> None:
        """Setup ncurses with the standard screen."""
        self._stdscr = stdscr

        # Make sure curses is imported
        if self._curses is None:
            import curses

            self._curses = curses

        # Set up special characters
        BoxChars.ACS_HLINE = self._curses.ACS_HLINE
        BoxChars.ACS_VLINE = self._curses.ACS_VLINE
        BoxChars.ACS_ULCORNER = self._curses.ACS_ULCORNER
        BoxChars.ACS_URCORNER = self._curses.ACS_URCORNER
        BoxChars.ACS_LLCORNER = self._curses.ACS_LLCORNER
        BoxChars.ACS_LRCORNER = self._curses.ACS_LRCORNER

        # Map text styles
        TextStyle.BOLD = self._curses.A_BOLD
        TextStyle.UNDERLINE = self._curses.A_UNDERLINE
        TextStyle.REVERSE = self._curses.A_REVERSE
        TextStyle.BLINK = self._curses.A_BLINK
        TextStyle.DIM = self._curses.A_DIM
        TextStyle.STANDOUT = self._curses.A_STANDOUT

        # Additional setup for the stdscr
        self._stdscr.nodelay(True)  # Non-blocking input
        self._stdscr.keypad(True)  # Enable special keys

    def cleanup(self) -> None:
        """Cleanup is handled by curses.wrapper."""
        pass

    def get_screen_size(self) -> tuple[int, int]:
        """Get screen size."""
        if self._stdscr is not None:
            return self._stdscr.getmaxyx()
        return (24, 80)  # Default size

    def create_window(self, spec: WindowSpec) -> "NCursesWindow":
        """Create a new ncurses window."""
        # For ncurses, we'll use the stdscr as the main window
        # In a more complex implementation, we could create subwindows
        return NCursesWindow(self._stdscr, self._curses)

    def refresh(self) -> None:
        """Refresh the display."""
        if self._stdscr is not None:
            self._stdscr.refresh()

    def get_input(self, timeout: int = -1) -> int:
        """Get keyboard input."""
        if self._stdscr is not None:
            if timeout >= 0:
                self._stdscr.timeout(timeout)
            return self._stdscr.getch()
        return -1

    def set_cursor_visible(self, visible: bool) -> None:
        """Set cursor visibility."""
        try:
            if self._curses is not None:
                self._curses.curs_set(1 if visible else 0)
        except Exception:  # type: ignore[misc]
            pass  # Some terminals don't support cursor visibility

    def has_colors(self) -> bool:
        """Check color support."""
        if self._curses is not None:
            return self._curses.has_colors()
        return False

    def init_colors(self) -> None:
        """Initialize colors."""
        if self.has_colors() and self._curses is not None:
            self._curses.start_color()
            self._curses.use_default_colors()

    def init_theme_colors(self, theme: Any) -> None:
        """Initialize theme colors."""
        if not self.has_colors():
            return

        # Get curses-compatible colors from theme
        colors_dict: dict[str, tuple[int, int]] = theme.colors.get_curses_colors()

        # Initialize color pairs according to theme mapping
        for pair_id, color_name in theme.COLOR_PAIR_MAPPING.items():
            if color_name in colors_dict:
                fg, bg = colors_dict[color_name]
                try:
                    if self._curses is not None:
                        self._curses.init_pair(pair_id, fg, bg)
                except Exception:  # type: ignore[misc]
                    # Ignore errors (e.g., invalid color values)
                    pass


class NCursesWindow(Window):
    """NCurses window implementation."""

    def __init__(self, window: Any, curses_module: Any) -> None:
        self._window = window
        self._curses = curses_module

    def clear(self) -> None:
        """Clear the window."""
        self._window.clear()

    def refresh(self) -> None:
        """Refresh this window."""
        self._window.refresh()

    def get_size(self) -> tuple[int, int]:
        """Get window size."""
        return self._window.getmaxyx()

    def add_str(self, y: int, x: int, text: str, attrs: int = 0) -> None:
        """Add string with error handling."""
        try:
            self._window.addstr(y, x, text, attrs)
        except Exception:  # type: ignore[misc]
            # Ignore curses errors (typically writing outside window bounds)
            pass

    def add_ch(self, y: int, x: int, ch: Any, attrs: int = 0) -> None:
        """Add character with error handling."""
        try:
            self._window.addch(y, x, ch, attrs)
        except Exception:  # type: ignore[misc]
            pass

    def get_max_yx(self) -> tuple[int, int]:
        """Get maximum coordinates."""
        return self._window.getmaxyx()


class MockBackend(RenderingBackend):
    """Mock rendering backend for testing."""

    def __init__(self, width: int = 80, height: int = 24) -> None:
        self.width = width
        self.height = height
        self.cursor_visible = True
        self.color_support = True
        self.input_queue: list[int] = []
        self.screen_buffer: list[list[str]] = [[" " for _ in range(width)] for _ in range(height)]
        self.attribute_buffer: list[list[int]] = [[0 for _ in range(width)] for _ in range(height)]

    def init(self) -> None:
        """Initialize mock backend."""
        # Set up text styles with mock values
        TextStyle.BOLD = 1
        TextStyle.UNDERLINE = 2
        TextStyle.REVERSE = 4
        TextStyle.BLINK = 8
        TextStyle.DIM = 16
        TextStyle.STANDOUT = 32

    def cleanup(self) -> None:
        """No cleanup needed for mock."""
        pass

    def get_screen_size(self) -> tuple[int, int]:
        """Return configured screen size."""
        return (self.height, self.width)

    def create_window(self, spec: WindowSpec) -> "MockWindow":
        """Create a mock window."""
        return MockWindow(self, spec)

    def refresh(self) -> None:
        """Mock refresh does nothing."""
        pass

    def get_input(self, timeout: int = -1) -> int:
        """Get input from queue."""
        if self.input_queue:
            return self.input_queue.pop(0)
        return -1

    def set_cursor_visible(self, visible: bool) -> None:
        """Set cursor visibility."""
        self.cursor_visible = visible

    def has_colors(self) -> bool:
        """Return color support."""
        return self.color_support

    def init_colors(self) -> None:
        """Mock color initialization."""
        pass

    def init_theme_colors(self, theme: Any) -> None:
        """Mock theme color initialization."""
        # For testing, we just store the theme reference
        # In a real implementation, this would set up color pairs
        self.current_theme: Any = theme

    def add_input(self, key: int) -> None:
        """Add input to the queue for testing."""
        self.input_queue.append(key)

    def get_text_at(self, y: int, x: int, length: int = 1) -> str:
        """Get text at position for testing."""
        if 0 <= y < self.height and 0 <= x < self.width:
            return "".join(self.screen_buffer[y][x : x + length])
        return ""


class MockWindow(Window):
    """Mock window for testing."""

    def __init__(self, backend: MockBackend, spec: WindowSpec) -> None:
        self.backend = backend
        self.spec = spec

    def clear(self) -> None:
        """Clear the window area."""
        for y in range(self.spec.y, min(self.spec.y + self.spec.height, self.backend.height)):
            for x in range(self.spec.x, min(self.spec.x + self.spec.width, self.backend.width)):
                self.backend.screen_buffer[y][x] = " "
                self.backend.attribute_buffer[y][x] = 0

    def refresh(self) -> None:
        """Mock refresh."""
        pass

    def get_size(self) -> tuple[int, int]:
        """Get window size."""
        return (self.spec.height, self.spec.width)

    def add_str(self, y: int, x: int, text: str, attrs: int = 0) -> None:
        """Add string to buffer."""
        abs_y = self.spec.y + y
        abs_x = self.spec.x + x

        for i, ch in enumerate(text):
            if 0 <= abs_y < self.backend.height and 0 <= abs_x + i < self.backend.width:
                self.backend.screen_buffer[abs_y][abs_x + i] = ch
                self.backend.attribute_buffer[abs_y][abs_x + i] = attrs

    def add_ch(self, y: int, x: int, ch: Any, attrs: int = 0) -> None:
        """Add character to buffer."""
        abs_y = self.spec.y + y
        abs_x = self.spec.x + x

        if 0 <= abs_y < self.backend.height and 0 <= abs_x < self.backend.width:
            # Handle special characters
            if isinstance(ch, int):
                # Map ncurses special chars to unicode
                char_map = {
                    ord("─"): "─",
                    ord("│"): "│",
                    ord("┌"): "┌",
                    ord("┐"): "┐",
                    ord("└"): "└",
                    ord("┘"): "┘",
                }
                ch = char_map.get(ch, chr(ch) if ch < 128 else "?")

            self.backend.screen_buffer[abs_y][abs_x] = str(ch)
            self.backend.attribute_buffer[abs_y][abs_x] = attrs

    def get_max_yx(self) -> tuple[int, int]:
        """Get maximum coordinates."""
        return (self.spec.height, self.spec.width)
