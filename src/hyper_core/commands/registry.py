"""Command registry for managing command registration and discovery."""

from typing import Optional

from ..protocols import ICommand


class CommandRegistry:
    """Registry for managing command classes."""

    def __init__(self):
        """Initialize the command registry."""
        self._commands: dict[str, type[ICommand]] = {}

    def register(self, command_class: type[ICommand], name: Optional[str] = None) -> None:
        """
        Register a command class.

        Args:
            command_class: The command class to register
            name: Optional name override (uses command.name if not provided)
        """
        # Always try to instantiate to get the name from the instance
        if name:
            cmd_name = name
        else:
            try:
                instance = command_class(None)
                cmd_name = instance.name
            except Exception:
                cmd_name = command_class.__name__.lower().replace("command", "")

        self._commands[cmd_name] = command_class

    def unregister(self, name: str) -> None:
        """
        Unregister a command.

        Args:
            name: The command name to unregister
        """
        self._commands.pop(name, None)

    def get(self, name: str) -> Optional[type[ICommand]]:
        """
        Get a command class by name.

        Args:
            name: The command name

        Returns:
            The command class or None if not found
        """
        return self._commands.get(name)

    def list_commands(self) -> list[str]:
        """
        List all registered command names.

        Returns:
            List of command names
        """
        return list(self._commands.keys())

    def get_all(self) -> dict[str, type[ICommand]]:
        """
        Get all registered commands.

        Returns:
            Dictionary mapping command names to classes
        """
        return self._commands.copy()

    def clear(self) -> None:
        """Clear all registered commands."""
        self._commands.clear()

    def create_command(self, name: str, container) -> Optional[ICommand]:
        """
        Create a command instance by name.

        Args:
            name: The command name
            container: Dependency injection container

        Returns:
            Command instance or None if not found
        """
        command_class = self.get(name)
        if command_class:
            return command_class(container)
        return None
