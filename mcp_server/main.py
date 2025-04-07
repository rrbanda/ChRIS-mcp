import uvicorn
from mcp_server.sse_server import app  # Import the SSE server

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=7005)  # Run the server on port 7004

