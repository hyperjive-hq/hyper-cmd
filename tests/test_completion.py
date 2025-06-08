"""Tests for shell completion functionality."""

import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

import pytest
from click.testing import CliRunner

from hyper_core.cli import (
    check_completion_installed,
    get_bash_completion_script,
    get_fish_completion_script,
    get_zsh_completion_script,
    install_bash_completion,
    install_fish_completion,
    install_shell_completion,
    install_zsh_completion,
    main,
    show_shell_completion,
)


class TestCompletionDetection:
    """Test completion detection functionality."""

    def test_check_completion_installed_zsh_true(self):
        """Test zsh completion detection when installed."""
        with patch("pathlib.Path.exists") as mock_exists:
            # Mock that one of the zsh completion paths exists
            mock_exists.side_effect = lambda: True
            
            result = check_completion_installed("zsh")
            assert result is True

    def test_check_completion_installed_zsh_false(self):
        """Test zsh completion detection when not installed."""
        with patch("pathlib.Path.exists") as mock_exists:
            # Mock that none of the zsh completion paths exist
            mock_exists.return_value = False
            
            result = check_completion_installed("zsh")
            assert result is False

    def test_check_completion_installed_bash_true(self):
        """Test bash completion detection when installed."""
        with patch("pathlib.Path.exists") as mock_exists:
            mock_exists.side_effect = lambda: True
            
            result = check_completion_installed("bash")
            assert result is True

    def test_check_completion_installed_bash_false(self):
        """Test bash completion detection when not installed."""
        with patch("pathlib.Path.exists") as mock_exists:
            mock_exists.return_value = False
            
            result = check_completion_installed("bash")
            assert result is False

    def test_check_completion_installed_fish_true(self):
        """Test fish completion detection when installed."""
        with patch("pathlib.Path.exists") as mock_exists:
            mock_exists.return_value = True
            
            result = check_completion_installed("fish")
            assert result is True

    def test_check_completion_installed_fish_false(self):
        """Test fish completion detection when not installed."""
        with patch("pathlib.Path.exists") as mock_exists:
            mock_exists.return_value = False
            
            result = check_completion_installed("fish")
            assert result is False

    def test_check_completion_installed_unsupported_shell(self):
        """Test completion detection for unsupported shell."""
        result = check_completion_installed("tcsh")
        assert result is False


class TestCompletionScripts:
    """Test completion script generation."""

    def test_get_zsh_completion_script(self):
        """Test zsh completion script generation."""
        script = get_zsh_completion_script()
        
        assert "#compdef hyper" in script
        assert "_hyper()" in script
        assert "_hyper_commands()" in script
        assert "--ui[Launch the UI interface]" in script
        assert "--install-completion[Install shell completion]" in script
        assert "--show-completion[Show shell completion script]" in script
        assert "init:Initialize a new Hyper project" in script

    def test_get_bash_completion_script(self):
        """Test bash completion script generation."""
        script = get_bash_completion_script()
        
        assert "_hyper_completion()" in script
        assert "complete -F _hyper_completion hyper" in script
        assert "init --ui --install-completion --show-completion --help" in script
        assert "COMPREPLY=(" in script

    def test_get_fish_completion_script(self):
        """Test fish completion script generation."""
        script = get_fish_completion_script()
        
        assert "complete -c hyper" in script
        assert "-l ui -d \"Launch the UI interface\"" in script
        assert "-l install-completion -d \"Install shell completion\"" in script
        assert "-l show-completion -d \"Show shell completion script\"" in script
        assert "init" in script and "Initialize a new Hyper project" in script


