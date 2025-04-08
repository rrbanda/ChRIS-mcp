import requests
import json
from typing import Dict, Any
import subprocess
from typing import Dict, Any
from mcp.server.fastmcp import FastMCP
from mcp.shared.exceptions import McpError
from mcp.types import ErrorData, INTERNAL_ERROR, INVALID_PARAMS
from mcp.server.sse import SseServerTransport
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.routing import Route, Mount

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
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return json.dumps(response.json(), indent=2)
    except requests.RequestException as e:
        raise McpError(ErrorData(INTERNAL_ERROR, f"ChRIS API error: {str(e)}")) from e
    except Exception as e:
        raise McpError(ErrorData(INTERNAL_ERROR, f"Unexpected error: {str(e)}")) from e

@mcp.tool()
def chris_chat(args: Dict[str, Any]) -> str:
    real_args = args.get("args", {})  # MCP Inspector wraps it like this
    query = real_args.get("query", "")

    if not query:
        return f"DEBUG: Missing 'query'. Full args={args}"

    try:
        import subprocess

        # Use LLM to decide which tool to call
        system_prompt = (
            "You are a helpful agent for the ChRIS API. "
            "Only say the name of the tool that should be called. Available: get_chris_root"
        )
        full_prompt = f"{system_prompt}\n\nUser said: {query}\nTool:"

        result = subprocess.run(
            ["ollama", "run", "mistral"],
            input=full_prompt.encode(),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=30,
        )

        if result.returncode != 0:
            return f"Ollama error: {result.stderr.decode()}"

        tool_name = result.stdout.decode().strip().lower()

        if "get_chris_root" in tool_name:
            return get_chris_root(args={"url": "https://cube.chrisproject.org/api/v1/"})

        return f"No matching tool. LLM said: {tool_name}"

    except subprocess.TimeoutExpired:
        return "LLM timed out."
    except Exception as e:
        return f"Unexpected error: {str(e)}"


# === SSE Transport ===
sse = SseServerTransport("/messages/")

async def handle_sse(request: Request) -> None:
    _server = mcp._mcp_server
    async with sse.connect_sse(request.scope, request.receive, request._send) as (reader, writer):
        await _server.run(reader, writer, _server.create_initialization_options())


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
    uvicorn.run(app, host="localhost", port=8000)
