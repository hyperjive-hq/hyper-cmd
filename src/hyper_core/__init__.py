"""Hyper Core - A pluggable CLI framework.

This package provides the core framework for building plugin-based
CLI applications with ncurses UI support.
"""

__version__ = "0.1.0"

# Core protocols
from .protocols import (
    ICommand,
    IWidget,
    IPage,
    IService,
    IPlugin,
    IConfigurable,
    IDataProvider,
    IThemeable,
)

# Plugin system
from .plugins import (
    PluginRegistry,
    PluginMetadata,
    PluginDiscovery,
    PluginLoader,
    plugin_registry,
)

# Command framework
from .commands import (
    BaseCommand,
    CommandRegistry,
)

# UI framework
from .ui import (
    NCursesFramework,
    ContentPanel,
    MenuItem,
    MenuAlignment,
    LayoutConfig,
    BaseWidget,
    WidgetSize,
    Theme,
    ThemeColors,
    ThemeManager,
    DEFAULT_THEME,
    DARK_THEME,
)

# Container system
from .container import (
    SimpleContainer,
    BaseHyperContainer,
    create_container,
    configure_container,
)

__all__ = [
    # Version
    "__version__",
    
    # Protocols
    "ICommand",
    "IWidget",
    "IPage",
    "IService",
    "IPlugin",
    "IConfigurable",
    "IDataProvider",
    "IThemeable",
    
    # Plugin system
    "PluginRegistry",
    "PluginMetadata",
    "PluginDiscovery",
    "PluginLoader",
    "plugin_registry",
    
    # Commands
    "BaseCommand",
    "CommandRegistry",
    
    # UI Framework
    "NCursesFramework",
    "ContentPanel",
    "MenuItem",
    "MenuAlignment",
    "LayoutConfig",
    "BaseWidget",
    "WidgetSize",
    "Theme",
    "ThemeColors",
    "ThemeManager",
    "DEFAULT_THEME",
    "DARK_THEME",
    
    # Container
    "SimpleContainer",
    "BaseHyperContainer",
    "create_container",
    "configure_container",
]