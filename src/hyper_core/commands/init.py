"""Initialize a new Hyper project with .hyper directory and example plugin."""

from pathlib import Path

from .base import BaseCommand


class InitCommand(BaseCommand):
    """Initialize a new Hyper project in the current directory.

    This command creates a .hyper directory structure with:
    - Configuration file
    - Plugins directory with an example plugin
    - Documentation and .gitignore files
    """

    @property
    def name(self) -> str:
        return "init"

    @property
    def description(self) -> str:
        return "Initialize a new Hyper project"

    @property
    def help_text(self) -> str:
        return """
        Usage: hyper init [--force]

        Initialize a new Hyper project in the current directory.

        This command creates:
        - .hyper/config.yaml - Project configuration
        - .hyper/plugins/ - Directory for project plugins
        - .hyper/plugins/hello_world/ - Example plugin with documentation
        - .hyper/.gitignore - Git ignore patterns

        Options:
            --force    Skip confirmation prompt and overwrite existing files
        """

    def execute(self, force: bool = False) -> int:
        """Execute the init command.

        Args:
            force: Skip confirmation and overwrite existing files

        Returns:
            Exit code (0 for success, non-zero for error)
        """
        current_dir = Path.cwd()
        hyper_dir = current_dir / ".hyper"

        # Check if .hyper directory already exists
        if hyper_dir.exists() and not force:
            self.print_warning(f".hyper directory already exists in {current_dir}")

            if not self._confirm_overwrite():
                self.print_info("Initialization cancelled.")
                return 1

        try:
            # Show what will be created
            self._show_initialization_plan(current_dir)

            if not force and not self._confirm_proceed():
                self.print_info("Initialization cancelled.")
                return 1

            # Create the .hyper directory structure
            with self.show_progress("Initializing Hyper project", total=4) as (progress, task):
                # Step 1: Create .hyper directory and config
                self._create_hyper_directory(hyper_dir)
                progress.update(task, advance=1, description="Created .hyper directory")

                # Step 2: Create plugins directory
                self._create_plugins_directory(hyper_dir)
                progress.update(task, advance=1, description="Created plugins directory")

                # Step 3: Create example plugin
                self._create_example_plugin(hyper_dir / "plugins")
                progress.update(task, advance=1, description="Created example plugin")

                # Step 4: Create additional files
                self._create_additional_files(hyper_dir)
                progress.update(task, advance=1, description="Created additional files")

            self.print_success("✓ Hyper project initialized successfully!")
            self._show_next_steps(current_dir)

            return 0

        except Exception as e:
            self.print_error(f"Failed to initialize project: {e}")
            return 1

    def _confirm_overwrite(self) -> bool:
        """Ask user to confirm overwriting existing .hyper directory."""
        response = input("Do you want to overwrite the existing .hyper directory? [y/N]: ")
        return response.lower().startswith("y")

    def _confirm_proceed(self) -> bool:
        """Ask user to confirm proceeding with initialization."""
        response = input("Proceed with initialization? [Y/n]: ")
        return not response.lower().startswith("n")

    def _show_initialization_plan(self, project_dir: Path) -> None:
        """Show what will be created during initialization."""
        self.print_info(f"Initializing Hyper project in: {project_dir}")
        self.console.print("\n[bold]The following will be created:[/bold]")
        self.console.print("  📁 .hyper/")
        self.console.print("  ├── 📄 config.yaml")
        self.console.print("  ├── 📄 .gitignore")
        self.console.print("  ├── 📄 README.md")
        self.console.print("  └── 📁 plugins/")
        self.console.print("      └── 📁 hello_world/")
        self.console.print("          ├── 📄 __init__.py")
        self.console.print("          ├── 📄 plugin.py")
        self.console.print("          └── 📄 plugin.yaml")
        self.console.print("")

    def _create_hyper_directory(self, hyper_dir: Path) -> None:
        """Create .hyper directory with config file."""
        # Create directory
        hyper_dir.mkdir(exist_ok=True)

        # Create config.yaml
        config_content = """# Hyper Core Project Configuration
version: '1.0'

# Plugin configuration
plugins:
  enabled: true
  auto_discover: true
  # Add custom plugin paths here (relative to this config file)
  # bundle_paths:
  #   - '../shared-plugins'
  #   - './custom-plugins'

# UI configuration
ui:
  theme: 'default'
  refresh_interval: 1000

# Logging configuration
logging:
  level: 'INFO'
  # file: 'hyper.log'  # Uncomment to log to file

# Custom application settings can be added here
# app:
#   name: 'My Hyper App'
#   version: '1.0.0'
"""

        config_file = hyper_dir / "config.yaml"
        with open(config_file, "w", encoding="utf-8") as f:
            f.write(config_content)

    def _create_plugins_directory(self, hyper_dir: Path) -> None:
        """Create plugins directory."""
        plugins_dir = hyper_dir / "plugins"
        plugins_dir.mkdir(exist_ok=True)

    def _create_example_plugin(self, plugins_dir: Path) -> None:
        """Create a comprehensive example plugin."""
        plugin_dir = plugins_dir / "hello_world"
        plugin_dir.mkdir(exist_ok=True)

        # Create __init__.py
        init_content = '''"""Hello World Example Plugin.

This is an example plugin that demonstrates the basic structure
and capabilities of Hyper Core plugins.
"""

# Make the plugin module importable
from .plugin import *
'''

        with open(plugin_dir / "__init__.py", "w", encoding="utf-8") as f:
            f.write(init_content)

        # Create plugin.py with comprehensive example
        plugin_content = '''"""Hello World Plugin - A comprehensive example for Hyper Core.

This plugin demonstrates:
- Command creation with arguments and validation
- Widget development with interactive features
- Service implementation for background tasks
- Configuration handling
- Error handling and logging
- Documentation best practices

Author: Hyper Core Framework
Version: 1.0.0
"""

import logging
import time
from pathlib import Path
from typing import Any, Dict, Optional

from hyper_core.commands import BaseCommand
from hyper_core.protocols import IService, IWidget
from hyper_core.ui import BaseWidget, WidgetSize

# Plugin metadata - these constants are automatically detected by the framework
PLUGIN_NAME = "hello_world"
PLUGIN_VERSION = "1.0.0"
PLUGIN_DESCRIPTION = "Hello World example plugin demonstrating Hyper Core capabilities"
PLUGIN_AUTHOR = "Hyper Core Framework"
PLUGIN_DEPENDENCIES = []  # List any Python package dependencies here

# Set up plugin logger
logger = logging.getLogger(__name__)


class HelloCommand(BaseCommand):
    """A simple hello world command with various features.

    This command demonstrates:
    - Basic command structure
    - Argument handling and validation
    - Output formatting with Rich
    - Progress indicators
    - Error handling
    """

    @property
    def name(self) -> str:
        return "hello"

    @property
    def description(self) -> str:
        return "Say hello with optional customization"

    @property
    def help_text(self) -> str:
        return """
        Usage: hyper hello [--name NAME] [--count COUNT] [--style STYLE]

        A friendly hello command that demonstrates plugin capabilities.

        Options:
            --name NAME      Name to greet (default: World)
            --count COUNT    Number of times to say hello (default: 1)
            --style STYLE    Greeting style: simple, fancy, rainbow (default: simple)

        Examples:
            hyper hello
            hyper hello --name Alice --count 3 --style fancy
        """

    def execute(
        self,
        name: str = "World",
        count: int = 1,
        style: str = "simple"
    ) -> int:
        """Execute the hello command.

        Args:
            name: Name to greet
            count: Number of times to greet
            style: Greeting style

        Returns:
            Exit code (0 for success)
        """
        try:
            # Validate arguments
            if count < 1 or count > 10:
                self.print_error("Count must be between 1 and 10")
                return 1

            if style not in ["simple", "fancy", "rainbow"]:
                self.print_error("Style must be: simple, fancy, or rainbow")
                return 1

            # Show progress for multiple greetings
            if count > 1:
                with self.show_progress(f"Saying hello {count} times", total=count) as (progress, task):
                    for i in range(count):
                        self._say_hello(name, style, i + 1, count)
                        progress.update(task, advance=1)
                        if i < count - 1:  # Don't sleep after the last greeting
                            time.sleep(0.5)  # Dramatic pause
            else:
                self._say_hello(name, style)

            # Show completion message
            self.print_success(f"✓ Completed {count} greeting(s)")

            return 0

        except Exception as e:
            logger.error(f"Error in hello command: {e}")
            self.print_error(f"An error occurred: {e}")
            return 1

    def _say_hello(self, name: str, style: str, current: int = 1, total: int = 1) -> None:
        """Say hello with the specified style."""
        if style == "simple":
            message = f"Hello, {name}!"
        elif style == "fancy":
            message = f"🎉 Greetings and salutations, {name}! 🎉"
        elif style == "rainbow":
            # Use Rich markup for colorful output
            message = f"[bold red]H[/bold red][bold yellow]e[/bold yellow][bold green]l[/bold green][bold blue]l[/bold blue][bold magenta]o[/bold magenta][bold cyan], {name}![/bold cyan] [rainbow]✨[/rainbow]"

        if total > 1:
            prefix = f"[{current}/{total}] "
            self.console.print(f"{prefix}{message}")
        else:
            self.console.print(message)


class HelloWidget(BaseWidget):
    """A simple status widget showing hello world information.

    This widget demonstrates:
    - Basic widget structure
    - Data refresh mechanisms
    - Interactive input handling
    - Drawing with curses
    """

    def __init__(self, data_provider: Optional[Any] = None):
        """Initialize the hello widget.

        Args:
            data_provider: Optional data provider for widget content
        """
        super().__init__(
            title="Hello World Widget",
            size=WidgetSize.MEDIUM
        )
        self.data_provider = data_provider
        self.greeting_count = 0
        self.last_name = "World"
        self.message = "Press 'h' to say hello!"

    def refresh_data(self) -> None:
        """Refresh widget data - called periodically by the framework."""
        # In a real widget, you might fetch data from an external source
        current_time = time.strftime("%H:%M:%S")
        self.message = f"Hello from {current_time}!"

    def draw_content(self, stdscr, x: int, y: int, width: int, height: int) -> None:
        """Draw the widget content.

        Args:
            stdscr: Curses screen object
            x, y: Top-left position to draw at
            width, height: Available space for drawing
        """
        try:
            # Draw main message
            if len(self.message) < width - 4:
                stdscr.addstr(y + 1, x + 2, self.message)

            # Draw statistics
            stats_line = f"Greetings sent: {self.greeting_count}"
            if len(stats_line) < width - 4 and height > 3:
                stdscr.addstr(y + 2, x + 2, stats_line)

            # Draw instructions
            help_line = "Press 'h' for hello, 'r' to refresh"
            if len(help_line) < width - 4 and height > 4:
                stdscr.addstr(y + 3, x + 2, help_line)

        except Exception:
            # Handle terminal size issues gracefully
            pass

    def handle_input(self, key: int) -> bool:
        """Handle keyboard input when widget has focus.

        Args:
            key: Pressed key code

        Returns:
            True if input was handled, False otherwise
        """
        if key == ord('h') or key == ord('H'):
            self.greeting_count += 1
            self.message = f"Hello, {self.last_name}! (#{self.greeting_count})"
            return True
        elif key == ord('r') or key == ord('R'):
            self.refresh_data()
            return True

        return False

    def get_minimum_size(self) -> tuple[int, int]:
        """Return minimum widget dimensions.

        Returns:
            Tuple of (width, height) minimum requirements
        """
        return (30, 6)


class HelloService(IService):
    """A simple service that manages hello world functionality.

    This service demonstrates:
    - Service lifecycle management
    - Background task processing
    - Health checking
    - Configuration handling
    """

    def __init__(self):
        """Initialize the hello service."""
        self._initialized = False
        self._config: Dict[str, Any] = {}
        self._greeting_count = 0
        self._last_greeting_time: Optional[float] = None

    @property
    def name(self) -> str:
        return "hello_service"

    @property
    def is_initialized(self) -> bool:
        return self._initialized

    def initialize(self, config: Optional[Dict[str, Any]] = None) -> None:
        """Initialize the service with optional configuration.

        Args:
            config: Optional service configuration
        """
        if self._initialized:
            logger.warning("Hello service already initialized")
            return

        self._config = config or {}

        # Initialize service resources
        logger.info("Initializing Hello service")
        self._greeting_count = 0
        self._last_greeting_time = None

        self._initialized = True
        logger.info("Hello service initialized successfully")

    def shutdown(self) -> None:
        """Clean up service resources."""
        logger.info(f"Shutting down Hello service (sent {self._greeting_count} greetings)")
        self._initialized = False
        self._greeting_count = 0
        self._last_greeting_time = None

    def health_check(self) -> Dict[str, Any]:
        """Perform a health check on the service.

        Returns:
            Dictionary containing health status and metrics
        """
        return {
            'service': self.name,
            'healthy': self._initialized,
            'timestamp': time.time(),
            'greeting_count': self._greeting_count,
            'last_greeting': self._last_greeting_time,
            'uptime_seconds': time.time() - (self._last_greeting_time or time.time()) if self._last_greeting_time else 0
        }

    def get_status(self) -> Dict[str, Any]:
        """Get detailed service status.

        Returns:
            Dictionary containing detailed status information
        """
        return {
            'service': self.name,
            'initialized': self._initialized,
            'config': self._config,
            'metrics': {
                'greeting_count': self._greeting_count,
                'last_greeting_time': self._last_greeting_time
            }
        }

    # Service-specific methods

    def send_greeting(self, name: str = "World") -> str:
        """Send a greeting through the service.

        Args:
            name: Name to greet

        Returns:
            The greeting message

        Raises:
            RuntimeError: If service is not initialized
        """
        if not self._initialized:
            raise RuntimeError("Hello service not initialized")

        self._greeting_count += 1
        self._last_greeting_time = time.time()

        greeting = f"Hello, {name}! (Service greeting #{self._greeting_count})"
        logger.info(f"Sent greeting to {name}")

        return greeting

    def get_greeting_count(self) -> int:
        """Get the total number of greetings sent.

        Returns:
            Number of greetings sent by this service
        """
        return self._greeting_count


# Plugin registration function (optional)
def register_plugin(container) -> Dict[str, Any]:
    """Register plugin components with the dependency injection container.

    This function is called by the framework when the plugin is loaded.
    It's optional - the framework can also auto-discover components.

    Args:
        container: The dependency injection container

    Returns:
        Dictionary describing registered components
    """
    # Register the service
    hello_service = HelloService()
    container.register(HelloService, hello_service)

    logger.info("Hello World plugin registered successfully")

    return {
        'commands': [HelloCommand],
        'widgets': [HelloWidget],
        'services': [HelloService]
    }
'''

        with open(plugin_dir / "plugin.py", "w", encoding="utf-8") as f:
            f.write(plugin_content)

        # Create plugin.yaml metadata file
        yaml_content = """name: hello_world
version: 1.0.0
description: Hello World example plugin demonstrating Hyper Core capabilities
author: Hyper Core Framework

# Plugin dependencies (Python packages)
dependencies: []

# Plugin components that will be registered
entry_points:
  commands:
    - HelloCommand
  widgets:
    - HelloWidget
  services:
    - HelloService

# Plugin configuration schema (optional)
config_schema:
  greeting_style:
    type: string
    default: simple
    description: Default greeting style
  max_count:
    type: integer
    default: 10
    description: Maximum number of greetings allowed

# Plugin metadata
tags:
  - example
  - tutorial
  - hello-world

# Minimum framework version required
min_hyper_version: "0.1.0"
"""

        with open(plugin_dir / "plugin.yaml", "w", encoding="utf-8") as f:
            f.write(yaml_content)

    def _create_additional_files(self, hyper_dir: Path) -> None:
        """Create additional files like .gitignore and README."""
        # Create .gitignore
        gitignore_content = """# Hyper Core generated files
*.log
*.cache
.hyper_cache/

# Plugin development
plugins/*/venv/
plugins/*/.env
plugins/*/__pycache__/
plugins/*/.pytest_cache/

# IDE files
.vscode/
.idea/
*.swp
*.swo

# OS files
.DS_Store
Thumbs.db
"""

        gitignore_file = hyper_dir / ".gitignore"
        with open(gitignore_file, "w", encoding="utf-8") as f:
            f.write(gitignore_content)

        # Create README.md
        readme_content = """# Hyper Core Project

This directory contains your Hyper Core project configuration and plugins.

## Structure

- `config.yaml` - Project configuration file
- `plugins/` - Directory containing project-specific plugins
- `plugins/hello_world/` - Example plugin demonstrating framework capabilities

## Getting Started

1. **Try the example plugin:**
   ```bash
   hyper hello --name "Your Name" --style fancy
   ```

2. **Create your own plugin:**
   - Copy the `hello_world` plugin as a template
   - Modify the plugin.py file with your logic
   - Update plugin.yaml with your metadata
   - Test with `hyper <your-command>`

3. **Configure your project:**
   - Edit `config.yaml` to customize settings
   - Add plugin bundle paths if needed
   - Set your preferred theme and logging level

## Plugin Development

The `hello_world` plugin demonstrates:

- **Commands**: CLI commands with arguments and validation
- **Widgets**: Interactive UI components for dashboard views
- **Services**: Background services and dependency injection
- **Configuration**: Plugin metadata and settings
- **Error Handling**: Robust error handling patterns

See the plugin files for detailed documentation and examples.

## Resources

- [Plugin Development Guide](https://github.com/your-repo/hyper-core/blob/main/plugin-guide.md)
- [Framework Documentation](https://github.com/your-repo/hyper-core/blob/main/README.md)
- [API Reference](https://github.com/your-repo/hyper-core/blob/main/docs/api.md)
"""

        readme_file = hyper_dir / "README.md"
        with open(readme_file, "w", encoding="utf-8") as f:
            f.write(readme_content)

    def _show_next_steps(self, project_dir: Path) -> None:
        """Show next steps after successful initialization."""
        self.console.print("\n[bold green]🎉 Success![/bold green] Your Hyper project is ready.")
        self.console.print("\n[bold]Next steps:[/bold]")
        self.console.print("1. Try the example plugin:")
        self.console.print("   [cyan]hyper hello --name 'Your Name' --style fancy[/cyan]")
        self.console.print("")
        self.console.print("2. Explore the project structure:")
        self.console.print(f"   [cyan]ls -la {project_dir / '.hyper'}[/cyan]")
        self.console.print(f"   [cyan]cat {project_dir / '.hyper' / 'README.md'}[/cyan]")
        self.console.print("")
        self.console.print("3. Create your own plugin:")
        self.console.print("   - Copy .hyper/plugins/hello_world as a template")
        self.console.print("   - Modify plugin.py with your logic")
        self.console.print("   - Update plugin.yaml with your metadata")
        self.console.print("")
        self.console.print("4. Learn more:")
        self.console.print("   [cyan]hyper help[/cyan]")
        self.console.print("   [cyan]cat .hyper/plugins/hello_world/plugin.py[/cyan]")
