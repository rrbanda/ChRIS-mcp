import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

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
    url = args.get("url", "http://localhost/api/v1/")
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
    url = args.get("url", "https://localhost/api/v1/plugins/")
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

    url = f"http://localhost/api/v1/plugins/instances/{plugin_id}/"
    try:
        response = requests.get(url, timeout=60)
        response.raise_for_status()
        logger.debug(f"Plugin instance {plugin_id} response: {response.json()}")
        return json.dumps(response.json(), indent=2)
    except requests.RequestException as e:
        raise McpError(ErrorData(code=INTERNAL_ERROR, message=f"ChRIS API error: {str(e)}")) from e
    except Exception as e:
        raise McpError(ErrorData(code=INTERNAL_ERROR, message=f"Unexpected error: {str(e)}")) from e



# === Tool 4: ChRIS Client Info ===

@mcp.tool(
    name="chris_client_info",
    description="Authenticates with the ChRIS API and returns a token and API root info. Requires 'url', 'username', 'password'."
)
def chris_client_info(*, args: Dict[str, Any]) -> str:
    url = args.get("url")
    username = args.get("username")
    password = args.get("password")

    if not all([url, username, password]):
        raise McpError(ErrorData(
            code=INVALID_PARAMS,
            message="Missing required argument(s): 'url', 'username', 'password'"
        ))

    try:
        token_url = f"{url.rstrip('/')}/auth-token/"
        token_resp = requests.post(token_url, data={"username": username, "password": password})
        token_resp.raise_for_status()
        token = token_resp.json().get("token")

        if not token:
            raise McpError(ErrorData(code=INTERNAL_ERROR, message="Token not found in auth response"))

        headers = {"Authorization": f"Token {token}"}

        # Safe fallback if /users/<username>/ is unavailable
        user_info = None
        try:
            user_url = f"{url.rstrip('/')}/users/{username}/"
            user_resp = requests.get(user_url, headers=headers, timeout=10)
            user_resp.raise_for_status()
            user_info = user_resp.json()
        except requests.RequestException:
            user_info = {"error": f"/users/{username}/ not found or not supported."}

        root_resp = requests.get(url, headers=headers, timeout=10)
        root_resp.raise_for_status()

        return json.dumps({
            "token": token,
            "user": user_info,
            "api_root": root_resp.json()
        }, indent=2)

    except requests.HTTPError as e:
        return json.dumps({
            "error": f"HTTPError: {e}",
            "status_code": e.response.status_code,
            "response": e.response.text
        }, indent=2)
    except requests.RequestException as e:
        raise McpError(ErrorData(code=INTERNAL_ERROR, message=f"ChRIS API error: {str(e)}")) from e
    except Exception as e:
        raise McpError(ErrorData(code=INTERNAL_ERROR, message=f"Unexpected error: {str(e)}")) from e
    

@mcp.tool(
    name="plugin_search",
    description="Search for ChRIS plugins by name, type, or category. Requires 'url', 'username', 'password'. Optional: 'name', 'type', 'category', 'title'."
)
def plugin_search(*, args: Dict[str, Any]) -> str:
    url = args.get("url")
    username = args.get("username")
    password = args.get("password")

    if not all([url, username, password]):
        raise McpError(ErrorData(
            code=INVALID_PARAMS,
            message="Missing required argument(s): 'url', 'username', 'password'"
        ))

    try:
        # Authenticate
        token_url = f"{url.rstrip('/')}/auth-token/"
        token_resp = requests.post(token_url, data={"username": username, "password": password})
        token_resp.raise_for_status()
        token = token_resp.json().get("token")
        if not token:
            raise McpError(ErrorData(code=INTERNAL_ERROR, message="Token not found in auth response"))

        headers = {"Authorization": f"Token {token}"}

        # Build search query
        valid_filters = ["name", "type", "category", "title"]
        query_params = {k: v for k, v in args.items() if k in valid_filters}

        plugins_url = f"{url.rstrip('/')}/plugins/"
        response = requests.get(plugins_url, headers=headers, params=query_params, timeout=30)
        response.raise_for_status()

        return json.dumps(response.json(), indent=2)

    except requests.HTTPError as e:
        return json.dumps({
            "error": f"HTTPError: {e}",
            "status_code": e.response.status_code,
            "response": e.response.text
        }, indent=2)
    except Exception as e:
        raise McpError(ErrorData(code=INTERNAL_ERROR, message=f"Plugin search failed: {str(e)}")) from e



@mcp.tool()
def run_plugin_instance(*, args: Dict[str, Any]) -> str:
    """
    Launch a new plugin instance in ChRIS.

    Required:
    - url, username, password, plugin_id

    Optional:
    - title, previous_id, dir, and any other plugin-specific parameters
    """
    import requests
    from mcp.types import ErrorData, INTERNAL_ERROR, INVALID_PARAMS

    url = args.get("url")
    username = args.get("username")
    password = args.get("password")
    plugin_id = args.get("plugin_id")

    if not all([url, username, password, plugin_id]):
        raise McpError(ErrorData(
            code=INVALID_PARAMS,
            message="Missing required argument(s): 'url', 'username', 'password', 'plugin_id'"
        ))

    try:
        # Step 1: Authenticate
        token_resp = requests.post(
            f"{url}/auth-token/",
            data={"username": username, "password": password},
            timeout=10
        )
        token_resp.raise_for_status()
        token = token_resp.json().get("token")
        headers = {"Authorization": f"Token {token}"}

        # Step 2: Extract plugin payload
        payload = {
            k: v for k, v in args.items()
            if k not in {"url", "username", "password"}
        }

        # Step 3: POST to plugin instance endpoint
        endpoint = f"{url}/plugins/{plugin_id}/instances/"
        response = requests.post(endpoint, headers=headers, data=payload, timeout=30)
        response.raise_for_status()

        return json.dumps(response.json(), indent=2)

    except requests.HTTPError as e:
        return f"Plugin launch failed: {e.response.text}"
    except Exception as e:
        raise McpError(ErrorData(
            code=INTERNAL_ERROR,
            message=f"Unexpected error: {str(e)}"
        ))



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