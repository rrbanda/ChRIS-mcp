import os
import streamlit as st
import uuid
from llama_stack_client import LlamaStackClient
from llama_stack_client.types.agent_create_params import AgentConfig
from llama_stack_client.lib.agents.agent import Agent

# === CONFIG ===
LLAMASTACK_BASE_URL = os.getenv("LLAMASTACK_BASE_URL", "https://llama-stack-llama-stack.apps.prod.rhoai.rh-aiservices-bu.com")
MCP_TOOLGROUP = "mcp::chris"

# === INIT ===
client = LlamaStackClient(base_url=LLAMASTACK_BASE_URL)

# === GET MODEL ===
try:
    models = client.models.list()
    model = next((m.identifier for m in models if m.api_model_type == "llm"), None)
    if not model:
        st.error("No LLM model found.")
        st.stop()
except Exception as e:
    st.error(f"Could not connect to LlamaStack: {e}")
    st.stop()

# === AGENT SETUP ===
agent_config = AgentConfig(
    model=model,
    instructions="You are a helpful AI assistant for the ChRIS medical image analysis platform. Use tools when needed.",
    toolgroups=[MCP_TOOLGROUP],
    sampling_params={"max_tokens": 1024}
)

agent = Agent(client=client, agent_config=agent_config)
session_id = agent.create_session(f"chat-{uuid.uuid4()}")

# === UI ===
st.set_page_config(page_title="ChAI - ChRIS Assistant", page_icon="🧠")
st.title("🧠 ChAI - Medical Image Assistant")

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "👋 Hi! Ask me anything about ChRIS and I’ll use tools if needed."}
    ]

# === RENDER CHAT HISTORY ===
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# === INPUT PROMPT ===
prompt = st.chat_input("Ask a question about ChRIS (e.g., what plugins exist?)")

if prompt:
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # === RUN TURN ===
    turn = agent.create_turn(
        messages=[{"role": "user", "content": prompt}],
        session_id=session_id,
        stream=True
    )

    def response_stream():
        full = ""
        for chunk in turn:
            if chunk.event and getattr(chunk.event, "payload", None):
                payload = chunk.event.payload

                if payload.event_type == "step_progress":
                    delta = getattr(payload.delta, "text", "")
                    full += delta
                    yield delta

                elif payload.event_type == "step_complete":
                    if payload.step_details.step_type == "tool_execution":
                        name = payload.step_details.tool_calls[0].tool_name
                        out = payload.step_details.tool_responses[0].content
                        yield f"\n\n✅ Tool `{name}` executed.\n```json\n{out}\n```"

            elif getattr(chunk, "error", None):
                yield f"\n\n❌ Error: {chunk.error.get('message', 'Unknown error')}"

        st.session_state.messages.append({"role": "assistant", "content": full or "✅ Tool executed."})

    with st.chat_message("assistant"):
        st.write_stream(response_stream())
