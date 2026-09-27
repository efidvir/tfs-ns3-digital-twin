"""
Unit tests for Generic Multi-Domain Telecom Digital Twin API and TFS Client
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from src.tfs_api_client import TfsApiClient
from src.tfs_digital_twin_api import NetworkDigitalTwinInstance, NDTIState

class TestTelecomDigitalTwin(unittest.TestCase):
    def setUp(self):
        desc_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "6g_transport_tfs_descriptors.json"))
        self.tfs_client = TfsApiClient(rest_url="http://localhost:8088", descriptor_fallback_path=desc_path)
        self.ndti = NetworkDigitalTwinInstance(
            instance_id="test-ndti-01",
            name="Test-Universal-Transport-Twin",
            scope="unit-test-multi-domain",
            tfs_client=self.tfs_client
        )
        self.ndti.sync_from_physical()

    def test_ndti_sync_from_physical(self):
        self.assertEqual(self.ndti.state, NDTIState.SYNCHRONIZED)
        self.assertGreater(len(self.ndti.topology_shadow.get("nodes", [])), 0)
        self.assertGreater(len(self.ndti.topology_shadow.get("links", [])), 0)

    # 1. Traffic Engineering & Congestion Surge Test
    def test_scenario_traffic_surge(self):
        scenario_req = {
            "scenario_id": "TEST-TRAFFIC-SURGE",
            "domain": "TRAFFIC_ENGINEERING",
            "perturbations": [
                {
                    "device_uuid": "f676623c-1a65-54bd-b1e8-279c8a6d8a1c",
                    "type": "traffic_surge",
                    "traffic_multiplier": 3.2
                }
            ]
        }
        res = self.ndti.execute_what_if_scenario(scenario_req)
        self.assertEqual(res["scenario_id"], "TEST-TRAFFIC-SURGE")
        impact = res["predicted_impacts"][0]
        self.assertEqual(impact["domain"], "TRAFFIC_ENGINEERING")
        self.assertGreater(impact["predicted_queue_buffer_occupancy_pct"], 80.0)
        self.assertTrue(impact["sla_breach_detected"])
        self.assertIn("recommended_mitigation", res)

    # 2. Topology Dynamics & Fiber Cut / Protection Switching Test
    def test_scenario_link_failure(self):
        scenario_req = {
            "scenario_id": "TEST-FIBER-CUT",
            "domain": "TOPOLOGY_RESILIENCE",
            "perturbations": [
                {
                    "type": "link_failure",
                    "link_uuid": "link-core-to-metro-01"
                }
            ]
        }
        res = self.ndti.execute_what_if_scenario(scenario_req)
        impact = res["predicted_impacts"][0]
        self.assertEqual(impact["domain"], "TOPOLOGY_RESILIENCE")
        self.assertEqual(impact["link_status"], "DOWN")
        self.assertLess(impact["switchover_time_ms"], 50.0) # Sub-50ms carrier requirement
        self.assertFalse(impact["sla_breach_detected"])

    # 3. Green Telco Energy Optimization Test
    def test_scenario_energy_sleep(self):
        scenario_req = {
            "scenario_id": "TEST-ENERGY-SLEEP",
            "domain": "ENERGY_OPTIMIZATION",
            "perturbations": [
                {
                    "device_uuid": "f676623c-1a65-54bd-b1e8-279c8a6d8a1c",
                    "type": "energy_saving_sleep",
                    "sectors": ["Sector-2", "Sector-3"],
                    "window": "01:00-05:00"
                }
            ]
        }
        res = self.ndti.execute_what_if_scenario(scenario_req)
        impact = res["predicted_impacts"][0]
        self.assertEqual(impact["domain"], "ENERGY_OPTIMIZATION")
        self.assertGreater(impact["power_saved_watts"], 40.0)
        self.assertFalse(impact["sla_breach_detected"]) # Safe to sleep

    # 4. Multi-Tenant Slice Admission Test
    def test_scenario_slice_admission(self):
        scenario_req = {
            "scenario_id": "TEST-SLICE-ADMISSION",
            "domain": "SLICE_ADMISSION_CONTROL",
            "perturbations": [
                {
                    "device_uuid": "f676623c-1a65-54bd-b1e8-279c8a6d8a1c",
                    "type": "slice_admission",
                    "slice_id": "slice-connected-ambulance",
                    "bandwidth_mbps": 300.0,
                    "max_latency_ms": 1.5
                }
            ]
        }
        res = self.ndti.execute_what_if_scenario(scenario_req)
        impact = res["predicted_impacts"][0]
        self.assertEqual(impact["domain"], "SLICE_ADMISSION_CONTROL")
        self.assertEqual(impact["admission_decision"], "GRANTED")

    # 5. Channel Fading / Atmospheric Degradation Test
    def test_scenario_channel_degradation(self):
        scenario_req = {
            "scenario_id": "TEST-RAIN-FADE",
            "domain": "PHYSICAL_CHANNEL_PROPAGATION",
            "perturbations": [
                {
                    "device_uuid": "f676623c-1a65-54bd-b1e8-279c8a6d8a1c",
                    "type": "rain_fade",
                    "rain_rate_mm_hr": 50.0,
                    "link_distance_km": 0.8
                }
            ]
        }
        res = self.ndti.execute_what_if_scenario(scenario_req)
        impact = res["predicted_impacts"][0]
        self.assertEqual(impact["domain"], "PHYSICAL_CHANNEL_PROPAGATION")
        self.assertGreater(impact["attenuation_db"], 10.0)

    # 6. Closed-Loop Safety Verification Test
    def test_closed_loop_safety_validation(self):
        valid_plan = {
            "device_uuid": "f676623c-1a65-54bd-b1e8-279c8a6d8a1c",
            "actions": [
                {"type": "DYNAMIC_QOS_SLICING", "rate_mbps": 1200},
                {"type": "CSPF_REROUTE_OPTIMIZATION"},
                {"type": "ENERGY_SLEEP_POLICY_ACTIVATE", "power_savings_w": 48.0}
            ]
        }
        val_res = self.ndti.validate_and_close_loop(valid_plan)
        self.assertTrue(val_res["safety_check"])
        self.assertEqual(val_res["status"], "APPLIED_AND_VERIFIED")

    # 7. Safety Rejection Test
    def test_closed_loop_safety_rejection(self):
        invalid_plan = {
            "device_uuid": "f676623c-1a65-54bd-b1e8-279c8a6d8a1c",
            "actions": [
                {"type": "CARRIER_FREQUENCY_RETUNE", "target_ghz": 150.0} # Outside legal V-Band
            ]
        }
        val_res = self.ndti.validate_and_close_loop(invalid_plan)
        self.assertFalse(val_res["safety_check"])
        self.assertEqual(val_res["status"], "VALIDATION_FAILED")


if __name__ == "__main__":
    unittest.main()
