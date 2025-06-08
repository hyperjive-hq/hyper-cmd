"""CLI module for the hyper command."""

import inspect
import os
import sys
from pathlib import Path

import click
from rich.console import Console

from .commands.init import InitCommand
from .commands.registry import CommandRegistry
from .container.simple_container import SimpleContainer
from .plugins.registry import plugin_registry


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


def install_shell_completion() -> None:
    """Install shell completion for the hyper command."""
    console = Console()

    # Detect shell
    shell = os.environ.get("SHELL", "").split("/")[-1]

    if shell == "zsh":
        install_zsh_completion()
    elif shell == "bash":
        install_bash_completion()
    elif shell == "fish":
        install_fish_completion()
    else:
        console.print(f"[yellow]Warning:[/yellow] Unsupported shell '{shell}'")
        console.print("Supported shells: zsh, bash, fish")
        console.print("You can manually install completion by running:")
        console.print("  hyper --show-completion")


def show_shell_completion() -> None:
    """Show the shell completion script."""
    shell = os.environ.get("SHELL", "").split("/")[-1]

    if shell == "zsh":
        print(get_zsh_completion_script())
    elif shell == "bash":
        print(get_bash_completion_script())
    elif shell == "fish":
        print(get_fish_completion_script())
    else:
        print("# Unsupported shell")


def install_zsh_completion() -> None:
    """Install Zsh completion."""
    console = Console()

    # Try user directories first, then system directories
    completion_dirs = [
        Path.home() / ".zsh" / "completions",
        Path.home() / ".local" / "share" / "zsh" / "site-functions",
    ]

    # Check system directories if they're writable
    system_dirs = [
        Path("/usr/local/share/zsh/site-functions"),
        Path("/opt/homebrew/share/zsh/site-functions"),  # macOS with Homebrew
    ]

    for dir_path in system_dirs:
        if dir_path.exists() and os.access(dir_path, os.W_OK):
            completion_dirs.append(dir_path)

    # Find or create completion directory
    completion_dir = None
    for dir_path in completion_dirs:
        if dir_path.exists() and os.access(dir_path, os.W_OK):
            completion_dir = dir_path
            break
        elif not dir_path.exists():
            try:
                dir_path.mkdir(parents=True, exist_ok=True)
                completion_dir = dir_path
                break
            except (PermissionError, OSError):
                continue

    if not completion_dir:
        # Fallback to user directory
        completion_dir = Path.home() / ".zsh" / "completions"
        completion_dir.mkdir(parents=True, exist_ok=True)

    completion_file = completion_dir / "_hyper"
    completion_file.write_text(get_zsh_completion_script())

    console.print(f"[green]✓[/green] Zsh completion installed to {completion_file}")

    # Check if fpath is already configured
    zshrc_path = Path.home() / ".zshrc"
    needs_fpath_config = True

    if zshrc_path.exists():
        zshrc_content = zshrc_path.read_text()
        if str(completion_dir) in zshrc_content or "fpath=" in zshrc_content:
            needs_fpath_config = False

    if needs_fpath_config:
        console.print("\n[yellow]Setup required:[/yellow] Add this to your ~/.zshrc:")
        console.print(f"  fpath=({completion_dir} $fpath)")
        console.print("  autoload -Uz compinit && compinit")
        console.print("\n[bold]To activate completion:[/bold]")
        console.print("  1. Restart your shell, OR")
        console.print("  2. Run: [cyan]source ~/.zshrc[/cyan]")
        console.print("\n[dim]Then try: hyper <TAB> to see commands[/dim]")
    else:
        console.print("\n[bold]To activate completion:[/bold]")
        console.print("  1. Restart your shell, OR")
        console.print("  2. Run: [cyan]compinit && rehash[/cyan]")
        console.print("\n[dim]Then try: hyper <TAB> to see commands[/dim]")


