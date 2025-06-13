"""MCP Server wrapper for Hyper CLI commands.

This module provides an MCP (Model Context Protocol) server that exposes
all Hyper CLI commands as MCP tools for AI integration.
"""

import contextlib
import inspect
import io
import json
import sys
import traceback
from typing import Any, Dict, List, Optional, Set

from .cli import discover_commands
from .container.simple_container import SimpleContainer


class InteractiveCommandFilter:
    """Handles detection and filtering of interactive commands."""
    
    # Commands that require interactive terminal sessions
    KNOWN_INTERACTIVE_COMMANDS: Set[str] = {
        "ui",  # hyper --ui launches ncurses interface
    }
    
    # Patterns that indicate interactive behavior
    INTERACTIVE_PATTERNS = {
        'input(': 'Uses input() for user prompts',
        'raw_input(': 'Uses raw_input() for user prompts', 
        'getch(': 'Uses getch() for character input',
        'getkey(': 'Uses getkey() for key input',
        'launch_ui(': 'Launches UI interface',
        'ncurses': 'Uses ncurses terminal interface',
        'curses': 'Uses curses terminal interface',
    }
    
    # UI-related attribute patterns
    UI_ATTRIBUTE_PATTERNS = ['launch_ui', 'ncurses', 'curses']
    
    @classmethod
    def is_interactive(cls, cmd_name: str, cmd_class: type, container) -> bool:
        """Check if a command is interactive and should be excluded from MCP."""
        # Check against known interactive commands
        if cmd_name in cls.KNOWN_INTERACTIVE_COMMANDS:
            return True
        
        # Check for interactive patterns in command implementation
        try:
            instance = cmd_class(container)
            
            # Check source code patterns
            if cls._has_interactive_source_patterns(instance):
                return True
                
            # Check attribute patterns
            if cls._has_interactive_attributes(instance):
                return True
                
        except Exception:
            # If we can't analyze the command, err on the side of caution
            # but don't exclude it unless we have a good reason
            pass
        
        return False
    
    @classmethod
    def get_interactive_reason(cls, cmd_name: str, cmd_class: type, container) -> str:
        """Get the specific reason why a command is considered interactive."""
        reasons = []
        
        # Check against known interactive commands
        if cmd_name in cls.KNOWN_INTERACTIVE_COMMANDS:
            reasons.append("Known interactive command")
        
        try:
            instance = cmd_class(container)
            
            # Check source code patterns
            source_reasons = cls._get_source_pattern_reasons(instance)
            reasons.extend(source_reasons)
            
            # Check attribute patterns
            attr_reasons = cls._get_attribute_pattern_reasons(instance)
            reasons.extend(attr_reasons)
                    
        except Exception:
            reasons.append("Could not analyze command")
        
        return "; ".join(reasons) if reasons else "Detected as interactive"
    
    @classmethod
    def _has_interactive_source_patterns(cls, instance) -> bool:
        """Check if command source code contains interactive patterns."""
        try:
            source = inspect.getsource(instance.execute)
            return any(pattern in source for pattern in cls.INTERACTIVE_PATTERNS)
        except (OSError, TypeError):
            return False
    
    @classmethod
    def _has_interactive_attributes(cls, instance) -> bool:
        """Check if command has UI-related attributes or methods."""
        for attr in dir(instance):
            attr_lower = attr.lower()
            if (attr_lower in cls.UI_ATTRIBUTE_PATTERNS or 
                attr_lower.startswith('interactive') or
                attr_lower.endswith('_ui') or
                attr_lower.startswith('ui_')):
                return True
        return False
    
    @classmethod
    def _get_source_pattern_reasons(cls, instance) -> List[str]:
        """Get reasons from source code pattern analysis."""
        reasons = []
        try:
            source = inspect.getsource(instance.execute)
            for pattern, reason in cls.INTERACTIVE_PATTERNS.items():
                if pattern in source:
                    reasons.append(reason)
        except (OSError, TypeError):
            pass
        return reasons
    
    @classmethod
    def _get_attribute_pattern_reasons(cls, instance) -> List[str]:
        """Get reasons from attribute pattern analysis."""
        for attr in dir(instance):
            attr_lower = attr.lower()
            if (attr_lower in cls.UI_ATTRIBUTE_PATTERNS or 
                attr_lower.startswith('interactive') or
                attr_lower.endswith('_ui') or
                attr_lower.startswith('ui_')):
                return [f"Has UI-related method/attribute: {attr}"]
        return []


