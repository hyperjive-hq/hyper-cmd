"""Command registry for managing command registration and discovery."""

from typing import Dict, Type, Optional, List
from ..protocols import ICommand


class CommandRegistry:
    """Registry for managing command classes."""
    
    def __init__(self):
        """Initialize the command registry."""
        self._commands: Dict[str, Type[ICommand]] = {}
    
    def register(self, command_class: Type[ICommand], name: Optional[str] = None) -> None:
        """
        Register a command class.
        
        Args:
            command_class: The command class to register
            name: Optional name override (uses command.name if not provided)
        """
        if not hasattr(command_class, 'name'):
            # Try to instantiate to get the name
            try:
                instance = command_class(None)
                cmd_name = instance.name
            except:
                cmd_name = command_class.__name__.lower().replace('command', '')
        else:
            cmd_name = name or command_class.name
        
        self._commands[cmd_name] = command_class
    
    def unregister(self, name: str) -> None:
        """
        Unregister a command.
        
        Args:
            name: The command name to unregister
        """
        self._commands.pop(name, None)
    
    def get(self, name: str) -> Optional[Type[ICommand]]:
        """
        Get a command class by name.
        
        Args:
            name: The command name
            
        Returns:
            The command class or None if not found
        """
        return self._commands.get(name)
    
    def list_commands(self) -> List[str]:
        """
        List all registered command names.
        
        Returns:
            List of command names
        """
        return list(self._commands.keys())
    
    def get_all(self) -> Dict[str, Type[ICommand]]:
        """
        Get all registered commands.
        
        Returns:
            Dictionary mapping command names to classes
        """
        return self._commands.copy()
    
    def clear(self) -> None:
        """Clear all registered commands."""
        self._commands.clear()