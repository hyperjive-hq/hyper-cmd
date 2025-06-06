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
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


@dataclass
class ThemeColors:
    """Color definitions for UI elements.
    
    Each color is defined as a tuple of (foreground, background) where:
    - Foreground/background values are curses color constants (COLOR_*)
    - Background of -1 means transparent/default terminal background
    
    These colors map to ncurses color pairs that are initialized when
    the theme is activated.
    """
    # Semantic colors for different states/purposes
    default: Tuple[int, int] = (curses.COLOR_WHITE, -1)
    primary: Tuple[int, int] = (curses.COLOR_GREEN, -1)
    secondary: Tuple[int, int] = (curses.COLOR_BLUE, -1)
    accent: Tuple[int, int] = (curses.COLOR_CYAN, -1)
    warning: Tuple[int, int] = (curses.COLOR_YELLOW, -1)
    error: Tuple[int, int] = (curses.COLOR_RED, -1)
    success: Tuple[int, int] = (curses.COLOR_GREEN, -1)
    info: Tuple[int, int] = (curses.COLOR_CYAN, -1)
    
    # UI element specific colors
    border: Tuple[int, int] = (curses.COLOR_GREEN, -1)
    header_bg: Tuple[int, int] = (curses.COLOR_BLACK, curses.COLOR_GREEN)
    selected: Tuple[int, int] = (curses.COLOR_BLACK, curses.COLOR_YELLOW)
    disabled: Tuple[int, int] = (curses.COLOR_RED, -1)
    
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
        }


@dataclass
class Theme:
    """Theme definition for Hyper Core UI.
    
    A theme encapsulates all color definitions and can be applied
    to change the appearance of the entire UI.
    """
    name: str
    description: str = ""
    colors: ThemeColors = field(default_factory=ThemeColors)
    
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
    
    def activate(self) -> None:
        """Activate this theme by initializing ncurses color pairs.
        
        This method should be called after curses.start_color() to
        set up all the color pairs defined by this theme.
        """
        if not curses.has_colors():
            return  # Terminal doesn't support colors
        
        colors_dict = self.colors.to_dict()
        
        for pair_id, color_name in self.COLOR_PAIR_MAPPING.items():
            if color_name in colors_dict:
                fg, bg = colors_dict[color_name]
                try:
                    curses.init_pair(pair_id, fg, bg)
                except curses.error:
                    # Ignore errors (e.g., invalid color values)
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
    
    @property
    def current_theme(self) -> Theme:
        """Get the currently active theme."""
        return self._themes[self._current_theme_name]
    
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
    
    def set_theme(self, name: str) -> None:
        """Set the active theme by name.
        
        Args:
            name: Name of the theme to activate
            
        Raises:
            KeyError: If theme name not found
        """
        if name not in self._themes:
            raise KeyError(f"Theme '{name}' not found. Available: {self.list_themes()}")
        
        self._current_theme_name = name
        # Activate the theme's colors
        self._themes[name].activate()
    
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