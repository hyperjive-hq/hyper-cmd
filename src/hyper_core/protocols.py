"""Protocol definitions for the Hyper framework.

This module defines the interfaces (protocols) that components must implement
to be compatible with the Hyper plugin architecture. These protocols ensure
consistency and enable runtime type checking for plugin compatibility.

Example:
    To create a custom command that implements ICommand::

        class MyCommand(BaseCommand):
            @property
            def name(self) -> str:
                return "mycommand"

            def execute(self, *args, **kwargs) -> int:
                print("Hello from MyCommand!")
                return 0
"""

from abc import abstractmethod
from typing import Any, Optional, Protocol, runtime_checkable

# Core Component Protocols


@runtime_checkable
class ICommand(Protocol):
    """Protocol for command implementations in the Hyper framework.

    Commands are the primary way users interact with Hyper functionality.
    Each command should have a unique name and provide clear help text.

    The command lifecycle is:
    1. Command instance is created with a container
    2. run() is called, which sets up error handling
    3. execute() is called with the actual command logic
    4. Exit code is returned (0 for success, non-zero for failure)
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """The unique identifier for this command."""
        ...

    @property
    @abstractmethod
    def description(self) -> str:
        """A brief description of what the command does."""
        ...

    @property
    @abstractmethod
    def help_text(self) -> str:
        """Detailed help text including usage examples."""
        ...

    @abstractmethod
    def execute(self, *args, **kwargs) -> int:
        """
        Execute the command's core logic.

        This method should contain the main functionality of the command.
        It's called by run() after error handling is set up.

        Args:
            *args: Positional arguments passed to the command
            **kwargs: Keyword arguments passed to the command

        Returns:
            Exit code (0 for success, non-zero for failure)
        """
        ...

    @abstractmethod
    def run(self, *args, **kwargs) -> int:
        """
        Run the command with standardized error handling.

        This method wraps execute() with proper error handling,
        logging, and cleanup. Users should call this method.

        Args:
            *args: Positional arguments passed to the command
            **kwargs: Keyword arguments passed to the command

        Returns:
            Exit code (0 for success, non-zero for failure)
        """
        ...


@runtime_checkable
class IWidget(Protocol):
    """
    Protocol for widget implementations in the Hyper dashboard.

    Widgets are visual components that display information or provide
    interaction in the terminal-based dashboard interface.
    """

    @property
    @abstractmethod
    def title(self) -> str:
        """The title displayed at the top of the widget."""
        ...

    @abstractmethod
    def draw(self, stdscr: Any, x: int, y: int, width: int, height: int) -> None:
        """
        Render the widget to the terminal screen.

        Args:
            stdscr: The curses screen object
            x: X coordinate of the top-left corner
            y: Y coordinate of the top-left corner
            width: Available width in characters
            height: Available height in lines
        """
        ...

    @abstractmethod
    def refresh_data(self) -> None:
        """Update the widget's internal data from its data source."""
        ...

    @abstractmethod
    def get_minimum_size(self) -> tuple[int, int]:
        """
        Get the minimum dimensions required for this widget.

        Returns:
            Tuple of (min_width, min_height) in characters
        """
        ...

    @abstractmethod
    def handle_input(self, key: int) -> bool:
        """
        Process keyboard input when this widget has focus.

        Args:
            key: The key code pressed

        Returns:
            True if the input was handled, False to pass to parent
        """
        ...

    @abstractmethod
    def handle_mouse(self, mx: int, my: int, bstate: int, widget_x: int, widget_y: int) -> bool:
        """
        Process mouse events for this widget.

        Args:
            mx: Mouse X coordinate (absolute screen position)
            my: Mouse Y coordinate (absolute screen position)
            bstate: Mouse button state flags
            widget_x: Widget's X position on screen
            widget_y: Widget's Y position on screen

        Returns:
            True if the event was handled, False to pass to parent
        """
        ...

    @abstractmethod
    def on_resize(self, width: int, height: int) -> None:
        """
        Handle terminal resize events.

        Args:
            width: New width in characters
            height: New height in lines
        """
        ...


@runtime_checkable
class IPage(Protocol):
    """
    Protocol for page implementations in the Hyper menu system.

    Pages represent full-screen views in the menu system, typically
    accessed through menu navigation.
    """

    @property
    @abstractmethod
    def title(self) -> str:
        """The page title shown in the header."""
        ...

    @property
    @abstractmethod
    def description(self) -> str:
        """A brief description of the page's purpose."""
        ...

    @abstractmethod
    def draw(self, stdscr: Any, start_y: int, height: int, width: int) -> None:
        """
        Render the page content.

        Args:
            stdscr: The curses screen object
            start_y: Y coordinate to start drawing (below header)
            height: Available height for content
            width: Available width for content
        """
        ...

    @abstractmethod
    def handle_input(self, key: int) -> Optional[str]:
        """
        Process keyboard input for this page.

        Args:
            key: The key code pressed

        Returns:
            Navigation command ('back', 'exit', etc.) or None to stay on page
        """
        ...

    @abstractmethod
    def refresh(self) -> None:
        """Update the page's data and trigger a redraw."""
        ...

    @abstractmethod
    def on_enter(self) -> None:
        """Called when the page becomes active."""
        ...

    @abstractmethod
    def on_exit(self) -> None:
        """Called when the page is about to be deactivated."""
        ...


