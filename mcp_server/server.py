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

# === chris_chat tool ===
@mcp.tool()
async def chris_chat(*, args: Dict[str, Any]) -> str:
    """
    Natural language query handler for ChRIS via MCP.

    Uses:
    - Ollama (Llama3.2) to select a tool like get_chris_root
    - Calls that tool using MCP
    - Then summarizes the result using LLM again

    Input example:
    {
      "args": {
        "query": "What is the root endpoint of the ChRIS API?"
      }
    }
    """
    # Handle both flat and nested query structure
    query = args.get("query") or args.get("args", {}).get("query")
    if not query:
        return "Please provide a question via the 'query' argument."

    # Step 1: Ask LLM which tool to route to
    try:
        tool_prompt = f"""
You are an assistant that helps route natural language questions to MCP tools.

Available tools:
- get_chris_root: Fetches the root Collection+JSON from a ChRIS API instance.

User question:
{query}

Respond with only the tool name (e.g., get_chris_root). Do not explain.
""".strip()

        # Run LLM to decide the tool to use (switching to llama3.2)
        logger.debug(f"LLM tool routing prompt: {tool_prompt}")
        tool_resp = subprocess.run(
            ["ollama", "run", "llama3.2", tool_prompt],  # Using llama3.2 model
            capture_output=True, text=True, timeout=10
        )
        tool_name = tool_resp.stdout.strip().split()[0]
        logger.debug(f"LLM chose tool: {tool_name}")
    except Exception as e:
        logger.error(f"Tool routing failed via LLM: {e}")
        return f"Tool routing failed via LLM: {e}"

    # Step 2: Call the selected tool with empty args and await the result
    try:
        tool_output = await mcp.call_tool(tool_name, arguments={"args": {}})
        logger.debug(f"Tool '{tool_name}' output: {tool_output}")
    except Exception as e:
        logger.error(f"Tool '{tool_name}' call failed: {e}")
        return f"Tool '{tool_name}' call failed: {e}"

    # Step 3: Ask LLM to summarize the tool output
    try:
        summary_prompt = f"""
The following is the JSON output from a ChRIS API tool ('{tool_name}').

Summarize it in plain language so a user can understand what it means:

{tool_output}
""".strip()

        # Summarize the tool output with LLM (llama3.2)
        logger.debug(f"LLM summarization prompt: {summary_prompt}")
        summary_resp = subprocess.run(
            ["ollama", "run", "llama3.2", summary_prompt],  # Using llama3.2 model for summarization
            capture_output=True, text=True, timeout=20
        )
        logger.debug(f"LLM summary: {summary_resp.stdout.strip()}")
        return summary_resp.stdout.strip()
    except Exception as e:
        logger.error(f"Tool '{tool_name}' succeeded, but LLM summarization failed: {e}")
        return f"Tool '{tool_name}' succeeded, but LLM summarization failed: {e}"

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
    uvicorn.run(app, host="localhost", port=8000)
