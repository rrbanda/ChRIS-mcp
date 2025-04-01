import subprocess
from mcp.server.fastmcp import FastMCP, Context
from mcp.server.fastmcp.prompts import base

# Import functions from chris_api.py
from mcp_server.chris_api import get_plugins, get_plugin_instance_details, get_pacs_files, get_user_files, get_pipelines, get_pipeline_details, search_plugins, create_pipeline

CHRIS_URL = "http://localhost:8000"

server = FastMCP("ChRIS MCP Server")

# Define a simple chat prompt in MCP Inspector
@server.prompt()
def chris_chat(message: str) -> list[base.Message]:
    return [
        base.UserMessage("Here is what the user wants to do:"),
        base.UserMessage(message),
        base.AssistantMessage("Would you like me to list all available ChRIS plugins?")
    ]

# Tool to list all plugins using the get_plugins function from chris_api.py
@server.tool()
def list_plugins(username: str, password: str) -> dict:
    return get_plugins(CHRIS_URL, username, password)

# Tool to get plugin instance details using get_plugin_instance_details function from chris_api.py
@server.tool()
def get_plugin_instance(instance_id: int, username: str, password: str) -> dict:
    return get_plugin_instance_details(CHRIS_URL, username, password, instance_id)

# Tool to get PACS files using get_pacs_files function from chris_api.py
@server.tool()
def list_pacs_files(username: str, password: str) -> dict:
    return get_pacs_files(CHRIS_URL, username, password)

# Tool to get user files using get_user_files function from chris_api.py
@server.tool()
def list_user_files(username: str, password: str) -> dict:
    return get_user_files(CHRIS_URL, username, password)

# Tool to get all pipelines using get_pipelines function from chris_api.py
@server.tool()
def list_pipelines(username: str, password: str) -> dict:
    return get_pipelines(CHRIS_URL, username, password)

# Tool to get details of a specific pipeline using get_pipeline_details function from chris_api.py
@server.tool()
def get_pipeline_details_tool(pipeline_id: int, username: str, password: str) -> dict:
    return get_pipeline_details(CHRIS_URL, username, password, pipeline_id)

# Tool to search for plugins using search_plugins function from chris_api.py
@server.tool()
def search_for_plugins(query: dict, username: str, password: str) -> dict:
    return search_plugins(CHRIS_URL, username, password, query)


@server.tool()
def create_chris_pipeline(username: str, password: str, pipeline_data: dict) -> dict:
    """Tool to create a new pipeline."""
    try:
        # Ensure the required fields are in the pipeline_data
        required_fields = ['name', 'description', 'plugin_ids']
        if not all(field in pipeline_data for field in required_fields):
            raise ValueError(f"Missing required fields: {', '.join([field for field in required_fields if field not in pipeline_data])}")

        # Call the ChRIS API to create the pipeline
        return create_pipeline(CHRIS_URL, username, password, pipeline_data)
    except Exception as e:
        return {"error": f"Failed to create pipeline: {str(e)}"}



# A generic tool that handles plugin-related requests (list plugins, show instance details, etc.)
@server.tool()
def chris_tool_chat(ctx: Context, message: str, username: str, password: str) -> list[base.Message]:
    msg = message.lower()

    if "plugin" in msg:
        plugins = get_plugins(CHRIS_URL, username, password)
        names = [p["name"] for p in plugins.get("plugins", [])]
        return [
            base.UserMessage("Listing all plugins."),
            base.AssistantMessage("Plugins:\n" + "\n".join(f"- {n}" for n in names))
        ]
    
    if "instance" in msg:
        try:
            parts = msg.split()
            instance_id = int(next(word for word in parts if word.isdigit()))
            instance = get_plugin_instance_details(CHRIS_URL, username, password, instance_id)
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

# Optional LLM wrapper
@server.tool()
def llama_response(message: str) -> base.AssistantMessage:
    result = subprocess.run(
        ["ollama", "run", "llama3"],
        input=message,
        text=True,
        capture_output=True
    )
    return base.AssistantMessage(result.stdout.strip())

if __name__ == "__main__":
    server.run()

# Required for MCP CLI discovery
__all__ = ["server"]
