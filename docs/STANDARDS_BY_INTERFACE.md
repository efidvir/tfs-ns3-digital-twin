# Relevant standards by interface

This page lists the standards that matter for each interface of the CER-Intent digital twin. For each interface it says what the code uses today and what it should adopt.

Statuses:

- **In use**: the code calls or implements it today.
- **In TFS**: TeraFlowSDN already ships an implementation, but our code does not use it yet.
- **Recommended**: the standard to adopt for this interface.
- **Emerging**: still in development. Track it; don't build on it yet.
- **De facto**: an open-source or industry convention, not a formal standard.

```
            ① intent / service               ④ southbound
 CER-Intent ─────────────────▶ TeraFlowSDN ───────────────▶ Ceragon MH-T261
 (agents)                          │ ▲
      │                       ③ state sync
      │ ② what-if jobs             ▼ │
      └────────────────────▶ Digital twin (ns-3.45)
```

## ① CER-Intent agents → TeraFlowSDN (northbound: intent and service)

**Today:** `PUT /tfs-api/device/{uuid}` with CONFIGACTION_SET rules and `POST /tfs-api/context/admin/slices`, sent to the TFS native REST NBI. The source is `cer_intent/device/adapter.py` and `device/tfs_client.py`.

| Standard | What it gives this interface | Status |
|---|---|---|
| TFS native REST NBI (`tfs_api`) | Device config rules, slices and topology reads | In use |
| TM Forum TMF921 Intent Management API | Intent resource model, lifecycle and reports, instead of the custom Pydantic schema | Recommended |
| 3GPP TS 28.312 Intent-driven management services | An expectation-based intent model (targets, contexts, fulfilment reports) that fits SLA intents | Recommended |
| IETF L3NM (RFC 9182), L2NM (RFC 9291), L3SM (RFC 8299) | Standard service requests, so we stop writing raw device rules | In TFS (`nbi/ietf_l3vpn`, `ietf_l2vpn`) |
| IETF network slice framework (RFC 9543) and slice NBI YANG | Transport slices with SLOs (bandwidth, latency) | In TFS (`nbi/ietf_network_slice`) |
| CAMARA Quality-on-Demand | A simple QoS API for application-driven intents | In TFS (`nbi/camara_qod`) |
| RFC 9315 (IRTF, intent-based networking concepts), ETSI ZSM closed loop, ETSI ENI | Reference frameworks for intent and closed-loop design | Framework |
| Model Context Protocol (MCP) | Exposes TFS and twin operations as tools that LLM agents can call | De facto, emerging |

## ② CER-Intent agents → digital twin (what-if jobs)

**Today:** CER-Intent reaches ns-3 over SSH to `efid@cersrv-029`, parsing JSON printed between markers (`tsn_simulation_runner.py`). It also has a custom REST API on :9100 (`tfs_digital_twin_api.py`) whose what-if results come from formulas, not ns-3.

| Standard | What it gives this interface | Status |
|---|---|---|
| OpenAPI 3 | Machine-readable API description (`docs/OPENAPI_SPECIFICATION.yaml`) | In use (docs only) |
| 3GPP TS 28.561 (NDT management) over TS 28.532 operations | Each what-if run becomes an NDTJob (capability, scope, execution limits), and results come back as an NDTReport | Recommended |
| ITU-T Y.3092 | Names this interface NDT-m: management-to-twin job control | Recommended |
| 3GPP TS 29.222 CAPIF | API discovery, onboarding and authorisation for the twin's APIs | Recommended (today a static JSON mock) |
| 3GPP TS 28.105 (AI/ML management) and ITU-T Y.3181 (ML sandbox) | Test agents' models in the twin before deployment, with lifecycle records | Recommended |
| Gymnasium API with ns3-ai or ns3-gym | Step-by-step coupling of Python agents inside a simulation run | De facto |
| 3GPP Rel-20 NDT phase 2 (TR 28.883), ITU-T Q.SDTN | Twin collaboration with automation functions; a signalling protocol for the twin | Emerging |

## ③ TeraFlowSDN ↔ digital twin (state sync and shared models)

