import asyncio
import os
import signal
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse

from core import PluginManager
from config import SettingsManager, get_logger

logger = get_logger(name="programming")

pm_config = SettingsManager().load_settings().config.plugin_manager
plugin_manager = PluginManager(pm_config)


# noinspection PyUnusedLocal,PyShadowingNames
@asynccontextmanager
async def lifespan(app: FastAPI):
    global plugin_manager
    load_all_plugins()
    logger.info(f"[plugin_server/lifespan] Server is running")
    yield
    logger.info(f'[plugin_server/lifespan] Plugin manager stopped.')
    # unload/close plugins. sent stop message to docker?


app = FastAPI(lifespan=lifespan)


@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/docs")


def unload_all_plugin_routes(plugin_name):
    for i, r in enumerate(app.router.routes):
        if r.path.startswith(f"/{plugin_name}"):
            logger.info(f"[unload_all_plugin_routes] Unloading: {r}, plugin: {plugin_name}")


def load_all_plugins():
    if pm_config.load_all_plugins:
        for plugin_name, plugin in plugin_manager.load_plugins().items():
            logger.info(f'[plugin_server/load_all_plugins] Loading plugins.')
            app.include_router(plugin.get_route(), prefix=f"/{plugin_name}")


@app.post("/unload_plugin")
async def unload_plugin(plugin_name: str):
    try:
        if plugin_name not in plugin_manager.plugins:
            raise HTTPException(status_code=404, detail=f"Plugin {plugin_name} is not loaded.")

        unload_all_plugin_routes(plugin_name)

        if not plugin_manager.unload_plugin(plugin_name):
            raise HTTPException(status_code=500, detail=f"Couldn't unload {plugin_name} plugin.")

        return {"status": "success", "message": f"Plugin {plugin_name} unloaded."}

    except Exception as e:
        logger.error(f"[plugin_server/unload_plugin] Error unloading {plugin_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to unload plugin: {str(e)}")


@app.post("/load_plugin")
async def load_plugin(plugin_name: str):
    try:
        if plugin_name in plugin_manager.plugins:
            raise HTTPException(status_code=404, detail=f"Plugin {plugin_name} is already loaded.")

        if not plugin_manager.load_plugin(plugin_name):
            raise HTTPException(status_code=404, detail=f"Plugin {plugin_name} couldnt be loaded.")

        # Since i explicitly check if that plugin has been loaded in an if statement higher, than i dont need to check if returned values i non None?
        plugin = plugin_manager.get_plugin(plugin_name)
        try:
            app.include_router(plugin.get_route(), prefix=f"/{plugin_name}")
        except:
            logger.warning(f"[plugin_server/load_plugin] couldnt add router, most likely this plugin was loaded before"
                           f" restart this server to see changes")

        return {"status": "success", "message": f"Plugin {plugin_name} loaded."}

    except Exception as e:
        logger.error(f"[plugin_server/load_plugin] Error loading {plugin_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to load plugin: {str(e)}")


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
