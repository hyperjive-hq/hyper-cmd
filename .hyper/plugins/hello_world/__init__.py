"""Hello World Example Plugin.

This is an example plugin that demonstrates the basic structure
and capabilities of Hyper Core plugins.
"""

# Make the plugin module importable
from .plugin import (
    PLUGIN_AUTHOR as PLUGIN_AUTHOR,
)
from .plugin import (
    PLUGIN_DEPENDENCIES as PLUGIN_DEPENDENCIES,
)
from .plugin import (
    PLUGIN_DESCRIPTION as PLUGIN_DESCRIPTION,
)
from .plugin import (
    PLUGIN_NAME as PLUGIN_NAME,
)
from .plugin import (
    PLUGIN_VERSION as PLUGIN_VERSION,
)
from .plugin import (
    HelloCommand as HelloCommand,
)
from .plugin import (
    HelloService as HelloService,
)
from .plugin import (
    HelloWidget as HelloWidget,
)
from .plugin import (
    logger as logger,
)
from .plugin import (
    register_plugin as register_plugin,
)