class TestCompletionInstallation:
    """Test completion installation functionality."""

    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.home_path = Path(self.temp_dir)

    def test_install_shell_completion_zsh(self):
        """Test shell completion installation for zsh."""
        with patch.dict(os.environ, {"SHELL": "/bin/zsh"}):
            with patch("hyper_core.cli.install_zsh_completion") as mock_install:
                install_shell_completion()
                mock_install.assert_called_once()

    def test_install_shell_completion_bash(self):
        """Test shell completion installation for bash."""
        with patch.dict(os.environ, {"SHELL": "/bin/bash"}):
            with patch("hyper_core.cli.install_bash_completion") as mock_install:
                install_shell_completion()
                mock_install.assert_called_once()

    def test_install_shell_completion_fish(self):
        """Test shell completion installation for fish."""
        with patch.dict(os.environ, {"SHELL": "/usr/bin/fish"}):
            with patch("hyper_core.cli.install_fish_completion") as mock_install:
                install_shell_completion()
                mock_install.assert_called_once()

    def test_install_shell_completion_unsupported(self):
        """Test shell completion installation for unsupported shell."""
        with patch.dict(os.environ, {"SHELL": "/bin/tcsh"}):
            with patch("rich.console.Console.print") as mock_print:
                install_shell_completion()
                # Should print warning about unsupported shell
                mock_print.assert_called()
                args = mock_print.call_args_list
                assert any("Unsupported shell" in str(call) for call in args)

    def test_install_zsh_completion_success(self):
        """Test successful zsh completion installation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            completion_dir = Path(temp_dir) / ".zsh" / "completions"
            
            with patch("pathlib.Path.home") as mock_home:
                mock_home.return_value = Path(temp_dir)
                with patch("rich.console.Console.print") as mock_print:
                    install_zsh_completion()
                    
                    # Check that completion file was created
                    completion_file = completion_dir / "_hyper"
                    assert completion_file.exists()
                    
                    # Check content
                    content = completion_file.read_text()
                    assert "#compdef hyper" in content
                    
                    # Check success message was printed
                    mock_print.assert_called()

    def test_install_zsh_completion_with_existing_fpath(self):
        """Test zsh completion installation with existing fpath config."""
        with tempfile.TemporaryDirectory() as temp_dir:
            zshrc_path = Path(temp_dir) / ".zshrc"
            zshrc_path.write_text("fpath=(~/.zsh/completions $fpath)")
            
            with patch("pathlib.Path.home") as mock_home:
                mock_home.return_value = Path(temp_dir)
                with patch("rich.console.Console.print") as mock_print:
                    install_zsh_completion()
                    
                    # Should not suggest adding fpath config
                    args = mock_print.call_args_list
                    setup_messages = [call for call in args if "Setup required" in str(call)]
                    assert len(setup_messages) == 0

    def test_install_bash_completion_success(self):
        """Test successful bash completion installation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            completion_dir = Path(temp_dir) / ".local" / "share" / "bash-completion" / "completions"
            
            with patch("pathlib.Path.home") as mock_home:
                mock_home.return_value = Path(temp_dir)
                with patch("rich.console.Console.print") as mock_print:
                    install_bash_completion()
                    
                    # Check that completion file was created
                    completion_file = completion_dir / "hyper"
                    assert completion_file.exists()
                    
                    # Check content
                    content = completion_file.read_text()
                    assert "_hyper_completion()" in content

    def test_install_fish_completion_success(self):
        """Test successful fish completion installation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            completion_dir = Path(temp_dir) / ".config" / "fish" / "completions"
            
            with patch("pathlib.Path.home") as mock_home:
                mock_home.return_value = Path(temp_dir)
                with patch("rich.console.Console.print") as mock_print:
                    install_fish_completion()
                    
                    # Check that completion file was created
                    completion_file = completion_dir / "hyper.fish"
                    assert completion_file.exists()
                    
                    # Check content
                    content = completion_file.read_text()
                    assert "complete -c hyper" in content

    def test_install_zsh_completion_permission_fallback(self):
        """Test zsh completion installation with permission errors."""
        with patch("pathlib.Path.mkdir") as mock_mkdir:
            with patch("pathlib.Path.exists") as mock_exists:
                with patch("os.access") as mock_access:
                    # Simulate permission errors for system directories
                    mock_exists.return_value = False
                    mock_access.return_value = False
                    mock_mkdir.side_effect = [PermissionError(), None]  # First fails, second succeeds
                    
                    with patch("pathlib.Path.write_text") as mock_write:
                        with patch("rich.console.Console.print"):
                            install_zsh_completion()
                            
                            # Should eventually succeed with fallback directory
                            mock_write.assert_called_once()


class TestCompletionCLIFlags:
    """Test CLI flags for completion."""

    def setup_method(self):
        """Set up test environment."""
        self.runner = CliRunner()

    def test_show_completion_flag_zsh(self):
        """Test --show-completion flag for zsh."""
        with patch.dict(os.environ, {"SHELL": "/bin/zsh"}):
            result = self.runner.invoke(main, ["--show-completion"])
            
            assert result.exit_code == 0
            assert "#compdef hyper" in result.output
            assert "_hyper()" in result.output

    def test_show_completion_flag_bash(self):
        """Test --show-completion flag for bash."""
        with patch.dict(os.environ, {"SHELL": "/bin/bash"}):
            result = self.runner.invoke(main, ["--show-completion"])
            
            assert result.exit_code == 0
            assert "_hyper_completion()" in result.output
            assert "complete -F _hyper_completion hyper" in result.output

    def test_show_completion_flag_fish(self):
        """Test --show-completion flag for fish."""
        with patch.dict(os.environ, {"SHELL": "/usr/bin/fish"}):
            result = self.runner.invoke(main, ["--show-completion"])
            
            assert result.exit_code == 0
            assert "complete -c hyper" in result.output

    def test_show_completion_flag_unsupported(self):
        """Test --show-completion flag for unsupported shell."""
        with patch.dict(os.environ, {"SHELL": "/bin/tcsh"}):
            result = self.runner.invoke(main, ["--show-completion"])
            
            assert result.exit_code == 0
            assert "# Unsupported shell" in result.output

    def test_install_completion_flag(self):
        """Test --install-completion flag."""
        with patch("hyper_core.cli.install_shell_completion") as mock_install:
            result = self.runner.invoke(main, ["--install-completion"])
            
            assert result.exit_code == 0
            mock_install.assert_called_once()

    def test_completion_flags_help(self):
        """Test that completion flags appear in help."""
        result = self.runner.invoke(main, ["--help"])
        
        assert result.exit_code == 0
        assert "--install-completion" in result.output
        assert "--show-completion" in result.output
        assert "Install shell completion" in result.output
        assert "Show shell completion script" in result.output


class TestCompletionUserGuidance:
    """Test user guidance for completion."""

    def setup_method(self):
        """Set up test environment."""
        self.runner = CliRunner()

    def test_main_shows_completion_tip_when_not_installed(self):
        """Test that main CLI shows completion tip when not installed."""
        with patch.dict(os.environ, {"SHELL": "/bin/zsh"}):
            with patch("hyper_core.cli.check_completion_installed") as mock_check:
                with patch("hyper_core.cli.discover_commands") as mock_discover:
                    mock_check.return_value = False
                    mock_registry = MagicMock()
                    mock_registry.list_commands.return_value = ["init"]
                    mock_discover.return_value = mock_registry
                    
                    result = self.runner.invoke(main, [])
                    
                    assert result.exit_code == 0
                    assert "Enable tab completion with 'hyper --install-completion'" in result.output

    def test_main_shows_completion_tip_when_installed(self):
        """Test that main CLI shows usage tip when completion is installed."""
        with patch.dict(os.environ, {"SHELL": "/bin/zsh"}):
            with patch("hyper_core.cli.check_completion_installed") as mock_check:
                with patch("hyper_core.cli.discover_commands") as mock_discover:
                    mock_check.return_value = True
                    mock_registry = MagicMock()
                    mock_registry.list_commands.return_value = ["init"]
                    mock_discover.return_value = mock_registry
                    
                    result = self.runner.invoke(main, [])
                    
                    assert result.exit_code == 0
                    assert "Use Tab to autocomplete commands and options" in result.output

    def test_main_no_completion_tip_for_unsupported_shell(self):
        """Test that main CLI doesn't show completion tip for unsupported shells."""
        with patch.dict(os.environ, {"SHELL": "/bin/tcsh"}):
            with patch("hyper_core.cli.discover_commands") as mock_discover:
                mock_registry = MagicMock()
                mock_registry.list_commands.return_value = ["init"]
                mock_discover.return_value = mock_registry
                
                result = self.runner.invoke(main, [])
                
                assert result.exit_code == 0
                assert "Enable tab completion" not in result.output
                assert "Use Tab to autocomplete" not in result.output

    def test_main_with_subcommand_no_completion_tip(self):
        """Test that completion tips don't show when running subcommands."""
        with patch.dict(os.environ, {"SHELL": "/bin/zsh"}):
            with patch("hyper_core.cli.check_completion_installed"):
                result = self.runner.invoke(main, ["init", "--help"])
                
                # Should not show completion tips when running subcommands
                assert "Enable tab completion" not in result.output
                assert "Use Tab to autocomplete" not in result.output


