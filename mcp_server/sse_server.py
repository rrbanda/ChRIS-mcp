from fastapi import FastAPI, Request
from sse_starlette.sse import EventSourceResponse
from mcp_server.mcp_instance import server  # Import the server with tools
import uuid
import json

app = FastAPI(title="ChRIS MCP SSE Server")

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
            
            # Access the tool dynamically
            tool_func = getattr(server, tool_name, None)
            if not tool_func:
                yield {"event": "error", "id": call_id, "data": f"Tool '{tool_name}' not found"}
                return

            # Execute the tool function and get the result
            result = await tool_func(**body)

            yield {"event": "result", "id": call_id, "data": json.dumps(result, default=str)}
            yield {"event": "end", "id": call_id, "data": "Tool execution complete"}
        except Exception as e:
            yield {"event": "error", "id": call_id, "data": str(e)}

    return EventSourceResponse(event_stream())
