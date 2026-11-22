"""
Pre-flight of a transport slice on the Ceragon ns-3 twin
=========================================================
Before a slice is applied, CER-Intent asks the twin whether the network can
carry it. The twin answers from the network as TeraFlowSDN describes it, not
from a hand-written scenario:

  topology     the twin's last sync (RFC 8345 or the TFS-API)
  radios       each Ceragon device's model, from its TFS-API inventory
  traffic      the services already provisioned (TFS-API), at their
               committed bandwidth, plus the candidate slice
  conditions   the site plan: hop distances and the design rain rate

Two ns-3 runs under the same weather:
  before   the services already provisioned
  after    the same, plus the candidate slice and its radio settings
           (an ACM floor becomes a min-mod event on the radio hop)

The verdict compares the "after" run with the slice's SLOs (bandwidth,
latency, loss), checks the modulation floor, and checks that the services
already provisioned keep their throughput. The answer is a simulation and is
labelled as one.

Site plan (TWIN_SITE_PLAN, JSON), every key optional:
  {"design_rain_mmh": 60, "rain_window_s": [2, 6], "sim_time_s": 8,
   "hop_distance_m": 250, "links": {"radio-1|radio-2": {"distance_m": 250}}}
"""
from __future__ import annotations

import collections
import json
import logging
import os
import re
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("CeragonPreflight")

DEFAULT_PLAN: Dict[str, Any] = {
    "design_rain_mmh": 60.0,
    "rain_window_s": [2.0, 6.0],
    "sim_time_s": 8.0,
    "hop_distance_m": 250.0,
    "host_offset_m": 10.0,
    "wire_rate_gbps": 10,
    "links": {},
}
THROUGHPUT_TOLERANCE = 0.99      # a flow keeps its SLO at 99 % of its offered rate
DEFAULT_MAX_LOSS_PCT = 0.1
DEFAULT_SLICE_DSCP = 34          # AF41: what a slice's traffic carries unless the intent says otherwise
EXISTING_DSCP = 0                # provisioned services without a marking: best effort


@dataclass
class Candidate:
    slice_id: str
    src: str
    dst: str
    bandwidth_mbps: float
    max_latency_ms: Optional[float] = None
    max_loss_pct: Optional[float] = None
    dscp: int = DEFAULT_SLICE_DSCP
    acm_floor: Optional[str] = None
    vlan_id: Optional[int] = None
    technology: Optional[str] = None

    @classmethod
    def from_request(cls, body: Dict[str, Any]) -> "Candidate":
        try:
            src, dst = body["src"], body["dst"]
            bandwidth = float(body["bandwidth_mbps"])
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError("candidate needs src, dst and bandwidth_mbps") from exc
        floor = body.get("acm_floor")
        if isinstance(floor, dict):
            floor = floor.get("min_modulation") or floor.get("min")
        return cls(
            slice_id=str(body.get("slice_id") or f"slice-{src}-{dst}"),
            src=str(src), dst=str(dst), bandwidth_mbps=bandwidth,
            max_latency_ms=_opt_float(body.get("max_latency_ms")),
            max_loss_pct=_opt_float(body.get("max_loss_pct")),
            dscp=int(body.get("dscp", DEFAULT_SLICE_DSCP)),
            acm_floor=str(floor).upper().replace("-", "") if floor else None,
            vlan_id=body.get("vlan_id"),
            technology=body.get("technology"),
        )


def _opt_float(value: Any) -> Optional[float]:
    try:
        return None if value in (None, "") else float(value)
    except (TypeError, ValueError):
        return None


