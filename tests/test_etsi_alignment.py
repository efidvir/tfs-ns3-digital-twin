"""
Twin alignment with the ETSI stack: RFC 8345 topology import, simulated
labels on what-if answers, the /what-if and /healthz routes, and MCP tools.
"""
import asyncio
import inspect
import json
import os
import sys
import threading
import unittest
import urllib.request
from http.server import HTTPServer

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

import tfs_digital_twin_api as twin_api  # noqa: E402
from rfc8345_import import to_twin_topology  # noqa: E402


def _link(a, a_tp, b, b_tp, kbps=None):
    link = {"link-id": f"{a}/{a_tp}=={b}/{b_tp}",
            "source": {"source-node": a, "source-tp": a_tp},
            "destination": {"dest-node": b, "dest-tp": b_tp}}
    if kbps is not None:
        link["ietf-te-topology:te"] = {"te-link-attributes": {
            "max-link-bandwidth": {"te-bandwidth": {"ietf-eth-te-topology:eth-bandwidth": kbps}}}}
    return link


def _node(node_id, *tps):
    return {"node-id": node_id, "ietf-network-topology:termination-point": [{"tp-id": tp} for tp in tps]}


RFC8345 = {"ietf-network:networks": {"network": [{
    "network-id": "admin",
    "node": [_node("pe-1", "ge-0/0/1", "eth1"), _node("radio-a", "eth1", "rf-sector-1"),
             _node("radio-b", "rf-sector-1", "eth1"), _node("pe-2", "eth1", "ge-0/0/1")],
    "ietf-network-topology:link": [
        _link("pe-1", "eth1", "radio-a", "eth1", kbps=10_000_000),
        _link("radio-a", "eth1", "pe-1", "eth1", kbps=10_000_000),          # reverse direction
        _link("radio-a", "rf-sector-1", "radio-b", "rf-sector-1", kbps=1_800_000),
        _link("radio-b", "eth1", "pe-2", "eth1"),                            # no TE attributes
        _link("pe-2", "eth1", "ghost", "eth1"),                              # unknown node
    ],
}]}}


class FakeTFS:
    def __init__(self, rfc8345_ok=True):
        self.rfc8345_ok = rfc8345_ok

    def get_rfc8345_networks(self):
        if not self.rfc8345_ok:
            raise RuntimeError("HTTP 404")
        return RFC8345

    def get_topology_model(self):
        return [{"uuid": "x", "name": "x"}], []

    def get_device_telemetry(self, uuid):
        return {"device": uuid}


class TestRfc8345Import(unittest.TestCase):
    def test_nodes_links_capacity_and_radio_marking(self):
        devices, links = to_twin_topology(RFC8345)
        self.assertEqual([d["uuid"] for d in devices], ["pe-1", "pe-2", "radio-a", "radio-b"])
        self.assertEqual(len(links), 3)  # reverse duplicate and dangling link dropped
        radio_link = next(l for l in links if l["src_endpoint"] == "rf-sector-1")
        self.assertTrue(radio_link["is_wireless"])
        self.assertEqual(radio_link["delay"], "0.5ms")
        self.assertAlmostEqual(radio_link["total_capacity_gbps"], 1.8)
        self.assertEqual(radio_link["capacity_source"], "rfc8795-te")
        plain = next(l for l in links if l["dst_uuid"] == "pe-2")
        self.assertEqual(plain["capacity_source"], "default")
        self.assertTrue(next(d for d in devices if d["uuid"] == "radio-a")["is_ceragon"])

    def test_document_without_networks_is_rejected(self):
        with self.assertRaises(ValueError):
            to_twin_topology({"ietf-network:networks": {}})


