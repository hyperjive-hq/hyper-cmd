"""Simple container implementation for basic dependency injection.

This module provides a lightweight dependency injection container that plugin
authors can use without needing to understand the complexity of the full
dependency-injector library.

Example:
    Basic usage of SimpleContainer::

        from hyper_core.container import SimpleContainer
        from rich.console import Console

        # Create container
        container = SimpleContainer()

        # Register a service instance
        console = Console()
        container.register(Console, console)

        # Register a factory function
        container.register_factory(MyService, lambda: MyService(console))

        # Retrieve services
        my_service = container.get(MyService)
"""

from typing import Any, Callable, Optional, TypeVar

T = TypeVar("T")


class SimpleContainer:
    """Simple dependency injection container.

    This container provides basic dependency injection functionality:
    - Service registration and retrieval
    - Factory functions for lazy instantiation
    - Singleton management (services are cached after first creation)

    This is designed to be easy to understand and use, making it ideal
    for plugin authors who need basic DI without complexity.
    """

    def __init__(self) -> None:
        """Initialize an empty container."""
        self._services: dict[type, Any] = {}
        self._factories: dict[type, Callable[[], Any]] = {}

    def register(self, service_type: type[T], instance: T) -> None:
        """Register a service instance.

        Args:
            service_type: The type to register the instance as
            instance: The service instance
        """
        self._services[service_type] = instance

    def register_factory(self, service_type: type[T], factory: Callable[[], T]) -> None:
        """Register a factory function for a service.

        Args:
            service_type: The type to register the factory for
            factory: Function that creates instances of the service
        """
        self._factories[service_type] = factory

    def get(self, service_type: type[T]) -> T:
        """Get a service instance.

        If the service was registered as an instance, returns that instance.
        If registered as a factory, calls the factory once and caches the result.

        Args:
            service_type: The type of service to retrieve

        Returns:
            The service instance

        Raises:
            ValueError: If the service is not registered

        Example:
            console = container.get(Console)  # Returns the registered Console instance
        """
        # Return cached instance if available
        if service_type in self._services:
            return self._services[service_type]  # type: ignore[return-value]

        # Create instance from factory if available
        if service_type in self._factories:
            instance = self._factories[service_type]()
            # Cache for future use (singleton behavior)
            self._services[service_type] = instance
            return instance  # type: ignore[return-value]

        # Service not found
        service_name = getattr(service_type, "__name__", str(service_type))
        available_services = list(self._services.keys()) + list(self._factories.keys())
        available_names = [getattr(svc, "__name__", str(svc)) for svc in available_services]

        raise ValueError(
            f"Service '{service_name}' not registered. "
            f"Available services: {available_names}. "
            f"Use register() or register_factory() to add it first."
        )

    def get_optional(self, service_type: type[T]) -> Optional[T]:
        """Get a service instance if it exists.

        Args:
            service_type: The type of service to retrieve

        Returns:
            The service instance or None if not registered
        """
        try:
            return self.get(service_type)
        except ValueError:
            return None

    def has(self, service_type: type) -> bool:
        """Check if a service is registered.

        Args:
            service_type: The type to check

        Returns:
            True if the service is registered
        """
        return service_type in self._services or service_type in self._factories

    def clear(self) -> None:
        """Clear all registered services and factories."""
        self._services.clear()
        self._factories.clear()

    def reset_singletons(self) -> None:
        """Reset singleton instances (keeps factories registered)."""
        # Only keep services that don't have factories
        self._services = {
            svc_type: instance
            for svc_type, instance in self._services.items()
            if svc_type not in self._factories
        }
