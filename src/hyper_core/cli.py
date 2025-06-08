"""CLI module for the hyper command."""

import sys
import inspect
from typing import List, Optional
import click
from rich.console import Console

from .commands.registry import CommandRegistry
from .commands.init import InitCommand
from .plugins.registry import plugin_registry
from .container.simple_container import SimpleContainer


def discover_commands() -> CommandRegistry:
    """Discover and register available commands."""
    registry = CommandRegistry()
    
    # Register built-in commands first
    registry.register(InitCommand, "init")
    
    # Initialize and load plugins from .hyper directory
    plugin_registry.initialize()
    discovered_plugins = plugin_registry.discover_plugins()
    
    # Load all discovered plugins
    for plugin_name in discovered_plugins:
        plugin_registry.load_plugin(plugin_name)
    
    # Get commands from plugin registry and register them with Click registry
    plugin_commands = plugin_registry.get_commands_for_click()
    for cmd_name, cmd_class in plugin_commands.items():
        registry.register(cmd_class, cmd_name)
    
    return registry


@click.group(invoke_without_command=True)
@click.option('--ui', is_flag=True, help='Launch the UI interface')
@click.pass_context
def main(ctx: click.Context, ui: bool) -> None:
    """Hyper framework CLI tool."""
    console = Console()
    
    if ctx.invoked_subcommand is None:
        if ui:
            launch_ui()
        else:
            # Show available commands
            registry = discover_commands()
            commands = registry.list_commands()
            
            console.print("[bold]Hyper CLI[/bold]")
            console.print("Available commands:")
            
            if commands:
                for cmd_name in sorted(commands):
                    cmd_class = registry.get(cmd_name)
                    if cmd_class:
                        try:
                            container = SimpleContainer()
                            instance = cmd_class(container)
                            description = instance.description if hasattr(instance, 'description') else 'No description'
                            console.print(f"  [cyan]{cmd_name}[/cyan] - {description}")
                        except Exception:
                            console.print(f"  [cyan]{cmd_name}[/cyan] - Command available")
            else:
                console.print("  [yellow]No commands found. Install plugins to add commands.[/yellow]")
            
            console.print("\nUse 'hyper --ui' to launch the UI interface.")
            console.print("Use 'hyper <command>' to run a specific command.")
            console.print("Use 'hyper init' to initialize a new project.")


@main.command()
@click.option('--force', is_flag=True, help='Skip confirmation and overwrite existing files')
@click.pass_context
def init(ctx: click.Context, force: bool) -> None:
    """Initialize a new Hyper project in the current directory."""
    container = SimpleContainer()
    init_command = InitCommand(container)
    exit_code = init_command.execute(force=force)
    sys.exit(exit_code)


def launch_ui() -> None:
    """Launch the ncurses UI interface."""
    try:
        from .ui.framework import NCursesFramework, LayoutConfig, MenuItem
        
        config = LayoutConfig(
            title="HYPER FRAMEWORK",
            subtitle="Plugin-based CLI Application Framework"
        )
        
        framework = NCursesFramework(config.title, config.subtitle)
        
        # Add menu items
        framework.add_menu_item(
            key='c',
            label='Commands',
            action=lambda: show_commands_panel(framework)
        )
        
        framework.add_menu_item(
            key='p',
            label='Plugins',
            action=lambda: show_plugins_panel(framework)
        )
        
        
        # Show the first panel (Commands) by default
        show_commands_panel(framework)
        
        framework.run()
        
    except ImportError as e:
        console = Console()
        console.print(f"[red]Error:[/red] UI dependencies not available: {e}")
        console.print("Install with: pip install 'hyper-core[ui]'")
        sys.exit(1)


def show_commands_panel(framework) -> None:
    """Show the commands panel in the UI."""
    from .ui.framework import ContentPanel
    from .ui.engine import RenderContext
    from .ui.renderer import TextStyle
    
    class CommandsPanel(ContentPanel):
        def __init__(self):
            super().__init__("Available Commands")
            self.registry = discover_commands()
            
        def render_content(self, ctx: RenderContext) -> None:
            """Render the commands list using the new rendering system."""
            commands = self.registry.list_commands()
            
            # Clear area
            for y in range(ctx.height):
                ctx.window.add_str(ctx.y + y, ctx.x, " " * ctx.width)
            
            # Render title
            ctx.window.add_str(ctx.y + 1, ctx.x + 2, "Available Commands:", TextStyle.BOLD)
            
            # Render commands
            if commands:
                for i, cmd_name in enumerate(sorted(commands)):
                    if i + 3 < ctx.height - 1:  # Leave space for help
                        cmd_class = self.registry.get(cmd_name)
                        if cmd_class:
                            try:
                                container = SimpleContainer()
                                instance = cmd_class(container)
                                description = instance.description if hasattr(instance, 'description') else 'No description'
                                line = f"{cmd_name}: {description}"[:ctx.width-6]
                                ctx.window.add_str(ctx.y + i + 3, ctx.x + 4, line)
                            except Exception:
                                line = f"{cmd_name}: Command available"[:ctx.width-6]
                                ctx.window.add_str(ctx.y + i + 3, ctx.x + 4, line)
            else:
                ctx.window.add_str(ctx.y + 3, ctx.x + 4, "No commands found.")
                
            # Render help
            ctx.window.add_str(ctx.y + ctx.height - 2, ctx.x + 2, "Press 'b' to go back")
    
    framework.set_panel(CommandsPanel())