**Today:** `ns3_tfs_runtime_bridge.py` polls the TFS REST NBI every second and writes `ns3_link_state.json`, but no ns-3 program reads that file. `tfs_topology_to_ns3.py` turns the TFS topology JSON into a C++ scenario.

| Standard | What it gives this interface | Status |
|---|---|---|
| TFS REST NBI and gRPC protos | Topology, devices and links as TFS models them | In use |
| IETF RFC 8345 network topology (plus RFC 8346 L3 and RFC 8795 TE) | A vendor-neutral topology the ns-3 generator can read | In TFS (`nbi/ietf_network`) |
| IETF RFC 8561 microwave radio link YANG | Standard radio-link parameters (frequency, bandwidth, modulation, power) to set ns-3 link models | Recommended |
| YANG-Push (RFC 8641 with RFC 8639) or gNMI Subscribe | Streamed state changes instead of 1 s polling | Recommended |
| TFS KPI manager, telemetry, analytics and Kafka | Where streamed KPIs and Python analytics run | In TFS (not deployed) |
| ITU-T Y.3092 NDT-p, Y.3093 data domain, Y.3094 model domain | How physical state is collected and how twin models are defined | Recommended |
| ITU-R P.838 (rain), P.676 (gaseous and 60 GHz oxygen absorption), P.530 (line-of-sight link design) | The propagation physics the twin should model | P.838 partial; others recommended |
| IEEE 802.1Q TSN (for example 802.1Qbv) | TSN traffic classes; today the scenario uses IP ToS 0xC0 and PfifoFast, with no VLAN or PCP | Recommended for fidelity |
| 3GPP Rel-20 NDT data collection, IRTF NMRG twin drafts | Future data-collection interfaces | Emerging |

## ④ TeraFlowSDN → Ceragon hardware (southbound)

**Today:** the TFS `CeragonDriver` (driver enum 22) PATCHes the RESTCONF candidate datastore, then POSTs `ietf-netconf:commit`, or `discard-changes` if staging fails. The source is `teraflowsdn/src/device/service/drivers/ceragon/client.py`.

| Standard | What it gives this interface | Status |
|---|---|---|
| IETF RFC 8040 RESTCONF | HTTP access to YANG data | In use |
| IETF RFC 8527 (RESTCONF for NMDA) and RFC 8342 (NMDA datastores) | The `/restconf/ds/ietf-datastores:candidate` path and the candidate, running and operational datastores | In use |
| IETF RFC 6241 NETCONF operations (commit, discard-changes) | Atomic commit of the candidate. Calling them through RESTCONF operations is a vendor mapping, not part of RFC 8040. | In use |
| IETF RFC 7950 YANG 1.1 and RFC 8525 YANG library | Data modelling and capability discovery (`test_connection` reads the YANG library) | In use |
| IETF RFC 8343 ietf-interfaces and IEEE 802.1Q YANG | VLAN sub-interfaces for transport slices | In use |
| Vendor `radio-bridge-tg-*` YANG | Radio and ACM configuration | In use (vendor-specific) |
| IETF RFC 8561 microwave radio link YANG and ONF TR-532 microwave model | Vendor-neutral radio configuration and status | Recommended |
| YANG-Push (RFC 8641) or gNMI | Live RSSI, SNR and MCS telemetry; `SubscribeState` does nothing today | Recommended |
| TLS 1.3 (RFC 8446) and NACM (RFC 8341) | Encrypted, access-controlled management; today it is HTTP with admin/admin | Recommended |
| ETSI EN 302 217 (fixed point-to-point radio) | Regulatory limits on the radio, used as input to pre-flight gates | Context |

## Recommended stack at a glance

| Interface | Adopt first |
|---|---|
| ① agents → TFS | TMF921 or TS 28.312 intent on top, with IETF L3NM or network-slice requests into TFS |
| ② agents → twin | TS 28.561 NDTJob over Y.3092 NDT-m, exposed through CAPIF |
| ③ TFS ↔ twin | RFC 8345 topology plus RFC 8561 link data; YANG-Push into TFS KPI and Kafka |
| ④ TFS → radio | RESTCONF/NMDA (RFC 8040 and 8527) with RFC 8561 models, YANG-Push telemetry, TLS and NACM |
