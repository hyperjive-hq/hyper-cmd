"""Plugin system for Hyper framework."""

from .loader import PluginDiscovery, PluginLoader
from .registry import PluginMetadata, PluginRegistry, plugin_registry

__all__ = [
    "PluginMetadata",
    "PluginRegistry",
    "plugin_registry",
    "PluginDiscovery",
    "PluginLoader",
]
