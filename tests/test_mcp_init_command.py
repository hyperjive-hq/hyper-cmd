"""Comprehensive tests for mcp-init command functionality."""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from hyper_core.commands.mcp_init import MCPConfigGenerator, McpInitCommand, MCPToolDetector
from hyper_core.container.simple_container import SimpleContainer


class TestMCPConfigGenerator:
    """Test the MCP configuration generator."""

    def test_generate_config(self):
        """Test configuration generation."""
        config = MCPConfigGenerator.generate_config()

        # Check structure
        assert "mcpServers" in config
        assert "hyper-core" in config["mcpServers"]
        assert "$schema" in config
        assert "version" in config
        assert "description" in config

        # Check hyper-core server config
        hyper_config = config["mcpServers"]["hyper-core"]
        assert hyper_config["command"] == "hyper-mcp"
        assert hyper_config["args"] == []
        assert hyper_config["env"] == {}
        assert "description" in hyper_config

    def test_write_config(self):
        """Test configuration file writing."""
        config = MCPConfigGenerator.generate_config()

        with tempfile.TemporaryDirectory() as tmp_dir:
            config_file = Path(tmp_dir) / "test.json"

            MCPConfigGenerator.write_config(config_file, config)

            # Verify file was created
            assert config_file.exists()

            # Verify content
            with open(config_file) as f:
                written_config = json.load(f)

            assert written_config == config

            # Verify proper formatting (should end with newline)
            with open(config_file) as f:
                content = f.read()
            assert content.endswith("\n")


