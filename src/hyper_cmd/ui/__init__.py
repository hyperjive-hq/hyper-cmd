"""UI framework components."""

from .components import ApplicationFrame, Header, MenuAlignment, MenuBar, StatusBar, Text
from .containers import BorderedContainer, FlexContainer
from .engine import RenderContext, RenderEngine, UIComponent
from .framework import ContentPanel, LayoutConfig, MenuItem, NCursesFramework
from .themes import DARK_THEME, DEFAULT_THEME, Theme, ThemeColors, ThemeManager
from .widgets import BaseWidget, WidgetSize

__all__ = [
    # Framework classes
    "ContentPanel",
    "LayoutConfig",
    "MenuItem",
    "NCursesFramework",
    # Components
    "ApplicationFrame",
    "Header",
    "StatusBar",
    "MenuBar",
    "Text",
    "MenuAlignment",
    # Containers
    "BorderedContainer",
    "FlexContainer",
    # Engine
    "RenderEngine",
    "UIComponent",
    "RenderContext",
    # Widget classes
    "BaseWidget",
    "WidgetSize",
    # Theme classes
    "DARK_THEME",
    "DEFAULT_THEME",
    "Theme",
    "ThemeColors",
    "ThemeManager",
]
