"""Real-world command usage tests demonstrating the framework."""

from io import StringIO
from unittest.mock import Mock, patch

from rich.console import Console

from hyper_core import BaseCommand, SimpleContainer
from hyper_core.commands import CommandRegistry


class DatabaseMigrationCommand(BaseCommand):
    """Example: Database migration command showing real-world usage."""

    @property
    def name(self) -> str:
        return "migrate"

    @property
    def description(self) -> str:
        return "Run database migrations"

    def execute(self, target: str = "latest", dry_run: bool = False) -> int:
        """Execute database migration.

        Args:
            target: Migration target (version or 'latest')
            dry_run: Show what would be done without executing
        """
        if dry_run:
            self.print_info(f"Would migrate to: {target}")
            return 0

        try:
            with self.progress_context("Running migrations"):
                # Simulate migration steps
                self.print_success(f"Migrated to {target}")
            return 0
        except Exception as e:
            self.print_error(f"Migration failed: {e}")
            return 1


class UserManagementCommand(BaseCommand):
    """Example: User management command with dependency injection."""

    @property
    def name(self) -> str:
        return "user"

    @property
    def description(self) -> str:
        return "Manage user accounts"

    def execute(self, action: str, username: str = None, email: str = None) -> int:
        """Execute user management action."""
        # Get services from container
        user_service = self.container.get("user_service")

        if action == "create":
            if not username or not email:
                self.print_error("Username and email required for user creation")
                return 1

            try:
                user_service.create_user(username, email)
                self.print_success(f"Created user: {username}")
                return 0
            except Exception as e:
                self.print_error(f"Failed to create user: {e}")
                return 1

        elif action == "list":
            users = user_service.list_users()
            self.print_info(f"Found {len(users)} users")
            for user in users:
                self.console.print(f"  • {user['username']} ({user['email']})")
            return 0

        else:
            self.print_error(f"Unknown action: {action}")
            return 1


class TestCommandFramework:
    """Test suite demonstrating command framework usage."""

    def test_basic_command_execution(self):
        """Test basic command creation and execution."""
        container = SimpleContainer()
        container.register(Console, Console())

        cmd = DatabaseMigrationCommand(container)

        # Test basic properties
        assert cmd.name == "migrate"
        assert cmd.description == "Run database migrations"

        # Test successful execution
        result = cmd.execute(target="v1.2.0", dry_run=True)
        assert result == 0

    def test_command_with_dependencies(self):
        """Test command using dependency injection."""
        # Mock user service
        mock_user_service = Mock()
        mock_user_service.create_user.return_value = {
            "id": 1,
            "username": "john",
            "email": "john@example.com",
        }
        mock_user_service.list_users.return_value = [
            {"username": "john", "email": "john@example.com"},
            {"username": "jane", "email": "jane@example.com"},
        ]

        # Set up container with dependencies
        container = SimpleContainer()
        container.register(Console, Console())
        container.register("user_service", mock_user_service)

        cmd = UserManagementCommand(container)

        # Test user creation
        result = cmd.execute("create", username="john", email="john@example.com")
        assert result == 0
        mock_user_service.create_user.assert_called_once_with("john", "john@example.com")

        # Test user listing
        result = cmd.execute("list")
        assert result == 0
        mock_user_service.list_users.assert_called_once()

    def test_command_error_handling(self):
        """Test command error handling and exit codes."""
        container = SimpleContainer()
        container.register(Console, Console())
        
        # Register mock user service
        mock_user_service = Mock()
        container.register("user_service", mock_user_service)

        cmd = UserManagementCommand(container)

        # Test missing required parameters
        result = cmd.execute("create", username="john")  # Missing email
        assert result == 1

        # Test unknown action
        result = cmd.execute("delete", username="john")
        assert result == 1

    def test_command_registry_integration(self):
        """Test command registration and discovery."""
        registry = CommandRegistry()
        container = SimpleContainer()
        container.register(Console, Console())

        # Register commands
        registry.register(DatabaseMigrationCommand, "migrate")
        registry.register(UserManagementCommand, "user")

        # Test command discovery
        commands = registry.list_commands()
        assert "migrate" in commands
        assert "user" in commands

        # Test command creation
        migrate_cmd = registry.create_command("migrate", container)
        assert isinstance(migrate_cmd, DatabaseMigrationCommand)
        assert migrate_cmd.name == "migrate"

    @patch("sys.stdout", new_callable=StringIO)
    def test_command_output_formatting(self, mock_stdout):
        """Test command output and console formatting."""
        container = SimpleContainer()
        console = Console(file=mock_stdout, force_terminal=False)
        container.register(Console, console)

        cmd = DatabaseMigrationCommand(container)
        cmd.execute(target="v1.2.0", dry_run=True)

        output = mock_stdout.getvalue()
        assert "Would migrate to: v1.2.0" in output

    def test_command_progress_context(self):
        """Test command progress indicators."""
        container = SimpleContainer()
        container.register(Console, Console())

        cmd = DatabaseMigrationCommand(container)

        # Test progress context manager
        with patch.object(cmd, "progress_context") as mock_progress:
            cmd.execute(target="latest", dry_run=False)
            mock_progress.assert_called_once_with("Running migrations")


