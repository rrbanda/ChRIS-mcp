from mcp.server.fastmcp import FastMCP

from mcp_server.chris_api import get_plugins, get_plugin_instance_details

CHRIS_URL = "http://localhost:8000"

server = FastMCP("ChRIS MCP Server")

@server.tool()
def list_plugins(username: str, password: str) -> dict:
    """List all plugins from ChRIS using basic auth."""
    return get_plugins(CHRIS_URL, username, password)

@server.tool()
def get_plugin_instance(instance_id: int, username: str, password: str) -> dict:
    """Get details for a specific plugin instance by ID."""
    return get_plugin_instance_details(CHRIS_URL, username, password, instance_id)

if __name__ == "__main__":
    server.run()
