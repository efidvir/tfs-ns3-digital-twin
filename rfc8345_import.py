"""
RFC 8345 topology import for the digital twin
=============================================
Reads an ``ietf-network:networks`` document, as TeraFlowSDN serves it at
``/restconf/data/ietf-network:networks/``, and returns the twin's topology
model: the same (devices, links) lists ``TfsApiClient.get_topology_model``
returns from the TFS API, so the rest of the twin (NS-3 export, what-if) is
unchanged.

Link capacity comes from the RFC 8795 TE attributes when present
(``max-link-bandwidth`` in kbps); links to or from a radio sector
(``rf-sector-*``) are marked wireless. RFC 8345 links are directional; a link
and its reverse become one twin link.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

DEFAULT_CAPACITY_GBPS = 1.0


def _networks(doc: Dict[str, Any]) -> List[Dict[str, Any]]:
    body = doc.get("ietf-network:networks", doc.get("networks", doc))
    networks = body.get("network", []) if isinstance(body, dict) else []
    if not networks:
        raise ValueError("no ietf-network:networks/network in the document")
    return networks


def _pick_network(networks: List[Dict[str, Any]], network_id: Optional[str]) -> Dict[str, Any]:
    if network_id is None:
        return networks[0]
    for net in networks:
        if net.get("network-id") == network_id:
            return net
    raise ValueError(f"network '{network_id}' not in the document")


def _capacity_gbps(link: Dict[str, Any]) -> Optional[float]:
    te = link.get("ietf-te-topology:te", {}) or {}
    attrs = te.get("te-link-attributes", {}) or {}
    bw = ((attrs.get("max-link-bandwidth") or {}).get("te-bandwidth") or {})
    kbps = bw.get("ietf-eth-te-topology:eth-bandwidth") or bw.get("eth-bandwidth")
    if kbps in (None, ""):
        return None
    return float(kbps) / 1e6


def _is_radio_tp(tp: Optional[str]) -> bool:
    return str(tp or "").lower().startswith("rf-sector-")


def to_twin_topology(doc: Dict[str, Any], network_id: Optional[str] = None) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    net = _pick_network(_networks(doc), network_id)

    devices: List[Dict[str, Any]] = []
    index: Dict[str, int] = {}
    for idx, node in enumerate(sorted(net.get("node", []), key=lambda n: str(n.get("node-id")))):
        node_id = str(node.get("node-id"))
        tps = [str(tp.get("tp-id")) for tp in node.get("ietf-network-topology:termination-point", []) or []]
        is_radio = any(_is_radio_tp(tp) for tp in tps)
        devices.append({
            "index": idx,
            "uuid": node_id,
            "name": node.get("name", node_id),
            "device_type": "ceragon-wireless" if is_radio else "packet-router",
            "operational_status": 2,
            "endpoints": [{"endpoint_id": {"endpoint_uuid": {"uuid": tp}}, "name": tp} for tp in tps],
            "num_endpoints": len(tps),
            "config_rules": {},
            "is_ceragon": is_radio,
        })
        index[node_id] = idx

    links: List[Dict[str, Any]] = []
    seen = set()
    for link in net.get("ietf-network-topology:link", []) or []:
        src = link.get("source") or {}
        dst = link.get("destination") or {}
        a, a_tp = str(src.get("source-node")), src.get("source-tp")
        b, b_tp = str(dst.get("dest-node")), dst.get("dest-tp")
        if a not in index or b not in index:
            continue
        key = tuple(sorted([(a, str(a_tp)), (b, str(b_tp))]))
        if key in seen:
            continue
        seen.add(key)
        link_id = str(link.get("link-id", f"{a}/{a_tp}=={b}/{b_tp}"))
        wireless = _is_radio_tp(a_tp) or _is_radio_tp(b_tp) or any(
            w in link_id.lower() for w in ("wireless", "radio", "mmwave"))
        capacity = _capacity_gbps(link)
        links.append({
            "index": len(links),
            "uuid": link_id,
            "name": link_id,
            "src_index": index[a],
            "src_uuid": a,
            "src_endpoint": a_tp or "port-0",
            "dst_index": index[b],
            "dst_uuid": b,
            "dst_endpoint": b_tp or "port-0",
            "total_capacity_gbps": capacity if capacity is not None else DEFAULT_CAPACITY_GBPS,
            "capacity_source": "rfc8795-te" if capacity is not None else "default",
            "delay": "0.5ms" if wireless else "1.5ms",
            "is_wireless": wireless,
        })
    return devices, links
