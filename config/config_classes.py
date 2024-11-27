from dataclasses import dataclass, field
from typing import Dict, Optional
from pathlib import Path
import yaml
from .settings import DEFAULT_SETTINGS, SETTINGS_FROM_ENV, ensure_directory_exists, logger, LLM_SETTINGS_DIR
from pydantic import BaseModel, model_validator


class BaseSettings(BaseModel):
    @classmethod
    def load_from_yaml(cls, filepath: str) -> "BaseSettings":
        if not Path(filepath).exists():
            raise FileNotFoundError(f"The specified YAML file '{filepath}' does not exist.")

        with open(filepath, 'r') as f:
            data = yaml.safe_load(f)

        instance = cls(**data)

        return instance

    def save_to_yaml(self, filepath: str):
        with open(filepath, 'w') as f:
            yaml.dump(self.dict(), f)

    def __str__(self):
        fields_str = ', '.join(f"{key}={value!r}" for key, value in self.dict().items())
        return f"{self.__class__.__name__}({fields_str})"


class DiscordSettings(BaseSettings):
    bot_chat: str = ""


class TelegramSettings(BaseSettings):
    creator_id: int = -1  # whitelist


class WeaviateSettings(BaseSettings):
    author_name: str
    class_name: str = "MemoryK"  # for testing, I will use an already created class
    http_host: str = "localhost"
    http_port: int = 8080
    http_secure: bool = False
    grpc_host: str = "localhost"
    grpc_port: int = 50051
    grpc_secure: bool = False
    retry_delay: int = 2  # seconds
    max_retries: int = 2
    max_distance: float = 0.5
    alpha: float = 0.5  # 1 pure vector search, 0 pure keyword search
    limit: int = 2
    sim_search_type: str = 'hybrid'


@dataclass
class PluginSettings:  # no idea currently how to make this work. in future fix
    plugin_name: str
    plugin_config: Dict[str, str] = field(default_factory=dict)


# noinspection PyNestedDecorators
class LLMSettings(BaseSettings):
    llm_model_name: str  # Pydantic safe
    llm_model_file: str
    verbose: bool
    cuda: int
    chat_format: str
    n_gpu_layers: int
    n_ctx: int
    n_batch: int
    temperature: float
    max_tokens: int
    repeat_penalty: float
    top_k: int
    top_p: float
    min_p: float
    typical_p: float
    stream: bool
    local: bool
    endpoint: Optional[str] = None
    seed: int | None = None
    stop: str | list[str] | None = field(default_factory=list)

    @model_validator(mode='before')
    @classmethod
    def check_endpoint_if_local_is_false(cls, values):
        local = values.get('local')
        endpoint = values.get('endpoint')

        # If 'local' is False, 'endpoint' must be provided
        if local is False and not endpoint:
            raise ValueError("If 'local' is set to False, 'endpoint' must be specified.")

        if local is True and endpoint is not None:
            raise ValueError("If 'local' is set to True, 'endpoint' must not be specified.")

        return values

    @model_validator(mode='before')
    @classmethod
    def check_cuda_and_layers(cls, values):
        cuda = values.get('cuda')
        n_gpu_layers = values.get('n_gpu_layers')

        # If cuda is set to 0, n_gpu_layers should also be 0
        if cuda == 0 and n_gpu_layers != 0:
            logger.warning("Setting 'n_gpu_layers' to 0 as 'cuda' is set to 0.")
            values['n_gpu_layers'] = 0

        return values


class PubSubSettings(BaseSettings):
    input_message_topic: str
    processed_message_topic: str


class BrainSettings(BaseSettings):
    use_memories: bool = False
    save_memories: bool = False
    add_context: bool = False
    persona_path: str = "default_persona"
    creator_name: str = ""
    assistant_name: str = ""


class Config(BaseSettings):
    telegram: Optional[TelegramSettings] = None
    discord: Optional[DiscordSettings] = None
    weaviate: Optional[WeaviateSettings] = None
    llm: Optional[LLMSettings] = None
    pubsub: Optional[PubSubSettings] = None
    brain: Optional[BrainSettings] = None
    llm_type: str = None


