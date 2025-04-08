import requests
import json
from typing import Dict, Any
import subprocess
import logging
from mcp.server.fastmcp import FastMCP
from mcp.shared.exceptions import McpError
from mcp.types import ErrorData, INTERNAL_ERROR, INVALID_PARAMS
from mcp.server.sse import SseServerTransport
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.routing import Route, Mount
import time
from mcp.types import ErrorData, INTERNAL_ERROR, INVALID_PARAMS

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create FastMCP instance
mcp = FastMCP("chris")

# === Tool 1: Get ChRIS Root ===
@mcp.tool()
def get_chris_root(*, args: Dict[str, Any]) -> str:
    """
    Fetch the root Collection+JSON document from a ChRIS API instance.
    """
    url = args.get("url", "https://cube.chrisproject.org/api/v1/")
    if not url.startswith("http"):
        raise McpError(ErrorData(INVALID_PARAMS, "URL must start with http or https."))

    try:
        response = requests.get(url, timeout=60)  # Extended timeout
        response.raise_for_status()
        logger.debug(f"Response from ChRIS API: {response.json()}")
        return json.dumps(response.json(), indent=2)
    except requests.RequestException as e:
        raise McpError(ErrorData(INTERNAL_ERROR, f"ChRIS API error: {str(e)}")) from e
    except Exception as e:
        raise McpError(ErrorData(INTERNAL_ERROR, f"Unexpected error: {str(e)}")) from e

# === Tool 2: List Plugins ===
@mcp.tool()
def list_plugins(*, args: Dict[str, Any]) -> str:
    """
    Lists all available plugins in the ChRIS API instance.
    """
    url = args.get("url", "https://cube.chrisproject.org/api/v1/plugins/")
    if not url.startswith("http"):
        raise McpError(ErrorData(INVALID_PARAMS, "URL must start with http or https."))

    try:
        response = requests.get(url, timeout=60)
        response.raise_for_status()
        logger.debug(f"Response from ChRIS Plugin List: {response.json()}")
        return json.dumps(response.json(), indent=2)
    except requests.RequestException as e:
        raise McpError(ErrorData(INTERNAL_ERROR, f"ChRIS plugin list error: {str(e)}")) from e
    except Exception as e:
        raise McpError(ErrorData(INTERNAL_ERROR, f"Unexpected error: {str(e)}")) from e





@mcp.tool()
def get_plugin_instance(*, args: Dict[str, Any]) -> str:
    """
    Fetch a specific plugin instance by ID from the ChRIS API.
    """
    plugin_id = args.get("id")
    if not plugin_id:
        raise McpError(ErrorData(code=INVALID_PARAMS, message="Missing required argument: 'id'"))

    url = f"https://cube.chrisproject.org/api/v1/plugins/instances/{plugin_id}/"
    try:
        response = requests.get(url, timeout=60)
        response.raise_for_status()
        logger.debug(f"Plugin instance {plugin_id} response: {response.json()}")
        return json.dumps(response.json(), indent=2)
    except requests.RequestException as e:
        raise McpError(ErrorData(code=INTERNAL_ERROR, message=f"ChRIS API error: {str(e)}")) from e
    except Exception as e:
        raise McpError(ErrorData(code=INTERNAL_ERROR, message=f"Unexpected error: {str(e)}")) from e


# === SSE Transport ===
sse = SseServerTransport("/messages/")

async def handle_sse(request: Request) -> None:
    _server = mcp._mcp_server
    try:
        async with sse.connect_sse(request.scope, request.receive, request._send) as (reader, writer):
            await _server.run(reader, writer, _server.create_initialization_options())
    except Exception as e:
        logger.error(f"SSE connection failed: {e}")
        raise

# === Starlette App ===
app = Starlette(
    debug=True,
    routes=[
        Route("/sse", endpoint=handle_sse),
        Mount("/messages/", app=sse.handle_post_message),
    ],
)

# === Entry Point ===
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=3001)