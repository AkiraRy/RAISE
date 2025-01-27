import asyncio
import os
import signal
from contextlib import asynccontextmanager
from utils import Message_server
from fastapi import FastAPI, HTTPException
from core import Brain, Model, WeaviateHelper
from config import SettingsManager, logger


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


@app.post("/messages")
async def create_message(message: Message_server):
    global brain
    # Validate the message
    if not message.is_valid():
        raise HTTPException(
            status_code=400,
            detail="At least one of text_content, photo_content, or voice_content must be provided."
        )
    # Simulate saving the message to the database (in-memory for now)
    response_message = await brain.process_message(message=message)
    return {"status": "success", "message": response_message}


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
