# app.py

import streamlit as st
import subprocess
import json
import requests

# Constants
CHRIS_URL = "http://localhost:8000"

st.set_page_config(page_title="ChRIS MCP Chatbot", layout="wide")
st.title("🧠 ChRIS MCP LLM Chatbot")
st.markdown("Use natural language to explore ChRIS plugins and data.")

# Get ChRIS credentials
username = st.text_input("ChRIS Username", "chris")
password = st.text_input("ChRIS Password", type="password")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display previous messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Prompt
prompt = st.chat_input("Ask something like 'List plugins' or 'Get plugin instance 2'")
if prompt:
    # Show user message
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Run prompt through LLM (Ollama)
    chat_payload = {
        "messages": [
            {"role": "user", "content": "Here is what the user wants to do:"},
            {"role": "user", "content": prompt}
        ]
    }

    ollama_proc = subprocess.run(
        ["ollama", "run", "llama3"],
        input=json.dumps(chat_payload),
        text=True,
        capture_output=True
    )

    llm_reply = ollama_proc.stdout.strip()

    # Check if this is a supported MCP tool instruction
    tool_output = ""
    if "list plugins" in prompt.lower():
        try:
            response = requests.get(f"{CHRIS_URL}/api/v1/plugins/", auth=(username, password))
            response.raise_for_status()
            plugins = response.json().get("results", [])
            plugin_names = [plugin["name"] for plugin in plugins]
            tool_output = "**🔧 Available ChRIS Plugins:**\n\n" + "\n".join(f"- {p}" for p in plugin_names)
        except Exception as e:
            tool_output = f"❌ Failed to fetch plugins: {str(e)}"

    # Combine both LLM reply and MCP tool output
    full_reply = llm_reply
    if tool_output:
        full_reply += "\n\n" + tool_output

    # Display assistant response
    st.chat_message("assistant").markdown(full_reply)
    st.session_state.messages.append({"role": "assistant", "content": full_reply})
