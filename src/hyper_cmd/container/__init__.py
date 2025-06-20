"""Dependency injection container components.

This module provides two container implementations:
1. SimpleContainer - Basic DI for plugins and simple use cases
2. BaseHyperContainer - Full-featured DI using dependency-injector library
"""

from .base_container import BaseHyperContainer, configure_container, create_container
from .providers import ConsoleProvider, service_config_params
from .simple_container import SimpleContainer

__all__ = [
    "SimpleContainer",
    "BaseHyperContainer",
    "create_container",
    "configure_container",
    "ConsoleProvider",
    "service_config_params",
]
