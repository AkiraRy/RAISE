from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from core import Weaviate, MemoryChain
from config import SettingsManager, logger


settings_manager = SettingsManager().load_settings()
weaviate_db = Weaviate(settings_manager.config.weaviate)


# noinspection PyUnusedLocal,PyShadowingNames
@asynccontextmanager
async def lifespan(app: FastAPI):
    global weaviate_db
    logger.info(f'[weaviate_server/lifespan] Connecting to weaviate db and starting the application')
    await weaviate_db.connect()
    yield
    logger.info(f'[weaviate_server/lifespan] Closing connection to weaviate db and shutting down the application')
    await weaviate_db.close()

# Initialize FastAPI app
app = FastAPI(lifespan=lifespan)


class AddMemoriesRequest(BaseModel):
    memory_chain: list[dict]


class DeleteMemoryRequest(BaseModel):
    uuid: str


@app.get("/is_alive")
async def is_alive():
    try:
        logger.info(f"[weaviate_server/is_alive] get request. checking if weaviate is still alive.")
        is_live = await weaviate_db.is_alive()
        if is_live:
            logger.info(f"[weaviate_server/is_alive] get request completed. weaviate is still alive.")
            return {"status": "success", "message": "Weaviate is alive and connected"}

        logger.error(f"[weaviate_server/is_alive] get request completed. weaviate is not alive.")
        raise HTTPException(status_code=503, detail="Weaviate is not reachable")
    except Exception as e:
        logger.error(f"Error checking Weaviate status: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to check Weaviate status")


@app.delete("/delete_memory")
async def delete_memory(request: DeleteMemoryRequest):
    """
    Deletes a memory object from the database using its UUID.
    """
    try:
        logger.info(f"[weaviate_server/delete_memory] delete request. trying to delete memory object with uuid {request.uuid}")
        success = await weaviate_db.delete_by_uuid(request.uuid)
        if not success:
            logger.info(
                f"[weaviate_server/delete_memory] delete request. Couldn't memory object with uuid {request.uuid}")
            raise HTTPException(status_code=404, detail="Memory with the specified UUID not found")
        logger.info(
            f"[weaviate_server/delete_memory] delete request. Successfully deleted memory object with uuid {request.uuid}")
        return {"status": "success", "message": f"Memory with UUID {request.uuid} deleted successfully"}
    except Exception as e:
        logger.error(
            f"[weaviate_server/delete_memory] delete request. got an unexpected error {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete memory: {str(e)}")


@app.post("/add_memories")
async def add_memories(request: AddMemoriesRequest):
    logger.info(f"[weaviate_server/add_memories] post request. Trying to add memories.")
    memory_chain = MemoryChain()
    for memory in request.memory_chain:
        memory_chain.add_object(
            from_name=memory["from_name"],
            message=memory["message"],
            time=memory["time"],
        )
    success = await weaviate_db.add_memories(memory_chain)
    if not success:
        logger.waerning(f"[weaviate_server/add_memories] post request. Couldn't add memories successfully.")
        raise HTTPException(status_code=500, detail="Failed to add memories")

    logger.info(f"[weaviate_server/add_memories] post request. Successfully added memories.")
    return {"status": "success", "message": "Memories added successfully"}


@app.get("/get_context")
async def get_context(query: str):
    logger.info(f"[weaviate_server/add_memories] get request. Requesting context for user query {query}")
    memory_chain = await weaviate_db.get_context(query)
    if not memory_chain:
        logger.info(f"[weaviate_server/add_memories] get request. Received no context.")
        return {"context": []}  # No similar messages found
    logger.info(f"[weaviate_server/add_memories] get request. Successfully received context.")
    return {
        "context": [
            {
                "from_name": memory.from_name,
                "message": memory.message,
                "time": memory.time,
                "distance": memory.distance,
                "certainty": memory.certainty,
                "score": memory.score,
            }
            for memory in memory_chain.memories
        ]
    }


@app.get("/get_chat_memory")
async def get_chat_memory(limit: int = 20):
    logger.info(f"[weaviate_server/add_memories] get request. Requesting last chat memories with limit of {limit} messages")
    chat_memory = await weaviate_db.get_chat_memory(limit)
    if not chat_memory:
        logger.info(f"[weaviate_server/add_memories] get request. There were no memories in db")
        return {"chat_history": []}
    logger.info(f"[weaviate_server/add_memories] get request. Successfully retrieved {limit} messages from db")
    return {
        "chat_history": [
            {
                "from_name": memory.from_name,
                "message": memory.message,
                "time": memory.time,
            }
            for memory in chat_memory.memories
        ]
    }
