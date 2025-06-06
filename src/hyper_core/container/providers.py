"""Provider definitions for hyper services.

This module defines custom providers and helper functions for the
dependency injection container.
"""

from typing import Dict, Any, Callable, TypeVar
from dependency_injector import providers

T = TypeVar('T')


def service_config_params(config_manager: providers.Provider, 
                         config_mapping: Dict[str, str]) -> Dict[str, Any]:
    """Helper to map ConfigManager methods to service parameters.
    
    Args:
        config_manager: Provider for ConfigManager instance
        config_mapping: Dict mapping parameter names to ConfigManager method names
        
    Returns:
        Dict of parameters with providers for lazy evaluation
    """
    params = {}
    for param_name, method_name in config_mapping.items():
        params[param_name] = providers.Factory(
            lambda cm=config_manager, mn=method_name: getattr(cm(), mn)()
        )
    return params


class ConsoleProvider(providers.Provider):
    """Provider that returns the registered console instance.
    
    This provider is used to inject the Rich console instance that
    is created externally and passed to the container.
    """
    
    def __init__(self, console_instance=None):
        self._console = console_instance
        super().__init__()
    
    def _provide(self, args, kwargs):
        if self._console is None:
            raise RuntimeError("Console instance not set in provider")
        return self._console
    
    def set_console(self, console):
        """Set the console instance."""
        self._console = console