import huggingface_hub
import os
from . import SettingsManager, MODEL_DIR, LLMSettings


def model_download(llm_settings: LLMSettings):
    HF_TOKEN = os.getenv('HF_TOKEN')
    repo_files = huggingface_hub.list_repo_files(llm_settings.llm_model_name, token=HF_TOKEN)

    target_files = [file for file in repo_files if file.startswith(llm_settings.llm_model_file)]

    if not target_files:
        print(f"No files found for prefix {llm_settings.llm_model_file} in {llm_settings.llm_model_name}.")
        return

    print(f"Found the following files for {llm_settings.llm_model_file}: {target_files}")

    for file in target_files:
        print(f"Downloading {file}...")
        huggingface_hub.hf_hub_download(
            repo_id=llm_settings.llm_model_name,
            filename=file,
            local_dir=MODEL_DIR,
            token=HF_TOKEN
        )
    print("Download complete.")


if __name__ == '__main__':
    settings_manager = SettingsManager().load_settings()
    llm_settings = settings_manager.config.llm
    model_download(llm_settings)
