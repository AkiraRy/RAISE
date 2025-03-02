import asyncio
import io
import os
import signal
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import RedirectResponse, StreamingResponse

from core import PluginService
from config import SettingsManager, get_logger
from utils import STTPlugin, TTSPlugin

logger = get_logger(name="programming")

pm_config = SettingsManager().load_settings().config.plugin_manager
plugin_service = PluginService(pm_config)


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
    # sent stop message to docker?


app = FastAPI(lifespan=lifespan)


@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/docs")


@app.post("/tts")
async def generate_audio(text, name: str = "voicevox"):
    tts_plugins: list = plugin_service.get_tts_plugins()
    if not tts_plugins:
        return HTTPException(status_code=500, detail=f"No tts plugin is loaded")

    logger.debug(f"[plugin_server/post(/tts).generate_audio] Received text: {text}")

    # looks for the plugin specified in name, defaults to first position
    matched_plugin: TTSPlugin = next((plugin for plugin_name, plugin in tts_plugins if plugin_name == name),
                                     tts_plugins[0][1] if tts_plugins else None)
    logger.debug(f"[plugin_server/post(/tts).generate_audio] Using {matched_plugin.__name__} plugin")

    # preprocess text, before generating voice, or handle that before sending a request?
    voice_data = await matched_plugin.tts(text)
    if not voice_data:
        logger.error(
            f"[plugin_server/post(/tts).generate_audio] Failed to generate speach using {matched_plugin.__name__} plugin, for '{text}'")
        return HTTPException(status_code=500, detail="No audio data was generated")

    audio_buffer = io.BytesIO(voice_data)
    audio_buffer.seek(0)
    logger.info(
        f"[plugin_server/post(/tts).generate_audio] Successfully generate speach using {matched_plugin.__name__} plugin, for '{text}'")
    return StreamingResponse(audio_buffer, media_type="audio/wav")


@app.post("/transcribe")  # rename to stt?
async def transcribe_file(file: UploadFile = File(...), name: str = "whisper"):
    stt_plugins: list = plugin_service.get_stt_plugins()
    if not stt_plugins:
        return HTTPException(status_code=500, detail=f"No stt plugin is loaded")

    logger.debug(f"[plugin_server/post(/transcribe).transcribe_file] Received file: {file.filename}")

    # looks for the plugin specified in name, defaults to first position
    matched_plugin: STTPlugin = next((plugin for plugin_name, plugin in stt_plugins if plugin_name == name),
                                     stt_plugins[0][1] if stt_plugins else None)
    logger.debug(f"[plugin_server/post(/transcribe).transcribe_file] Using {matched_plugin.__name__} plugin")

    audio_data = await file.read()
    transcription = await matched_plugin.stt(io.BytesIO(audio_data))
    logger.info(
        f"[plugin_server/post(/transcribe).transcribe_file] Successfully transcribed file '{file.filename}' using {matched_plugin.__name__} plugin.")

    return {"transcription": transcription}


@app.post("/unload_plugin")
async def unload_plugin(plugin_name: str):
    try:
        status, status_code, message = await plugin_service.unload_plugin(plugin_name)

        if not status:
            logger.error(f"[plugin_server/post/unload_plugin] Failed to unload {plugin_name}")
            raise HTTPException(status_code=status_code, detail=message)
        logger.info(f"[plugin_server/post/unload_plugin] Successfully unloaded {plugin_name}")
        return {"status": "success", "message": message}
    except Exception as e:
        logger.error(f"[plugin_server/unload_plugin] Error unloading {plugin_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to unload plugin: {str(e)}")


@app.post("/load_plugin")
async def load_plugin(plugin_name: str):
    status, status_code, message = plugin_service.load_plugin(plugin_name)

    if not status:
        logger.error(f"[plugin_server/post/load_plugin] Failed to load {plugin_name}")
        raise HTTPException(status_code=status_code, detail=message)

    logger.info(f"[plugin_server/post/load_plugin] Successfully loaded {plugin_name}")
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
