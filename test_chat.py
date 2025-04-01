import asyncio
from client import types
from client.stdio import stdio_client
from client.params import StdioServerParameters
from client.client_session import ClientSession
from llm_handler import handle_sampling_message


async def run():
    server_params = StdioServerParameters(
        command="python",
        args=["-m", "mcp_server.entrypoint"]
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write, sampling_callback=handle_sampling_message) as session:
            await session.initialize()

            print("🔁 Type a message. Ctrl+C to quit.")
            while True:
                user_input = input("🧑 You: ")
                message = types.CreateMessageRequestParams(
                    messages=[
                        types.Message(
                            role="user",
                            content=types.TextContent(type="text", text=user_input)
                        )
                    ]
                )
                reply = await session.create_message(message)
                print(f"🤖 Assistant: {reply.content.text.strip()}")


if __name__ == "__main__":
    asyncio.run(run())