class MCPCommandAnalyzer:
    """Analyzes commands and provides metadata for MCP integration."""
    
    def __init__(self, container, command_filter: InteractiveCommandFilter):
        self.container = container
        self.filter = command_filter
    
    def analyze_command(self, cmd_name: str, cmd_class: type) -> Optional[Dict[str, Any]]:
        """Analyze a command and return its metadata."""
        try:
            instance = cmd_class(self.container)
            return {
                "name": cmd_name,
                "description": getattr(instance, 'description', f"Command: {cmd_name}"),
                "help_text": getattr(instance, 'help_text', ''),
            }
        except Exception:
            return None
    
    def get_tool_schema(self, cmd_name: str, cmd_class: type) -> Optional[Dict[str, Any]]:
        """Generate MCP tool schema for a command."""
        try:
            instance = cmd_class(self.container)
            
            tool_schema = {
                "name": f"hyper_{cmd_name}",
                "description": getattr(instance, 'description', f"Execute hyper {cmd_name} command"),
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                    "additionalProperties": True
                }
            }
            
            # Extract parameters from execute method signature
            properties = self._extract_parameters(instance)
            if properties:
                tool_schema["inputSchema"]["properties"] = properties
                
            return tool_schema
            
        except Exception:
            return None
    
    def _extract_parameters(self, instance) -> Dict[str, Any]:
        """Extract parameter schema from command execute method."""
        try:
            sig = inspect.signature(instance.execute)
            properties = {}
            
            for param_name, param in sig.parameters.items():
                if param_name in ['args', 'kwargs']:
                    continue
                    
                prop_def = {
                    "type": "string",  # Default to string
                    "description": f"Parameter: {param_name}"
                }
                
                # Handle boolean parameters
                if param.annotation is bool or (
                    param.default != inspect.Parameter.empty and 
                    isinstance(param.default, bool)
                ):
                    prop_def["type"] = "boolean"
                
                # Handle numeric parameters
                elif param.annotation in [int, float]:
                    prop_def["type"] = "number" if param.annotation is float else "integer"
                
                # Set default if available
                if param.default != inspect.Parameter.empty:
                    prop_def["default"] = param.default
                
                properties[param_name] = prop_def
            
            return properties
            
        except Exception:
            return {}


