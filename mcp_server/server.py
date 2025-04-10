import sys
import os
import json
import time
import logging
import requests
from typing import Dict, Any
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route, Mount

from mcp.server.fastmcp import FastMCP
from mcp.shared.exceptions import McpError
from mcp.server.sse import SseServerTransport
from mcp.types import ErrorData, INTERNAL_ERROR, INVALID_PARAMS

# Add current folder to sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# === Response Helper ===
def wrap_tool_output(tool_name: str, payload: Any) -> str:
    return json.dumps({
        "tool": tool_name,
        "output": payload,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
    }, indent=2)

# === Safety Helper ===
def ensure_args_is_dict(args: Any) -> Dict[str, Any]:
    if isinstance(args, str):
        try:
            fixed_args = json.loads(args.replace("'", '"'))
            logger.warning(f"🔁 Fixed stringified args: {fixed_args}")
            return fixed_args
        except Exception as e:
            logger.error(f"❌ Could not parse stringified args: {e}")
            raise McpError(ErrorData(INVALID_PARAMS, "Invalid args format: must be dict or parseable JSON string"))
    return args

# === MCP Server ===
mcp = FastMCP("chris")

@mcp.tool(name="health_check", description="Simple test tool to confirm LlamaStack <-> ChRIS MCP integration.")
def health_check(*, args: Dict[str, Any]) -> str:
    return wrap_tool_output("health_check", {
        "status": "✅ MCP server is alive!",
        "message": "From the ChRIS MCP server via FastMCP + LlamaStack."
    })

@mcp.tool(description="Fetch the root of a ChRIS API instance.")
def get_chris_root(*, args: Dict[str, Any]) -> str:
    args = ensure_args_is_dict(args)
    url = args.get("url", "https://cube.chrisproject.org/api/v1/")
    try:
        response = requests.get(url, timeout=60)
        response.raise_for_status()
        return wrap_tool_output("get_chris_root", response.json())
    except requests.RequestException as e:
        raise McpError(ErrorData(INTERNAL_ERROR, f"ChRIS root error: {str(e)}"))

@mcp.tool(description="List all available ChRIS plugins (public access).")
def list_plugins(*, args: Dict[str, Any]) -> str:
    args = ensure_args_is_dict(args)
    url = args.get("url", "https://cube.chrisproject.org/api/v1/plugins/")
    try:
        response = requests.get(url, timeout=60)
        response.raise_for_status()
        plugins_data = response.json()

        total = plugins_data.get("total", 0)
        items = plugins_data.get("data") or plugins_data.get("results") or []

        plugin_names = [plugin.get("name", "unknown") for plugin in items]

        return wrap_tool_output("list_plugins", {
            "total_plugins": total,
            "example_plugin_names": plugin_names[:10],
            "note": f"Showing first {min(10, len(plugin_names))} plugin names."
        })

    except requests.RequestException as e:
        logger.exception("Failed to list plugins")
        raise McpError(ErrorData(INTERNAL_ERROR, f"ChRIS plugin list error: {str(e)}"))

@mcp.tool(description="Fetch plugin instance by ID.")
def get_plugin_instance(*, args: Dict[str, Any]) -> str:
    args = ensure_args_is_dict(args)
    plugin_id = args.get("id")
    if not plugin_id:
        raise McpError(ErrorData(INVALID_PARAMS, "Missing required argument: 'id'"))

    url = f"https://cube.chrisproject.org/api/v1/plugins/instances/{plugin_id}/"
    try:
        response = requests.get(url, timeout=60)
        response.raise_for_status()
        return wrap_tool_output("get_plugin_instance", response.json())
    except requests.RequestException as e:
        raise McpError(ErrorData(INTERNAL_ERROR, f"Plugin instance error: {str(e)}"))

@mcp.tool(
    name="plugin_search",
    description="Search for ChRIS plugins by name, type, category, title, version or id. Public access only."
)
def plugin_search(*, args: Dict[str, Any]) -> str:
    args = ensure_args_is_dict(args)
    base_url = args.get("url", "https://cube.chrisproject.org/api/v1/")
    plugins_url = f"{base_url.rstrip('/')}/plugins/"
    query_keys = ["name", "type", "category", "title", "version", "id"]
    query_params = {k: v for k, v in args.items() if k in query_keys}

    try:
        response = requests.get(plugins_url, params=query_params, timeout=30)
        response.raise_for_status()
        return wrap_tool_output("plugin_search", response.json())
    except requests.RequestException as e:
        raise McpError(ErrorData(INTERNAL_ERROR, f"Plugin search failed: {str(e)}"))

@mcp.tool(
    name="run_plugin_instance",
    description="Run a ChRIS plugin instance (requires plugin_id, url, username, password)"
)
def run_plugin_instance(*, args: Dict[str, Any]) -> str:
    args = ensure_args_is_dict(args)
    url = args.get("url")
    username = args.get("username")
    password = args.get("password")
    plugin_id = args.get("plugin_id")

    if not all([url, username, password, plugin_id]):
        raise McpError(ErrorData(INVALID_PARAMS, "Missing required arguments: url, username, password, plugin_id"))

    try:
        token_resp = requests.post(f"{url}/auth-token/", data={"username": username, "password": password})
        token_resp.raise_for_status()
        token = token_resp.json().get("token")
        headers = {"Authorization": f"Token {token}"}

        payload = {k: v for k, v in args.items() if k not in {"url", "username", "password"}}
        response = requests.post(f"{url}/plugins/{plugin_id}/instances/", headers=headers, data=payload)
        response.raise_for_status()

        return wrap_tool_output("run_plugin_instance", response.json())
    except requests.RequestException as e:
        raise McpError(ErrorData(INTERNAL_ERROR, f"Plugin instance launch failed: {str(e)}"))

# === SSE Endpoint ===
sse = SseServerTransport("/messages/")

async def handle_sse(request: Request):
    try:
        async with sse.connect_sse(request.scope, request.receive, request._send) as (reader, writer):
            await mcp._mcp_server.run(reader, writer, mcp._mcp_server.create_initialization_options())
    except Exception as e:
        logger.error(f"SSE connection failed: {e}")
        raise

# === Root Metadata Endpoint ===
async def api_root(request: Request):
    return JSONResponse({
        "status": "ok",
        "name": "ChRIS MCP Server",
        "tools": list(mcp._tool_registry.keys()),
        "sse_endpoint": "/sse"
    })

# === Starlette App ===
app = Starlette(
    debug=True,
    routes=[
        Route("/sse", endpoint=handle_sse),
        Route("/api/v1/", endpoint=api_root),
        Mount("/messages/", app=sse.handle_post_message),
    ],
)

# === Local Run ===
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=3001)
