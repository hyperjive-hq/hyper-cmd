"""CLI module for the hyper command."""

import sys
from typing import List, Optional
import click
from rich.console import Console

from .commands.registry import CommandRegistry
from .plugins.loader import PluginLoader
from .container.simple_container import SimpleContainer


def discover_commands() -> CommandRegistry:
    """Discover and register available commands."""
    registry = CommandRegistry()
    
    # Load plugins which may register commands
    plugin_loader = PluginLoader()
    plugin_loader.discover_plugins()
    
    for plugin in plugin_loader.get_loaded_plugins():
        if hasattr(plugin, 'register_commands'):
            plugin.register_commands(registry)
    
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
                            instance = cmd_class()
                            description = instance.description if hasattr(instance, 'description') else 'No description'
                            console.print(f"  [cyan]{cmd_name}[/cyan] - {description}")
                        except Exception:
                            console.print(f"  [cyan]{cmd_name}[/cyan] - Command available")
            else:
                console.print("  [yellow]No commands found. Install plugins to add commands.[/yellow]")
            
            console.print("\nUse 'hyper --ui' to launch the UI interface.")
            console.print("Use 'hyper <command>' to run a specific command.")


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
        
        framework.add_menu_item(
            key='q',
            label='Quit',
            action=lambda: 'quit'
        )
        
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
                                instance = cmd_class()
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
            self.plugin_loader = PluginLoader()
            self.plugin_loader.discover_plugins()
            
        def render_content(self, ctx: RenderContext) -> None:
            """Render the plugins list using the new rendering system."""
            plugins = self.plugin_loader.get_loaded_plugins()
            
            # Clear area
            for y in range(ctx.height):
                ctx.window.add_str(ctx.y + y, ctx.x, " " * ctx.width)
            
            # Render title
            ctx.window.add_str(ctx.y + 1, ctx.x + 2, "Loaded Plugins:", TextStyle.BOLD)
            
            # Render plugins
            if plugins:
                for i, plugin in enumerate(plugins):
                    if i + 3 < ctx.height - 1:  # Leave space for help
                        plugin_name = getattr(plugin, '__name__', str(plugin))
                        line = f"{plugin_name}"[:ctx.width-6]
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
        cmd_class = registry.get(cmd_name)
        if cmd_class:
            @click.command(name=cmd_name)
            @click.pass_context
            def command_wrapper(ctx, cmd_class=cmd_class):
                """Dynamically created command wrapper."""
                try:
                    instance = cmd_class(container)
                    exit_code = instance.run()
                    sys.exit(exit_code)
                except Exception as e:
                    console = Console()
                    console.print(f"[red]Error running command '{cmd_name}':[/red] {e}")
                    sys.exit(1)
            
            main.add_command(command_wrapper)


if __name__ == '__main__':
    register_dynamic_commands()
    main()