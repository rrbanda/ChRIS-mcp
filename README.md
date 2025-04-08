Got it! Here's the full README.md content as a single Markdown document — ready for you to copy-paste into your project folder:

# 🧠 ChRIS MCP Server — LLM-Powered Tool Invocation

This MCP server lets you ask natural language questions about the [ChRIS API](https://chrisproject.org/), and routes them to actual tools like `get_chris_root` using a local LLM (Ollama + Mistral).

---

## ✅ Features

- 💬 Ask things like: “What is the root endpoint of ChRIS?”
- 🧠 Uses [Mistral](https://ollama.com/library/mistral) via [Ollama](https://ollama.com)
- 🛠 Dynamically calls real MCP tools (e.g. `get_chris_root`)
- 🧪 Works with [MCP Inspector UI](https://github.com/modelcontext/mcp)

---

## 📦 Requirements

- Python 3.10+
- [Ollama](https://ollama.com/download) (for LLM)
- `mcp` library (`pip install mcp`)
- `uvicorn` (for running the server)
- Optional: [`uv`](https://github.com/astral-sh/uv) for modern Python workflows

---

## 🔧 Setup

# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install mcp requests html2text beautifulsoup4 uvicorn
Make sure you have mistral pulled locally:

ollama pull mistral
▶️ Run the MCP Server
From the mcp_server/ folder:

uv run -- server.py
Or if you're not using uv:

python server.py
Your server will be available at:

http://localhost:8000/sse
🧪 Test with MCP Inspector
1. Run in development mode
mcp dev server.py
This launches:

🧠 MCP Inspector UI: http://localhost:5173

🔁 SSE endpoint: http://localhost:3000/sse

2. Open Inspector in your browser
Go to http://localhost:5173

3. Call the chris_chat Tool
Use the following input:

{
  "args": {
    "query": "What is the root endpoint of the ChRIS API?"
  }
}
✅ You should see a structured response from the real ChRIS API.

🧩 Available Tools
get_chris_root
Fetches the root Collection+JSON from ChRIS (e.g. https://cube.chrisproject.org/api/v1/)

chris_chat
Natural language interface that uses mistral to decide which tool to run (currently just get_chris_root)

🛠️ Add More Tools
Example: add a list_plugins tool

@mcp.tool()
def list_plugins(args: Dict[str, Any]) -> str:
    url = "https://cube.chrisproject.org/api/v1/plugins/"
    response = requests.get(url)
    return json.dumps(response.json(), indent=2)
Then update chris_chat logic to:

if "plugins" in query:
    return list_plugins(args={})
🧠 How It Works
You call chris_chat with a natural language query.

It sends the query to ollama run mistral.

Based on LLM output, it chooses a tool (e.g. get_chris_root)

It calls that tool and returns the result.

🙋 Need Help?
Want to:

Add support for multiple tools?

Build a frontend chatbot UI?

Add tool chaining or streaming?

Just ask — we can extend this step by step.

© 2025 — Made with 🧠 and 🔧 for AI + ChRIS


---

Let me know if you’d like a matching `Makefile`, `.env.example`, or a `client.py` test script added to this!