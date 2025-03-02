import os
import signal
import subprocess
import sys
from config import logger
from translate import Translator
import re


def detect_japanese(text):
    jp_pattern = r'[\u3041-\u3096\u30A0-\u30FF\u3400-\u4DB5\u4E00-\u9FCB\uF900-\uFA6A]'

    return bool(re.search(jp_pattern, text))


def translate_text(text, target_language):
    provider = "google"
    translator = Translator(provider=provider, from_lang="ja", to_lang=target_language)
    translation = translator.translate(text)
    return translation


def start_server_handler(server_module: str, port: int):
    try:
        process = subprocess.Popen(
            [
                "uvicorn",
                server_module,
                "--host", "127.0.0.1",
                "--port", str(port)
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        for line in process.stdout:
            logger.debug(line.strip())
            if "running" in line:  # Will block everything until server starts, shouldnt be an issue?
                logger.info("Server started successfully.")
                return process, process.pid

        _, stderr = process.communicate(timeout=10)
        logger.error(f"Error during startup: {stderr}")
        sys.exit(1)

    except Exception as e:
        logger.error(f"Error starting uvicorn server: {e}")
        sys.exit(1)


def terminate_process(process, process_name="", timeout=10):
    if process.poll() is None:  # Check if the process is still running
        try:
            os.kill(process.pid, signal.SIGINT)
            process.wait(timeout=timeout)
            logger.info(f"Gracefully terminated {process_name}.")
        except Exception as e:
            logger.error(f"Failed to terminate {process_name} gracefully: {e}. Forcing termination.")
            process.terminate()
            process.wait()
            logger.info(f"Forcefully terminated {process_name}.")
    else:
        logger.info(f"Process {process_name} was not running.")
