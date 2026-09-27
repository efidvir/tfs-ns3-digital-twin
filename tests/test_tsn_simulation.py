"""
Unit tests for TSN Simulation Runner (Ceragon 4-Node Microwave + WiFi EDCA).
Verifies fallback discrete emulator logic, priority queuing models, and response formats.
"""

import unittest
from tsn_simulation_runner import TSNSimulationRunner

class TestTSNSimulationRunner(unittest.TestCase):
    def setUp(self):
        self.runner = TSNSimulationRunner(host="efid@cersrv-029", ns3_dir="/home/efid/ns3-dev")

    def test_baseline_tsn_simulation_fallback(self):
        """Test baseline simulation with TSN QoS enabled."""
        res = self.runner.run_tsn_simulation(
            sim_time=2.0,
            perturbation="none",
            enable_tsn_qos=True,
            use_remote=False
        )
        self.assertIn("flows", res)
        self.assertIn("tsn_urllc", res["flows"])
        self.assertIn("best_effort_burst", res["flows"])
        self.assertIn("ceragon_devices", res)
        self.assertEqual(len(res["ceragon_devices"]), 4)
        self.assertIn("wifi_access_points", res)
        self.assertEqual(len(res["wifi_access_points"]), 2)
        
        # Verify SLA compliance when QoS is active
        tsn_flow = res["flows"]["tsn_urllc"]
        self.assertLess(tsn_flow["mean_delay_ms"], 1.5)
        self.assertFalse(tsn_flow["sla_breached"])
        self.assertEqual(tsn_flow["wifi_access_category"], "AC_VO")

    def test_traffic_surge_without_qos_causes_sla_breach(self):
        """Test that turning off TSN QoS during traffic surge causes latency breach."""
        res = self.runner.run_tsn_simulation(
            sim_time=2.0,
            perturbation="traffic_surge",
            enable_tsn_qos=False,
            surge_multiplier=3.5,
            use_remote=False
        )
        tsn_flow = res["flows"]["tsn_urllc"]
        self.assertTrue(tsn_flow["sla_breached"])
        self.assertGreater(tsn_flow["mean_delay_ms"], 1.5)
        self.assertEqual(res["verdict"]["status"], "BREACH_PREDICTED")

    def test_ceragon_device_attributes(self):
        """Verify the 4 Ceragon devices reflect the microwave topology."""
        res = self.runner.run_tsn_simulation(sim_time=1.0, use_remote=False)
        devices = res["ceragon_devices"]
        self.assertEqual(len(devices), 4)
        self.assertIn("192.168.1.225", devices[0]["ip"])
        self.assertIn("60GHz", devices[0]["link_type"])
        self.assertIn("80GHz", devices[2]["link_type"])

    def test_wifi_edca_kpis(self):
        """Verify EDCA AC_VO has lower contention delay than AC_BE."""
        res = self.runner.run_tsn_simulation(sim_time=1.0, use_remote=False)
        aps = res["wifi_access_points"]
        ap_tsn = next(a for a in aps if a["edca_access_category"] == "AC_VO")
        ap_be = next(a for a in aps if a["edca_access_category"] == "AC_BE")
        self.assertLess(ap_tsn["mean_contention_delay_us"], ap_be["mean_contention_delay_us"])

if __name__ == "__main__":
    unittest.main()
