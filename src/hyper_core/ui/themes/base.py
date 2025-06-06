"""Theme system for Hyper Core UI.

This module provides a simple but flexible theming system for ncurses-based
applications. Themes define color pairs and can be switched at runtime.

Example:
    Creating and using a custom theme::
    
        from hyper_core.ui.themes import Theme, ThemeColors
        
        # Create a custom theme
        dark_theme = Theme(
            name="dark",
            description="Dark mode theme",
            colors=ThemeColors(
                default=(curses.COLOR_WHITE, curses.COLOR_BLACK),
                primary=(curses.COLOR_CYAN, curses.COLOR_BLACK),
                error=(curses.COLOR_RED, curses.COLOR_BLACK),
                # ... other colors
            )
        )
        
        # Register and use the theme
        theme_manager = ThemeManager()
        theme_manager.register_theme(dark_theme)
        theme_manager.set_theme("dark")
"""

import curses
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Callable


class ThemeColors:
    """Color definitions for UI elements.
    
    Supports both RGB tuples (for testing/configuration) and curses color constants.
    RGB values are preserved for external access, curses values used internally.
    """
    
    def __init__(self, **kwargs):
        """Initialize theme colors with default values."""
        # Default values (curses colors)
        self._defaults = {
            'default': (curses.COLOR_WHITE, -1),
            'primary': (curses.COLOR_GREEN, -1),
            'secondary': (curses.COLOR_BLUE, -1),
            'accent': (curses.COLOR_CYAN, -1),
            'warning': (curses.COLOR_YELLOW, -1),
            'error': (curses.COLOR_RED, -1),
            'success': (curses.COLOR_GREEN, -1),
            'info': (curses.COLOR_CYAN, -1),
            'border': (curses.COLOR_GREEN, -1),
            'header_bg': (curses.COLOR_BLACK, curses.COLOR_GREEN),
            'selected': (curses.COLOR_BLACK, curses.COLOR_YELLOW),
            'disabled': (curses.COLOR_RED, -1),
            'background': (curses.COLOR_BLACK, -1),
            'text': (curses.COLOR_WHITE, -1)
        }
        
        # Initialize all attributes with defaults
        for key, default_value in self._defaults.items():
            setattr(self, key, default_value)
        
        # Override with provided values
        for key, value in kwargs.items():
            if key in self._defaults:
                setattr(self, key, value)
    
    def get_curses_colors(self) -> Dict[str, Tuple[int, int]]:
        """Get curses-compatible color pairs for terminal rendering."""
        result = {}
        for key in self._defaults:
            value = getattr(self, key)
            if isinstance(value, tuple) and len(value) == 3:
                # RGB tuple - convert to curses colors
                result[key] = self._rgb_to_curses(value)
            else:
                # Already curses colors
                result[key] = value
        return result
    
    def _rgb_to_curses(self, rgb: Tuple[int, int, int]) -> Tuple[int, int]:
        """Convert RGB tuple to curses color pair."""
        r, g, b = rgb
        
        # Simple mapping to closest curses color
        if r > 200 and g > 200 and b > 200:
            return (curses.COLOR_WHITE, -1)
        elif r < 50 and g < 50 and b < 50:
            return (curses.COLOR_BLACK, -1)
        elif r > g and r > b:
            return (curses.COLOR_RED, -1)
        elif g > r and g > b:
            return (curses.COLOR_GREEN, -1)
        elif b > r and b > g:
            return (curses.COLOR_BLUE, -1)
        elif r > 150 and g > 150:
            return (curses.COLOR_YELLOW, -1)
        elif r > 150 and b > 150:
            return (curses.COLOR_MAGENTA, -1)
        elif g > 150 and b > 150:
            return (curses.COLOR_CYAN, -1)
        else:
            return (curses.COLOR_WHITE, -1)
    
    def to_dict(self) -> Dict[str, Tuple[int, int]]:
        """Convert colors to a dictionary for easier access."""
        return {
            'default': self.default,
            'primary': self.primary,
            'secondary': self.secondary,
            'accent': self.accent,
            'warning': self.warning,
            'error': self.error,
            'success': self.success,
            'info': self.info,
            'border': self.border,
            'header_bg': self.header_bg,
            'selected': self.selected,
            'disabled': self.disabled,
            'background': self.background,
            'text': self.text,
        }


