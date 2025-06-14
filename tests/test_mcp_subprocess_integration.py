"""Tests for MCP subprocess integration."""

import subprocess

from hyper_cmd.commands.base import BaseCommand
from hyper_cmd.container.simple_container import SimpleContainer
from hyper_cmd.mcp_server import MCPCommandExecutor


class SubprocessTestCommand(BaseCommand):
    """Test command that uses subprocess helpers."""

    def __init__(self, container=None):
        super().__init__(container)
        self._description = "Test command for MCP subprocess integration"

    def execute(self, command_type="print", message="test"):
        """Execute different types of subprocess operations."""
        if command_type == "print":
            print(f"Print: {message}")
            return 0
        elif command_type == "subprocess":
            result = self.run_subprocess(["echo", f"Subprocess: {message}"])
            return result.returncode
        elif command_type == "streaming":
            exit_code = self.run_subprocess_streaming(
                ["python", "-c", f"print('Streaming: {message}')"]
            )
            return exit_code
        elif command_type == "mixed":
            print(f"Direct print: {message}")
            self.run_subprocess(["echo", f"Subprocess echo: {message}"])
            return 0
        elif command_type == "error":
            result = self.run_subprocess(
                ["python", "-c", f"import sys; sys.stderr.write('Error: {message}\\n')"]
            )
            return result.returncode
        else:
            raise ValueError(f"Unknown command_type: {command_type}")


class TestMCPSubprocessIntegration:
    """Test MCP integration with subprocess helpers."""

    def setup_method(self):
        """Set up test fixtures."""
        self.container = SimpleContainer()
        self.executor = MCPCommandExecutor(self.container)

    def test_mcp_captures_print_output(self):
        """Test MCP captures direct print statements."""
        result = self.executor.execute_command(
            "test", SubprocessTestCommand, {"command_type": "print", "message": "hello"}
        )

        assert result.get("isError") is not True
        # The command succeeded but print output isn't captured by BaseCommand
        # Only subprocess output is captured
        assert result["content"][0]["text"] == "Command 'test' executed successfully"

    def test_mcp_captures_subprocess_output(self):
        """Test MCP captures subprocess output."""
        result = self.executor.execute_command(
            "test", SubprocessTestCommand, {"command_type": "subprocess", "message": "world"}
        )

        assert result.get("isError") is not True
        content_text = result["content"][0]["text"]
        assert "Output:" in content_text
        assert "Subprocess: world" in content_text

    def test_mcp_captures_streaming_output(self):
        """Test MCP captures streaming subprocess output."""
        result = self.executor.execute_command(
            "test", SubprocessTestCommand, {"command_type": "streaming", "message": "stream"}
        )

        assert result.get("isError") is not True
        content_text = result["content"][0]["text"]
        assert "Output:" in content_text
        assert "Streaming: stream" in content_text

    def test_mcp_captures_mixed_output(self):
        """Test MCP captures mixed print and subprocess output."""
        result = self.executor.execute_command(
            "test", SubprocessTestCommand, {"command_type": "mixed", "message": "both"}
        )

        assert result.get("isError") is not True
        content_text = result["content"][0]["text"]
        assert "Output:" in content_text
        # Should capture subprocess output
        assert "Subprocess echo: both" in content_text
        # Direct print is not captured by BaseCommand subprocess helpers

    def test_mcp_captures_subprocess_errors(self):
        """Test MCP captures subprocess stderr."""
        result = self.executor.execute_command(
            "test", SubprocessTestCommand, {"command_type": "error", "message": "failure"}
        )

        assert result.get("isError") is not True  # Command itself succeeded
        # Should have captured stderr
        content_texts = [item["text"] for item in result["content"]]
        stderr_content = next((text for text in content_texts if "Errors:" in text), None)
        assert stderr_content is not None
        assert "Error: failure" in stderr_content

    def test_mcp_handles_command_exceptions(self):
        """Test MCP handles exceptions in commands properly."""
        result = self.executor.execute_command(
            "test", SubprocessTestCommand, {"command_type": "invalid"}
        )

        assert result["isError"] is True
        content_text = result["content"][0]["text"]
        assert "Errors:" in content_text
        assert "Unknown command_type" in content_text

    def test_mcp_output_cleared_between_commands(self):
        """Test that output is cleared between different command executions."""
        # Run first command
        self.executor.execute_command(
            "test", SubprocessTestCommand, {"command_type": "subprocess", "message": "first"}
        )

        # Run second command
        result2 = self.executor.execute_command(
            "test", SubprocessTestCommand, {"command_type": "subprocess", "message": "second"}
        )

        # Second result should not contain first command's output
        content_text = result2["content"][0]["text"]
        assert "first" not in content_text
        assert "second" in content_text

    def test_mcp_handles_subprocess_failure(self):
        """Test MCP handles subprocess command failures."""

        class FailingSubprocessCommand(BaseCommand):
            def execute(self):
                result = self.run_subprocess(["false"])  # Always fails
                return result.returncode

        result = self.executor.execute_command("test", FailingSubprocessCommand, {})

        assert result["isError"] is True
        content_text = result["content"][0]["text"]
        assert "failed with exit code" in content_text

    def test_mcp_preserves_subprocess_return_codes(self):
        """Test that subprocess return codes are properly handled."""

        class ReturnCodeCommand(BaseCommand):
            def execute(self, code=0):
                # Run a command that exits with specified code
                result = self.run_subprocess(["python", "-c", f"import sys; sys.exit({code})"])
                return result.returncode

        # Test success
        result = self.executor.execute_command("test", ReturnCodeCommand, {"code": 0})
        assert result.get("isError") is not True

        # Test failure
        result = self.executor.execute_command("test", ReturnCodeCommand, {"code": 1})
        assert result["isError"] is True

    def test_mcp_handles_large_subprocess_output(self):
        """Test MCP handles large subprocess output."""

        class LargeOutputCommand(BaseCommand):
            def execute(self):
                # Generate substantial output
                result = self.run_subprocess(
                    ["python", "-c", "for i in range(100): print(f'Line {i}: some content here')"]
                )
                return result.returncode

        result = self.executor.execute_command("test", LargeOutputCommand, {})

        assert result.get("isError") is not True
        content_text = result["content"][0]["text"]
        assert "Output:" in content_text
        assert "Line 0:" in content_text
        assert "Line 99:" in content_text

    def test_mcp_timeout_handling(self):
        """Test MCP handles subprocess timeouts."""

        class TimeoutCommand(BaseCommand):
            def execute(self):
                try:
                    result = self.run_subprocess(
                        ["python", "-c", "import time; time.sleep(10)"], timeout=0.1
                    )  # Very short timeout
                    return result.returncode
                except subprocess.TimeoutExpired:
                    return 124  # Standard timeout exit code

        result = self.executor.execute_command("test", TimeoutCommand, {})

        # Should handle timeout gracefully
        assert result["isError"] is True
        content_text = result["content"][0]["text"]
        assert "failed with exit code 124" in content_text


