# llm_handler.py
import subprocess
import json
from mcp import types

async def handle_sampling_message(message: types.CreateMessageRequestParams) -> types.CreateMessageResult:
    # Convert messages to JSON for Ollama
    messages = []
    for msg in message.messages:
        if isinstance(msg.content, types.TextContent):
            messages.append({
                "role": msg.role,
                "content": msg.content.text
            })

    input_json = json.dumps({"messages": messages})

    result = subprocess.run(
        ["ollama", "run", "llama3"],
        input=input_json,
        text=True,
        capture_output=True
    )

    return types.CreateMessageResult(
        role="assistant",
        content=types.TextContent(type="text", text=result.stdout.strip()),
        model="llama3",
        stopReason="endTurn"
    )
