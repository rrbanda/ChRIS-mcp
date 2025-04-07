# mcp_server/main.py
from mcp_server.sse_server import app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7001)