class TestShowShellCompletion:
    """Test show_shell_completion function."""

    def test_show_shell_completion_zsh(self):
        """Test show_shell_completion for zsh."""
        with patch.dict(os.environ, {"SHELL": "/bin/zsh"}):
            with patch("builtins.print") as mock_print:
                show_shell_completion()
                
                mock_print.assert_called_once()
                args, _ = mock_print.call_args
                assert "#compdef hyper" in args[0]

    def test_show_shell_completion_bash(self):
        """Test show_shell_completion for bash."""
        with patch.dict(os.environ, {"SHELL": "/bin/bash"}):
            with patch("builtins.print") as mock_print:
                show_shell_completion()
                
                mock_print.assert_called_once()
                args, _ = mock_print.call_args
                assert "_hyper_completion()" in args[0]

    def test_show_shell_completion_fish(self):
        """Test show_shell_completion for fish."""
        with patch.dict(os.environ, {"SHELL": "/usr/bin/fish"}):
            with patch("builtins.print") as mock_print:
                show_shell_completion()
                
                mock_print.assert_called_once()
                args, _ = mock_print.call_args
                assert "complete -c hyper" in args[0]

    def test_show_shell_completion_unsupported(self):
        """Test show_shell_completion for unsupported shell."""
        with patch.dict(os.environ, {"SHELL": "/bin/tcsh"}):
            with patch("builtins.print") as mock_print:
                show_shell_completion()
                
                mock_print.assert_called_once()
                args, _ = mock_print.call_args
                assert "# Unsupported shell" in args[0]


