import subprocess
import json
from client import types

async def handle_sampling_message(message: types.CreateMessageRequestParams) -> types.CreateMessageResult:
    # Prepare messages as JSON for input to Ollama
    input_json = json.dumps({
        "messages": [
            {
                "role": msg.role,
                "content": {
                    "type": "text",
                    "text": msg.content.text if isinstance(msg.content, types.TextContent) else ""
                }
            } for msg in message.messages
        ]
    })

    # Run llama3 with Ollama
    result = subprocess.run(
        ["ollama", "run", "llama3"],
        input=input_json,
        capture_output=True,
        text=True
    )

    return types.CreateMessageResult(
        role="assistant",
        content=types.TextContent(type="text", text=result.stdout.strip()),
        model="llama3",
        stopReason="endTurn"
    )
