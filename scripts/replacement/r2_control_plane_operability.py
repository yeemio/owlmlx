"""R2 control-plane operability rehearsal (mutates runtime state).

Drives the control-plane lifecycle (load -> switch -> evict -> restart) via the
EXISTING owlmlx endpoints and asserts each transition is correctly reported, plus
watermark coherence. Pure-function step evaluators are unit-tested; the live
`rehearse` run MUST target an isolated bench server (never :8066) and is
cost-flagged. Promotes nothing; one controlled run != sustained stability.
"""
from __future__ import annotations

PASS = "pass"
FAIL = "fail"

_WATERMARK_OK = {"GREEN", "YELLOW", "RED", "FATAL"}


def _active(status):
    return (status or {}).get("summary", {}).get("active_model_id")


def _readiness(status):
    return (status or {}).get("summary", {}).get("readiness")


def evaluate_load_step(model_id, healthz, status):
    reasons = []
    if healthz.get("active_model_id") != model_id:
        reasons.append("healthz.active_model_id != %s" % model_id)
    if healthz.get("readiness") != "ready":
        reasons.append("healthz.readiness != ready")
    if _active(status) != model_id:
        reasons.append("status.summary.active_model_id != %s" % model_id)
    return {"step": "load", "model_id": model_id, "status": PASS if not reasons else FAIL, "reasons": reasons}


def evaluate_switch_step(model_id, status):
    reasons = [] if _active(status) == model_id else ["status.summary.active_model_id != %s" % model_id]
    return {"step": "model_switch", "model_id": model_id, "status": PASS if not reasons else FAIL, "reasons": reasons}


def evaluate_evict_step(expected_victim, evict_response, status):
    reasons = []
    if evict_response.get("selected_victim") != expected_victim:
        reasons.append("selected_victim != %s" % expected_victim)
    if _active(status) == expected_victim:
        reasons.append("evicted model still active")
    return {"step": "evict", "expected_victim": expected_victim,
            "status": PASS if not reasons else FAIL, "reasons": reasons}


def evaluate_restart_step(recovery_contract, status):
    reasons = []
    if not isinstance(recovery_contract, dict) or not recovery_contract:
        reasons.append("recovery-supervisor-contract empty")
    if _readiness(status) not in ("ready", "loading"):
        reasons.append("post-restart readiness not ready/loading")
    return {"step": "restart", "status": PASS if not reasons else FAIL, "reasons": reasons}


def evaluate_watermark_step(watermark):
    level = (watermark or {}).get("level")
    reasons = [] if level in _WATERMARK_OK else ["watermark level %r not in known set" % level]
    return {"step": "watermark", "level": level, "status": PASS if not reasons else FAIL, "reasons": reasons}


def aggregate_lifecycle(steps):
    failed = [s for s in steps if s.get("status") == FAIL]
    return {
        "round": "R2",
        "tier": "control-plane-operability-rehearsal",
        "verdict": "rehearsal_failed" if failed else "passed",
        "failed_count": len(failed),
        "steps": steps,
    }


import argparse
import json
import os
import sys
import urllib.request


def _http(base_url, method, path, body=None, timeout=120):
    url = base_url.rstrip("/") + path
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(url, data=data, method=method,
                                 headers={"content-type": "application/json", "accept": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310 (local trusted URL)
        raw = resp.read().decode("utf-8")
        return resp.status, (json.loads(raw) if raw else {})


def rehearse(base_url, model_a, model_b, *, victim=None):
    """Drive load -> switch -> evict -> restart and sample watermark each phase."""
    steps = []
    _http(base_url, "POST", "/v1/load", {"model_id": model_a})
    _, hz = _http(base_url, "GET", "/healthz")
    _, st = _http(base_url, "GET", "/v1/runtime/status")
    steps.append(evaluate_load_step(model_a, hz, st))
    steps.append(evaluate_watermark_step(_http(base_url, "GET", "/v1/runtime/memory-watermark")[1]))

    _http(base_url, "POST", "/v1/load", {"model_id": model_b})
    _, st = _http(base_url, "GET", "/v1/runtime/status")
    steps.append(evaluate_switch_step(model_b, st))

    evict_victim = victim or model_a
    _, ev = _http(base_url, "POST", "/v1/runtime/memory-pressure-eviction", {"protect_active": True})
    _, st = _http(base_url, "GET", "/v1/runtime/status")
    steps.append(evaluate_evict_step(evict_victim, ev, st))

    _http(base_url, "POST", "/v1/runtime/restart", {})
    _, rec = _http(base_url, "GET", "/v1/runtime/recovery-supervisor-contract")
    _, st = _http(base_url, "GET", "/v1/runtime/status")
    steps.append(evaluate_restart_step(rec, st))
    steps.append(evaluate_watermark_step(_http(base_url, "GET", "/v1/runtime/memory-watermark")[1]))

    return aggregate_lifecycle(steps)


def main(argv=None):
    parser = argparse.ArgumentParser(description="R2 control-plane operability rehearsal (bench only — mutates state)")
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("rehearse", help="drive control-plane lifecycle on an ISOLATED bench server")
    p.add_argument("--base-url", required=True)
    p.add_argument("--model-a", required=True)
    p.add_argument("--model-b", required=True)
    p.add_argument("--victim", default=None)
    p.add_argument("--out", default=None)
    p.add_argument("--i-understand-bench-only", action="store_true",
                   help="required ack: this mutates runtime state; never run against :8066")
    args = parser.parse_args(argv)

    if args.cmd == "rehearse":
        if not args.i_understand_bench_only:
            print("REFUSED: rehearse mutates runtime state. Pass --i-understand-bench-only "
                  "and target an isolated bench server (never :8066).", file=sys.stderr)
            return 3
        if ":8066" in args.base_url:
            print("REFUSED: --base-url points at :8066 (the default daemon). Use an isolated bench.",
                  file=sys.stderr)
            return 3
        result = rehearse(args.base_url, args.model_a, args.model_b, victim=args.victim)
        result["base_url"] = args.base_url
        text = json.dumps(result, indent=2, ensure_ascii=False)
        if args.out:
            os.makedirs(os.path.dirname(args.out), exist_ok=True)
            with open(args.out, "w", encoding="utf-8") as fh:
                fh.write(text + "\n")
        print(text)
        return 0 if result["verdict"] == "passed" else 2
    return 1


if __name__ == "__main__":
    sys.exit(main())
