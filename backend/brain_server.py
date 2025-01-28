import asyncio
import os
import signal
from contextlib import asynccontextmanager
from utils import Message_server
from fastapi import FastAPI, HTTPException
from core import Brain, Model, WeaviateHelper
from config import SettingsManager, get_logger
from fastapi.responses import RedirectResponse

logger = get_logger("brain_logger")

settings_manager = SettingsManager().load_settings()
weaviate_base_url = 'http://127.0.0.1:8000'
weaviate_db = WeaviateHelper(weaviate_base_url)

model = Model(settings_manager.config.llm)
brain = Brain(
            memory_manager=weaviate_db,
            model=model,
            config=settings_manager.config.brain
)


# noinspection PyUnusedLocal,PyShadowingNames
@asynccontextmanager
async def lifespan(app: FastAPI):
    # global brain
    logger.info(f'[brain_server/lifespan] Starting brain and application')
    await brain.start()
    yield
    logger.info(f'[brain_server/lifespan] Stopping brain and shutting down the application')
    brain.close()

# Initialize FastAPI app
app = FastAPI(lifespan=lifespan)


@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/docs")


@app.post("/generate")
async def generate_response(message: Message_server):
    global brain
    response_message = await brain.process_message(message=message)
    # add preprocessing, egg if failed return status failed
    return {"status": "success", "message": response_message}

# TODO
# add endpoints for voice/photo interference


# noinspection PyAsyncCall
@app.post("/shutdown")
async def shutdown_server():
    try:
        logger.info("[brain_server/shutdown] Received shutdown request. Shutting down the brain.")
        await brain.close()

        async def shutdown_task():
            await asyncio.sleep(1)  # Give time for the response to complete
            os.kill(os.getpid(), signal.SIGTERM)

        asyncio.create_task(shutdown_task())
        return {"status": "success", "message": "Server is shutting down"}
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to shutdown server: {str(e)}")
