# mcp_server/entrypoint.py
import anyio
from mcp.server.stdio import stdio_server
from mcp.shared.registry import FunctionRegistry  # ✅ FIXED import
from mcp.shared.protocol import JSONRPCResponse, JSONRPCError
from mcp.shared import create_server
from mcp_server.chris_api import get_plugins

CHRIS_URL = "http://localhost:8000"

registry = FunctionRegistry()

@registry.function("list_plugins", description="List all available ChRIS plugins")
async def list_plugins_handler(params):
    username = params.get("username")
    password = params.get("password")
    return await get_plugins(CHRIS_URL, username, password)

async def main():
    async with stdio_server() as (reader, writer):
        server = await create_server(registry)

        async for request in server.run_reader(reader):
            try:
                result = await server.dispatch(request)
                await server.send(writer, JSONRPCResponse(id=request.id, result=result, jsonrpc="2.0"))
            except Exception as e:
                await server.send(writer, JSONRPCError(id=getattr(request, "id", None), jsonrpc="2.0", error={
                    "code": -32000,
                    "message": f"Error: {str(e)}"
                }))

if __name__ == "__main__":
    anyio.run(main)