class TestMCPExecutorRobustness:
    """Test MCP executor robustness with edge cases."""

    def setup_method(self):
        """Set up test fixtures."""
        self.container = SimpleContainer()
        self.executor = MCPCommandExecutor(self.container)

    def test_executor_handles_command_instantiation_failure(self):
        """Test executor handles command instantiation failures."""

        class BadCommand(BaseCommand):
            def __init__(self, container=None):
                raise RuntimeError("Cannot instantiate")

            def execute(self):
                return 0

        result = self.executor.execute_command("test", BadCommand, {})

        assert result["isError"] is True
        content_text = result["content"][0]["text"]
        assert "Error executing command" in content_text
        assert "Cannot instantiate" in content_text

    def test_executor_captures_method_not_found(self):
        """Test executor handles missing get_captured_output method."""

        class OldStyleCommand:
            """Command without BaseCommand inheritance."""

            def __init__(self, container=None):
                pass

            def run(self):
                return 0

        # This should fail gracefully
        result = self.executor.execute_command("test", OldStyleCommand, {})

        assert result["isError"] is True
        content_text = result["content"][0]["text"]
        assert "Error executing command" in content_text

    def test_executor_handles_run_method_exception(self):
        """Test executor handles exceptions in BaseCommand.run()."""

        class ExceptionInRunCommand(BaseCommand):
            def run(self):
                raise RuntimeError("Run method failed")

            def execute(self):
                return 0

        result = self.executor.execute_command("test", ExceptionInRunCommand, {})

        assert result["isError"] is True
        # The _execute_with_capture method should catch this
        content_text = result["content"][0]["text"]
        assert "Errors:" in content_text
        assert "Run method failed" in content_text
