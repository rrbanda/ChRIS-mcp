import sys
import os
import json
import time
import logging
from typing import Dict, Any

import httpx
import yaml

from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route, Mount

from mcp.server.fastmcp import FastMCP
from mcp.server.sse import SseServerTransport
from mcp.shared.exceptions import McpError
from mcp.types import ErrorData, INVALID_PARAMS

# ─────────────── Pipeline Spec ───────────────
PIPELINE_DEF = {
    "name": "Leg Length Discrepancy Full Workflow v20240705",
    "plugin_tree": [
        {"title": "root-0", "plugin": "pl-simpledsapp v2.1.0", "previous": None},
        {"title": "dcm-to-mha-1", "plugin": "pl-dcm2mha_cnvtr v1.2.24", "previous": "root-0"},
        {"title": "joiner-2", "plugin": "pl-tsjoiner v1.1.3", "previous": "dcm-to-mha-1"},
        {"title": "segmentor-3", "plugin": "pl-legseg v2.3.9", "previous": "joiner-2"},
        {"title": "analyzer-4", "plugin": "pl-legmeasure v3.1.7", "previous": "segmentor-3"}
    ]
}

# In-memory job store
JOBS: Dict[str, Any] = {}

# Add current folder to sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("chris-server")

# === Helpers ===
def wrap_tool_output(tool_name: str, payload: Any) -> str:
    return json.dumps({
        "tool": tool_name,
        "output": payload,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
    }, indent=2)

# === MCP Server & Tools ===
mcp = FastMCP("ChRIS MCP Server 🚀", dependencies=["httpx"])
sse = SseServerTransport("/messages/")

@mcp.tool(name="list_chris_plugins", description="List plugins from ChRIS Cube")
async def list_chris_plugins(limit: int = 5) -> str:
    url = "https://cube.chrisproject.org/api/v1/plugins/"
    headers = {"Accept": "application/vnd.collection+json"}
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(url, params={"limit": limit}, headers=headers, timeout=10.0)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            return wrap_tool_output("list_chris_plugins", {"error": str(e)})
    items = data.get("collection", {}).get("items", [])
    plugins = [{d["name"]: d["value"] for d in item.get("data", [])} for item in items]
    return wrap_tool_output("list_chris_plugins", {"plugins": plugins})

@mcp.tool(
    name="get_pacs_image",
    description="Grab a PACS image URL by patient MRN (defaults to 12345)"
)
async def get_pacs_image(mrn: str = "12345") -> str:
    url = f"https://fakepacs.org/images/{mrn}.png"
    return wrap_tool_output("get_pacs_image", {"url": url})

@mcp.tool(
    name="run_pipeline",
    description="Kick off the full LLD pipeline for a given patient MRN (defaults to 12345)"
)
async def run_pipeline(mrn: str = "12345") -> str:
    job_id = f"job-{int(time.time())}"
    JOBS[job_id] = {
        "pipeline_id": PIPELINE_DEF["name"],
        "input_data": {"mrn": mrn},
        "steps": PIPELINE_DEF["plugin_tree"],
        "start_time": time.time()
    }
    return wrap_tool_output("run_pipeline", {"job_id": job_id})

@mcp.tool(name="get_job_status", description="Get status of a job with step delays")
async def get_job_status(job_id: str) -> str:
    job = JOBS.get(job_id)
    if not job:
        return wrap_tool_output("get_job_status", {"error": "job not found"})
    steps = job["steps"]
    elapsed = time.time() - job["start_time"]
    per_step = 30
    idx = min(int(elapsed // per_step), len(steps) - 1)
    completed = elapsed >= per_step * len(steps)
    status = "COMPLETED" if completed else "RUNNING"
    step_num = len(steps) if completed else (idx + 1)
    title = steps[-1]["title"] if completed else steps[idx]["title"]
    pct = int(step_num / len(steps) * 100)
    return wrap_tool_output("get_job_status", {
        "job_id": job_id,
        "status": status,
        "step": step_num,
        "total_steps": len(steps),
        "step_title": title,
        "percent_complete": pct
    })

# === SSE & REST Endpoints ===
async def handle_sse(request: Request):
    async with sse.connect_sse(request.scope, request.receive, request._send) as (r, w):
        await mcp._mcp_server.run(r, w, mcp._mcp_server.create_initialization_options())

async def api_root(request: Request):
    return JSONResponse({"status": "ok", "tools": list(mcp._tool_registry.keys())})

async def pacs_endpoint(request: Request):
    mrn = request.path_params["mrn"]
    return JSONResponse(json.loads(await get_pacs_image(mrn)))

async def pipeline_run(request: Request):
    return JSONResponse(json.loads(await run_pipeline()))

async def job_status(request: Request):
    job_id = request.path_params["job_id"]
    return JSONResponse(json.loads(await get_job_status(job_id)))

app = Starlette(
    debug=True,
    routes=[
        Route("/sse", handle_sse),
        Route("/api/v1/", api_root),
        Route("/api/v1/pacs/{mrn}", pacs_endpoint, methods=["GET"]),
        Route("/api/v1/pipeline/run/{pipeline_id}", pipeline_run, methods=["POST"]),
        Route("/api/v1/job/status/{job_id}", job_status, methods=["GET"]),
        Mount("/messages/", app=sse.handle_post_message),
    ],
)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8096)