class SettingsManager:
    def __init__(self):
        self.config: Config = Config()
        self.yaml_path = Path(SETTINGS_FROM_ENV)

        if not self.yaml_path.exists():
            logger.warning(
                f"[SettingsManager/__init__] File '{self.yaml_path}' does not exist. Falling back to DEFAULT_SETTINGS.")
            self.yaml_path = DEFAULT_SETTINGS

        if not self.yaml_path.exists():
            logger.error(f"[SettingsManager/__init__] Neither '{SETTINGS_FROM_ENV}' nor '{DEFAULT_SETTINGS}' exists.")
            raise RuntimeError(f"[SettingsManager/__init__] Configuration file not found: '{SETTINGS_FROM_ENV}' or '{DEFAULT_SETTINGS}'.")

        ensure_directory_exists(self.yaml_path.parent)

    def load_settings(self):
        if not self.yaml_path.exists():
            logger.error(f"[SettingsManager/load_settings] Yaml({self.yaml_path}) path doesn't exists")
            raise RuntimeError(f"[SettingsManager/load_settings] Configuration file '{self.yaml_path}' not found.")

        try:
            with open(self.yaml_path, 'r') as f:
                data = yaml.safe_load(f)

            if 'telegram' in data:
                self.config.telegram = TelegramSettings(**data['telegram'])
            if 'discord' in data:
                self.config.discord = DiscordSettings(**data['discord'])
            if 'weaviate' in data:
                self.config.weaviate = WeaviateSettings(**data['weaviate'])
            if 'pubsub' in data:
                self.config.pubsub = PubSubSettings(**data['pubsub'])
            if 'brain' in data:
                self.config.brain = BrainSettings(**data['brain'])

            # if 'plugins' in data:
            #     for name, settings in data['plugins'].items():
            #         self.config.plugins[name] = PluginSettings(plugin_name=name, plugin_config=settings)

            self.config.llm_type = data.get('llm_type', 'default')

            self.load_llm_settings()
            # self.config.validate()
            logger.info("[SettingsManager/load_settings] Settings loaded successfully.")

        except (FileNotFoundError, yaml.YAMLError) as e:
            logger.error(f"[SettingsManager/load_settings] Error loading settings from {self.yaml_path}: {e}")
            raise

        return self

    def load_single_module(self, component):
        if not self.yaml_path.exists():
            logger.error(f"[SettingsManager/load_single_module] Yaml({self.yaml_path}) path doesn't exists")
            raise RuntimeError(f"[SettingsManager/load_single_module] Configuration file '{self.yaml_path}' not found.")

        try:
            with open(self.yaml_path, 'r') as f:
                data = yaml.safe_load(f)

                component_loaders = {
                    'telegram': lambda: TelegramSettings(**data['telegram']) if 'telegram' in data else None,
                    'discord': lambda: DiscordSettings(**data['discord']) if 'discord' in data else None,
                    'weaviate': lambda: WeaviateSettings(**data['weaviate']) if 'weaviate' in data else None,
                    # 'plugins': lambda: {name: PluginSettings(plugin_name=name, plugin_config=settings)
                    #                     for name, settings in data['plugins'].items()} if 'plugins' in data else None,
                    'llm': lambda: self.load_llm_settings(data['llm_type']) if 'llm_type' in data else None
                }

                if component in component_loaders:
                    result = component_loaders[component]()
                    if result is None:
                        logger.warning(f"[SettingsManager/load_single_module] Component '{component}' not found in settings.")
                        return

                    logger.info(f"[SettingsManager/load_single_module] Component '{component}' loaded successfully.")
                    return result
                else:
                    logger.error(f"[SettingsManager/load_single_module] Invalid component: '{component}'. Cannot load settings.")
                    raise ValueError(f"Invalid component: '{component}'.")
        except (FileNotFoundError, yaml.YAMLError) as e:
            logger.error(f"[SettingsManager/load_single_module] Error loading settings from {self.yaml_path}: {e}")
            raise

    def save_settings(self):
        all_settings = {}
        if self.config.telegram:
            all_settings['telegram'] = self.config.telegram.dict()
        if self.config.discord:
            all_settings['discord'] = self.config.discord.dict()
        if self.config.weaviate:
            all_settings['weaviate'] = self.config.weaviate.dict()
        if self.config.pubsub:
            all_settings['pubsub'] = self.config.pubsub.dict()
        if self.config.brain:
            all_settings['brain'] = self.config.brain.dict()

        # all_settings['plugins'] = {name: asdict(plugin) for name, plugin in self.config.plugins.items()}
        all_settings['llm_type'] = self.config.llm_type

        try:
            logger.info(f"[SettingsManager/save_settings] Trying to save settings to {self.yaml_path}")
            # Ensure parent directory for the settings file exists
            ensure_directory_exists(self.yaml_path.parent)

            with open(self.yaml_path, 'w') as f:
                yaml.dump(all_settings, f, default_flow_style=False)

            llm_settings_path = LLM_SETTINGS_DIR / f"{self.config.llm_type}.yaml"
            self.config.llm.save_to_yaml(llm_settings_path)

            logger.info(f"[SettingsManager/save_settings] Settings saved successfully to {self.yaml_path}")
        except Exception as e:
            logger.error(f"Error saving settings to {self.yaml_path}: {e}")
            raise

    def load_llm_settings(self, llm_type: str = None):
        if not llm_type:
            llm_type = self.config.llm_type

        llm_settings_path = LLM_SETTINGS_DIR / f"{llm_type}.yaml"
        logger.info(f"[SettingsManager/load_llm_settings] Loading LLM settings from: {llm_settings_path}")
        if not llm_settings_path.exists():
            logger.error(f"[SettingsManager/load_llm_settings] LLM settings file '{self.config.llm_type}.yaml' not found in {LLM_SETTINGS_DIR}.")
            raise FileNotFoundError(f"LLM settings file '{self.config.llm_type}.yaml' not found.")
        try:
            self.config.llm = LLMSettings.load_from_yaml(llm_settings_path)
            #     self.config.llm.validate()
            logger.info(f"[SettingsManager/load_llm_settings] LLM settings for {self.config.llm_type} loaded successfully.")
        except (FileNotFoundError, yaml.YAMLError) as e:
            logger.error(f"[SettingsManager/load_llm_settings] Error loading LLM settings from {llm_settings_path}: {e}")
            raise
