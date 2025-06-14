# Hyper MCP Server

This document describes the Model Context Protocol (MCP) server wrapper for the Hyper CLI framework, which allows AI systems to interact with all Hyper commands through a standardized protocol.

## Overview

The MCP server exposes all Hyper CLI commands as MCP tools, enabling AI agents to:
- Discover available Hyper commands and plugins
- Execute commands with proper parameter handling
- Receive structured responses with captured output
- Handle errors gracefully

## Installation & Quick Setup

The MCP server is included with Hyper Core and can be set up easily:

```bash
# 1. Install Hyper Core (if not already installed)
pip install -e .

# 2. Generate MCP configuration automatically
hyper init-mcp

# 3. Run the MCP server
hyper-mcp
```

### Automatic Configuration Generation

The `hyper init-mcp` command creates a `.mcp.json` file with the correct configuration:

```bash
# Generate .mcp.json in current directory
hyper init-mcp

# Force overwrite existing config
hyper init-mcp --force

# Save to specific location
hyper init-mcp --config-path /path/to/directory
```

## Configuration

### MCP Client Configuration

**Easy way:** Use the built-in command to generate configuration automatically:

```bash
hyper init-mcp
```

**Manual way:** Add the following to your MCP client configuration (e.g., Claude Code, etc.):

```json
{
  "mcpServers": {
    "hyper-core": {
      "command": "hyper-mcp",
      "args": [],
      "env": {},
      "description": "Hyper CLI commands via MCP for AI integration"
    }
  }
}
```

### Example Configuration Files

The `hyper init-mcp` command generates a complete `.mcp.json` file. A sample is also provided at `mcp-config.json`:

```json
{
  "mcpServers": {
    "hyper-core": {
      "command": "hyper-mcp",
      "args": [],
      "env": {},
      "description": "Hyper CLI commands via MCP for AI integration"
    }
  }
}
```

## Available Tools

The MCP server automatically discovers and exposes all **non-interactive** Hyper commands as tools. Interactive commands that require terminal input or UI interaction are filtered out for safety.

Each tool follows the naming convention `hyper_<command_name>`. For example:

- `hyper_init` - Initialize a new Hyper project (automatically uses --force flag)
- `hyper_init-mcp` - **Generate MCP configuration for AI integration** 
- `hyper_hello` - Example command from plugins  
- `hyper_test` - Run project tests
- `hyper_testinfo` - Show test environment information
- `hyper_<plugin_command>` - Commands from loaded plugins (if non-interactive)

### Interactive Command Filtering

The following types of commands are **automatically excluded** from MCP:

- **UI Commands**: Commands that launch ncurses/terminal UI (e.g., `hyper --ui`)
- **Interactive Commands**: Commands that prompt for user input
- **Commands with Interactive Patterns**: Commands detected to have interactive code patterns

### Special Handling

- **Init Command**: The `hyper_init` tool automatically applies the `--force` flag to bypass interactive prompts, making it safe for AI use

### Tool Discovery

Tools are discovered dynamically by:
1. Scanning built-in commands (like `init`)
2. Loading and discovering plugin commands
3. Analyzing command signatures to generate parameter schemas
4. Filtering out interactive commands for safety

### MCP Resources

The server provides additional resources to help AI agents understand command availability:

- **`hyper://commands/available`** - List of commands that can be executed via MCP
- **`hyper://commands/interactive`** - List of commands filtered out due to interactive requirements
- **`hyper://commands/all`** - Complete overview of all commands and their availability status

These resources allow AI agents to:
- Explain to users why certain commands aren't available
- Provide alternative suggestions for interactive commands
- Show comprehensive help about the Hyper CLI capabilities

## Protocol Details

### Methods Supported

#### `tools/list`

Returns a list of available tools with their schemas.

**Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/list",
  "params": {}
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "tools": [
      {
        "name": "hyper_init",
        "description": "Initialize a new Hyper project",
        "inputSchema": {
          "type": "object",
          "properties": {
            "force": {
              "type": "boolean",
              "description": "Parameter: force",
              "default": false
            }
          },
          "additionalProperties": true
        }
      }
    ]
  }
}
```

#### `tools/call`

Executes a specific tool with given arguments.

**Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "tools/call",
  "params": {
    "name": "hyper_hello",
    "arguments": {
      "name": "MCP User"
    }
  }
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "Output:\nHello, MCP User!\n✓ ✓ Completed 1 greeting(s)"
      }
    ]
  }
}
```

#### `resources/list`

Returns available MCP resources for additional information.

**Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "method": "resources/list",
  "params": {}
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "result": {
    "resources": [
      {
        "uri": "hyper://commands/available",
        "name": "Available Hyper Commands",
        "description": "List of Hyper commands that can be executed via MCP",
        "mimeType": "application/json"
      },
      {
        "uri": "hyper://commands/interactive",
        "name": "Interactive Hyper Commands", 
        "description": "List of Hyper commands that are filtered out due to interactive requirements",
        "mimeType": "application/json"
      },
      {
        "uri": "hyper://commands/all",
        "name": "All Hyper Commands Information",
        "description": "Complete information about all Hyper commands including availability status",
        "mimeType": "application/json"
      }
    ]
  }
}
```

#### `resources/read`

Reads a specific resource to get detailed command information.

**Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 4,
  "method": "resources/read",
  "params": {
    "uri": "hyper://commands/interactive"
  }
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 4,
  "result": {
    "contents": [
      {
        "uri": "hyper://commands/interactive",
        "mimeType": "application/json",
        "text": "{\n  \"commands\": [\n    {\n      \"name\": \"ui\",\n      \"description\": \"Launch interactive UI\",\n      \"interactive_reason\": \"Known interactive command; Launches UI interface\"\n    }\n  ],\n  \"count\": 1,\n  \"description\": \"Commands that require interactive terminal sessions and cannot be executed via MCP\",\n  \"note\": \"These commands are filtered out for safety - they require user input, terminal UI, or other interactive features\"\n}"
      }
    ]
  }
}
```

### Error Handling

The server provides comprehensive error handling:

- **Invalid method**: Returns `-32601` error code
- **Command not found**: Returns tool execution error with `isError: true`
- **Command failure**: Captures exit codes and error output
- **Exception handling**: Full traceback information for debugging

**Error Response Example:**
```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "Error executing command 'invalid': Command not found: invalid"
      }
    ],
    "isError": true
  }
}
```

## Output Capture

The MCP server captures both stdout and stderr from command execution:

- **stdout**: Command output (user-facing messages)
- **stderr**: Error messages and warnings
- **Exit codes**: Properly handled and reported

Output is structured in the response for easy parsing by AI systems.

## Testing

Test the MCP server functionality:

```bash
# Run the included test suite
python test_mcp.py

# Manual testing with direct command
echo '{"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}' | hyper-mcp
```

## Plugin Integration

The MCP server automatically discovers commands from:

1. **Built-in commands**: Core Hyper commands like `init`
2. **Plugin commands**: Commands from loaded plugins in `.hyper/plugins/`
3. **Dynamic discovery**: New plugins are discovered at runtime

### Plugin Command Example

If you have a plugin with a command class:

```python
from hyper_core.commands.base import BaseCommand

class CustomCommand(BaseCommand):
    @property
    def name(self) -> str:
        return "custom"
    
    @property 
    def description(self) -> str:
        return "My custom command"
    
    def execute(self, arg1: str = "default", flag: bool = False) -> int:
        self.console.print(f"Running custom command with {arg1}, flag={flag}")
        return 0
```

This automatically becomes available as `hyper_custom` in the MCP server with proper parameter schema generation.

## Architecture

The MCP server consists of:

1. **MCPServer class**: Main server implementation
2. **Tool discovery**: Dynamic command and plugin scanning
3. **Parameter introspection**: Automatic schema generation from command signatures
4. **Output capture**: Clean separation of command output from protocol responses
5. **Error handling**: Comprehensive error reporting and recovery

## Security Considerations

- Commands execute with the same permissions as the user running the MCP server
- No additional authentication is provided beyond the MCP transport layer
- Command output is captured and returned - be aware of sensitive information
- File system access is limited to what the Hyper commands allow
- **Interactive commands are automatically filtered out** to prevent hanging or unsafe operations
- The `init` command automatically uses `--force` flag to avoid interactive prompts

## Troubleshooting

### Common Issues

1. **"Plugin registry already initialized"**: This is a warning, not an error. It occurs when the plugin system is initialized multiple times.

2. **Commands not appearing**: Ensure plugins are properly installed in `.hyper/plugins/` directory.

3. **JSON parse errors**: Check that the MCP client is sending properly formatted JSON-RPC 2.0 requests.

### Debug Mode

Enable debug logging by setting environment variables:

```bash
export PYTHONPATH=src:$PYTHONPATH
export HYPER_DEBUG=1
hyper-mcp
```

### Manual Testing

Test individual components:

```python
from hyper_core.mcp_server import MCPServer

# Create server and test tool discovery
server = MCPServer()
tools = server.get_tools()
print(f"Found {len(tools)} tools")

# Test command execution
result = server.execute_tool("hyper_hello", {"name": "Test"})
print(result)
```

## Contributing

To extend the MCP server:

1. Commands are automatically discovered - just create new command classes
2. Follow the `BaseCommand` interface for proper integration
3. Add tests to `test_mcp.py` for new functionality
4. Update this documentation for significant changes

## Future Enhancements

Potential improvements:

- Authentication and authorization
- Streaming support for long-running commands
- Progress reporting for multi-step operations
- Resource management for concurrent requests
- Configuration options for output capture