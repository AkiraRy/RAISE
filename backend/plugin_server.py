import asyncio
import os
import signal
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse

from core import PluginService
from config import SettingsManager, get_logger


logger = get_logger(name="programming")

pm_config = SettingsManager().load_settings().config.plugin_manager
plugin_service = PluginService(pm_config)

# have some scheme for voice generation? E.g. in which order to use plugins


# noinspection PyUnusedLocal,PyShadowingNames
@asynccontextmanager
async def lifespan(app: FastAPI):
    global plugin_service
    plugin_service.load_all_plugins()
    logger.info(f"[plugin_server/lifespan] Server is running")
    yield
    names = list(plugin_service.plugin_manager.plugins.keys())
    for name in names:
        await plugin_service.unload_plugin(name)
    logger.info(f'[plugin_server/lifespan] Plugin manager stopped.')
    # unload/close plugins. sent stop message to docker?


app = FastAPI(lifespan=lifespan)


@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/docs")


@app.post("/unload_plugin")  # REFACTOR
async def unload_plugin(plugin_name: str):
    try:
        status, status_code, message = await plugin_service.unload_plugin(plugin_name)

        if not status:
            raise HTTPException(status_code=status_code, detail=message)

        return {"status": "success", "message": message}

    except Exception as e:
        logger.error(f"[plugin_server/unload_plugin] Error unloading {plugin_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to unload plugin: {str(e)}")


@app.post("/load_plugin")
async def load_plugin(plugin_name: str):
    status, status_code, message = plugin_service.load_plugin(plugin_name)

    if not status:
        raise HTTPException(status_code=status_code, detail=message) # WWWWWWWWWW

    return {"status": "success", "message": message}



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


@app.get("/is_plugin_loaded")
async def is_plugin_loaded(plugin_name: str):
    if not plugin_service.plugin_manager.get_plugin(plugin_name):
        logger.info(f"[plugin_server/is_plugin_loaded] Request info about {plugin_name} plugin, not loaded.")
        raise HTTPException(status_code=404, detail=f"Plugin {plugin_name} is not loaded.")

    logger.info(f"[plugin_server/is_plugin_loaded] Request info about {plugin_name} plugin loaded")
    return {"status": "success", "message": f"Plugin {plugin_name} is loaded."}


@app.get("/is_alive")
async def is_alive():
    try:
        logger.info(f"[plugin_server/shutdown] Plugin manager server, /is_alive get_request")
        return {"status": "success", "message": "Plugin manager is running"}
    except Exception as e:
        logger.error(f"[plugin_server/shutdown] Error checking Plugin manager status: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to check Plugin manager status")
