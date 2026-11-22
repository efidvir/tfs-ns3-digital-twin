"""
Ceragon ns-3 Functional Twin Runner
===================================
Runs the ``contrib/ceragon`` ns-3 module (Ceragon portfolio functional twin)
and returns its JSON report.

Flow:
    CER-Intent topology (TFS-synced state)  --tfs_to_ceragon_twin.convert-->  .twin text
    .twin text  -->  ns3.45-ceragon-twin --topology=<file>
    stdout ===CERAGON_TWIN_METRICS_START=== {json} ===CERAGON_TWIN_METRICS_END===  -> dict

Execution modes (NS3_TWIN_MODE):
    ssh     the binary on the remote ns-3 host over SSH (default)
    local   the binary on this machine; the telemetry CSV comes back as a
            time series (capacity, modulation and rain rate per radio link)
    replay  reports recorded earlier by local runs (NS3_TWIN_RECORDINGS), for
            places with no ns-3 build, such as the browser copy of the demo.
            A scenario that was not recorded gets the recorded run of the same
            scenario whose traffic rates are closest, and says so.

Environment:
    NS3_SSH_HOST / NS3_HOST / NS3_USER   remote host (same as the TSN runner)
    NS3_DIR                              ns-3 tree (default /home/efid/ns3-dev)
    CERAGON_TWIN_BINARY                  override the twin executable path
    CERAGON_TWIN_TMPDIR                  remote TMPDIR (default /home/efid/.ceragon_tmp)
    NS3_TWIN_RECORD_TO                   local mode: append every run to this file
    NS3_TWIN_RECORDINGS                  replay mode: recorded runs
"""
from __future__ import annotations

import csv
import hashlib
import json
import logging
import os
import re
import subprocess
import sys
import tempfile
import threading
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

logger = logging.getLogger("CeragonNs3TwinRunner")


def _repo_root() -> Path:
    here = Path(__file__).resolve().parent
    for cand in (here, here.parent):
        if (cand / "ns3_ceragon" / "tools").is_dir():
            return cand
    return here.parent


_REPO_ROOT = _repo_root()
_TOOLS = _REPO_ROOT / "ns3_ceragon" / "tools"
if str(_TOOLS) not in sys.path:
    sys.path.insert(0, str(_TOOLS))

try:
    from tfs_to_ceragon_twin import convert as _convert_topology  # type: ignore
except Exception:  # pragma: no cover
    _convert_topology = None

METRICS_START = "===CERAGON_TWIN_METRICS_START==="
METRICS_END = "===CERAGON_TWIN_METRICS_END==="
PORTFOLIO_START = "===CERAGON_PORTFOLIO_START==="
PORTFOLIO_END = "===CERAGON_PORTFOLIO_END==="
MODES = ("ssh", "local", "replay")
MAX_SERIES_POINTS = 160


def _extract(stdout: str, start: str, end: str) -> Optional[Any]:
    if start in stdout and end in stdout:
        return json.loads(stdout.split(start, 1)[1].split(end, 1)[0].strip())
    return None


def _subprocess_run(cmd: List[str], **kwargs: Any) -> subprocess.CompletedProcess:
    """subprocess.run, through eventlet's thread pool when eventlet has monkey-patched this process."""
    if "eventlet" in sys.modules:
        try:
            from eventlet import patcher  # type: ignore
            if patcher.is_monkey_patched("thread"):
                from eventlet import tpool as _ev_tpool  # type: ignore
                return _ev_tpool.execute(patcher.original("subprocess").run, cmd, **kwargs)
        except Exception:
            pass
    return subprocess.run(cmd, **kwargs)


# ── Scenario keys (record / replay) ─────────────────────────────────────────

def _statements(twin_text: str) -> List[List[str]]:
    out = []
    for line in twin_text.splitlines():
        line = line.split("#", 1)[0].strip()
        if line:
            out.append(line.split())
    return out


