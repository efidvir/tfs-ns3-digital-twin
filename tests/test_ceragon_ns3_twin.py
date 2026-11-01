"""Unit tests for the NS-3.45 Ceragon Functional Digital Twin (contrib/ceragon) and TFS bridge."""
from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

from ns3_ceragon.tools.tfs_to_ceragon_twin import convert, resolve

REPO_ROOT = Path(__file__).resolve().parent.parent
CONTRIB_DIR = REPO_ROOT / "ns3_ceragon" / "contrib" / "ceragon"


class TestCeragonNs3FunctionalTwin(unittest.TestCase):
    def test_contrib_ceragon_module_files_present(self) -> None:
        expected = [
            "CMakeLists.txt",
            "README.md",
            "doc/ceragon.rst",
            "model/ceragon-portfolio.h",
            "model/ceragon-portfolio.cc",
            "model/ceragon-acm.h",
            "model/ceragon-acm.cc",
            "model/ceragon-propagation.h",
            "model/ceragon-propagation.cc",
            "model/ceragon-radio-header.h",
            "model/ceragon-radio-header.cc",
            "model/ceragon-radio-channel.h",
            "model/ceragon-radio-channel.cc",
            "model/ceragon-radio-net-device.h",
            "model/ceragon-radio-net-device.cc",
            "model/ceragon-qos-queue-disc.h",
            "model/ceragon-qos-queue-disc.cc",
            "model/ceragon-oran-xhaul.h",
            "model/ceragon-oran-xhaul.cc",
            "helper/ceragon-helper.h",
            "helper/ceragon-helper.cc",
            "helper/ceragon-twin-helper.h",
            "helper/ceragon-twin-helper.cc",
            "test/ceragon-test-suite.cc",
            "examples/CMakeLists.txt",
            "examples/ceragon-portfolio-twin.cc",
            "examples/ceragon-multiband-rain.cc",
            "examples/ceragon-tsn-fronthaul.cc",
            "examples/ceragon-terragraph-mesh.cc",
            "examples/ceragon-protection-switchover.cc",
            "examples/ceragon-twin-from-file.cc",
            "examples/topologies/metro-ring.twin",
        ]
        for rel in expected:
            self.assertTrue((CONTRIB_DIR / rel).is_file(), f"Missing: {rel}")

    def test_cpp_portfolio_has_all_31_models_and_5_fallbacks(self) -> None:
        cpp_text = (CONTRIB_DIR / "model" / "ceragon-portfolio.cc").read_text(encoding="utf-8")
        cpp_explicit = set(re.findall(r'Spec\(\s*"([^"]+)"', cpp_text))
        self.assertEqual(len(cpp_explicit), 31)
        self.assertIn("MH-T261", cpp_explicit)
        self.assertIn("IP-50EX", cpp_explicit)
        self.assertIn("IP-100E", cpp_explicit)
        self.assertIn("EH-8010FX", cpp_explicit)
        self.assertIn("IP-20C", cpp_explicit)
        for model in cpp_explicit:
            resolved = resolve(model)
            self.assertIsNotNone(resolved, f"Failed to resolve {model}")

    def test_tfs_topology_to_ceragon_twin_conversion(self) -> None:
        sample_topo = {
            "source": "TeraFlowSDN",
            "nodes": [
                {"id": "dn-sector-1", "model": "MH-N366", "x": 10, "y": 20},
                {"id": "cn-rooftop-1", "model": "MH-T261", "x": 25, "y": 20},
                {"id": "core-eband-1", "model": "IP-50EX", "x": 0, "y": 0},
                {"id": "core-dc", "model": "O-CU", "x": -10, "y": 0, "role": "core"},
                {"id": "edge-ru", "model": "O-RU", "x": 35, "y": 20, "role": "ru"},
            ],
            "links": [
                {"src": "dn-sector-1", "dst": "cn-rooftop-1", "role": "60ghz", "distance_km": 0.25},
                {"src": "dn-sector-1", "dst": "core-eband-1", "role": "eband", "distance_km": 1.8},
                {"src": "core-dc", "dst": "core-eband-1", "capacity_gbps": 25},
                {"src": "cn-rooftop-1", "dst": "edge-ru", "capacity_gbps": 10},
            ],
            "devices": {
                "core-eband-1": {
                    "configs": {
                        "tsn": {"parameters": {"cycle_time_us": 500}},
                        "security": {"parameters": {}},
                    }
                }
            },
        }
        twin_text = convert(sample_topo, rain=(1.0, 2.0, 80.0), auto_flows=1)
        self.assertIn("node dn-sector-1", twin_text)
        self.assertIn("link dn-sector-1 cn-rooftop-1 model=MH-N366 distance=250", twin_text)
        self.assertIn("link dn-sector-1 core-eband-1 model=IP-50EX distance=1800", twin_text)
        self.assertIn("rain 1 2 80", twin_text)


if __name__ == "__main__":
    unittest.main()
