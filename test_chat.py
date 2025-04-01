import asyncio
import subprocess
import json

from mcp import ClientSession, types
from mcp.client.stdio import stdio_client
from mcp.client.params import StdioServerParameters  # ✅ Correct import

# 🔁 LLM integration with Ollama
async def handle_sampling_message(message: types.CreateMessageRequestParams) -> types.CreateMessageResult:
    user_messages = [
        msg.content.text
        for msg in message.messages
        if isinstance(msg.content, types.TextContent)
    ]
    input_text = "\n".join(user_messages)

    result = subprocess.run(
        ["ollama", "run", "llama3"],
        input=input_text,
        text=True,
        capture_output=True
    )

    return types.CreateMessageResult(
        role="assistant",
        content=types.TextContent(type="text", text=result.stdout.strip()),
        model="llama3",
        stopReason="endTurn"
    )

# 🤖 Chat loop
async def run():
    server_params = StdioServerParameters(
        command="python",
        args=["-m", "mcp_server.entrypoint"]
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write, sampling_callback=handle_sampling_message) as session:
            await session.initialize()
            print("💬 Ready to chat with ChRIS MCP Server (LLM-enabled).\n")

            while True:
                user_input = input("🧑 You: ")
                message = types.CreateMessageRequestParams(
                    messages=[
                        types.Message(role="user", content=types.TextContent(type="text", text=user_input))
                    ]
                )
                reply = await session.create_message(message)
                print(f"🤖 Assistant: {reply.content.text.strip()}")

if __name__ == "__main__":
    asyncio.run(run())
