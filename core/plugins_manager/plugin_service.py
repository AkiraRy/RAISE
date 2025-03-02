from . import logger, PluginSettings
from .main import PluginManager
from utils import PluginType, BasePlugin


class PluginService:
    def __init__(self, config: PluginSettings):
        self.plugin_manager = PluginManager(config)
        self.loaded_plugins = {
            PluginType.STT: [],  # all plugins of this type must have .transcribe
            PluginType.STS: [],
            PluginType.TTS: [],
            PluginType.ELSE: []
        }

    def get_tts_plugins(self) -> list[BasePlugin]:
        return self.loaded_plugins.get(PluginType.TTS, [])

    def get_sts_plugins(self) -> list[BasePlugin]:
        return self.loaded_plugins.get(PluginType.STS, [])

    def get_stt_plugins(self) -> list[BasePlugin]:
        return self.loaded_plugins.get(PluginType.STT, [])

    def load_all_plugins(self):
        if not self.plugin_manager.config.load_all_plugins:
            return
        logger.info(f'[PluginService/load_all_plugins] Loading plugins.')
        for plugin_name, plugin in self.plugin_manager.load_plugins().items():
            self._add_plugin(plugin.plugin_type, plugin_name, plugin)

    def load_plugin(self, name: str):
        if not self.plugin_manager.load_plugin(name):
            return False, 404, f"Plugin {name} couldn't be loaded."

        plugin = self.plugin_manager.get_plugin(name)
        self._add_plugin(plugin.plugin_type, name, plugin)
        return True, 200, f"Plugin {name} loaded successfully."

    async def unload_plugin(self, name: str):
        plugin = self.plugin_manager.get_plugin(name)
        if not plugin:
            return False, 404, f"Plugin {name} is not loaded."

        self.loaded_plugins[plugin.plugin_type] = [
            (n, p) for n, p in self.loaded_plugins[plugin.plugin_type] if n != name
        ]

        if not await self.plugin_manager.unload_plugin(name):  # if failed to unload, then load it back.
            self._add_plugin(plugin.plugin_type, name, plugin)
            return False, 500, f"Couldn't unload {name} plugin."

        return True, 200, f"Plugin {name} unloaded."

    def _remove_plugin(self, plugin_type: PluginType, name: str):
        plugin_list = self.loaded_plugins.get(plugin_type, None)
        if not plugin_list:
            return  # add logging?

        self.loaded_plugins[plugin_type] = [
            (n, p) for n, p in plugin_list if n != name
        ]

    def _add_plugin(self, plugin_type: PluginType, name: str, plugin: BasePlugin):
        if plugin_type not in self.loaded_plugins:
            self.loaded_plugins[plugin_type] = []

        plugin_list = self.loaded_plugins[plugin_type]

        if any(tup[0] == name for tup in plugin_list):
            return

        plugin_list.append((name, plugin))