def scenario_key(twin_text: str, sim_time: float) -> str:
    """The same statements and simulated time give the same key (comments and spacing aside)."""
    canon = "\n".join(" ".join(t) for t in _statements(twin_text))
    return hashlib.sha256(f"{canon}\n#sim={float(sim_time):g}".encode("utf-8")).hexdigest()


def _rate_mbps(token: str) -> float:
    m = re.fullmatch(r"([\d.]+)\s*([kKmMgG]?)(bps)?", token)
    if not m:
        return 0.0
    scale = {"k": 1e-3, "m": 1.0, "g": 1e3, "": 1e-6}[m.group(2).lower()]
    return float(m.group(1)) * scale


def _flow_spec(t: List[str]) -> Dict[str, Any]:
    """A flow statement: flow <name> <src> <dst> <rate> [key=value ...]."""
    opts = dict(x.split("=", 1) for x in t[5:] if "=" in x)
    return {"name": t[1], "src": t[2], "dst": t[3], "rate_mbps": _rate_mbps(t[4]), "dscp": int(opts.get("dscp", 0))}


def scenario_shape(twin_text: str, sim_time: float) -> Tuple[str, List[Dict[str, Any]]]:
    """
    (signature, flows): the scenario without its flows' names and rates (and without
    modulation-floor events), and its flows sorted by (src, dst, dscp, rate). Two
    scenarios with the same signature differ only in how much traffic each flow offers.
    """
    canon, flows = [], []
    for t in _statements(twin_text):
        if t[0] == "flow" and len(t) >= 5:
            spec = _flow_spec(t)
            flows.append(spec)
            canon.append(" ".join(["flow", "*", t[2], t[3], "*"] + t[5:]))
        elif t[0] == "event" and len(t) >= 5 and t[4] in ("min-mod", "max-mod"):
            continue
        else:
            canon.append(" ".join(t))
    canon.sort()
    canon.append(f"#sim={float(sim_time):g}")
    flows.sort(key=lambda f: (f["src"], f["dst"], f["dscp"], f["rate_mbps"]))
    return hashlib.sha256("\n".join(canon).encode("utf-8")).hexdigest(), flows


def _series_from_csv(path: str) -> Dict[str, List[Dict[str, Any]]]:
    """Telemetry CSV -> per radio link [{t, capacity_mbps, modulation, rain_mmh, rsl_dbm}], carrier 0."""
    series: Dict[str, List[Dict[str, Any]]] = {}
    try:
        with open(path, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                if row.get("carrier", "0") != "0":
                    continue
                series.setdefault(row["link"], []).append({
                    "t": round(float(row["time_s"]), 3),
                    "capacity_mbps": round(float(row["capacity_mbps"]), 1),
                    "modulation": row["modulation"],
                    "rain_mmh": round(float(row["rain_mmh"]), 2),
                    "rsl_dbm": round(float(row["rsl_dbm"]), 2),
                    "up": row.get("link_up") == "1",
                })
    except (OSError, KeyError, ValueError) as exc:
        logger.debug("telemetry CSV unreadable: %s", exc)
        return {}
    for link, points in series.items():
        if len(points) > MAX_SERIES_POINTS:
            step = len(points) / MAX_SERIES_POINTS
            series[link] = [points[int(i * step)] for i in range(MAX_SERIES_POINTS)] + [points[-1]]
    return series


class _Recordings:
    """Recorded runs, keyed by scenario_key, with their shape for nearest-rate lookups."""

    _lock = threading.Lock()

    def __init__(self, path: Path) -> None:
        self.path = path
        self.runs: List[Dict[str, Any]] = []
        if path.exists():
            data = json.loads(path.read_text(encoding="utf-8"))
            self.runs = data.get("runs", [])

    def find(self, twin_text: str, sim_time: float) -> Tuple[Optional[Dict[str, Any]], Dict[str, Any]]:
        key = scenario_key(twin_text, sim_time)
        for run in self.runs:
            if run["key"] == key:
                return run, {"exact": True}
        signature, flows = scenario_shape(twin_text, sim_time)
        best, best_d = None, None
        for run in self.runs:
            other = run.get("flows", [])
            if run.get("signature") != signature or len(other) != len(flows):
                continue
            d = sum(abs(o["rate_mbps"] - f["rate_mbps"]) for o, f in zip(other, flows))
            if best_d is None or d < best_d:
                best, best_d = run, d
        if best is None:
            return None, {"exact": False}
        return best, {"exact": False,
                      "flows": [{"name": f["name"], "requested_mbps": f["rate_mbps"],
                                 "recorded_mbps": o["rate_mbps"], "recorded_name": o["name"]}
                                for o, f in zip(best["flows"], flows)]}

    @classmethod
    def append(cls, path: Path, twin_text: str, sim_time: float, report: Dict[str, Any]) -> None:
        with cls._lock:
            data = {"version": 1, "runs": []}
            if path.exists():
                data = json.loads(path.read_text(encoding="utf-8"))
            key = scenario_key(twin_text, sim_time)
            signature, flows = scenario_shape(twin_text, sim_time)
            data["runs"] = [r for r in data.get("runs", []) if r.get("key") != key]
            data["runs"].append({"key": key, "signature": signature, "flows": flows, "sim_time": sim_time,
                                 "twin_text": twin_text, "report": report})
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(data, indent=1), encoding="utf-8")


