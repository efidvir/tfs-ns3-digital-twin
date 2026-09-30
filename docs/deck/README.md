# As-built deck

`CER-Intent_Digital_Twin_As-Built.pptx` documents the digital twin as it is built today:
CER-Intent, TeraFlowSDN, ns-3 and the Ceragon MH-T261. Each capability is marked
IMPLEMENTED, PARTIAL, MOCK or PLANNED, and the speaker notes cite the source file for each claim.

Rebuild:

```bash
python audit_stats.py <path-to-cer-intent>/data/audit_log.jsonl audit_stats.json
npm install pptxgenjs react react-dom react-icons sharp
node build_deck.js
```
