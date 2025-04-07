# mcp_instance.py

from mcp.server.fastmcp import FastMCP, Context
from mcp.server.fastmcp.prompts import base
from mcp_server.chris_api import get_plugins, get_plugin_instance_details, get_pacs_files, get_user_files, get_pipelines, get_pipeline_details

CHRIS_URL = "http://localhost:8000"

# Create the FastMCP server
server = FastMCP("ChRIS MCP Server")

# Debugging tool registration
print("🧪 Registering tools...")

# 🧠 Optional prompt (used for natural language reasoning in UI)
@server.prompt()
def chris_chat(message: str) -> list[base.Message]:
    return [
        base.UserMessage("Here is what the user wants to do:"),
        base.UserMessage(message),
        base.AssistantMessage("Would you like me to list all available ChRIS plugins?")
    ]

# 🔌 Plugin tool: list all ChRIS plugins
@server.tool()
def list_plugins(username: str, password: str) -> dict:
    print("🔧 Tool 'list_plugins' registered.")  # Debugging tool registration
    return get_plugins(username, password)

# 🔌 Plugin tool: get plugin instance details
@server.tool()
def get_plugin_instance(instance_id: int, username: str, password: str) -> dict:
    print("🔧 Tool 'get_plugin_instance' registered.")  # Debugging tool registration
    return get_plugin_instance_details(username, password, instance_id)

# 🔌 Tool to get PACS files
@server.tool()
def list_pacs_files(username: str, password: str) -> dict:
    return get_pacs_files(username, password)

# 🔌 Tool to get user files
@server.tool()
def list_user_files(username: str, password: str) -> dict:
    return get_user_files(username, password)

# 🔌 Tool to list all pipelines
@server.tool()
def list_pipelines(username: str, password: str) -> dict:
    return get_pipelines(username, password)

# 🔌 Tool to get pipeline details
@server.tool()
def get_pipeline_details_tool(pipeline_id: int, username: str, password: str) -> dict:
    return get_pipeline_details(username, password, pipeline_id)

# 🔌 Generic tool to handle plugin-related requests
@server.tool()
def chris_tool_chat(ctx: Context, message: str, username: str, password: str) -> list[base.Message]:
    msg = message.lower()

    if "plugin" in msg:
        plugins = get_plugins(username, password)
        names = [p["name"] for p in plugins.get("plugins", [])]
        return [
            base.UserMessage("Listing all plugins."),
            base.AssistantMessage("Plugins:\n" + "\n".join(f"- {n}" for n in names))
        ]
    
    if "instance" in msg:
        try:
            instance_id = int(next(word for word in msg.split() if word.isdigit()))
            instance = get_plugin_instance_details(username, password, instance_id)
            formatted = "\n".join(f"{k}: {v}" for k, v in instance.items())
            return [
                base.UserMessage(f"You asked for instance {instance_id}"),
                base.AssistantMessage(f"Here are the details:\n{formatted}")
            ]
        except Exception as e:
            return [
                base.AssistantMessage(f"❌ Failed to fetch instance info: {str(e)}")
            ]
    
    return [base.AssistantMessage("Try saying: 'Show plugin instance 2'")]

# Start the server
if __name__ == "__main__":
    server.run()

# Export the server instance to be used in the SSE server
__all__ = ["server"]
