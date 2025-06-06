# Hyper Core Plugin Development Guide

This guide explains how to develop plugins for the Hyper Core framework, including plugin structure, available APIs, and best practices.

## Overview

Plugins extend Hyper Core functionality by providing:
- **Commands**: CLI commands for user interaction
- **Widgets**: UI components for dashboard interfaces
- **Pages**: Full-screen views in the menu system
- **Services**: Background services and utilities

## Plugin Structure

### Basic Plugin Package

Every plugin must be structured as a Python package:

```
my_plugin/
├── __init__.py          # Required: Makes it a Python package
├── plugin.py            # Required: Main plugin module
├── plugin.yaml          # Optional: Plugin metadata
├── commands/            # Optional: Command modules
│   ├── __init__.py
│   └── my_command.py
├── widgets/             # Optional: Widget modules
│   ├── __init__.py
│   └── my_widget.py
└── services/            # Optional: Service modules
    ├── __init__.py
    └── my_service.py
```

### Plugin Discovery

The framework searches for plugins in these locations:
- `./plugins/` (current directory)
- `~/.hyper/plugins/` (user home directory)
- Custom paths via `PluginLoader.add_search_path()`

### Plugin Metadata

Define plugin metadata in `plugin.py`:

```python
# plugin.py
PLUGIN_NAME = "my_plugin"
PLUGIN_VERSION = "1.0.0"
PLUGIN_DESCRIPTION = "My awesome plugin"
PLUGIN_AUTHOR = "Your Name"
PLUGIN_DEPENDENCIES = ["requests", "pyyaml"]  # Optional Python dependencies
```

Alternatively, use a `plugin.yaml` file:

```yaml
# plugin.yaml
name: my_plugin
version: 1.0.0
description: My awesome plugin
author: Your Name
dependencies:
  - requests
  - pyyaml
entry_points:
  commands:
    - MyCommand
  widgets:
    - MyWidget
  services:
    - MyService
```

## Creating Commands

Commands are the primary way users interact with your plugin functionality.

### Basic Command

```python
# plugin.py or commands/my_command.py
from hyper_core.commands import BaseCommand

class MyCommand(BaseCommand):
    """A simple example command."""
    
    @property
    def name(self) -> str:
        return "my-command"
    
    @property
    def description(self) -> str:
        return "Does something awesome"
    
    @property
    def help_text(self) -> str:
        return """
        Usage: my-command [options]
        
        This command demonstrates basic plugin functionality.
        
        Options:
            --verbose    Enable verbose output
            --config     Configuration file path
        """
    
    def execute(self, verbose: bool = False, config: str = None) -> int:
        """Execute the command logic."""
        if verbose:
            self.print_info("Running in verbose mode")
        
        if config:
            self.print_info(f"Using config file: {config}")
        
        # Your command logic here
        with self.show_progress("Processing", total=100) as (progress, task):
            for i in range(100):
                # Do work
                progress.update(task, advance=1)
        
        self.print_success("Command completed successfully!")
        return 0
```

### Advanced Command Features

#### Using Dependency Injection

```python
from rich.console import Console
from hyper_core.commands import BaseCommand

class AdvancedCommand(BaseCommand):
    def __init__(self, container):
        super().__init__(container)
        # Access injected services
        self.my_service = container.get(MyService)
    
    def execute(self) -> int:
        result = self.my_service.do_something()
        self.console.print(f"Result: {result}")
        return 0
```

#### Input Validation and Error Handling

```python
class ValidatedCommand(BaseCommand):
    def execute(self, port: str, directory: str) -> int:
        # Validate port
        if not self.validate_port(port):
            self.print_error(f"Invalid port: {port}")
            return 1
        
        # Validate directory
        dir_path = Path(directory)
        if not self.validate_path(dir_path, must_exist=True, must_be_dir=True):
            return 1
        
        # Check if port is available
        port_num = int(port)
        if not self.check_port_available(port_num):
            self.print_error(f"Port {port_num} is already in use")
            return 1
        
        # Command logic here
        return 0
```

