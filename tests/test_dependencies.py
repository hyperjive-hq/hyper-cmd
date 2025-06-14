"""Tests for project dependencies."""

import importlib.util

import pytest


class TestDependencies:
    """Test project dependencies are available."""

    def test_typing_extensions_available(self) -> None:
        """Test that typing-extensions is available."""
        try:
            import typing_extensions  # noqa: F401
            import typing_extensions as te

            assert hasattr(te, "TypedDict")
        except ImportError:
            pytest.fail("typing-extensions not available")

    def test_core_dependencies_available(self) -> None:
        """Test that core dependencies are available."""
        # Test PyYAML
        if importlib.util.find_spec("yaml") is None:
            pytest.fail("PyYAML not available")

        # Test click
        if importlib.util.find_spec("click") is None:
            pytest.fail("click not available")

        # Test rich
        if importlib.util.find_spec("rich") is None:
            pytest.fail("rich not available")

        # Test dependency-injector
        if importlib.util.find_spec("dependency_injector") is None:
            pytest.fail("dependency-injector not available")
