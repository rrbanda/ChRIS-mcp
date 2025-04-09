# --- Stage 1: Install Python and dependencies ---
    FROM registry.access.redhat.com/ubi9/python-311 as builder

    WORKDIR /app
    
    # Copy only requirements to leverage Docker caching
    COPY requirements.txt .
    
    # Install dependencies
    RUN pip install --upgrade pip && \
        pip install --no-cache-dir -r requirements.txt
    
    # --- Stage 2: Final image using UBI minimal ---
    FROM registry.access.redhat.com/ubi9/ubi-minimal
    
    WORKDIR /app
    
    # Copy dependencies from builder
    COPY --from=builder /usr/lib64 /usr/lib64
    COPY --from=builder /usr/local/lib /usr/local/lib
    COPY --from=builder /usr/local/bin /usr/local/bin
    COPY --from=builder /usr/lib /usr/lib
    
    # Copy your actual MCP server code
    COPY mcp_server /app/mcp_server
    
    # Set entrypoint
    ENTRYPOINT ["uvicorn", "mcp_server.server:app", "--host", "0.0.0.0", "--port", "8080"]
    
    EXPOSE 8080
    