"""Base widget class for Hyper UI components.

This module provides the base class for all widgets in the Hyper UI framework.
Widgets are reusable UI components that can be placed in dashboards, pages,
and other containers.

Example:
    Creating a simple status widget::

        from hyper_core.ui.widgets import BaseWidget, WidgetSize

        class StatusWidget(BaseWidget):
            def __init__(self):
                super().__init__(title="System Status", size=WidgetSize.SMALL)
                self.status = "OK"

            def draw_content(self, stdscr, x, y, width, height):
                # Draw status in the center
                status_text = f"Status: {self.status}"
                center_y = y + height // 2
                center_x = x + (width - len(status_text)) // 2

                color = self.COLOR_SUCCESS if self.status == "OK" else self.COLOR_ERROR
                stdscr.addstr(center_y, center_x, status_text, curses.color_pair(color))

            def refresh_data(self):
                # Update status from some data source
                self.status = get_system_status()
                self.needs_redraw = True
"""

import curses
import logging
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Optional

from ...protocols import IWidget

logger = logging.getLogger(__name__)


class WidgetSize(Enum):
    """Widget size hints for layout engines.

    These sizes help layout managers determine how to arrange widgets
    in a grid or column layout.
    """

    SMALL = 1  # Minimal width (e.g., 1/3 of screen)
    MEDIUM = 2  # Medium width (e.g., 2/3 of screen)
    LARGE = 3  # Full width