class TestMCPToolDetector:
    """Test the MCP tool detector."""

    def test_detect_tools_no_tools(self):
        """Test tool detection when no tools are present."""
        with patch.dict("os.environ", {}, clear=True):
            with patch.object(MCPToolDetector, "_find_existing_configs", return_value=[]):
                tools = MCPToolDetector.detect_tools()
                assert tools == []

    def test_detect_tools_claude_code(self):
        """Test detection of Claude Code."""
        with patch.dict("os.environ", {"CLAUDE_CODE": "1"}):
            with patch.object(MCPToolDetector, "_find_existing_configs", return_value=[]):
                tools = MCPToolDetector.detect_tools()
                assert "Claude Code" in tools

    def test_detect_tools_existing_configs(self):
        """Test detection of existing configs."""
        mock_configs = [Path("/fake/config1.json"), Path("/fake/config2.json")]

        with patch.dict("os.environ", {}, clear=True):
            with patch.object(MCPToolDetector, "_find_existing_configs", return_value=mock_configs):
                tools = MCPToolDetector.detect_tools()
                assert any("Existing MCP configs" in tool for tool in tools)

    def test_find_existing_configs(self):
        """Test finding existing configuration files."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Create a mock config file
            config_file = Path(tmp_dir) / ".mcp.json"
            config_file.write_text('{"test": true}')

            # Mock Path.cwd() to return our temp directory
            with patch("pathlib.Path.cwd", return_value=Path(tmp_dir)):
                # Mock Path.home() to return temp directory (to avoid real home)
                with patch("pathlib.Path.home", return_value=Path(tmp_dir)):
                    configs = MCPToolDetector._find_existing_configs()

                    # Should find our config file
                    assert any(config_file.name in str(config) for config in configs)


class TestMcpInitCommand:
    """Test the mcp-init command."""

    def setup_method(self):
        """Set up test fixtures."""
        self.container = SimpleContainer()
        self.command = McpInitCommand(self.container)

    def test_initialization(self):
        """Test command initialization."""
        assert self.command.name == "mcp-init"
        assert "MCP" in self.command.description
        assert self.command.config_generator is not None
        assert self.command.tool_detector is not None

    def test_properties(self):
        """Test command properties."""
        assert self.command.name == "mcp-init"
        assert isinstance(self.command.description, str)
        assert isinstance(self.command.help_text, str)
        assert "mcp-init" in self.command.help_text

    def test_execute_success_force(self):
        """Test successful execution with force flag."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            exit_code = self.command.execute(force=True, config_path=tmp_dir)

            assert exit_code == 0

            # Verify config file was created
            config_file = Path(tmp_dir) / ".mcp.json"
            assert config_file.exists()

            # Verify config content
            with open(config_file) as f:
                config = json.load(f)

            assert "mcpServers" in config
            assert "hyper-core" in config["mcpServers"]

    def test_execute_current_directory(self):
        """Test execution in current directory."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Change to temp directory
            import os

            old_cwd = os.getcwd()
            try:
                os.chdir(tmp_dir)

                exit_code = self.command.execute(force=True)

                assert exit_code == 0

                # Verify config file was created in current directory
                config_file = Path(tmp_dir) / ".mcp.json"
                assert config_file.exists()

            finally:
                os.chdir(old_cwd)

    def test_execute_invalid_directory(self):
        """Test execution with invalid directory."""
        exit_code = self.command.execute(force=True, config_path="/nonexistent/directory")

        assert exit_code == 1

    def test_execute_file_as_directory(self):
        """Test execution with file path instead of directory."""
        with tempfile.NamedTemporaryFile() as tmp_file:
            exit_code = self.command.execute(force=True, config_path=tmp_file.name)

            assert exit_code == 1

    def test_determine_config_file_valid(self):
        """Test config file location determination."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            config_file = self.command._determine_config_file(tmp_dir)

            assert config_file is not None
            assert config_file.name == ".mcp.json"
            assert str(tmp_dir) in str(config_file.parent)

    def test_determine_config_file_invalid(self):
        """Test config file determination with invalid path."""
        config_file = self.command._determine_config_file("/nonexistent")

        assert config_file is None

    def test_handle_existing_file_no_file(self):
        """Test handling when no existing file."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            config_file = Path(tmp_dir) / ".mcp.json"

            result = self.command._handle_existing_file(config_file, force=False)

            assert result is True

    def test_handle_existing_file_with_force(self):
        """Test handling existing file with force flag."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            config_file = Path(tmp_dir) / ".mcp.json"
            config_file.write_text('{"existing": true}')

            result = self.command._handle_existing_file(config_file, force=True)

            assert result is True

    def test_handle_existing_file_without_force(self):
        """Test handling existing file without force flag."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            config_file = Path(tmp_dir) / ".mcp.json"
            config_file.write_text('{"existing": true}')

            # Mock user input to decline
            with patch("builtins.input", return_value="n"):
                result = self.command._handle_existing_file(config_file, force=False)

                assert result is False

            # Mock user input to accept
            with patch("builtins.input", return_value="y"):
                result = self.command._handle_existing_file(config_file, force=False)

                assert result is True

    def test_show_config_preview(self):
        """Test configuration preview display."""
        config = MCPConfigGenerator.generate_config()

        with tempfile.TemporaryDirectory() as tmp_dir:
            config_file = Path(tmp_dir) / ".mcp.json"

            # Should not raise an exception
            self.command._show_config_preview(config, config_file)

    def test_write_config_file_success(self):
        """Test successful config file writing."""
        config = MCPConfigGenerator.generate_config()

        with tempfile.TemporaryDirectory() as tmp_dir:
            config_file = Path(tmp_dir) / ".mcp.json"

            # Should not raise an exception
            self.command._write_config_file(config_file, config)

            assert config_file.exists()

    def test_write_config_file_permission_error(self):
        """Test config file writing with permission error."""
        config = MCPConfigGenerator.generate_config()

        # Try to write to a read-only location
        config_file = Path("/root/.mcp.json")  # Assuming this will fail

        with pytest.raises(RuntimeError):
            self.command._write_config_file(config_file, config)

    def test_confirm_overwrite_accept(self):
        """Test overwrite confirmation - accept."""
        with patch("builtins.input", return_value="y"):
            result = self.command._confirm_overwrite()
            assert result is True

        with patch("builtins.input", return_value="yes"):
            result = self.command._confirm_overwrite()
            assert result is True

    def test_confirm_overwrite_decline(self):
        """Test overwrite confirmation - decline."""
        with patch("builtins.input", return_value="n"):
            result = self.command._confirm_overwrite()
            assert result is False

        with patch("builtins.input", return_value=""):
            result = self.command._confirm_overwrite()
            assert result is False

    def test_confirm_overwrite_interrupt(self):
        """Test overwrite confirmation with interrupt."""
        with patch("builtins.input", side_effect=KeyboardInterrupt()):
            result = self.command._confirm_overwrite()
            assert result is False

        with patch("builtins.input", side_effect=EOFError()):
            result = self.command._confirm_overwrite()
            assert result is False

    def test_confirm_proceed_accept(self):
        """Test proceed confirmation - accept."""
        with patch("builtins.input", return_value="y"):
            result = self.command._confirm_proceed()
            assert result is True

        with patch("builtins.input", return_value=""):
            result = self.command._confirm_proceed()
            assert result is True

    def test_confirm_proceed_decline(self):
        """Test proceed confirmation - decline."""
        with patch("builtins.input", return_value="n"):
            result = self.command._confirm_proceed()
            assert result is False

        with patch("builtins.input", return_value="no"):
            result = self.command._confirm_proceed()
            assert result is False

    def test_confirm_proceed_interrupt(self):
        """Test proceed confirmation with interrupt."""
        with patch("builtins.input", side_effect=KeyboardInterrupt()):
            result = self.command._confirm_proceed()
            assert result is False

        with patch("builtins.input", side_effect=EOFError()):
            result = self.command._confirm_proceed()
            assert result is False

    def test_execute_with_confirmation_flow(self):
        """Test execution with user confirmation flow."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Create existing file
            config_file = Path(tmp_dir) / ".mcp.json"
            config_file.write_text('{"existing": true}')

            # Mock user to accept overwrite and proceed
            with patch("builtins.input", side_effect=["y", "y"]):
                exit_code = self.command.execute(force=False, config_path=tmp_dir)

                assert exit_code == 0

                # Verify new config was written
                with open(config_file) as f:
                    config = json.load(f)

                assert "hyper-core" in config["mcpServers"]

    def test_execute_with_cancellation(self):
        """Test execution cancelled by user."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Mock user to decline proceeding
            with patch("builtins.input", return_value="n"):
                exit_code = self.command.execute(force=False, config_path=tmp_dir)

                assert exit_code == 1

                # Verify no config file was created
                config_file = Path(tmp_dir) / ".mcp.json"
                assert not config_file.exists()

    def test_execute_exception_handling(self):
        """Test exception handling during execution."""
        # Mock an exception in config generation
        with patch.object(
            self.command.config_generator, "generate_config", side_effect=Exception("Test error")
        ):
            exit_code = self.command.execute(force=True, config_path="/tmp")

            assert exit_code == 1

    def test_show_next_steps(self):
        """Test next steps display."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            config_file = Path(tmp_dir) / ".mcp.json"

            # Should not raise an exception
            self.command._show_next_steps(config_file)

    def test_integration_with_mcp_server(self):
        """Test integration between mcp-init and MCP server."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Create config with mcp-init
            exit_code = self.command.execute(force=True, config_path=tmp_dir)
            assert exit_code == 0

            # Verify config file
            config_file = Path(tmp_dir) / ".mcp.json"
            assert config_file.exists()

            # Load and verify config structure matches MCP server expectations
            with open(config_file) as f:
                config = json.load(f)

            assert "mcpServers" in config
            server_config = config["mcpServers"]["hyper-core"]
            assert server_config["command"] == "hyper-mcp"

            # Verify config has required fields for MCP
            assert "$schema" in config
            assert "version" in config


class TestMCPInitIntegration:
    """Integration tests for mcp-init command."""

    def test_command_available_in_registry(self):
        """Test that mcp-init command is properly registered."""
        from hyper_core.cli import discover_commands

        registry = discover_commands()
        commands = registry.list_commands()

        assert "mcp-init" in commands

        # Test command can be retrieved and instantiated
        cmd_class = registry.get("mcp-init")
        assert cmd_class is not None

        container = SimpleContainer()
        instance = cmd_class(container)
        assert instance.name == "mcp-init"

    def test_command_available_via_mcp(self):
        """Test that mcp-init command is available via MCP server."""
        from hyper_core.mcp_server import MCPServer

        server = MCPServer()
        tools = server.get_tools()

        # Should find mcp-init tool
        mcp_init_tools = [tool for tool in tools if tool["name"] == "hyper_mcp-init"]
        assert len(mcp_init_tools) == 1

        tool = mcp_init_tools[0]
        assert "Initialize MCP configuration" in tool["description"]
        assert "inputSchema" in tool

    def test_end_to_end_workflow(self):
        """Test complete end-to-end workflow."""
        from hyper_core.mcp_server import MCPServer

        with tempfile.TemporaryDirectory() as tmp_dir:
            # 1. Execute mcp-init via MCP server
            server = MCPServer()

            request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": "hyper_mcp-init",
                    "arguments": {"force": True, "config_path": tmp_dir},
                },
            }

            response = server.handle_request(request)

            # 2. Verify MCP response
            assert response["jsonrpc"] == "2.0"
            assert response["id"] == 1
            assert "result" in response
            assert "isError" not in response["result"]

            # 3. Verify config file was created
            config_file = Path(tmp_dir) / ".mcp.json"
            assert config_file.exists()

            # 4. Verify config content
            with open(config_file) as f:
                config = json.load(f)

            assert "mcpServers" in config
            assert "hyper-core" in config["mcpServers"]
            assert config["mcpServers"]["hyper-core"]["command"] == "hyper-mcp"
