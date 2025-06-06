# Hyper Core

A pluggable CLI framework for building terminal applications with ncurses UI support.

## Features

- **Plugin System**: Dynamic plugin discovery and loading
- **Command Framework**: Base classes for CLI commands with dependency injection
- **NCurses UI**: Reusable terminal UI components including widgets and themes  
- **Dependency Injection**: Both simple and advanced DI container options
- **Type-Safe Protocols**: Well-defined interfaces for extensions

## Installation

```bash
pip install hyper-core
```

## Quick Start

### Creating a Simple Plugin

```python
# my_plugin/plugin.py
from hyper_core.commands import BaseCommand
from hyper_core.protocols import ICommand

PLUGIN_NAME = "my_plugin"
PLUGIN_VERSION = "1.0.0"
PLUGIN_DESCRIPTION = "My awesome plugin"

class HelloCommand(BaseCommand):
    """Say hello!"""
    
    @property
    def name(self) -> str:
        return "hello"
    
    @property
    def description(self) -> str:
        return "Say hello to the world"
    
    def execute(self) -> int:
        self.console.print("Hello from my plugin!")
        return 0
```

### Using the Plugin System

```python
from hyper_core.plugins import plugin_registry

# Initialize the registry
plugin_registry.initialize(["/path/to/plugins"])

# Discover and load plugins
discovered = plugin_registry.discover_plugins()
for plugin_name in discovered:
    plugin_registry.load_plugin(plugin_name)

# Use loaded commands
cmd_class = plugin_registry.get_command("hello")
if cmd_class:
    cmd = cmd_class(container)
    cmd.run()
```

### Creating a Widget

```python
from hyper_core.ui import BaseWidget, WidgetSize

class StatusWidget(BaseWidget):
    def __init__(self):
        super().__init__(title="Status", size=WidgetSize.MEDIUM)
    
    def draw_content(self, stdscr, x, y, width, height):
        stdscr.addstr(y, x, "System Status: OK")
    
    def refresh_data(self):
        # Update widget data here
        pass
```

## Documentation

Full documentation is available at [https://hyper-core.readthedocs.io](https://hyper-core.readthedocs.io)

## License

MIT License - see LICENSE file for details.