class MCPCommandExecutor:
    """Handles execution of commands with proper output capture."""
    
    def __init__(self, container):
        self.container = container
    
    def execute_command(self, cmd_name: str, cmd_class: type, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a command with given arguments and capture output."""
        try:
            instance = cmd_class(self.container)
            
            # Apply special handling for certain commands
            arguments = self._apply_special_handling(cmd_name, arguments)
            
            # Prepare arguments for execution
            filtered_args, extra_args = self._prepare_arguments(instance, arguments)
            
            # Execute with output capture
            stdout_output, stderr_output, exit_code = self._execute_with_capture(
                instance, extra_args, filtered_args
            )
            
            # Build response
            return self._build_response(cmd_name, stdout_output, stderr_output, exit_code)
            
        except Exception as e:
            error_msg = f"Error executing command '{cmd_name}': {str(e)}"
            traceback_str = traceback.format_exc()
            
            return {
                "content": [
                    {"type": "text", "text": error_msg},
                    {"type": "text", "text": f"Traceback:\n{traceback_str}"}
                ],
                "isError": True
            }
    
    def _apply_special_handling(self, cmd_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Apply special handling for specific commands."""
        # Make a copy to avoid modifying the original
        args = dict(arguments)
        
        # Always force init command to avoid interactive prompts
        if cmd_name == "init":
            args["force"] = True
            
        return args
    
    def _prepare_arguments(self, instance, arguments: Dict[str, Any]) -> tuple:
        """Prepare arguments for command execution."""
        sig = inspect.signature(instance.execute)
        
        filtered_args = {}
        extra_args = []
        
        for param_name, param in sig.parameters.items():
            if param_name == 'args' and param.kind == inspect.Parameter.VAR_POSITIONAL:
                # Handle *args
                if 'args' in arguments:
                    extra_args = arguments['args'] if isinstance(arguments['args'], list) else [arguments['args']]
            elif param_name in arguments:
                filtered_args[param_name] = arguments[param_name]
        
        return filtered_args, extra_args
    
    def _execute_with_capture(self, instance, extra_args: List, filtered_args: Dict) -> tuple:
        """Execute command with stdout/stderr capture."""
        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()
        
        with contextlib.redirect_stdout(stdout_capture), contextlib.redirect_stderr(stderr_capture):
            if extra_args:
                exit_code = instance.execute(*extra_args, **filtered_args)
            else:
                exit_code = instance.execute(**filtered_args)
        
        return stdout_capture.getvalue(), stderr_capture.getvalue(), exit_code
    
    def _build_response(self, cmd_name: str, stdout_output: str, stderr_output: str, exit_code: int) -> Dict[str, Any]:
        """Build MCP response from command execution results."""
        content = []
        
        if stdout_output.strip():
            content.append({"type": "text", "text": f"Output:\n{stdout_output.strip()}"})
        
        if stderr_output.strip():
            content.append({"type": "text", "text": f"Errors:\n{stderr_output.strip()}"})
        
        if exit_code == 0:
            if not content:
                content = [{"type": "text", "text": f"Command '{cmd_name}' executed successfully"}]
            return {"content": content}
        else:
            content.append({"type": "text", "text": f"Command '{cmd_name}' failed with exit code {exit_code}"})
            return {
                "content": content,
                "isError": True
            }


class MCPServer:
    """MCP server that wraps Hyper CLI commands."""

    def __init__(self):
        """Initialize the MCP server."""
        self.container = SimpleContainer()
        self._initialize_plugins()
        self.registry = discover_commands()
        
        # Initialize components
        self.command_filter = InteractiveCommandFilter()
        self.command_analyzer = MCPCommandAnalyzer(self.container, self.command_filter)
        self.command_executor = MCPCommandExecutor(self.container)

    def _initialize_plugins(self) -> None:
        """Initialize the plugin registry."""
        # Use force_reinitialize to avoid warning when already initialized
        from .plugins.registry import plugin_registry
        plugin_registry.initialize(force_reinitialize=True)

    def get_command_info(self) -> Dict[str, Any]:
        """Get comprehensive command information including filtered commands."""
        available_commands = []
        interactive_commands = []
        
        for cmd_name in self.registry.list_commands():
            cmd_class = self.registry.get(cmd_name)
            if not cmd_class:
                continue
                
            command_info = self.command_analyzer.analyze_command(cmd_name, cmd_class)
            if not command_info:
                continue
            
            if self.command_filter.is_interactive(cmd_name, cmd_class, self.container):
                reason = self.command_filter.get_interactive_reason(cmd_name, cmd_class, self.container)
                command_info["interactive_reason"] = reason
                interactive_commands.append(command_info)
            else:
                available_commands.append(command_info)
        
        return {
            "available_commands": available_commands,
            "interactive_commands": interactive_commands,
            "total_commands": len(available_commands) + len(interactive_commands),
            "available_count": len(available_commands),
            "interactive_count": len(interactive_commands)
        }

    def get_tools(self) -> List[Dict[str, Any]]:
        """Get all available tools (commands) for MCP."""
        tools = []
        
        for cmd_name in self.registry.list_commands():
            cmd_class = self.registry.get(cmd_name)
            if not cmd_class:
                continue
                
            # Skip interactive commands
            if self.command_filter.is_interactive(cmd_name, cmd_class, self.container):
                continue
                
            tool_schema = self.command_analyzer.get_tool_schema(cmd_name, cmd_class)
            if tool_schema:
                tools.append(tool_schema)
        
        return tools

    def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool (command) with given arguments."""
        # Extract command name from tool name
        if not tool_name.startswith("hyper_"):
            return {
                "content": [{"type": "text", "text": f"Invalid tool name: {tool_name}"}],
                "isError": True
            }
        
        cmd_name = tool_name[6:]  # Remove "hyper_" prefix
        
        # Get command class
        cmd_class = self.registry.get(cmd_name)
        if not cmd_class:
            return {
                "content": [{"type": "text", "text": f"Command not found: {cmd_name}"}],
                "isError": True
            }
        
        # Double-check that this isn't an interactive command
        if self.command_filter.is_interactive(cmd_name, cmd_class, self.container):
            return {
                "content": [{"type": "text", "text": f"Command '{cmd_name}' is interactive and cannot be executed via MCP"}],
                "isError": True
            }
        
        # Execute the command
        return self.command_executor.execute_command(cmd_name, cmd_class, arguments)

    def get_resources(self) -> List[Dict[str, Any]]:
        """Get available MCP resources."""
        return [
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

    def read_resource(self, uri: str) -> Dict[str, Any]:
        """Read a specific MCP resource."""
        command_info = self.get_command_info()
        
        resource_handlers = {
            "hyper://commands/available": self._handle_available_resource,
            "hyper://commands/interactive": self._handle_interactive_resource,
            "hyper://commands/all": self._handle_all_resource,
        }
        
        handler = resource_handlers.get(uri)
        if not handler:
            raise ValueError(f"Unknown resource URI: {uri}")
        
        return handler(uri, command_info)
    
    def _handle_available_resource(self, uri: str, command_info: Dict[str, Any]) -> Dict[str, Any]:
        """Handle the available commands resource."""
        return {
            "contents": [
                {
                    "uri": uri,
                    "mimeType": "application/json",
                    "text": json.dumps({
                        "commands": command_info["available_commands"],
                        "count": command_info["available_count"],
                        "description": "Commands that can be executed via MCP tools"
                    }, indent=2)
                }
            ]
        }
    
    def _handle_interactive_resource(self, uri: str, command_info: Dict[str, Any]) -> Dict[str, Any]:
        """Handle the interactive commands resource."""
        return {
            "contents": [
                {
                    "uri": uri,
                    "mimeType": "application/json", 
                    "text": json.dumps({
                        "commands": command_info["interactive_commands"],
                        "count": command_info["interactive_count"],
                        "description": "Commands that require interactive terminal sessions and cannot be executed via MCP",
                        "note": "These commands are filtered out for safety - they require user input, terminal UI, or other interactive features"
                    }, indent=2)
                }
            ]
        }
    
    def _handle_all_resource(self, uri: str, command_info: Dict[str, Any]) -> Dict[str, Any]:
        """Handle the all commands resource."""
        return {
            "contents": [
                {
                    "uri": uri,
                    "mimeType": "application/json",
                    "text": json.dumps({
                        "summary": {
                            "total_commands": command_info["total_commands"],
                            "available_via_mcp": command_info["available_count"], 
                            "filtered_interactive": command_info["interactive_count"]
                        },
                        "available_commands": command_info["available_commands"],
                        "interactive_commands": command_info["interactive_commands"],
                        "description": "Complete overview of all Hyper commands and their MCP availability"
                    }, indent=2)
                }
            ]
        }

    def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle MCP request."""
        method = request.get("method")
        params = request.get("params", {})
        request_id = request.get("id")
        
        try:
            # Route request to appropriate handler
            result = self._route_request(method, params)
                
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": result
            }
            
        except Exception as e:
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {str(e)}"
                }
            }
    
    def _route_request(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Route request to appropriate handler method."""
        handlers = {
            "tools/list": lambda p: {"tools": self.get_tools()},
            "tools/call": lambda p: self.execute_tool(p.get("name"), p.get("arguments", {})),
            "resources/list": lambda p: {"resources": self.get_resources()},
            "resources/read": lambda p: self.read_resource(p.get("uri")),
        }
        
        handler = handlers.get(method)
        if not handler:
            return {
                "error": {
                    "code": -32601,
                    "message": f"Method not found: {method}"
                }
            }
        
        return handler(params)

    def run_server(self) -> None:
        """Run the MCP server (stdio mode)."""
        for line in sys.stdin:
            try:
                request = json.loads(line.strip())
                response = self.handle_request(request)
                print(json.dumps(response), flush=True)
            except json.JSONDecodeError:
                error_response = {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {
                        "code": -32700,
                        "message": "Parse error"
                    }
                }
                print(json.dumps(error_response), flush=True)
            except Exception as e:
                error_response = {
                    "jsonrpc": "2.0", 
                    "id": None,
                    "error": {
                        "code": -32603,
                        "message": f"Internal error: {str(e)}"
                    }
                }
                print(json.dumps(error_response), flush=True)


def main() -> None:
    """Main entry point for MCP server."""
    server = MCPServer()
    server.run_server()


if __name__ == "__main__":
    main()