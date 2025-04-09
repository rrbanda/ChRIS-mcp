FROM registry.access.redhat.com/ubi9/python-311:latest

WORKDIR /app

# Copy your MCP server code
COPY mcp_server /app/mcp_server
COPY requirements.txt .

# 🟡 Install MCP SDK from GitHub (FastMCP)
RUN pip install --no-cache-dir "mcp[fastmcp] @ git+https://github.com/ml-explore/mcp.git"

# ✅ Install your app requirements
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 3001

# ✅ Run the FastMCP server
CMD ["uvicorn", "mcp_server.server:app", "--host", "0.0.0.0", "--port", "3001"]