def install_bash_completion() -> None:
    """Install Bash completion."""
    console = Console()

    # Try user directories first, then system directories
    completion_dirs = [
        Path.home() / ".local" / "share" / "bash-completion" / "completions",
    ]

    # Check system directories if they're writable
    system_dirs = [
        Path("/usr/local/etc/bash_completion.d"),
        Path("/etc/bash_completion.d"),
    ]

    for dir_path in system_dirs:
        if dir_path.exists() and os.access(dir_path, os.W_OK):
            completion_dirs.append(dir_path)

    # Find or create completion directory
    completion_dir = None
    for dir_path in completion_dirs:
        if dir_path.exists() and os.access(dir_path, os.W_OK):
            completion_dir = dir_path
            break
        elif not dir_path.exists():
            try:
                dir_path.mkdir(parents=True, exist_ok=True)
                completion_dir = dir_path
                break
            except (PermissionError, OSError):
                continue

    if not completion_dir:
        # Fallback to user directory
        completion_dir = Path.home() / ".local" / "share" / "bash-completion" / "completions"
        completion_dir.mkdir(parents=True, exist_ok=True)

    completion_file = completion_dir / "hyper"
    completion_file.write_text(get_bash_completion_script())

    console.print(f"[green]✓[/green] Bash completion installed to {completion_file}")
    console.print("\n[bold]To activate completion:[/bold]")
    console.print("  1. Restart your shell, OR")
    console.print("  2. Run: [cyan]source ~/.bashrc[/cyan]")
    console.print("\n[dim]Then try: hyper <TAB> to see commands[/dim]")


def install_fish_completion() -> None:
    """Install Fish completion."""
    console = Console()

    completion_dir = Path.home() / ".config" / "fish" / "completions"
    completion_dir.mkdir(parents=True, exist_ok=True)

    completion_file = completion_dir / "hyper.fish"
    completion_file.write_text(get_fish_completion_script())

    console.print(f"[green]✓[/green] Fish completion installed to {completion_file}")
    console.print("\n[bold]Completion activated automatically in Fish![/bold]")
    console.print("[dim]Try: hyper <TAB> to see commands[/dim]")


def get_zsh_completion_script() -> str:
    """Generate Zsh completion script."""
    return """#compdef hyper

_hyper() {
    local context state line

    _arguments -C \
        '--ui[Launch the UI interface]' \
        '--install-completion[Install shell completion]' \
        '--show-completion[Show shell completion script]' \
        '--help[Show help message]' \
        '1: :_hyper_commands' \
        '*::arg:->args'

    case $state in
        args)
            case $line[1] in
                init)
                    _arguments \
                        '--force[Skip confirmation and overwrite existing files]' \
                        '--help[Show help message]'
                    ;;
            esac
            ;;
    esac
}

_hyper_commands() {
    local commands
    commands=(
        'init:Initialize a new Hyper project in the current directory'
    )

    # Add dynamic commands from plugins
    local dynamic_commands
    dynamic_commands=($(hyper 2>/dev/null | grep -E '^  [a-zA-Z]' | awk '{print $1":"$3}' | tr -d '[]'))

    _describe 'commands' commands
    _describe 'plugin commands' dynamic_commands
}

_hyper
"""


def get_bash_completion_script() -> str:
    """Generate Bash completion script."""
    return """_hyper_completion() {
    local cur prev commands
    COMPREPLY=()
    cur="${COMP_WORDS[COMP_CWORD]}"
    prev="${COMP_WORDS[COMP_CWORD-1]}"

    commands="init --ui --install-completion --show-completion --help"

    # Add dynamic commands
    if command -v hyper >/dev/null 2>&1; then
        local dynamic_commands
        dynamic_commands=$(hyper 2>/dev/null | grep -E '^  [a-zA-Z]' | awk '{print $1}' | tr -d '[]')
        commands="$commands $dynamic_commands"
    fi

    case "${prev}" in
        init)
            COMPREPLY=( $(compgen -W "--force --help" -- ${cur}) )
            return 0
            ;;
        hyper)
            COMPREPLY=( $(compgen -W "${commands}" -- ${cur}) )
            return 0
            ;;
    esac

    COMPREPLY=( $(compgen -W "${commands}" -- ${cur}) )
}

complete -F _hyper_completion hyper
"""


