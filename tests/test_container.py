"""Real-world dependency injection container tests."""

from typing import Protocol, runtime_checkable
from unittest.mock import Mock

from rich.console import Console

from hyper_cmd.container import SimpleContainer, create_container


# Example Services for Testing
@runtime_checkable
class IEmailService(Protocol):
    """Email service interface."""

    def send_email(self, to: str, subject: str, body: str) -> bool:
        """Send an email."""
        ...


@runtime_checkable
class ILoggerService(Protocol):
    """Logger service interface."""

    def log(self, level: str, message: str) -> None:
        """Log a message."""
        ...


class SMTPEmailService:
    """SMTP implementation of email service."""

    def __init__(self, host: str, port: int, username: str, password: str):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.connected = False

    def connect(self):
        """Connect to SMTP server."""
        self.connected = True
        return True

    def send_email(self, to: str, subject: str, body: str) -> bool:
        """Send email via SMTP."""
        if not self.connected:
            self.connect()

        # Simulate sending email
        print(f"Sending email to {to}: {subject}")
        return True


class FileLoggerService:
    """File-based logger service."""

    def __init__(self, log_file: str, level: str = "INFO"):
        self.log_file = log_file
        self.level = level
        self.logs = []  # In-memory for testing

    def log(self, level: str, message: str) -> None:
        """Log message to file."""
        log_entry = f"[{level}] {message}"
        self.logs.append(log_entry)
        # In real implementation, would write to file


class DatabaseConnection:
    """Database connection service."""

    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self.connected = False
        self.transactions = []

    def connect(self):
        """Connect to database."""
        self.connected = True
        return self

    def execute(self, query: str, params: dict = None):
        """Execute database query."""
        if not self.connected:
            raise RuntimeError("Database not connected")

        transaction = {"query": query, "params": params or {}}
        self.transactions.append(transaction)
        return f"Result for: {query}"


class UserRepository:
    """User repository with database dependency."""

    def __init__(self, db: DatabaseConnection, logger: ILoggerService):
        self.db = db
        self.logger = logger

    def create_user(self, username: str, email: str) -> dict:
        """Create a new user."""
        self.logger.log("INFO", f"Creating user: {username}")

        query = "INSERT INTO users (username, email) VALUES (?, ?)"
        self.db.execute(query, {"username": username, "email": email})

        user = {"id": 1, "username": username, "email": email}
        self.logger.log("INFO", f"User created: {user['id']}")
        return user

    def get_user(self, user_id: int) -> dict:
        """Get user by ID."""
        self.logger.log("INFO", f"Fetching user: {user_id}")

        query = "SELECT * FROM users WHERE id = ?"
        self.db.execute(query, {"id": user_id})

        # Simulate user data
        return {"id": user_id, "username": "john", "email": "john@example.com"}


class NotificationService:
    """Notification service with multiple dependencies."""

    def __init__(self, email: IEmailService, logger: ILoggerService):
        self.email = email
        self.logger = logger

    def send_welcome_email(self, user: dict) -> bool:
        """Send welcome email to new user."""
        self.logger.log("INFO", f"Sending welcome email to {user['email']}")

        subject = "Welcome to our platform!"
        body = f"Hello {user['username']}, welcome to our platform!"

        success = self.email.send_email(user["email"], subject, body)

        if success:
            self.logger.log("INFO", f"Welcome email sent to {user['email']}")
        else:
            self.logger.log("ERROR", f"Failed to send welcome email to {user['email']}")

        return success


