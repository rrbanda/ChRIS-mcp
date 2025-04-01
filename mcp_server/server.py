from mcp.server.fastmcp import FastMCP, Context
from mcp.server.fastmcp.prompts import base

from mcp_server.chris_api import get_plugins, get_plugin_instance_details

CHRIS_URL = "http://localhost:8000"

server = FastMCP("ChRIS MCP Server")

# 💬 Prompt shown in MCP Inspector
@server.prompt()
def chris_chat(message: str) -> list[base.Message]:
    return [
        base.UserMessage("Here is what the user wants to do:"),
        base.UserMessage(message),
        base.AssistantMessage("Would you like me to list all available ChRIS plugins?")
    ]

# 🔧 List all plugins from ChRIS
@server.tool()
def list_plugins(username: str, password: str) -> dict:
    """List all plugins from ChRIS using basic auth."""
    return get_plugins(CHRIS_URL, username, password)

# 🔍 Get specific plugin instance details
@server.tool()
def get_plugin_instance(instance_id: int, username: str, password: str) -> dict:
    """Get details for a specific plugin instance by ID."""
    return get_plugin_instance_details(CHRIS_URL, username, password, instance_id)

# 🧠 Smart NLP-aware tool that can trigger real actions
@server.tool()
def chris_tool_chat(ctx: Context, message: str, username: str, password: str) -> list[base.Message]:
    """Intelligently respond to user input and optionally invoke ChRIS tools."""
    lower_msg = message.lower()

    if any(kw in lower_msg for kw in ["list plugin", "show plugins", "available plugins", "plugin list"]):
        plugins = get_plugins(CHRIS_URL, username, password)
        plugin_names = [plugin["name"] for plugin in plugins.get("plugins", [])]
        return [
            base.UserMessage("You asked me to list all plugins."),
            base.AssistantMessage("Here are the plugins available:\n- " + "\n- ".join(plugin_names))
        ]

    return [
        base.UserMessage("You said:"),
        base.UserMessage(message),
        base.AssistantMessage("I'm here to help! Do you want to list plugins or inspect a plugin instance?")
    ]

if __name__ == "__main__":
    server.run()

@server.tool()
def llama_response(message: str) -> base.AssistantMessage:
    """Call local Ollama (llama3) and return its response."""
    result = subprocess.run(
        ["ollama", "run", "llama3"],
        input=message,
        text=True,
        capture_output=True
    )
    return base.AssistantMessage(result.stdout.strip())