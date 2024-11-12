import huggingface_hub
import os
from . import SettingsManager, MODEL_DIR, LLM_SETTINGS_DIR


def model_download(llm_settings: LLM_SETTINGS_DIR):
    HF_TOKEN = os.getenv('HF_TOKEN')
    model_path = huggingface_hub.hf_hub_download(
        llm_settings.model_name,
        filename=llm_settings.model_file,
        local_dir=MODEL_DIR,
        token=HF_TOKEN
    )

    print("My model path:", model_path)


if __name__ == '__main__':
    settings_manager = SettingsManager().load_settings()
    llm_settings = settings_manager.config.llm
    model_download(llm_settings)
