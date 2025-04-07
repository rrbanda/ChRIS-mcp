from fastapi import FastAPI
import uvicorn

from mcp_server.sse_server import app  # Import the SSE server

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8089)
