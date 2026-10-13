"""
IETF Transport Slicing, Topology & Energy Data Models (D3.1 Alignment)
"""
from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any


@dataclass
class ServiceLevelObjective:
    metric_type: str
    metric_unit: str
    metric_value: float
    slo_status: str = "COMPLIANT"


@dataclass
class ServiceLevelExpectation:
    expectation_type: str
    expectation_value: str
    enforcement_rule: Optional[str] = None


@dataclass
class SLOSLETemplate:
    id: str
    description: str
    slos: List[Dict[str, Any]] = field(default_factory=list)
    sles: List[Dict[str, Any]] = field(default_factory=list)

    def to_ietf_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "description": self.description,
            "metric-bounds": {
                "metric-bound": [
                    {
                        "metric-type": slo.get("metric_type"),
                        "metric-unit": slo.get("metric_unit"),
                        "bound": slo.get("metric_value")
                    } for slo in self.slos
                ]
            },
            "service-level-expectations": {
                "expectation": [
                    {
                        "expectation-type": sle.get("expectation_type"),
                        "value": sle.get("expectation_value"),
                        "policy": sle.get("enforcement_rule", "strict")
                    } for sle in self.sles
                ]
            }
        }


@dataclass
class ServiceDemarcationPoint:
    sdp_id: str
    node_id: str
    tp_id: str
    ip_address: Optional[str] = None
    vlan_id: Optional[int] = None
    dscp_code: Optional[int] = None

    def to_ietf_dict(self) -> Dict[str, Any]:
        d = {
            "id": self.sdp_id,
            "node-id": self.node_id,
            "service-match-criteria": {
                "match-criterion": [{"type": "interface", "value": self.tp_id}]
            }
        }
        if self.ip_address:
            d["service-match-criteria"]["match-criterion"].append({"type": "ip-address", "value": self.ip_address})
        if self.vlan_id:
            d["service-match-criteria"]["match-criterion"].append({"type": "vlan-id", "value": str(self.vlan_id)})
        if self.dscp_code is not None:
            d["service-match-criteria"]["match-criterion"].append({"type": "dscp", "value": str(self.dscp_code)})
        return d


@dataclass
class ConnectivityConstruct:
    construct_id: str
    connectivity_type: str
    src_sdp_id: str
    dst_sdp_id: str


@dataclass
class IETFSliceService:
    slice_id: str
    description: str
    slo_sle_template_ref: str
    sdps: List[ServiceDemarcationPoint] = field(default_factory=list)
    connectivity_constructs: List[ConnectivityConstruct] = field(default_factory=list)
    status: str = "active"
    computed_path: List[str] = field(default_factory=list)
    realization_technology: str = "L2SM"
    controller_reference: str = "TeraFlowSDN"
    created_at: float = field(default_factory=time.time)

    def to_ietf_dict(self) -> Dict[str, Any]:
        return {
            "id": self.slice_id,
            "description": self.description,
            "slo-sle-policy": {"slo-sle-template": self.slo_sle_template_ref},
            "status": self.status,
            "sdps": {"sdp": [sdp.to_ietf_dict() for sdp in self.sdps]},
            "connection-groups": {
                "connection-group": [
                    {
                        "id": f"cg-{self.slice_id}",
                        "connectivity-construct": [
                            {
                                "id": cc.construct_id,
                                "type": cc.connectivity_type,
                                "p2p-sender-sdp": cc.src_sdp_id,
                                "p2p-receiver-sdp": cc.dst_sdp_id
                            } for cc in self.connectivity_constructs
                        ]
                    }
                ]
            },
            "custom-topology": {
                "realization-technology": self.realization_technology,
                "computed-path": self.computed_path,
                "controller": self.controller_reference
            }
        }


@dataclass
class TVRScheduleItem:
    schedule_id: str
    target_element_id: str
    element_type: str
    start_time_iso: str
    duration_seconds: int
    scheduled_state: str
    predicted_capacity_mbps: Optional[float] = None
    predicted_attenuation_db: Optional[float] = None
    reason: str = "scheduled-event"


@dataclass
class InstantaneousDeviceEnergy:
    name: str
    power: float
    energy_mode: str
    energy_efficiency: float
    configuration_summary: str
    transceivers_summary: str
    boards_summary: str
    ambient_temperature: float
    cpu_load: int
    fan_speed: int
    traffic_type: str
    traffic_throughput_gbps: float
    traffic_packet_size_bytes: int
    power_supplies: List[Dict[str, Any]] = field(default_factory=list)
    boards: List[Dict[str, Any]] = field(default_factory=list)
    transceivers: List[Dict[str, Any]] = field(default_factory=list)
    components: List[Dict[str, Any]] = field(default_factory=list)

    def to_yang_dict(self) -> Dict[str, Any]:
        return {
            "instantaneous-device-energy-tid:device": {
                "name": self.name,
                "power": str(round(self.power, 2)),
                "energy-mode": self.energy_mode,
                "energy-efficiency": str(round(self.energy_efficiency, 6)),
                "configuration": {
                    "configuration": self.configuration_summary,
                    "transceivers": self.transceivers_summary,
                    "boards": self.boards_summary,
                },
                "performance-metrics": {
                    "ambient-temperature": round(self.ambient_temperature, 1),
                    "cpu-load": self.cpu_load,
                    "fan-speed": self.fan_speed,
                    "traffic-type": self.traffic_type,
                    "traffic-throughput": str(round(self.traffic_throughput_gbps, 3)),
                    "traffic-packet-size": self.traffic_packet_size_bytes,
                },
                "power-supply": self.power_supplies,
                "boards": self.boards,
                "transceivers": self.transceivers,
                "components": self.components,
            }
        }


@dataclass
class StaticDeviceEnergy:
    name: str
    typical_power: float
    nominal_power: float
    max_power: float
    maximum_traffic_throughput: str
    efficiency: float
    power_supplies: List[Dict[str, Any]] = field(default_factory=list)
    boards: List[Dict[str, Any]] = field(default_factory=list)
    transceivers: List[Dict[str, Any]] = field(default_factory=list)

    def to_yang_dict(self) -> Dict[str, Any]:
        return {
            "static-device-energy-tid:device": {
                "name": self.name,
                "typical-power": round(self.typical_power, 2),
                "nominal-power": round(self.nominal_power, 2),
                "max-power": round(self.max_power, 2),
                "maximum-traffic-throughput": self.maximum_traffic_throughput,
                "efficiency": round(self.efficiency, 6),
                "power-supply": self.power_supplies,
                "boards": self.boards,
                "transceivers": self.transceivers,
            }
        }
