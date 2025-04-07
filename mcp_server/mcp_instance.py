# mcp_server/mcp_instance.py
from mcp.server.fastmcp import FastMCP, Context
from mcp.server.fastmcp.prompts import base
from mcp_server.chris_api import get_plugins, get_plugin_instance_details

CHRIS_URL = "http://localhost:8000"

# Create the FastMCP server
server = FastMCP("ChRIS MCP Server")

# Debug: Print when tools are registered
print("🧪 Registering tools...")

# Define the list_plugins tool
@server.tool()
def list_plugins(username: str, password: str) -> dict:
    print("🔧 Tool 'list_plugins' registered.")  # Debugging tool registration
    return get_plugins(CHRIS_URL, username, password)

# Define other tools like get_plugin_instance, list_pacs_files, etc.
@server.tool()
def get_plugin_instance(instance_id: int, username: str, password: str) -> dict:
    return get_plugin_instance_details(CHRIS_URL, username, password, instance_id)

# Start the server
if __name__ == "__main__":
    print("🧪 Starting the server...")
    server.run()

# Export the server instance to be used in the SSE server
__all__ = ["server"]
