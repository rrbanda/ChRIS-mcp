# test_mcp_client.py
import subprocess
import json

request = {
    "jsonrpc": "2.0",
    "id": 2,
    "method": "run_plugin",
    "params": {
        "username": "chris",
        "password": "chris1234",
        "plugin_id": 1,
        "input_dir": "home/chris/uploads/testdir"
    }
}

proc = subprocess.Popen(
    ["python", "-m", "mcp_server.entrypoint"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True
)

try:
    stdout, stderr = proc.communicate(json.dumps(request) + "\n", timeout=10)
    print("STDOUT:", stdout)
    print("STDERR:", stderr)
except subprocess.TimeoutExpired:
    proc.kill()
    print("❌ MCP server took too long to respond.")
