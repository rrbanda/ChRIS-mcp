FROM registry.access.redhat.com/ubi9/python-311:latest

WORKDIR /app
COPY mcp_server /app/mcp_server
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

CMD ["uvicorn", "mcp_server.server:app", "--host", "0.0.0.0", "--port", "8080"]
