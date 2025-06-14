"""Comprehensive tests for MCP server functionality."""

import json
from unittest.mock import Mock, patch

import pytest

from hyper_cmd.commands.base import BaseCommand
from hyper_cmd.container.simple_container import SimpleContainer
from hyper_cmd.mcp_server import (
    InteractiveCommandFilter,
    MCPCommandAnalyzer,
    MCPCommandExecutor,
    MCPServer,
)


class MockInteractiveCommand(BaseCommand):
    """Mock command that should be filtered as interactive."""

    def __init__(self, container):
        super().__init__(container)

    @property
    def name(self) -> str:
        return "mock-interactive"

    @property
    def description(self) -> str:
        return "Mock interactive command"

    def execute(self) -> int:
        # This contains interactive patterns
        input("Enter something: ")
        return 0


class MockSafeCommand(BaseCommand):
    """Mock command that should be allowed."""

    def __init__(self, container):
        super().__init__(container)

    @property
    def name(self) -> str:
        return "mock-safe"

    @property
    def description(self) -> str:
        return "Mock safe command"

    def execute(self, arg1: str = "default", flag: bool = False) -> int:
        return 0


class MockUICommand(BaseCommand):
    """Mock command with UI-related attributes."""

    def __init__(self, container):
        super().__init__(container)

    @property
    def name(self) -> str:
        return "mock-ui"

    @property
    def description(self) -> str:
        return "Mock UI command"

    def execute(self) -> int:
        return 0

    def launch_ui(self):
        """This method makes it detectable as UI command."""
        pass


class TestInteractiveCommandFilter:
    """Test the interactive command filter."""

    def setup_method(self):
        """Set up test fixtures."""
        self.container = SimpleContainer()
        self.filter = InteractiveCommandFilter()

    def test_known_interactive_commands(self):
        """Test detection of known interactive commands."""
        # Mock a command with known interactive name
        mock_class = Mock()

        # Should detect 'ui' as interactive
        assert self.filter.is_interactive("ui", mock_class, self.container) is True

        # Should not detect regular commands as interactive
        assert self.filter.is_interactive("regular", mock_class, self.container) is False

    def test_source_pattern_detection(self):
        """Test detection of interactive patterns in source code."""
        # Test with mock interactive command
        assert self.filter.is_interactive("test", MockInteractiveCommand, self.container) is True

        # Test with safe command
        assert self.filter.is_interactive("test", MockSafeCommand, self.container) is False

    def test_ui_attribute_detection(self):
        """Test detection of UI-related attributes."""
        # Test with UI command
        assert self.filter.is_interactive("test", MockUICommand, self.container) is True

        # Test with safe command
        assert self.filter.is_interactive("test", MockSafeCommand, self.container) is False

    def test_interactive_reason_generation(self):
        """Test generation of interactive reasons."""
        # Test known interactive command
        reason = self.filter.get_interactive_reason("ui", Mock(), self.container)
        assert "Known interactive command" in reason

        # Test interactive pattern detection
        reason = self.filter.get_interactive_reason("test", MockInteractiveCommand, self.container)
        assert "input()" in reason

        # Test UI attribute detection
        reason = self.filter.get_interactive_reason("test", MockUICommand, self.container)
        assert "launch_ui" in reason


class TestMCPCommandAnalyzer:
    """Test the command analyzer."""

    def setup_method(self):
        """Set up test fixtures."""
        self.container = SimpleContainer()
        self.filter = InteractiveCommandFilter()
        self.analyzer = MCPCommandAnalyzer(self.container, self.filter)

    def test_command_analysis(self):
        """Test command metadata analysis."""
        result = self.analyzer.analyze_command("test", MockSafeCommand)

        assert result is not None
        assert result["name"] == "test"
        assert result["description"] == "Mock safe command"
        assert "help_text" in result

    def test_tool_schema_generation(self):
        """Test MCP tool schema generation."""
        schema = self.analyzer.get_tool_schema("test", MockSafeCommand)

        assert schema is not None
        assert schema["name"] == "hyper_test"
        assert "inputSchema" in schema
        assert "properties" in schema["inputSchema"]

        # Check parameter extraction
        properties = schema["inputSchema"]["properties"]
        assert "arg1" in properties
        assert "flag" in properties
        assert properties["flag"]["type"] == "boolean"
        assert properties["arg1"]["default"] == "default"

    def test_invalid_command_handling(self):
        """Test handling of invalid commands."""

        # Test with class that can't be instantiated
        class BadCommand:
            def __init__(self, container):
                raise Exception("Can't instantiate")

        result = self.analyzer.analyze_command("bad", BadCommand)
        assert result is None

        schema = self.analyzer.get_tool_schema("bad", BadCommand)
        assert schema is None


