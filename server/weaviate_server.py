from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from core import Weaviate, MemoryChain
from config import SettingsManager, logger


# Create a Weaviate instance
settings_manager = SettingsManager().load_settings()
weaviate_db = Weaviate(settings_manager.config.weaviate)


@asynccontextmanager
async def lifespan(app: FastAPI):
    global weaviate_db
    await weaviate_db.connect()
    yield
    await weaviate_db.close()

# Initialize FastAPI app
app = FastAPI(lifespan=lifespan)


# Define models for request/response
class AddMemoriesRequest(BaseModel):
    memory_chain: list[dict]  # List of memories (each memory as a dict with from_name, message, time)


class DeleteMemoryRequest(BaseModel):
    uuid: str  # UUID string of the memory object to delete


class GetContextRequest(BaseModel):
    query: str


class ChatMemoryResponse(BaseModel):
    chat_history: list[dict]  # List of chat memories


@app.delete("/delete_memory")
async def delete_memory(request: DeleteMemoryRequest):
    """
    Deletes a memory object from the database using its UUID.
    """
    try:
        success = await weaviate_db.delete_by_uuid(request.uuid)
        if not success:
            raise HTTPException(status_code=404, detail="Memory with the specified UUID not found")
        return {"status": "success", "message": f"Memory with UUID {request.uuid} deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete memory: {str(e)}")


# Endpoint: Add Memories
@app.post("/add_memories")
async def add_memories(request: AddMemoriesRequest):
    memory_chain = MemoryChain()
    for memory in request.memory_chain:
        memory_chain.add_object(
            from_name=memory["from_name"],
            message=memory["message"],
            time=memory["time"],
        )
    success = await weaviate_db.add_memories(memory_chain)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to add memories")
    return {"status": "success", "message": "Memories added successfully"}



# Endpoint: Get Context
@app.post("/get_context")
async def get_context(request: GetContextRequest):
    memory_chain = await weaviate_db.get_context(request.query)
    if not memory_chain:
        return {"context": []}  # No similar messages found
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


# Endpoint: Get Chat History
@app.get("/get_chat_memory")
async def get_chat_memory(limit: int = 20):
    chat_memory = await weaviate_db.get_chat_memory(limit)
    if not chat_memory:
        return {"chat_history": []}  # No chat history found
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