@runtime_checkable
class IService(Protocol):
    """
    Protocol for service implementations in the Hyper framework.

    Services are long-running components that provide functionality
    to other parts of the system. They follow a standard lifecycle
    with initialization, health checking, and shutdown.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """The unique identifier for this service."""
        ...

    @property
    @abstractmethod
    def is_initialized(self) -> bool:
        """Whether the service has been successfully initialized."""
        ...

    @abstractmethod
    def initialize(self, config: Optional[dict[str, Any]] = None) -> None:
        """
        Initialize the service with optional configuration.

        This method should be idempotent - calling it multiple times
        should have no effect if already initialized.

        Args:
            config: Optional configuration dictionary

        Raises:
            Exception: If initialization fails
        """
        ...

    @abstractmethod
    def shutdown(self) -> None:
        """
        Gracefully shutdown the service and release resources.

        This method should be idempotent and safe to call even
        if the service was never initialized.
        """
        ...

    @abstractmethod
    def health_check(self) -> dict[str, Any]:
        """
        Perform a health check on the service.

        Returns:
            Dictionary containing at minimum:
            - 'service': str - The service name
            - 'healthy': bool - Overall health status
            - 'timestamp': float - Check timestamp
            - Additional service-specific health metrics
        """
        ...

    @abstractmethod
    def get_status(self) -> dict[str, Any]:
        """
        Get detailed service status information.

        Returns:
            Dictionary containing at minimum:
            - 'service': str - The service name
            - 'initialized': bool - Initialization status
            - 'timestamp': float - Status timestamp
            - Additional service-specific status details
        """
        ...


# Plugin System Protocols


@runtime_checkable
class IPlugin(Protocol):
    """
    Protocol for plugin implementations.

    Plugins extend Hyper's functionality by providing new commands,
    widgets, pages, and services in a modular way.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """The unique identifier for this plugin."""
        ...

    @property
    @abstractmethod
    def version(self) -> str:
        """The plugin version (recommended: semantic versioning)."""
        ...

    @property
    @abstractmethod
    def description(self) -> str:
        """A brief description of the plugin's functionality."""
        ...

    @abstractmethod
    def initialize(self, container: Any) -> None:
        """
        Initialize the plugin with access to the DI container.

        Args:
            container: The dependency injection container for accessing services

        Raises:
            Exception: If plugin initialization fails
        """
        ...

    @abstractmethod
    def register(self) -> dict[str, list[Any]]:
        """
        Register all components provided by this plugin.

        Returns:
            Dictionary mapping component types to lists of component classes:
            {
                'commands': [CommandClass1, CommandClass2, ...],
                'widgets': [WidgetClass1, WidgetClass2, ...],
                'pages': [PageClass1, PageClass2, ...],
                'services': [ServiceClass1, ServiceClass2, ...]
            }
        """
        ...

    @abstractmethod
    def shutdown(self) -> None:
        """Clean up any resources allocated by the plugin."""
        ...


# Configuration Protocols


@runtime_checkable
class IConfigurable(Protocol):
    """
    Protocol for components that support runtime configuration.

    Configurable components can validate and apply configuration
    changes without requiring a restart.
    """

    @abstractmethod
    def get_config_schema(self) -> dict[str, Any]:
        """
        Get the JSON Schema for configuration validation.

        Returns:
            JSON Schema dictionary describing valid configuration
        """
        ...

    @abstractmethod
    def validate_config(self, config: dict[str, Any]) -> tuple[bool, Optional[str]]:
        """
        Validate a configuration dictionary.

        Args:
            config: Configuration dictionary to validate

        Returns:
            Tuple of (is_valid, error_message)
            error_message is None if valid, descriptive string if invalid
        """
        ...

    @abstractmethod
    def apply_config(self, config: dict[str, Any]) -> None:
        """
        Apply a validated configuration to this component.

        Args:
            config: Pre-validated configuration dictionary

        Raises:
            Exception: If configuration cannot be applied
        """
        ...


# Data Provider Protocols


@runtime_checkable
class IDataProvider(Protocol):
    """
    Protocol for data providers used by widgets and other components.

    Data providers abstract the source of data from its presentation,
    allowing widgets to display data from various sources.
    """

    @abstractmethod
    def fetch_data(self) -> Any:
        """
        Fetch the current data from this provider.

        Returns:
            The fetched data in provider-specific format

        Raises:
            Exception: If data cannot be fetched
        """
        ...

    @abstractmethod
    def is_available(self) -> bool:
        """
        Check if the data provider is currently available.

        Returns:
            True if data can be fetched, False otherwise
        """
        ...

    @property
    @abstractmethod
    def refresh_interval(self) -> Optional[int]:
        """
        Get the recommended refresh interval for this data.

        Returns:
            Seconds between refreshes, or None for no auto-refresh
        """
        ...


# UI Protocols


@runtime_checkable
class IThemeable(Protocol):
    """
    Protocol for components that support theming.

    Themeable components can change their appearance based on
    the current theme without requiring code changes.
    """

    @abstractmethod
    def set_theme(self, theme: Any) -> None:
        """
        Apply a theme to this component.

        Args:
            theme: Theme object containing colors, styles, etc.
        """
        ...

    @abstractmethod
    def get_theme(self) -> Any:
        """
        Get the currently applied theme.

        Returns:
            The current theme object
        """
        ...
