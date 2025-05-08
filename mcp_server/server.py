import sys
import os
import json
import time
import logging
from typing import Dict, Any
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route, Mount

from mcp.server.fastmcp import FastMCP
from mcp.server.sse import SseServerTransport
from mcp.shared.exceptions import McpError
from mcp.types import ErrorData, INTERNAL_ERROR, INVALID_PARAMS

import httpx

# Add current folder to sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("chris-server")

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
mcp = FastMCP("ChRIS MCP Server 🚀", dependencies=["httpx"])

# === Tool 1: Health check ===
@mcp.tool(name="health_check", description="Simple test to confirm MCP server is alive.")
def health_check(*, args: Dict[str, Any]) -> str:
    return wrap_tool_output("health_check", {
        "status": "✅ MCP server is alive!",
        "message": "This is a test response from the ChRIS MCP server."
    })

# === Tool 2: List plugins from ChRIS Cube ===
@mcp.tool()
async def list_chris_plugins(limit: int = 5) -> str:
    """
    List plugins from the ChRIS Cube API using Collection+JSON format.
    """
    url = "https://cube.chrisproject.org/api/v1/plugins/"
    params = {"limit": limit}
    headers = {
        "Accept": "application/vnd.collection+json"
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, params=params, headers=headers, timeout=10.0)
            response.raise_for_status()
            data = response.json()
        except Exception as e:
            return f"❌ Failed to fetch plugin list: {e}"

    try:
        items = data["collection"]["items"]
        result = []
        for item in items:
            plugin = {entry["name"]: entry["value"] for entry in item["data"]}
            result.append(
                f"- {plugin.get('name')} (v{plugin.get('version')}): {plugin.get('title')}"
            )
        return "\n".join(result)
    except Exception as e:
        return f"❌ Error parsing response: {e}"

# === SSE Transport Endpoint ===
sse = SseServerTransport("/messages/")

async def handle_sse(request: Request):
    try:
        async with sse.connect_sse(request.scope, request.receive, request._send) as (reader, writer):
            await mcp._mcp_server.run(reader, writer, mcp._mcp_server.create_initialization_options())
    except Exception as e:
        logger.error(f"SSE connection failed: {e}")
        raise

# === REST Endpoint: Root Metadata ===
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

# === Local Run Mode ===
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=3001)

