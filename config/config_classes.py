from dataclasses import dataclass, asdict, field
from abc import ABC, abstractmethod
from typing import Dict, Optional
from pathlib import Path
import yaml
from .settings import DEFAULT_SETTINGS, ensure_directory_exists, logger, LLM_SETTINGS
from pydantic import BaseModel


class BaseSettings(BaseModel):
    def load_from_yaml(self, filepath: str):
        if Path(filepath).exists():
            with open(filepath, 'r') as f:
                data = yaml.safe_load(f)
                for key, value in data.items():
                    setattr(self, key, value)

    def save_to_yaml(self, filepath: str):
        with open(filepath, 'w') as f:
            yaml.dump(self.dict(), f)

    def __str__(self):
        fields_str = ', '.join(f"{key}={value!r}" for key, value in self.dict().items())
        return f"{self.__class__.__name__}({fields_str})"


class TelegramSettings(BaseSettings):
    # def validate(self):
    #     errors = []
    #     if not self.bot_username:
    #         errors.append("Bot username is required.")
    #     if self.creator_id <= 0:
    #         errors.append("Creator ID must be a positive integer.")
    #     if errors:
    #         raise ValueError(f"Validation errors in TelegramSettings: {', '.join(errors)}")

    bot_username: str = ""
    bot_nickname: str = ""  # used for storing in the vectordb
    creator_id: int = -1  # whitelist
    creator_username: str = ""  # used for storing in the vectordb
    sticker_path: str = ""


class WeaviateSettings(BaseSettings):
    # def validate(self):
    #     errors = []
    #     if not self.class_name:
    #         errors.append("Class name is required.")
    #     if not (0 < self.http_port < 65536):
    #         errors.append("Port must be a valid number between 1 and 65535.")
    #     if errors:
    #         raise ValueError(f"Validation errors in WeaviateSettings: {', '.join(errors)}")

    author_name: str
    class_name: str = "MemoryK"  # for testing i will use an already created class
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


class DiscordSettings(BaseSettings):
    # def validate(self):
    #     raise NotImplemented

    bot_name: str = ""


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
    seed: int | None = None
    stop: str | list[str] | None = field(default_factory=list)

    # def validate(self):
    #     pass


class Config(BaseSettings):
    telegram: Optional[TelegramSettings] = None
    discord: Optional[DiscordSettings] = None
    weaviate: Optional[WeaviateSettings] = None
    # plugins: Dict[str, PluginSettings] = field(default_factory=dict)
    llm: Optional[LLMSettings] = None
    llm_type: str = None
    persona: str = "default_persona"

    # def validate(self):
    #     if not self.weaviate:
    #         raise ValueError("Weaviate must exists")
    #     if not (self.telegram or self.discord):
    #         raise ValueError("At least one of Telegram, Discord, or Weaviate settings must be provided.")
    #
    #     if self.telegram:
    #         self.telegram.validate()
    #     if self.discord:
    #         self.discord.validate()
    #     if self.weaviate:
    #         self.weaviate.validate()


class SettingsManager:
    def __init__(self, config: Config = Config(),  yaml_path: Path = DEFAULT_SETTINGS):
        self.config: Config = config
        self.yaml_path = Path(yaml_path)
        ensure_directory_exists(self.yaml_path.parent)

    def load_settings(self):
        if self.yaml_path.exists():
            try:
                with open(self.yaml_path, 'r') as f:
                    data = yaml.safe_load(f)

                if 'telegram' in data:
                    self.config.telegram = TelegramSettings(**data['telegram'])
                if 'discord' in data:
                    self.config.discord = DiscordSettings(**data['discord'])
                if 'weaviate' in data:
                    self.config.weaviate = WeaviateSettings(**data['weaviate'])
                # if 'plugins' in data:
                #     for name, settings in data['plugins'].items():
                #         self.config.plugins[name] = PluginSettings(plugin_name=name, plugin_config=settings)

                self.config.llm_type = data.get('llm_type', 'default')
                self.config.persona = data.get("persona", "default_persona")
                self.load_llm_settings()
                # self.config.validate()
                logger.info("Settings loaded successfully.")

            except (FileNotFoundError, yaml.YAMLError) as e:
                logger.error(f"Error loading settings from {self.yaml_path}: {e}")
                raise

        return self

    def load_single_module(self, component):
        if not self.yaml_path.exists():
            logger.error(f"[SettingsManager/load_single_module] Yaml({self.yaml_path}) path doesn't exists")

        try:
            with open(self.yaml_path, 'r') as f:
                data = yaml.safe_load(f)

                component_loaders = {
                    'telegram': lambda: TelegramSettings(**data['telegram']) if 'telegram' in data else None,
                    'discord': lambda: DiscordSettings(**data['discord']) if 'discord' in data else None,
                    'weaviate': lambda: WeaviateSettings(**data['weaviate']) if 'weaviate' in data else None,
                    # 'plugins': lambda: {name: PluginSettings(plugin_name=name, plugin_config=settings)
                    #                     for name, settings in data['plugins'].items()} if 'plugins' in data else None,
                    'llm': lambda: self.load_llm_settings() if 'llm_type' in data else None
                }

                if component in component_loaders:
                    result = component_loaders[component]()
                    if result is None:
                        logger.warning(f"Component '{component}' not found in settings.")
                        return

                    logger.info(f"Component '{component}' loaded successfully.")
                    return result
                else:
                    logger.error(f"Invalid component: '{component}'. Cannot load settings.")
                    raise ValueError(f"Invalid component: '{component}'.")
        except (FileNotFoundError, yaml.YAMLError) as e:
            logger.error(f"Error loading settings from {self.yaml_path}: {e}")
            raise

    def save_settings(self):
        all_settings = {}
        if self.config.telegram:
            all_settings['telegram'] = asdict(self.config.telegram)
        if self.config.discord:
            all_settings['discord'] = asdict(self.config.discord)
        if self.config.weaviate:
            all_settings['weaviate'] = asdict(self.config.weaviate)

        all_settings['plugins'] = {name: asdict(plugin) for name, plugin in self.config.plugins.items()}
        all_settings['llm_type'] = self.config.llm_type

        try:
            # Ensure parent directory for the settings file exists
            ensure_directory_exists(self.yaml_path.parent)

            with open(self.yaml_path, 'w') as f:
                yaml.dump(all_settings, f, default_flow_style=False)
            logger.info("Settings saved successfully.")
        except Exception as e:
            logger.error(f"Error saving settings to {self.yaml_path}: {e}")
            raise

    def load_llm_settings(self):
        llm_settings_path = LLM_SETTINGS / f"{self.config.llm_type}.yaml"
        logger.debug(f"Loading LLM settings from: {llm_settings_path}")
        if not llm_settings_path.exists():
            logger.error(f"LLM settings file '{self.config.llm_type}.yaml' not found in {LLM_SETTINGS}.")
            raise FileNotFoundError(f"LLM settings file '{self.config.llm_type}.yaml' not found.")
        try:
            with open(llm_settings_path, 'r') as f:
                llm_data = yaml.safe_load(f)
                self.config.llm = LLMSettings(**llm_data)
                # self.config.llm.validate()
                logger.info(f"LLM settings for {self.config.llm_type} loaded successfully.")
        except (FileNotFoundError, yaml.YAMLError) as e:
            logger.error(f"Error loading LLM settings from {llm_settings_path}: {e}")
            raise