def show_plugins_panel(framework) -> None:
    """Show the plugins panel in the UI."""
    from .ui.framework import ContentPanel
    from .ui.engine import RenderContext
    from .ui.renderer import TextStyle
    
    class PluginsPanel(ContentPanel):
        def __init__(self):
            super().__init__("Loaded Plugins")
            
        def render_content(self, ctx: RenderContext) -> None:
            """Render the plugins list using the new rendering system."""
            # Get plugins from the new plugin registry
            plugins = plugin_registry.plugins
            
            # Clear area
            for y in range(ctx.height):
                ctx.window.add_str(ctx.y + y, ctx.x, " " * ctx.width)
            
            # Render title
            ctx.window.add_str(ctx.y + 1, ctx.x + 2, "Loaded Plugins:", TextStyle.BOLD)
            
            # Render plugins
            if plugins:
                for i, (plugin_name, plugin_info) in enumerate(plugins.items()):
                    if i + 3 < ctx.height - 1:  # Leave space for help
                        status = plugin_info['status']
                        line = f"{plugin_name} ({status})"[:ctx.width-6]
                        ctx.window.add_str(ctx.y + i + 3, ctx.x + 4, line)
            else:
                ctx.window.add_str(ctx.y + 3, ctx.x + 4, "No plugins loaded.")
                
            # Render help
            ctx.window.add_str(ctx.y + ctx.height - 2, ctx.x + 2, "Press 'b' to go back")
    
    framework.set_panel(PluginsPanel())


# Register dynamic commands
def register_dynamic_commands():
    """Register commands discovered from plugins."""
    registry = discover_commands()
    container = SimpleContainer()
    
    for cmd_name in registry.list_commands():
        # Skip commands that are already registered as click commands
        if cmd_name == "init":
            continue
            
        cmd_class = registry.get(cmd_name)
        if cmd_class:
            # Get the command's execute method signature to create Click options
            temp_instance = cmd_class(container)
            description = getattr(temp_instance, 'description', f"Command: {cmd_name}")
            
            @click.command(name=cmd_name, help=description)
            @click.pass_context
            def command_wrapper(ctx, cmd_class=cmd_class, **kwargs):
                """Dynamically created command wrapper."""
                try:
                    instance = cmd_class(container)
                    
                    # Handle extra arguments
                    extra_args = kwargs.pop('extra_args', ())
                    
                    # Filter kwargs to only include those accepted by the execute method
                    sig = inspect.signature(instance.execute)
                    filtered_kwargs = {k: v for k, v in kwargs.items() if k in sig.parameters}
                    
                    # Add extra args if the method accepts *args
                    has_varargs = any(p.kind == inspect.Parameter.VAR_POSITIONAL for p in sig.parameters.values())
                    if has_varargs:
                        exit_code = instance.execute(*extra_args, **filtered_kwargs)
                    else:
                        exit_code = instance.execute(**filtered_kwargs)
                    
                    sys.exit(exit_code)
                except Exception as e:
                    console = Console()
                    console.print(f"[red]Error running command '{cmd_name}':[/red] {e}")
                    sys.exit(1)
            
            # Add Click options based on the execute method signature
            try:
                sig = inspect.signature(temp_instance.execute)
                has_varargs = False
                
                for param_name, param in sig.parameters.items():
                    if param_name == 'args' and param.kind == inspect.Parameter.VAR_POSITIONAL:
                        # Add support for extra arguments
                        command_wrapper = click.argument('extra_args', nargs=-1)(command_wrapper)
                        has_varargs = True
                        continue
                    elif param_name in ['kwargs']:
                        continue
                    
                    # Determine parameter type and default
                    param_type = str
                    default = None
                    is_flag = False
                    
                    if param.annotation == bool:
                        is_flag = True
                    elif param.annotation in [int, float]:
                        param_type = param.annotation
                    
                    if param.default != inspect.Parameter.empty:
                        default = param.default
                        if isinstance(default, bool):
                            is_flag = True
                    
                    # Create option name
                    option_name = f"--{param_name.replace('_', '-')}"
                    
                    if is_flag:
                        command_wrapper = click.option(option_name, is_flag=True, default=default, 
                                                     help=f"{param_name} flag")(command_wrapper)
                    else:
                        command_wrapper = click.option(option_name, default=default, type=param_type,
                                                     help=f"{param_name} parameter")(command_wrapper)
            except Exception:
                # If we can't analyze the signature, just continue
                pass
            
            main.add_command(command_wrapper)


# Register dynamic commands when module is imported
register_dynamic_commands()


if __name__ == '__main__':
    main()