"""Test runner plugin for running pytest tests with venv management."""

import os
import subprocess
import sys
from pathlib import Path
from typing import Optional

from hyper_cmd.commands import BaseCommand

PLUGIN_NAME = "test_runner"
PLUGIN_VERSION = "1.0.0"
PLUGIN_DESCRIPTION = "Run project tests using pytest with virtual environment management"
PLUGIN_AUTHOR = "Hyper Team"


class TestCommand(BaseCommand):
    """Command to run tests in the project with proper venv handling."""

    @property
    def name(self) -> str:
        return "test"

    @property
    def description(self) -> str:
        return "Run project tests using pytest (handles venv activation and dependencies)"

    @property
    def help_text(self) -> str:
        return """
Run project tests using pytest with automatic virtual environment management.

This command will:
1. Check if we're in an activated virtual environment
2. If not, try to find and activate a virtual environment
3. Install the project in editable mode (pip install -e .)
4. Run pytest with the specified options

Examples:
  hyper test                     # Run all tests
  hyper test -v                  # Run tests with verbose output
  hyper test -k "plugin"         # Run only tests matching "plugin"
  hyper test --cov               # Run tests with coverage
  hyper test tests/test_cli.py   # Run specific test file
  hyper test --skip-install      # Skip pip install -e . step
"""

    def execute(
        self,
        pattern: Optional[str] = None,
        verbose: bool = False,
        coverage: bool = False,
        file: Optional[str] = None,
        skip_install: bool = False,
        *args: str
    ) -> int:
        """Execute the test command with venv management.

        Args:
            pattern: Test name pattern to match (pytest -k option)
            verbose: Enable verbose output (pytest -v option)
            coverage: Enable coverage reporting (pytest --cov option)
            file: Specific test file to run
            skip_install: Skip the pip install -e . step
            *args: Additional arguments to pass to pytest

        Returns:
            Exit code from pytest
        """
        # Find project root
        project_root = self._find_project_root()
        if not project_root:
            self.print_error("Could not find project root (no pyproject.toml found)")
            return 1

        self.print_info(f"Project root: {project_root}")

        # Check and setup virtual environment
        venv_python, venv_path = self._ensure_venv_activated(project_root)
        if not venv_python:
            return 1

        # Install project dependencies unless skipped
        if not skip_install:
            if not self._install_project_dependencies(venv_python, project_root):
                return 1

        # Build and run pytest command
        cmd = self._build_pytest_command(
            python_executable=venv_python,
            project_root=project_root,
            pattern=pattern,
            verbose=verbose,
            coverage=coverage,
            file=file,
            extra_args=list(args)
        )

        self.print_info(f"Running tests with virtual environment: {venv_path}")
        if verbose:
            self.print_info(f"Command: {' '.join(cmd)}")

        # Run pytest
        try:
            result = subprocess.run(
                cmd,
                cwd=project_root,
                capture_output=False,  # Show output in real-time
                text=True,
                env=self._get_venv_environment(venv_path)
            )

            # Print summary based on exit code
            if result.returncode == 0:
                self.print_success("All tests passed!")
            elif result.returncode == 1:
                self.print_error("Some tests failed")
            elif result.returncode == 2:
                self.print_error("Test execution was interrupted")
            elif result.returncode == 3:
                self.print_error("Internal error occurred")
            elif result.returncode == 4:
                self.print_error("pytest usage error")
            elif result.returncode == 5:
                self.print_warning("No tests were collected")
            else:
                self.print_error(f"pytest exited with code {result.returncode}")

            return result.returncode

        except FileNotFoundError:
            self.print_error("pytest not found in virtual environment")
            return 1
        except KeyboardInterrupt:
            self.print_warning("Test execution interrupted by user")
            return 130
        except Exception as e:
            self.print_error(f"Error running tests: {e}")
            return 1

    def _find_project_root(self) -> Optional[Path]:
        """Find the project root by looking for pyproject.toml."""
        current = Path.cwd()

        # Check current directory and all parent directories
        for path in [current] + list(current.parents):
            if (path / "pyproject.toml").exists():
                return path

        return None

    def _is_venv_activated(self) -> tuple[bool, Optional[Path]]:
        """Check if we're currently in an activated virtual environment."""
        # Check for VIRTUAL_ENV environment variable
        venv_path = os.environ.get('VIRTUAL_ENV')
        if venv_path:
            venv_path = Path(venv_path)
            python_path = venv_path / ("Scripts" if os.name == 'nt' else "bin") / "python"
            if python_path.exists():
                return True, venv_path

        # Check if current Python is in a venv by looking at sys.prefix
        if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
            # We're in a venv, try to determine the path
            venv_path = Path(sys.prefix)
            return True, venv_path

        return False, None

    def _find_venv(self, project_root: Path) -> Optional[Path]:
        """Find a virtual environment in common locations."""
        # Common venv directory names and locations
        possible_venv_locations = [
            project_root / "venv",
            project_root / ".venv",
            project_root / "env",
            project_root / ".env",
            Path.home() / "venvs" / project_root.name,
        ]

        for venv_path in possible_venv_locations:
            if venv_path.exists() and venv_path.is_dir():
                # Check if it's actually a venv by looking for python executable
                python_path = venv_path / ("Scripts" if os.name == 'nt' else "bin") / "python"
                if python_path.exists():
                    self.print_info(f"Found virtual environment at: {venv_path}")
                    return venv_path

        return None

    def _ensure_venv_activated(self, project_root: Path) -> tuple[Optional[str], Optional[Path]]:
        """Ensure we have an activated virtual environment."""
        # First check if we're already in an activated venv
        is_activated, current_venv = self._is_venv_activated()

        if is_activated and current_venv:
            python_exe = current_venv / ("Scripts" if os.name == 'nt' else "bin") / "python"
            self.print_info(f"Using already activated virtual environment: {current_venv}")
            return str(python_exe), current_venv

        # Try to find a venv
        venv_path = self._find_venv(project_root)
        if not venv_path:
            self.print_error("No virtual environment found!")
            self.print_error("Please create one with: python -m venv venv")
            self.print_error("Then activate it and run this command again.")
            return None, None

        # Get python executable from found venv
        python_exe = venv_path / ("Scripts" if os.name == 'nt' else "bin") / "python"

        if not python_exe.exists():
            self.print_error(f"Python executable not found in venv: {python_exe}")
            return None, None

        self.print_info(f"Using virtual environment: {venv_path}")
        return str(python_exe), venv_path

    def _install_project_dependencies(self, python_executable: str, project_root: Path) -> bool:
        """Install the project in editable mode with all dependencies."""
        self.print_info("Installing project dependencies...")

        # Install the project in editable mode
        cmd = [python_executable, "-m", "pip", "install", "-e", ".[dev]"]

        try:
            result = subprocess.run(
                cmd,
                cwd=project_root,
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                self.print_success("Dependencies installed successfully")
                return True
            else:
                self.print_error("Failed to install dependencies")
                if result.stderr:
                    self.print_error(f"Error: {result.stderr}")
                return False

        except Exception as e:
            self.print_error(f"Error installing dependencies: {e}")
            return False

    def _get_venv_environment(self, venv_path: Path) -> dict:
        """Get environment variables for running commands in the venv."""
        env = os.environ.copy()

        # Set VIRTUAL_ENV
        env['VIRTUAL_ENV'] = str(venv_path)

        # Update PATH to include venv bin directory
        bin_dir = venv_path / ("Scripts" if os.name == 'nt' else "bin")
        if 'PATH' in env:
            env['PATH'] = f"{bin_dir}{os.pathsep}{env['PATH']}"
        else:
            env['PATH'] = str(bin_dir)

        # Remove PYTHONHOME if set (can interfere with venv)
        env.pop('PYTHONHOME', None)

        return env

    def _build_pytest_command(
        self,
        python_executable: str,
        project_root: Path,
        pattern: Optional[str] = None,
        verbose: bool = False,
        coverage: bool = False,
        file: Optional[str] = None,
        extra_args: Optional[list[str]] = None
    ) -> list[str]:
        """Build the pytest command with appropriate arguments."""
        cmd = [python_executable, "-m", "pytest"]

        # Add verbose flag
        if verbose:
            cmd.append("-v")

        # Add pattern matching
        if pattern:
            cmd.extend(["-k", pattern])

        # Add coverage
        if coverage:
            cmd.extend(["--cov=src/hyper_cmd", "--cov-report=term-missing"])

        # Add specific file or default to tests directory
        if file:
            # Handle both absolute and relative paths
            test_path = Path(file)
            if not test_path.is_absolute():
                test_path = project_root / test_path

            if test_path.exists():
                cmd.append(str(test_path))
            else:
                # If file doesn't exist, let pytest handle the error
                cmd.append(file)
        else:
            # Default to tests directory if it exists
            tests_dir = project_root / "tests"
            if tests_dir.exists():
                cmd.append("tests/")

        # Add any extra arguments
        if extra_args:
            cmd.extend(extra_args)

        return cmd


class TestInfoCommand(BaseCommand):
    """Command to show test-related information."""

    @property
    def name(self) -> str:
        return "test-info"

    @property
    def description(self) -> str:
        return "Show information about the test suite and environment"

    def execute(self) -> int:
        """Show test and environment information."""
        project_root = self._find_project_root()
        if not project_root:
            self.print_error("Could not find project root")
            return 1

        self.print_info(f"Project root: {project_root}")

        # Check virtual environment status
        is_activated, venv_path = self._is_venv_activated()
        if is_activated and venv_path:
            self.print_success(f"Virtual environment active: {venv_path}")
        else:
            self.print_warning("No virtual environment activated")

            # Try to find one
            found_venv = self._find_venv(project_root)
            if found_venv:
                self.print_info(f"Found virtual environment: {found_venv}")
            else:
                self.print_warning("No virtual environment found")

        # Show test directory info
        tests_dir = project_root / "tests"
        self.print_info(f"Tests directory: {tests_dir}")

        if tests_dir.exists():
            test_files = list(tests_dir.glob("test_*.py"))
            self.print_info(f"Test files found: {len(test_files)}")

            if test_files:
                self.console.print("\n[bold]Test files:[/bold]")
                for test_file in sorted(test_files):
                    self.console.print(f"  • {test_file.name}")
        else:
            self.print_warning("Tests directory not found")

        # Check pytest availability
        python_to_check = sys.executable
        if is_activated and venv_path:
            python_to_check = str(venv_path / ("Scripts" if os.name == 'nt' else "bin") / "python")

        try:
            result = subprocess.run([python_to_check, "-m", "pytest", "--version"],
                                  capture_output=True, text=True)
            if result.returncode == 0:
                version_line = result.stdout.strip().split('\n')[0]
                self.print_info(f"pytest: {version_line}")
            else:
                self.print_warning("pytest not available")
        except FileNotFoundError:
            self.print_warning("pytest not installed")

        return 0

    def _find_project_root(self) -> Optional[Path]:
        """Find the project root by looking for pyproject.toml."""
        current = Path.cwd()

        for path in [current] + list(current.parents):
            if (path / "pyproject.toml").exists():
                return path

        return None

    def _is_venv_activated(self) -> tuple[bool, Optional[Path]]:
        """Check if we're currently in an activated virtual environment."""
        venv_path = os.environ.get('VIRTUAL_ENV')
        if venv_path:
            venv_path = Path(venv_path)
            python_path = venv_path / ("Scripts" if os.name == 'nt' else "bin") / "python"
            if python_path.exists():
                return True, venv_path

        if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
            venv_path = Path(sys.prefix)
            return True, venv_path

        return False, None

    def _find_venv(self, project_root: Path) -> Optional[Path]:
        """Find a virtual environment in common locations."""
        possible_locations = [
            project_root / "venv",
            project_root / ".venv",
            project_root / "env",
            project_root / ".env",
        ]

        for venv_path in possible_locations:
            if venv_path.exists() and venv_path.is_dir():
                python_path = venv_path / ("Scripts" if os.name == 'nt' else "bin") / "python"
                if python_path.exists():
                    return venv_path

        return None
