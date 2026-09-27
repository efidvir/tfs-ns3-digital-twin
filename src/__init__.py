"""
TFS-NS3 Digital Twin Package
=============================
Standardized Telecom Network Digital Twin (NDT) and NS-3 Co-Simulation Framework.
Standards: 3GPP TS 28.561 | ITU-T Y.3090 | IETF NMRG DTI | TM Forum ODA | ETSI OpenCAPIF
"""

from .tfs_api_client import TfsApiClient
from .tfs_digital_twin_api import NetworkDigitalTwinInstance, NDTIState
from .tfs_topology_to_ns3 import generate_cc_source

generate_ns3_script = generate_cc_source

__version__ = "1.0.0"
__all__ = [
    "TfsApiClient",
    "NetworkDigitalTwinInstance",
    "NDTIState",
    "generate_cc_source",
    "generate_ns3_script",
]
