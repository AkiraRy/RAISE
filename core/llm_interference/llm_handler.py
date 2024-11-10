from pathlib import Path
from typing import Optional, Union
from config import logger, LLMSettings, MODEL_DIR
from llama_cpp import Llama


class Model:
    def __init__(self, llm_settings: LLMSettings):
        self.llm_settings = llm_settings
        self.llm: Optional[Union[Llama, str]] = None

    def load_model(self):
        if self.llm_settings.local:
            self.load_model_local()
            return
        self.load_model_remote()

    def load_model_local(self) -> bool:
        """ Returns true if loaded successfully"""

        logger.info(f"[Model/load_model_local] Trying to load model locally using llama-cpp-python")
        model_path = MODEL_DIR / self.llm_settings.llm_model_file
        if not Path.exists(model_path):
            logger.error(f"[Model/load_model_local] There is no model at {model_path}")
            raise FileNotFoundError(f"No model at {model_path}")

        try:
            self.llm = Llama(model_path=str(model_path),
                             n_gpu_layers=self.llm_settings.n_gpu_layers,
                             seed=self.llm_settings.seed,
                             n_ctx=self.llm_settings.n_ctx,
                             n_batch=self.llm_settings.n_batch,
                             chat_format=self.llm_settings.chat_format,
                             verbose=self.llm_settings.verbose)

        except Exception as e:
            logger.error(f"[Model/load_model_local] Failed to load model at {model_path}, reason: {e}")
            return False
        else:
            logger.info(f"[Model/load_model_local] Model {self.llm_settings.llm_model_name} loaded successfully")

    def load_model_remote(self):
        """TODO for future. ping endpoint to check if alive and add that endpoint to self.llm"""
        raise NotImplemented
