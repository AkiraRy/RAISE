import asyncio
import os
import signal
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from core import Brain, Model, MemoryChain, WeaviateHelper
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
    global brain
    logger.info(f'[brain_server/lifespan] Starting brain and application')
    await brain.start()
    yield
    logger.info(f'[brain_server/lifespan] Stopping brain and shutting down the application')
    await brain.close()

# Initialize FastAPI app
app = FastAPI(lifespan=lifespan)

#
# class AddMemoriesRequest(BaseModel):
#     memory_chain: list[dict]
#
#
# class DeleteMemoryRequest(BaseModel):
#     uuid: str
#
#
# # noinspection PyAsyncCall
# @app.post("/shutdown")
# async def shutdown_server():
#     try:
#         logger.info("[weaviate_server/shutdown] Received shutdown request. Shutting down the server.")
#         await weaviate_db.close()
#
#         async def shutdown_task():
#             await asyncio.sleep(1)  # Give time for the response to complete
#             os.kill(os.getpid(), signal.SIGTERM)
#
#         asyncio.create_task(shutdown_task())
#         return {"status": "success", "message": "Server is shutting down"}
#     except Exception as e:
#         logger.error(f"Error during shutdown: {e}")
#         raise HTTPException(status_code=500, detail=f"Failed to shutdown server: {str(e)}")
#
#
# @app.get("/is_alive")
# async def is_alive():
#     try:
#         logger.info(f"[weaviate_server/is_alive] get request. checking if weaviate is still alive.")
#         is_live = await weaviate_db.is_alive()
#         if is_live:
#             logger.info(f"[weaviate_server/is_alive] get request completed. weaviate is still alive.")
#             return {"status": "success", "message": "Weaviate is alive and connected"}
#
#         logger.error(f"[weaviate_server/is_alive] get request completed. weaviate is not alive.")
#         raise HTTPException(status_code=503, detail="Weaviate is not reachable")
#     except Exception as e:
#         logger.error(f"Error checking Weaviate status: {str(e)}")
#         raise HTTPException(status_code=500, detail="Failed to check Weaviate status")
#
#
# @app.post("/add_memories")
# async def add_memories(request: AddMemoriesRequest):
#     logger.info(f"[weaviate_server/add_memories] post request. Trying to add memories.")
#     memory_chain = MemoryChain()
#     for memory in request.memory_chain:
#         memory_chain.add_object(
#             from_name=memory["from_name"],
#             message=memory["message"],
#             time=memory["time"],
#         )
#     success = await weaviate_db.add_memories(memory_chain)
#     if not success:
#         logger.waerning(f"[weaviate_server/add_memories] post request. Couldn't add memories successfully.")
#         raise HTTPException(status_code=500, detail="Failed to add memories")
#
#     logger.info(f"[weaviate_server/add_memories] post request. Successfully added memories.")
#     return {"status": "success", "message": "Memories added successfully"}
