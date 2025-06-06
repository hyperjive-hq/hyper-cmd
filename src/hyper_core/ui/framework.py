"""
Reusable NCurses Framework for Hyper Script
Provides a flexible layout system with menu navigation and content areas.
"""

import curses
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Optional, Callable, Any
from enum import Enum


class MenuAlignment(Enum):
    LEFT = "left"
    CENTER = "center"
    RIGHT = "right"


@dataclass
class MenuItem:
    """Represents a menu item"""
    key: str
    label: str
    description: str
    action: Optional[Callable] = None
    enabled: bool = True


@dataclass
class LayoutConfig:
    """Configuration for the ncurses layout"""
    title: str = "HYPER INTERFACE"
    subtitle: str = ""
    menu_alignment: MenuAlignment = MenuAlignment.CENTER
    show_borders: bool = True
    show_help: bool = True
    theme: Optional[Any] = None


class ContentPanel(ABC):
    """
    Abstract base class for content panels.
    
    Content panels are responsible for rendering and managing their own content
    within the main content area of the ncurses layout. Each panel operates
    independently and must handle its own state management.
    """
    
    def __init__(self):
        self._needs_refresh = True
        self._data = {}
        
    @abstractmethod
    def draw(self, win, height: int, width: int) -> None:
        """
        Draw the panel content.
        
        Args:
            win: NCurses window object for the content area
            height: Available height for content
            width: Available width for content
        """
        pass
        
    @abstractmethod
    def handle_input(self, key: int) -> Optional[str]:
        """
        Handle keyboard input.
        
        Args:
            key: The pressed key code
            
        Returns:
            Optional navigation command ('back', 'quit', etc.)
        """
        pass
        
    def refresh(self) -> None:
        """Mark the panel as needing refresh"""
        self._needs_refresh = True
        
    def needs_refresh(self) -> bool:
        """Check if the panel needs to be redrawn"""
        return self._needs_refresh
        
    def set_data(self, key: str, value: Any) -> None:
        """Set data for the panel"""
        self._data[key] = value
        self.refresh()


