import uvicorn
# start here each server using subprocesses
if __name__ == '__main__':
    # Main entry point to run the server
    # uvicorn.run("server.weaviate_server:app", host="127.0.0.1", port=8000, reload=True)
    uvicorn.run("server.weaviate_server:app", host="127.0.0.1", port=8000)
