# 🛠️ Guide: Building an MCP Server in Python

This guide walks you through creating an MCP-compatible tool server using the [MCP SDK for Python](https://pypi.org/project/mcp/).

---

##  Prerequisites

- Python 3.10+
- [uv](https://github.com/astral-sh/uv) package manager (recommended)
- MCP SDK `1.2.0` or higher
- Internet access (for API requests)

---

## 📁 Step 1: Set Up Your Project

```bash
# Initialize a new Python project
uv init myserver
cd myserver

# Create a virtual environment and activate it
uv venv
source .venv/bin/activate

# Install dependencies (including MCP CLI + HTTPX)
uv add "mcp[cli]" httpx
````

---

## 🧠 Step 2: Create Your MCP Server Script

```bash
touch server.py
```

Use the following starter code:

```python
from typing import Any
import httpx
from mcp.server.fastmcp import FastMCP

# Initialize MCP server
mcp = FastMCP("myserver")

# Example constant
USER_AGENT = "my-mcp-server/1.0"
```

---

## 🧰 Step 3: Add Helper Functions

```python
async def make_request(url: str) -> dict[str, Any] | None:
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/json"
    }
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, timeout=30.0)
            response.raise_for_status()
            return response.json()
        except Exception:
            return None

def format_response(data: dict[str, Any]) -> str:
    return f"Response keys: {', '.join(data.keys())}"
```

---

## 🧩 Step 4: Define MCP Tools

```python
@mcp.tool()
async def sample_tool(query: str) -> str:
    """Example tool to query a remote API."""
    url = f"https://api.example.com/search?q={query}"
    data = await make_request(url)

    if not data:
        return "Failed to retrieve data."

    return format_response(data)
```

You can define as many tools as you like using the `@mcp.tool()` decorator.

---

## 🚀 Step 5: Run the Server

At the bottom of `server.py`, add:

```python
if __name__ == "__main__":
    mcp.run(transport="stdio")
```

Then run:

```bash
uv run server.py
```

---

## 🧪 Example: Weather Server

Here’s a real-world tool you can add:

```python
NWS_API_BASE = "https://api.weather.gov"

@mcp.tool()
async def get_alerts(state: str) -> str:
    url = f"{NWS_API_BASE}/alerts/active/area/{state}"
    data = await make_request(url)

    if not data or "features" not in data:
        return "No alerts found."

    return f"{len(data['features'])} alert(s) found."
```

---

## 📦 Deployment

Your server is now ready to be called by an MCP agent via stdio or HTTP (if extended). You can:

* Package this as a plugin
* Wrap it in a Docker container
* Deploy in agent workflows (e.g., for RAG or clinical AI tools)

---

## 📚 References

* [MCP SDK on PyPI](https://pypi.org/project/mcp/)
* [httpx Docs](https://www.python-httpx.org/)
* [FastMCP GitHub](https://github.com/mcp-lang/mcp)

```