class TestMCPCommandExecutor:
    """Test the command executor."""

    def setup_method(self):
        """Set up test fixtures."""
        self.container = SimpleContainer()
        self.executor = MCPCommandExecutor(self.container)

    def test_successful_execution(self):
        """Test successful command execution."""
        result = self.executor.execute_command(
            "test", MockSafeCommand, {"arg1": "hello", "flag": True}
        )

        assert "content" in result
        assert "isError" not in result
        assert any("executed successfully" in content["text"] for content in result["content"])

    def test_special_handling_init(self):
        """Test special handling for init command."""

        # Mock init command
        class MockInitCommand(BaseCommand):
            def __init__(self, container):
                super().__init__(container)
                self.force_used = False

            def execute(self, force: bool = False) -> int:
                self.force_used = force
                return 0

        # Execute without force - should be added automatically
        result = self.executor.execute_command("init", MockInitCommand, {})

        # Verify force was applied (indirectly through successful execution)
        assert "isError" not in result

    def test_argument_preparation(self):
        """Test argument preparation for different parameter types."""
        # Test with various argument types
        result = self.executor.execute_command(
            "test",
            MockSafeCommand,
            {
                "arg1": "test_value",
                "flag": True,
                "unknown_arg": "ignored",  # Should be filtered out
            },
        )

        assert "isError" not in result

    def test_error_handling(self):
        """Test error handling during execution."""

        class FailingCommand(BaseCommand):
            def execute(self) -> int:
                raise Exception("Command failed")

        result = self.executor.execute_command("fail", FailingCommand, {})

        assert "isError" in result
        assert result["isError"] is True
        assert any("Error: Command failed" in content["text"] or "failed with exit code" in content["text"] for content in result["content"])


