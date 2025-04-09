# app.py
import os
import json
import asyncio
import subprocess
import streamlit as st
from llama_index.tools.mcp import BasicMCPClient, McpToolSpec
from llama_index.llms.ollama import Ollama
from llama_index.core.agent.workflow import ReActAgent

# === CONFIG ===
MCP_URL = "https://chris-mcp-server-llama-stack.apps.prod.rhoai.rh-aiservices-bu.com/sse"
MODEL_NAME = "llama3"
TEMPERATURE = 0.7

# Optional config injection
CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.json")
CONFIG = {}
if os.path.exists(CONFIG_PATH):
    with open(CONFIG_PATH) as f:
        CONFIG = json.load(f)

@st.cache_resource
def setup_agent():
    mcp_client = BasicMCPClient(MCP_URL)
    tools = asyncio.run(McpToolSpec(client=mcp_client).to_tool_list_async())
    llm = Ollama(model=MODEL_NAME, temperature=TEMPERATURE)
    agent = ReActAgent(
        name="ChRISAgent",
        llm=llm,
        tools=tools,
        system_prompt="You are an assistant for the ChRIS medical image platform.",
        temperature=TEMPERATURE,
    )
    return agent, mcp_client, tools

def route_tool_and_args(query, tools):
    tool_list = "\n".join(f"- {t.metadata.name}: {t.metadata.description}" for t in tools)
    routing_prompt = f"""
Available tools:
{tool_list}

User query:
"{query}"

Respond in this exact JSON format (no commentary):
{{
  "tool": "<tool_name>",
  "args": {{
    ... tool arguments ...
  }}
}}
""".strip()

    result = subprocess.run(["ollama", "run", MODEL_NAME], input=routing_prompt, capture_output=True, text=True)
    try:
        parsed = json.loads(result.stdout.strip())
        tool = parsed["tool"]
        args = parsed.get("args", {})
        # Inject missing args from config
        for key in ["url", "username", "password"]:
            if key not in args and key in CONFIG:
                args[key] = CONFIG[key]
        return tool, args
    except Exception as e:
        st.error(f"Routing failed: {e}")
        st.text(result.stdout)
        return None, {}

def summarize_output(raw):
    prompt = f"Summarize this ChRIS API response:\n\n{raw}"
    result = subprocess.run(["ollama", "run", MODEL_NAME], input=prompt, capture_output=True, text=True)
    return result.stdout.strip()

# === Streamlit UI ===
st.set_page_config(page_title="ChRIS + MCP via LlamaStack", layout="wide")
st.title("🧠 ChRIS Agent with LlamaStack")

agent, mcp, tools = setup_agent()

query = st.text_input("Ask a question about ChRIS:", placeholder="e.g. What plugins are available?")

if query:
    with st.spinner("Routing query and executing tool..."):
        tool, args = route_tool_and_args(query, tools)
        if tool:
            st.markdown(f"🔧 Tool: `{tool}`")
            st.json(args)

            try:
                response = asyncio.run(mcp.call_tool(tool, {"args": args}))
                raw_output = str(response)
                st.subheader("📄 Raw Output")
                st.code(raw_output, language="json")

                summary = summarize_output(raw_output)
                st.subheader("📝 Summary")
                st.success(summary)
            except Exception as e:
                st.error(f"❌ Error calling tool: {e}")