def load_site_plan(overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    plan = json.loads(json.dumps(DEFAULT_PLAN))
    path = os.getenv("TWIN_SITE_PLAN")
    if path and os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            plan.update(json.load(f))
    if overrides:
        plan.update({k: v for k, v in overrides.items() if v is not None})
    return plan


def _safe(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]", "_", str(name))


def _rules(device: Dict[str, Any]) -> Dict[str, Any]:
    out = {}
    for rule in (device or {}).get("device_config", {}).get("config_rules", []):
        custom = rule.get("custom") or {}
        value = custom.get("resource_value")
        if isinstance(value, str):
            try:
                value = json.loads(value)
            except ValueError:
                pass
        out[custom.get("resource_key")] = value
    return out


def radio_model(details: Optional[Dict[str, Any]]) -> Optional[str]:
    """A Ceragon radio's product model from its TFS-API inventory rules."""
    rules = _rules(details or {})
    for key in ("/device/hardware_info", "/device/capabilities"):
        value = rules.get(key)
        if isinstance(value, dict) and value.get("model"):
            return str(value["model"])
    return None


# ── Network model ────────────────────────────────────────────────────────────

@dataclass
class NetModel:
    nodes: Dict[str, str] = field(default_factory=dict)              # name -> model ("host" for sites)
    wires: List[Tuple[str, str, float]] = field(default_factory=list)  # (a, b, Gbps)
    hops: List[Tuple[str, str, str, float]] = field(default_factory=list)  # (a, b, model, distance m)
    positions: Dict[str, Tuple[float, float]] = field(default_factory=dict)
    sources: Dict[str, str] = field(default_factory=dict)

    def path(self, src: str, dst: str) -> List[str]:
        adj: Dict[str, List[str]] = collections.defaultdict(list)
        for a, b, *_ in self.wires + self.hops:
            adj[a].append(b)
            adj[b].append(a)
        prev, queue, seen = {}, collections.deque([src]), {src}
        while queue:
            n = queue.popleft()
            if n == dst:
                break
            for m in sorted(adj[n]):
                if m not in seen:
                    seen.add(m)
                    prev[m] = n
                    queue.append(m)
        if dst not in seen:
            return []
        out = [dst]
        while out[-1] != src:
            out.append(prev[out[-1]])
        return list(reversed(out))


def build_model(devices: List[Dict[str, Any]], links: List[Dict[str, Any]],
                details: Dict[str, Optional[Dict[str, Any]]], plan: Dict[str, Any],
                start: Optional[str] = None) -> NetModel:
    """The twin's synced topology plus device inventory -> nodes, wires and radio hops."""
    model = NetModel()
    by_uuid = {}
    for dev in devices:
        uid = str(dev.get("uuid") or dev.get("name"))
        name = _safe(dev.get("name") or uid)
        by_uuid[uid] = name
        m = radio_model(details.get(uid)) if dev.get("is_ceragon") else None
        model.nodes[name] = m or "host"
        model.sources[name] = "TFS-API inventory" if m else ("site" if not dev.get("is_ceragon") else "unknown model")
    link_plans = plan.get("links", {}) or {}
    for lk in links:
        a, b = by_uuid.get(str(lk.get("src_uuid"))), by_uuid.get(str(lk.get("dst_uuid")))
        if not a or not b:
            continue
        radio_a, radio_b = model.nodes.get(a) != "host", model.nodes.get(b) != "host"
        if lk.get("is_wireless") and radio_a and radio_b:
            hop_plan = link_plans.get(f"{a}|{b}") or link_plans.get(f"{b}|{a}") or {}
            distance = float(hop_plan.get("distance_m", plan["hop_distance_m"]))
            model.hops.append((a, b, model.nodes[a], distance))
        else:
            cap = lk.get("total_capacity_gbps")
            rate = float(cap) if cap and not lk.get("is_wireless") else float(plan["wire_rate_gbps"])
            model.wires.append((a, b, max(rate, float(plan["wire_rate_gbps"]))))
    _place(model, float(plan["host_offset_m"]), _safe(start) if start else None)
    return model


def _place(model: NetModel, host_offset: float, start: Optional[str] = None) -> None:
    """Positions along the hops, so the radio geometry matches the planned distances."""
    adj: Dict[str, List[Tuple[str, float]]] = collections.defaultdict(list)
    for a, b, _rate in model.wires:
        adj[a].append((b, host_offset))
        adj[b].append((a, host_offset))
    for a, b, _m, dist in model.hops:
        adj[a].append((b, dist))
        adj[b].append((a, dist))
    names = sorted(model.nodes, key=lambda n: (n != start, model.nodes[n] != "host", n))
    y = 0.0
    for start in names:
        if start in model.positions:
            continue
        model.positions[start] = (0.0, y)
        queue = collections.deque([start])
        while queue:
            n = queue.popleft()
            x0, y0 = model.positions[n]
            for m, d in sorted(adj[n]):
                if m not in model.positions:
                    model.positions[m] = (x0 + d, y0)
                    queue.append(m)
        y += 500.0


# ── Traffic ──────────────────────────────────────────────────────────────────

@dataclass
class Flow:
    name: str
    src: str
    dst: str
    rate_mbps: float
    dscp: int
    kind: str                       # "existing" | "slice"
    service: Optional[str] = None


def _service_capacity_mbps(svc: Dict[str, Any]) -> Optional[float]:
    for c in svc.get("service_constraints", []) or []:
        if "sla_capacity" in c:
            return float(c["sla_capacity"]["capacity_gbps"]) * 1000.0
    return None


def existing_flows(services: List[Dict[str, Any]], model: NetModel, skip: str) -> Tuple[List[Flow], List[Dict[str, Any]]]:
    """Active services with a committed bandwidth -> flows between their end devices."""
    flows, ignored = [], []
    for svc in services:
        name = svc.get("name") or svc.get("service_id", {}).get("service_uuid", {}).get("uuid")
        status = (svc.get("service_status") or {}).get("service_status", "")
        if name == skip or "ACTIVE" not in str(status):
            continue
        eps = svc.get("service_endpoint_ids", []) or []
        rate = _service_capacity_mbps(svc)
        if len(eps) < 2 or not rate:
            ignored.append({"service": name, "reason": "no committed bandwidth" if not rate else "fewer than two endpoints"})
            continue
        src = _safe(eps[0]["device_id"]["device_uuid"]["uuid"])
        dst = _safe(eps[1]["device_id"]["device_uuid"]["uuid"])
        if src not in model.nodes or dst not in model.nodes:
            ignored.append({"service": name, "reason": "endpoints outside the synced topology"})
            continue
        flows.append(Flow(_safe(name), src, dst, rate, EXISTING_DSCP, "existing", service=name))
    return flows, ignored


# ── Scenario text ────────────────────────────────────────────────────────────

def twin_text(model: NetModel, flows: List[Flow], plan: Dict[str, Any], title: str,
              acm_floor: Optional[str] = None, floor_hops: Optional[List[Tuple[str, str]]] = None) -> str:
    rain = float(plan["design_rain_mmh"])
    start, end = (float(x) for x in plan["rain_window_s"])
    lines = [
        f"# {title}",
        "# topology: the twin's last sync from TeraFlowSDN; radios: TFS-API inventory;",
        f"# conditions: site plan (design rain {rain:g} mm/h between t={start:g}s and t={end:g}s)",
    ]
    for name in sorted(model.nodes, key=lambda n: (model.positions.get(n, (0, 0))[1], model.positions.get(n, (0, 0))[0])):
        x, y = model.positions.get(name, (0.0, 0.0))
        lines.append(f"node {name:<14} {model.nodes[name]:<10} {x:7.1f} {y:7.1f}")
    for a, b, rate in model.wires:
        lines.append(f"wire {a} {b} rate={rate:g}Gbps")
    for a, b, m, dist in model.hops:
        lines.append(f"link {a} {b} model={m} distance={dist:g}")
    stop = float(plan["sim_time_s"]) - 0.5     # traffic stops before the end, so packets in flight are not lost
    for f in flows:
        lines.append(f"flow {f.name} {f.src} {f.dst} {f.rate_mbps:g}Mbps dscp={f.dscp} start=0.5 stop={stop:g}")
    if rain > 0:
        lines.append(f"rain {start:g} {end:g} {rain:g}")
    if acm_floor:
        for a, b in floor_hops or []:
            lines.append(f"event 0.05 {a} {b} min-mod {acm_floor}")
            lines.append(f"event 0.05 {b} {a} min-mod {acm_floor}")
    return "\n".join(lines) + "\n"


# ── Verdict ──────────────────────────────────────────────────────────────────

_MCS_RE = re.compile(r"MCS(\d+)", re.I)


def _mcs_index(name: Optional[str]) -> Optional[int]:
    m = _MCS_RE.search(str(name or ""))
    return int(m.group(1)) if m else None


def lowest_modulation(report: Dict[str, Any], hops: List[Tuple[str, str]]) -> Optional[str]:
    """Lowest modulation the hops reached, from the ACM timeline and the telemetry series."""
    keys = {f"{a}->{b}" for a, b in hops} | {f"{b}->{a}" for a, b in hops}
    seen = []
    for ev in report.get("timeline", []) or []:
        detail = str(ev.get("detail", ""))
        if ev.get("type") == "acm" and any(detail.startswith(k) for k in keys):
            seen += _MCS_RE.findall(detail)
    for key, points in (report.get("series") or {}).items():
        if key in keys:
            seen += [_MCS_RE.search(p.get("modulation", "")).group(1) for p in points
                     if _MCS_RE.search(p.get("modulation", ""))]
    for lk in report.get("links", []) or []:
        if lk.get("link") in keys:
            for c in (lk.get("state") or {}).get("carriers", []) or []:
                if _mcs_index(c.get("modulation")) is not None:
                    seen.append(str(_mcs_index(c.get("modulation"))))
    idx = [int(s) for s in seen]
    return f"MCS{min(idx)}" if idx else None


def _flow(report: Dict[str, Any], name: str) -> Optional[Dict[str, Any]]:
    return next((f for f in report.get("flows", []) or [] if f.get("name") == name), None)


def evaluate(before: Dict[str, Any], after: Dict[str, Any], cand: Candidate, slice_flow: Flow,
             existing: List[Flow], hops: List[Tuple[str, str]]) -> Dict[str, Any]:
    checks: List[Dict[str, Any]] = []
    got = _flow(after, slice_flow.name) or {}
    thr = float(got.get("throughput_mbps") or 0.0)
    checks.append({"id": "bandwidth", "label": "Slice bandwidth",
                   "target": f"{cand.bandwidth_mbps:g} Mbps", "value": f"{thr:.0f} Mbps",
                   "ok": thr >= THROUGHPUT_TOLERANCE * cand.bandwidth_mbps})
    delay = float(got.get("mean_delay_ms") or 0.0)
    if cand.max_latency_ms is not None:
        checks.append({"id": "latency", "label": "Slice latency (mean)",
                       "target": f"≤ {cand.max_latency_ms:g} ms", "value": f"{delay:.2f} ms",
                       "ok": delay <= cand.max_latency_ms})
    loss = float(got.get("loss_pct") or 0.0)
    max_loss = cand.max_loss_pct if cand.max_loss_pct is not None else DEFAULT_MAX_LOSS_PCT
    checks.append({"id": "loss", "label": "Slice packet loss",
                   "target": f"≤ {max_loss:g} %", "value": f"{loss:.2f} %", "ok": loss <= max_loss})
    low = lowest_modulation(after, hops)
    if cand.acm_floor:
        ok = low is None or (_mcs_index(low) or 0) >= (_mcs_index(cand.acm_floor) or 0)
        checks.append({"id": "acm_floor", "label": "Radio modulation floor",
                       "target": f"≥ {cand.acm_floor}", "value": low or "n/a", "ok": ok})
    for f in existing:
        b, a = _flow(before, f.name) or {}, _flow(after, f.name) or {}
        b_thr, a_thr = float(b.get("throughput_mbps") or 0.0), float(a.get("throughput_mbps") or 0.0)
        checks.append({"id": f"existing:{f.name}", "label": f"Existing service {f.service}",
                       "target": f"keeps {b_thr:.0f} Mbps", "value": f"{a_thr:.0f} Mbps",
                       "ok": a_thr >= THROUGHPUT_TOLERANCE * b_thr})
    verdict = "pass" if all(c["ok"] for c in checks) else "fail"
    failed = [c["label"] for c in checks if not c["ok"]]
    return {"verdict": verdict, "checks": checks, "lowest_modulation": low,
            "summary": ("The twin predicts every SLO holds under the design rain."
                        if verdict == "pass" else
                        "The twin predicts a breach: " + ", ".join(failed) + ".")}


def _hop_summary(report: Dict[str, Any], hops: List[Tuple[str, str]]) -> List[Dict[str, Any]]:
    out = []
    for lk in report.get("links", []) or []:
        if any(lk.get("link") == f"{a}->{b}" for a, b in hops):
            out.append({k: lk.get(k) for k in ("link", "availability", "min_capacity_mbps",
                                                "avg_capacity_mbps", "max_capacity_mbps")})
    return out


# ── The whole pre-flight ─────────────────────────────────────────────────────

def run_preflight(ndti: Any, runner: Any, body: Dict[str, Any]) -> Dict[str, Any]:
    """
    ndti     a NetworkDigitalTwinInstance (topology_shadow, tfs_client)
    runner   a CeragonNs3TwinRunner
    body     {"candidate": {...}, "plan": {...}}
    """
    cand = Candidate.from_request(body.get("candidate") or {})
    plan = load_site_plan(body.get("plan"))
    shadow = ndti.topology_shadow or {}
    devices, links = shadow.get("nodes", []), shadow.get("links", [])
    if not devices:
        raise ValueError("the twin has no topology yet; sync it first")

    client = ndti.tfs_client
    details = {}
    for dev in devices:
        if dev.get("is_ceragon"):
            uid = str(dev.get("uuid") or dev.get("name"))
            details[uid] = client.get_device_details(uid)
    model = build_model(devices, links, details, plan, start=cand.src)
    src, dst = _safe(cand.src), _safe(cand.dst)
    route = model.path(src, dst)
    if not route:
        raise ValueError(f"no path between {cand.src} and {cand.dst} in the synced topology")
    route_hops = [(a, b) for a, b, *_ in model.hops
                  if a in route and b in route and abs(route.index(a) - route.index(b)) == 1]

    try:
        services = client.list_services()
    except Exception as exc:  # the controller may not list services; simulate the slice alone
        logger.info("services unavailable: %s", exc)
        services = []
    existing, ignored = existing_flows(services, model, skip=cand.slice_id)
    slice_flow = Flow(_safe(cand.slice_id), src, dst, cand.bandwidth_mbps, cand.dscp, "slice")

    sim_time = float(plan["sim_time_s"])
    text_before = twin_text(model, existing, plan, "pre-flight BEFORE: services already provisioned")
    text_after = twin_text(model, existing + [slice_flow], plan,
                           f"pre-flight AFTER: provisioned services + slice {cand.slice_id}",
                           acm_floor=cand.acm_floor, floor_hops=route_hops)
    before = runner.run(text_before, sim_time=sim_time) if existing else {"flows": [], "links": [], "timeline": [],
                                                                            "note": "no provisioned traffic"}
    after = runner.run(text_after, sim_time=sim_time)
    result = evaluate(before, after, cand, slice_flow, existing, route_hops)
    return {
        "insight": "simulated",
        "candidate": asdict(cand),
        "plan": {k: plan[k] for k in ("design_rain_mmh", "rain_window_s", "sim_time_s")},
        "network": {
            "topology_source": getattr(ndti, "topology_source", None),
            "nodes": [{"name": n, "model": m, "source": model.sources.get(n)} for n, m in model.nodes.items()],
            "radio_hops": [{"a": a, "b": b, "model": m, "distance_m": d} for a, b, m, d in model.hops],
            "path": route,
            "existing_services": [asdict(f) for f in existing],
            "ignored_services": ignored,
        },
        "scenarios": {
            "before": {"twin_text": text_before, "report": before, "hops": _hop_summary(before, route_hops)},
            "after": {"twin_text": text_after, "report": after, "hops": _hop_summary(after, route_hops)},
        },
        "engine": (after.get("execution") or {}),
        **result,
    }