class TestSimpleContainer:
    """Test the SimpleContainer implementation."""

    def test_basic_registration_and_retrieval(self):
        """Test basic service registration and retrieval."""
        container = SimpleContainer()

        # Register a simple instance
        console = Console()
        container.register(Console, console)

        # Retrieve the instance
        retrieved_console = container.get(Console)
        assert retrieved_console is console

    def test_string_key_registration(self):
        """Test registration with string keys."""
        container = SimpleContainer()

        # Register with string key
        config = {"database_url": "sqlite:///test.db", "debug": True}
        container.register("config", config)

        # Retrieve by string key
        retrieved_config = container.get("config")
        assert retrieved_config == config
        assert retrieved_config["database_url"] == "sqlite:///test.db"

    def test_factory_registration(self):
        """Test registration with factory functions."""
        container = SimpleContainer()

        # Register factory function
        def create_email_service():
            return SMTPEmailService(
                host="smtp.example.com",
                port=587,
                username="user@example.com",
                password="password123",
            )

        container.register_factory(IEmailService, create_email_service)

        # Retrieve service created by factory
        email_service = container.get(IEmailService)
        assert isinstance(email_service, SMTPEmailService)
        assert email_service.host == "smtp.example.com"

    def test_singleton_behavior(self):
        """Test that services are singletons by default."""
        container = SimpleContainer()

        # Register a service
        logger = FileLoggerService("/tmp/test.log")
        container.register(ILoggerService, logger)

        # Get the service multiple times
        logger1 = container.get(ILoggerService)
        logger2 = container.get(ILoggerService)

        # Should be the same instance
        assert logger1 is logger2
        assert logger1 is logger

    def test_dependency_injection(self):
        """Test automatic dependency injection."""
        container = SimpleContainer()

        # Register dependencies
        db = DatabaseConnection("sqlite:///test.db")
        db.connect()
        container.register(DatabaseConnection, db)

        logger = FileLoggerService("/tmp/test.log")
        container.register(ILoggerService, logger)

        # Register service with dependencies
        def create_user_repo():
            return UserRepository(container.get(DatabaseConnection), container.get(ILoggerService))

        container.register_factory(UserRepository, create_user_repo)

        # Get service - dependencies should be injected
        user_repo = container.get(UserRepository)
        assert isinstance(user_repo, UserRepository)
        assert user_repo.db is db
        assert user_repo.logger is logger

        # Test functionality
        user = user_repo.create_user("john", "john@example.com")
        assert user["username"] == "john"
        assert len(logger.logs) > 0
        assert len(db.transactions) > 0


class TestAdvancedContainerFeatures:
    """Test advanced container features."""

    def test_complex_dependency_graph(self):
        """Test complex dependency injection scenarios."""
        container = SimpleContainer()

        # Set up dependency chain: NotificationService -> EmailService + Logger

        # 1. Register logger
        logger = FileLoggerService("/tmp/app.log")
        container.register(ILoggerService, logger)

        # 2. Register email service
        email_service = SMTPEmailService("smtp.gmail.com", 587, "app@example.com", "secret")
        container.register(IEmailService, email_service)

        # 3. Register notification service with dependencies
        def create_notification_service():
            return NotificationService(container.get(IEmailService), container.get(ILoggerService))

        container.register_factory(NotificationService, create_notification_service)

        # 4. Get the notification service
        notification_service = container.get(NotificationService)

        # Verify dependency injection worked
        assert notification_service.email is email_service
        assert notification_service.logger is logger

        # Test functionality
        user = {"username": "alice", "email": "alice@example.com"}
        success = notification_service.send_welcome_email(user)
        assert success

        # Verify logging occurred
        assert len(logger.logs) >= 2  # At least info and success logs
        assert any("Sending welcome email" in log for log in logger.logs)

    def test_container_scoping(self):
        """Test container scoping and isolation."""
        parent_container = SimpleContainer()
        child_container = SimpleContainer()

        # Register service in parent
        parent_logger = FileLoggerService("/tmp/parent.log")
        parent_container.register(ILoggerService, parent_logger)

        # Register different service in child
        child_logger = FileLoggerService("/tmp/child.log")
        child_container.register(ILoggerService, child_logger)

        # Verify isolation
        assert parent_container.get(ILoggerService) is parent_logger
        assert child_container.get(ILoggerService) is child_logger

    def test_conditional_registration(self):
        """Test conditional service registration."""
        container = SimpleContainer()

        # Register different implementations based on environment
        environment = "development"

        if environment == "development":
            # Use mock email service for development
            mock_email = Mock(spec=IEmailService)
            mock_email.send_email.return_value = True
            container.register(IEmailService, mock_email)
        else:
            # Use real SMTP service for production
            container.register(
                IEmailService, SMTPEmailService("smtp.example.com", 587, "user", "pass")
            )

        email_service = container.get(IEmailService)

        # In development, should get mock
        assert isinstance(email_service, Mock)

        # Test that mock works
        result = email_service.send_email("test@example.com", "Subject", "Body")
        assert result is True
        email_service.send_email.assert_called_once_with("test@example.com", "Subject", "Body")

    def test_lazy_initialization(self):
        """Test lazy initialization of services."""
        container = SimpleContainer()

        # Track initialization
        init_called = False

        class ExpensiveService:
            def __init__(self):
                nonlocal init_called
                init_called = True
                self.data = "expensive initialization"

        # Register factory for lazy initialization
        def create_expensive_service():
            return ExpensiveService()

        container.register_factory("expensive", create_expensive_service)

        # Service should not be initialized yet
        assert not init_called

        # Get service - should initialize now
        service = container.get("expensive")
        assert init_called
        assert service.data == "expensive initialization"

        # Second call should return same instance
        init_called = False
        service2 = container.get("expensive")
        assert not init_called  # Should not initialize again
        assert service2 is service