class Theme:
    """Theme definition for Hyper Core UI.
    
    A theme encapsulates all color definitions and can be applied
    to change the appearance of the entire UI.
    """
    
    def __init__(self, name: str, colors: ThemeColors = None, description: str = "", 
                 author: str = "", version: str = "1.0.0"):
        self.name = name
        self.description = description
        self.author = author
        self.version = version
        self.colors = colors if colors is not None else ThemeColors()
    
    # Color pair ID mapping - matches BaseWidget color constants
    COLOR_PAIR_MAPPING = {
        1: 'success',    # COLOR_SUCCESS
        2: 'info',       # COLOR_INFO
        3: 'warning',    # COLOR_WARNING
        4: 'accent',     # COLOR_ACCENT
        5: 'secondary',  # COLOR_SECONDARY
        6: 'error',      # COLOR_ERROR
        7: 'default',    # COLOR_DEFAULT (not used, 0 is default)
        # Extended pairs for UI elements
        10: 'header_bg',
        11: 'border',
        12: 'selected',
        13: 'disabled',
    }
    
    def activate(self, renderer_backend) -> None:
        """Activate this theme by initializing colors through the rendering backend.
        
        Args:
            renderer_backend: The rendering backend to use for color initialization.
                             Must implement init_theme_colors(theme) method.
        """
        # Delegate theme color initialization to the rendering backend
        try:
            renderer_backend.init_theme_colors(self)
        except (AttributeError, Exception):
            # Backend doesn't support theme color initialization or other error
            pass


# Pre-defined themes

DEFAULT_THEME = Theme(
    name="default",
    description="Default Hyper Core theme with green accents"
)

DARK_THEME = Theme(
    name="dark",
    description="Dark theme with muted colors",
    colors=ThemeColors(
        default=(curses.COLOR_WHITE, curses.COLOR_BLACK),
        primary=(curses.COLOR_CYAN, curses.COLOR_BLACK),
        secondary=(curses.COLOR_BLUE, curses.COLOR_BLACK),
        accent=(curses.COLOR_MAGENTA, curses.COLOR_BLACK),
        warning=(curses.COLOR_YELLOW, curses.COLOR_BLACK),
        error=(curses.COLOR_RED, curses.COLOR_BLACK),
        success=(curses.COLOR_GREEN, curses.COLOR_BLACK),
        info=(curses.COLOR_CYAN, curses.COLOR_BLACK),
        border=(curses.COLOR_WHITE, curses.COLOR_BLACK),
        header_bg=(curses.COLOR_BLACK, curses.COLOR_CYAN),
        selected=(curses.COLOR_BLACK, curses.COLOR_WHITE),
        disabled=(curses.COLOR_BLACK, curses.COLOR_BLACK),
    )
)


class ThemeManager:
    """Manages themes for the application.
    
    The ThemeManager is responsible for:
    - Storing available themes
    - Switching between themes
    - Activating theme colors in ncurses
    
    Example:
        manager = ThemeManager()
        manager.register_theme(my_custom_theme)
        manager.set_theme("my_custom")
    """
    
    def __init__(self):
        """Initialize with default themes."""
        self._themes: Dict[str, Theme] = {
            "default": DEFAULT_THEME,
            "dark": DARK_THEME,
        }
        self._current_theme_name = "default"
        self._callbacks: List[Callable] = []
    
    @property
    def current_theme(self) -> Theme:
        """Get the currently active theme."""
        return self._themes[self._current_theme_name]
    
    def get_current_theme(self) -> Theme:
        """Get the currently active theme (method version for compatibility)."""
        return self.current_theme
    
    def get_available_themes(self) -> List[str]:
        """Get a list of available theme names."""
        return self.list_themes()
    
    def add_theme_change_callback(self, callback: Callable) -> None:
        """Add a callback to be called when theme changes."""
        self._callbacks.append(callback)
    
    def register_theme(self, theme: Theme) -> None:
        """Register a new theme.
        
        Args:
            theme: Theme to register
            
        Raises:
            ValueError: If a theme with this name already exists
        """
        if theme.name in self._themes:
            raise ValueError(f"Theme '{theme.name}' already registered")
        self._themes[theme.name] = theme
    
    def set_theme(self, name: str, renderer_backend) -> None:
        """Set the active theme by name.
        
        Args:
            name: Name of the theme to activate
            renderer_backend: Rendering backend for color initialization
            
        Raises:
            KeyError: If theme name not found
        """
        if name not in self._themes:
            raise KeyError(f"Theme '{name}' not found. Available: {self.list_themes()}")
        
        old_theme = self._current_theme_name
        self._current_theme_name = name
        
        # Activate the theme's colors
        self._themes[name].activate(renderer_backend)
        
        # Call callbacks with theme objects
        for callback in self._callbacks:
            try:
                old_theme_obj = self._themes.get(old_theme)
                new_theme_obj = self._themes[name]
                callback(old_theme_obj, new_theme_obj)
            except Exception:
                pass  # Ignore callback errors
    
    def get_theme(self, name: str) -> Theme:
        """Get a theme by name.
        
        Args:
            name: Theme name to retrieve
            
        Returns:
            The requested theme
            
        Raises:
            KeyError: If theme not found
        """
        if name not in self._themes:
            raise KeyError(f"Theme '{name}' not found")
        return self._themes[name]
    
    def list_themes(self) -> List[str]:
        """Get a list of available theme names.
        
        Returns:
            List of registered theme names
        """
        return sorted(self._themes.keys())
    
    def theme_exists(self, name: str) -> bool:
        """Check if a theme is registered.
        
        Args:
            name: Theme name to check
            
        Returns:
            True if theme exists
        """
        return name in self._themes