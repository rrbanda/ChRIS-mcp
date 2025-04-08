import asyncio
import subprocess
import os
import json
from llama_index.tools.mcp import BasicMCPClient, McpToolSpec
from llama_index.core.agent.workflow import ReActAgent
from llama_index.llms.ollama import Ollama

# === CONFIGURATION ===
MCP_URL = os.environ.get("MCP_URL", "http://localhost:3001/sse")
MODEL_NAME = os.environ.get("LLM_MODEL", "llama3.2")
TEMPERATURE = float(os.environ.get("LLM_TEMPERATURE", "0.7"))

# === AGENT SETUP ===
async def setup_agent():
    print(f"🔌 Connecting to MCP server at {MCP_URL}")
    mcp_client = BasicMCPClient(MCP_URL)

    print("🧰 Fetching available tools...")
    tools = await McpToolSpec(client=mcp_client).to_tool_list_async()
    print(f"✅ Found {len(tools)} tools:")
    for tool in tools:
        print(f" • {tool.metadata.name}: {tool.metadata.description}")

    print(f"🤖 Initializing Ollama with model: {MODEL_NAME}")
    llm = Ollama(model=MODEL_NAME, temperature=TEMPERATURE)

    agent = ReActAgent(
        name="ChRISAgent",
        llm=llm,
        tools=tools,
        system_prompt="You are an assistant for the ChRIS medical image platform.",
        temperature=TEMPERATURE,
    )
    return agent, mcp_client

# === TOOL ROUTER WITH ARGUMENT INJECTION ===
def route_tool_and_args(query: str, tools: list) -> tuple[str, dict]:
    tool_descriptions = "\n".join(
        f"- {tool.metadata.name}: {tool.metadata.description}" for tool in tools
    )

    prompt = f"""
You are a routing assistant for MCP tools.

Available tools:
{tool_descriptions}

User question:
"{query}"

Respond in this exact JSON format (no preamble or comments):
{{
  "tool": "<tool_name>",
  "args": {{
    ... any arguments to pass to the tool ...
  }}
}}
""".strip()

    print("🧭 Routing tool and extracting args using Llama3...")
    result = subprocess.run(["ollama", "run", MODEL_NAME], input=prompt, capture_output=True, text=True)
    
    try:
        parsed = json.loads(result.stdout.strip())
        tool_name = parsed["tool"]
        args = parsed.get("args", {})
        print(f"📦 Routed to: {tool_name} with args: {args}")
        return tool_name, args
    except Exception as e:
        print(f"❌ Failed to parse routing response: {result.stdout}")
        raise e

# === SUMMARY FUNCTION ===
def summarize_output(output: str) -> str:
    summary_prompt = f"Summarize this ChRIS API output:\n\n{output}"
    result = subprocess.run(["ollama", "run", MODEL_NAME], input=summary_prompt, capture_output=True, text=True)
    return result.stdout.strip()

# === MAIN CHAT LOOP ===
async def main():
    print("\n💬 Welcome to the ChRIS Natural Language MCP Client!")
    print("Ask questions like:")
    print("  • What's at the root of the ChRIS API?")
    print("  • What plugins are available?")
    print("  • Show me plugin instance 2\n")

    agent, mcp = await setup_agent()

    while True:
        try:
            query = input("🧠 Ask: ").strip()
            if not query:
                continue
            if query.lower() in {"exit", "quit"}:
                print("👋 Goodbye!")
                break

            # Step 1: Route tool + extract args
            tool, args = route_tool_and_args(query, agent.tools)

            # Step 2: Call tool via MCP
            print(f"🚀 Calling `{tool}` tool via MCP...")
            response = await mcp.call_tool(tool, arguments={"args": args})
            print("🗂️ Raw output received.")

            # Step 3: Summarize
            summary = summarize_output(response)
            print("\n📋 Summary:\n", summary)

        except Exception as e:
            print(f"❌ Error: {e}")

# === ENTRY POINT ===
if __name__ == "__main__":
    asyncio.run(main())
# === ENTRY POINT ===
def run():
    asyncio.run(main())

if __name__ == "__main__":
    run()
