from mcp.server.fastmcp import FastMCP, Context
from mcp.server.fastmcp.prompts import base
import subprocess
import requests
import json

CHRIS_URL = "http://localhost:8000"

# Create the FastMCP server
server = FastMCP("ChRIS MCP Server")

# Function to get the list of plugins from ChRIS
def get_plugins(chris_url: str, username: str, password: str) -> dict:
    url = f"{chris_url}/api/v1/plugins/"
    response = requests.get(url, auth=(username, password))
    response.raise_for_status()  # Raise an error if the status code is not 200
    return response.json()

# Tool to list all plugins using the get_plugins function from chris_api.py
@server.tool()
def list_plugins(username: str, password: str) -> dict:
    return get_plugins(CHRIS_URL, username, password)

# Tool to execute a custom command (e.g., plugin instance)
@server.tool()
def run_custom_command(command: str) -> str:
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    return result.stdout

# Exported for use in SSE server
__all__ = ["server"]
