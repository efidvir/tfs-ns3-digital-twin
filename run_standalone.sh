#!/usr/bin/env bash
# ==============================================================================
# TFS-NS3 Telecom Digital Twin: Standalone Mode (Zero Dependencies)
# ==============================================================================
# Runs completely in-memory using bundled 6G transport descriptors.
# Safe to run anywhere without access to Ceragon hardware, VPN, or remote hosts.
echo ""
echo "============================================================================"
echo "  Starting Standalone Telecom Digital Twin (0 External Dependencies)"
echo "============================================================================"
echo ""
python3 web_dashboard.py --profile standalone --port 9200
