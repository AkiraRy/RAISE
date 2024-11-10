from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Union, List, Literal

from config import logger, LLMSettings, MODEL_DIR
from llama_cpp import Llama, ChatCompletionRequestMessage


@dataclass
class ResponseContent:
    message: dict[str, str]
    content: str
    finish_reason: Optional[Literal["stop", "length"]]


@dataclass
class Usage:
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class Model:
    def __init__(self, llm_settings: LLMSettings):
        self.llm_settings = llm_settings
        self.llm: Optional[Union[Llama, str]] = None

    def load_model(self):
        if self.llm_settings.local:
            return self._load_model_local()
        return self._load_model_remote()

    def _load_model_local(self) -> bool:
        """ Returns true if loaded successfully"""

        logger.info(f"[Model/load_model_local] Trying to load model locally using llama-cpp-python")
        model_path = MODEL_DIR / self.llm_settings.llm_model_file
        if not Path.exists(model_path):
            logger.error(f"[Model/load_model_local] There is no model at {model_path}")
            raise FileNotFoundError(f"No model at {model_path}")

        try:
            self.llm = Llama(model_path=str(model_path),
                             n_gpu_layers=self.llm_settings.n_gpu_layers,
                             n_ctx=self.llm_settings.n_ctx,
                             n_batch=self.llm_settings.n_batch,
                             chat_format=self.llm_settings.chat_format,
                             verbose=self.llm_settings.verbose)
        except Exception as e:
            logger.error(f"[Model/load_model_local] Failed to load model at {model_path}, reason: {e}")
            return False
        else:
            logger.info(f"[Model/load_model_local] Model {self.llm_settings.llm_model_name} loaded successfully")
            return True

    def _load_model_remote(self) -> bool:
        """TODO for future. ping endpoint to check if alive and add that endpoint to self.llm"""
        raise NotImplemented

    def generate(self, messages: List[ChatCompletionRequestMessage]):
        response = self.llm.create_chat_completion(
            messages=messages,
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

        created = response['created']  # unix time
        choices = response['choices'][0]  #
        response_content = ResponseContent(
            message=choices['message'],
            content=choices['message']['content'],
            finish_reason=choices['finish_reason']
        )

        usage = Usage(**response['usage'])

        return response_content, usage, created

    def count_tokens(self, prompt: str) -> int:
        if self.llm_settings.local:
            return self._count_tokens_local(prompt)
        return self._count_tokens_remote(prompt)

    def _count_tokens_local(self, prompt: str) -> int:
        return len(self.llm.tokenize(prompt.encode('utf-8')))

    def _count_tokens_remote(self, prompt):
        raise NotImplemented


    # def format(self): maybe use in future?
    #     from llama_cpp.llama_chat_format import format_mistral_instruct, format_chatml
