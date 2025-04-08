# 🧠 ChRIS MCP Server — LLM-Powered Tool Invocation

This is an MCP server that uses natural language queries to call real tools from the [ChRIS API](https://chrisproject.org/), powered by [Ollama](https://ollama.com) running the `mistral` model.

## ✅ Features

- 💬 Natural language queries like “What is the root endpoint of ChRIS?”
- 🔁 Routes to actual tools (e.g., `get_chris_root`)
- 🧠 Uses local LLM via `ollama run mistral`
- 🧪 Fully testable using MCP Inspector UI

---

## 📦 Requirements

- Python 3.10+
- [Ollama](https://ollama.com/download) (must be installed locally)
- Mistral model pulled locally via `ollama pull mistral`
- MCP Python SDK: `pip install mcp`
- `uvicorn` or `uv` for running the FastAPI/Starlette app

---

## 🔧 Setup

```bash
# Clone the repo or cd into your server folder
cd mcp_server

# Set up a virtual environment
python -m venv .venv
source .venv/bin/activate

# Install Python dependencies
pip install mcp requests html2text beautifulsoup4 uvicorn

# Pull the LLM (Mistral) via Ollama
ollama pull mistral
```

---

## 🚀 Run the MCP Server

You can use `uv` (recommended) or plain Python:

```bash
uv run -- server.py
# or
python server.py
```

The server will be running at:

```
http://localhost:8000/sse
```

---

## 🧪 Test via MCP Inspector

Open a new terminal and run:

```bash
mcp dev server.py
```

Then open the MCP Inspector UI in your browser:

```
http://localhost:5173
```

### Example Input (chris_chat tool)

```json
{
  "args": {
    "query": "What is the root endpoint of the ChRIS API?"
  }
}
```

If LLM replies with a valid tool (like `get_chris_root`), the server will call that tool and return the actual API result from:

```
https://cube.chrisproject.org/api/v1/
```

---

## 🔧 Available Tools

### `get_chris_root`

Fetches the root Collection+JSON document from a ChRIS instance (defaults to https://cube.chrisproject.org/api/v1/).

### `chris_chat`

Accepts natural language `query`, uses `ollama run mistral` to determine the correct tool (e.g., `get_chris_root`), and then executes it.

---

## 🛠️ Add More Tools (Optional)

To expand your server:

```python
@mcp.tool()
def list_plugins(args: Dict[str, Any]) -> str:
    response = requests.get("https://cube.chrisproject.org/api/v1/plugins/")
    return json.dumps(response.json(), indent=2)
```

Then enhance `chris_chat` logic to call it based on query intent.

---

## 💡 Debug Tips

- If you get `"No matching tool"`, the LLM likely returned a name that’s not registered.
- To improve reliability, use a strict prompt like:

```python
"You are a tool router. Valid tools: get_chris_root. Only respond with one tool name."
```

---