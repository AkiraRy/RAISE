import uvicorn
# start here each server using subprocesses
if __name__ == '__main__':
    # Main entry point to run the server
    uvicorn.run("server.weaviate_server:app", host="127.0.0.1", port=8000)
    # allows access across the whole network, use ipconfig on windows and get ipv4 address to use later
    # uvicorn.run("server.weaviate_server:app", host="0.0.0.0", port=8000)
