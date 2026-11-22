"""
Digital twin as MCP tools
=========================
    python src/twin_mcp.py                                  # stdio
    python src/twin_mcp.py --transport streamable-http --port 8766

Offers the twin to agents as tools: synchronise from TeraFlowSDN (TFS API or
RFC 8345), read its state, list the simulators, and run what-if scenarios.
Every scenario answer carries ``"insight": "simulated"`` and the basis it
rests on (sync time, topology source, engine): a prediction, not a measurement.

With TWIN_URL set, the tools use that twin's HTTP API, so the MCP tools and the
HTTP API share one twin; without it they run a twin in this process.
"""
# Annotations stay real types (no `from __future__ import annotations`): MCP SDK 1.x
# inspects them with issubclass() when it builds the tool schemas.

import argparse
import os
import shutil
import sys
from typing import Any, Dict, List, Optional

import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tfs_api_client import TfsApiClient  # noqa: E402
from tfs_digital_twin_api import NetworkDigitalTwinInstance  # noqa: E402


class _Twin:
    instance: Optional[NetworkDigitalTwinInstance] = None

    @classmethod
    def get(cls) -> NetworkDigitalTwinInstance:
        if cls.instance is None:
            client = TfsApiClient(descriptor_fallback_path=os.getenv("TWIN_DESCRIPTORS"))
            cls.instance = NetworkDigitalTwinInstance(
                instance_id=os.getenv("TWIN_INSTANCE_ID", "ndti-mcp-01"),
                name="Transport twin (MCP)",
                scope="transport",
                tfs_client=client,
            )
        return cls.instance


def _remote() -> Optional[str]:
    url = os.getenv("TWIN_URL", "").strip().rstrip("/")
    return url or None


def _call(method: str, path: str, body: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    resp = requests.request(method, f"{_remote()}{path}", json=body, timeout=float(os.getenv("TWIN_HTTP_TIMEOUT", "60")))
    resp.raise_for_status()
    return resp.json()


def list_simulators() -> Dict[str, Any]:
    """Simulators the twin can run a scenario on, and whether each is available here."""
    ns3 = bool(os.getenv("NS3_HOME") or shutil.which("ns3"))
    return {"simulators": [
        {"engine": "analytical", "available": True,
         "covers": "rain fade (ITU-R P.838), congestion, link loss, slice admission, energy"},
        {"engine": "hybrid-ns3-analytical", "available": True,
         "covers": "analytical model, refined by NS-3 runs when NS-3 is installed", "ns3_installed": ns3},
    ]}


def sync_twin() -> Dict[str, Any]:
    """Synchronise the twin's topology and telemetry from TeraFlowSDN."""
    if _remote():
        return _call("POST", "/api/v1/dti/sync", {})
    return _Twin.get().sync_from_physical()


def get_twin_state() -> Dict[str, Any]:
    """The twin's lifecycle state, size, last sync and where its topology came from."""
    if _remote():
        instances = _call("GET", "/api/v1/dti/instances").get("instances", [])
        if not instances:
            return {"state": "absent"}
        first = instances[0]
        health = _call("GET", "/healthz")
        return {
            "instance_id": first.get("instance_id"),
            "state": first.get("lifecycle_state"),
            "nodes": first.get("nodes_in_shadow"),
            "links": first.get("links_in_shadow"),
            "last_sync_timestamp": first.get("last_sync_timestamp"),
            "topology_source": health.get("topology_source"),
        }
    twin = _Twin.get()
    return {
        "instance_id": twin.instance_id,
        "state": twin.state,
        "nodes": len(twin.topology_shadow.get("nodes", [])),
        "links": len(twin.topology_shadow.get("links", [])),
        "last_sync_timestamp": twin.last_sync_time,
        "topology_source": twin.topology_source,
        "scenarios_run": len(twin.scenarios),
    }


def run_what_if(perturbations: List[Dict[str, Any]], engine: str = "hybrid-ns3-analytical",
                domain: str = "multi-domain-transport", scenario_id: Optional[str] = None) -> Dict[str, Any]:
    """Run a what-if scenario on the twin; the result is simulated and says what it rests on."""
    request: Dict[str, Any] = {"perturbations": perturbations, "engine": engine, "domain": domain}
    if scenario_id:
        request["scenario_id"] = scenario_id
    if _remote():
        answer = _call("POST", "/what-if", request)
        answer.setdefault("insight", "simulated")
        return answer
    return _Twin.get().execute_what_if_scenario(request)


TOOLS = (
    (list_simulators, True),
    (sync_twin, False),
    (get_twin_state, True),
    (run_what_if, True),
)


def register(server: Any) -> List[str]:
    try:
        from mcp.types import ToolAnnotations
    except ImportError:
        ToolAnnotations = None
    names = []
    for fn, read_only in TOOLS:
        kwargs: Dict[str, Any] = {"name": fn.__name__, "description": (fn.__doc__ or "").strip()}
        if ToolAnnotations is not None:
            kwargs["annotations"] = ToolAnnotations(readOnlyHint=read_only, destructiveHint=False,
                                                    openWorldHint=fn is sync_twin)
        server.add_tool(fn, **kwargs)
        names.append(fn.__name__)
    return names


def build_server(host: str = "127.0.0.1", port: int = 8766):
    try:
        from mcp.server.mcpserver import MCPServer
        server = MCPServer("transport-twin", instructions=__doc__)
    except ImportError:
        from mcp.server.fastmcp import FastMCP
        server = FastMCP("transport-twin", instructions=__doc__, host=host, port=port)
    register(server)
    return server


def main() -> None:
    parser = argparse.ArgumentParser(description="Digital twin MCP server")
    parser.add_argument("--transport", choices=("stdio", "streamable-http", "sse"), default="stdio")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8766)
    args = parser.parse_args()
    server = build_server(args.host, args.port)
    if args.transport == "stdio":
        server.run(transport="stdio")
    elif server.__class__.__name__ == "MCPServer":
        server.run(transport=args.transport, host=args.host, port=args.port)
    else:
        server.run(transport=args.transport)


if __name__ == "__main__":
    main()
