"""
Modern NCurses Framework for Hyper using Rendering Engine

Clean, optimized UI framework built on the rendering engine architecture.
Provides consistent, flicker-free rendering with proper state management.
"""

import curses
from typing import Optional, Callable, Any

from .engine import RenderEngine, UIComponent, RenderContext
from .components import ApplicationFrame


class ContentPanel(UIComponent):
    """Base class for content panels in the framework."""
    
    def __init__(self, title: str = ""):
        super().__init__()
        self.title = title
    
    def handle_input(self, key: int) -> Optional[str]:
        """Handle input - override in subclasses."""
        if key == ord('b') or key == ord('B'):
            return 'back'
        return None
    
    def get_size_hint(self) -> tuple[int, int]:
        """Content panels fill available space by default."""
        return (0, 0)
    
    def render_content(self, ctx: RenderContext) -> None:
        """Override to implement panel content rendering."""
        # Default: show title and help
        try:
            if self.title:
                ctx.window.addstr(
                    ctx.y + 1, ctx.x + 2,
                    self.title[:ctx.width - 4],
                    curses.A_BOLD
                )
            
            help_text = "Press 'b' to go back"
            ctx.window.addstr(
                ctx.y + ctx.height - 2, ctx.x + 2,
                help_text[:ctx.width - 4]
            )
        except curses.error:
            pass


class NCursesFramework:
    """
    Modern NCurses framework using the rendering engine.
    
    Provides optimized rendering with:
    - Automatic dirty checking and minimal redraws
    - Smooth double-buffered updates
    - Clean component lifecycle management
    - Event-driven architecture
    """
    
    def __init__(self, title: str = "HYPER INTERFACE", subtitle: str = ""):
        self.running = False
        self._render_engine: Optional[RenderEngine] = None
        
        # Create application frame with rendering engine
        self.app_frame = ApplicationFrame(title, subtitle)
        self.current_panel: Optional[ContentPanel] = None
        
        # Setup default behavior
        self._setup_defaults()
    
    def _setup_defaults(self) -> None:
        """Setup default menu items and behaviors."""
        self.add_menu_item('q', 'Quit', self._quit_action)
    
    def _quit_action(self) -> str:
        """Default quit action."""
        self.running = False
        return 'quit'
    
    def add_menu_item(self, key: str, label: str, action: Optional[Callable] = None) -> None:
        """Add a menu item to the application."""
        def wrapped_action():
            if action:
                result = action()
                if result == 'quit':
                    self.running = False
                return result
            return None
        
        self.app_frame.add_menu_item(key, label, wrapped_action)
    
    def set_panel(self, panel: ContentPanel) -> None:
        """Set the current content panel."""
        self.current_panel = panel
        if panel:
            self.app_frame.set_content(panel)
    
    def set_status(self, message: str, duration: float = 3.0) -> None:
        """Display a temporary status message."""
        self.app_frame.set_status_message(message, duration)
    
    def run(self) -> None:
        """Run the main application loop."""
        try:
            curses.wrapper(self._main_loop)
        except KeyboardInterrupt:
            pass
    
    def _main_loop(self, stdscr) -> None:
        """Main application loop with rendering engine."""
        # Create NCurses backend and setup with stdscr
        from .renderer import NCursesBackend
        backend = NCursesBackend()
        backend.setup(stdscr)
        
        # Initialize rendering engine
        self._render_engine = RenderEngine(backend)
        self._render_engine.set_root_component(self.app_frame)
        
        self.running = True
        
        while self.running:
            # Render frame (only if needed - engine handles optimization)
            self._render_engine.render_frame()
            
            # Handle input
            key = backend.get_input(50)  # 50ms timeout
            if key != -1:  # Only process actual input
                self._handle_input(key)
            
            # Sleep is handled by get_input timeout
    
    def _handle_input(self, key: int) -> None:
        """Handle keyboard input with priority system."""
        # Convert to character if possible
        try:
            key_char = chr(key).lower()
        except (ValueError, OverflowError):
            key_char = None
        
        # 1. Try application frame (handles global keys like 'q' and menu)
        if key_char:
            result = self.app_frame.handle_key(key_char)
            if result == 'quit':
                self.running = False
                return
        
        # 2. Try current panel
        if self.current_panel:
            result = self.current_panel.handle_input(key)
            if result == 'quit':
                self.running = False
            elif result == 'back':
                self._handle_back_navigation()
    
    def _handle_back_navigation(self) -> None:
        """Handle back navigation - can be overridden."""
        # Default: just clear the current panel
        self.set_panel(None)
    
    def get_performance_stats(self) -> dict:
        """Get rendering performance statistics."""
        if self._render_engine:
            return self._render_engine.get_performance_stats()
        return {}


# Configuration class for backward compatibility with CLI
class LayoutConfig:
    """Configuration for framework layout."""
    
    def __init__(self, title: str = "HYPER INTERFACE", subtitle: str = "", 
                 show_borders: bool = True, show_help: bool = True, theme=None):
        self.title = title
        self.subtitle = subtitle
        self.show_borders = show_borders
        self.show_help = show_help
        self.theme = theme


# Menu item for CLI compatibility
class MenuItem:
    """Menu item configuration."""
    
    def __init__(self, key: str, label: str, description: str, 
                 action: Optional[Callable] = None, enabled: bool = True):
        self.key = key
        self.label = label
        self.description = description
        self.action = action
        self.enabled = enabled