def check_completion_installed(shell: str) -> bool:
    """Check if completion is already installed for the given shell."""
    if shell == "zsh":
        # Check common zsh completion locations
        completion_paths = [
            Path.home() / ".zsh" / "completions" / "_hyper",
            Path.home() / ".local" / "share" / "zsh" / "site-functions" / "_hyper",
            Path("/usr/local/share/zsh/site-functions/_hyper"),
            Path("/opt/homebrew/share/zsh/site-functions/_hyper"),
        ]
        return any(path.exists() for path in completion_paths)

    elif shell == "bash":
        completion_paths = [
            Path.home() / ".local" / "share" / "bash-completion" / "completions" / "hyper",
            Path("/usr/local/etc/bash_completion.d/hyper"),
            Path("/etc/bash_completion.d/hyper"),
        ]
        return any(path.exists() for path in completion_paths)

    elif shell == "fish":
        completion_path = Path.home() / ".config" / "fish" / "completions" / "hyper.fish"
        return completion_path.exists()

    return False


def get_fish_completion_script() -> str:
    """Generate Fish completion script."""
    return """# Completions for hyper command

complete -c hyper -f

# Main options
complete -c hyper -l ui -d "Launch the UI interface"
complete -c hyper -l install-completion -d "Install shell completion"
complete -c hyper -l show-completion -d "Show shell completion script"
complete -c hyper -l help -d "Show help message"

# Commands
complete -c hyper -n "__fish_use_subcommand" -a "init" -d "Initialize a new Hyper project"

# Init command options
complete -c hyper -n "__fish_seen_subcommand_from init" -l force -d "Skip confirmation and overwrite existing files"
complete -c hyper -n "__fish_seen_subcommand_from init" -l help -d "Show help message"

# Dynamic command completion function
function __fish_hyper_complete_commands
    hyper 2>/dev/null | grep -E '^  [a-zA-Z]' | awk '{print $1}' | tr -d '[]'
end

# Add dynamic commands
complete -c hyper -n "__fish_use_subcommand" -a "(__fish_hyper_complete_commands)"
"""


@click.group(invoke_without_command=True)
@click.option("--ui", is_flag=True, help="Launch the UI interface")
@click.option("--install-completion", is_flag=True, help="Install shell completion")
@click.option("--show-completion", is_flag=True, help="Show shell completion script")
@click.pass_context
def main(ctx: click.Context, ui: bool, install_completion: bool, show_completion: bool) -> None:
    """Hyper framework CLI tool."""
    console = Console()

    if ctx.invoked_subcommand is None:
        if install_completion:
            install_shell_completion()
            return
        elif show_completion:
            show_shell_completion()
            return
        elif ui:
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
                            description = (
                                instance.description
                                if hasattr(instance, "description")
                                else "No description"
                            )
                            console.print(f"  [cyan]{cmd_name}[/cyan] - {description}")
                        except Exception:
                            console.print(f"  [cyan]{cmd_name}[/cyan] - Command available")
            else:
                console.print(
                    "  [yellow]No commands found. Install plugins to add commands.[/yellow]"
                )

            console.print("\nUse 'hyper --ui' to launch the UI interface.")
            console.print("Use 'hyper <command>' to run a specific command.")
            console.print("Use 'hyper init' to initialize a new project.")

            # Check if autocompletion is installed
            shell = os.environ.get("SHELL", "").split("/")[-1]
            if shell in ["zsh", "bash", "fish"]:
                completion_installed = check_completion_installed(shell)
                if not completion_installed:
                    console.print(
                        "\n[dim]💡 Tip: Enable tab completion with 'hyper --install-completion'[/dim]"
                    )
                else:
                    console.print(
                        "\n[dim]💡 Tip: Use Tab to autocomplete commands and options[/dim]"
                    )


