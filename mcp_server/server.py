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
PIPELINE_YAML = r"""
authors: Rudolph Pienaar <dev@babymri.org>
name: "Leg Length Discrepancy Full Workflow v20240705"
description: "Perform the full leg length workflow, including joins"
category: Imaging
locked: false
plugin_tree:
  - title: root-0
    plugin: pl-simpledsapp v2.1.0
    previous: ~
  - title: dcm-to-mha-1
    plugin: pl-dcm2mha_cnvtr v1.2.24
    previous: root-0
    plugin_parameter_defaults:
      inputFileFilter: "**/*.dcm"
      rotate: 90
      imageName: 'composite.png'
      filterPerc: 30
  - title: generate-landmark-heatmaps-2
    plugin: pl-lld_inference v2.2.11
    previous: dcm-to-mha-1
    plugin_parameter_defaults:
      inputFileFilter: "**/*.mha"
      heatmapThreshold: '0.5'
  - title: heatmaps-join-root-3
    plugin: pl-topologicalcopy v1.0.2
    previous: root-0
    plugin_parameter_defaults:
      plugininstances: root-0,generate-landmark-heatmaps-2
      filter: \.dcm$,\.csv$
  - title: landmarks-to-json-4
    plugin: pl-csv2json v1.2.4
    previous: heatmaps-join-root-3
    plugin_parameter_defaults:
      inputFileFilter: "**/*.csv"
      outputFileStem: "prediction"
      addTags: "PatientID,PatientName,PatientAge,StudyDate"
  - title: heatmaps-join-json-5
    plugin: pl-topologicalcopy v1.0.2
    previous: landmarks-to-json-4
    plugin_parameter_defaults:
      plugininstances: generate-landmark-heatmaps-2,landmarks-to-json-4
      filter: \.jpg$,\.json$
  - title: measure-leg-segments-6
    plugin: pl-markimg v1.4.8
    previous: heatmaps-join-json-5
    plugin_parameter_defaults:
      inputImageName: "input.jpg"
      pointMarker: "."
      pointSize: 10
      linewidth: 0.5
      lineGap: 70
      addText: "Not for diagnostic use"
      addTextPos: bottom
      addTextSize: 5
      addTextColor: darkred
  - title: measurement-join-dicom-7
    plugin: pl-topologicalcopy v1.0.2
    previous: heatmaps-join-root-3
    plugin_parameter_defaults:
      plugininstances: heatmaps-join-root-3,measure-leg-segments-6
      filter: \.dcm$,\.png$
  - title: image-to-DICOM-8
    plugin: pl-dicommake v2.3.2
    previous: measurement-join-dicom-7
    plugin_parameter_defaults:
      filterIMG: "**/*.png"
      outputSubDir: data
      thread: true
  - title: pacs-push-9
    plugin: pl-dicom_dirsend v1.1.2
    previous: image-to-DICOM-8
    plugin_parameter_defaults:
      fileFilter: "dcm"
      host: 0.0.0.0
      port: 104
      aetTitle: "SYNAPSERESEARCH"
"""
PIPELINE_DEF = yaml.safe_load(PIPELINE_YAML)

# ─────────────── Report Stub ───────────────
REPORT_JSON = {
  "data": {
    "61928-1.2.250.1.118.3.1305.235.1.8008.46.1727122139": {
      "info": {
        "PatientID": "71054xfdsar",
        "PatientName": "SMITH^JANE",
        "PatientAge": "012Y",
        "StudyDate": "20240923"
      },
      "femur": {
        "Right_femur": "41.8 cm",
        "Left_femur": "42.0 cm",
        "Difference": "00.2 cm, left longer 0.5%"
      },
      "tibia": {
        "Right_tibia": "34.5 cm",
        "Left_tibia": "34.3 cm",
        "Difference": "00.2 cm, right longer 0.6%"
      },
      "total": {
        "Total_right": "76.3 cm",
        "Total_left": "76.3 cm",
        "Difference": "00.0 cm, equal 0.0%"
      },
      "pixel_distance": {
        "Left_femur": 1892,
        "Left_tibia": 1544,
        "Right_femur": 1886,
        "Right_tibia": 1555
      },
      "details": {
        "AccessionNumber": "100876169",
        "StudyDescription": "XR HIPS TO ANKLES LEG MEASUREMENTS",
        "SeriesDescription": "Lower limbs",
        "BodyPartExamined": "LEG",
        "FieldOfViewDimensions": "[975, 391]",
        "StationName": "EOSRM7"
      }
    }
  }
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

# 1) List plugins
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

# 2) PACS stub (default MRN = "12345")
@mcp.tool(
    name="get_pacs_image",
    description="Grab a PACS image URL by patient MRN (defaults to 12345)"
)
async def get_pacs_image(mrn: str = "12345") -> str:
    url = f"https://fakepacs.org/images/{mrn}.png"
    return wrap_tool_output("get_pacs_image", {"url": url})

# 3) Pipeline preview
@mcp.tool(name="get_pipeline_definition", description="Return the LLD pipeline definition")
async def get_pipeline_definition() -> str:
    return wrap_tool_output("get_pipeline_definition", PIPELINE_DEF)

# 4) Run pipeline (only one optional arg, MRN)
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

# 5) Job status with simulated delays
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

# 6) Report stub
@mcp.tool(name="get_job_results_report", description="Return JSON report for leg length")
async def get_job_results_report(job_id: str) -> str:
    return wrap_tool_output("get_job_results_report", REPORT_JSON)

# === SSE & REST Endpoints ===
async def handle_sse(request: Request):
    async with sse.connect_sse(request.scope, request.receive, request._send) as (r, w):
        await mcp._mcp_server.run(r, w, mcp._mcp_server.create_initialization_options())

async def api_root(request: Request):
    return JSONResponse({"status": "ok", "tools": list(mcp._tool_registry.keys())})

async def pacs_endpoint(request: Request):
    mrn = request.path_params["mrn"]
    return JSONResponse(json.loads(await get_pacs_image(mrn)))

async def pipeline_definition(request: Request):
    return JSONResponse(json.loads(await get_pipeline_definition()))

async def pipeline_run(request: Request):
    # ignore the path param; MRN will default to "12345"
    return JSONResponse(json.loads(await run_pipeline()))

async def job_status(request: Request):
    job_id = request.path_params["job_id"]
    return JSONResponse(json.loads(await get_job_status(job_id)))

async def job_results_report(request: Request):
    job_id = request.path_params["job_id"]
    return JSONResponse(json.loads(await get_job_results_report(job_id)))

app = Starlette(
    debug=True,
    routes=[
        Route("/sse", handle_sse),
        Route("/api/v1/", api_root),
        Route("/api/v1/pacs/{mrn}", pacs_endpoint, methods=["GET"]),
        Route("/api/v1/pipeline/{pipeline_id}/definition", pipeline_definition, methods=["GET"]),
        Route("/api/v1/pipeline/run/{pipeline_id}", pipeline_run, methods=["POST"]),
        Route("/api/v1/job/status/{job_id}", job_status, methods=["GET"]),
        Route("/api/v1/job/results/report/{job_id}", job_results_report, methods=["GET"]),
        Mount("/messages/", app=sse.handle_post_message),
    ],
)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8096)