class TestContainerIntegration:
    """Test container integration with other framework components."""

    def test_container_with_commands(self):
        """Test container integration with command system."""
        from hyper_cmd import BaseCommand

        class UserCommand(BaseCommand):
            @property
            def name(self) -> str:
                return "user-cmd"

            @property
            def description(self) -> str:
                return "User management command"

            def execute(self, action: str, username: str = None) -> int:
                # Get services from container
                user_repo = self.container.get(UserRepository)
                notification_service = self.container.get(NotificationService)

                if action == "create" and username:
                    user = user_repo.create_user(username, f"{username}@example.com")
                    notification_service.send_welcome_email(user)
                    self.print_success(f"Created user: {username}")
                    return 0

                return 1

        # Set up container with all dependencies
        container = SimpleContainer()

        # Register all services
        container.register(Console, Console())

        db = DatabaseConnection("sqlite:///test.db")
        db.connect()
        container.register(DatabaseConnection, db)

        logger = FileLoggerService("/tmp/test.log")
        container.register(ILoggerService, logger)

        email_service = SMTPEmailService("smtp.example.com", 587, "app", "pass")
        container.register(IEmailService, email_service)

        # Register higher-level services
        container.register_factory(
            UserRepository,
            lambda: UserRepository(
                container.get(DatabaseConnection), container.get(ILoggerService)
            ),
        )

        container.register_factory(
            NotificationService,
            lambda: NotificationService(
                container.get(IEmailService), container.get(ILoggerService)
            ),
        )

        # Test command with container
        cmd = UserCommand(container)
        result = cmd.execute("create", "testuser")
        assert result == 0

        # Verify all services were used
        assert len(logger.logs) > 0
        assert len(db.transactions) > 0

    def test_container_factory_functions(self):
        """Test using container factory functions."""
        from dependency_injector.containers import DynamicContainer

        # Test the create_container factory
        container = create_container()
        # create_container returns a dependency-injector DynamicContainer instance
        assert isinstance(container, DynamicContainer)

        # Test that it can be configured
        console = Console()
        from hyper_cmd.container import configure_container

        configure_container(container, console=console)

        # Verify console was configured by accessing the provided instance
        assert hasattr(container, "console")
        provided_console = container.console()
        assert provided_console is console

    def test_configuration_driven_container(self):
        """Test configuration-driven container setup."""

        # Configuration for services
        config = {
            "database": {"connection_string": "postgresql://localhost:5432/mydb", "pool_size": 10},
            "email": {
                "host": "smtp.gmail.com",
                "port": 587,
                "username": "app@example.com",
                "password": "app_password",
            },
            "logging": {"file": "/var/log/app.log", "level": "INFO"},
        }

        container = SimpleContainer()
        container.register("config", config)

        # Register services based on configuration
        def create_database():
            cfg = container.get("config")["database"]
            return DatabaseConnection(cfg["connection_string"])

        def create_email_service():
            cfg = container.get("config")["email"]
            return SMTPEmailService(cfg["host"], cfg["port"], cfg["username"], cfg["password"])

        def create_logger():
            cfg = container.get("config")["logging"]
            return FileLoggerService(cfg["file"], cfg["level"])

        container.register_factory(DatabaseConnection, create_database)
        container.register_factory(IEmailService, create_email_service)
        container.register_factory(ILoggerService, create_logger)

        # Test that services are created with correct configuration
        db = container.get(DatabaseConnection)
        assert db.connection_string == "postgresql://localhost:5432/mydb"

        email = container.get(IEmailService)
        assert email.host == "smtp.gmail.com"
        assert email.port == 587

        logger = container.get(ILoggerService)
        assert logger.log_file == "/var/log/app.log"
        assert logger.level == "INFO"
