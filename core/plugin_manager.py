import importlib
import os
import json
import sys

PLUGIN_DIR = os.path.join(os.path.dirname(__file__), '..', 'plugins')


class PluginManager:
    def __init__(self):
        self.plugins = {}
        self.active_plugins = {}

    def discover_plugins(self):
        """Discover available plugins by scanning the plugins directory."""
        for plugin_name in os.listdir(PLUGIN_DIR):
            plugin_path = os.path.join(PLUGIN_DIR, plugin_name)
            if os.path.isdir(plugin_path):
                metadata_file = os.path.join(plugin_path, 'plugin.json')
                if os.path.exists(metadata_file):
                    with open(metadata_file, 'r') as f:
                        metadata = json.load(f)
                        self.plugins[plugin_name] = metadata

    def list_plugins(self):
        """List all discovered plugins with their metadata."""
        for plugin_name, metadata in self.plugins.items():
            print(f"Plugin: {metadata['name']}")
            print(f"Description: {metadata['description']}")
            print(f"Entry Point: {metadata['entry_point']}\n")

    def load_plugin(self, plugin_name):
        """Load and run a plugin based on its entry point."""
        print(f"{plugin_name=}")
        print(f"{self.plugins=}")
        if plugin_name in self.plugins:
            entry_point = self.plugins[plugin_name]['entry_point']
            print(entry_point)
            module_name, func_name = entry_point.rsplit('.', 1)
            print(module_name)
            try:
                module = importlib.import_module(f'plugins.{module_name}')
                func = getattr(module, func_name)
                func()  # Run the plugin's main function
                self.active_plugins[plugin_name] = module  # Track active plugin
                print(f"Successfully loaded plugin: {plugin_name}")
            except (ImportError, AttributeError) as e:
                print(f"Error loading plugin {plugin_name}: {e}")
        else:
            print(f"Plugin {plugin_name} not found!")

    def unload_plugin(self, plugin_name):
        """Unload a plugin and clean up its resources."""
        if plugin_name in self.active_plugins:
            # Attempt to call the plugin's cleanup function (if defined)
            cleanup_entry = self.plugins[plugin_name].get("cleanup")
            if cleanup_entry:
                module_name, func_name = cleanup_entry.rsplit('.', 1)
                try:
                    module = importlib.import_module(f'plugins.{module_name}')
                    func = getattr(module, func_name)
                    func()  # Call the cleanup function
                    print(f"Successfully cleaned up plugin: {plugin_name}")
                except (ImportError, AttributeError) as e:
                    print(f"Error cleaning up plugin {plugin_name}: {e}")

            # Remove the plugin from active plugins
            del self.active_plugins[plugin_name]

            # Optionally, remove from sys.modules (to force reload if re-enabled)
            if f'plugins.{module_name}' in sys.modules:
                del sys.modules[f'plugins.{module_name}']

            print(f"Plugin {plugin_name} unloaded.")
        else:
            print(f"Plugin {plugin_name} is not currently active.")
