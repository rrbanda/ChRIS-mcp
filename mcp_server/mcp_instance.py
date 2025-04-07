# mcp_server/mcp_instance.py
from mcp.server.fastmcp import FastMCP, Context
from mcp.server.fastmcp.prompts import base
from mcp_server.chris_api import get_plugins, get_plugin_instance_details, get_pacs_files, get_user_files, get_pipelines, get_pipeline_details, search_plugins, create_pipeline

CHRIS_URL = "http://localhost:8000"

# Create the FastMCP server
server = FastMCP("ChRIS MCP Server")

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

# Tool to create a new pipeline
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

# Export the server for usage in sse_server.py
__all__ = ["server"]