class TestTwinSyncAndLabels(unittest.TestCase):
    def setUp(self):
        self._source = twin_api.TOPOLOGY_SOURCE

    def tearDown(self):
        twin_api.TOPOLOGY_SOURCE = self._source

    def _twin(self, client):
        return twin_api.NetworkDigitalTwinInstance("t1", "test", "unit", client)

    def test_sync_from_rfc8345(self):
        twin_api.TOPOLOGY_SOURCE = "rfc8345"
        twin = self._twin(FakeTFS())
        res = twin.sync_from_physical()
        self.assertEqual(res["topology_source"], "rfc8345")
        self.assertEqual(res["nodes_count"], 4)

    def test_falls_back_to_the_tfs_api(self):
        twin_api.TOPOLOGY_SOURCE = "rfc8345"
        twin = self._twin(FakeTFS(rfc8345_ok=False))
        self.assertEqual(twin.sync_from_physical()["topology_source"], "tfs-api")

    def test_offline_descriptor_fallback_is_named_in_the_basis(self):
        import tempfile
        from tfs_api_client import TfsApiClient
        twin_api.TOPOLOGY_SOURCE = "tfs-api"
        descriptors = {"devices": [{"device_id": {"device_uuid": {"uuid": "radio-a"}}, "device_type": "ceragon-wireless"}],
                       "links": []}
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            json.dump(descriptors, f)
        try:
            client = TfsApiClient(rest_url="http://127.0.0.1:9", timeout=1, descriptor_fallback_path=f.name)
            twin = self._twin(client)
            self.assertEqual(twin.sync_from_physical()["topology_source"], "descriptors")
            res = twin.execute_what_if_scenario({"perturbations": [], "engine": "analytical"})
            self.assertEqual(res["basis"]["topology_source"], "descriptors")
        finally:
            os.unlink(f.name)

    def test_what_if_answers_are_labelled_simulated(self):
        twin_api.TOPOLOGY_SOURCE = "rfc8345"
        twin = self._twin(FakeTFS())
        twin.sync_from_physical()
        res = twin.execute_what_if_scenario({"perturbations": [], "engine": "analytical"})
        self.assertEqual(res["insight"], "simulated")
        self.assertEqual(res["basis"]["topology_source"], "rfc8345")
        self.assertEqual(res["basis"]["engine"], "analytical")


class TestHttpRoutes(unittest.TestCase):
    def test_what_if_and_health(self):
        twin = twin_api.NetworkDigitalTwinInstance(
            twin_api.DigitalTwinHttpHandler.default_ndti_id, "test", "unit", FakeTFS())
        twin.sync_from_physical()
        twin_api.DigitalTwinHttpHandler.ndti_manager[twin.instance_id] = twin
        httpd = HTTPServer(("127.0.0.1", 0), twin_api.DigitalTwinHttpHandler)
        thread = threading.Thread(target=httpd.serve_forever, daemon=True)
        thread.start()
        base = f"http://127.0.0.1:{httpd.server_address[1]}"
        try:
            with urllib.request.urlopen(f"{base}/healthz", timeout=5) as resp:
                health = json.loads(resp.read())
            self.assertEqual(health["status"], "ok")
            req = urllib.request.Request(f"{base}/what-if", data=json.dumps({"perturbations": []}).encode(),
                                         headers={"Content-Type": "application/json"}, method="POST")
            with urllib.request.urlopen(req, timeout=5) as resp:
                answer = json.loads(resp.read())
            self.assertEqual(answer["insight"], "simulated")
        finally:
            httpd.shutdown()
            twin_api.DigitalTwinHttpHandler.ndti_manager.pop(twin.instance_id, None)


class TestTwinMcp(unittest.TestCase):
    def test_tools_are_registered(self):
        try:
            import mcp  # noqa: F401
        except ImportError:
            self.skipTest("MCP SDK not installed")
        import twin_mcp
        server = twin_mcp.build_server()
        listed = server.list_tools()
        listed = asyncio.run(listed) if inspect.isawaitable(listed) else listed
        self.assertEqual({t.name for t in listed}, {"list_simulators", "sync_twin", "get_twin_state", "run_what_if"})

    def test_run_what_if_tool(self):
        import twin_mcp
        twin_mcp._Twin.instance = twin_api.NetworkDigitalTwinInstance("m1", "test", "unit", FakeTFS())
        try:
            twin_mcp.sync_twin()
            self.assertEqual(twin_mcp.get_twin_state()["nodes"], 1)
            self.assertEqual(twin_mcp.run_what_if([], engine="analytical")["insight"], "simulated")
        finally:
            twin_mcp._Twin.instance = None


if __name__ == "__main__":
    unittest.main()


class TestTwinMcpProxy(unittest.TestCase):
    def test_tools_share_the_http_twin(self):
        import twin_mcp
        twin = twin_api.NetworkDigitalTwinInstance(
            twin_api.DigitalTwinHttpHandler.default_ndti_id, "test", "unit", FakeTFS())
        twin_api.DigitalTwinHttpHandler.ndti_manager = {twin.instance_id: twin}
        httpd = HTTPServer(("127.0.0.1", 0), twin_api.DigitalTwinHttpHandler)
        threading.Thread(target=httpd.serve_forever, daemon=True).start()
        os.environ["TWIN_URL"] = f"http://127.0.0.1:{httpd.server_address[1]}"
        try:
            twin_mcp.sync_twin()
            state = twin_mcp.get_twin_state()
            self.assertEqual(state["nodes"], 1)
            self.assertEqual(twin_mcp.run_what_if([], engine="analytical")["insight"], "simulated")
            self.assertEqual(len(twin.scenarios), 1)  # ran on the HTTP API's twin
        finally:
            os.environ.pop("TWIN_URL", None)
            httpd.shutdown()
            twin_api.DigitalTwinHttpHandler.ndti_manager = {}
