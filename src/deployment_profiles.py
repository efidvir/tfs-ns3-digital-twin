"""
Deployment Profiles & Decoupled Configuration Architecture
==========================================================
Allows the TFS-NS3 Telecom Digital Twin to be instantiated by any user or researcher
without coupling to a specific developer laptop, VPN, or physical lab infrastructure:

1. STANDALONE (Default):
   - Zero external hardware or server dependencies.
   - Out-of-the-box experience for any user cloning from GitHub:
       git clone https://github.com/efidvir/tfs-ns3-digital-twin.git
       python web_dashboard.py
   - Uses bundled 6G transport descriptors (data/6g_transport_tfs_descriptors.json).
   - In-memory synthetic Ceragon MultiHaul TG telemetry and analytical NS-3 co-simulation.

2. LOCAL_CERAGON_LAB:
   - Configured specifically for the physical lab deployment:
     - TFS Controller: http://localhost:8088 (WebUI: :8004)
     - Physical Transceiver: 192.168.1.225 (Ceragon MH-T261 / ctu-96)
     - NS-3 Remote Host: efid@cersrv-029 (/home/efid/ns3-dev/ns3)
     - Device UUID: f676623c-1a65-54bd-b1e8-279c8a6d8a1c

3. CUSTOM:
   - Configured dynamically via CLI flags, environment variables, or custom JSON config file.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger("DeploymentProfiles")

DEFAULT_DATA_DIR = Path(__file__).parent / "data"
DEFAULT_DESCRIPTORS_FILE = DEFAULT_DATA_DIR / "6g_transport_tfs_descriptors.json"


class DeploymentMode(str, Enum):
    STANDALONE = "standalone"
    LOCAL_CERAGON_LAB = "local-ceragon"
    CUSTOM = "custom"


@dataclass
class DeploymentConfig:
    profile_name: str = "standalone"
    mode: DeploymentMode = DeploymentMode.STANDALONE
    description: str = "Standalone self-contained digital twin simulation (0 hardware dependencies)"

    # TFS SDN Controller parameters
    tfs_url: str = "http://localhost:8088"
    tfs_webui_url: str = "http://localhost:8004"
    tfs_token: Optional[str] = None
    tfs_context: str = "admin"
    tfs_topology: str = "admin"
    use_mock_tfs: bool = True

    # Physical / Simulated Device parameters
    device_ip: str = "192.168.1.225"
    device_port: int = 80
    device_user: str = "admin"
    device_pass: str = "admin"
    device_uuid: str = "f676623c-1a65-54bd-b1e8-279c8a6d8a1c"
    device_name: str = "Ceragon MH-T261 (ctu-96)"
    device_model: str = "Ceragon MultiHaul TG (60 GHz V-Band)"
    use_mock_hw: bool = True

    # NS-3 Simulation Core parameters
    ns3_mode: str = "analytical_co_sim"  # "remote_ssh", "local_binary", "analytical_co_sim"
    ns3_host: str = "cersrv-029"
    ns3_path: str = "/home/efid/ns3-dev/ns3"
    ns3_remote_user: str = "efid"
    use_mock_ns3: bool = True

    # Fallback and runtime ports
    descriptor_fallback_path: str = str(DEFAULT_DESCRIPTORS_FILE)
    web_port: int = 9200
    api_port: int = 9100

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["mode"] = self.mode.value
        return d


# Pre-defined Profiles
PROFILES: Dict[str, DeploymentConfig] = {
    # 1. Standalone Profile: Zero dependencies, works anywhere
    "standalone": DeploymentConfig(
        profile_name="standalone",
        mode=DeploymentMode.STANDALONE,
        description="Self-contained sandbox digital twin (works anywhere, 0 external dependencies)",
        tfs_url="http://localhost:8088",
        tfs_webui_url="",
        use_mock_tfs=True,
        device_ip="127.0.0.1",
        device_uuid="f676623c-1a65-54bd-b1e8-279c8a6d8a1c",
        device_name="Simulated Ceragon MH-T261 (ctu-96)",
        device_model="Ceragon MultiHaul TG (60 GHz V-Band Simulation)",
        use_mock_hw=True,
        ns3_mode="analytical_co_sim",
        ns3_host="localhost",
        ns3_path="ns3",
        use_mock_ns3=True,
        web_port=9200,
        api_port=9100,
    ),

    # 2. Local Ceragon Lab Profile: Matches this specific physical setup
    "local-ceragon": DeploymentConfig(
        profile_name="local-ceragon",
        mode=DeploymentMode.LOCAL_CERAGON_LAB,
        description="Physical Ceragon hardware + ETSI TeraFlowSDN + remote NS-3 on cersrv-029",
        tfs_url=os.getenv("TFS_URL", "http://localhost:8088"),
        tfs_webui_url=os.getenv("TFS_WEBUI_URL", "http://localhost:8004"),
        use_mock_tfs=False,
        device_ip=os.getenv("CERAGON_IP", "192.168.1.225"),
        device_port=80,
        device_user=os.getenv("CERAGON_USER", "admin"),
        device_pass=os.getenv("CERAGON_PASS", "admin"),
        device_uuid="f676623c-1a65-54bd-b1e8-279c8a6d8a1c",
        device_name="Ceragon MH-T261 (ctu-96)",
        device_model="Siklu / Ceragon MultiHaul TG (MH-T261)",
        use_mock_hw=False,
        ns3_mode="remote_ssh",
        ns3_host=os.getenv("NS3_HOST", "cersrv-029"),
        ns3_path=os.getenv("NS3_PATH", "/home/efid/ns3-dev/ns3"),
        ns3_remote_user="efid",
        use_mock_ns3=False,
        web_port=9200,
        api_port=9100,
    ),
}

# Alias mapping
PROFILES["demo"] = PROFILES["standalone"]
PROFILES["local"] = PROFILES["local-ceragon"]
PROFILES["ceragon-lab"] = PROFILES["local-ceragon"]


def load_deployment_config(
    profile_name: Optional[str] = None,
    config_file: Optional[str] = None,
    overrides: Optional[Dict[str, Any]] = None,
) -> DeploymentConfig:
    """
    Loads deployment configuration resolving in order:
    1. Base profile (standalone, local-ceragon, custom).
    2. Optional JSON config file.
    3. Environment variables (TFS_URL, CERAGON_IP, NS3_HOST, etc.).
    4. Explicit programmatic or CLI overrides.
    """
    # 1. Determine profile
    requested_profile = (
        profile_name
        or os.getenv("DIGITAL_TWIN_PROFILE")
        or "standalone"
    ).lower().strip()

    if config_file and os.path.exists(config_file):
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            config = DeploymentConfig(**data)
            logger.info(f"Loaded deployment config from file: {config_file}")
            return config
        except Exception as e:
            logger.warning(f"Failed to load config file {config_file}: {e}; falling back to profile.")

    base_config = PROFILES.get(requested_profile, PROFILES["standalone"])
    # Copy attributes to create fresh instance
    config = DeploymentConfig(**asdict(base_config))

    # 2. Check Environment Variables for overrides
    if "TFS_URL" in os.environ:
        config.tfs_url = os.environ["TFS_URL"]
        config.use_mock_tfs = False
    if "CERAGON_IP" in os.environ:
        config.device_ip = os.environ["CERAGON_IP"]
        config.use_mock_hw = False
    if "NS3_HOST" in os.environ:
        config.ns3_host = os.environ["NS3_HOST"]
        config.use_mock_ns3 = False
    if "NS3_PATH" in os.environ:
        config.ns3_path = os.environ["NS3_PATH"]

    # 3. Apply programmatic overrides
    if overrides:
        for k, v in overrides.items():
            if hasattr(config, k) and v is not None:
                setattr(config, k, v)

    logger.info(
        f"Initialized Digital Twin Deployment Config: [{config.profile_name.upper()}] "
        f"(TFS: {config.tfs_url} [mock={config.use_mock_tfs}], "
        f"HW: {config.device_ip} [mock={config.use_mock_hw}], "
        f"NS-3: {config.ns3_host} [mode={config.ns3_mode}])"
    )
    return config


def add_deployment_cli_args(parser: argparse.ArgumentParser) -> None:
    """Adds standard deployment arguments to an existing ArgumentParser."""
    group = parser.add_argument_group("Deployment Profile & Topology Options")
    group.add_argument(
        "--profile",
        choices=["standalone", "local-ceragon", "demo", "local"],
        default="standalone",
        help="Deployment profile: 'standalone' (0 dependencies, self-contained GitHub clone) or 'local-ceragon' (local lab hardware and TFS). Default: standalone",
    )
    group.add_argument(
        "--config-file",
        type=str,
        default=None,
        help="Path to custom JSON deployment configuration file.",
    )
    group.add_argument(
        "--tfs-url",
        type=str,
        default=None,
        help="ETSI TeraFlowSDN Northbound REST URL (e.g., http://localhost:8088)",
    )
    group.add_argument(
        "--device-ip",
        type=str,
        default=None,
        help="Physical Ceragon hardware IP address (e.g., 192.168.1.225)",
    )
    group.add_argument(
        "--device-uuid",
        type=str,
        default=None,
        help="Target device UUID registered in TeraFlowSDN",
    )
    group.add_argument(
        "--ns3-host",
        type=str,
        default=None,
        help="NS-3 execution host (e.g., cersrv-029 or localhost)",
    )
    group.add_argument(
        "--ns3-path",
        type=str,
        default=None,
        help="Path to ns-3 binary or repository (e.g., /home/efid/ns3-dev/ns3)",
    )
    group.add_argument(
        "--port",
        type=int,
        default=9200,
        help="Web dashboard HTTP port (default: 9200)",
    )
