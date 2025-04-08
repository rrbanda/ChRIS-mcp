# 🧠 ChRIS-Assistant

An AI-powered CLI assistant for exploring the [ChRIS](https://chrisproject.org) medical image platform using natural language.

This tool connects to a running [ChRIS MCP Server](https://github.com/FNNDSC), dynamically fetches its tools, and uses [Ollama](https://ollama.com) with [Llama3](https://llama.meta.com/llama3/) to route questions and summarize responses.

---

## 🚀 Features

- 🔌 Connects to any MCP-compatible ChRIS server over SSE
- 🤖 Uses `llama3` via Ollama to understand natural questions
- 🧠 Automatically selects the right ChRIS API tool
- 🧾 Summarizes JSON output into plain English
- 🧰 Built with [llama-index](https://github.com/jerryjliu/llama_index) + [mcp](https://github.com/FNNDSC/mcp)

---

## 📦 Installation

### 1. Clone and install locally (dev mode)

```bash
git clone https://github.com/YOUR_GITHUB/chris-assistant.git
cd chris-assistant
pip install -e .
```

### 2. Or install via PyPI (once published)

```bash
pip install chris-assistant
```

---

## 💬 Usage

Make sure you have [Ollama](https://ollama.com) running and the ChRIS MCP server accessible:

```bash
OLLAMA_HOST=localhost:11434 \
MCP_URL=http://localhost:3001/sse \
LLM_MODEL=llama3.2 \
chris-assistant
```

---

## 💡 Example Questions

```text
What's at the root of the ChRIS API?
List available plugins
Show me plugin instance 2
```

---

## ⚙️ Environment Variables

| Variable      | Description                              | Default                |
|---------------|------------------------------------------|------------------------|
| `MCP_URL`     | MCP server SSE endpoint                  | `http://localhost:3001/sse` |
| `OLLAMA_HOST` | Ollama runtime (local model endpoint)    | `localhost:11434`      |
| `LLM_MODEL`   | LLM model name (e.g. `llama3.2`)          | `llama3.2`             |

---

## 📚 Project Layout

```bash
chris_assistant/
├── chris_assistant/
│   └── cli.py        # Main CLI logic
├── pyproject.toml    # Packaging config
├── README.md
```

---

## 📜 License

MIT © [Your Name]
```

---