## Creating Widgets

Widgets provide visual components for terminal-based dashboard interfaces.

### Basic Widget

```python
# widgets/my_widget.py
from hyper_core.ui import BaseWidget, WidgetSize
from hyper_core.protocols import IWidget
import curses

class StatusWidget(BaseWidget):
    """Displays system status information."""
    
    def __init__(self, data_provider=None):
        super().__init__(
            title="System Status",
            size=WidgetSize.MEDIUM
        )
        self.data_provider = data_provider
        self.status_data = {"cpu": 0, "memory": 0, "disk": 0}
    
    def refresh_data(self) -> None:
        """Update widget data from data source."""
        if self.data_provider:
            self.status_data = self.data_provider.get_system_status()
    
    def draw_content(self, stdscr, x: int, y: int, width: int, height: int) -> None:
        """Render the widget content."""
        try:
            # Draw status information
            stdscr.addstr(y + 1, x + 2, f"CPU: {self.status_data['cpu']:.1f}%")
            stdscr.addstr(y + 2, x + 2, f"Memory: {self.status_data['memory']:.1f}%")
            stdscr.addstr(y + 3, x + 2, f"Disk: {self.status_data['disk']:.1f}%")
            
            # Color coding based on values
            for i, (key, value) in enumerate(self.status_data.items()):
                color = curses.COLOR_GREEN if value < 70 else \
                       curses.COLOR_YELLOW if value < 90 else curses.COLOR_RED
                stdscr.addstr(y + 1 + i, x + 2, f"{key.upper()}: ", 
                             curses.color_pair(1))
                stdscr.addstr(f"{value:.1f}%", curses.color_pair(color))
                
        except curses.error:
            # Handle terminal size issues gracefully
            pass
    
    def handle_input(self, key: int) -> bool:
        """Handle keyboard input when widget has focus."""
        if key == ord('r') or key == ord('R'):
            self.refresh_data()
            return True
        return False
    
    def get_minimum_size(self) -> tuple[int, int]:
        """Return minimum widget dimensions."""
        return (20, 6)  # width, height
```

### Interactive Widget

```python
class MenuWidget(BaseWidget):
    """Interactive menu widget with selection."""
    
    def __init__(self, items: list[str]):
        super().__init__(title="Menu", size=WidgetSize.MEDIUM)
        self.items = items
        self.selected_index = 0
    
    def handle_input(self, key: int) -> bool:
        """Handle navigation and selection."""
        if key == curses.KEY_UP and self.selected_index > 0:
            self.selected_index -= 1
            return True
        elif key == curses.KEY_DOWN and self.selected_index < len(self.items) - 1:
            self.selected_index += 1
            return True
        elif key == ord('\n'):  # Enter key
            self._on_item_selected(self.selected_index)
            return True
        return False
    
    def draw_content(self, stdscr, x: int, y: int, width: int, height: int) -> None:
        """Draw menu items with selection highlight."""
        for i, item in enumerate(self.items):
            if i >= height - 2:  # Don't exceed widget height
                break
            
            attrs = curses.A_REVERSE if i == self.selected_index else curses.A_NORMAL
            stdscr.addstr(y + 1 + i, x + 2, item[:width-4], attrs)
    
    def _on_item_selected(self, index: int) -> None:
        """Handle item selection - override in subclasses."""
        pass
```

## Creating Services

Services provide background functionality and shared resources.

### Basic Service

