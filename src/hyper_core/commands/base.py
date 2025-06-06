"""Base command class for Hyper framework.

This module provides the base class for all commands in the Hyper framework.
Commands are the primary way users interact with applications built on Hyper.
"""

import socket
import sys
from abc import ABC, abstractmethod
from contextlib import contextmanager
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional

from rich.console import Console
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn

from ..protocols import ICommand

if TYPE_CHECKING:
    from ..container import Container


class BaseCommand(ABC, ICommand):
    """Base class for all Hyper commands.
    
    This class provides common functionality for commands including:
    - Error handling and exit codes
    - Console output utilities
    - Progress indicators
    - Path and port validation helpers
    
    Example:
        class HelloCommand(BaseCommand):
            @property
            def name(self) -> str:
                return "hello"
            
            @property
            def description(self) -> str:
                return "Say hello to the user"
            
            def execute(self, name: str = "World") -> int:
                self.console.print(f"Hello, {name}!")
                return 0
    """
    
    def __init__(self, container: Optional['Container'] = None):
        """Initialize the command.
        
        Args:
            container: Dependency injection container. If not provided,
                      a default console will be created.
        """
        self.container = container
        
        # Get or create console
        if container and hasattr(container, 'get'):
            try:
                self.console = container.get(Console)
            except:
                self.console = Console()
        else:
            self.console = Console()
        
        # Default command metadata (can be overridden)
        self._name = self._generate_default_name()
        self._description = self.__class__.__doc__ or 'No description available'
        self._help_text = self._description
    
    def _generate_default_name(self) -> str:
        """Generate a default command name from the class name."""
        class_name = self.__class__.__name__
        if class_name.endswith('Command'):
            class_name = class_name[:-7]
        return class_name.lower().replace('_', '-')
    
    @abstractmethod
    def execute(self, *args, **kwargs) -> int:
        """Execute the command logic.
        
        This method contains the actual command implementation.
        It should return an exit code (0 for success, non-zero for failure).
        
        Args:
            *args: Positional arguments passed to the command
            **kwargs: Keyword arguments passed to the command
            
        Returns:
            Exit code (0 for success, non-zero for failure)
        """
        pass
    
    def run(self, *args, **kwargs) -> int:
        """Run the command with error handling.
        
        This method wraps execute() with standardized error handling,
        including keyboard interrupt handling and exception catching.
        
        Args:
            *args: Positional arguments to pass to execute()
            **kwargs: Keyword arguments to pass to execute()
            
        Returns:
            Exit code (0 for success, non-zero for failure)
        """
        try:
            return self.execute(*args, **kwargs)
        except KeyboardInterrupt:
            self.console.print("\n[yellow]Operation cancelled by user[/]")
            return 130  # Standard exit code for SIGINT
        except Exception as e:
            self.console.print(f"[red]Error:[/] {str(e)}")
            if self.console.is_dumb_terminal:
                # Print full traceback in non-interactive terminals
                import traceback
                traceback.print_exc()
            return 1
    
    # UI Helper Methods
    
    @contextmanager
    def show_progress(self, description: str, total: Optional[int] = None):
        """Show a progress indicator while performing an operation.
        
        Args:
            description: Text to display next to the progress indicator
            total: Total number of steps (for progress bar) or None (for spinner)
            
        Yields:
            Tuple of (progress, task_id) for updating progress
            
        Example:
            with self.show_progress("Processing files", total=len(files)) as (progress, task):
                for file in files:
                    process_file(file)
                    progress.update(task, advance=1)
        """
        columns = [SpinnerColumn(), TextColumn("[progress.description]{task.description}")]
        if total is not None:
            columns.extend([BarColumn(), TextColumn("[progress.percentage]{task.percentage:>3.0f}%")])
        
        with Progress(*columns, console=self.console) as progress:
            task_id = progress.add_task(description, total=total)
            yield progress, task_id
    
    @contextmanager
    def progress_context(self, description: str, total: Optional[int] = None):
        """Context manager for progress indicators (alias for show_progress).
        
        Args:
            description: Text to display next to the progress indicator
            total: Total number of steps (for progress bar) or None (for spinner)
            
        Yields:
            Tuple of (progress, task_id) for updating progress
        """
        with self.show_progress(description, total) as (progress, task_id):
            yield progress, task_id
    
    def print_success(self, message: str) -> None:
        """Print a success message in green."""
        self.console.print(f"[green]✓[/] {message}")
    
    def print_error(self, message: str) -> None:
        """Print an error message in red."""
        self.console.print(f"[red]✗[/] {message}")
    
    def print_warning(self, message: str) -> None:
        """Print a warning message in yellow."""
        self.console.print(f"[yellow]![/] {message}")
    
    def print_info(self, message: str) -> None:
        """Print an info message in blue."""
        self.console.print(f"[blue]ℹ[/] {message}")
    
    # Validation Helper Methods
    
    @staticmethod
    def validate_port(port: str) -> bool:
        """Validate that a string represents a valid port number.
        
        Args:
            port: String to validate
            
        Returns:
            True if valid port number (1-65535), False otherwise
        """
        try:
            port_num = int(port)
            return 1 <= port_num <= 65535
        except ValueError:
            return False
    
    @staticmethod
    def check_port_available(port: int, host: str = "localhost") -> bool:
        """Check if a port is available for binding.
        
        Args:
            port: Port number to check
            host: Host to check on (default: localhost)
            
        Returns:
            True if port is available, False if in use
        """
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            try:
                sock.bind((host, port))
                return True
            except OSError:
                return False
    
    # Path Helper Methods
    
    @staticmethod
    def get_project_root() -> Path:
        """Get the current project root directory.
        
        Returns:
            Path to the current working directory
        """
        return Path.cwd()
    
    def ensure_directory(self, path: Path) -> bool:
        """Ensure a directory exists, creating it if necessary.
        
        Args:
            path: Directory path to ensure exists
            
        Returns:
            True if directory exists or was created, False on error
        """
        try:
            path.mkdir(parents=True, exist_ok=True)
            return True
        except Exception as e:
            self.print_error(f"Failed to create directory {path}: {e}")
            return False
    
    def validate_path(self, path: Path, must_exist: bool = False, must_be_dir: bool = False, must_be_file: bool = False) -> bool:
        """Validate a path according to specified criteria.
        
        Args:
            path: Path to validate
            must_exist: If True, path must exist
            must_be_dir: If True, path must be a directory
            must_be_file: If True, path must be a file
            
        Returns:
            True if path is valid according to criteria, False otherwise
        """
        if must_exist and not path.exists():
            self.print_error(f"Path does not exist: {path}")
            return False
        
        if must_be_dir and path.exists() and not path.is_dir():
            self.print_error(f"Path is not a directory: {path}")
            return False
            
        if must_be_file and path.exists() and not path.is_file():
            self.print_error(f"Path is not a file: {path}")
            return False
            
        return True
    
    # ICommand Protocol Implementation
    
    @property
    def name(self) -> str:
        """Get the command name."""
        return self._name
    
    @property
    def description(self) -> str:
        """Get the command description."""
        return self._description
    
    @property
    def help_text(self) -> str:
        """Get detailed help text for the command."""
        return self._help_text
    
    # Legacy compatibility method
    
    def run_with_error_handling(self, *args, **kwargs) -> Any:
        """Legacy method for backward compatibility.
        
        Deprecated: Use run() instead.
        """
        exit_code = self.run(*args, **kwargs)
        if exit_code != 0:
            raise RuntimeError(f"Command failed with exit code {exit_code}")
        return exit_code