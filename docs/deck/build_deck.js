// Builds CER-Intent_Digital_Twin_As-Built.pptx
//   python audit_stats.py <cer-intent>/data/audit_log.jsonl audit_stats.json
//   node build_deck.js
// Needs pptxgenjs, react, react-dom, react-icons and sharp (npm install).
// Every status and number on the slides comes from a code review of
// cer-intent (f2c3fea), tfs-ns3-digital-twin (a9ccad6) and teraflowsdn (1e91cf2);
// the speaker notes cite the source file for each claim.
const fs = require("fs");
const path = require("path");
const pptxgen = require("pptxgenjs");
const React = require("react");
const ReactDOMServer = require("react-dom/server");
const sharp = require("sharp");
const fa = require("react-icons/fa");

const STATS = JSON.parse(fs.readFileSync(path.join(__dirname, "audit_stats.json"), "utf8"));

// ---------- palette ----------
const NAVY = "0B1D33";
const NAVY2 = "14304F";
const INK = "1A2B3C";
const MUTED = "5A6B7D";
const TINT = "F2F5F8";
const LINE = "D5DDE5";
const WHITE = "FFFFFF";
const C_INTENT = "7C5CFF";
const C_SDN = "0FA3B1";
const C_SIM = "E8912D";
const C_HW = "22A06B";
const RED = "D64545";
const HEAD = "Arial";
const BODY = "Calibri";
const MONO = "Courier New";

// status vocabulary used on every slide
const STATUS = {
  IMPLEMENTED: { fill: C_HW, text: WHITE, line: C_HW },
  PARTIAL: { fill: C_SIM, text: WHITE, line: C_SIM },
  MOCK: { fill: RED, text: WHITE, line: RED },
  PLANNED: { fill: WHITE, text: MUTED, line: "9AA7B4", dash: true },
};

async function icon(Comp, color) {
  const svg = ReactDOMServer.renderToStaticMarkup(React.createElement(Comp, { color: "#" + color, size: "256" }));
  const png = await sharp(Buffer.from(svg)).png().toBuffer();
  return "image/png;base64," + png.toString("base64");
}

async function iconCircle(s, pres, Comp, x, y, d, bg, fg = WHITE) {
  s.addShape(pres.shapes.OVAL, { x, y, w: d, h: d, fill: { color: bg }, line: { color: bg } });
  const pad = d * 0.25;
  s.addImage({ data: await icon(Comp, fg), x: x + pad, y: y + pad, w: d - 2 * pad, h: d - 2 * pad });
}

function txt(s, text, o) {
  s.addText(text, Object.assign({ fontFace: BODY, fontSize: 11, color: INK, margin: 0, isTextBox: true, valign: "top" }, o));
}

function title(s, kicker, text) {
  txt(s, kicker.toUpperCase(), { x: 0.5, y: 0.3, w: 9, h: 0.25, fontFace: HEAD, fontSize: 10, bold: true, color: C_SDN, charSpacing: 2 });
  txt(s, text, { x: 0.5, y: 0.55, w: 9, h: 0.6, fontFace: HEAD, fontSize: 24, bold: true, color: NAVY, valign: "middle" });
}

function badge(s, pres, x, y, status, w = 0.95) {
  const st = STATUS[status];
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x, y, w, h: 0.22, fill: { color: st.fill }, rectRadius: 0.11,
    line: { color: st.line, width: 1, dashType: st.dash ? "dash" : "solid" },
  });
  txt(s, status, { x, y, w, h: 0.22, fontFace: HEAD, fontSize: 7, bold: true, color: st.text, align: "center", valign: "middle", charSpacing: 0.5 });
}

function arrow(s, pres, x1, y1, x2, y2, color = MUTED, both = false, dash = false) {
  s.addShape(pres.shapes.LINE, {
    x: Math.min(x1, x2), y: Math.min(y1, y2), w: Math.abs(x2 - x1), h: Math.abs(y2 - y1),
    flipH: x2 < x1, flipV: y2 < y1,
    line: { color, width: 1.75, endArrowType: "triangle", beginArrowType: both ? "triangle" : "none", dashType: dash ? "dash" : "solid" },
  });
}

function card(s, pres, x, y, w, h, fill = TINT) {
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, fill: { color: fill }, line: { color: fill }, rectRadius: 0.08 });
}

const fmt = (n) => n.toLocaleString("en-US");

