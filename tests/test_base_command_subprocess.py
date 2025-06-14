"""Tests for BaseCommand subprocess helpers."""

import sys
from unittest.mock import Mock, patch

import pytest

from hyper_cmd.commands.base import BaseCommand
from hyper_cmd.container.simple_container import SimpleContainer


class TestSubprocessCommand(BaseCommand):
    """Test command for subprocess functionality."""

    def __init__(self, container=None):
        super().__init__(container)
        self._description = "Test command for subprocess functionality"

    def execute(self):
        """Simple execute for testing."""
        return 0


class TestBaseCommandSubprocess:
    """Test subprocess helpers in BaseCommand."""

    def setup_method(self):
        """Set up test fixtures."""
        self.container = SimpleContainer()
        self.command = TestSubprocessCommand(self.container)

    def test_run_subprocess_success(self):
        """Test successful subprocess execution."""
        result = self.command.run_subprocess(["echo", "hello world"])

        assert result.returncode == 0
        assert "hello world" in result.stdout

        # Check output was captured for MCP
        stdout, stderr = self.command.get_captured_output()
        assert "hello world" in stdout
        assert stderr == ""

    def test_run_subprocess_with_stderr(self):
        """Test subprocess execution with stderr output."""
        # Use python to write to stderr
        result = self.command.run_subprocess(
            [sys.executable, "-c", "import sys; sys.stderr.write('error message\\n')"]
        )

        assert result.returncode == 0
        assert "error message" in result.stderr

        # Check stderr was captured for MCP
        stdout, stderr = self.command.get_captured_output()
        assert "error message" in stderr

    def test_run_subprocess_failure(self):
        """Test subprocess execution that fails."""
        result = self.command.run_subprocess(["false"])  # Command that always fails

        assert result.returncode != 0

        # Output should still be captured even on failure
        stdout, stderr = self.command.get_captured_output()
        # false command produces no output, so both should be empty
        assert stdout == "" or stderr == ""

    def test_run_subprocess_capture_disabled(self):
        """Test subprocess with capture_output=False."""
        result = self.command.run_subprocess(["echo", "no capture"], capture_output=False)

        assert result.returncode == 0
        # When capture_output=False, subprocess.run doesn't capture
        assert result.stdout is None
        assert result.stderr is None

        # Should not be captured for MCP either
        stdout, stderr = self.command.get_captured_output()
        assert stdout == ""
        assert stderr == ""

    def test_run_subprocess_show_output_disabled(self):
        """Test subprocess with show_output=False."""
        with patch.object(self.command.console, "print") as mock_print:
            result = self.command.run_subprocess(["echo", "hidden output"], show_output=False)

            assert result.returncode == 0
            # Should not have printed to console
            mock_print.assert_not_called()

            # Should still be captured for MCP
            stdout, stderr = self.command.get_captured_output()
            assert "hidden output" in stdout

    def test_run_subprocess_shell_command(self):
        """Test subprocess with shell=True."""
        result = self.command.run_subprocess("echo 'shell command'", shell=True)

        assert result.returncode == 0
        assert "shell command" in result.stdout

        stdout, stderr = self.command.get_captured_output()
        assert "shell command" in stdout

    def test_run_subprocess_with_cwd(self):
        """Test subprocess with working directory."""
        result = self.command.run_subprocess(["pwd"], cwd="/tmp")

        assert result.returncode == 0
        assert "/tmp" in result.stdout

    def test_run_subprocess_streaming_success(self):
        """Test streaming subprocess execution."""
        with patch.object(self.command.console, "print") as mock_print:
            exit_code = self.command.run_subprocess_streaming(
                [sys.executable, "-c", "print('line1'); print('line2')"]
            )

            assert exit_code == 0

            # Should have printed each line as it came
            calls = [call.args[0] for call in mock_print.call_args_list]
            assert "line1" in calls
            assert "line2" in calls

            # Should be captured for MCP
            stdout, stderr = self.command.get_captured_output()
            assert "line1" in stdout
            assert "line2" in stdout

    def test_run_subprocess_streaming_with_stderr(self):
        """Test streaming subprocess with stderr."""
        with patch.object(self.command.console, "print") as mock_print:
            exit_code = self.command.run_subprocess_streaming(
                [
                    sys.executable,
                    "-c",
                    "import sys; sys.stderr.write('error1\\n'); sys.stderr.write('error2\\n')",
                ]
            )

            assert exit_code == 0

            # Should have printed stderr with red formatting
            calls = [call.args[0] for call in mock_print.call_args_list]
            assert any("[red]error1[/]" in str(call) for call in calls)
            assert any("[red]error2[/]" in str(call) for call in calls)

            # Should be captured for MCP
            stdout, stderr = self.command.get_captured_output()
            assert "error1" in stderr
            assert "error2" in stderr

    @patch("sys.platform", "win32")
    def test_run_subprocess_streaming_windows(self):
        """Test streaming subprocess on Windows (uses simple method)."""
        with patch.object(self.command, "_stream_process_output_simple") as mock_simple:
            self.command.run_subprocess_streaming(["echo", "test"])
            mock_simple.assert_called_once()

    @patch("sys.platform", "linux")
    def test_run_subprocess_streaming_unix(self):
        """Test streaming subprocess on Unix (uses select)."""
        with patch.object(self.command, "_stream_process_output") as mock_stream:
            with patch("subprocess.Popen") as mock_popen:
                mock_process = Mock()
                mock_process.wait.return_value = 0
                mock_popen.return_value.__enter__ = Mock(return_value=mock_process)
                mock_popen.return_value.__exit__ = Mock(return_value=None)

                self.command.run_subprocess_streaming(["echo", "test"])
                mock_stream.assert_called_once()

    def test_get_captured_output_empty(self):
        """Test get_captured_output when no commands have been run."""
        stdout, stderr = self.command.get_captured_output()
        assert stdout == ""
        assert stderr == ""

    def test_get_captured_output_multiple_commands(self):
        """Test captured output accumulates across multiple commands."""
        self.command.run_subprocess(["echo", "first"])
        self.command.run_subprocess(["echo", "second"])

        stdout, stderr = self.command.get_captured_output()
        assert "first" in stdout
        assert "second" in stdout
        assert stderr == ""

    def test_clear_captured_output(self):
        """Test clearing captured output."""
        self.command.run_subprocess(["echo", "test"])

        # Verify output was captured
        stdout, stderr = self.command.get_captured_output()
        assert "test" in stdout

        # Clear and verify it's gone
        self.command.clear_captured_output()
        stdout, stderr = self.command.get_captured_output()
        assert stdout == ""
        assert stderr == ""

    def test_output_capture_integration_with_run(self):
        """Test that BaseCommand.run() clears captured output."""
        # Add some output first
        self.command.run_subprocess(["echo", "old"])
        stdout, stderr = self.command.get_captured_output()
        assert "old" in stdout

        # Run the command (which should clear output at start)
        exit_code = self.command.run()
        assert exit_code == 0

        # Should have been cleared
        stdout, stderr = self.command.get_captured_output()
        assert stdout == ""
        assert stderr == ""

    def test_exception_capture_in_run(self):
        """Test that exceptions are captured in stderr."""

        class FailingCommand(BaseCommand):
            def execute(self):
                raise ValueError("Test error")

        failing_command = FailingCommand(self.container)
        exit_code = failing_command.run()

        assert exit_code == 1

        # Error should be captured
        stdout, stderr = failing_command.get_captured_output()
        assert "Error: Test error" in stderr

    def test_keyboard_interrupt_capture_in_run(self):
        """Test that KeyboardInterrupt is captured in stderr."""

        class InterruptedCommand(BaseCommand):
            def execute(self):
                raise KeyboardInterrupt()

        interrupted_command = InterruptedCommand(self.container)
        exit_code = interrupted_command.run()

        assert exit_code == 130

        # Interrupt message should be captured
        stdout, stderr = interrupted_command.get_captured_output()
        assert "Operation cancelled by user" in stderr

    def test_subprocess_error_handling(self):
        """Test subprocess error handling."""
        # Test with invalid command
        with pytest.raises(FileNotFoundError):
            self.command.run_subprocess(["nonexistent_command_12345"])

    def test_streaming_error_handling(self):
        """Test streaming subprocess error handling."""
        # Test with invalid command
        with pytest.raises(FileNotFoundError):
            self.command.run_subprocess_streaming(["nonexistent_command_12345"])