class BaseWidget(ABC, IWidget):
    """Abstract base class for all Hyper widgets.

    This class provides common functionality for widgets including:
    - Border drawing and title display
    - Error handling and display
    - Redraw optimization
    - Standard color scheme
    - Mouse and keyboard input handling

    Subclasses must implement:
    - draw_content(): To render the widget's content
    - get_minimum_size(): To specify minimum dimensions

    Subclasses may override:
    - refresh_data(): To update data from sources
    - handle_input(): To process keyboard input
    - handle_mouse(): To process mouse events
    """

    # Standard ncurses color pair IDs
    # These should be initialized by the application using curses.init_pair()
    COLOR_DEFAULT = 0  # Default terminal colors
    COLOR_SUCCESS = 1  # Green - for success/active states
    COLOR_INFO = 2  # Cyan - for informational text
    COLOR_WARNING = 3  # Yellow - for warnings
    COLOR_ACCENT = 4  # Magenta - for emphasis
    COLOR_SECONDARY = 5  # Blue - for secondary elements
    COLOR_ERROR = 6  # Red - for errors/stopped states
    COLOR_HIGHLIGHT = 7  # For highlighted/selected items

    def __init__(self, title: str = "", size: WidgetSize = WidgetSize.SMALL):
        """Initialize the widget.

        Args:
            title: Title to display in the widget border
            size: Size hint for layout managers
        """
        self._title = title
        self.size = size

        # State management
        self._needs_redraw = True
        self._last_dimensions = (0, 0, 0, 0)
        self._error_message: Optional[str] = None

        # Data storage for subclasses
        self.data: Any = None

    @property
    def title(self) -> str:
        """Get the widget title."""
        return self._title

    @title.setter
    def title(self, value: str) -> None:
        """Set the widget title and mark for redraw."""
        self._title = value
        self._needs_redraw = True

    # Main drawing method (template pattern)

    def draw(self, stdscr: Any, x: int, y: int, width: int, height: int) -> None:
        """Draw the widget at the specified position.

        This method implements the template pattern for widget drawing:
        1. Check if redraw is needed
        2. Clear the widget area
        3. Draw border and title
        4. Draw content or error message
        5. Mark as drawn

        Args:
            stdscr: The curses window object
            x: X coordinate of the top-left corner
            y: Y coordinate of the top-left corner
            width: Total width available for the widget
            height: Total height available for the widget
        """
        # Skip if no redraw needed
        if not self._should_redraw(x, y, width, height):
            return

        # Ensure dimensions are valid
        if width < 3 or height < 3:
            return  # Too small to draw anything meaningful

        # Clear and draw frame
        self._clear_area(stdscr, x, y, width, height)
        self._draw_frame(stdscr, x, y, width, height)

        # Calculate content area (inside borders)
        content_x = x + 1
        content_y = y + 1
        content_width = width - 2
        content_height = height - 2

        # Draw content or error
        if self._error_message:
            self._draw_error(stdscr, content_x, content_y, content_width, content_height)
        else:
            try:
                self.draw_content(stdscr, content_x, content_y, content_width, content_height)
            except Exception as e:
                logger.exception(f"Error drawing widget '{self.title}'")
                self.set_error(f"Draw error: {str(e)}")
                self._draw_error(stdscr, content_x, content_y, content_width, content_height)

        # Mark as drawn
        self._mark_drawn(x, y, width, height)

    @abstractmethod
    def draw_content(self, stdscr: Any, x: int, y: int, width: int, height: int) -> None:
        """Draw the widget's content area.

        This method must be implemented by subclasses to render their
        specific content. The coordinates provided are for the content
        area inside the widget's border.

        Args:
            stdscr: The curses window object
            x: X coordinate of content area (inside border)
            y: Y coordinate of content area (inside border)
            width: Width of content area
            height: Height of content area
        """
        pass

    # IWidget protocol methods

    def refresh_data(self) -> None:
        """Update the widget's data from its source.

        Subclasses should override this to fetch new data and call
        mark_for_redraw() if the display needs updating.
        """
        pass  # Default implementation does nothing

    def get_minimum_size(self) -> tuple[int, int]:
        """Get the minimum dimensions required for this widget.

        Returns:
            Tuple of (min_width, min_height) in characters
        """
        # Default: enough for border + title + one line of content
        min_width = max(20, len(self.title) + 4)
        min_height = 5
        return (min_width, min_height)

    def handle_input(self, key: int) -> bool:
        """Process keyboard input when this widget has focus.

        Args:
            key: The key code pressed

        Returns:
            True if the input was handled, False to pass to parent
        """
        return False  # Default: don't handle any input

    def handle_mouse(self, mx: int, my: int, bstate: int, widget_x: int, widget_y: int) -> bool:
        """Process mouse events for this widget.

        Args:
            mx: Mouse X coordinate (absolute screen position)
            my: Mouse Y coordinate (absolute screen position)
            bstate: Mouse button state flags from curses
            widget_x: Widget's X position on screen
            widget_y: Widget's Y position on screen

        Returns:
            True if the event was handled, False to pass to parent
        """
        return False  # Default: don't handle mouse events

    def on_resize(self, width: int, height: int) -> None:
        """Handle terminal resize events.

        Args:
            width: New terminal width in characters
            height: New terminal height in lines
        """
        self.mark_for_redraw()

    # Public utility methods

    def mark_for_redraw(self) -> None:
        """Mark this widget as needing to be redrawn."""
        self._needs_redraw = True

    def set_error(self, message: str) -> None:
        """Set an error message to be displayed instead of content.

        Args:
            message: Error message to display
        """
        self._error_message = message
        self.mark_for_redraw()

    def clear_error(self) -> None:
        """Clear any error message and return to normal display."""
        self._error_message = None
        self.mark_for_redraw()

    def has_error(self) -> bool:
        """Check if the widget is in an error state.

        Returns:
            True if an error message is set
        """
        return self._error_message is not None

    # Private helper methods

    def _should_redraw(self, x: int, y: int, width: int, height: int) -> bool:
        """Check if the widget needs to be redrawn."""
        dimensions = (x, y, width, height)
        return self._needs_redraw or dimensions != self._last_dimensions

    def _mark_drawn(self, x: int, y: int, width: int, height: int) -> None:
        """Mark the widget as having been drawn."""
        self._needs_redraw = False
        self._last_dimensions = (x, y, width, height)

    def _clear_area(self, stdscr: Any, x: int, y: int, width: int, height: int) -> None:
        """Clear the widget area."""
        try:
            for row in range(height):
                if y + row < curses.LINES:
                    # Move to start of row and clear to end of line
                    stdscr.move(y + row, x)
                    stdscr.clrtoeol()
        except curses.error:
            pass  # Ignore errors near screen edges

    def _draw_frame(self, stdscr: Any, x: int, y: int, width: int, height: int) -> None:
        """Draw the widget border and title."""
        try:
            # Draw corners
            stdscr.addch(y, x, curses.ACS_ULCORNER)
            stdscr.addch(y, x + width - 1, curses.ACS_URCORNER)
            stdscr.addch(y + height - 1, x, curses.ACS_LLCORNER)
            stdscr.addch(y + height - 1, x + width - 1, curses.ACS_LRCORNER)

            # Draw horizontal lines
            for i in range(1, width - 1):
                stdscr.addch(y, x + i, curses.ACS_HLINE)
                stdscr.addch(y + height - 1, x + i, curses.ACS_HLINE)

            # Draw vertical lines
            for i in range(1, height - 1):
                stdscr.addch(y + i, x, curses.ACS_VLINE)
                stdscr.addch(y + i, x + width - 1, curses.ACS_VLINE)

            # Draw title if present
            if self.title:
                title_str = f" {self.title} "
                if len(title_str) <= width - 4:
                    title_x = x + (width - len(title_str)) // 2
                    stdscr.addstr(y, title_x, title_str)
        except curses.error:
            pass  # Ignore errors near screen edges

    def _draw_error(self, stdscr: Any, x: int, y: int, width: int, height: int) -> None:
        """Draw error message in the content area."""
        if not self._error_message:
            return

        try:
            # Split error message into lines
            words = self._error_message.split()
            lines = []
            current_line = []

            for word in words:
                if sum(len(w) + 1 for w in current_line) + len(word) <= width:
                    current_line.append(word)
                else:
                    if current_line:
                        lines.append(" ".join(current_line))
                    current_line = [word]

            if current_line:
                lines.append(" ".join(current_line))

            # Center the error message vertically
            start_y = y + max(0, (height - len(lines)) // 2)

            # Draw each line centered horizontally
            for i, line in enumerate(lines[:height]):
                line_y = start_y + i
                if line_y < y + height:
                    # Truncate if too long
                    if len(line) > width:
                        line = line[: width - 3] + "..."

                    line_x = x + (width - len(line)) // 2
                    stdscr.addstr(line_y, line_x, line, curses.color_pair(self.COLOR_ERROR))
        except curses.error:
            pass  # Ignore errors near screen edges
