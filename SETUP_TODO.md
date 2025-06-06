# Hyper-Core Setup and Testing Todo List

## Phase 1: Prepare Hyper-Core as a Standalone Package

### 1. Create New Repository
- [x] Create new directory/repository for hyper-core
- [x] Copy the hyper-core directory contents
- [ ] Initialize git repository
- [ ] Create .gitignore file:
  ```
  __pycache__/
  *.py[cod]
  *$py.class
  *.so
  .Python
  build/
  develop-eggs/
  dist/
  downloads/
  eggs/
  .eggs/
  lib/
  lib64/
  parts/
  sdist/
  var/
  wheels/
  *.egg-info/
  .installed.cfg
  *.egg
  MANIFEST
  .env
  venv/
  ENV/
  .vscode/
  .idea/
  *.swp
  .DS_Store
  .coverage
  htmlcov/
  .pytest_cache/
  .mypy_cache/
  .ruff_cache/
  ```

### 2. Verify Package Structure
- [ ] Ensure this structure exists:
  ```
  hyper-core/
  ├── src/
  │   └── hyper_core/
  │       ├── __init__.py
  │       ├── commands/
  │       ├── container/
  │       ├── plugins/
  │       ├── protocols.py
  │       ├── py.typed
  │       └── ui/
  ├── tests/  # Create this
  │   └── __init__.py
  ├── pyproject.toml
  ├── README.md
  └── LICENSE  # Add appropriate license
  ```

### 3. Create Initial Tests
- [ ] Create tests/__init__.py
- [ ] Create tests/test_import.py:
  ```python
  """Basic import tests to ensure package is installable."""
  
  def test_can_import_package():
      import hyper_core
      assert hyper_core.__version__ == "0.1.0"
  
  def test_can_import_main_classes():
      from hyper_core import BaseCommand, SimpleContainer, BaseWidget
      from hyper_core.plugins import plugin_registry
      assert BaseCommand is not None
  ```

## Phase 2: Set Up for Development Installation

### 4. Create Development Environment
- [ ] Create virtual environment: `python -m venv venv`
- [ ] Activate it: `source venv/bin/activate` (or `venv\Scripts\activate` on Windows)
- [ ] Install package in editable mode: `pip install -e .`
- [ ] Install dev dependencies: `pip install -e ".[dev]"`
- [ ] Run basic tests: `pytest tests/`

## Phase 3: Install in Another Project (Multiple Methods)

### Method A: Direct Path Installation (Easiest for Testing)
- [ ] In your test project, create a virtual environment
- [ ] Install directly from local path:
  ```bash
  pip install -e /path/to/hyper-core
  ```

### Method B: Git Installation (Good for Development)
- [ ] Push hyper-core to a git repository (GitHub, GitLab, etc.)
- [ ] In your test project's pyproject.toml:
  ```toml
  [project]
  dependencies = [
      "hyper-core @ git+https://github.com/yourusername/hyper-core.git@main",
      # or for SSH:
      # "hyper-core @ git+ssh://git@github.com/yourusername/hyper-core.git@main",
  ]
  ```

### Method C: File URL Installation (Local Testing)
- [ ] In your test project's pyproject.toml:
  ```toml
  [project]
  dependencies = [
      "hyper-core @ file:///absolute/path/to/hyper-core",
  ]
  ```

### Method D: Build and Install Wheel (Most Production-Like)
- [ ] In hyper-core directory:
  ```bash
  pip install build
  python -m build
  ```
- [ ] This creates dist/ directory with wheel and tarball
- [ ] In test project:
  ```bash
  pip install /path/to/hyper-core/dist/hyper_core-0.1.0-py3-none-any.whl
  ```

## Phase 4: Create Test Project

