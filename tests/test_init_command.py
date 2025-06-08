"""Tests for the init command functionality."""

import tempfile
import yaml
from pathlib import Path
from unittest import mock

import pytest

from hyper_core.commands.init import InitCommand
from hyper_core.container.simple_container import SimpleContainer


class TestInitCommand:
    """Test InitCommand functionality."""
    
    def setup_method(self):
        """Set up test environment."""
        self.container = SimpleContainer()
        self.init_command = InitCommand(self.container)
    
    def test_command_properties(self):
        """Test basic command properties."""
        assert self.init_command.name == "init"
        assert "Initialize a new Hyper project" in self.init_command.description
        assert "Usage: hyper init" in self.init_command.help_text
    
    def test_init_new_project_with_force(self, tmp_path):
        """Test initializing a new project with --force flag."""
        with mock.patch('pathlib.Path.cwd', return_value=tmp_path):
            # Run init with force flag
            exit_code = self.init_command.execute(force=True)
            
            assert exit_code == 0
            
            # Verify .hyper directory structure
            hyper_dir = tmp_path / ".hyper"
            assert hyper_dir.exists()
            assert hyper_dir.is_dir()
            
            # Verify config file
            config_file = hyper_dir / "config.yaml"
            assert config_file.exists()
            
            with open(config_file) as f:
                config_data = yaml.safe_load(f)
                assert config_data['version'] == '1.0'
                assert config_data['plugins']['enabled'] is True
            
            # Verify plugins directory
            plugins_dir = hyper_dir / "plugins"
            assert plugins_dir.exists()
            assert plugins_dir.is_dir()
            
            # Verify example plugin
            hello_world_dir = plugins_dir / "hello_world"
            assert hello_world_dir.exists()
            assert (hello_world_dir / "__init__.py").exists()
            assert (hello_world_dir / "plugin.py").exists()
            assert (hello_world_dir / "plugin.yaml").exists()
            
            # Verify additional files
            assert (hyper_dir / ".gitignore").exists()
            assert (hyper_dir / "README.md").exists()
    
    def test_init_existing_project_without_force(self, tmp_path):
        """Test initializing when .hyper directory already exists."""
        # Create existing .hyper directory
        hyper_dir = tmp_path / ".hyper"
        hyper_dir.mkdir()
        
        with mock.patch('pathlib.Path.cwd', return_value=tmp_path):
            with mock.patch('builtins.input', return_value='n'):  # User says no
                exit_code = self.init_command.execute(force=False)
                
                assert exit_code == 1  # Should exit with error
    
    def test_init_existing_project_with_user_confirmation(self, tmp_path):
        """Test initializing with user confirmation when directory exists."""
        # Create existing .hyper directory
        hyper_dir = tmp_path / ".hyper"
        hyper_dir.mkdir()
        
        with mock.patch('pathlib.Path.cwd', return_value=tmp_path):
            # Mock user input: yes to overwrite, yes to proceed
            with mock.patch('builtins.input', side_effect=['y', 'y']):
                exit_code = self.init_command.execute(force=False)
                
                assert exit_code == 0
                
                # Verify structure was created
                assert (hyper_dir / "config.yaml").exists()
                assert (hyper_dir / "plugins").exists()
    
    def test_example_plugin_content(self, tmp_path):
        """Test that example plugin has correct content."""
        with mock.patch('pathlib.Path.cwd', return_value=tmp_path):
            self.init_command.execute(force=True)
            
            plugin_file = tmp_path / ".hyper" / "plugins" / "hello_world" / "plugin.py"
            assert plugin_file.exists()
            
            # Verify plugin content contains expected components
            content = plugin_file.read_text()
            assert "class HelloCommand(BaseCommand)" in content
            assert "class HelloWidget(BaseWidget)" in content
            assert "class HelloService(IService)" in content
            assert "PLUGIN_NAME = \"hello_world\"" in content
            assert "def register_plugin(container)" in content
            
            # Verify plugin.yaml metadata
            yaml_file = tmp_path / ".hyper" / "plugins" / "hello_world" / "plugin.yaml"
            assert yaml_file.exists()
            
            with open(yaml_file) as f:
                plugin_metadata = yaml.safe_load(f)
                assert plugin_metadata['name'] == 'hello_world'
                assert plugin_metadata['version'] == '1.0.0'
                assert 'HelloCommand' in plugin_metadata['entry_points']['commands']
    
    def test_config_file_content(self, tmp_path):
        """Test that config file has correct structure."""
        with mock.patch('pathlib.Path.cwd', return_value=tmp_path):
            self.init_command.execute(force=True)
            
            config_file = tmp_path / ".hyper" / "config.yaml"
            with open(config_file) as f:
                config_data = yaml.safe_load(f)
                
            # Verify config structure
            assert 'version' in config_data
            assert 'plugins' in config_data
            assert 'ui' in config_data
            assert 'logging' in config_data
            
            # Verify plugin settings
            plugins_config = config_data['plugins']
            assert plugins_config['enabled'] is True
            assert plugins_config['auto_discover'] is True
    
    def test_gitignore_content(self, tmp_path):
        """Test that .gitignore file has appropriate content."""
        with mock.patch('pathlib.Path.cwd', return_value=tmp_path):
            self.init_command.execute(force=True)
            
            gitignore_file = tmp_path / ".hyper" / ".gitignore"
            content = gitignore_file.read_text()
            
            # Verify important patterns are included
            assert "*.log" in content
            assert "*.cache" in content
            assert "plugins/*/venv/" in content
            assert ".DS_Store" in content
    
    def test_readme_content(self, tmp_path):
        """Test that README.md file has helpful content."""
        with mock.patch('pathlib.Path.cwd', return_value=tmp_path):
            self.init_command.execute(force=True)
            
            readme_file = tmp_path / ".hyper" / "README.md"
            content = readme_file.read_text()
            
            # Verify README contains helpful information
            assert "# Hyper Core Project" in content
            assert "hyper hello" in content  # Example command
            assert "plugins/" in content
            assert "config.yaml" in content
    
    def test_error_handling(self, tmp_path):
        """Test error handling when init fails."""
        with mock.patch('pathlib.Path.cwd', return_value=tmp_path):
            # Mock Path.mkdir to raise an exception
            with mock.patch.object(Path, 'mkdir', side_effect=PermissionError("Permission denied")):
                exit_code = self.init_command.execute(force=True)
                
                assert exit_code == 1  # Should exit with error