@main.command()
@click.option("--force", is_flag=True, help="Skip confirmation and overwrite existing files")
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
        from .ui.framework import LayoutConfig, NCursesFramework

        config = LayoutConfig(
            title="HYPER FRAMEWORK", subtitle="Plugin-based CLI Application Framework"
        )

        framework = NCursesFramework(config.title, config.subtitle)

        # Add menu items
        framework.add_menu_item(
            key="c", label="Commands", action=lambda: show_commands_panel(framework)
        )

        framework.add_menu_item(
            key="p", label="Plugins", action=lambda: show_plugins_panel(framework)
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
    from .ui.engine import RenderContext
    from .ui.framework import ContentPanel
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
                                description = (
                                    instance.description
                                    if hasattr(instance, "description")
                                    else "No description"
                                )
                                line = f"{cmd_name}: {description}"[: ctx.width - 6]
                                ctx.window.add_str(ctx.y + i + 3, ctx.x + 4, line)
                            except Exception:
                                line = f"{cmd_name}: Command available"[: ctx.width - 6]
                                ctx.window.add_str(ctx.y + i + 3, ctx.x + 4, line)
            else:
                ctx.window.add_str(ctx.y + 3, ctx.x + 4, "No commands found.")

            # Render help
            ctx.window.add_str(ctx.y + ctx.height - 2, ctx.x + 2, "Press 'b' to go back")

    framework.set_panel(CommandsPanel())


def show_plugins_panel(framework) -> None:
    """Show the plugins panel in the UI."""
    from .ui.engine import RenderContext
    from .ui.framework import ContentPanel
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
                        status = plugin_info["status"]
                        line = f"{plugin_name} ({status})"[: ctx.width - 6]
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
            description = getattr(temp_instance, "description", f"Command: {cmd_name}")

            @click.command(name=cmd_name, help=description)
            @click.pass_context
            def command_wrapper(ctx, cmd_class=cmd_class, **kwargs):
                """Dynamically created command wrapper."""
                try:
                    instance = cmd_class(container)

                    # Handle extra arguments
                    extra_args = kwargs.pop("extra_args", ())

                    # Filter kwargs to only include those accepted by the execute method
                    sig = inspect.signature(instance.execute)
                    filtered_kwargs = {k: v for k, v in kwargs.items() if k in sig.parameters}

                    # Add extra args if the method accepts *args
                    has_varargs = any(
                        p.kind == inspect.Parameter.VAR_POSITIONAL for p in sig.parameters.values()
                    )
                    if has_varargs:
                        exit_code = instance.execute(*extra_args, **filtered_kwargs)
                    else:
                        exit_code = instance.execute(**filtered_kwargs)

                    sys.exit(exit_code)
                except Exception as e:
                    console = Console()
                    console.print(
                        f"[red]Error running command '{cmd_class.__name__.lower()}':[/red] {e}"
                    )
                    sys.exit(1)

            # Add Click options based on the execute method signature
            try:
                sig = inspect.signature(temp_instance.execute)

                for param_name, param in sig.parameters.items():
                    if param_name == "args" and param.kind == inspect.Parameter.VAR_POSITIONAL:
                        # Add support for extra arguments
                        command_wrapper = click.argument("extra_args", nargs=-1)(command_wrapper)
                        continue
                    elif param_name in ["kwargs"]:
                        continue

                    # Determine parameter type and default
                    param_type = str
                    default = None
                    is_flag = False

                    if param.annotation is bool:
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
                        command_wrapper = click.option(
                            option_name, is_flag=True, default=default, help=f"{param_name} flag"
                        )(command_wrapper)
                    else:
                        command_wrapper = click.option(
                            option_name,
                            default=default,
                            type=param_type,
                            help=f"{param_name} parameter",
                        )(command_wrapper)
            except Exception:
                # If we can't analyze the signature, just continue
                pass

            main.add_command(command_wrapper)


# Register dynamic commands when module is imported
register_dynamic_commands()


if __name__ == "__main__":
    main()
