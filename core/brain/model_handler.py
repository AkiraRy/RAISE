import yaml
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Union

from jinja2 import Template
from llama_cpp import Llama

from . import LLMSettings, logger, MODEL_DIR, ResponseContent, Usage, PROMPT_TEMPLATES_DIR

DEFAULT_TEMPLATE = PROMPT_TEMPLATES_DIR / "llama-2.yaml"


class Model:
    def __init__(self, llm_settings: LLMSettings):
        self.llm_settings = llm_settings
        self.llm: Optional[Union['Llama', str]] = None
        self.prompt_template_name = self.llm_settings.chat_format
        self.prompt_template = None
        self._eos_token = None
        self._bos_token = None
        self.template_source = None

    def load_model(self):
        if self.llm_settings.local:
            logger.info(f'[Model/load_model] Proceeding to load model locally')
            return self._load_model_local()
        logger.info(f'[Model/load_model] Proceeding to load model remotely')
        return self._load_model_remote()

    def _load_model_local(self) -> bool:
        """ Returns true if loaded successfully"""

        logger.info(f"[Model/_load_model_local] Trying to load model locally using llama-cpp-python")
        model_path = MODEL_DIR / self.llm_settings.llm_model_file
        if not Path.exists(model_path):
            logger.error(f"[Model/_load_model_local] There is no model at {model_path}")
            raise FileNotFoundError(f"No model at {model_path}")

        try:
            self.llm = Llama(model_path=str(model_path),
                             n_gpu_layers=self.llm_settings.n_gpu_layers,
                             n_ctx=self.llm_settings.n_ctx,
                             n_batch=self.llm_settings.n_batch,
                             # chat_format=self.llm_settings.chat_format,
                             verbose=self.llm_settings.verbose)
            self.initialize_tokens()
            self.load_prompt_template()
            logger.info(f"[Model/_load_model_local] Template source: {self.template_source}")
        except Exception as e:
            logger.error(f"[Model/_load_model_local] Failed to load model at {model_path}, reason: {e}")
            return False
        else:
            logger.info(f"[Model/_load_model_local] Model {self.llm_settings.llm_model_name} loaded successfully")
            return True

    def _load_model_remote(self) -> bool:
        """TODO for future. ping endpoint to check if alive and add that endpoint to self.llm"""
        raise NotImplemented

    def _generate_remote(self, messages: List[dict]):
        raise NotImplemented

    # noinspection PyTypeChecker
    def _generate_local(self, messages: List[dict]):
        stat_time = datetime.now()
        formatted_prompt = self.format_prompt(messages)
        logger.debug(f"[Model/_generate_local] formatted_prompt {formatted_prompt}")
        logger.debug(f"[Model/_generate_local] settings {self.llm_settings}")
        response = self.llm.create_completion(
            prompt=formatted_prompt,
            temperature=self.llm_settings.temperature,
            top_p=self.llm_settings.top_p,
            top_k=self.llm_settings.top_k,
            min_p=self.llm_settings.min_p,
            typical_p=self.llm_settings.typical_p,
            stream=self.llm_settings.stream,
            stop=self.llm_settings.stop,
            max_tokens=self.llm_settings.max_tokens,
            repeat_penalty=self.llm_settings.repeat_penalty,
            seed=self.llm_settings.seed
        )
        end_time = datetime.now()
        generation_time = int((end_time - stat_time).total_seconds())

        # created = response['created']  # unix time
        choices = response['choices'][0]
        response_content = ResponseContent(
            content=choices['text'],
            finish_reason=choices['finish_reason']
        )
        usage = Usage(**response['usage'])
        logger.debug(f'[Model/_generate_local] generated this response {response_content.content}')
        logger.info(f"[Model/_generate_local] Generated message with {usage.completion_tokens} tokens in {generation_time}s ")

        return response_content, usage, generation_time

    def generate(self, messages: List[dict]):
        logger.debug(f"[Model/generate] prompt for generation {messages}")
        if self.llm_settings.local:
            logger.info(f'[Model/generate] Proceeding generate text locally')
            return self._generate_local(messages)
        logger.info(f'[Model/generate] Proceeding to generate text remotely')
        return self._generate_remote(messages)

    def _supports_system_role(self) -> bool:
        if not self.prompt_template:
            raise Exception("No template loaded.")

        unsupported_roles_pattern = "system"
        return unsupported_roles_pattern in self.prompt_template

    def format_prompt(self, messages: List[dict], add_generation_prompt=False):
        if not self.prompt_template:
            raise Exception('There is no template prompt.')

        if not self._supports_system_role():
            logger.info("[Model/format_prompt] System role unsupported; filtering 'system' messages.")
            messages = preprocess_messages(messages)

        template = Template(self.prompt_template)

        formatted_prompt = template.render(messages=messages,
                                           bos_token=self._bos_token,
                                           eos_token=self._eos_token,
                                           add_generation_prompt=add_generation_prompt,
                                           raise_exception=template_exception)
        return formatted_prompt

    def count_tokens(self, prompt: str) -> int:
        if self.llm_settings.local:
            return self._count_tokens_local(prompt)
        return self._count_tokens_remote(prompt)

    def _count_tokens_local(self, prompt: str) -> int:
        return len(self.llm.tokenize(prompt.encode('utf-8')))

    def _count_tokens_remote(self, prompt):
        raise NotImplemented

    def _load_template_from_file(self, path: Union[str, Path]):
        if not Path(path).exists():
            logger.debug(f"[Model/_load_template_from_file] Template file {path} does not exist.")
            return False

        try:
            with open(path, 'r') as file:
                yaml_data = yaml.safe_load(file)
                self.prompt_template = yaml_data['instruction_template']
        except Exception as e:
            logger.error(
                f"[Model/_load_template_from_file] Failed to load prompt_template at {path}, reason: {e}")
            return False
        else:
            logger.debug(
                f"[Model/_load_template_from_file] Prompt_template `{self.prompt_template}` loaded successfully")
            return True

    def _load_template_from_metadata(self):
        if not self.llm:
            logger.warning("[Model/_load_template_from_metadata] LLM instance not initialized.")
            return False

        metadata = getattr(self.llm, 'metadata', None)
        if not metadata or "tokenizer.chat_template" not in metadata:
            logger.debug("[Model/_load_template_from_metadata] No template found in model metadata.")
            return False

        self.prompt_template = metadata["tokenizer.chat_template"]
        self.template_source = "metadata"
        logger.info("[Model/_load_template_from_metadata] Successfully loaded template from metadata.")
        return True

    def load_prompt_template(self):
        logger.info(f"[Model/load_prompt_template] Trying to load prompt_template: {self.prompt_template_name}")
        prompt_template_path = PROMPT_TEMPLATES_DIR / f"{self.prompt_template_name}.yaml"

        if self._load_template_from_file(prompt_template_path):
            self.template_source = 'chat_format'
            return

        if self._load_template_from_metadata():
            return

        if self._load_default_template():
            return

        logger.error("[Model/load_prompt_template] Failed to load any prompt template.")
        raise RuntimeError("Unable to load a prompt template.")

    def initialize_tokens(self):
        eos_token_id = self.llm.token_eos()
        bos_token_id = self.llm.token_bos()
        try:
            self._eos_token = (self.llm._model.token_get_text(eos_token_id) if eos_token_id != -1 else "")
            self._bos_token = (self.llm._model.token_get_text(bos_token_id) if bos_token_id != -1 else "")
        except Exception as e:
            logger.debug(f"[Model/initialize_tokens] Got an unexpected error {e}")

    def _load_default_template(self):
        logger.info("[Model/_load_default_template] Loading default template.")
        if self._load_template_from_file(DEFAULT_TEMPLATE):
            self.template_source = "default"
            return True
        return False


def preprocess_messages(messages: List[dict]) -> List[dict]:
    return [message for message in messages if message['role'] != 'system']


def template_exception(message):
    logger.info(f'[template_exception] got unexpected error {message}')
