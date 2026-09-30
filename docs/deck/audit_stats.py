"""Summarise the CER-Intent audit log for the as-built deck.

Usage: python audit_stats.py <path/to/cer-intent/data/audit_log.jsonl> [out.json]
Every number on the deck's operating-data slide comes from this script.
"""
import collections
import json
import statistics
import sys
from datetime import datetime


def ts(e):
    return datetime.fromisoformat(e["timestamp"])


def main(path, out):
    events = [json.loads(l) for l in open(path, encoding="utf-8") if l.strip()]
    by_type = collections.Counter(e["event_type"] for e in events)

    applies = [e for e in events if e["event_type"] == "CONFIG_APPLIED"]
    by_backend = collections.defaultdict(lambda: {"ok": 0, "failed": 0})
    for e in applies:
        by_backend[e.get("backend", "unknown")]["ok" if e.get("success") else "failed"] += 1
    fail_msgs = collections.Counter(e.get("message", "")[:80] for e in applies if not e.get("success"))
    config_types = collections.Counter(e.get("config_type", "unknown") for e in applies)
    devices = collections.Counter(e.get("device_id", "unknown") for e in applies)

    # parse -> last apply per intent
    parsed = {e["intent_id"]: ts(e) for e in events if e["event_type"] == "INTENT_PARSED"}
    last_apply = {}
    for e in applies:
        iid = e.get("intent_id")
        if iid in parsed:
            last_apply[iid] = max(last_apply.get(iid, ts(e)), ts(e))
    spans_ms = sorted((last_apply[i] - parsed[i]).total_seconds() * 1000 for i in last_apply)

    months = collections.Counter(ts(e).strftime("%Y-%m") for e in events if e["event_type"] == "INTENT_PARSED")
    strategies = collections.Counter(
        e["message"].split(": ", 1)[1] for e in events
        if e["event_type"] == "SYSTEM_EVENT" and e.get("message", "").startswith("Architect plan created: "))
    sources = collections.Counter(
        e["message"].rsplit(" ", 1)[-1] for e in events
        if e["event_type"] == "SYSTEM_EVENT" and e.get("message", "").startswith("Intent received from "))
    previews = [e.get("input_preview", "") for e in events if e["event_type"] == "INTENT_PARSED"]

    result = {
        "source": path,
        "events_total": len(events),
        "first": min(ts(e) for e in events).isoformat(),
        "last": max(ts(e) for e in events).isoformat(),
        "by_type": dict(by_type),
        "applies_by_backend": dict(by_backend),
        "apply_failure_messages": dict(fail_msgs.most_common(5)),
        "applies_by_config_type": dict(config_types.most_common()),
        "distinct_devices": len(devices),
        "top_devices": dict(devices.most_common(8)),
        "intents_parsed_by_month": dict(sorted(months.items())),
        "parse_to_last_apply_ms": {
            "n": len(spans_ms),
            "median": statistics.median(spans_ms) if spans_ms else None,
            "p90": spans_ms[int(0.9 * (len(spans_ms) - 1))] if spans_ms else None,
            "max": spans_ms[-1] if spans_ms else None,
            "under_100ms": sum(s < 100 for s in spans_ms),
            "under_1s": sum(s < 1000 for s in spans_ms),
        },
        "architect_strategies": dict(strategies.most_common()),
        "intent_sources": dict(sources),
        "intent_previews": previews,
    }
    json.dump(result, open(out, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    return result


if __name__ == "__main__":
    r = main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "audit_stats.json")
    print(json.dumps({k: v for k, v in r.items() if k != "intent_previews"}, indent=2, ensure_ascii=False))
