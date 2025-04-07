# mcp_server/main.py
from mcp_server.sse_server import app  # Import the SSE server
import uvicorn

if __name__ == "__main__":
    # Start the FastAPI server using Uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7001)