class TestInitCommandIntegration:
    """Test init command integration with the framework."""
    
    def test_plugin_directory_integration(self, tmp_path):
        """Test that initialized project works with plugin loading."""
        from hyper_core.config import HyperConfig, reset_config
        
        # Initialize project
        container = SimpleContainer()
        init_command = InitCommand(container)
        
        with mock.patch('pathlib.Path.cwd', return_value=tmp_path):
            exit_code = init_command.execute(force=True)
            assert exit_code == 0
            
            # Reset global config to force reload
            reset_config()
            
            # Test that config system finds the .hyper directory
            config = HyperConfig(tmp_path)
            assert config.has_hyper_directory()
            assert config.get_plugins_directory() == tmp_path / ".hyper" / "plugins"
    
    def test_example_plugin_is_discoverable(self, tmp_path):
        """Test that the created example plugin can be discovered."""
        from hyper_core.plugins.loader import PluginDiscovery
        
        # Initialize project
        container = SimpleContainer()
        init_command = InitCommand(container)
        
        with mock.patch('pathlib.Path.cwd', return_value=tmp_path):
            exit_code = init_command.execute(force=True)
            assert exit_code == 0
            
            # Test plugin discovery
            plugins_dir = tmp_path / ".hyper" / "plugins"
            discovery = PluginDiscovery(str(plugins_dir))
            discovered_plugins = discovery.discover()
            
            # Should find the hello_world plugin
            plugin_names = [p.name for p in discovered_plugins]
            assert "hello_world" in plugin_names
    
    def test_init_command_available_in_registry(self):
        """Test that init command is properly registered."""
        from hyper_core.commands.registry import CommandRegistry
        
        registry = CommandRegistry()
        registry.register(InitCommand, "init")
        
        assert "init" in registry.list_commands()
        assert registry.get("init") == InitCommand


if __name__ == "__main__":
    pytest.main([__file__])