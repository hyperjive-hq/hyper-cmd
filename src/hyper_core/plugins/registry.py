"""Plugin registry system for Hyper framework."""

import inspect
import logging
import sys
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Type, Union

from ..config import get_config
from ..protocols import ICommand, IPage, IService, IWidget

logger = logging.getLogger(__name__)


class PluginLifecycleHook(Enum):
    """Plugin lifecycle hooks."""
    
    BEFORE_LOAD = "before_load"
    BEFORE_ACTIVATE = "before_activate"
    BEFORE_UNLOAD = "before_unload"
    ON_ERROR = "on_error"


class PluginMetadata:
    """Metadata for a registered plugin."""
    
    def __init__(
        self,
        name: str,
        version: str,
        description: str = "",
        author: str = "",
        dependencies: Optional[List[str]] = None,
        config_schema: Optional[Dict[str, Any]] = None,
    ):
        self.name = name
        self.version = version
        self.description = description
        self.author = author
        self.dependencies = dependencies or []
        self.config_schema = config_schema or {}
        self.loaded = False
        self.module = None
        self.components: Dict[str, List[Type]] = {
            "commands": [],
            "widgets": [],
            "pages": [],
            "services": [],
        }


class PluginRegistry:
    """Central registry for managing Hyper plugins.
    
    This registry handles plugin discovery, loading, lifecycle management,
    and component registration (commands, widgets, pages, services).
    """
    
    def __init__(self):
        # Plugin metadata storage
        self._plugins: Dict[str, PluginMetadata] = {}
        
        # Component registries
        self._command_registry: Dict[str, Type[ICommand]] = {}
        self._widget_registry: Dict[str, Type[IWidget]] = {}
        self._page_registry: Dict[str, Type[IPage]] = {}
        self._service_registry: Dict[str, Type[IService]] = {}
        
        # Plugin configuration
        self._plugin_paths: Set[Path] = set()
        self._initialized = False
        
        # Lifecycle management
        self._lifecycle_hooks: Dict[PluginLifecycleHook, List[Callable]] = {
            hook: [] for hook in PluginLifecycleHook
        }
    
    @property
    def plugins(self) -> Dict[str, Dict[str, Any]]:
        """Get plugin information for integration.
        
        Returns:
            Dictionary mapping plugin names to plugin info
        """
        return {
            name: {
                'name': metadata.name,
                'version': metadata.version,
                'status': 'active' if metadata.loaded else 'inactive',
                'module': metadata.module,
                'components': metadata.components
            }
            for name, metadata in self._plugins.items()
        }
    
    def initialize(self, plugin_paths: Optional[List[Union[str, Path]]] = None, force_reinitialize: bool = False):
        """Initialize the registry with plugin search paths."""
        if self._initialized and not force_reinitialize:
            logger.warning("Plugin registry already initialized")
            return
        
        # Clear existing plugins when initializing to ensure replacement
        self._plugins.clear()
        self._command_registry.clear()
        self._widget_registry.clear()
        self._page_registry.clear()
        self._service_registry.clear()
        self._plugin_paths.clear()
        
        # Add .hyper/plugins directory if it exists - only use the first .hyper directory found
        config = get_config()
        if config.has_hyper_directory():
            hyper_plugins = config.get_plugins_directory()
            if hyper_plugins:
                self.add_plugin_path(hyper_plugins)
                # Only use additional plugin paths if specified, but not default paths
                if plugin_paths:
                    for path in plugin_paths:
                        self.add_plugin_path(path)
            else:
                # .hyper exists but no plugins directory - still don't use default paths
                if plugin_paths:
                    for path in plugin_paths:
                        self.add_plugin_path(path)
        else:
            # Add any additional plugin paths
            if plugin_paths:
                for path in plugin_paths:
                    self.add_plugin_path(path)
            
            # Add default paths only if no .hyper directory found
            default_paths = [
                Path.cwd() / "plugins",
                Path.home() / ".hyper" / "plugins"
            ]
            for path in default_paths:
                self.add_plugin_path(path)
        
        self._initialized = True
        logger.info(f"Plugin registry initialized with paths: {self._plugin_paths}")
    
    def add_plugin_path(self, path: Union[str, Path]):
        """Add a path to search for plugins."""
        path = Path(path).resolve()
        if path.exists() and path.is_dir():
            self._plugin_paths.add(path)
            logger.debug(f"Added plugin path: {path}")
        else:
            logger.warning(f"Plugin path does not exist or is not a directory: {path}")
    
    def discover_plugins(self) -> List[str]:
        """Discover available plugins in configured paths."""
        discovered = []
        
        for plugin_path in self._plugin_paths:
            # Import PluginDiscovery here to avoid circular import
            from .loader import PluginDiscovery
            discovery = PluginDiscovery(str(plugin_path))
            plugin_dirs = discovery.discover()
            
            for plugin_dir in plugin_dirs:
                plugin_name = plugin_dir.name
                # Always discover plugins, even if they exist (for replacement)
                discovered.append(plugin_name)
                logger.info(f"Discovered plugin: {plugin_name}")
        
        return discovered
    
    def load_plugin(self, plugin_name: str, reload: bool = False) -> bool:
        """Load a plugin by name."""
        try:
            # If plugin already exists, unload it first to ensure replacement
            if plugin_name in self._plugins:
                logger.info(f"Plugin '{plugin_name}' already loaded, unloading for replacement")
                self.unload_plugin(plugin_name)
            
            # Trigger lifecycle hook
            self._trigger_lifecycle_hook(PluginLifecycleHook.BEFORE_LOAD, plugin_name)
            
            # Find plugin directory
            plugin_dir = None
            for plugin_path in self._plugin_paths:
                potential_dir = plugin_path / plugin_name
                if potential_dir.exists() and potential_dir.is_dir():
                    plugin_dir = potential_dir
                    break
            
            if not plugin_dir:
                raise ValueError(f"Plugin '{plugin_name}' not found in any plugin path")
            
            # Load plugin
            from .loader import PluginLoader
            loader = PluginLoader()
            plugin_info = loader.load_plugin(str(plugin_dir))
            
            if not plugin_info:
                raise RuntimeError(f"Failed to load plugin from {plugin_dir}")
            
            # Create metadata
            metadata = PluginMetadata(
                name=plugin_info.get("name", plugin_name),
                version=plugin_info.get("version", "0.0.0"),
                description=plugin_info.get("description", ""),
                author=plugin_info.get("author", ""),
                dependencies=plugin_info.get("dependencies", []),
                config_schema=plugin_info.get("config_schema", {}),
            )
            
            # Get module
            module_name = f"hyper_plugins.{plugin_name}"
            if module_name not in sys.modules:
                raise RuntimeError(f"Plugin module {module_name} not loaded")
            
            metadata.module = sys.modules[module_name]
            metadata.loaded = True
            
            # Register components
            self._discover_and_register_components(metadata)
            
            # Store metadata
            self._plugins[plugin_name] = metadata
            
            logger.info(f"Successfully loaded plugin: {plugin_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load plugin '{plugin_name}': {e}")
            self._trigger_lifecycle_hook(PluginLifecycleHook.ON_ERROR, plugin_name, e)
            return False
    
    def unload_plugin(self, plugin_name: str) -> bool:
        """Unload a plugin and its components."""
        if plugin_name not in self._plugins:
            logger.warning(f"Plugin '{plugin_name}' not found")
            return False
        
        try:
            # Trigger lifecycle hook
            self._trigger_lifecycle_hook(PluginLifecycleHook.BEFORE_UNLOAD, plugin_name)
            
            metadata = self._plugins[plugin_name]
            
            # Unregister components
            self._unregister_plugin_components(metadata)
            
            # Remove from module cache
            module_name = f"hyper_plugins.{plugin_name}"
            if module_name in sys.modules:
                del sys.modules[module_name]
            
            # Remove metadata
            del self._plugins[plugin_name]
            
            logger.info(f"Successfully unloaded plugin: {plugin_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to unload plugin '{plugin_name}': {e}")
            self._trigger_lifecycle_hook(PluginLifecycleHook.ON_ERROR, plugin_name, e)
            return False
    
    def reload_plugins(self) -> bool:
        """Reload all plugins from the first .hyper directory found."""
        try:
            logger.info("Reloading plugins from .hyper directory")
            
            # Reinitialize to clear existing plugins and reload from .hyper directory
            self.initialize(force_reinitialize=True)
            
            # Discover and load all plugins
            discovered_plugins = self.discover_plugins()
            
            for plugin_name in discovered_plugins:
                self.load_plugin(plugin_name)
            
            logger.info(f"Successfully reloaded {len(discovered_plugins)} plugins")
            return True
            
        except Exception as e:
            logger.error(f"Failed to reload plugins: {e}")
            return False
    
    def activate_plugin(self, plugin_name: str) -> bool:
        """Activate a loaded plugin."""
        if plugin_name not in self._plugins:
            logger.warning(f"Plugin '{plugin_name}' not found")
            return False
        
        metadata = self._plugins[plugin_name]
        if not metadata.loaded:
            logger.warning(f"Plugin '{plugin_name}' not loaded")
            return False
        
        try:
            # Trigger lifecycle hook
            self._trigger_lifecycle_hook(PluginLifecycleHook.BEFORE_ACTIVATE, plugin_name)
            
            # Plugin is already activated when loaded
            logger.info(f"Plugin '{plugin_name}' activated")
            return True
            
        except Exception as e:
            logger.error(f"Failed to activate plugin '{plugin_name}': {e}")
            self._trigger_lifecycle_hook(PluginLifecycleHook.ON_ERROR, plugin_name, e)
            return False
    
    # Component registration methods
    
    def register_command(self, command_class: Type[ICommand], plugin_name: Optional[str] = None):
        """Register a command class."""
        name = self._get_component_name(command_class, "command")
        self._command_registry[name] = command_class
        
        if plugin_name and plugin_name in self._plugins:
            self._plugins[plugin_name].components["commands"].append(command_class)
        
        logger.debug(f"Registered command: {name}")
    
    def unregister_command(self, name: str):
        """Unregister a command."""
        if name in self._command_registry:
            del self._command_registry[name]
            logger.debug(f"Unregistered command: {name}")
    
    def get_command(self, name: str) -> Optional[Type[ICommand]]:
        """Get a command class by name."""
        return self._command_registry.get(name)
    
    def list_commands(self) -> List[str]:
        """List all registered command names."""
        return list(self._command_registry.keys())
    
    def get_commands_for_click(self) -> Dict[str, Type[ICommand]]:
        """Get all commands for Click integration."""
        return self._command_registry.copy()
    
    def get_commands_by_plugin(self) -> Dict[str, List[Type[ICommand]]]:
        """Get commands organized by plugin."""
        result = {}
        for plugin_name, metadata in self._plugins.items():
            if metadata.components["commands"]:
                result[plugin_name] = metadata.components["commands"]
        return result
    
    def register_widget(self, widget_class: Type[IWidget], plugin_name: Optional[str] = None):
        """Register a widget class."""
        name = self._get_component_name(widget_class, "widget")
        self._widget_registry[name] = widget_class
        
        if plugin_name and plugin_name in self._plugins:
            self._plugins[plugin_name].components["widgets"].append(widget_class)
        
        logger.debug(f"Registered widget: {name}")
    
    def unregister_widget(self, name: str):
        """Unregister a widget."""
        if name in self._widget_registry:
            del self._widget_registry[name]
            logger.debug(f"Unregistered widget: {name}")
    
    def get_widget(self, name: str) -> Optional[Type[IWidget]]:
        """Get a widget class by name."""
        return self._widget_registry.get(name)
    
    def list_widgets(self) -> List[str]:
        """List all registered widget names."""
        return list(self._widget_registry.keys())
    
    def register_page(self, page_class: Type[IPage], plugin_name: Optional[str] = None):
        """Register a page class."""
        name = self._get_component_name(page_class, "page")
        self._page_registry[name] = page_class
        
        if plugin_name and plugin_name in self._plugins:
            self._plugins[plugin_name].components["pages"].append(page_class)
        
        logger.debug(f"Registered page: {name}")
    
    def unregister_page(self, name: str):
        """Unregister a page."""
        if name in self._page_registry:
            del self._page_registry[name]
            logger.debug(f"Unregistered page: {name}")
    
    def get_page(self, name: str) -> Optional[Type[IPage]]:
        """Get a page class by name."""
        return self._page_registry.get(name)
    
    def list_pages(self) -> List[str]:
        """List all registered page names."""
        return list(self._page_registry.keys())
    
    def register_service(self, service_class: Type[IService], plugin_name: Optional[str] = None):
        """Register a service class."""
        name = self._get_component_name(service_class, "service")
        self._service_registry[name] = service_class
        
        if plugin_name and plugin_name in self._plugins:
            self._plugins[plugin_name].components["services"].append(service_class)
        
        logger.debug(f"Registered service: {name}")
    
    def unregister_service(self, name: str):
        """Unregister a service."""
        if name in self._service_registry:
            del self._service_registry[name]
            logger.debug(f"Unregistered service: {name}")
    
    def get_service(self, name: str) -> Optional[Type[IService]]:
        """Get a service class by name."""
        return self._service_registry.get(name)
    
    def list_services(self) -> List[str]:
        """List all registered service names."""
        return list(self._service_registry.keys())
    
    # Lifecycle hook management
    
    def register_lifecycle_hook(self, hook: PluginLifecycleHook, callback: Callable):
        """Register a lifecycle hook callback."""
        self._lifecycle_hooks[hook].append(callback)
        logger.debug(f"Registered lifecycle hook: {hook.value}")
    
    def unregister_lifecycle_hook(self, hook: PluginLifecycleHook, callback: Callable):
        """Unregister a lifecycle hook callback."""
        if callback in self._lifecycle_hooks[hook]:
            self._lifecycle_hooks[hook].remove(callback)
            logger.debug(f"Unregistered lifecycle hook: {hook.value}")
    
    # Private helper methods
    
    def _discover_and_register_components(self, metadata: PluginMetadata):
        """Discover and register all components in a plugin module."""
        if not metadata.module:
            return
        
        plugin_name = metadata.name
        
        # Discover components by inspecting module
        for name, obj in inspect.getmembers(metadata.module):
            if inspect.isclass(obj):
                # Check if it's a command
                if self._is_command(obj) and obj.__module__.startswith(f"hyper_plugins.{plugin_name}"):
                    self.register_command(obj, plugin_name)
                
                # Check if it's a widget
                elif self._is_widget(obj) and obj.__module__.startswith(f"hyper_plugins.{plugin_name}"):
                    self.register_widget(obj, plugin_name)
                
                # Check if it's a page
                elif self._is_page(obj) and obj.__module__.startswith(f"hyper_plugins.{plugin_name}"):
                    self.register_page(obj, plugin_name)
                
                # Check if it's a service
                elif self._is_service(obj) and obj.__module__.startswith(f"hyper_plugins.{plugin_name}"):
                    self.register_service(obj, plugin_name)
    
    def _unregister_plugin_components(self, metadata: PluginMetadata):
        """Unregister all components from a plugin."""
        # Unregister commands
        for cmd_class in metadata.components["commands"]:
            name = self._get_component_name(cmd_class, "command")
            self.unregister_command(name)
        
        # Unregister widgets
        for widget_class in metadata.components["widgets"]:
            name = self._get_component_name(widget_class, "widget")
            self.unregister_widget(name)
        
        # Unregister pages
        for page_class in metadata.components["pages"]:
            name = self._get_component_name(page_class, "page")
            self.unregister_page(name)
        
        # Unregister services
        for service_class in metadata.components["services"]:
            name = self._get_component_name(service_class, "service")
            self.unregister_service(name)
    
    def _get_component_name(self, component_class: Type, component_type: str) -> str:
        """Extract name from a component class."""
        # Try to get name from property or attribute
        if hasattr(component_class, 'name'):
            try:
                # Check if it's a property
                name_attr = getattr(component_class, 'name')
                if isinstance(name_attr, property):
                    # Can't call property without instance, use class name
                    return component_class.__name__.lower().replace(component_type, '')
                else:
                    return name_attr
            except:
                pass
        
        # Fallback to class name
        return component_class.__name__.lower().replace(component_type, '')
    
    def _is_command(self, obj: Any) -> bool:
        """Check if an object is a command using duck typing."""
        required_attrs = ['name', 'description', 'help_text', 'execute', 'run']
        return all(hasattr(obj, attr) for attr in required_attrs)
    
    def _is_widget(self, obj: Any) -> bool:
        """Check if an object is a widget using duck typing."""
        required_attrs = ['title', 'draw', 'refresh_data', 'get_minimum_size', 
                         'handle_input', 'handle_mouse', 'on_resize']
        return all(hasattr(obj, attr) for attr in required_attrs)
    
    def _is_page(self, obj: Any) -> bool:
        """Check if an object is a page using duck typing."""
        required_attrs = ['title', 'description', 'draw', 'handle_input', 
                         'refresh', 'on_enter', 'on_exit']
        return all(hasattr(obj, attr) for attr in required_attrs)
    
    def _is_service(self, obj: Any) -> bool:
        """Check if an object is a service using duck typing."""
        required_attrs = ['name', 'is_initialized', 'initialize', 'shutdown',
                         'health_check', 'get_status']
        return all(hasattr(obj, attr) for attr in required_attrs)
    
    def _trigger_lifecycle_hook(self, hook: PluginLifecycleHook, plugin_name: str, *args):
        """Trigger all callbacks for a lifecycle hook."""
        for callback in self._lifecycle_hooks[hook]:
            try:
                callback(plugin_name, *args)
            except Exception as e:
                logger.error(f"Error in lifecycle hook {hook.value}: {e}")


# Global plugin registry instance
plugin_registry = PluginRegistry()