### 5. Set Up Test Project Structure
- [ ] Create new directory for test project
- [ ] Create pyproject.toml:
  ```toml
  [build-system]
  requires = ["setuptools>=61.0"]
  build-backend = "setuptools.build_meta"
  
  [project]
  name = "hyper-core-test"
  version = "0.1.0"
  requires-python = ">=3.9"
  dependencies = [
      "hyper-core",  # Add using one of the methods above
      "click>=8.0",
      "rich>=13.0",
  ]
  ```

### 6. Create Test Plugin
- [ ] Create example_plugin/plugin.py:
  ```python
  """Example plugin to test hyper-core."""
  
  PLUGIN_NAME = "example"
  PLUGIN_VERSION = "1.0.0"
  PLUGIN_DESCRIPTION = "Example plugin for testing"
  
  from hyper_core import BaseCommand, BaseWidget, WidgetSize
  
  
  class HelloCommand(BaseCommand):
      @property
      def name(self) -> str:
          return "hello"
      
      @property
      def description(self) -> str:
          return "Test command from plugin"
      
      def execute(self) -> int:
          self.print_success("Hello from hyper-core plugin!")
          return 0
  
  
  class StatusWidget(BaseWidget):
      def __init__(self):
          super().__init__(title="Test Status", size=WidgetSize.SMALL)
      
      def draw_content(self, stdscr, x, y, width, height):
          stdscr.addstr(y + height // 2, x, "Plugin widget works!")
  ```

### 7. Create Test Application
- [ ] Create test_app.py:
  ```python
  """Test application using hyper-core."""
  
  import click
  from hyper_core import SimpleContainer, plugin_registry
  from hyper_core.plugins import PluginDiscovery
  from rich.console import Console
  
  
  @click.command()
  def main():
      """Test hyper-core functionality."""
      # Set up container
      container = SimpleContainer()
      container.register(Console, Console())
      
      # Test plugin system
      plugin_registry.initialize(["./plugins"])
      discovered = plugin_registry.discover_plugins()
      
      print(f"Discovered plugins: {discovered}")
      
      # Test command
      from example_plugin.plugin import HelloCommand
      cmd = HelloCommand(container)
      cmd.run()
  
  
  if __name__ == "__main__":
      main()
  ```

## Phase 5: Testing and Validation

### 8. Run Tests
- [ ] Test imports: `python -c "import hyper_core; print(hyper_core.__version__)"`
- [ ] Run test application: `python test_app.py`
- [ ] Test CLI integration with Click
- [ ] Test widget in a simple ncurses app
- [ ] Test theme system

### 9. Create More Complex Example
- [ ] Create a full example app showing:
  - [ ] Plugin loading
  - [ ] Command execution
  - [ ] Widget rendering
  - [ ] Theme switching
  - [ ] DI container usage

## Phase 6: Prepare for Distribution (Optional)

### 10. PyPI Preparation
- [ ] Register on PyPI (pypi.org) and Test PyPI (test.pypi.org)
- [ ] Create ~/.pypirc with credentials
- [ ] Test upload to Test PyPI:
  ```bash
  python -m build
  python -m twine upload --repository testpypi dist/*
  ```
- [ ] Test install from Test PyPI:
  ```bash
  pip install --index-url https://test.pypi.org/simple/ hyper-core
  ```

## Troubleshooting Tips

### Common Issues:
1. **Import errors**: Make sure `src/` layout is used and package is installed
2. **Missing dependencies**: Check all imports are in pyproject.toml
3. **Version conflicts**: Use virtual environments for isolation
4. **Module not found**: Ensure __init__.py files exist in all directories

### Debug Commands:
```bash
# Check if package is installed
pip list | grep hyper-core

# Show package info
pip show hyper-core

# Check import path
python -c "import hyper_core; print(hyper_core.__file__)"

# Reinstall in editable mode
pip uninstall hyper-core
pip install -e /path/to/hyper-core
```

## Next Steps After Testing

1. Add comprehensive test suite
2. Set up CI/CD (GitHub Actions)
3. Add documentation (Sphinx/MkDocs)
4. Create example projects
5. Publish to PyPI for public use
