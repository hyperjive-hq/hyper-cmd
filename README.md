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

### Initialize a New Project

Start by creating a new Hyper project in your directory:

```bash
hyper init
```

This creates a `.hyper` directory with:
- `config.yaml` - Project configuration file
- `plugins/` - Directory for your custom plugins
- `plugins/hello_world/` - Example plugin with full documentation
- `.gitignore` - Git ignore patterns for Hyper files

### Try the Example Plugin

Test the framework with the included example:

```bash
hyper hello --name "Your Name" --style fancy
```

Or launch the interactive UI:

```bash
hyper --ui
```

### Project Configuration

The `.hyper/config.yaml` file controls project settings:

```yaml
# Plugin configuration
plugins:
  enabled: true
  auto_discover: true
  # bundle_paths:
  #   - '../shared-plugins'

# UI configuration
ui:
  theme: 'default'
  refresh_interval: 1000

# Logging configuration  
logging:
  level: 'INFO'
  # file: 'hyper.log'
```

### Creating Your Own Plugin

1. **Copy the example plugin as a template:**
   ```bash
   cp -r .hyper/plugins/hello_world .hyper/plugins/my_plugin
   ```

2. **Modify the plugin files:**
   - Edit `plugin.py` with your command logic
   - Update `plugin.yaml` with your metadata
   - Customize the `__init__.py` if needed

3. **Test your plugin:**
   ```bash
   hyper <your-command>
   ```

### Plugin Structure

```python
# .hyper/plugins/my_plugin/plugin.py
from hyper_core.commands import BaseCommand

PLUGIN_NAME = "my_plugin"
PLUGIN_VERSION = "1.0.0"
PLUGIN_DESCRIPTION = "My awesome plugin"

class MyCommand(BaseCommand):
    @property
    def name(self) -> str:
        return "my-command"
    
    @property
    def description(self) -> str:
        return "Description of my command"
    
    def execute(self) -> int:
        self.console.print("Hello from my plugin!")
        return 0
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

- **[Architecture Guide](architecture.md)** - High-level system architecture and component interactions
- **[Plugin Development Guide](plugin-guide.md)** - Complete guide for developing plugins

## License

MIT License - see LICENSE file for details.