class CeragonNs3TwinRunner:
    """Execute Ceragon functional-twin scenarios (remote over SSH, locally, or from recordings)."""

    def __init__(self, host: Optional[str] = None, ns3_dir: Optional[str] = None,
                 binary: Optional[str] = None, mode: Optional[str] = None):
        default_host = os.getenv("NS3_SSH_HOST", os.getenv("NS3_HOST", "efid@cersrv-029"))
        if "@" not in default_host and default_host not in ("localhost", "127.0.0.1", "local"):
            default_host = f"{os.getenv('NS3_USER', 'efid')}@{default_host}"
        self.host = host or default_host
        mode = (mode or os.getenv("NS3_TWIN_MODE") or "").strip().lower()
        if not mode:
            mode = "local" if self.host in ("localhost", "127.0.0.1", "local") else "ssh"
        if mode not in MODES:
            raise ValueError(f"NS3_TWIN_MODE must be one of {MODES}, not {mode!r}")
        self.mode = mode
        self.ns3_dir = ns3_dir or os.getenv("NS3_DIR", "/home/efid/ns3-dev")
        default_bin = "ns3.45-ceragon-twin" if mode == "local" else "ns3.45-ceragon-twin-default"
        self.binary = binary or os.getenv("CERAGON_TWIN_BINARY", f"{self.ns3_dir}/build/scratch/{default_bin}")
        self.remote_tmp = os.getenv("CERAGON_TWIN_TMPDIR", "/home/efid/.ceragon_tmp")
        self.record_to = os.getenv("NS3_TWIN_RECORD_TO")
        self.recordings_path = Path(os.getenv("NS3_TWIN_RECORDINGS", str(_REPO_ROOT / "data" / "ns3_recordings.json")))
        self._recordings: Optional[_Recordings] = None

    def describe(self) -> Dict[str, Any]:
        """Where runs happen, for status pages."""
        if self.mode == "replay":
            return {"mode": "replay", "engine": "ns-3.45 contrib/ceragon (recorded runs)",
                    "recordings": len(self._load_recordings().runs)}
        if self.mode == "local":
            return {"mode": "local", "engine": "ns-3.45 contrib/ceragon (local)",
                    "binary": Path(self.binary).name, "available": Path(self.binary).exists()}
        return {"mode": "ssh", "engine": "ns-3.45 contrib/ceragon (Live SSH)", "host": self.host}

    # ── topology ───────────────────────────────────────────────────────────
    @staticmethod
    def load_cer_topology(path: Optional[str] = None) -> Dict[str, Any]:
        p = Path(path) if path else _REPO_ROOT / "data" / "topology_state.json"
        return json.loads(p.read_text(encoding="utf-8"))

    def build_twin_text(self, topology: Optional[Dict[str, Any]] = None,
                        rain: Optional[Sequence[float]] = None,
                        flows: Optional[List[str]] = None,
                        events: Optional[List[str]] = None,
                        auto_flows: int = 2) -> str:
        if _convert_topology is None:
            raise RuntimeError("ns3_ceragon/tools/tfs_to_ceragon_twin.py not importable")
        topo = topology if topology is not None else self.load_cer_topology()
        return _convert_topology(topo, rain=tuple(rain) if rain else None, flows=flows or [],
                                 auto_flows=auto_flows, events=events or [])

    # ── execution ──────────────────────────────────────────────────────────
    def _ssh(self, remote_cmd: str, stdin: Optional[str], timeout: int) -> subprocess.CompletedProcess:
        cmd = ["ssh", "-o", "ConnectTimeout=6", "-o", "BatchMode=yes", self.host, remote_cmd]
        kwargs: Dict[str, Any] = {"capture_output": True, "text": True, "timeout": timeout}
        if stdin is not None:
            kwargs["input"] = stdin
        else:
            kwargs["stdin"] = subprocess.DEVNULL
        return _subprocess_run(cmd, **kwargs)

    def run(self, twin_text: str, sim_time: float = 8.0, telemetry_interval: float = 0.1,
            timeout: int = 180, seed: int = 1) -> Dict[str, Any]:
        """Run a .twin scenario and return the parsed JSON report."""
        if self.mode == "replay":
            return self._replay(twin_text, sim_time)
        if self.mode == "local":
            return self._run_local(twin_text, sim_time, telemetry_interval, timeout, seed)
        return self._run_ssh(twin_text, sim_time, telemetry_interval, timeout)

    def _run_ssh(self, twin_text: str, sim_time: float, telemetry_interval: float, timeout: int) -> Dict[str, Any]:
        import base64
        started = time.time()
        run_id = uuid.uuid4().hex[:10]
        remote_file = f"{self.remote_tmp}/twin-{run_id}.twin"
        b64_payload = base64.b64encode(twin_text.encode("utf-8")).decode("ascii")
        args = f"--topology={remote_file} --simTime={sim_time} --telemetryInterval={telemetry_interval}"
        remote_cmd = (f"mkdir -p {self.remote_tmp} && echo '{b64_payload}' | base64 -d > {remote_file} && "
                      f"TMPDIR={self.remote_tmp} {self.binary} {args}; rc=$?; rm -f {remote_file}; exit $rc")
        proc = self._ssh(remote_cmd, None, timeout)
        report = _extract(proc.stdout, METRICS_START, METRICS_END)
        if report is None:
            raise RuntimeError(f"ns-3 twin returned no report (rc={proc.returncode}): "
                               f"{(proc.stderr or proc.stdout)[-800:]}")
        report["execution"] = {
            "engine": "ns-3.45 contrib/ceragon (Live SSH)",
            "mode": "ssh",
            "host": self.host,
            "binary": self.binary,
            "command": f"{Path(self.binary).name} {args}",
            "wall_clock_ms": round((time.time() - started) * 1000, 1),
            "is_live_remote": True,
            "stderr_tail": (proc.stderr or "")[-400:],
        }
        return report

    def _run_local(self, twin_text: str, sim_time: float, telemetry_interval: float, timeout: int,
                   seed: int) -> Dict[str, Any]:
        if not Path(self.binary).exists():
            raise RuntimeError(f"ns-3 twin binary not found: {self.binary} (set CERAGON_TWIN_BINARY)")
        started = time.time()
        with tempfile.TemporaryDirectory(prefix="ceragon-twin-") as tmp:
            topo_file = os.path.join(tmp, "scenario.twin")
            csv_file = os.path.join(tmp, "telemetry.csv")
            Path(topo_file).write_text(twin_text, encoding="utf-8")
            args = [f"--topology={topo_file}", f"--simTime={sim_time}",
                    f"--telemetryInterval={telemetry_interval}", f"--telemetry={csv_file}", f"--seed={seed}"]
            proc = _subprocess_run([self.binary, *args], capture_output=True, text=True, timeout=timeout,
                                   stdin=subprocess.DEVNULL, cwd=tmp)
            report = _extract(proc.stdout, METRICS_START, METRICS_END)
            if report is None:
                raise RuntimeError(f"ns-3 twin returned no report (rc={proc.returncode}): "
                                   f"{(proc.stderr or proc.stdout)[-800:]}")
            report["series"] = _series_from_csv(csv_file)
        report["execution"] = {
            "engine": "ns-3.45 contrib/ceragon (local)",
            "mode": "local",
            "binary": Path(self.binary).name,
            "command": f"{Path(self.binary).name} --topology=scenario.twin --simTime={sim_time:g} "
                       f"--telemetryInterval={telemetry_interval:g} --telemetry=telemetry.csv --seed={seed}",
            "wall_clock_ms": round((time.time() - started) * 1000, 1),
            "recorded_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "stderr_tail": (proc.stderr or "")[-400:],
        }
        if self.record_to:
            _Recordings.append(Path(self.record_to), twin_text, sim_time, report)
        return report

    def _load_recordings(self) -> _Recordings:
        if self._recordings is None:
            self._recordings = _Recordings(self.recordings_path)
        return self._recordings

    def _replay(self, twin_text: str, sim_time: float) -> Dict[str, Any]:
        run, match = self._load_recordings().find(twin_text, sim_time)
        if run is None:
            raise RuntimeError("no recorded ns-3 run for this scenario (replay mode)")
        report = json.loads(json.dumps(run["report"]))
        if not match["exact"]:      # the recorded flows carry this scenario's names
            names = {m["recorded_name"]: m["name"] for m in match["flows"]}
            for f in report.get("flows", []) or []:
                if f.get("name") in names:
                    f["recorded_as"] = f["name"]
                    f["name"] = names[f["name"]]
        execution = dict(report.get("execution") or {})
        execution.update({
            "mode": "replay",
            "engine": "ns-3.45 contrib/ceragon (recorded run)",
            "replay": match,
            "recorded_twin_text": None if match["exact"] else run["twin_text"],
        })
        report["execution"] = execution
        return report

    def run_from_cer_topology(self, sim_time: float = 10.0, rain: Optional[Sequence[float]] = None,
                              flows: Optional[List[str]] = None, events: Optional[List[str]] = None,
                              auto_flows: int = 2) -> Dict[str, Any]:
        text = self.build_twin_text(rain=rain, flows=flows, events=events, auto_flows=auto_flows)
        report = self.run(text, sim_time=sim_time)
        report["twin_topology"] = text
        return report

    def portfolio(self, timeout: int = 30) -> List[Dict[str, Any]]:
        if self.mode == "local":
            proc = _subprocess_run([self.binary, "--listPortfolio"], capture_output=True, text=True,
                                   timeout=timeout, stdin=subprocess.DEVNULL)
        elif self.mode == "ssh":
            proc = self._ssh(f"{self.binary} --listPortfolio", None, timeout)
        else:
            raise RuntimeError("the portfolio needs an ns-3 build (local or ssh mode)")
        data = _extract(proc.stdout, PORTFOLIO_START, PORTFOLIO_END)
        if data is None:
            raise RuntimeError(f"portfolio query failed: {(proc.stderr or proc.stdout)[-400:]}")
        return data


if __name__ == "__main__":  # manual smoke test
    logging.basicConfig(level=logging.INFO)
    r = CeragonNs3TwinRunner()
    print(json.dumps(r.portfolio()[:3], indent=2))
