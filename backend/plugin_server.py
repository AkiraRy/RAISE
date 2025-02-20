import asyncio
import os
import signal
from contextlib import asynccontextmanager
import io

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import RedirectResponse

from core import PluginManager
from config import SettingsManager, get_logger

logger = get_logger() # change later to plugin manager logger

settings_manager = SettingsManager().load_settings()
plugin_manager = PluginManager()


# noinspection PyUnusedLocal,PyShadowingNames
@asynccontextmanager
async def lifespan(app: FastAPI):
    global plugin_manager
    logger.info(f'[plugin_server/lifespan] Loading plugins.')
    for plugin_name, plugin in plugin_manager.load_plugins().items():
        app.include_router(plugin.get_route(), prefix=f"/{plugin_name}")

    logger.info(f"[plugin_server/lifespan] Server is running")
    yield
    logger.info(f'[plugin_server/lifespan] Plugin manager stopped.')
    # unload/close plugins. sent stop message to docker?

app = FastAPI(lifespan=lifespan)


@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/docs")


# noinspection PyAsyncCall
@app.post("/shutdown")
async def shutdown_server():
    try:
        logger.info("[plugin_server/shutdown] Received shutdown request. Shutting down the server.")

        async def shutdown_task():
            await asyncio.sleep(1)  # Give time for the response to complete
            os.kill(os.getpid(), signal.SIGTERM)

        asyncio.create_task(shutdown_task())
        return {"status": "success", "message": "Server is shutting down"}
    except Exception as e:
        logger.error(f"[plugin_server/shutdown] Error during shutdown: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to shutdown server: {str(e)}")


@app.get("/is_alive")
async def is_alive():
    try:
        logger.info(f"[plugin_server/shutdown] Plugin manager server, /is_alive get_request")
        return {"status": "success", "message": "Plugin manager is running"}
    except Exception as e:
        logger.error(f"[plugin_server/shutdown] Error checking Plugin manager status: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to check Plugin manager status")
