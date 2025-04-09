FROM registry.access.redhat.com/ubi9/python-311:latest

WORKDIR /app

# Copy code and install deps
COPY mcp_server /app/mcp_server
COPY requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir -r /app/requirements.txt

EXPOSE 3001

# 🟢 Start the FastAPI MCP server
CMD ["uvicorn", "mcp_server.server:app", "--host", "0.0.0.0", "--port", "3001"]