class TestSubprocessHelperMethods:
    """Test the helper methods for subprocess handling."""

    def setup_method(self):
        """Set up test fixtures."""
        self.container = SimpleContainer()
        self.command = TestSubprocessCommand(self.container)

    def test_store_captured_lines_empty(self):
        """Test storing empty line lists."""
        self.command._store_captured_lines([], [])

        stdout, stderr = self.command.get_captured_output()
        assert stdout == ""
        assert stderr == ""

    def test_store_captured_lines_with_content(self):
        """Test storing line lists with content."""
        stdout_lines = ["line1", "line2"]
        stderr_lines = ["error1", "error2"]

        self.command._store_captured_lines(stdout_lines, stderr_lines)

        stdout, stderr = self.command.get_captured_output()
        assert stdout == "line1\nline2"
        assert stderr == "error1\nerror2"

    def test_stream_process_output_simple_stdout_only(self):
        """Test simple streaming with stdout only."""
        with patch.object(self.command.console, "print") as mock_print:
            # Mock process with stdout
            mock_process = Mock()
            mock_process.stdout.readline.side_effect = ["line1\n", "line2\n", ""]
            mock_process.stderr = None

            stdout_lines = []
            stderr_lines = []

            self.command._stream_process_output_simple(mock_process, stdout_lines, stderr_lines)

            assert stdout_lines == ["line1", "line2"]
            assert stderr_lines == []
            assert mock_print.call_count == 2

    def test_stream_process_output_simple_stderr_only(self):
        """Test simple streaming with stderr only."""
        with patch.object(self.command.console, "print") as mock_print:
            # Mock process with stderr
            mock_process = Mock()
            mock_process.stdout = None
            mock_process.stderr.readline.side_effect = ["error1\n", "error2\n", ""]

            stdout_lines = []
            stderr_lines = []

            self.command._stream_process_output_simple(mock_process, stdout_lines, stderr_lines)

            assert stdout_lines == []
            assert stderr_lines == ["error1", "error2"]
            assert mock_print.call_count == 2
            # Should print with red formatting
            mock_print.assert_any_call("[red]error1[/]")
            mock_print.assert_any_call("[red]error2[/]")