class NCursesFramework:
    """
    Main framework class that provides a reusable ncurses layout.
    
    Features:
    - Header with title and subtitle
    - Menu area with navigation options
    - Main content area for panels
    - Status bar with help text
    - Configurable theme support
    """
    
    def __init__(self, config: LayoutConfig):
        self.config = config
        self.menu_items: List[MenuItem] = []
        self.current_panel: Optional[ContentPanel] = None
        self.running = False
        self._status_message = ""
        self._status_time = 0
        
        # Initialize ncurses
        self.stdscr = None
        self.colors_initialized = False
        
    def add_menu_item(self, item: MenuItem) -> None:
        """Add a menu item to the framework"""
        self.menu_items.append(item)
        
    def set_panel(self, panel: ContentPanel) -> None:
        """Set the current content panel"""
        self.current_panel = panel
        if panel:
            panel.refresh()
            
    def set_status(self, message: str, duration: float = 3.0) -> None:
        """Display a temporary status message"""
        self._status_message = message
        self._status_time = time.time() + duration
        
    def run(self) -> None:
        """Run the main ncurses loop"""
        try:
            curses.wrapper(self._main_loop)
        except KeyboardInterrupt:
            pass
            
    def _main_loop(self, stdscr) -> None:
        """Main ncurses loop"""
        self.stdscr = stdscr
        self._setup_curses()
        
        self.running = True
        while self.running:
            self._draw_layout()
            
            # Handle input
            key = self.stdscr.getch()
            self._handle_input(key)
            
            # Small delay to prevent high CPU usage
            curses.napms(50)
            
    def _setup_curses(self) -> None:
        """Initialize curses settings"""
        curses.curs_set(0)  # Hide cursor
        self.stdscr.nodelay(True)  # Non-blocking input
        self.stdscr.keypad(True)  # Enable special keys
        
        # Initialize colors if available
        if curses.has_colors() and self.config.theme:
            curses.start_color()
            self.colors_initialized = True
            # Theme initialization would go here
            
    def _draw_layout(self) -> None:
        """Draw the complete layout"""
        height, width = self.stdscr.getmaxyx()
        self.stdscr.clear()
        
        # Draw header
        header_height = self._draw_header(height, width)
        
        # Draw menu
        menu_height = self._draw_menu(header_height, width)
        
        # Draw content area
        content_start = header_height + menu_height
        content_height = height - content_start - 2  # Leave room for status
        if content_height > 0 and self.current_panel:
            self._draw_content(content_start, content_height, width)
            
        # Draw status bar
        self._draw_status(height - 1, width)
        
        self.stdscr.refresh()
        
    def _draw_header(self, height: int, width: int) -> int:
        """Draw the header section"""
        lines_used = 0
        
        # Draw title
        if self.config.title:
            title = self.config.title[:width-2]
            x = (width - len(title)) // 2
            self.stdscr.addstr(lines_used, x, title, curses.A_BOLD)
            lines_used += 1
            
        # Draw subtitle
        if self.config.subtitle:
            subtitle = self.config.subtitle[:width-2]
            x = (width - len(subtitle)) // 2
            self.stdscr.addstr(lines_used, x, subtitle)
            lines_used += 1
            
        # Draw separator
        if lines_used > 0:
            self.stdscr.addstr(lines_used, 0, "─" * width)
            lines_used += 1
            
        return lines_used
        
    def _draw_menu(self, start_y: int, width: int) -> int:
        """Draw the menu section"""
        if not self.menu_items:
            return 0
            
        # Build menu string
        menu_parts = []
        for item in self.menu_items:
            if item.enabled:
                menu_parts.append(f"[{item.key}] {item.label}")
            else:
                menu_parts.append(f"[{item.key}] {item.label} (disabled)")
                
        menu_str = "  ".join(menu_parts)
        
        # Calculate position based on alignment
        if self.config.menu_alignment == MenuAlignment.CENTER:
            x = (width - len(menu_str)) // 2
        elif self.config.menu_alignment == MenuAlignment.RIGHT:
            x = width - len(menu_str) - 2
        else:
            x = 2
            
        # Draw menu
        self.stdscr.addstr(start_y, max(0, x), menu_str[:width])
        
        # Draw separator
        self.stdscr.addstr(start_y + 1, 0, "─" * width)
        
        return 2
        
    def _draw_content(self, start_y: int, height: int, width: int) -> None:
        """Draw the content area"""
        # Create a subwindow for content
        content_win = self.stdscr.subwin(height, width, start_y, 0)
        
        # Let the panel draw itself
        if self.current_panel and self.current_panel.needs_refresh():
            self.current_panel.draw(content_win, height, width)
            self.current_panel._needs_refresh = False
            
    def _draw_status(self, y: int, width: int) -> None:
        """Draw the status bar"""
        # Draw separator
        self.stdscr.addstr(y - 1, 0, "─" * width)
        
        # Show temporary status or help
        if self._status_message and time.time() < self._status_time:
            status = self._status_message
        elif self.config.show_help:
            status = "Press 'q' to quit | Use arrow keys to navigate"
        else:
            status = ""
            
        if status:
            self.stdscr.addstr(y, 2, status[:width-4])
            
    def _handle_input(self, key: int) -> None:
        """Handle keyboard input"""
        # Global keys
        if key == ord('q') or key == ord('Q'):
            self.running = False
            return
            
        # Check menu items
        for item in self.menu_items:
            if item.enabled and item.action and key == ord(item.key):
                result = item.action()
                if result == 'quit':
                    self.running = False
                return
                
        # Pass to current panel
        if self.current_panel:
            result = self.current_panel.handle_input(key)
            if result == 'quit':
                self.running = False
            elif result == 'back':
                # Handle navigation
                pass