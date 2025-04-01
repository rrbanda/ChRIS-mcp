from mcp.server.fastmcp import FastMCP, Context
from mcp.server.fastmcp.prompts import base

from mcp_server.chris_api import get_plugins, get_plugin_instance_details

CHRIS_URL = "http://localhost:8000"

server = FastMCP("ChRIS MCP Server")

# 🧠 Smart LLM-aware chat logic
@server.tool()
def chris_chat(ctx: Context, message: str, username: str, password: str) -> list[base.Message]:
    """Respond to natural language and optionally call ChRIS tools."""
    lower_msg = message.lower()

    if "list plugin" in lower_msg:
        plugins = get_plugins(CHRIS_URL, username, password)
        plugin_names = [plugin["name"] for plugin in plugins.get("plugins", [])]
        return [
            base.UserMessage("You asked me to list all plugins."),
            base.AssistantMessage(f"Here are the plugins available:\n- " + "\n- ".join(plugin_names))
        ]
    
    return [
        base.UserMessage("Here is what the user wants to do:"),
        base.UserMessage(message),
        base.AssistantMessage("I'm going to help you with that. What specific plugin or feed would you like to interact with?")
    ]

# 🔧 Plugin listing
@server.tool()
def list_plugins(username: str, password: str) -> dict:
    """List all plugins from ChRIS using basic auth."""
    return get_plugins(CHRIS_URL, username, password)

# 🔍 Plugin instance details
@server.tool()
def get_plugin_instance(instance_id: int, username: str, password: str) -> dict:
    """Get details for a specific plugin instance by ID."""
    return get_plugin_instance_details(CHRIS_URL, username, password, instance_id)

if __name__ == "__main__":
    server.run()
