from mcp.server.fastmcp import FastMCP
from mcp_server.chris_api import get_plugins

CHRIS_URL = "http://localhost:8000"

# Create the FastMCP server
server = FastMCP("ChRIS MCP Server")

# Define the 'list_plugins' tool
@server.tool()
def list_plugins(username: str, password: str) -> dict:
    return get_plugins(CHRIS_URL, username, password)

# Optional: Add more tools for other operations like getting plugin instance details

# Run the server
if __name__ == "__main__":
    server.run()

# Exported for import in sse_server.py
__all__ = ["server"]
