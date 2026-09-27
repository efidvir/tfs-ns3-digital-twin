"""
Unit tests for SimulationResolutionGovernor
===========================================
Verifies:
1. Automatic mapping from simulation scenario goals to resolution tiers.
2. Operator explicit tier override capability.
3. Accurate KPI scoping (retained vs pruned metrics).
4. Correct NS-3 C++ module activation selection.
5. Graph scaling and scope factor calculations.
"""

import unittest
from simulation_resolution_governor import (
    SimulationResolutionGovernor,
    ResolutionTier,
    TIER_SPECIFICATIONS,
    GOAL_TO_TIER_MAP,
)


class TestSimulationResolutionGovernor(unittest.TestCase):

    def setUp(self):
        self.governor = SimulationResolutionGovernor()
        self.mock_topology = {
            "nodes": [{"uuid": f"node-{i}"} for i in range(34)],
            "links": [{"uuid": f"link-{i}"} for i in range(34)],
        }

    def test_goal_to_tier_resolution(self):
        """Test automatic mapping from scenarios to recommended fidelity tiers."""
        self.assertEqual(
            self.governor.resolve_tier("link_failure"),
            ResolutionTier.TIER_1_MACRO_TOPOLOGY
        )
        self.assertEqual(
            self.governor.resolve_tier("traffic_surge"),
            ResolutionTier.TIER_2_QUEUE_DYNAMICS
        )
        self.assertEqual(
            self.governor.resolve_tier("channel_degradation"),
            ResolutionTier.TIER_3_PHYSICAL_RF
        )
        self.assertEqual(
            self.governor.resolve_tier("slice_admission"),
            ResolutionTier.TIER_4_URLLC_MICRO
        )
        self.assertEqual(
            self.governor.resolve_tier("energy_saving_sleep"),
            ResolutionTier.TIER_5_ENERGY_MACRO
        )

    def test_explicit_tier_override(self):
        """Test that explicit operator tier requests override default mapping."""
        # For a link_failure scenario, override with full URLLC micro resolution
        scoped = self.governor.scope_simulation(
            tfs_topology=self.mock_topology,
            scenario_goal="link_failure",
            requested_tier="urllc_micro"
        )
        self.assertEqual(scoped.tier, ResolutionTier.TIER_4_URLLC_MICRO)
        self.assertEqual(scoped.fidelity_factor_pct, 95)
        self.assertIn("ns3::FlowMonitorHelper", scoped.activated_ns3_modules)

    def test_tier_1_macro_scoping(self):
        """Tier 1 must retain routing topology but prune RF and packet queues."""
        scoped = self.governor.scope_simulation(
            tfs_topology=self.mock_topology,
            scenario_goal="link_failure"
        )
        self.assertEqual(scoped.tier_number, 1)
        self.assertEqual(scoped.scoped_nodes_count, 34)  # 100% graph scope
        self.assertIn("link_status (UP/DOWN)", scoped.retained_kpis)
        self.assertIn("rf_carrier_frequency_ghz", scoped.pruned_kpis)
        self.assertIn("ns3::Ipv4GlobalRoutingHelper", scoped.activated_ns3_modules)

    def test_tier_3_physical_rf_scoping(self):
        """Tier 3 must retain rain attenuation and carrier parameters but prune global routing."""
        scoped = self.governor.scope_simulation(
            tfs_topology=self.mock_topology,
            scenario_goal="channel_degradation"
        )
        self.assertEqual(scoped.tier_number, 3)
        self.assertIn("carrier_frequency_ghz", scoped.retained_kpis)
        self.assertIn("rain_intensity_mm_hr", scoped.retained_kpis)
        self.assertIn("active_mcs_constellation", scoped.retained_kpis)
        self.assertIn("multi_hop_core_ip_routing", scoped.pruned_kpis)
        self.assertIn("ns3::PropagationLossModel", scoped.activated_ns3_modules)
        self.assertLess(scoped.scoped_nodes_count, 34)  # Sub-graph isolation

    def test_tier_4_urllc_micro_scoping(self):
        """Tier 4 must activate microsecond FlowMonitor and jitter windows."""
        scoped = self.governor.scope_simulation(
            tfs_topology=self.mock_topology,
            scenario_goal="slice_admission"
        )
        self.assertEqual(scoped.tier_number, 4)
        self.assertEqual(scoped.fidelity_factor_pct, 95)
        self.assertIn("5qi_qos_identifier", scoped.retained_kpis)
        self.assertIn("per_packet_arrival_timestamps_us", scoped.retained_kpis)
        self.assertIn("ns3::FlowMonitorHelper", scoped.activated_ns3_modules)

    def test_governor_digest_formatting(self):
        """Ensure governor produces clear human-readable explanations."""
        scoped = self.governor.scope_simulation(
            tfs_topology=self.mock_topology,
            scenario_goal="traffic_surge"
        )
        self.assertIn("Resolution Governor:", scoped.governor_digest)
        self.assertIn("Tier 2: Queue & Congestion Dynamics", scoped.governor_digest)
        self.assertIn("55% fidelity", scoped.governor_digest)


if __name__ == "__main__":
    unittest.main()
