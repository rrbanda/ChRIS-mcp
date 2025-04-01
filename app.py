# app.py

import streamlit as st
import subprocess
import json
import requests

CHRIS_URL = "http://localhost:8000"
MCP_CHAT_TOOL_URL = "http://localhost:3000/tool/chris_tool_chat"

st.set_page_config(page_title="🧠 ChRIS MCP LLM Chatbot", layout="wide")
st.title("🧠 ChRIS MCP LLM Chatbot")
st.markdown("Use natural language to explore ChRIS plugins and data.")

# 🔐 Credentials
username = st.text_input("ChRIS Username", value="chris")
password = st.text_input("ChRIS Password", type="password")

# 💬 Chat history state
if "messages" not in st.session_state:
    st.session_state.messages = []

# 📜 Render previous messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# ➕ New user input
prompt = st.chat_input("Ask something like 'List plugins' or 'Show instance 2'")
if prompt:
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # 🚀 Call MCP smart tool
    try:
        payload = {
            "message": prompt,
            "username": username,
            "password": password
        }
        response = requests.post(MCP_CHAT_TOOL_URL, json=payload, timeout=15)
        response.raise_for_status()
        mcp_messages = response.json()

        # 🔁 Add all returned messages to chat
        full_response = ""
        for msg in mcp_messages:
            content = msg.get("content", "")
            role = msg.get("role", "assistant")
            if role == "assistant":
                full_response += content + "\n\n"

        st.chat_message("assistant").markdown(full_response.strip())
        st.session_state.messages.append({"role": "assistant", "content": full_response.strip()})

    except Exception as e:
        error_msg = f"❌ MCP call failed: {str(e)}"
        st.chat_message("assistant").markdown(error_msg)
        st.session_state.messages.append({"role": "assistant", "content": error_msg})
