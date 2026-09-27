"""
Unit tests for Telecom Digital Twin API and TFS Client
"""
import os
import sys
import unittest

# Ensure parent and src are in path
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
            name="Test-Transport-Twin",
            scope="unit-test-backhaul",
            tfs_client=self.tfs_client
        )

    def test_ndti_initial_state(self):
        self.assertEqual(self.ndti.state, NDTIState.INITIALIZING)

    def test_ndti_sync_from_physical(self):
        sync_res = self.ndti.sync_from_physical()
        self.assertEqual(sync_res["state"], NDTIState.SYNCHRONIZED)
        self.assertGreater(sync_res["nodes_count"], 0)
        self.assertGreater(sync_res["links_count"], 0)

    def test_dti_what_if_scenario_rain_fade(self):
        self.ndti.sync_from_physical()
        scenario_req = {
            "scenario_id": "TEST-SC-01",
            "base_state": "current-network",
            "engine": "ns3-itur-p838",
            "perturbations": [
                {
                    "device_uuid": "f676623c-1a65-54bd-b1e8-279c8a6d8a1c",
                    "type": "rain_fade",
                    "rain_rate_mm_hr": 45.0,
                    "link_distance_km": 0.8
                }
            ]
        }
        res = self.ndti.execute_what_if_scenario(scenario_req)
        self.assertEqual(res["scenario_id"], "TEST-SC-01")
        self.assertEqual(len(res["predicted_impacts"]), 1)
        impact = res["predicted_impacts"][0]
        self.assertGreater(impact["attenuation_db"], 5.0)
        self.assertIn("recommended_mitigation", res)

    def test_closed_loop_safety_validation(self):
        self.ndti.sync_from_physical()
        valid_plan = {
            "device_uuid": "f676623c-1a65-54bd-b1e8-279c8a6d8a1c",
            "actions": [
                {"type": "ACM_FLOOR_HARDENING", "min_mcs": 2},
                {"type": "CARRIER_FREQUENCY_RETUNE", "target_ghz": 64.8, "target_bw_mhz": 2000}
            ]
        }
        val_res = self.ndti.validate_and_close_loop(valid_plan)
        self.assertTrue(val_res["safety_check"])
        self.assertEqual(val_res["status"], "APPLIED_AND_VERIFIED")

    def test_closed_loop_safety_rejection(self):
        self.ndti.sync_from_physical()
        invalid_plan = {
            "device_uuid": "f676623c-1a65-54bd-b1e8-279c8a6d8a1c",
            "actions": [
                {"type": "CARRIER_FREQUENCY_RETUNE", "target_ghz": 120.0} # Outside V-Band range
            ]
        }
        val_res = self.ndti.validate_and_close_loop(invalid_plan)
        self.assertFalse(val_res["safety_check"])
        self.assertEqual(val_res["status"], "VALIDATION_FAILED")


if __name__ == "__main__":
    unittest.main()
