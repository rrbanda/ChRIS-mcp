from mcp.server.fastmcp import FastMCP, Context
from mcp.server.fastmcp.prompts import base
from mcp_server import chris_api
import subprocess

CHRIS_URL = "http://localhost:8000"

# Create FastMCP server
server = FastMCP("ChRIS MCP Server")

# Optional prompt for chat (can be used for natural language)
@server.prompt()
def chris_chat(message: str) -> list[base.Message]:
    return [
        base.UserMessage("Here is what the user wants to do:"),
        base.UserMessage(message),
        base.AssistantMessage("Would you like me to list all available ChRIS plugins?")
    ]

# Register tools

@server.tool()
def list_plugins(username: str, password: str) -> dict:
    return chris_api.get_plugins(CHRIS_URL, username, password)

@server.tool()
def get_plugin_instance(instance_id: int, username: str, password: str) -> dict:
    return chris_api.get_plugin_instance_details(CHRIS_URL, username, password, instance_id)

@server.tool()
def list_pacs_files(username: str, password: str) -> dict:
    return chris_api.get_pacs_files(CHRIS_URL, username, password)

@server.tool()
def list_user_files(username: str, password: str) -> dict:
    return chris_api.get_user_files(CHRIS_URL, username, password)

@server.tool()
def list_pipelines(username: str, password: str) -> dict:
    return chris_api.get_pipelines(CHRIS_URL, username, password)

@server.tool()
def get_pipeline_details_tool(pipeline_id: int, username: str, password: str) -> dict:
    return chris_api.get_pipeline_details(CHRIS_URL, username, password, pipeline_id)

@server.tool()
def search_for_plugins(query: dict, username: str, password: str) -> dict:
    return chris_api.search_plugins(CHRIS_URL, username, password, query)

# Debugging registered tools
print("🧪 Tools registered:", list(getattr(server, "_tool_map", {}).keys()))

# Run the server
if __name__ == "__main__":
    server.run()

