import subprocess
import sys
from config import logger


def start_server_handler():
    try:
        process = subprocess.Popen(
            ["python", "-m", "server_handler"],
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
        logger.error(f"Error starting server_handler: {e}")
        sys.exit(1)


def terminate_process(process, process_name=""):
    if process.poll() is None:
        process.terminate()
        logger.info(f"Terminated {process_name}.")
    else:
        logger.info(f"Process {process_name} was not running.")