```python
# services/my_service.py
from hyper_core.protocols import IService
from typing import Dict, Any, Optional
import time

class DataProcessingService(IService):
    """Service for processing data in the background."""
    
    def __init__(self):
        self._initialized = False
        self._config = {}
        self._data_cache = {}
    
    @property
    def name(self) -> str:
        return "data_processing"
    
    @property
    def is_initialized(self) -> bool:
        return self._initialized
    
    def initialize(self, config: Optional[Dict[str, Any]] = None) -> None:
        """Initialize the service."""
        if self._initialized:
            return
        
        self._config = config or {}
        # Setup service resources
        self._setup_data_sources()
        self._initialized = True
    
    def shutdown(self) -> None:
        """Cleanup service resources."""
        self._data_cache.clear()
        self._initialized = False
    
    def health_check(self) -> Dict[str, Any]:
        """Perform health check."""
        return {
            'service': self.name,
            'healthy': self._initialized and self._check_data_sources(),
            'timestamp': time.time(),
            'cache_size': len(self._data_cache),
            'config': self._config
        }
    
    def get_status(self) -> Dict[str, Any]:
        """Get detailed status."""
        return {
            'service': self.name,
            'initialized': self._initialized,
            'timestamp': time.time(),
            'cache_entries': len(self._data_cache),
            'last_update': self._get_last_update_time()
        }
    
    # Service-specific methods
    def process_data(self, data: Any) -> Any:
        """Process data using service logic."""
        if not self._initialized:
            raise RuntimeError("Service not initialized")
        
        # Implementation here
        processed = self._transform_data(data)
        self._cache_result(data, processed)
        return processed
    
    def _setup_data_sources(self) -> None:
        """Setup internal data sources."""
        pass
    
    def _check_data_sources(self) -> bool:
        """Check if data sources are available."""
        return True
    
    def _transform_data(self, data: Any) -> Any:
        """Transform data logic."""
        return data
    
    def _cache_result(self, key: Any, result: Any) -> None:
        """Cache processing result."""
        self._data_cache[str(key)] = result
    
    def _get_last_update_time(self) -> float:
        """Get last update timestamp."""
        return time.time()
```

## Plugin Registration

### Manual Registration

```python
# plugin.py
from .commands.my_command import MyCommand
from .widgets.my_widget import StatusWidget
from .services.my_service import DataProcessingService

def register_plugin(container):
    """Register plugin components with the container."""
    # Register services
    service = DataProcessingService()
    container.register(DataProcessingService, service)
    
    # Commands and widgets are typically registered by the framework
    return {
        'commands': [MyCommand],
        'widgets': [StatusWidget],
        'services': [DataProcessingService]
    }
```

### IPlugin Interface

For advanced plugins, implement the `IPlugin` interface:

```python
from hyper_core.protocols import IPlugin
from typing import Dict, List, Any

class MyPlugin(IPlugin):
    """Full plugin implementation with IPlugin interface."""
    
    @property
    def name(self) -> str:
        return "my_plugin"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    @property
    def description(self) -> str:
        return "My awesome plugin with full interface"
    
    def initialize(self, container: Any) -> None:
        """Initialize plugin with container access."""
        self.container = container
        # Setup plugin resources
        self._register_services()
    
    def register(self) -> Dict[str, List[Any]]:
        """Register all plugin components."""
        return {
            'commands': [MyCommand, AnotherCommand],
            'widgets': [StatusWidget, MenuWidget],
            'pages': [SettingsPage],
            'services': [DataProcessingService]
        }
    
    def shutdown(self) -> None:
        """Cleanup plugin resources."""
        # Cleanup logic here
        pass
    
    def _register_services(self) -> None:
        """Register services with the container."""
        service = DataProcessingService()
        self.container.register(DataProcessingService, service)
```

## Framework APIs

### Container Access

The framework provides dependency injection through containers:

```python
class MyCommand(BaseCommand):
    def __init__(self, container):
        super().__init__(container)
        
        # Get required services
        self.console = container.get(Console)
        self.my_service = container.get(MyService)
        
        # Get optional services
        optional_service = container.get_optional(OptionalService)
        if optional_service:
            self.use_optional_feature(optional_service)
```

### UI Rendering System

The framework provides a modern rendering engine:

```python
from hyper_core.ui.engine import UIComponent, RenderContext

class CustomComponent(UIComponent):
    def render(self, ctx: RenderContext) -> None:
        """Render component content."""
        # The framework handles dirty checking and optimization
        ctx.window.addstr(ctx.y, ctx.x, "Custom content")
    
    def get_size_hint(self) -> tuple[int, int]:
        """Return preferred size (width, height)."""
        return (40, 10)
```