(async () => {
  const pres = new pptxgen();
  pres.layout = "LAYOUT_16x9"; // 10 x 5.625
  pres.title = "CER-Intent Digital Twin: As-Built";

  const tfsApplies = STATS.applies_by_backend.TeraFlowAdapter;
  const tfsTotal = tfsApplies.ok + tfsApplies.failed;
  const applyTotal = STATS.by_type.CONFIG_APPLIED;
  const intents = STATS.by_type.INTENT_PARSED;
  const p2a = STATS.parse_to_last_apply_ms;
  const period = `${STATS.first.slice(0, 10)} – ${STATS.last.slice(0, 10)}`;

  // ===================================================================
  // 1. Title
  // ===================================================================
  {
    const s = pres.addSlide();
    s.background = { color: NAVY };
    txt(s, "TELECOM DIGITAL TWIN · AS-BUILT REVIEW", { x: 0.6, y: 0.85, w: 5.8, h: 0.3, fontFace: HEAD, fontSize: 11, bold: true, color: C_SDN, charSpacing: 3 });
    txt(s, "CER-Intent Digital Twin", { x: 0.6, y: 1.25, w: 5.8, h: 0.9, fontFace: HEAD, fontSize: 38, bold: true, color: WHITE, valign: "middle" });
    txt(s, "Architecture, what works today, and the roadmap for TeraFlowSDN, ns-3 and Ceragon microwave hardware", { x: 0.6, y: 2.25, w: 5.5, h: 0.8, fontSize: 15, color: "C9D6E3" });
    // status legend
    const legend = [["IMPLEMENTED", "works end to end in code"], ["PARTIAL", "real code, with limits"], ["MOCK", "hard-coded or simulated output"], ["PLANNED", "design or docs only"]];
    for (let i = 0; i < legend.length; i++) {
      badge(s, pres, 0.6, 3.3 + i * 0.32, legend[i][0], 1.05);
      txt(s, legend[i][1], { x: 1.8, y: 3.3 + i * 0.32, w: 4, h: 0.22, fontSize: 10.5, color: "C9D6E3", valign: "middle" });
    }
    txt(s, "Based on cer-intent @f2c3fea · tfs-ns3-digital-twin @a9ccad6 · teraflowsdn @1e91cf2 · September 2026", { x: 0.6, y: 4.95, w: 8.8, h: 0.3, fontSize: 10, color: "8FA3B8" });

    const items = [
      [fa.FaUserTie, C_INTENT, "CER-Intent", "intent → config"],
      [fa.FaProjectDiagram, C_SDN, "TeraFlowSDN", "SDN controller"],
      [fa.FaFlask, C_SIM, "ns-3.45", "discrete-event twin"],
      [fa.FaBroadcastTower, C_HW, "Ceragon MH-T261", "60 GHz radio"],
    ];
    const x0 = 6.9, y0 = 0.85, step = 1.0, d = 0.6;
    s.addShape(pres.shapes.LINE, { x: x0 + d / 2, y: y0 + d / 2, w: 0, h: step * 3, line: { color: "3A5575", width: 2, dashType: "dash" } });
    for (let i = 0; i < items.length; i++) {
      const [I, c, a, b] = items[i];
      await iconCircle(s, pres, I, x0, y0 + i * step, d, c);
      txt(s, a, { x: x0 + 0.78, y: y0 + i * step + 0.05, w: 2.2, h: 0.28, fontFace: HEAD, fontSize: 13, bold: true, color: WHITE });
      txt(s, b, { x: x0 + 0.78, y: y0 + i * step + 0.32, w: 2.2, h: 0.25, fontSize: 10.5, color: "8FA3B8" });
    }
    s.addNotes(
      "This deck documents the system as it is built, not as it was first pitched. Each capability carries one of four statuses: IMPLEMENTED (works end to end in code), PARTIAL (real code with known limits), MOCK (the UI or API returns hard-coded or simulated values), PLANNED (only in docs or slides).\n" +
      "Sources: code review of efidvir/cer-intent (commit f2c3fea), efidvir/tfs-ns3-digital-twin (a9ccad6) and efidvir/teraflowsdn (1e91cf2), plus the CER-Intent audit log data/audit_log.jsonl. Numbers on the operating-data slide are produced by docs/deck/audit_stats.py."
    );
  }

  // ===================================================================
  // 1b. Motivation: purpose and goals
  // ===================================================================
  {
    const s = pres.addSlide();
    s.background = { color: WHITE };
    title(s, "Motivation", "Why this project exists");
    card(s, pres, 0.5, 1.3, 9.0, 0.62, NAVY);
    txt(s, [
      { text: "Purpose: ", options: { bold: true, color: C_SDN } },
      { text: "let operators state what they want in plain words, test it in a digital twin, and only then change the live microwave network, automatically and safely.", options: { color: WHITE } },
    ], { x: 0.7, y: 1.3, w: 8.6, h: 0.62, fontSize: 11.5, valign: "middle" });

    txt(s, "WHY", { x: 0.5, y: 2.1, w: 4, h: 0.22, fontSize: 9, bold: true, color: RED, charSpacing: 1.5 });
    const why = [
      [fa.FaCloudShowersHeavy, "Weather moves capacity", "Rain fade at 60–80 GHz can cut a link from 1 Gbps to 100 Mbps."],
      [fa.FaKeyboard, "Changes are manual and risky", "CLI work per radio; a bad change hits live traffic."],
      [fa.FaPuzzlePiece, "Tools don't talk", "Intent, SDN, simulator and radio use different languages and clocks."],
      [fa.FaRobot, "AI needs a safe sandbox", "Agents must be tested before they touch the network."],
    ];
    for (let i = 0; i < why.length; i++) {
      const y = 2.4 + i * 0.7;
      await iconCircle(s, pres, why[i][0], 0.5, y + 0.04, 0.46, RED);
      txt(s, why[i][1], { x: 1.1, y, w: 3.3, h: 0.26, fontFace: HEAD, fontSize: 11, bold: true });
      txt(s, why[i][2], { x: 1.1, y: y + 0.27, w: 3.35, h: 0.38, fontSize: 9.5, color: MUTED });
    }

    txt(s, "GOALS · STATUS TODAY", { x: 4.85, y: 2.1, w: 4.6, h: 0.22, fontSize: 9, bold: true, color: C_HW, charSpacing: 1.5 });
    const goals = [
      ["Intent → configuration through the SDN controller", "PARTIAL"],
      ["Every change tested in the ns-3 twin before commit", "PARTIAL"],
      ["Closed loop on real radios: verify, then roll back", "PLANNED"],
      ["Standard interfaces end to end, no vendor lock-in", "PARTIAL"],
      ["AI/ML agents trained and gated in the twin", "PLANNED"],
    ];
    for (let i = 0; i < goals.length; i++) {
      const y = 2.4 + i * 0.56;
      card(s, pres, 4.85, y, 4.65, 0.48);
      txt(s, `G${i + 1}`, { x: 4.97, y, w: 0.4, h: 0.48, fontFace: HEAD, fontSize: 12, bold: true, color: C_HW, valign: "middle" });
      txt(s, goals[i][0], { x: 5.38, y, w: 3.0, h: 0.48, fontSize: 10, valign: "middle" });
      badge(s, pres, 8.45, y + 0.13, goals[i][1], 0.95);
    }
    s.addNotes(
      "Purpose: an intent-driven, twin-validated closed loop for microwave and millimetre-wave transport in 5G/6G networks, built on the open-source ETSI TeraFlowSDN controller, the ns-3 simulator and Ceragon MH-T261 radios.\n" +
      "Why: (1) at 60-80 GHz, rain attenuation drives adaptive modulation down; the ns-3 scenario models hop-1 rate falling from 1 Gbps to 100 Mbps under heavy rain. (2) Radio changes are done per device and a mistake lands on live traffic. (3) Intent, SDN, simulator and radio speak different protocols on timescales from microseconds to days. (4) AI agents, such as reinforcement-learning policies, need an isolated place to train and be validated.\n" +
      "Goals and where they stand: G1 intents reach TFS and the radio driver (PARTIAL: key mismatch, canned read-back). G2 the ns-3 scenario runs over SSH but its results do not gate commits yet (PARTIAL). G3 verify and rollback after commit are not implemented (PLANNED). G4 RESTCONF/YANG is real; TMF921, TS 28.561 and CAPIF are labels (PARTIAL). G5 no ML in the loop yet (PLANNED). The gap register and roadmap later in the deck show how each goal gets closed."
    );
  }

  // ===================================================================
  // 2. The problem
  // ===================================================================
  {
    const s = pres.addSlide();
    s.background = { color: WHITE };
    title(s, "The problem", "Four components, four languages, four clocks");
    const lo = -6.3, hi = 5.3, X0 = 3.75, X1 = 9.5;
    const X = (v) => X0 + ((v - lo) / (hi - lo)) * (X1 - X0);
    const rowY = 1.45, rowH = 0.75, axisY = rowY + 4 * rowH + 0.05;
    const ticks = [[-6, "1 µs"], [-3, "1 ms"], [0, "1 s"], [Math.log10(60), "1 min"], [Math.log10(3600), "1 h"], [Math.log10(86400), "1 day"]];
    for (const [v, lab] of ticks) {
      s.addShape(pres.shapes.LINE, { x: X(v), y: rowY - 0.1, w: 0, h: axisY - rowY + 0.1, line: { color: LINE, width: 0.75 } });
      txt(s, lab, { x: X(v) - 0.4, y: axisY + 0.05, w: 0.8, h: 0.25, fontSize: 10, color: MUTED, align: "center" });
    }
    s.addShape(pres.shapes.LINE, { x: X0, y: axisY, w: X1 - X0, h: 0, line: { color: MUTED, width: 1 } });
    txt(s, "Operating timescale (log)", { x: X0, y: axisY + 0.32, w: X1 - X0, h: 0.25, fontSize: 9.5, italic: true, color: MUTED, align: "center" });
    const rows = [
      [fa.FaUserTie, C_INTENT, "Intent (CER-Intent)", "natural language / JSON", Math.log10(60), Math.log10(86400), "minutes – days"],
      [fa.FaProjectDiagram, C_SDN, "SDN (TeraFlowSDN)", "REST NBI · gRPC services", -0.3, Math.log10(60), "seconds"],
      [fa.FaFlask, C_SIM, "Simulator (ns-3.45)", "C++ event queue", -6, -3, "microseconds"],
      [fa.FaBroadcastTower, C_HW, "Radio (MH-T261)", "RESTCONF · PHY", -5, -3, "sub-ms"],
    ];
    for (let i = 0; i < rows.length; i++) {
      const [I, c, name, speaks, a, b, lab] = rows[i];
      const y = rowY + i * rowH;
      await iconCircle(s, pres, I, 0.5, y + 0.1, 0.5, c);
      txt(s, name, { x: 1.15, y: y + 0.08, w: 2.5, h: 0.28, fontFace: HEAD, fontSize: 12.5, bold: true });
      txt(s, speaks, { x: 1.15, y: y + 0.36, w: 2.5, h: 0.25, fontSize: 10.5, color: MUTED });
      s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: X(a), y: y + 0.17, w: X(b) - X(a), h: 0.36, fill: { color: c }, line: { color: c }, rectRadius: 0.08 });
      txt(s, lab, { x: X(a), y: y + 0.17, w: X(b) - X(a), h: 0.36, fontSize: 10.5, bold: true, color: WHITE, align: "center", valign: "middle" });
    }
    card(s, pres, 0.5, 4.85, 3.05, 0.5);
    txt(s, [{ text: "Adapters ", options: { bold: true, color: NAVY } }, { text: "translate both the protocol and the clock between neighbours.", options: { color: INK } }],
      { x: 0.62, y: 4.85, w: 2.85, h: 0.5, fontSize: 10.5, valign: "middle" });
    s.addNotes("Unchanged from the earlier deck: the four parts run on timescales from microseconds (ns-3 events) to days (operator intent). The adapters described next translate protocol and time between them.");
  }

  // ===================================================================
  // 3. As-built architecture
  // ===================================================================
  {
    const s = pres.addSlide();
    s.background = { color: WHITE };
    title(s, "As-built architecture", "What is actually wired together today");

    async function box(x, y, w, h, I, c, name, sub, status) {
      s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, fill: { color: WHITE }, line: { color: c, width: 1.5 }, rectRadius: 0.08, shadow: { type: "outer", blur: 4, offset: 1, angle: 90, color: "000000", opacity: 0.12 } });
      await iconCircle(s, pres, I, x + 0.12, y + 0.14, 0.4, c);
      txt(s, name, { x: x + 0.6, y: y + 0.1, w: w - 0.7, h: 0.26, fontFace: HEAD, fontSize: 11, bold: true });
      txt(s, sub, { x: x + 0.6, y: y + 0.36, w: w - 0.7, h: 0.42, fontSize: 9, color: MUTED });
      badge(s, pres, x + w - 1.07, y + h - 0.32, status);
    }
    function lbl(x, y, w, t, c = NAVY) {
      txt(s, t, { x, y, w, h: 0.2, fontSize: 8.5, bold: true, color: c, align: "center" });
    }

    await box(0.5, 1.35, 2.6, 1.15, fa.FaUserTie, C_INTENT, "CER-Intent", "Flask + Socket.IO :5000\nparser · architect · reconciler", "IMPLEMENTED");
    await box(3.7, 1.35, 2.6, 1.15, fa.FaProjectDiagram, C_SDN, "TeraFlowSDN", "microk8s · NBI :8080\nclients use localhost:8088", "IMPLEMENTED");
    await box(6.9, 1.35, 2.6, 1.15, fa.FaBroadcastTower, C_HW, "Ceragon MH-T261", "192.168.1.225 · RESTCONF\ndevice ctu-96", "IMPLEMENTED");
    await box(0.5, 3.35, 2.6, 1.15, fa.FaFlask, C_SIM, "ns-3.45 on cersrv-029", "tsn_wifi_ceragon scenario\nSSH + JSON markers", "PARTIAL");
    await box(3.7, 3.35, 2.6, 1.15, fa.FaServer, NAVY2, "Twin API + bridge", ":9100 what-if = formulas\n:9099 bridge output unused", "MOCK");

    // CER-Intent -> TFS
    arrow(s, pres, 3.1, 1.8, 3.7, 1.8, NAVY);
    lbl(2.95, 1.55, 0.9, "PUT device");
    // TFS -> radio (driver 22)
    arrow(s, pres, 6.3, 1.8, 6.9, 1.8, NAVY);
    lbl(6.15, 1.55, 0.9, "driver 22");
    // CER-Intent -> radio probe (GET only)
    s.addShape(pres.shapes.LINE, { x: 1.8, y: 2.5, w: 0, h: 0.35, line: { color: RED, width: 1.25, dashType: "dash" } });
    s.addShape(pres.shapes.LINE, { x: 1.8, y: 2.85, w: 6.4, h: 0, line: { color: RED, width: 1.25, dashType: "dash" } });
    arrow(s, pres, 8.2, 2.85, 8.2, 2.5, RED, false, true);
    txt(s, "direct GET of candidate datastore (health probe only)", { x: 4.3, y: 2.9, w: 3.8, h: 0.2, fontSize: 8.5, italic: true, color: RED, align: "center" });
    // CER-Intent -> ns-3
    arrow(s, pres, 1.2, 2.5, 1.2, 3.35, C_SIM);
    lbl(0.2, 2.97, 0.95, "SSH run", C_SIM);
    // bridge polls TFS
    arrow(s, pres, 5.0, 3.35, 5.0, 2.5, MUTED, false, true);
    lbl(5.05, 3.12, 1.0, "poll 1 s", MUTED);

    // key
    card(s, pres, 6.9, 3.35, 2.6, 1.15);
    txt(s, "Only the solid arrows move real configuration. The twin API and bridge are not yet in the loop.", { x: 7.05, y: 3.45, w: 2.3, h: 0.95, fontSize: 10, color: INK, valign: "middle" });

    s.addNotes(
      "CER-Intent (cer-intent/run.py, cer_intent/api/server.py) serves REST and Socket.IO on :5000 and writes to TeraFlowSDN with PUT /tfs-api/device/{uuid} carrying CONFIGACTION_SET rules (cer_intent/device/adapter.py TeraFlowAdapter, device/tfs_client.py). Clients default to TERAFLOW_URL=http://localhost:8088; the TFS NBI service listens on 8080 (teraflowsdn/manifests/nbiservice.yaml), so 8088 is a local port-forward or proxy.\n" +
      "TeraFlowSDN is deployed with microk8s via my_deploy.sh with only context, device, pathcomp, service, nbi and webui. The Ceragon driver (DEVICEDRIVER_CERAGON = 22) pushes RESTCONF to the MH-T261 at 192.168.1.225 (manifests/ceragon_mh_t261_descriptor.json).\n" +
      "ns-3.45 runs on cersrv-029: tsn_simulation_runner.py SSHes to efid@cersrv-029 and parses JSON between ===TSN_METRICS_START/END===. If SSH fails, it returns constants that are still labelled as ns-3 output, hence PARTIAL.\n" +
      "tfs_digital_twin_api.py (:9100) computes what-if results with closed-form formulas; ns3_tfs_runtime_bridge.py (:9099) polls TFS every second and writes ns3_link_state.json, which no ns-3 program reads. Hence MOCK.\n" +
      "The red dashed path: the dashboard's 'physical write' is a GET of https://192.168.1.225:80/restconf/ds/ietf-datastores:candidate used as a health probe (web_dashboard.py, cer_intent/api/digital_twin_routes.py)."
    );
  }

  // ===================================================================
  // 4. Repositories
  // ===================================================================
  {
    const s = pres.addSlide();
    s.background = { color: WHITE };
    title(s, "Code map", "Three repositories, one system");
    const repos = [
      [fa.FaUserTie, C_INTENT, "cer-intent", "45 Python files · 9.1k lines (core)", [
        "Intent parser, schema, validator", "Rule-based architect with 9 skills", "TFS + RESTCONF + XML adapters", "Reconciler, audit log, dashboards"],
        "Vendors a copy of the twin repo in tfs_unity/"],
      [fa.FaFlask, C_SIM, "tfs-ns3-digital-twin", "26 Python files · 8.7k lines · 22/22 tests", [
        "TFS → ns-3 C++ generator", "ns-3.45 TSN / 60 GHz scenario", "Twin API :9100, bridge :9099", "Fidelity governor, web dashboard"],
        "Modules duplicated at root and in src/"],
      [fa.FaProjectDiagram, C_SDN, "teraflowsdn", "upstream TFS + Ceragon driver (881 lines)", [
        "CeragonDriver, driver enum 22", "RESTCONF client: stage → commit", "51 YANG models (radio-bridge-tg)", "MH-T261 and IP-50C descriptors"],
        "Upstream history squashed; version label unverified"],
    ];
    const cw = 2.9, gap = 0.15;
    for (let i = 0; i < repos.length; i++) {
      const [I, c, name, meta, items, warn] = repos[i];
      const x = 0.5 + i * (cw + gap), y = 1.35;
      card(s, pres, x, y, cw, 3.85);
      await iconCircle(s, pres, I, x + 0.18, y + 0.18, 0.5, c);
      txt(s, name, { x: x + 0.8, y: y + 0.18, w: cw - 0.9, h: 0.28, fontFace: HEAD, fontSize: 13, bold: true, color: NAVY });
      txt(s, meta, { x: x + 0.8, y: y + 0.46, w: cw - 0.9, h: 0.36, fontSize: 9, color: MUTED });
      for (let j = 0; j < items.length; j++) {
        const yy = y + 1.0 + j * 0.45;
        s.addImage({ data: await icon(fa.FaChevronRight, c), x: x + 0.22, y: yy + 0.06, w: 0.16, h: 0.16 });
        txt(s, items[j], { x: x + 0.48, y: yy, w: cw - 0.6, h: 0.3, fontSize: 10.5 });
      }
      s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: x + 0.15, y: y + 3.0, w: cw - 0.3, h: 0.65, fill: { color: "FDECEC" }, line: { color: "FDECEC" }, rectRadius: 0.06 });
      s.addImage({ data: await icon(fa.FaExclamationTriangle, RED), x: x + 0.27, y: y + 3.2, w: 0.22, h: 0.22 });
      txt(s, warn, { x: x + 0.6, y: y + 3.0, w: cw - 0.8, h: 0.65, fontSize: 9.5, color: "8A2A2A", valign: "middle" });
    }
    s.addNotes(
      "cer-intent: core package cer_intent/ (parser, schema, validator, yang_builder, translators, architect, device adapters, assurance, api). tfs_unity/ is a copy of the tfs-ns3-digital-twin repo; ceragon_tfs_adapter/ is an installable package; tfs_upstream_contribution/ holds the proposed TFS driver patch.\n" +
      "tfs-ns3-digital-twin: Python modules exist at the repo root and again in src/. Five are identical; tsn_simulation_runner.py has diverged (404 lines at root, 236 in src/). Tests: 22 pass (python -m pytest tests).\n" +
      "teraflowsdn: one squashed commit. Custom code is src/device/service/drivers/ceragon/ (CeragonDriver.py, client.py, templates.py, models.py, Tools.py, 51 YANG files), proto enum DEVICEDRIVER_CERAGON = 22, device type ceragon-wireless, and two descriptors in manifests/. The README calls this TFS 7.0; the code does not confirm a version."
    );
  }

  // ===================================================================
  // 5. Intent layer
  // ===================================================================
  {
    const s = pres.addSlide();
    s.background = { color: WHITE };
    title(s, "Intent layer · CER-Intent", "From a sentence to device configuration");
    const steps = [
      [fa.FaCommentDots, "Parse", "Gemini 1.5 Flash, regex fallback", "IMPLEMENTED"],
      [fa.FaCheckDouble, "Validate", "topology + capability matrix", "IMPLEMENTED"],
      [fa.FaChessKnight, "Plan", "9 rule-based skills", "PARTIAL"],
      [fa.FaUserCheck, "Approve", "human gate (HTTP 202)", "IMPLEMENTED"],
      [fa.FaCogs, "Apply", "TFS · RESTCONF · simulated", "IMPLEMENTED"],
    ];
    const sw = 1.72, sg = 0.1;
    for (let i = 0; i < steps.length; i++) {
      const [I, t, d, st] = steps[i];
      const x = 0.5 + i * (sw + sg);
      card(s, pres, x, 1.3, sw, 1.35);
      await iconCircle(s, pres, I, x + 0.14, 1.42, 0.42, C_INTENT);
      txt(s, `${i + 1}  ${t}`, { x: x + 0.64, y: 1.46, w: sw - 0.7, h: 0.3, fontFace: HEAD, fontSize: 11.5, bold: true, color: NAVY, valign: "middle" });
      txt(s, d, { x: x + 0.14, y: 1.9, w: sw - 0.25, h: 0.36, fontSize: 9.5, color: MUTED });
      badge(s, pres, x + 0.14, 2.3, st);
      if (i < steps.length - 1) arrow(s, pres, x + sw, 1.97, x + sw + sg, 1.97, NAVY);
    }

    const strat = Object.entries(STATS.architect_strategies).filter(([k]) => k !== "none");
    s.addChart(pres.charts.BAR, [{ name: "Plans", labels: strat.map(([k]) => k.replace(/_/g, " ")), values: strat.map(([, v]) => v) }], {
      x: 0.4, y: 2.85, w: 5.3, h: 2.45, barDir: "bar", chartColors: [C_INTENT],
      showTitle: true, title: "Architect strategies chosen (audit log)", titleFontFace: HEAD, titleFontSize: 11, titleColor: NAVY,
      catAxisOrientation: "maxMin", catAxisLabelFontFace: BODY, catAxisLabelFontSize: 9.5, catAxisLabelColor: INK, catAxisLineShow: false,
      valAxisHidden: true, valGridLine: { style: "none" }, catGridLine: { style: "none" },
      showValue: true, dataLabelPosition: "outEnd", dataLabelFontSize: 10, dataLabelColor: INK, barGapWidthPct: 45, showLegend: false,
    });

    card(s, pres, 6.0, 2.9, 3.5, 2.35);
    txt(s, "Real operator inputs", { x: 6.2, y: 3.0, w: 3.1, h: 0.28, fontFace: HEAD, fontSize: 11, bold: true, color: NAVY });
    const quotes = ["Increase capacity on link-A-B to 5 Gbps for eMBB slice", "Set ACM range 64QAM to 2048QAM on sector-south links", "Create slice slice-uran-6g with 1 Gbps on Ceragon MH-T261"];
    for (let j = 0; j < quotes.length; j++) {
      s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 6.15, y: 3.35 + j * 0.62, w: 3.2, h: 0.54, fill: { color: WHITE }, line: { color: WHITE }, rectRadius: 0.06 });
      txt(s, "“" + quotes[j] + "”", { x: 6.25, y: 3.35 + j * 0.62, w: 3.0, h: 0.54, fontSize: 9.5, italic: true, valign: "middle" });
    }
    s.addNotes(
      "1 Parse (cer_intent/intent_parser.py): Google Gemini (GEMINI_MODEL, default gemini-1.5-flash) with a schema prompt and three few-shot examples; without a key it falls back to regex/keyword rules; JSON input skips parsing. Eight intent types: capacity, qos, modulation, resilience, slice, energy, sync, security (intent_schema.py, Pydantic).\n" +
      "2 Validate (intent_validator.py): topology and the DEVICE_CAPABILITIES hardware matrix.\n" +
      "3 Plan (architect/agent.py): nine rule-based skills score strategies by a heuristic confidence; the conflict resolver is a mock with time.sleep(0.1). PARTIAL because the 'AI architect' is rules, not a model.\n" +
      "4 Approve: POST /api/v1/intent returns 202 awaiting_approval unless always_apply; POST /intents/<id>/approve resumes.\n" +
      "5 Apply: ArchitectExecutor or legacy translators, then adapter.apply_all (TeraFlowAdapter, DirectRESTAdapter, SimulatedAdapter, IP-50C XML).\n" +
      "Chart: counts of 'Architect plan created: <strategy>' events in data/audit_log.jsonl (audit_stats.py). Quotes are verbatim inputs from the same log.\n" +
      "Roadmap: add pluggable parsers (on-prem Qwen, Claude) next to Gemini, and grow the skill bank to cover more transport knowledge."
    );
  }

  // ===================================================================
  // 6. Operating data
  // ===================================================================
  {
    const s = pres.addSlide();
    s.background = { color: WHITE };
    title(s, "Operating data", "What the audit log shows");
    const tiles = [
      [fmt(intents), "intents parsed"],
      [fmt(applyTotal), "configuration applies"],
      [`${((tfsApplies.ok / tfsTotal) * 100).toFixed(1)}%`, "accepted by TeraFlowSDN"],
      [fmt(STATS.distinct_devices), "devices configured"],
    ];
    for (let i = 0; i < tiles.length; i++) {
      const x = 0.5 + i * 2.3;
      card(s, pres, x, 1.3, 2.15, 1.0);
      txt(s, tiles[i][0], { x: x + 0.18, y: 1.36, w: 1.9, h: 0.55, fontFace: HEAD, fontSize: 26, bold: true, color: C_SDN, valign: "middle" });
      txt(s, tiles[i][1], { x: x + 0.18, y: 1.92, w: 1.9, h: 0.3, fontSize: 10.5 });
    }
    const be = STATS.applies_by_backend;
    const names = Object.keys(be).sort((a, b) => (be[b].ok + be[b].failed) - (be[a].ok + be[a].failed));
    s.addChart(pres.charts.BAR, [
      { name: "Succeeded", labels: names.map((n) => n.replace("Adapter", "")), values: names.map((n) => be[n].ok) },
      { name: "Failed", labels: names.map((n) => n.replace("Adapter", "")), values: names.map((n) => be[n].failed) },
    ], {
      x: 0.4, y: 2.5, w: 4.6, h: 2.75, barDir: "bar", barGrouping: "stacked", chartColors: [C_HW, RED],
      showTitle: true, title: "Configuration applies by backend", titleFontFace: HEAD, titleFontSize: 11, titleColor: NAVY,
      catAxisOrientation: "maxMin", catAxisLabelFontSize: 10, catAxisLabelColor: INK, catAxisLineShow: false,
      valAxisLabelFontSize: 9, valAxisLabelColor: MUTED, valGridLine: { color: "E6EBF0", size: 0.5 }, catGridLine: { style: "none" },
      showLegend: true, legendPos: "b", legendFontSize: 9.5, barGapWidthPct: 40,
    });
    const months = Object.entries(STATS.intents_parsed_by_month);
    s.addChart(pres.charts.BAR, [{ name: "Intents", labels: months.map(([m]) => m), values: months.map(([, v]) => v) }], {
      x: 5.2, y: 2.5, w: 4.4, h: 2.0, barDir: "col", chartColors: [C_INTENT],
      showTitle: true, title: "Intents parsed per month", titleFontFace: HEAD, titleFontSize: 11, titleColor: NAVY,
      catAxisLabelFontSize: 9.5, catAxisLabelColor: INK, valAxisHidden: true, valGridLine: { style: "none" }, catGridLine: { style: "none" },
      showValue: true, dataLabelPosition: "outEnd", dataLabelFontSize: 10, dataLabelColor: INK, showLegend: false, barGapWidthPct: 60,
    });
    txt(s, [
      { text: `Parse → last apply: median ${Math.round(p2a.median)} ms`, options: { bold: true, color: NAVY } },
      { text: ` (n = ${p2a.n}, ${p2a.under_1s} under 1 s). ${period}.`, options: { color: MUTED } },
    ], { x: 5.3, y: 4.6, w: 4.2, h: 0.6, fontSize: 10, valign: "middle" });
    s.addNotes(
      `All numbers come from cer-intent/data/audit_log.jsonl (${fmt(STATS.events_total)} events, ${period}) via docs/deck/audit_stats.py.\n` +
      `TeraFlowAdapter: ${tfsApplies.ok} succeeded, ${tfsApplies.failed} failed. Failures: 'Cannot reach TeraFlow SDN at http://localhost:8088' (32) and HTTP 500 from the NBI (3). 'Succeeded' means the TFS NBI accepted the config rule; it does not prove the radio changed, because the Ceragon driver's read-back is canned (see the hardware slide).\n` +
      `SimulatedAdapter ${be.SimulatedAdapter ? be.SimulatedAdapter.ok : 0} and IP-50C XML ${be.IP50CXMLAdapter ? be.IP50CXMLAdapter.ok : 0} applies are local simulations or files.\n` +
      `Parse-to-last-apply is measured only for the ${p2a.n} intents whose applies carry the intent id; the median is ${Math.round(p2a.median)} ms and the maximum ${Math.round(p2a.max / 1000)} s, because the long spans include waiting for human approval.\n` +
      `One drift event was recorded: 'SNR 11.9 dB on link-A-F may not sustain min modulation 64QAM' (the reconciler works on synthetic telemetry).`
    );
  }

  // ===================================================================
  // 7. TFS integration
  // ===================================================================
  {
    const s = pres.addSlide();
    s.background = { color: WHITE };
    title(s, "TeraFlowSDN integration", "Deployed components and the calls we use");
    txt(s, "DEPLOYED (my_deploy.sh)", { x: 0.5, y: 1.3, w: 4.4, h: 0.22, fontSize: 9, bold: true, color: C_HW, charSpacing: 1.5 });
    const on = [["context", "gRPC 1010"], ["device", "gRPC 2020"], ["service", "gRPC 3030"], ["pathcomp", "gRPC 10020"], ["nbi", "HTTP 8080"], ["webui", "HTTP 8004"]];
    for (let i = 0; i < on.length; i++) {
      const x = 0.5 + (i % 3) * 1.48, y = 1.6 + Math.floor(i / 3) * 0.55;
      s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w: 1.4, h: 0.45, fill: { color: "DDF3E8" }, line: { color: "DDF3E8" }, rectRadius: 0.06 });
      txt(s, [{ text: on[i][0], options: { bold: true, color: "157A50", breakLine: true } }, { text: on[i][1], options: { color: MUTED, fontSize: 8.5 } }], { x: x + 0.1, y, w: 1.25, h: 0.45, fontSize: 10, valign: "middle" });
    }
    txt(s, "NOT DEPLOYED (telemetry · analytics · ML)", { x: 0.5, y: 2.85, w: 4.4, h: 0.22, fontSize: 9, bold: true, color: MUTED, charSpacing: 1 });
    const off = [["monitoring", "7070"], ["kpi_manager", "30010"], ["telemetry", "30050"], ["analytics", "30080"], ["automation", "30200"], ["forecaster", "10040"]];
    for (let i = 0; i < off.length; i++) {
      const x = 0.5 + (i % 3) * 1.48, y = 3.15 + Math.floor(i / 3) * 0.55;
      s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w: 1.4, h: 0.45, fill: { color: WHITE }, line: { color: "9AA7B4", width: 1, dashType: "dash" }, rectRadius: 0.06 });
      txt(s, [{ text: off[i][0], options: { bold: true, color: MUTED, breakLine: true } }, { text: "gRPC " + off[i][1], options: { color: MUTED, fontSize: 8.5 } }], { x: x + 0.1, y, w: 1.25, h: 0.45, fontSize: 10, valign: "middle" });
    }
    txt(s, "The 10010–10040 ports shown in the old dashboard are mock values.", { x: 0.5, y: 4.35, w: 4.4, h: 0.4, fontSize: 9.5, italic: true, color: RED });

    card(s, pres, 5.3, 1.3, 4.2, 3.95);
    txt(s, "NBI calls used by CER-Intent and the twin", { x: 5.5, y: 1.42, w: 3.9, h: 0.28, fontFace: HEAD, fontSize: 11, bold: true, color: NAVY });
    const calls = [["GET", "/tfs-api/contexts"], ["GET", "/tfs-api/context/admin/topology_details/admin"], ["GET", "/tfs-api/devices · /links"], ["PUT", "/tfs-api/device/{uuid}  (config rules)"], ["POST", "/tfs-api/context/admin/slices"]];
    for (let i = 0; i < calls.length; i++) {
      const y = 1.82 + i * 0.4;
      s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 5.5, y: y + 0.04, w: 0.55, h: 0.26, fill: { color: calls[i][0] === "GET" ? C_SDN : NAVY }, line: { color: WHITE }, rectRadius: 0.05 });
      txt(s, calls[i][0], { x: 5.5, y: y + 0.04, w: 0.55, h: 0.26, fontSize: 8, bold: true, color: WHITE, align: "center", valign: "middle" });
      txt(s, calls[i][1], { x: 6.15, y, w: 3.3, h: 0.34, fontFace: MONO, fontSize: 8.5, valign: "middle" });
    }
    txt(s, "Ceragon device in TFS", { x: 5.5, y: 3.9, w: 3.9, h: 0.25, fontFace: HEAD, fontSize: 10.5, bold: true, color: NAVY });
    txt(s, "DEVICEDRIVER_CERAGON = 22 · type microwave-radio-system · ceragon-mh-t261-ctu-96 @ 192.168.1.225:80", { x: 5.5, y: 4.17, w: 3.9, h: 0.5, fontSize: 9.5, color: INK });
    badge(s, pres, 5.5, 4.8, "IMPLEMENTED");
    txt(s, "No TFS Service or PathComp (CSPF) request is made yet.", { x: 6.55, y: 4.75, w: 2.9, h: 0.35, fontSize: 9, italic: true, color: MUTED, valign: "middle" });
    s.addNotes(
      "Deployed components: teraflowsdn/my_deploy.sh exports TFS_COMPONENTS='context device pathcomp service nbi webui'. Ports from manifests/*service.yaml: context 1010, device 2020, service 3030, pathcomp 10020, nbi 8080, webui 8004.\n" +
      "Not deployed but available in the tree: monitoring 7070, kpi_manager 30010, kpi_value_api/writer 30020/30030, telemetry 30050/30060, analytics 30080/30090, automation 30200, forecaster 10040, plus Kafka. These are the natural hosts for streamed KPIs and Python analytics.\n" +
      "The old dashboard's gRPC ports 10010/10020/10030/10040 come from mock JSON in web_dashboard.py get_tfs_microservice_state() and cer_intent/api/digital_twin_routes.py.\n" +
      "NBI calls: cer_intent/device/tfs_client.py and tfs_api_client.py. Writes are PUT /tfs-api/device/{uuid} with CONFIGACTION_SET custom rules; slices go to POST /tfs-api/context/admin/slices. The dashboard's POST /tfs-api/device/{uuid}/config is not a TFS endpoint.\n" +
      "Ceragon: proto/context.proto DEVICEDRIVER_CERAGON = 22; src/device/service/drivers/__init__.py registers it (needs LOAD_ALL_DEVICE_DRIVERS); descriptor manifests/ceragon_mh_t261_descriptor.json. The WebUI device form has no Ceragon checkbox, so devices are added by descriptor."
    );
  }

  // ===================================================================
  // 8. Simulation adapter
  // ===================================================================
  {
    const s = pres.addSlide();
    s.background = { color: WHITE };
    title(s, "Simulation adapter · ns-3.45", "The TSN-over-microwave scenario the twin runs");

    // topology chain
    const nodes = [["STA ×2", C_INTENT], ["Wi-Fi AP ×2", C_INTENT], ["C0", C_HW], ["C1", C_HW], ["C2", C_HW], ["C3 → sink", C_HW]];
    const links = ["802.11n\nHtMcs7", "10 Gbps", "60 GHz\n1 Gbps · 0.15 ms", "10 Gbps\n0.02 ms", "80 GHz\n10 Gbps · 0.10 ms"];
    const nw = 1.0, lw = (9.0 - nodes.length * nw) / links.length;
    for (let i = 0; i < nodes.length; i++) {
      const x = 0.5 + i * (nw + lw);
      s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y: 1.45, w: nw, h: 0.5, fill: { color: WHITE }, line: { color: nodes[i][1], width: 1.5 }, rectRadius: 0.08 });
      txt(s, nodes[i][0], { x, y: 1.45, w: nw, h: 0.5, fontSize: 9.5, bold: true, align: "center", valign: "middle" });
      if (i < links.length) {
        const lx = x + nw;
        s.addShape(pres.shapes.LINE, { x: lx, y: 1.7, w: lw, h: 0, line: { color: i === 2 ? C_SIM : MUTED, width: i === 2 ? 3 : 1.5 } });
        txt(s, links[i], { x: lx - 0.3, y: 1.98, w: lw + 0.6, h: 0.36, fontSize: 8, color: i === 2 ? C_SIM : MUTED, bold: i === 2, align: "center" });
      }
    }
    txt(s, "rain attenuation acts on this hop", { x: 0.5 + 2 * (nw + lw) + nw - 0.4, y: 1.2, w: lw + 0.8, h: 0.22, fontSize: 8, italic: true, color: C_SIM, align: "center" });

    // traffic + queue facts
    const facts = [
      ["TSN flow", "128 B every 1 ms · ToS 0xC0 (AC_VO, band 0)"],
      ["Best effort", "1400 B at 150 Mbps × surge factor"],
      ["Queue", "PfifoFast (QoS on) or FIFO · 150 packets"],
      ["SLA check", "TSN mean delay > 1.5 ms or loss > 0.001 %"],
    ];
    for (let i = 0; i < facts.length; i++) {
      const y = 2.6 + i * 0.5;
      card(s, pres, 0.5, y, 4.4, 0.42);
      txt(s, facts[i][0], { x: 0.65, y, w: 1.15, h: 0.42, fontSize: 10, bold: true, color: NAVY, valign: "middle" });
      txt(s, facts[i][1], { x: 1.8, y, w: 3.05, h: 0.42, fontSize: 9.5, valign: "middle" });
    }
    badge(s, pres, 0.5, 4.72, "IMPLEMENTED");
    txt(s, "fallback when SSH fails:", { x: 1.55, y: 4.7, w: 1.6, h: 0.26, fontSize: 9, color: MUTED, valign: "middle" });
    badge(s, pres, 3.1, 4.72, "MOCK", 0.7);

    s.addChart(pres.charts.BAR, [{ name: "Rate", labels: ["0 dB", "< 8 dB", "8–15 dB", "15–25 dB", "≥ 25 dB"], values: [1000, 750, 500, 250, 100] }], {
      x: 5.1, y: 2.5, w: 4.5, h: 2.75, barDir: "col", chartColors: [C_HW, C_SIM, C_SIM, C_SIM, RED],
      showTitle: true, title: "Hop-1 rate vs rain attenuation (Mbps, scenario rule)", titleFontFace: HEAD, titleFontSize: 10.5, titleColor: NAVY,
      catAxisLabelFontSize: 9, catAxisLabelColor: INK, valAxisHidden: true, valAxisMaxVal: 1150, valGridLine: { style: "none" }, catGridLine: { style: "none" },
      showValue: true, dataLabelPosition: "outEnd", dataLabelFontSize: 10, dataLabelColor: INK, showLegend: false, barGapWidthPct: 50,
    });
    s.addNotes(
      "Scenario: tfs-ns3-digital-twin/simulation/tsn_wifi_ceragon.cc (ns-3.45). Two stations to two 802.11n APs (HtMcs7), then C0 -60 GHz 1 Gbps 0.15 ms- C1 -10 Gbps 0.02 ms- C2 -80 GHz 10 Gbps 0.10 ms- C3 to the sink.\n" +
      "Traffic: TSN flow 128 B at 1.024 Mbps (one packet per ms) with ToS 0xC0, mapped to PfifoFast band 0 and Wi-Fi AC_VO. There is no 802.1Q VLAN/PCP tagging in the simulation; the 'PCP 6' label in the old deck comes from dashboard mock JSON. Best effort: 1400 B at 150 Mbps times the surge factor.\n" +
      "Rain: rainLossDb steps hop-1 rate to 750/500/250/100 Mbps at the 8/15/25 dB thresholds; this is a rule, not an ACM model. FlowMonitor results are printed as JSON between ===TSN_METRICS_START/END=== and parsed by tsn_simulation_runner.py over SSH (efid@cersrv-029, 25 s timeout). The Wi-Fi contention, retry and airtime numbers in that JSON are hard-coded.\n" +
      "Fallback: if SSH fails the runner returns constants (0.93 ms TSN with QoS, 6.83 / 8.12 ms without) and still labels them as ns-3 output. MOCK.\n" +
      "Second path: tfs_topology_to_ns3.py generates a C++ program from the TFS topology (one point-to-point link per TFS link, /30 subnets, optional 500 Mbps OnOff traffic, NetAnim). It produces no metrics yet.\n" +
      "The simulation resolution governor (simulation_resolution_governor.py) picks a tier and scales node counts; its per-tier latencies (75, 350, 650, 1150, 35 ms) are constants, not measurements."
    );
  }

  // ===================================================================
  // 9. Hardware path
  // ===================================================================
  {
    const s = pres.addSlide();
    s.background = { color: WHITE };
    title(s, "Hardware path · Ceragon driver", "Stage, commit, discard: real RESTCONF, with gaps");
    const L = 1.4, R = 4.6;
    for (const [x, c, a, b] of [[L, C_SDN, "TFS device service", "CeragonDriver (22)"], [R, C_HW, "MH-T261", "192.168.1.225"]]) {
      s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: x - 0.9, y: 1.3, w: 1.8, h: 0.62, fill: { color: WHITE }, line: { color: c, width: 1.5 }, rectRadius: 0.08 });
      txt(s, a, { x: x - 0.9, y: 1.33, w: 1.8, h: 0.28, fontFace: HEAD, fontSize: 10.5, bold: true, align: "center" });
      txt(s, b, { x: x - 0.9, y: 1.6, w: 1.8, h: 0.25, fontSize: 9, color: c, bold: true, align: "center" });
      s.addShape(pres.shapes.LINE, { x, y: 1.92, w: 0, h: 2.95, line: { color: "AAB6C2", width: 1.25, dashType: "dash" } });
    }
    const msgs = [
      [true, "① PATCH candidate datastore", "radio · VLAN sub-interface · ACM floor", NAVY],
      [true, "② if staging fails: discard-changes", "POST ietf-netconf:discard-changes", RED],
      [true, "③ POST ietf-netconf:commit", "candidate → running", C_HW],
      [false, "④ read state", "returns canned values today", C_SIM],
    ];
    for (let i = 0; i < msgs.length; i++) {
      const [fwd, a, b, c] = msgs[i];
      const y = 2.35 + i * 0.66;
      txt(s, a, { x: L + 0.05, y: y - 0.28, w: R - L - 0.1, h: 0.24, fontSize: 10, bold: true, color: c, align: "center" });
      if (fwd) arrow(s, pres, L, y, R, y, c); else arrow(s, pres, R, y, L, y, c, false, true);
      txt(s, b, { x: L + 0.05, y: y + 0.04, w: R - L - 0.1, h: 0.22, fontSize: 8.5, color: MUTED, align: "center" });
    }
    badge(s, pres, 0.5, 4.95, "IMPLEMENTED");
    txt(s, "steps ①–③", { x: 1.55, y: 4.93, w: 1, h: 0.26, fontSize: 9, color: MUTED, valign: "middle" });
    badge(s, pres, 2.45, 4.95, "MOCK", 0.7);
    txt(s, "step ④", { x: 3.25, y: 4.93, w: 1, h: 0.26, fontSize: 9, color: MUTED, valign: "middle" });

    card(s, pres, 5.6, 1.3, 3.9, 3.95);
    txt(s, "Not yet in place", { x: 5.8, y: 1.42, w: 3.5, h: 0.28, fontFace: HEAD, fontSize: 11.5, bold: true, color: NAVY });
    const gaps = [
      ["No rollback after commit", "discard only runs when staging fails", "PLANNED"],
      ["No telemetry subscription", "SubscribeState returns True, streams nothing", "PLANNED"],
      ["Intent keys ≠ driver keys", "min/max modulation never reaches the radio", "PARTIAL"],
      ["Dashboard wire log and diff", "static JSON, never sent", "MOCK"],
    ];
    for (let i = 0; i < gaps.length; i++) {
      const y = 1.82 + i * 0.83;
      s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 5.75, y, w: 3.6, h: 0.72, fill: { color: WHITE }, line: { color: WHITE }, rectRadius: 0.06 });
      txt(s, gaps[i][0], { x: 5.88, y: y + 0.07, w: 2.4, h: 0.26, fontSize: 10, bold: true });
      txt(s, gaps[i][1], { x: 5.88, y: y + 0.35, w: 3.35, h: 0.3, fontSize: 9, color: MUTED });
      badge(s, pres, 8.3, y + 0.08, gaps[i][2], 0.95);
    }
    s.addNotes(
      "teraflowsdn/src/device/service/drivers/ceragon/client.py: stage_candidate() PATCHes /restconf/ds/ietf-datastores:candidate; on failure apply_* calls discard_candidate() (POST /restconf/operations/ietf-netconf:discard-changes); otherwise commit_candidate() POSTs /restconf/operations/ietf-netconf:commit. Payloads come from templates.py: radio-bridge-tg:radio, ietf-interfaces sub-interfaces for VLAN slices, radio-bridge-tg-acm:acm-configuration for the ACM floor. CeragonDriver.SetConfig routes by resource key (/radio, /frequency, /operating_parameters, /slice, /vlan, /modulation, /acm, /rain).\n" +
      "Gaps: there is no verification after commit and no rollback of a committed change. get_device_state() (lines 95-195) returns hard-coded values (60.48 GHz, SNR 28.5, RSSI -42) and discards the live ietf-interfaces GET. SubscribeState/UnsubscribeState/DeleteConfig return True without doing anything.\n" +
      "Key mismatch: CER-Intent sends /interface[name=...]/modulation with min/max modulation, while the driver's modulation branch reads mrmc_script_id, tx_frequency and tx_power_dbm. Most intents therefore change nothing on the radio.\n" +
      "The old deck's 'two-phase commit with automatic rollback', the four pre-flight gates and the RESTCONF wire log came from static JSON in web_dashboard.py and cer_intent/api/digital_twin_routes.py (which also label the device 'siklu-radio')."
    );
  }

  // ===================================================================
  // 10. Closed loop today vs target
  // ===================================================================
  {
    const s = pres.addSlide();
    s.background = { color: WHITE };
    title(s, "Closed loop", "Today it detects; the target loop also acts");
    function lane(y, label, color, steps) {
      txt(s, label, { x: 0.5, y, w: 9, h: 0.25, fontFace: HEAD, fontSize: 10, bold: true, color, charSpacing: 1.5 });
      const w = 9.0 / steps.length - 0.12;
      for (let i = 0; i < steps.length; i++) {
        const x = 0.5 + i * (w + 0.12);
        card(s, pres, x, y + 0.32, w, 1.25);
        txt(s, steps[i][0], { x: x + 0.1, y: y + 0.4, w: w - 0.2, h: 0.28, fontFace: HEAD, fontSize: 10.5, bold: true, color: NAVY });
        txt(s, steps[i][1], { x: x + 0.1, y: y + 0.68, w: w - 0.2, h: 0.5, fontSize: 9, color: MUTED });
        badge(s, pres, x + 0.1, y + 1.24, steps[i][2], Math.min(0.95, w - 0.2));
        if (i < steps.length - 1) arrow(s, pres, x + w, y + 0.95, x + w + 0.12, y + 0.95, NAVY);
      }
    }
    lane(1.3, "TODAY", C_SIM, [
      ["Intent", "parse, plan, approve", "IMPLEMENTED"],
      ["Apply", "PUT to TFS, driver commit", "IMPLEMENTED"],
      ["Telemetry", "synthetic, every 5 s", "MOCK"],
      ["Drift check", "thresholds, every 10 s", "PARTIAL"],
      ["Alert", "DRIFT state + event", "IMPLEMENTED"],
      ["Remediate", "never runs", "PLANNED"],
    ]);
    lane(3.3, "TARGET", C_HW, [
      ["Intent", "plus live telemetry", "PARTIAL"],
      ["What-if", "ns-3 job per candidate", "PARTIAL"],
      ["Gate", "from simulated KPIs", "PLANNED"],
      ["Commit", "stage → commit", "IMPLEMENTED"],
      ["Verify", "YANG-Push read-back", "PLANNED"],
      ["Rollback", "if KPIs regress", "PLANNED"],
    ]);
    s.addNotes(
      "Today: cer_intent/assurance/telemetry_simulator.py generates sinusoidal load and SNR every 5 s; assurance/reconciler.py checks every 10 s (capacity below 80% of target with utilisation above 90%, latency more than 5 ms over target, SNR below 12 dB) and sets DRIFT plus a Socket.IO intent_drift event. It never re-applies; REMEDIATED is never set. The architect receives empty telemetry because app.telemetry_snapshot is never set.\n" +
      "Target: every candidate change becomes an ns-3 what-if job, the pre-flight gates are computed from its KPIs instead of constant PASS strings, the driver commits, live telemetry verifies the result, and a committed change is rolled back if KPIs regress. The old '~1.9–2.2 s end-to-end' figure is not backed by any log; measure the real loop time once it exists."
    );
  }

  // ===================================================================
  // 11. Standards: claimed vs implemented
  // ===================================================================
  {
    const s = pres.addSlide();
    s.background = { color: WHITE };
    title(s, "Standards", "Claimed vs implemented");
    const rows = [
      ["IETF RFC 8040 RESTCONF", "Ceragon driver: PATCH candidate, commit, discard", "IMPLEMENTED"],
      ["IETF RFC 7950 YANG 1.1", "51 bundled models; payload templates", "IMPLEMENTED"],
      ["IETF RFC 8345 topology", "TFS NBI plugin exists; not used by our code", "PLANNED"],
      ["IETF RFC 6241 NETCONF", "XML generated by yang_builder, never sent", "PARTIAL"],
      ["TM Forum TMF921 intent", "custom schema; :9100 endpoint stores and acknowledges", "MOCK"],
      ["3GPP TS 28.561 NDT", "NDTI state enum only; no NDTJob or report", "PARTIAL"],
      ["3GPP TS 29.222 CAPIF", "static discovery JSON", "MOCK"],
      ["ITU-T Y.3090 / Y.3092", "labels on endpoints and slides", "PLANNED"],
      ["YANG-Push / gNMI", "claimed in docs; driver subscribes to nothing", "PLANNED"],
      ["ITU-R P.838 rain", "approximate coefficients in formulas", "PARTIAL"],
    ];
    const rh = 0.36, y0 = 1.3;
    txt(s, "STANDARD", { x: 0.6, y: y0, w: 2.6, h: 0.25, fontSize: 8.5, bold: true, color: MUTED, charSpacing: 1 });
    txt(s, "WHAT THE CODE DOES", { x: 3.3, y: y0, w: 4.5, h: 0.25, fontSize: 8.5, bold: true, color: MUTED, charSpacing: 1 });
    txt(s, "STATUS", { x: 8.3, y: y0, w: 1.1, h: 0.25, fontSize: 8.5, bold: true, color: MUTED, charSpacing: 1 });
    for (let i = 0; i < rows.length; i++) {
      const y = y0 + 0.3 + i * rh;
      if (i % 2 === 0) s.addShape(pres.shapes.RECTANGLE, { x: 0.5, y, w: 9.0, h: rh, fill: { color: TINT }, line: { color: TINT } });
      txt(s, rows[i][0], { x: 0.6, y, w: 2.65, h: rh, fontSize: 10, bold: true, valign: "middle" });
      txt(s, rows[i][1], { x: 3.3, y, w: 4.9, h: rh, fontSize: 9.5, color: MUTED, valign: "middle" });
      badge(s, pres, 8.3, y + (rh - 0.22) / 2, rows[i][2]);
    }
    s.addNotes(
      "RFC 8040: teraflowsdn/src/device/service/drivers/ceragon/client.py and cer-intent/ceragon_tfs_adapter. RFC 7950: 51 YANG files in drivers/ceragon/schemas/yang (radio-bridge-tg-*, IEEE 802.1Q, IETF, Clixon). RFC 8345: TFS has an ietf_network NBI plugin (src/nbi/service/ietf_network) but CER-Intent reads TFS's own topology_details JSON instead.\n" +
      "RFC 6241: cer_intent/yang_builder.py builds NETCONF XML; ncclient is a dependency but never used to send it.\n" +
      "TMF921: CER-Intent's intent model is a custom Pydantic schema; tfs_digital_twin_api.py POST /api/v1/tmf/tmf921/intent stores the payload and returns 'acknowledged' with no TMF resource model or lifecycle. TMF639 is a minimal GET projection.\n" +
      "TS 28.561: only the NDTI states (NULL, INITIALIZING, SYNCHRONIZED, UPDATING, EXECUTING_EXPERIMENT, TERMINATED) in tfs_digital_twin_api.py; the NdtJob model exists only in generate_deck.py. CAPIF: a static JSON descriptor without OAuth or mTLS.\n" +
      "Y.3090 is a label on /dti/sync; Y.3092 and Q.5040 appear only in slides and a commit message. YANG-Push and gNMI are claimed in docs only. P.838: approximate k and alpha at 60 GHz in formulas."
    );
  }

  // ===================================================================
  // 11b. Interface map with the standards per interface
  // ===================================================================
  {
    const s = pres.addSlide();
    s.background = { color: WHITE };
    title(s, "Standards by interface", "Four interfaces, and the standards that fit each");
    async function node(x, y, I, c, a, b) {
      s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w: 2.0, h: 0.8, fill: { color: WHITE }, line: { color: c, width: 1.5 }, rectRadius: 0.08, shadow: { type: "outer", blur: 4, offset: 1, angle: 90, color: "000000", opacity: 0.12 } });
      await iconCircle(s, pres, I, x + 0.1, y + 0.18, 0.44, c);
      txt(s, a, { x: x + 0.62, y: y + 0.12, w: 1.35, h: 0.28, fontFace: HEAD, fontSize: 10.5, bold: true });
      txt(s, b, { x: x + 0.62, y: y + 0.4, w: 1.35, h: 0.3, fontSize: 8.5, color: MUTED });
    }
    function chip(x, y, w, n, t, c) {
      s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h: 0.5, fill: { color: TINT }, line: { color: c, width: 1 }, rectRadius: 0.06 });
      txt(s, [{ text: n + " ", options: { bold: true, color: c } }, { text: t, options: { color: INK } }], { x: x + 0.08, y, w: w - 0.12, h: 0.5, fontSize: 8.5, valign: "middle" });
    }
    await node(0.5, 2.55, fa.FaUserTie, C_INTENT, "CER-Intent", "LLM + rule agents");
    await node(4.0, 1.35, fa.FaProjectDiagram, C_SDN, "TeraFlowSDN", "SDN controller");
    await node(4.0, 4.35, fa.FaFlask, C_SIM, "Digital twin", "ns-3.45");
    await node(7.5, 1.35, fa.FaBroadcastTower, C_HW, "MH-T261", "Ceragon radio");
    arrow(s, pres, 2.5, 2.75, 4.0, 1.95, NAVY);
    arrow(s, pres, 2.5, 3.15, 4.0, 4.55, NAVY);
    arrow(s, pres, 5.0, 2.15, 5.0, 4.35, NAVY, true);
    arrow(s, pres, 6.0, 1.75, 7.5, 1.75, NAVY);
    chip(0.5, 1.35, 3.3, "①", "TMF921 · TS 28.312 · IETF L3NM / slice NBI", C_INTENT);
    chip(0.5, 4.2, 3.3, "②", "TS 28.561 NDTJob · Y.3092 NDT-m · CAPIF", C_SIM);
    chip(5.2, 2.95, 4.3, "③", "RFC 8345 · RFC 8561 · YANG-Push / gNMI · Y.3092 NDT-p", C_SDN);
    chip(6.2, 2.3, 3.3, "④", "RESTCONF 8040/8527 · YANG · RFC 8561 · TLS", C_HW);
    card(s, pres, 6.3, 3.65, 3.2, 1.5);
    txt(s, "In use today", { x: 6.45, y: 3.72, w: 3.0, h: 0.25, fontFace: HEAD, fontSize: 10, bold: true, color: NAVY });
    txt(s, "① TFS native REST NBI\n② SSH + JSON, custom REST :9100\n③ TFS REST polling every 1 s\n④ RESTCONF candidate → commit", { x: 6.45, y: 3.98, w: 3.0, h: 1.1, fontSize: 9.5, color: INK, paraSpaceAfter: 2 });
    s.addNotes(
      "① CER-Intent agents to TFS (northbound): today TFS native REST (PUT /tfs-api/device, POST slices). Adopt TM Forum TMF921 or 3GPP TS 28.312 for the intent itself, and hand TFS standard service requests through its existing IETF L3NM (RFC 9182), L2NM (RFC 9291) and network-slice (RFC 9543 framework) NBI plugins.\n" +
      "② CER-Intent to the digital twin: today SSH to cersrv-029 plus a custom REST API on :9100. Adopt 3GPP TS 28.561 NDTJob/NDTReport over TS 28.532 operations, which ITU-T Y.3092 calls NDT-m, and expose it through CAPIF (TS 29.222).\n" +
      "③ TFS and the twin: today REST polling every second. Adopt RFC 8345 topology (TFS ietf_network NBI) and RFC 8561 microwave link data for the ns-3 model, and YANG-Push (RFC 8641) or gNMI streaming into TFS KPI/Kafka (Y.3092 NDT-p). Model physics from ITU-R P.838, P.676 and P.530.\n" +
      "④ TFS to the radio: today RESTCONF (RFC 8040) on the NMDA candidate datastore (RFC 8527 path /restconf/ds/ietf-datastores:candidate) with NETCONF commit/discard operations and vendor radio-bridge-tg YANG. Adopt RFC 8561 / ONF TR-532 models, YANG-Push telemetry, TLS 1.3 and NACM.\n" +
      "Full list with statuses: docs/STANDARDS_BY_INTERFACE.md."
    );
  }

  // ===================================================================
  // 11c. Standards matrix per interface
  // ===================================================================
  {
    const s = pres.addSlide();
    s.background = { color: WHITE };
    title(s, "Standards by interface", "What we use, what TFS offers, what to adopt");
    const TAG = {
      "IN USE": { fill: C_HW, text: WHITE, line: C_HW },
      "IN TFS": { fill: C_SDN, text: WHITE, line: C_SDN },
      ADOPT: { fill: NAVY, text: WHITE, line: NAVY },
      EMERGING: { fill: WHITE, text: C_SIM, line: C_SIM, dash: true },
      "DE FACTO": { fill: WHITE, text: MUTED, line: "9AA7B4" },
    };
    const cols = [
      ["①", "Agents → TFS", C_INTENT, [
        ["IN USE", "TFS REST NBI"], ["ADOPT", "TMF921 intent API"], ["ADOPT", "3GPP TS 28.312 intent"],
        ["IN TFS", "IETF L3NM · L2NM"], ["IN TFS", "IETF network slice NBI"], ["IN TFS", "CAMARA QoD"], ["DE FACTO", "MCP tools for agents"]]],
      ["②", "Agents → twin", C_SIM, [
        ["IN USE", "SSH + JSON · OpenAPI"], ["ADOPT", "TS 28.561 NDTJob"], ["ADOPT", "Y.3092 NDT-m"],
        ["ADOPT", "CAPIF TS 29.222"], ["ADOPT", "TS 28.105 · Y.3181"], ["DE FACTO", "Gymnasium · ns3-ai"], ["EMERGING", "Rel-20 NDT · Q.SDTN"]]],
      ["③", "TFS ↔ twin", C_SDN, [
        ["IN USE", "TFS REST polling"], ["IN TFS", "RFC 8345 topology"], ["ADOPT", "RFC 8561 microwave YANG"],
        ["ADOPT", "YANG-Push · gNMI"], ["IN TFS", "KPI · telemetry · Kafka"], ["ADOPT", "ITU-R P.838 · P.676 · P.530"], ["ADOPT", "Y.3092 NDT-p · Y.3093"]]],
      ["④", "TFS → radio", C_HW, [
        ["IN USE", "RESTCONF RFC 8040"], ["IN USE", "NMDA RFC 8527 · 8342"], ["IN USE", "YANG 1.1 · 802.1Q"],
        ["ADOPT", "RFC 8561 · ONF TR-532"], ["ADOPT", "YANG-Push telemetry"], ["ADOPT", "TLS 1.3 · NACM"], ["DE FACTO", "vendor radio-bridge-tg"]]],
    ];
    const cw = 2.175, gap = 0.1;
    for (let i = 0; i < cols.length; i++) {
      const [n, name, c, items] = cols[i];
      const x = 0.5 + i * (cw + gap), y = 1.3;
      card(s, pres, x, y, cw, 3.92);
      txt(s, [{ text: n + " ", options: { color: c } }, { text: name, options: { color: NAVY } }], { x: x + 0.12, y: y + 0.1, w: cw - 0.2, h: 0.32, fontFace: HEAD, fontSize: 12, bold: true, valign: "middle" });
      for (let j = 0; j < items.length; j++) {
        const yy = y + 0.55 + j * 0.47;
        const t = TAG[items[j][0]];
        s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: x + 0.1, y: yy, w: cw - 0.2, h: 0.4, fill: { color: WHITE }, line: { color: WHITE }, rectRadius: 0.05 });
        s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: x + 0.16, y: yy + 0.1, w: 0.62, h: 0.2, fill: { color: t.fill }, line: { color: t.line, width: 0.75, dashType: t.dash ? "dash" : "solid" }, rectRadius: 0.1 });
        txt(s, items[j][0], { x: x + 0.16, y: yy + 0.1, w: 0.62, h: 0.2, fontFace: HEAD, fontSize: 5.5, bold: true, color: t.text, align: "center", valign: "middle" });
        txt(s, items[j][1], { x: x + 0.84, y: yy, w: cw - 0.96, h: 0.4, fontSize: 8.5, valign: "middle" });
      }
    }
    s.addNotes(
      "Tags: IN USE = our code uses it today; IN TFS = TeraFlowSDN ships it but we do not use it yet; ADOPT = recommended for this interface; EMERGING = still being standardised; DE FACTO = open-source or vendor convention.\n" +
      "Notes: TS 28.312 is 3GPP's intent-driven management service; RFC 8527 defines the /restconf/ds/<datastore> paths our driver uses; calling NETCONF commit/discard through RESTCONF operations is a vendor mapping, not part of RFC 8040. MCP (Model Context Protocol) is a de facto way to expose TFS and twin operations as tools for LLM agents.\n" +
      "Details and rationale for every entry: docs/STANDARDS_BY_INTERFACE.md."
    );
  }

  // ===================================================================
  // 12. Target standards stack
  // ===================================================================
  {
    const s = pres.addSlide();
    s.background = { color: WHITE };
    title(s, "Target standards stack", "TFS ↔ ns-3: what exists today, what is coming");
    const cL = 0.5, cN = 2.6, wN = 3.85, cF = 6.6, wF = 2.9;
    txt(s, "AVAILABLE NOW", { x: cN, y: 1.3, w: wN, h: 0.22, fontSize: 9, bold: true, color: C_HW, charSpacing: 1.5 });
    txt(s, "EMERGING · 2026–28", { x: cF, y: 1.3, w: wF, h: 0.22, fontSize: 9, bold: true, color: C_SIM, charSpacing: 1.5 });
    function chip(x, y, w, t, now, star) {
      if (now) s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h: 0.36, fill: { color: star ? "DDF3E8" : TINT }, line: { color: star ? "DDF3E8" : TINT }, rectRadius: 0.06 });
      else s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h: 0.36, fill: { color: WHITE }, line: { color: C_SIM, width: 1, dashType: "dash" }, rectRadius: 0.06 });
      txt(s, (star ? "★ " : "") + t, { x: x + 0.1, y, w: w - 0.15, h: 0.36, fontSize: 9.5, color: star ? "157A50" : INK, bold: !!star, valign: "middle" });
    }
    const rows = [
      [fa.FaPlayCircle, NAVY2, "Job control", "start, steer, stop what-if runs",
        [["3GPP TS 28.561 NDTJob over TS 28.532 REST", 1], ["ITU-T Y.3092 NDT-m interface", 0]],
        ["3GPP Rel-20 NDT phase 2 (TR 28.883)", "ITU-T Q.SDTN twin signalling protocol"]],
      [fa.FaSatelliteDish, C_HW, "State sync", "live topology, RF state, KPIs",
        [["TFS NBI + KPI/telemetry components", 1], ["YANG-Push (RFC 8641) · gNMI · Y.3092 NDT-p", 0]],
        ["Rel-20 NDT data collection", "IRTF NMRG twin interface drafts"]],
      [fa.FaSitemap, C_SDN, "Shared models", "what the graph and data mean",
        [["IETF RFC 8345 topology (TFS ietf_network NBI)", 1], ["ITU-T Y.3093 data · Y.3094 model domain", 0]],
        ["Multi-twin collaboration (TR 28.883)", "O-RAN nGRG digital-twin research"]],
    ];
    for (let i = 0; i < rows.length; i++) {
      const [I, c, a, b, now, next] = rows[i];
      const y = 1.6 + i * 1.0;
      if (i > 0) s.addShape(pres.shapes.LINE, { x: cL, y: y - 0.09, w: 9.0, h: 0, line: { color: LINE, width: 0.75 } });
      await iconCircle(s, pres, I, cL, y + 0.17, 0.46, c);
      txt(s, a, { x: cL + 0.58, y: y + 0.13, w: 1.45, h: 0.27, fontFace: HEAD, fontSize: 11.5, bold: true });
      txt(s, b, { x: cL + 0.58, y: y + 0.4, w: 1.45, h: 0.4, fontSize: 9, color: MUTED });
      for (let j = 0; j < 2; j++) {
        chip(cN, y + j * 0.43, wN, now[j][0], true, now[j][1]);
        chip(cF, y + j * 0.43, wF, next[j], false, false);
      }
    }
    card(s, pres, 0.5, 4.62, 9.0, 0.6, NAVY);
    txt(s, [
      { text: "Frameworks: ", options: { bold: true, color: "8FA3B8" } },
      { text: "ITU-T Y.3090  ·  ETSI GR ZSM 015  ·  IRTF NMRG twin architecture", options: { color: WHITE } },
      { text: "      ★ = our recommended stack", options: { bold: true, color: "6FD3A4" } },
    ], { x: 0.7, y: 4.62, w: 8.7, h: 0.6, fontSize: 10.5, valign: "middle" });
    s.addNotes(
      "Where the TFS to ns-3 link should go. Job control: 3GPP TS 28.561 models each what-if as an NDTJob managed through TS 28.532 REST operations (ITU-T Y.3092 NDT-m). State sync: TFS already ships KPI manager, telemetry and Kafka components that are not yet deployed; YANG-Push (RFC 8641) or gNMI would feed them from the radios (Y.3092 NDT-p). Shared models: TFS's ietf_network NBI plugin exposes RFC 8345 topology, which the ns-3 generator could read instead of TFS's own JSON.\n" +
      "Emerging: 3GPP Release 20 NDT phase 2 (study TR 28.883), ITU-T Q.SDTN (SG11, under study, target around December 2026), Y.3093/Y.3094, IRTF NMRG drafts, O-RAN nGRG digital-twin research."
    );
  }

  // ===================================================================
  // 13. Gap register
  // ===================================================================
  {
    const s = pres.addSlide();
    s.background = { color: WHITE };
    title(s, "Gap register", "Top ten gaps, ranked by risk");
    const RISK = { High: RED, Med: C_SIM, Low: "9AA7B4" };
    const gaps = [
      ["High", "Fallback constants labelled as ns-3 results", "tsn_simulation_runner.py"],
      ["High", "Failed TFS write reported as success", "digital_twin_routes.py · web_dashboard.py"],
      ["High", "Intent keys don't match driver keys", "adapter.py ↔ CeragonDriver.py"],
      ["High", "Device state is canned, not read back", "ceragon/client.py"],
      ["High", "admin/admin, verify=False, creds in wire log", "descriptors · clients"],
      ["Med", "No telemetry subscription from radios", "CeragonDriver.SubscribeState"],
      ["Med", "Drift detected on synthetic data, never fixed", "assurance/reconciler.py"],
      ["Med", "Retune passes GHz as frequency_mhz", "tfs_digital_twin_api.py"],
      ["Med", "Core cer_intent package has no tests", "cer_intent/"],
      ["Low", "Duplicated modules, Windows paths, fixed host", "root · src/ · tfs_unity/"],
    ];
    const rh = 0.365, y0 = 1.3;
    txt(s, "RISK", { x: 0.6, y: y0, w: 0.8, h: 0.25, fontSize: 8.5, bold: true, color: MUTED, charSpacing: 1 });
    txt(s, "GAP", { x: 1.55, y: y0, w: 4.4, h: 0.25, fontSize: 8.5, bold: true, color: MUTED, charSpacing: 1 });
    txt(s, "WHERE", { x: 6.0, y: y0, w: 3.4, h: 0.25, fontSize: 8.5, bold: true, color: MUTED, charSpacing: 1 });
    for (let i = 0; i < gaps.length; i++) {
      const y = y0 + 0.3 + i * rh;
      if (i % 2 === 0) s.addShape(pres.shapes.RECTANGLE, { x: 0.5, y, w: 9.0, h: rh, fill: { color: TINT }, line: { color: TINT } });
      const c = RISK[gaps[i][0]];
      s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 0.6, y: y + 0.07, w: 0.65, h: 0.22, fill: { color: c }, line: { color: c }, rectRadius: 0.11 });
      txt(s, gaps[i][0].toUpperCase(), { x: 0.6, y: y + 0.07, w: 0.65, h: 0.22, fontFace: HEAD, fontSize: 7, bold: true, color: WHITE, align: "center", valign: "middle" });
      txt(s, `${i + 1}. ${gaps[i][1]}`, { x: 1.55, y, w: 4.4, h: rh, fontSize: 10, bold: i < 5, valign: "middle" });
      txt(s, gaps[i][2], { x: 6.0, y, w: 3.45, h: rh, fontFace: MONO, fontSize: 8, color: MUTED, valign: "middle" });
    }
    s.addNotes(
      "1. tsn_simulation_runner.py returns constants when SSH fails and labels them 'ns-3.45-discrete-event (Simulation Engine)'.\n" +
      "2. The run-loop POSTs to /tfs-api/device/{uuid}/config (not a TFS endpoint) and sets applied_to_tfs = True on exception (cer_intent/api/digital_twin_routes.py, web_dashboard.py). The TFS status check counts HTTP 404/500 as ONLINE.\n" +
      "3. CER-Intent sends /interface[name=...]/modulation {min,max}; the driver reads mrmc_script_id, tx_frequency, tx_power_dbm and /device/operating_parameters frequency_mhz, tx_power_dbm.\n" +
      "4. ceragon/client.py get_device_state() returns hard-coded MH-T261 values.\n" +
      "5. Descriptors and defaults use admin/admin over HTTP; requests use verify=False; the restconf-wire endpoint echoes credentials; CORS * and Flask debug on by default.\n" +
      "6. SubscribeState/UnsubscribeState return True.\n" +
      "7. telemetry_simulator.py is sinusoidal; reconciler never re-applies.\n" +
      "8. validate_and_close_loop passes target_ghz (64.8) as frequency_mhz and 2000 as channel_id.\n" +
      "9. No tests for cer_intent/ (only ceragon_tfs_adapter and the driver patch have tests).\n" +
      "10. Root and src/ copies (tsn_simulation_runner diverged), tfs_unity/ vendored copy, c:\\CER_Intent paths in several modules, ns-3 host hard-coded to efid@cersrv-029."
    );
  }

  // ===================================================================
  // 14. Roadmap
  // ===================================================================
  {
    const s = pres.addSlide();
    s.background = { color: WHITE };
    title(s, "Roadmap", "Three phases from demo to working twin");
    const phases = [
      [fa.FaBalanceScale, RED, "1  Make it truthful", "weeks", [
        "Label mock and fallback output", "Propagate TFS and driver errors", "One key contract: intent ↔ driver", "Live device read-back", "Secrets out of repos; TLS on", "Tests for cer_intent"],
        "Exit: every number on screen is real or labelled"],
      [fa.FaSyncAlt, C_SIM, "2  Make the loop real", "1–2 quarters", [
        "What-if as TS 28.561 NDTJob API", "Gates computed from ns-3 KPIs", "Telemetry: YANG-Push → TFS KPI/Kafka", "Post-commit verify + rollback", "Pluggable parsers: Gemini · Qwen · Claude", "Measure real loop time"],
        "Exit: one storm scenario closes the loop on hardware"],
      [fa.FaBrain, C_INTENT, "3  Standards & AI/ML", "2026–27", [
        "Expanded transport skill bank", "RFC 8345 topology into ns-3", "Y.3092 NDT-m / NDT-p split", "ns3-ai Gym env for RL agents", "TS 28.105 + Y.3181 model gating", "Track Rel-20 NDT, Q.SDTN"],
        "Exit: ML policies validated in the twin before deploy"],
    ];
    const cw = 2.9, gap = 0.15;
    for (let i = 0; i < phases.length; i++) {
      const [I, c, t, when, items, exit] = phases[i];
      const x = 0.5 + i * (cw + gap), y = 1.3;
      card(s, pres, x, y, cw, 3.95);
      await iconCircle(s, pres, I, x + 0.18, y + 0.16, 0.46, c);
      txt(s, t, { x: x + 0.76, y: y + 0.14, w: cw - 0.85, h: 0.28, fontFace: HEAD, fontSize: 12, bold: true, color: NAVY });
      txt(s, when, { x: x + 0.76, y: y + 0.42, w: cw - 0.85, h: 0.22, fontSize: 9, bold: true, color: c });
      for (let j = 0; j < items.length; j++) {
        const yy = y + 0.85 + j * 0.37;
        s.addShape(pres.shapes.OVAL, { x: x + 0.24, y: yy + 0.1, w: 0.1, h: 0.1, fill: { color: c }, line: { color: c } });
        txt(s, items[j], { x: x + 0.45, y: yy, w: cw - 0.55, h: 0.3, fontSize: 10, valign: "middle" });
      }
      s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: x + 0.15, y: y + 3.18, w: cw - 0.3, h: 0.6, fill: { color: WHITE }, line: { color: WHITE }, rectRadius: 0.06 });
      txt(s, exit, { x: x + 0.28, y: y + 3.18, w: cw - 0.5, h: 0.6, fontSize: 9.5, bold: true, color: c, valign: "middle" });
    }
    s.addNotes(
      "Phase 1 closes the high-risk gaps in the gap register so the demo shows only real or labelled data.\n" +
      "Phase 2 turns the what-if into a real job: expose ns-3 runs through a TS 28.561-style NDTJob API, compute the pre-flight gates from the simulated KPIs, stream radio telemetry into TFS's KPI/telemetry/Kafka components, verify after commit and roll back on regression. Add pluggable intent parsers next to Gemini: an on-prem Qwen model for air-gapped sites and Claude via the Anthropic API, selected by configuration with the regex parser as the last fallback. Then measure the true end-to-end loop time.\n" +
      "Phase 3: expand the architect's skill bank well beyond today's nine skills to cover transport knowledge (ACM and MRMC planning, rain and multipath fade margins, XPIC and space diversity, 1+1 HSB and ring protection, LAG and multi-band aggregation, QoS and slicing, synchronisation, energy saving, capacity planning). Feed the ns-3 generator from RFC 8345 topology, split twin interfaces per Y.3092, and wrap scenarios as ns3-ai Gymnasium environments so RL agents (for example the MARL-RIC MAPPO policy) train and are gated per TS 28.105 and Y.3181 before deployment."
    );
  }

  // ===================================================================
  // 15. Closing
  // ===================================================================
  {
    const s = pres.addSlide();
    s.background = { color: NAVY };
    txt(s, "SUMMARY", { x: 0.5, y: 0.3, w: 9, h: 0.25, fontFace: HEAD, fontSize: 10, bold: true, color: C_SDN, charSpacing: 2 });
    txt(s, "A real foundation, an honest gap list", { x: 0.5, y: 0.55, w: 9, h: 0.6, fontFace: HEAD, fontSize: 26, bold: true, color: WHITE, valign: "middle" });
    const tiles = [
      [`${fmt(intents)} · ${fmt(applyTotal)}`, "intents parsed · configs applied", C_INTENT],
      ["22 / 22", "twin tests passing", C_SIM],
      ["3 steps", "real RESTCONF stage → commit → discard", C_HW],
    ];
    for (let i = 0; i < tiles.length; i++) {
      const x = 0.5 + i * 3.05;
      s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y: 1.45, w: 2.85, h: 1.3, fill: { color: NAVY2 }, line: { color: NAVY2 }, rectRadius: 0.08 });
      txt(s, tiles[i][0], { x: x + 0.2, y: 1.55, w: 2.5, h: 0.65, fontFace: HEAD, fontSize: 26, bold: true, color: tiles[i][2], valign: "middle" });
      txt(s, tiles[i][1], { x: x + 0.2, y: 2.2, w: 2.5, h: 0.45, fontSize: 10.5, color: "C9D6E3" });
    }
    const next = [
      ["Next 4 weeks", "Phase 1: label mocks, fix error handling and key contract, live read-back, secrets."],
      ["Then", "Phase 2: NDTJob what-if, KPI-based gates, telemetry, verify and rollback."],
      ["Ask", "Lab time on cersrv-029 and the MH-T261 to measure the real loop."],
    ];
    for (let i = 0; i < next.length; i++) {
      const y = 3.1 + i * 0.62;
      txt(s, next[i][0], { x: 0.5, y, w: 1.8, h: 0.5, fontFace: HEAD, fontSize: 12, bold: true, color: C_SDN, valign: "middle" });
      txt(s, next[i][1], { x: 2.3, y, w: 7.2, h: 0.5, fontSize: 12, color: WHITE, valign: "middle" });
    }
    s.addNotes("Real today: the intent pipeline with Gemini and rule parsing, the TFS NBI integration, the ns-3.45 TSN scenario over SSH, the TFS to ns-3 generator and the Ceragon RESTCONF stage/commit/discard driver. The gap register lists what is mocked. The roadmap turns the demo into a working closed loop.");
  }

  const out = path.join(__dirname, "CER-Intent_Digital_Twin_As-Built.pptx");
  await pres.writeFile({ fileName: out });
  console.log("written", out);
})();
