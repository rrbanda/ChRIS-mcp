from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse
import uuid
import json

# Import FastMCP server instance
from mcp_server.mcp_instance import server

# Create FastAPI app
app = FastAPI(title="ChRIS MCP SSE Server")

# Enable CORS for local testing / LlamaStack integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update with LlamaStack host in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "ChRIS MCP SSE Server is running."}

@app.post("/tool/{tool_name}")
async def run_tool(tool_name: str, request: Request):
    body = await request.json()
    call_id = str(uuid.uuid4())

    async def event_stream():
        try:
            yield {"event": "start", "id": call_id, "data": f"Running tool: {tool_name}"}
            
            # Get the tool function from the server
            tool_map = getattr(server, "_tool_map", {})
            tool_func = tool_map.get(tool_name)

            if not tool_func:
                yield {"event": "error", "id": call_id, "data": f"Tool '{tool_name}' not found"}
                return

            # Run the tool function
            kwargs = body if isinstance(body, dict) else {}
            result = await tool_func(**kwargs)

            yield {"event": "result", "id": call_id, "data": json.dumps(result, default=str)}
            yield {"event": "end", "id": call_id, "data": "Tool execution complete"}

        except Exception as e:
            yield {"event": "error", "id": call_id, "data": str(e)}

    return EventSourceResponse(event_stream())