class FileProcessorCommand(BaseCommand):
    """Example: File processing command showing path validation."""

    @property
    def name(self) -> str:
        return "process-files"

    @property
    def description(self) -> str:
        return "Process files in a directory"

    def execute(self, input_dir: str, output_dir: str = None, pattern: str = "*.txt") -> int:
        """Process files matching pattern."""
        from pathlib import Path

        input_path = Path(input_dir)
        if not self.validate_path(input_path, must_exist=True, must_be_dir=True):
            return 1

        output_path = Path(output_dir) if output_dir else input_path / "processed"
        if not self.validate_path(output_path.parent, must_exist=True, must_be_dir=True):
            return 1

        # Create output directory if it doesn't exist
        output_path.mkdir(exist_ok=True)

        files = list(input_path.glob(pattern))
        self.print_info(f"Found {len(files)} files matching {pattern}")

        for file_path in files:
            try:
                # Simulate file processing
                processed_file = output_path / f"processed_{file_path.name}"
                self.print_success(f"Processed: {file_path.name} -> {processed_file.name}")
            except Exception as e:
                self.print_error(f"Failed to process {file_path.name}: {e}")
                return 1

        return 0


class TestAdvancedCommandFeatures:
    """Test advanced command features and utilities."""

    def test_path_validation(self, tmp_path):
        """Test command path validation utilities."""
        container = SimpleContainer()
        container.register(Console, Console())

        cmd = FileProcessorCommand(container)

        # Create test directory structure
        input_dir = tmp_path / "input"
        input_dir.mkdir()
        (input_dir / "test1.txt").write_text("content1")
        (input_dir / "test2.txt").write_text("content2")

        # Test successful processing
        result = cmd.execute(str(input_dir), pattern="*.txt")
        assert result == 0

        # Verify output directory was created
        output_dir = input_dir / "processed"
        assert output_dir.exists()
        assert output_dir.is_dir()

    def test_command_chaining(self):
        """Test command composition and chaining."""
        container = SimpleContainer()
        container.register(Console, Console())

        # Create a composite command that uses other commands
        class DeploymentCommand(BaseCommand):
            @property
            def name(self) -> str:
                return "deploy"

            @property
            def description(self) -> str:
                return "Full deployment pipeline"

            def execute(self, environment: str = "staging") -> int:
                # Chain multiple commands
                migrate_cmd = DatabaseMigrationCommand(self.container)
                if migrate_cmd.execute(target="latest") != 0:
                    self.print_error("Migration failed, aborting deployment")
                    return 1

                self.print_success(f"Deployed to {environment}")
                return 0

        deploy_cmd = DeploymentCommand(container)
        result = deploy_cmd.execute("production")
        assert result == 0
