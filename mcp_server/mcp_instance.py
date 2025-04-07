from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.prompts import base
from mcp_server.chris_api import get_plugins, get_plugin_instance_details

# ChRIS API URL
CHRIS_URL = "http://localhost:8000"

# Create FastMCP server
server = FastMCP("ChRIS MCP Server")

# Tool to list all plugins
@server.tool()
def list_plugins(username: str, password: str) -> dict:
    print("🔧 Tool 'list_plugins' is being executed.")  # Debug message
    return get_plugins(CHRIS_URL, username, password)

# Tool to get plugin instance details
@server.tool()
def get_plugin_instance(instance_id: int, username: str, password: str) -> dict:
    print(f"🔧 Tool 'get_plugin_instance' is being executed for ID: {instance_id}")  # Debug message
    return get_plugin_instance_details(CHRIS_URL, username, password, instance_id)

# Add more tools as needed...

if __name__ == "__main__":
    print("🧪 Starting the server...")
    server.run()  # Run the server

__all__ = ["server"]
