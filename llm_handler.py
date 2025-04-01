# llm_handler.py
import subprocess
import json
from mcp import types

async def handle_sampling_message(message: types.CreateMessageRequestParams) -> types.CreateMessageResult:
    input_texts = [
        f"{msg.role}: {msg.content.text}"
        for msg in message.messages
        if isinstance(msg.content, types.TextContent)
    ]
    prompt = "\n".join(input_texts)

    result = subprocess.run(
        ["ollama", "run", "llama3"],
        input=prompt,
        capture_output=True,
        text=True
    )

    return types.CreateMessageResult(
        role="assistant",
        content=types.TextContent(type="text", text=result.stdout.strip()),
        model="llama3",
        stopReason="endTurn"
    )