class TestMCPServer:
    """Test the main MCP server functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        with patch("hyper_cmd.mcp_server.discover_commands") as mock_discover:
            # Mock command registry
            mock_registry = Mock()
            mock_registry.list_commands.return_value = ["safe", "interactive"]
            mock_registry.get.side_effect = lambda name: {
                "safe": MockSafeCommand,
                "interactive": MockInteractiveCommand,
            }.get(name)

            mock_discover.return_value = mock_registry
            self.server = MCPServer()

    def test_initialization(self):
        """Test server initialization."""
        assert self.server.container is not None
        assert self.server.command_filter is not None
        assert self.server.command_analyzer is not None
        assert self.server.command_executor is not None

    def test_get_tools(self):
        """Test tool discovery and filtering."""
        tools = self.server.get_tools()

        # Should only include safe commands
        tool_names = [tool["name"] for tool in tools]
        assert "hyper_safe" in tool_names
        assert "hyper_interactive" not in tool_names

    def test_get_command_info(self):
        """Test comprehensive command information."""
        info = self.server.get_command_info()

        assert "available_commands" in info
        assert "interactive_commands" in info
        assert info["total_commands"] == 2
        assert info["available_count"] == 1
        assert info["interactive_count"] == 1

    def test_execute_tool_success(self):
        """Test successful tool execution."""
        result = self.server.execute_tool("hyper_safe", {"arg1": "test"})

        assert "isError" not in result
        assert "content" in result

    def test_execute_tool_invalid_name(self):
        """Test execution with invalid tool name."""
        result = self.server.execute_tool("invalid_name", {})

        assert "isError" in result
        assert result["isError"] is True

    def test_execute_tool_not_found(self):
        """Test execution with non-existent command."""
        result = self.server.execute_tool("hyper_nonexistent", {})

        assert "isError" in result
        assert result["isError"] is True

    def test_execute_tool_interactive_blocked(self):
        """Test that interactive commands are blocked."""
        result = self.server.execute_tool("hyper_interactive", {})

        assert "isError" in result
        assert result["isError"] is True
        assert any("interactive" in content["text"] for content in result["content"])

    def test_get_resources(self):
        """Test MCP resource listing."""
        resources = self.server.get_resources()

        assert len(resources) == 3
        resource_uris = [r["uri"] for r in resources]
        assert "hyper://commands/available" in resource_uris
        assert "hyper://commands/interactive" in resource_uris
        assert "hyper://commands/all" in resource_uris

    def test_read_resource_available(self):
        """Test reading available commands resource."""
        result = self.server.read_resource("hyper://commands/available")

        assert "contents" in result
        content = json.loads(result["contents"][0]["text"])
        assert "commands" in content
        assert content["count"] >= 0

    def test_read_resource_interactive(self):
        """Test reading interactive commands resource."""
        result = self.server.read_resource("hyper://commands/interactive")

        assert "contents" in result
        content = json.loads(result["contents"][0]["text"])
        assert "commands" in content
        assert "note" in content

    def test_read_resource_all(self):
        """Test reading all commands resource."""
        result = self.server.read_resource("hyper://commands/all")

        assert "contents" in result
        content = json.loads(result["contents"][0]["text"])
        assert "summary" in content
        assert "available_commands" in content
        assert "interactive_commands" in content

    def test_read_resource_invalid(self):
        """Test reading invalid resource."""
        with pytest.raises(ValueError):
            self.server.read_resource("invalid://resource")

    def test_handle_request_tools_list(self):
        """Test handling tools/list request."""
        request = {"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}

        response = self.server.handle_request(request)

        assert response["jsonrpc"] == "2.0"
        assert response["id"] == 1
        assert "result" in response
        assert "tools" in response["result"]

    def test_handle_request_tools_call(self):
        """Test handling tools/call request."""
        request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {"name": "hyper_safe", "arguments": {"arg1": "test"}},
        }

        response = self.server.handle_request(request)

        assert response["jsonrpc"] == "2.0"
        assert response["id"] == 2
        assert "result" in response

    def test_handle_request_resources_list(self):
        """Test handling resources/list request."""
        request = {"jsonrpc": "2.0", "id": 3, "method": "resources/list", "params": {}}

        response = self.server.handle_request(request)

        assert response["jsonrpc"] == "2.0"
        assert response["id"] == 3
        assert "result" in response
        assert "resources" in response["result"]

    def test_handle_request_resources_read(self):
        """Test handling resources/read request."""
        request = {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "resources/read",
            "params": {"uri": "hyper://commands/all"},
        }

        response = self.server.handle_request(request)

        assert response["jsonrpc"] == "2.0"
        assert response["id"] == 4
        assert "result" in response

    def test_handle_request_initialize(self):
        """Test handling initialize request."""
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {"protocolVersion": "2024-11-05"},
        }

        response = self.server.handle_request(request)

        assert response["jsonrpc"] == "2.0"
        assert response["id"] == 1
        assert "result" in response

        result = response["result"]
        assert result["protocolVersion"] == "2024-11-05"
        assert "capabilities" in result
        assert "serverInfo" in result
        assert result["serverInfo"]["name"] == "hyper-cmd"
        assert result["serverInfo"]["version"] == "0.1.0"

    def test_handle_request_invalid_method(self):
        """Test handling invalid method request."""
        request = {"jsonrpc": "2.0", "id": 5, "method": "invalid/method", "params": {}}

        response = self.server.handle_request(request)

        assert response["jsonrpc"] == "2.0"
        assert response["id"] == 5
        assert "result" in response
        assert "error" in response["result"]

    def test_handle_request_exception(self):
        """Test handling request with exception."""
        # Mock an exception in request handling
        with patch.object(self.server, "_route_request", side_effect=Exception("Test error")):
            request = {"jsonrpc": "2.0", "id": 6, "method": "tools/list", "params": {}}

            response = self.server.handle_request(request)

            assert response["jsonrpc"] == "2.0"
            assert response["id"] == 6
            assert "error" in response


class TestMCPServerIntegration:
    """Integration tests for the MCP server."""

    def test_full_workflow(self):
        """Test a complete MCP workflow."""
        # This test uses the real command discovery
        server = MCPServer()

        # 1. List tools
        tools = server.get_tools()
        assert len(tools) > 0

        # 2. Get command info
        info = server.get_command_info()
        assert info["total_commands"] > 0

        # 3. List resources
        resources = server.get_resources()
        assert len(resources) == 3

        # 4. Read a resource
        result = server.read_resource("hyper://commands/all")
        assert "contents" in result

        # 5. Execute a safe command (hello)
        if any(tool["name"] == "hyper_hello" for tool in tools):
            result = server.execute_tool("hyper_hello", {"name": "Test"})
            # Should succeed or fail gracefully
            assert "content" in result

    def test_mcp_protocol_compliance(self):
        """Test MCP protocol compliance."""
        server = MCPServer()

        # Test JSON-RPC 2.0 compliance
        request = {"jsonrpc": "2.0", "id": "test-id", "method": "tools/list", "params": {}}

        response = server.handle_request(request)

        # Check required fields
        assert response["jsonrpc"] == "2.0"
        assert response["id"] == "test-id"
        assert "result" in response or "error" in response

        # Test with null id
        request["id"] = None
        response = server.handle_request(request)
        assert response["id"] is None