### Theme Support

Make components themeable:

```python
from hyper_core.protocols import IThemeable
from hyper_core.ui.themes import Theme

class ThemedWidget(BaseWidget, IThemeable):
    def __init__(self):
        super().__init__()
        self.theme = None
    
    def set_theme(self, theme: Theme) -> None:
        """Apply theme to widget."""
        self.theme = theme
    
    def get_theme(self) -> Theme:
        """Get current theme."""
        return self.theme
    
    def draw_content(self, stdscr, x, y, width, height):
        """Draw with theme colors."""
        if self.theme:
            color = self.theme.colors.primary
            stdscr.addstr(y, x, "Themed content", curses.color_pair(color))
```

## Best Practices

### 1. Error Handling

```python
class RobustCommand(BaseCommand):
    def execute(self) -> int:
        try:
            # Command logic
            result = self.risky_operation()
            self.print_success(f"Operation completed: {result}")
            return 0
        except SpecificError as e:
            self.print_error(f"Specific error occurred: {e}")
            return 2
        except Exception as e:
            self.print_error(f"Unexpected error: {e}")
            return 1
```

### 2. Configuration Management

```python
from pathlib import Path
import yaml

class ConfigurableCommand(BaseCommand):
    def __init__(self, container):
        super().__init__(container)
        self.config = self._load_config()
    
    def _load_config(self) -> dict:
        """Load plugin configuration."""
        config_path = Path.home() / ".hyper" / "my_plugin.yaml"
        if config_path.exists():
            with open(config_path) as f:
                return yaml.safe_load(f)
        return {}
```

### 3. Resource Management

```python
class ResourceAwareService(IService):
    def __init__(self):
        self.resources = []
    
    def initialize(self, config=None):
        """Initialize with proper resource management."""
        try:
            resource = self._acquire_resource()
            self.resources.append(resource)
        except Exception:
            self.shutdown()  # Cleanup on failure
            raise
    
    def shutdown(self):
        """Ensure all resources are released."""
        for resource in self.resources:
            try:
                resource.close()
            except Exception:
                pass  # Log but don't raise
        self.resources.clear()
```

### 4. Testing Your Plugin

```python
# tests/test_my_plugin.py
import pytest
from hyper_core.container import SimpleContainer
from my_plugin.commands.my_command import MyCommand

def test_my_command():
    """Test command execution."""
    container = SimpleContainer()
    command = MyCommand(container)
    
    result = command.execute()
    assert result == 0

def test_my_command_with_args():
    """Test command with arguments."""
    container = SimpleContainer()
    command = MyCommand(container)
    
    result = command.execute(verbose=True)
    assert result == 0
```

## Plugin Lifecycle

```mermaid
sequenceDiagram
    participant Framework
    participant Plugin
    participant Container
    participant Components
    
    Framework->>Plugin: Discovery
    Framework->>Plugin: Load module
    Framework->>Plugin: Extract metadata
    Framework->>Plugin: initialize(container)
    Plugin->>Container: Register services
    Plugin->>Framework: register() -> components
    Framework->>Components: Create instances
    
    Note over Framework,Components: Runtime
    Framework->>Components: Use functionality
    
    Framework->>Plugin: shutdown()
    Plugin->>Container: Cleanup services
```

## Troubleshooting

### Common Issues

1. **Plugin not discovered**: Check directory structure and `__init__.py` files
2. **Import errors**: Ensure all dependencies are installed
3. **Service injection fails**: Verify service is registered in container
4. **UI rendering issues**: Check terminal size and curses error handling

### Debugging

```python
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class DebuggableCommand(BaseCommand):
    def execute(self) -> int:
        logger.debug("Starting command execution")
        # Command logic with debug statements
        logger.debug("Command completed")
        return 0
```

## Examples

Check the `examples/` directory in the Hyper Core repository for complete plugin examples and templates.