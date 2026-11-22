"""
Slice pre-flight on the Ceragon ns-3 twin: the scenario the twin builds from the
network it synced, the SLO verdict, and recorded runs for places without ns-3.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import ceragon_preflight as pf  # noqa: E402
from ceragon_ns3_twin_runner import CeragonNs3TwinRunner, _Recordings, scenario_key, scenario_shape  # noqa: E402

DEVICES = [
    {"uuid": "edge", "name": "edge", "is_ceragon": False},
    {"uuid": "radio-1", "name": "radio-1", "is_ceragon": True},
    {"uuid": "radio-2", "name": "radio-2", "is_ceragon": True},
    {"uuid": "region-a", "name": "region-a", "is_ceragon": False},
]
LINKS = [
    {"src_uuid": "region-a", "dst_uuid": "radio-1", "is_wireless": False, "total_capacity_gbps": 1.0},
    {"src_uuid": "radio-1", "dst_uuid": "radio-2", "is_wireless": True, "total_capacity_gbps": 1.0},
    {"src_uuid": "radio-2", "dst_uuid": "edge", "is_wireless": False, "total_capacity_gbps": 1.0},
]


def device(model: str):
    return {"device_config": {"config_rules": [
        {"custom": {"resource_key": "/device/hardware_info", "resource_value": json.dumps({"model": model})}}]}}


def service(name: str, mbps: float, status: str = "SERVICESTATUS_ACTIVE"):
    ep = lambda d: {"device_id": {"device_uuid": {"uuid": d}}, "endpoint_uuid": {"uuid": "eth1"}}  # noqa: E731
    return {"name": name, "service_status": {"service_status": status},
            "service_endpoint_ids": [ep("region-a"), ep("edge")],
            "service_constraints": [{"sla_capacity": {"capacity_gbps": mbps / 1000}}]}


def report(flows, low="MCS7", cap=(770, 1000)):
    return {"flows": flows, "timeline": [{"t": 4.8, "type": "acm", "detail": f"radio-1->radio-2 carrier 0 MCS8 -> {low}"}],
            "links": [{"link": "radio-1->radio-2", "availability": 1.0, "min_capacity_mbps": cap[0],
                       "avg_capacity_mbps": 950, "max_capacity_mbps": cap[1]}]}


def flow(name, offered, thr, loss=0.0, delay=0.2):
    return {"name": name, "offered_mbps": offered, "throughput_mbps": thr, "loss_pct": loss, "mean_delay_ms": delay}


class FakeClient:
    def __init__(self, services):
        self.services = services

    def get_device_details(self, uid):
        return device("MH-T261")

    def list_services(self):
        return self.services


class FakeNdti:
    topology_source = "rfc8345"

    def __init__(self, services):
        self.topology_shadow = {"nodes": DEVICES, "links": LINKS}
        self.tfs_client = FakeClient(services)


class FakeRunner:
    """Answers like ns-3 would for a 770 Mbps worst-case hop shared fairly."""

    def __init__(self):
        self.texts = []

    def run(self, text, sim_time=8.0):
        self.texts.append(text)
        flows = []
        specs = [ln.split() for ln in text.splitlines() if ln.startswith("flow ")]
        offered = sum(float(s[4].rstrip("Mbps")) for s in specs)
        for s in specs:
            rate = float(s[4].rstrip("Mbps"))
            share = rate if offered <= 770 else rate * 770 / offered
            flows.append(flow(s[1], rate, share, loss=0 if offered <= 770 else 12.0, delay=0.2 if offered <= 770 else 30))
        return {**report(flows), "execution": {"mode": "fake"}}


class PreflightTests(unittest.TestCase):
    def setUp(self):
        self.plan = pf.load_site_plan({"links": {"radio-1|radio-2": {"distance_m": 250}}})

    def test_model_comes_from_the_synced_topology_and_inventory(self):
        model = pf.build_model(DEVICES, LINKS, {"radio-1": device("MH-T261"), "radio-2": device("MH-T261")},
                               self.plan, start="region-a")
        self.assertEqual(model.nodes, {"edge": "host", "radio-1": "MH-T261", "radio-2": "MH-T261", "region-a": "host"})
        self.assertEqual(model.hops, [("radio-1", "radio-2", "MH-T261", 250.0)])
        self.assertEqual(model.path("region-a", "edge"), ["region-a", "radio-1", "radio-2", "edge"])
        self.assertEqual(model.positions["region-a"], (0.0, 0.0))
        self.assertEqual(model.positions["radio-2"][0] - model.positions["radio-1"][0], 250.0)

    def test_scenario_text_carries_traffic_weather_and_the_modulation_floor(self):
        model = pf.build_model(DEVICES, LINKS, {"radio-1": device("MH-T261"), "radio-2": device("MH-T261")}, self.plan)
        flows = [pf.Flow("backhaul", "region-a", "edge", 200, 0, "existing"), pf.Flow("s1", "region-a", "edge", 500, 34, "slice")]
        text = pf.twin_text(model, flows, self.plan, "t", acm_floor="MCS4", floor_hops=[("radio-1", "radio-2")])
        self.assertIn("link radio-1 radio-2 model=MH-T261 distance=250", text)
        self.assertIn("flow s1 region-a edge 500Mbps dscp=34 start=0.5", text)
        self.assertIn("rain 2 6 60", text)
        self.assertIn("event 0.05 radio-2 radio-1 min-mod MCS4", text)

    def test_only_active_services_with_a_committed_bandwidth_become_traffic(self):
        model = pf.build_model(DEVICES, LINKS, {}, self.plan)
        flows, ignored = pf.existing_flows(
            [service("backhaul", 200), service("old", 300, "SERVICESTATUS_PLANNED"), service("cand", 500),
             {**service("nobw", 1), "service_constraints": []}], model, skip="cand")
        self.assertEqual([(f.name, f.rate_mbps) for f in flows], [("backhaul", 200.0)])
        self.assertEqual(ignored, [{"service": "nobw", "reason": "no committed bandwidth"}])

    def test_a_slice_that_fits_passes_and_one_that_does_not_is_held(self):
        runner = FakeRunner()
        ok = pf.run_preflight(FakeNdti([service("backhaul", 200)]), runner, {"candidate": {
            "slice_id": "s500", "src": "region-a", "dst": "edge", "bandwidth_mbps": 500, "max_latency_ms": 10,
            "acm_floor": {"min_modulation": "MCS4"}}})
        self.assertEqual(ok["verdict"], "pass", ok["checks"])
        self.assertEqual(len(runner.texts), 2)
        self.assertIn("min-mod MCS4", ok["scenarios"]["after"]["twin_text"])
        self.assertNotIn("s500", ok["scenarios"]["before"]["twin_text"])
        held = pf.run_preflight(FakeNdti([service("backhaul", 200)]), FakeRunner(), {"candidate": {
            "slice_id": "s800", "src": "region-a", "dst": "edge", "bandwidth_mbps": 800, "max_latency_ms": 10}})
        self.assertEqual(held["verdict"], "fail")
        failed = {c["id"] for c in held["checks"] if not c["ok"]}
        self.assertTrue({"bandwidth", "latency", "loss"} <= failed)

    def test_the_floor_check_reads_the_lowest_modulation_reached(self):
        cand = pf.Candidate.from_request({"src": "a", "dst": "b", "bandwidth_mbps": 10, "acm_floor": "MCS8"})
        res = pf.evaluate(report([]), report([flow("slice-a-b", 10, 10)], low="MCS7"), cand,
                          pf.Flow("slice-a-b", "a", "b", 10, 34, "slice"), [], [("radio-1", "radio-2")])
        floor = next(c for c in res["checks"] if c["id"] == "acm_floor")
        self.assertEqual((floor["value"], floor["ok"]), ("MCS7", False))


class ReplayTests(unittest.TestCase):
    TEXT = ("node a host 0 0\nnode b host 10 0\nwire a b rate=10Gbps\n"
            "flow backhaul a b 200Mbps dscp=0 start=0.5\nflow s1 a b {rate}Mbps dscp=34 start=0.5\nrain 2 6 60\n")

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.path = os.path.join(self.tmp, "rec.json")
        for rate in (500, 800):
            text = self.TEXT.format(rate=rate)
            _Recordings.append(__import__("pathlib").Path(self.path), text, 8.0,
                               {"flows": [flow("backhaul", 200, 200), flow("s1", rate, rate * 0.9)], "execution": {}})
        os.environ["NS3_TWIN_RECORDINGS"] = self.path

    def tearDown(self):
        os.environ.pop("NS3_TWIN_RECORDINGS", None)

    def test_exact_scenarios_replay_as_recorded(self):
        rep = CeragonNs3TwinRunner(mode="replay").run("# comment\n" + self.TEXT.format(rate=500), sim_time=8.0)
        self.assertTrue(rep["execution"]["replay"]["exact"])
        self.assertEqual(rep["execution"]["mode"], "replay")

    def test_other_rates_and_names_get_the_nearest_recorded_run_and_say_so(self):
        text = self.TEXT.format(rate=700).replace("flow s1 ", "flow slice-x ")
        rep = CeragonNs3TwinRunner(mode="replay").run(text, sim_time=8.0)
        match = rep["execution"]["replay"]
        self.assertFalse(match["exact"])
        moved = {m["name"]: m for m in match["flows"]}
        self.assertEqual((moved["slice-x"]["recorded_mbps"], moved["slice-x"]["requested_mbps"]), (800.0, 700.0))
        self.assertIn("slice-x", [f["name"] for f in rep["flows"]])

    def test_unrecorded_shapes_are_refused(self):
        with self.assertRaises(RuntimeError):
            CeragonNs3TwinRunner(mode="replay").run("node a host 0 0\n", sim_time=8.0)

    def test_keys_ignore_comments_and_spacing(self):
        self.assertEqual(scenario_key("# x\nnode a  host 0 0\n", 8), scenario_key("node a host 0 0", 8.0))
        sig1, _ = scenario_shape(self.TEXT.format(rate=1), 8)
        sig2, _ = scenario_shape(self.TEXT.format(rate=2).replace("event", "x"), 8)
        self.assertEqual(sig1, sig2)


if __name__ == "__main__":
    unittest.main()