class TestCompletionIntegration:
    """Integration tests for completion functionality."""

    def test_completion_workflow_zsh(self):
        """Test complete workflow for zsh completion."""
        with tempfile.TemporaryDirectory() as temp_dir:
            runner = CliRunner()
            
            with patch.dict(os.environ, {"SHELL": "/bin/zsh"}):
                with patch("pathlib.Path.home") as mock_home:
                    mock_home.return_value = Path(temp_dir)
                    
                    # Install completion
                    result = runner.invoke(main, ["--install-completion"])
                    assert result.exit_code == 0
                    assert "Zsh completion installed" in result.output
                    
                    # Check file was created
                    completion_file = Path(temp_dir) / ".zsh" / "completions" / "_hyper"
                    assert completion_file.exists()
                    
                    # Show completion
                    result = runner.invoke(main, ["--show-completion"])
                    assert result.exit_code == 0
                    assert "#compdef hyper" in result.output

    def test_completion_detection_after_installation(self):
        """Test that completion is detected after installation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            completion_file = Path(temp_dir) / ".zsh" / "completions" / "_hyper"
            completion_file.parent.mkdir(parents=True)
            completion_file.write_text("#compdef hyper")
            
            with patch("pathlib.Path.home") as mock_home:
                mock_home.return_value = Path(temp_dir)
                
                # Should detect as installed
                assert check_completion_installed("zsh") is True