"""Base dependency injection container for the Hyper Core framework.

This module provides a base container that can be extended by applications
using the Hyper Core framework.
"""

from dependency_injector import containers, providers
from typing import Any, Optional

from .providers import ConsoleProvider


class BaseHyperContainer(containers.DeclarativeContainer):
    """Base IoC container for Hyper Core framework.
    
    This container provides core framework services that can be extended
    by applications. It follows these principles:
    - Services are singletons by default
    - Services are lazy-loaded on first access
    - Services can be overridden for testing
    - External dependencies (like console) are injected
    """
    
    # Configuration
    config = providers.Configuration()
    
    # External console instance (set during initialization)
    console = ConsoleProvider()
    
    # Plugin registry (to be set by the application)
    plugin_registry = providers.Object(None)


# Container configuration helpers

def create_container(**overrides) -> BaseHyperContainer:
    """Create a new container instance with optional overrides.
    
    Args:
        **overrides: Service overrides for testing or customization
        
    Returns:
        Configured container instance
    """
    container = BaseHyperContainer()
    if overrides:
        container.override_providers(**overrides)
    return container


def configure_container(container: BaseHyperContainer, 
                       console: Optional[Any] = None,
                       config: Optional[dict] = None) -> None:
    """Configure a container instance.
    
    Args:
        container: Container instance to configure
        console: Optional console instance to inject
        config: Optional configuration dictionary
    """
    if console:
        container.console.set_console(console)
    
    if config:
        container.config.from_dict(config)
    
    # Reset singletons after configuration changes
    container.reset_singletons()