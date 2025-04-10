import os
import uuid
import json
import streamlit as st
from llama_stack_client import LlamaStackClient, Agent

# === CONFIG ===
BASE_URL = os.getenv("REMOTE_BASE_URL", "https://llama-stack-llama-stack.apps.prod.rhoai.rh-aiservices-bu.com")
TOOL_DEBUG = os.getenv("TOOL_DEBUG", "0") == "1"

# === INIT CLIENT ===
client = LlamaStackClient(base_url=BASE_URL)

# === FETCH MODELS & MCP SERVERS ===
try:
    models = client.models.list()
    model_ids = [m.identifier for m in models if m.api_model_type == "llm"]
    toolgroups = [tg.identifier for tg in client.toolgroups.list() if tg.identifier.startswith("mcp::")]
    connected = True
except Exception as e:
    models = []
    toolgroups = []
    model_ids = []
    connected = False
    st.error(f"❌ Could not connect to LlamaStack: {e}")

# === SIDEBAR CONFIG ===
with st.sidebar:
    st.title("🔌 LlamaStack")
    if connected:
        st.success("✅ Connected to LlamaStack")
    else:
        st.error("❌ Connection failed")

    selected_model = st.selectbox("Model:", model_ids) if model_ids else ""
    selected_toolgroups = st.multiselect("MCP Servers:", toolgroups, default=toolgroups)

# === AGENT (cached) ===
@st.cache_resource
def create_agent(model_id, tools):
    return Agent(
        client=client,
        model=model_id,
        instructions="You are a helpful agent for ChRIS. Use MCP tools if needed and summarize clearly.",
        tools=tools,
        sampling_params={"max_tokens": 1024}
    )

agent = create_agent(selected_model, selected_toolgroups)

# === SESSION STATE ===
if "session_id" not in st.session_state:
    st.session_state.session_id = agent.create_session(f"chat-{uuid.uuid4()}")

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "👋 Hi! Ask me anything about ChRIS — I’ll use the right tool if needed."}
    ]

# === MAIN UI ===
st.title("🧠 ChAI - Medical Image Analysis Assistant")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

prompt = st.chat_input("Ask a question about ChRIS...")

if prompt:
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    turn = agent.create_turn(
        session_id=st.session_state.session_id,
        messages=[{"role": "user", "content": prompt}],
        stream=True
    )

    def stream_response():
        full_response = ""
        for chunk in turn:
            if chunk.event and hasattr(chunk.event, "payload"):
                payload = chunk.event.payload

                if payload.event_type == "step_progress":
                    delta = getattr(payload.delta, "text", "")
                    if delta:
                        full_response += delta
                        yield delta

                elif payload.event_type == "step_complete":
                    step = payload.step_details
                    if step.step_type == "tool_execution":
                        tool_name = step.tool_calls[0].tool_name
                        tool_output_raw = step.tool_responses[0].content

                        try:
                            parsed = json.loads(tool_output_raw)
                            pretty_output = json.dumps(parsed, indent=2)
                        except Exception:
                            pretty_output = tool_output_raw

                        debug_block = (
                            f"\n\n✅ **Tool**: `{tool_name}`\n"
                            f"📤 **Output**:\n```json\n{pretty_output}\n```"
                            if TOOL_DEBUG else f"\n\n✅ Tool `{tool_name}` executed."
                        )
                        yield debug_block

            elif getattr(chunk, "error", None):
                yield f"\n\n❌ Error: {chunk.error.get('message', 'Unknown error')}"

        if full_response.strip() == "":
            full_response = "✅ Tool executed, but no direct reply was generated."

        st.session_state.messages.append({"role": "assistant", "content": full_response})

    with st.chat_message("assistant"):
        st.write_stream(stream_response())
