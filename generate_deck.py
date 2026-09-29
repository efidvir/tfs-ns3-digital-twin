import os
import sys
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE

def create_deck(output_path):
    prs = Presentation()
    # 16:9 widescreen layout
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_layout = prs.slide_layouts[6]  # Blank slide

    # Theme Colors
    BG_DARK = RGBColor(11, 19, 43)        # Deep Navy #0B132B
    SURFACE_CARD = RGBColor(26, 38, 57)   # Card Navy #1A2639
    SURFACE_BORDER = RGBColor(45, 62, 80) # Border #2D3E50
    TEXT_WHITE = RGBColor(248, 250, 252)  # #F8FAFC
    TEXT_MUTED = RGBColor(148, 163, 184)  # #94A3B8
    CYAN_ACCENT = RGBColor(0, 212, 255)   # #00D4FF
    PURPLE_ACCENT = RGBColor(192, 132, 252) # #C084FC
    GREEN_ACCENT = RGBColor(16, 185, 129) # #10B981
    AMBER_ACCENT = RGBColor(245, 158, 11) # #F59E0B
    RED_ACCENT = RGBColor(239, 68, 68)    # #EF4444

    def add_bg(slide):
        bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height)
        bg.fill.solid()
        bg.fill.fore_color.rgb = BG_DARK
        bg.line.fill.background()
        return bg

    def add_header(slide, title_text, category_text="CER-INTENT & ETSI TERAFLOWSDN DIGITAL TWIN"):
        # Category / Pill
        cat_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.5), Inches(11.7), Inches(0.4))
        tf_cat = cat_box.text_frame
        tf_cat.word_wrap = True
        tf_cat.margin_left = tf_cat.margin_top = tf_cat.margin_right = tf_cat.margin_bottom = 0
        p_cat = tf_cat.paragraphs[0]
        p_cat.text = category_text.upper()
        p_cat.font.size = Pt(10)
        p_cat.font.bold = True
        p_cat.font.color.rgb = CYAN_ACCENT

        # Main Title
        title_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.85), Inches(11.7), Inches(0.7))
        tf_title = title_box.text_frame
        tf_title.word_wrap = True
        tf_title.margin_left = tf_title.margin_top = tf_title.margin_right = tf_title.margin_bottom = 0
        p_title = tf_title.paragraphs[0]
        p_title.text = title_text
        p_title.font.size = Pt(24)
        p_title.font.bold = True
        p_title.font.color.rgb = TEXT_WHITE

    # ─────────────────────────────────────────────────────────────────────────
    # SLIDE 1: Title Slide
    # ─────────────────────────────────────────────────────────────────────────
    s1 = prs.slides.add_slide(blank_layout)
    add_bg(s1)

    # Decorative accent card
    decor = s1.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(1.2), Inches(11.733), Inches(5.1))
    decor.fill.solid()
    decor.fill.fore_color.rgb = SURFACE_CARD
    decor.line.color.rgb = SURFACE_BORDER
    decor.line.width = Pt(1.5)

    # Sub-badge
    badge = s1.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(1.4), Inches(1.8), Inches(4.5), Inches(0.45))
    badge.fill.solid()
    badge.fill.fore_color.rgb = RGBColor(30, 41, 59)
    badge.line.color.rgb = CYAN_ACCENT
    badge.line.width = Pt(1)
    tf_b = badge.text_frame
    p_b = tf_b.paragraphs[0]
    p_b.text = "⚡ TELECOM DIGITAL TWIN ARCHITECTURE"
    p_b.font.size = Pt(11)
    p_b.font.bold = True
    p_b.font.color.rgb = CYAN_ACCENT
    p_b.alignment = PP_ALIGN.CENTER

    # Main Title
    t_box = s1.shapes.add_textbox(Inches(1.4), Inches(2.45), Inches(10.5), Inches(1.6))
    tf_t = t_box.text_frame
    tf_t.word_wrap = True
    p1 = tf_t.paragraphs[0]
    p1.text = "Digital Twin Adapters & Standards"
    p1.font.size = Pt(36)
    p1.font.bold = True
    p1.font.color.rgb = TEXT_WHITE

    p2 = tf_t.add_paragraph()
    p2.text = "How Intent, ETSI TeraFlowSDN, NS-3 Co-Simulation, and Ceragon Microwave Hardware Interconnect"
    p2.font.size = Pt(16)
    p2.font.color.rgb = PURPLE_ACCENT
    p2.space_before = Pt(12)

    # 3 Bullet Key Highlights
    hl_box = s1.shapes.add_textbox(Inches(1.4), Inches(4.3), Inches(10.5), Inches(1.5))
    tf_hl = hl_box.text_frame
    tf_hl.word_wrap = True
    
    highlights = [
        ("• What are the Adapters?", " Software translators bridging heterogeneous timing, data formats, and control protocols."),
        ("• International Standards:", " Anchored in TM Forum TMF921, 3GPP TS 28.561, ITU-T Y.3090, IETF DTI, and RFC 8040 RESTCONF."),
        ("• Closed-Loop Automation:", " Zero-risk What-If discrete prediction prior to physical hardware 2-phase commit actuation.")
    ]
    for i, (title, desc) in enumerate(highlights):
        p = tf_hl.paragraphs[0] if i == 0 else tf_hl.add_paragraph()
        r1 = p.add_run()
        r1.text = title
        r1.font.bold = True
        r1.font.size = Pt(13)
        r1.font.color.rgb = CYAN_ACCENT
        r2 = p.add_run()
        r2.text = desc
        r2.font.size = Pt(13)
        r2.font.color.rgb = TEXT_MUTED
        if i > 0:
            p.space_before = Pt(6)

    # Footer
    f_box = s1.shapes.add_textbox(Inches(1.4), Inches(5.65), Inches(10.5), Inches(0.4))
    tf_f = f_box.text_frame
    p_f = tf_f.paragraphs[0]
    p_f.text = "Ceragon Networks & ETSI TeraFlowSDN Research • Standalone & Production Hybrid Architecture"
    p_f.font.size = Pt(11)
    p_f.font.color.rgb = TEXT_MUTED

    # ─────────────────────────────────────────────────────────────────────────
    # SLIDE 2: The Core Problem & Why Adapters Are Needed (Simplified)
    # ─────────────────────────────────────────────────────────────────────────
    s2 = prs.slides.add_slide(blank_layout)
    add_bg(s2)
    add_header(s2, "The Core Problem: Why Do We Need Adapters?", "THE PROBLEM & ARCHITECTURAL NEED")

    # Top summary banner
    banner = s2.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(1.65), Inches(11.733), Inches(0.95))
    banner.fill.solid()
    banner.fill.fore_color.rgb = SURFACE_CARD
    banner.line.color.rgb = CYAN_ACCENT
    banner.line.width = Pt(1)
    tf_ban = banner.text_frame
    tf_ban.margin_left = tf_ban.margin_right = Inches(0.3)
    p_ban = tf_ban.paragraphs[0]
    p_ban.text = "💡 In a Telecom Digital Twin, components speak completely different languages and operate at vastly different timescales. Adapters are the critical translators that bridge this semantic and temporal chasm."
    p_ban.font.size = Pt(13)
    p_ban.font.color.rgb = TEXT_WHITE
    p_ban.font.bold = True

    # 4 Domain Columns
    cols_data = [
        {
            "title": "1. Declarative Intent",
            "actor": "Human Operator / SLA",
            "lang": "Natural Language / JSON",
            "clock": "Minutes to Days",
            "sample": '"Ensure URLLC latency < 1.5ms and 99.999% availability during storms"',
            "color": PURPLE_ACCENT
        },
        {
            "title": "2. SDN Controller",
            "actor": "ETSI TeraFlowSDN",
            "lang": "Context DB, gRPC, CSPF",
            "clock": "Seconds (Control Plane)",
            "sample": 'Device UUIDs, Endpoints, Topology Graphs, TI-LFA backup paths',
            "color": CYAN_ACCENT
        },
        {
            "title": "3. Discrete Simulator",
            "actor": "NS-3 Discrete Core",
            "lang": "C++ Event Queue & Packets",
            "clock": "Microseconds (t = 0.000s)",
            "sample": 'QueueDisc buffer drops, WiFi EDCA AC_VO, link propagation delay',
            "color": AMBER_ACCENT
        },
        {
            "title": "4. Physical Hardware",
            "actor": "Ceragon MH-T261",
            "lang": "RFC 8040 RESTCONF & PHY",
            "clock": "Sub-millisecond Hardware",
            "sample": 'V-Band 60.48 GHz, ACM MCS 0-9, PHY RSSI/SNR, RF registers',
            "color": GREEN_ACCENT
        }
    ]

    card_w = Inches(2.76)
    gap = Inches(0.23)
    left_start = Inches(0.8)

    for i, c in enumerate(cols_data):
        c_left = left_start + i * (card_w + gap)
        card = s2.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, c_left, Inches(2.8), card_w, Inches(4.2))
        card.fill.solid()
        card.fill.fore_color.rgb = SURFACE_CARD
        card.line.color.rgb = c["color"]
        card.line.width = Pt(1.5)

        tf_c = card.text_frame
        tf_c.word_wrap = True
        tf_c.margin_left = tf_c.margin_right = Inches(0.2)
        tf_c.margin_top = Inches(0.25)

        # Title
        p_t = tf_c.paragraphs[0]
        p_t.text = c["title"]
        p_t.font.size = Pt(14)
        p_t.font.bold = True
        p_t.font.color.rgb = c["color"]

        # Subtitle
        p_sub = tf_c.add_paragraph()
        p_sub.text = c["actor"]
        p_sub.font.size = Pt(11)
        p_sub.font.bold = True
        p_sub.font.color.rgb = TEXT_WHITE
        p_sub.space_before = Pt(4)

        # Fields
        fields = [
            ("Speaks:", c["lang"]),
            ("Timescale:", c["clock"]),
            ("Key Data:", c["sample"])
        ]
        for f_label, f_val in fields:
            p_f = tf_c.add_paragraph()
            r_l = p_f.add_run()
            r_l.text = f_label + "\n"
            r_l.font.size = Pt(10)
            r_l.font.bold = True
            r_l.font.color.rgb = TEXT_MUTED
            
            r_v = p_f.add_run()
            r_v.text = f_val
            r_v.font.size = Pt(10)
            r_v.font.color.rgb = TEXT_WHITE
            p_f.space_before = Pt(8)

    # ─────────────────────────────────────────────────────────────────────────
    # SLIDE 3: Digital Twin API Standards (Dedicated Slide as requested!)
    # ─────────────────────────────────────────────────────────────────────────
    s3 = prs.slides.add_slide(blank_layout)
    add_bg(s3)
    add_header(s3, "Standards for Digital Twin APIs We Use & What They Are", "INTERNATIONAL STANDARDS REFERENCE")

    # 6 Standard Cards in 2 rows x 3 columns
    stds = [
        {
            "name": "TM Forum TMF921",
            "role": "Intent Management API",
            "what": "REST API standard for expressing declarative network intent and SLA expectations.",
            "usage": "Operator defines latency (< 1.5ms) and availability without writing low-level scripts. Tracks intent state: Acknowledged → In Evaluation → Compliant.",
            "color": PURPLE_ACCENT,
            "badge": "BUSINESS & SLA"
        },
        {
            "name": "3GPP TS 28.561",
            "role": "Network Digital Twin (NDT) Lifecycle",
            "what": "3GPP 5G/6G standard defining digital twin management services and closed-loop control.",
            "usage": "Governs the 4-phase pre-flight verification gate before any action is actuated: verifies latency envelope, queue stability, jitter, and spectral mask.",
            "color": GREEN_ACCENT,
            "badge": "5G / 6G CORE"
        },
        {
            "name": "ITU-T Y.3090",
            "role": "Digital Twin Network (DTN) Architecture",
            "what": "ITU-T standard defining the 3-layer Digital Twin reference model and synchronization.",
            "usage": "Defines data repository synchronization between the Physical Network Layer and the Cyber Twin Layer. Powers our real-time shadow datastore.",
            "color": CYAN_ACCENT,
            "badge": "ARCHITECTURE"
        },
        {
            "name": "IETF NMRG DTI",
            "role": "Digital Twin Interface (RFC Draft)",
            "what": "IETF Network Management Research Group interface for Twin-to-Simulator communication.",
            "usage": "Standardizes the East-West protocol for injecting What-If perturbations (traffic surge, rain fade) and streaming discrete telemetry back to controller.",
            "color": AMBER_ACCENT,
            "badge": "SIMULATION SBI"
        },
        {
            "name": "IETF RFC 8040 / 7950",
            "role": "RESTCONF Protocol & YANG 1.1",
            "what": "IETF standard for HTTP-based network device management accessing YANG data stores.",
            "usage": "Southbound interface to Ceragon MH-T261 (192.168.1.225:80). Provides Candidate Datastore staging, diff validation, and 2-Phase Commit (2PC).",
            "color": CYAN_ACCENT,
            "badge": "HARDWARE SBI"
        },
        {
            "name": "ETSI TeraFlowSDN APIs",
            "role": "Cloud-Native SDN Controller Microservices",
            "what": "ETSI standard cloud-native gRPC microservices pipeline for autonomous transport networks.",
            "usage": "Exposes Context Service (gRPC :10010), Service/PCE (gRPC :10030), Device Driver (gRPC :10020), and Monitoring Telemetry Daemon (gRPC :10040).",
            "color": PURPLE_ACCENT,
            "badge": "SDN CONTROL"
        }
    ]

    sw_w = Inches(3.75)
    sw_h = Inches(2.55)
    col_x = [Inches(0.8), Inches(4.79), Inches(8.78)]
    row_y = [Inches(1.7), Inches(4.45)]

    for idx, st in enumerate(stds):
        rx = idx % 3
        ry = idx // 3
        cx = col_x[rx]
        cy = row_y[ry]

        card = s3.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, cx, cy, sw_w, sw_h)
        card.fill.solid()
        card.fill.fore_color.rgb = SURFACE_CARD
        card.line.color.rgb = st["color"]
        card.line.width = Pt(1.5)

        tf_s = card.text_frame
        tf_s.word_wrap = True
        tf_s.margin_left = tf_s.margin_right = Inches(0.2)
        tf_s.margin_top = Inches(0.18)

        # Standard Name & Badge
        p_n = tf_s.paragraphs[0]
        r_n = p_n.add_run()
        r_n.text = st["name"] + "  "
        r_n.font.size = Pt(13)
        r_n.font.bold = True
        r_n.font.color.rgb = st["color"]

        r_badge = p_n.add_run()
        r_badge.text = f"[{st['badge']}]"
        r_badge.font.size = Pt(9)
        r_badge.font.bold = True
        r_badge.font.color.rgb = TEXT_MUTED

        # Role
        p_r = tf_s.add_paragraph()
        p_r.text = st["role"]
        p_r.font.size = Pt(11)
        p_r.font.bold = True
        p_r.font.color.rgb = TEXT_WHITE
        p_r.space_before = Pt(2)

        # What it is
        p_w = tf_s.add_paragraph()
        r_w1 = p_w.add_run()
        r_w1.text = "Standard: "
        r_w1.font.bold = True
        r_w1.font.size = Pt(9.5)
        r_w1.font.color.rgb = TEXT_MUTED
        r_w2 = p_w.add_run()
        r_w2.text = st["what"]
        r_w2.font.size = Pt(9.5)
        r_w2.font.color.rgb = TEXT_WHITE
        p_w.space_before = Pt(4)

        # In Our System
        p_u = tf_s.add_paragraph()
        r_u1 = p_u.add_run()
        r_u1.text = "In Our Platform: "
        r_u1.font.bold = True
        r_u1.font.size = Pt(9.5)
        r_u1.font.color.rgb = CYAN_ACCENT
        r_u2 = p_u.add_run()
        r_u2.text = st["usage"]
        r_u2.font.size = Pt(9.5)
        r_u2.font.color.rgb = TEXT_WHITE
        p_u.space_before = Pt(4)

    # ─────────────────────────────────────────────────────────────────────────
    # SLIDE 4: TFS-to-NS-3 Adapter: How It Functions (Simplified)
    # ─────────────────────────────────────────────────────────────────────────
    s4 = prs.slides.add_slide(blank_layout)
    add_bg(s4)
    add_header(s4, "Adapter 1: TFS-to-NS-3 Simulation Adapter (The Cyber Mirror)", "HOW THE ADAPTER FUNCTIONS")

    # Left: 4 Step Pipeline
    pipe_w = Inches(7.2)
    p_card = s4.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(1.65), pipe_w, Inches(5.35))
    p_card.fill.solid()
    p_card.fill.fore_color.rgb = SURFACE_CARD
    p_card.line.color.rgb = CYAN_ACCENT
    p_card.line.width = Pt(1.5)

    tf_p = p_card.text_frame
    tf_p.word_wrap = True
    tf_p.margin_left = tf_p.margin_right = Inches(0.25)
    tf_p.margin_top = Inches(0.2)

    p_head = tf_p.paragraphs[0]
    p_head.text = "🔁 Step-by-Step Functional Flow (Simplified)"
    p_head.font.size = Pt(14)
    p_head.font.bold = True
    p_head.font.color.rgb = CYAN_ACCENT

    steps = [
        ("Step 1: Reconcile Live Topology & State", 
         "The adapter queries ETSI TeraFlowSDN (:8088 Context) to extract the active 34-node graph, link bandwidths, and live Ceragon RF metrics (RSSI -58 dBm, MCS 8).",
         PURPLE_ACCENT),
        ("Step 2: Simulation Resolution Governor (Fidelity Scoping)",
         "Instead of simulating all 34 nodes (which takes minutes), the Governor automatically scopes the graph to the relevant target domain (e.g. Tier 4: URLLC Micro-Packet, 23 nodes) executing in ~1150ms.",
         CYAN_ACCENT),
        ("Step 3: What-If Perturbation Dispatch",
         "Injects real-world stress conditions into NS-3: 3.5x bulk traffic surge (bufferbloat) or ITU-R P.838 rain fade (ACM rate degradation from 1Gbps to 100Mbps).",
         AMBER_ACCENT),
        ("Step 4: Discrete Trace Ingestion & NetAnim Generation",
         "NS-3 simulates microsecond discrete packet events on cersrv-029, generates /tmp/tsn_wifi_ceragon_anim.xml, and the adapter streams packet queues, buffer drops, and latencies back to the twin.",
         GREEN_ACCENT)
    ]

    for title, desc, col in steps:
        p_st = tf_p.add_paragraph()
        r_t = p_st.add_run()
        r_t.text = "\n" + title + "\n"
        r_t.font.size = Pt(11.5)
        r_t.font.bold = True
        r_t.font.color.rgb = col

        r_d = p_st.add_run()
        r_d.text = desc
        r_d.font.size = Pt(10.5)
        r_d.font.color.rgb = TEXT_WHITE
        p_st.space_before = Pt(4)

    # Right: Technical Architecture Box
    tech_w = Inches(4.3)
    t_card = s4.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(8.23), Inches(1.65), tech_w, Inches(5.35))
    t_card.fill.solid()
    t_card.fill.fore_color.rgb = SURFACE_CARD
    t_card.line.color.rgb = SURFACE_BORDER
    t_card.line.width = Pt(1.5)

    tf_t = t_card.text_frame
    tf_t.word_wrap = True
    tf_t.margin_left = tf_t.margin_right = Inches(0.25)
    tf_t.margin_top = Inches(0.2)

    p_th = tf_t.paragraphs[0]
    p_th.text = "⚙️ Key Implementation Features"
    p_th.font.size = Pt(14)
    p_th.font.bold = True
    p_th.font.color.rgb = TEXT_WHITE

    tech_features = [
        ("Remote Execution Core", "Dispatches via SSH/JSON to ns-3.45 on efid@cersrv-029; falls back to analytical local simulation for zero-dependency standalone mode."),
        ("Multi-Tier Governor", "5 Resolution Tiers (Macro-Topology 25%, Queue Dynamics 55%, Physical RF 75%, URLLC 95%, Green Energy 20%)."),
        ("NetAnim XML Output", "Instruments AnimationInterface for real timeline playback (0.000s - 2.500s) with 10 visual buffer slots and tail-drop alerts."),
        ("Deterministic TSN Mapping", "Maps 802.1Q PCP Class 6 & EDCA AC_VO into PfifoFast Band 0 priority queues.")
    ]

    for title, desc in tech_features:
        p_tf = tf_t.add_paragraph()
        r_t = p_tf.add_run()
        r_t.text = "\n• " + title + ": "
        r_t.font.size = Pt(10.5)
        r_t.font.bold = True
        r_t.font.color.rgb = CYAN_ACCENT

        r_d = p_tf.add_run()
        r_d.text = desc
        r_d.font.size = Pt(10)
        r_d.font.color.rgb = TEXT_MUTED
        p_tf.space_before = Pt(4)

    # ─────────────────────────────────────────────────────────────────────────
    # SLIDE 5: Hardware & Southbound Driver Adapter (The Physical Actuator)
    # ─────────────────────────────────────────────────────────────────────────
    s5 = prs.slides.add_slide(blank_layout)
    add_bg(s5)
    add_header(s5, "Adapter 2: TFS Southbound & Hardware Driver Adapter", "PHYSICAL ACTUATION & TELEMETRY")

    # 3 Horizontal Cards (Candidate Staging -> Pre-Flight Gate -> 2PC Actuation)
    h_cards = [
        {
            "step": "STAGE 1",
            "title": "Candidate Datastore Staging",
            "icon": "📝",
            "desc": "Translates AI Decision Engine output into concrete YANG configuration rules staged in ETSI TeraFlowSDN's Candidate Datastore (RFC 8040).",
            "points": [
                "Target Device: Ceragon MH-T261 (UUID f676623c...)",
                "ACM Floor Hardened: MCS 0 → MCS 4 (≥ 500 Mbps min)",
                "QoS Queue: FIFO → IEEE 802.1Q PCP Class 6 (PfifoFast)",
                "Carrier Frequency: 60.48 GHz → 64.80 GHz"
            ],
            "color": PURPLE_ACCENT
        },
        {
            "step": "STAGE 2",
            "title": "Pre-Flight Safety Envelope Gate",
            "icon": "🛡️",
            "desc": "Before touching physical production traffic, 3GPP TS 28.561 requires verification of the candidate configuration against live constraints.",
            "points": [
                "Gate 1: Latency Bound Pass (Predicted 1.12ms ≤ 1.5ms)",
                "Gate 2: Queue Stability Pass (Buffer occupancy < 40%)",
                "Gate 3: Hardware Capability Pass (MH-T261 supports MCS 4)",
                "Gate 4: Spectral Mask Pass (64.80 GHz approved in V-Band)"
            ],
            "color": AMBER_ACCENT
        },
        {
            "step": "STAGE 3",
            "title": "RFC 8040 RESTCONF 2PC Commit",
            "icon": "🚀",
            "desc": "Executes Two-Phase Commit transaction directly over HTTP/RESTCONF to physical transceiver socket 192.168.1.225:80.",
            "points": [
                "Phase 1 (Prepare): PATCH candidate datastore via RESTCONF",
                "Phase 2 (Commit): POST ietf-netconf:commit operation",
                "Telemetry Verification: Continuous RFC 8040 poll",
                "Instant Rollback: Automatic 2PC revert if health checks fail"
            ],
            "color": GREEN_ACCENT
        }
    ]

    h_card_w = Inches(3.75)
    h_gap = Inches(0.24)
    h_start = Inches(0.8)

    for i, hc in enumerate(h_cards):
        h_left = h_start + i * (h_card_w + h_gap)
        card = s5.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, h_left, Inches(1.65), h_card_w, Inches(4.3))
        card.fill.solid()
        card.fill.fore_color.rgb = SURFACE_CARD
        card.line.color.rgb = hc["color"]
        card.line.width = Pt(1.5)

        tf_h = card.text_frame
        tf_h.word_wrap = True
        tf_h.margin_left = tf_h.margin_right = Inches(0.2)
        tf_h.margin_top = Inches(0.2)

        # Step tag
        p_tag = tf_h.paragraphs[0]
        p_tag.text = hc["icon"] + " " + hc["step"]
        p_tag.font.size = Pt(11)
        p_tag.font.bold = True
        p_tag.font.color.rgb = hc["color"]

        # Title
        p_t = tf_h.add_paragraph()
        p_t.text = hc["title"]
        p_t.font.size = Pt(13)
        p_t.font.bold = True
        p_t.font.color.rgb = TEXT_WHITE
        p_t.space_before = Pt(3)

        # Desc
        p_d = tf_h.add_paragraph()
        p_d.text = hc["desc"]
        p_d.font.size = Pt(10)
        p_d.font.color.rgb = TEXT_MUTED
        p_d.space_before = Pt(6)

        # Points
        for pt in hc["points"]:
            p_pt = tf_h.add_paragraph()
            p_pt.text = "• " + pt
            p_pt.font.size = Pt(9.5)
            p_pt.font.color.rgb = TEXT_WHITE
            p_pt.space_before = Pt(4)

    # Bottom summary callout
    bot_callout = s5.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(6.1), Inches(11.733), Inches(0.9))
    bot_callout.fill.solid()
    bot_callout.fill.fore_color.rgb = RGBColor(15, 23, 42)
    bot_callout.line.color.rgb = CYAN_ACCENT
    bot_callout.line.width = Pt(1)
    tf_bot = bot_callout.text_frame
    tf_bot.margin_left = tf_bot.margin_right = Inches(0.25)
    p_bot = tf_bot.paragraphs[0]
    p_bot.text = "🔒 Zero-Outage Guarantee: By combining Candidate Datastore staging, Pre-Flight discrete validation, and 2-Phase Commit, the adapter ensures that bad configurations are rejected in software before they can impact customer SLA."
    p_bot.font.size = Pt(11)
    p_bot.font.bold = True
    p_bot.font.color.rgb = TEXT_WHITE

    # ─────────────────────────────────────────────────────────────────────────
    # SLIDE 6: Summary & Operational Value (The Complete Closed Loop)
    # ─────────────────────────────────────────────────────────────────────────
    s6 = prs.slides.add_slide(blank_layout)
    add_bg(s6)
    add_header(s6, "Summary: End-to-End Closed-Loop Operational Value", "ARCHITECTURE SUMMARY")

    # 3 Large Value Pillars
    pillars = [
        {
            "title": "Zero-Risk What-If Validation",
            "icon": "🛡️",
            "sub": "Predictive Discrete Simulation",
            "body": "Operators can test severe perturbations (3.5x bulk surges, category-5 tropical rain fade, fiber link cuts) in a microsecond-accurate digital twin without putting live production circuits at risk.",
            "color": CYAN_ACCENT
        },
        {
            "title": "Standardized Multi-Vendor Interoperability",
            "icon": "🌐",
            "sub": "Anchored in 3GPP, ITU-T & IETF",
            "body": "Zero proprietary lock-in. Built entirely on open telecom specifications: TM Forum TMF921 Intent API, 3GPP TS 28.561 NDT lifecycle, ITU-T Y.3090, IETF DTI, and RFC 8040 RESTCONF.",
            "color": PURPLE_ACCENT
        },
        {
            "title": "Sub-Second Autonomous Closed Loop",
            "icon": "⚡",
            "sub": "Autonomous Self-Healing Transport",
            "body": "Replaces hours of manual CLI troubleshooting with autonomous, closed-loop assurance: SLA intent is ingested, simulated in NS-3, safety-verified, and actuated via TFS in ~1.9 to 2.2 seconds total.",
            "color": GREEN_ACCENT
        }
    ]

    p_w = Inches(3.75)
    p_gap = Inches(0.24)
    p_left = Inches(0.8)

    for i, pil in enumerate(pillars):
        px = p_left + i * (p_w + p_gap)
        card = s6.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, px, Inches(1.65), p_w, Inches(3.6))
        card.fill.solid()
        card.fill.fore_color.rgb = SURFACE_CARD
        card.line.color.rgb = pil["color"]
        card.line.width = Pt(1.5)

        tf_pil = card.text_frame
        tf_pil.word_wrap = True
        tf_pil.margin_left = tf_pil.margin_right = Inches(0.25)
        tf_pil.margin_top = Inches(0.25)

        p_t = tf_pil.paragraphs[0]
        p_t.text = pil["icon"] + " " + pil["title"]
        p_t.font.size = Pt(13)
        p_t.font.bold = True
        p_t.font.color.rgb = pil["color"]

        p_s = tf_pil.add_paragraph()
        p_s.text = pil["sub"]
        p_s.font.size = Pt(11)
        p_s.font.bold = True
        p_s.font.color.rgb = TEXT_WHITE
        p_s.space_before = Pt(4)

        p_b = tf_pil.add_paragraph()
        p_b.text = pil["body"]
        p_b.font.size = Pt(10.5)
        p_b.font.color.rgb = TEXT_MUTED
        p_b.space_before = Pt(10)

    # Bottom Table: Summary Matrix of Components & Adapters
    bot_box = s6.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(5.45), Inches(11.733), Inches(1.55))
    bot_box.fill.solid()
    bot_box.fill.fore_color.rgb = SURFACE_CARD
    bot_box.line.color.rgb = SURFACE_BORDER
    bot_box.line.width = Pt(1)

    tf_bb = bot_box.text_frame
    tf_bb.word_wrap = True
    tf_bb.margin_left = tf_bb.margin_right = Inches(0.25)
    tf_bb.margin_top = Inches(0.15)

    p_bbh = tf_bb.paragraphs[0]
    p_bbh.text = "📋 Digital Twin Adapter Quick Reference Table"
    p_bbh.font.size = Pt(12)
    p_bbh.font.bold = True
    p_bbh.font.color.rgb = CYAN_ACCENT

    table_lines = [
        ("• Intent Adapter:", " Translates Natural Language / SLA bounds into TFS Service & CSPF requests (TM Forum TMF921)."),
        ("• Simulation Adapter:", " Syncs TFS live graph into NS-3 C++ discrete engine, scopes fidelity (Tiers 1-5), and outputs microsecond traces."),
        ("• Southbound Driver:", " Manages candidate datastore diffs and 2-phase commits to Ceragon MH-T261 via RFC 8040 RESTCONF.")
    ]
    for lbl, desc in table_lines:
        p_tl = tf_bb.add_paragraph()
        r_l = p_tl.add_run()
        r_l.text = lbl
        r_l.font.size = Pt(10)
        r_l.font.bold = True
        r_l.font.color.rgb = TEXT_WHITE
        r_d = p_tl.add_run()
        r_d.text = desc
        r_d.font.size = Pt(10)
        r_d.font.color.rgb = TEXT_MUTED
        p_tl.space_before = Pt(2)

    # Save presentation
    prs.save(output_path)
    print(f"[SUCCESS] Presentation generated: {output_path}")

if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "Telecom_Digital_Twin_Adapters_and_Standards.pptx"
    create_deck(out)
