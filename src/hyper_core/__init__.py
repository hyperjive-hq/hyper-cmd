"""Hyper Core - A pluggable CLI framework.

This package provides the core framework for building plugin-based
CLI applications with ncurses UI support.
"""

__version__ = "0.1.0"

# Core protocols
# Command framework
from .commands import (
    BaseCommand,
    CommandRegistry,
    InitCommand,
)

# Configuration system
from .config import (
    HyperConfig,
    find_hyper_directory,
    get_config,
    reset_config,
)

# Container system
from .container import (
    BaseHyperContainer,
    SimpleContainer,
    configure_container,
    create_container,
)

# Plugin system
from .plugins import (
    PluginDiscovery,
    PluginLoader,
    PluginMetadata,
    PluginRegistry,
    plugin_registry,
)
from .protocols import (
    ICommand,
    IConfigurable,
    IDataProvider,
    IPage,
    IPlugin,
    IService,
    IThemeable,
    IWidget,
)

# UI framework
from .ui import (
    DARK_THEME,
    DEFAULT_THEME,
    BaseWidget,
    ContentPanel,
    LayoutConfig,
    MenuItem,
    NCursesFramework,
    Theme,
    ThemeColors,
    ThemeManager,
    WidgetSize,
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
    "InitCommand",
    # UI Framework
    "NCursesFramework",
    "ContentPanel",
    "MenuItem",
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
    # Configuration
    "HyperConfig",
    "get_config",
    "reset_config",
    "find_hyper_directory",
]
