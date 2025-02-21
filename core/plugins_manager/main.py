import importlib
import json
import os
import yaml

from utils import Singleton
from . import *

FOLDERS = {
    "AUDIO_DIR": AUDIO_DIR,
    "PLUGINS_BASE_DIR": PLUGIN_BASE_DIR,  # for config save purposes
    "ASSETS_DIR": ASSETS_DIR
}

FILES = {
    "VOICEVOX_FILE_NAME": VOICEVOX_FILE_NAME,
    "COMMUNICATION_FILE_NAME": COMMUNICATION_FILE_NAME
}

# All allowed things for plugins to export


class PluginManager(metaclass=Singleton):
    def __init__(self):  # config: PluginSettings
        # self.config = config ??
        # self.logger = logger
        self.plugins = {}
        self.plugins_metadata = discover_plugins()

    def new_plugins_discovered(self) -> dict | bool:
        all_plugins = discover_plugins()
        new_plugins_metadata = {k: all_plugins[k] for k in all_plugins if k not in self.plugins_metadata}
        return False if not new_plugins_metadata else new_plugins_metadata

    def load_plugins(self):
        if not os.path.exists(PLUGIN_BASE_DIR):
            logger.warning(f"[PluginManager/load_plugins] Plugins directory '{PLUGIN_BASE_DIR}' not found.")
            return

        for plugin_name, plugin_path in self.plugins_metadata.items():
            raw_config = read_config(plugin_path, plugin_name)

            entry_file = raw_config.get("entry_point")
            class_name = raw_config.get("class_name")
            config_class_name = raw_config.get("config_class_name", "Config")

            if not entry_file or not class_name:
                logger.warning(f"[PluginManager/load_plugins] Skipping {plugin_name}: Missing entry_point or class_name.")
                continue

            entry_path = os.path.join(plugin_path, entry_file)
            if not os.path.exists(entry_path):
                logger.warning(f"[PluginManager/load_plugins] Skipping {plugin_name}: Entry file '{entry_file}' not found.")
                continue

            self._load_plugin(plugin_name, entry_path, class_name, config_class_name, raw_config)

        return self.plugins

    def _load_plugin(self, plugin_name, entry_path, class_name, config_class_name, raw_config):
        if self.plugins.get(plugin_name) is not None:
            logger.debug(
                f"[PluginManager/_load_plugins] Plugin {plugin_name} is already loaded.")
            return

        logger.debug(f"[PluginManager/_load_plugins] Entering with those args: {plugin_name=}, {entry_path=}, {class_name=}, {config_class_name=}, {raw_config=}")
        module_name = f"{plugin_name}_plugin"
        spec = importlib.util.spec_from_file_location(module_name, entry_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        if not hasattr(module, class_name):
            logger.error(f"[PluginManager/_load_plugins] Plugin {plugin_name}: Class '{class_name}' not found.")
            return

        PluginClass = getattr(module, class_name)

        # Load the config class if available
        ConfigClass = getattr(module, config_class_name, None)
        if ConfigClass:
            try:
                config = ConfigClass(**raw_config)
            except TypeError as e:
                logger.error(f"[PluginManager/_load_plugins] Failed to initialize config for {plugin_name}: {e}")
                return
        else:
            config = raw_config

        self.plugins[plugin_name] = PluginClass(logger, config)
        logger.info(f"[PluginManager/_load_plugins] Loaded plugin: {plugin_name}")

    def get_plugin(self, name):
        return self.plugins.get(name)


def discover_plugins():
    if not os.path.exists(PLUGIN_BASE_DIR):
        logger.warning(f"[discover_plugins] Plugins directory '{PLUGIN_BASE_DIR}' not found.")
        return

    plugins_metadata = {}
    for plugin_name in os.listdir(PLUGIN_BASE_DIR):
        plugin_path = os.path.join(PLUGIN_BASE_DIR, plugin_name)
        if not os.path.isdir(plugin_path) or plugin_name.startswith("__"):
            continue  # Skip non-directory items

        plugins_metadata[plugin_name] = plugin_path

    return plugins_metadata


def read_config(plugin_path, plugin_name):
    config_path = os.path.join(plugin_path, "config.yaml")
    if not os.path.exists(config_path):
        config_path = os.path.join(plugin_path, "config.json")
        if not os.path.exists(config_path):
            logger.warning(f"[read_config] Skipping {plugin_name}: No config file found.")
            return False

    logger.debug(f"[read_config] Loading config: {config_path}\tfor plugin: {plugin_name}")
    with open(config_path, "r") as f:
        return yaml.safe_load(f) if config_path.endswith(".yaml") else json.load(f)


# function to discover names of plugins in the plugin folder
# - populate the metadata dictionary using that.
# use that load plugins
# add access to that function through fastapi.
# make a helper function to discover if there is a new plugin? instead of doing that logic on server side
