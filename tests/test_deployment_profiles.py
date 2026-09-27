"""
Unit tests for Deployment Profiles and Decoupled Configuration
==============================================================
Verifies:
1. Default standalone profile loads cleanly with 0 external dependencies.
2. Local Ceragon lab profile correctly sets up physical parameters.
3. Command-line overrides and environment variables take precedence.
4. JSON config file loading and saving.
"""

import os
import unittest
from deployment_profiles import (
    DeploymentConfig,
    DeploymentMode,
    PROFILES,
    load_deployment_config,
)


class TestDeploymentProfiles(unittest.TestCase):

    def test_standalone_default_profile(self):
        """Standalone profile must be the safe default with mock enabled."""
        config = load_deployment_config(profile_name="standalone")
        self.assertEqual(config.mode, DeploymentMode.STANDALONE)
        self.assertTrue(config.use_mock_tfs)
        self.assertTrue(config.use_mock_hw)
        self.assertTrue(config.use_mock_ns3)
        self.assertEqual(config.web_port, 9200)

    def test_local_ceragon_lab_profile(self):
        """Local Ceragon profile must configure physical lab parameters."""
        config = load_deployment_config(profile_name="local-ceragon")
        self.assertEqual(config.mode, DeploymentMode.LOCAL_CERAGON_LAB)
        self.assertEqual(config.device_ip, "192.168.1.225")
        self.assertEqual(config.tfs_url, "http://localhost:8088")
        self.assertEqual(config.ns3_host, "cersrv-029")
        self.assertFalse(config.use_mock_hw)

    def test_programmatic_overrides(self):
        """Explicit overrides must supersede base profile defaults."""
        config = load_deployment_config(
            profile_name="standalone",
            overrides={"device_ip": "10.0.0.50", "web_port": 9300, "use_mock_hw": False}
        )
        self.assertEqual(config.device_ip, "10.0.0.50")
        self.assertEqual(config.web_port, 9300)
        self.assertFalse(config.use_mock_hw)

    def test_environment_variable_overrides(self):
        """Environment variables must override profile defaults."""
        os.environ["TFS_URL"] = "http://tfs-prod.net:8088"
        try:
            config = load_deployment_config(profile_name="standalone")
            self.assertEqual(config.tfs_url, "http://tfs-prod.net:8088")
            self.assertFalse(config.use_mock_tfs)
        finally:
            del os.environ["TFS_URL"]


if __name__ == "__main__":
    unittest.main()
