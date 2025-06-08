# Hyper Core Project

This directory contains your Hyper Core project configuration and plugins.

## Structure

- `config.yaml` - Project configuration file
- `plugins/` - Directory containing project-specific plugins
- `plugins/hello_world/` - Example plugin demonstrating framework capabilities

## Getting Started

1. **Try the example plugin:**
   ```bash
   hyper hello --name "Your Name" --style fancy
   ```

2. **Create your own plugin:**
   - Copy the `hello_world` plugin as a template
   - Modify the plugin.py file with your logic
   - Update plugin.yaml with your metadata
   - Test with `hyper <your-command>`

3. **Configure your project:**
   - Edit `config.yaml` to customize settings
   - Add plugin bundle paths if needed
   - Set your preferred theme and logging level

## Plugin Development

The `hello_world` plugin demonstrates:

- **Commands**: CLI commands with arguments and validation
- **Widgets**: Interactive UI components for dashboard views
- **Services**: Background services and dependency injection
- **Configuration**: Plugin metadata and settings
- **Error Handling**: Robust error handling patterns

See the plugin files for detailed documentation and examples.

## Resources

- [Plugin Development Guide](https://github.com/your-repo/hyper-core/blob/main/plugin-guide.md)
- [Framework Documentation](https://github.com/your-repo/hyper-core/blob/main/README.md)
- [API Reference](https://github.com/your-repo/hyper-core/blob/main/docs/api.md)
