#!/usr/bin/env python3
"""R4 Phase-1 ops-cutover pilot harness.

owlmlx-internal readiness probe + controlled-smoke evidence assembler for the
boundary-replacement campaign (runtime13 §5, R4). Phase 1 only: probes a running
owlmlx server for cutover readiness, then assembles one controlled non-default
OwlCoda agentic smoke into an honest pilot verdict.

This harness PROMOTES NOTHING. A `passed` verdict means "this one controlled
pilot session met its gates" — not "replacement complete", not a capability
promotion. The replacement verdict stays `not yet replaceable`.

Subcommands:
  probe-readiness    Probe $OWLMLX_PILOT_BASE_URL; emit readiness_passed OR
                     pilot_readiness_failed artifact (failure ALWAYS produces an
                     artifact).
  assemble-evidence  Combine operator-captured smoke artifacts into the §4
                     evidence schema + pilot verdict (passed / pilot_readiness_failed
                     / loop_failed).
"""

from __future__ import annotations

import argparse
import json
import os
import socket
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping, Sequence


DEFAULT_BASE_URL = "http://127.0.0.1:8066"
DEFAULT_EVIDENCE_DIR = (
    Path(__file__).resolve().parents[2]
    / "files"
    / "evidence"
    / "owlmlx"
    / "replacement"
    / "r4-ops-cutover"
)
EVIDENCE_SURFACE = "owlmlx.replacement.r4_ops_cutover_pilot"
EVIDENCE_VERSION = "v1"

# The tool lane is verified as 4 INDEPENDENT sub-gates (spec constraint #3).
TOOL_LANE_SUBGATES: tuple[str, ...] = (
    "tool_call_emitted",
    "tool_call_executed",
    "tool_result_roundtrip",
    "final_answer_after_tool",
)
# A watermark classification in this set means the per-session health gate tripped.
WATERMARK_RED_CLASSIFICATIONS: frozenset[str] = frozenset({"red", "fatal"})


def _now_compact_utc() -> str:
    return time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())


def _now_iso_utc() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def _append_jsonl(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(payload, sort_keys=True))
        stream.write("\n")


def _http_json(
    *,
    method: str,
    url: str,
    payload: dict[str, Any] | None = None,
    timeout_s: float,
) -> tuple[int, dict[str, Any]]:
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout_s) as response:
            raw = response.read().decode("utf-8")
            return int(response.status), json.loads(raw or "{}")
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8")
        try:
            body = json.loads(raw or "{}")
        except json.JSONDecodeError:
            body = {"raw": raw}
        return int(exc.code), body
    except (urllib.error.URLError, socket.timeout, TimeoutError) as exc:
        return 0, {"error": str(exc)}


@dataclass(frozen=True, slots=True)
class ReadinessCheck:
    name: str
    ok: bool
    detail: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ReadinessVerdict:
    verdict: str  # "readiness_passed" | "pilot_readiness_failed"
    ready: bool
    checks: tuple[ReadinessCheck, ...]
    failures: tuple[str, ...]


def _tool_calls_from_chat_body(body: Mapping[str, Any]) -> list[Any]:
    choices = body.get("choices") or []
    if not choices:
        return []
    message = choices[0].get("message") or {}
    return list(message.get("tool_calls") or [])


def evaluate_readiness(
    probes: Mapping[str, Any], *, model_id: str
) -> ReadinessVerdict:
    """Evaluate cutover readiness from probe responses (pure; no I/O).

    `probes` maps probe name -> {"status": int, "body": dict}. Readiness passes
    only when every check is ok. A failing input still returns a full verdict so
    the caller can persist a `pilot_readiness_failed` artifact (constraint #5).
    """

    def _entry(name: str) -> tuple[int, dict[str, Any]]:
        entry = probes.get(name) or {}
        return int(entry.get("status") or 0), dict(entry.get("body") or {})

    checks: list[ReadinessCheck] = []

    hz_status, hz_body = _entry("healthz")
    checks.append(
        ReadinessCheck(
            "healthz_ok",
            hz_status == 200 and bool(hz_body.get("ok")),
            {"status": hz_status, "readiness": hz_body.get("readiness")},
        )
    )

    mv_status, mv_body = _entry("model_visibility")
    visible = list(mv_body.get("visible_model_ids") or [])
    checks.append(
        ReadinessCheck(
            "model_visible",
            mv_status == 200 and model_id in visible,
            {"status": mv_status, "visible_model_ids": visible},
        )
    )

    om_status, om_body = _entry("openai_models")
    openai_ids = [str(m.get("id")) for m in (om_body.get("data") or [])]
    checks.append(
        ReadinessCheck(
            "model_in_openai_models",
            om_status == 200 and model_id in openai_ids,
            {"status": om_status, "ids": openai_ids},
        )
    )

    tl_status, tl_body = _entry("tool_lane")
    tool_calls = _tool_calls_from_chat_body(tl_body)
    checks.append(
        ReadinessCheck(
            "tool_lane_live",
            tl_status == 200 and len(tool_calls) > 0,
            {"status": tl_status, "tool_call_count": len(tool_calls)},
        )
    )

    mon_status, mon_body = _entry("monitor")
    classification = (
        (mon_body.get("resources") or {}).get("host_pressure") or {}
    ).get("classification")
    checks.append(
        ReadinessCheck(
            "monitor_reachable",
            mon_status == 200 and classification is not None,
            {"status": mon_status, "classification": classification},
        )
    )

    failures = tuple(c.name for c in checks if not c.ok)
    ready = not failures
    return ReadinessVerdict(
        verdict="readiness_passed" if ready else "pilot_readiness_failed",
        ready=ready,
        checks=tuple(checks),
        failures=failures,
    )


@dataclass(frozen=True, slots=True)
class ToolLaneVerdict:
    passed: bool
    subgates: dict[str, bool]
    failing: tuple[str, ...]


def evaluate_tool_lane(subgates: Mapping[str, bool]) -> ToolLaneVerdict:
    """Evaluate the 4 INDEPENDENT tool-lane sub-gates (constraint #3).

    Every sub-gate is normalized into the record (missing -> False), so the
    artifact always carries all four booleans. The lane passes only when all
    four are True.
    """
    normalized = {name: bool(subgates.get(name, False)) for name in TOOL_LANE_SUBGATES}
    failing = tuple(name for name in TOOL_LANE_SUBGATES if not normalized[name])
    return ToolLaneVerdict(
        passed=not failing,
        subgates=normalized,
        failing=failing,
    )


@dataclass(frozen=True, slots=True)
class FallbackProof:
    proven: bool
    config_ok: bool
    consumer_outbound_ok: bool
    owlmlx_inbound_ok: bool
    reasons: tuple[str, ...]


def _host_of(url: str) -> str:
    # "http://127.0.0.1:8066/v1/..." -> "127.0.0.1:8066"
    rest = url.split("://", 1)[-1]
    return rest.split("/", 1)[0]


def evaluate_fallback_proof(
    *,
    config_snapshot: Mapping[str, Any],
    consumer_outbound: Mapping[str, Any],
    owlmlx_inbound: Mapping[str, Any],
    pilot_request_ids: Sequence[str],
    pilot_base_url: str,
) -> FallbackProof:
    """Double-proof that the pilot used owlmlx with NO `:8009` fallback (#2).

    Leg (a) consumer config snapshot, (b) consumer outbound, (c) owlmlx inbound
    coverage. owlmlx never makes outbound `:8009` calls, so the no-`:8009` leg is
    consumer-side; owlmlx contributes inbound coverage as corroboration.
    """
    reasons: list[str] = []
    pilot_host = _host_of(pilot_base_url)

    # Leg (a): consumer config points at the pilot, fallback disabled, not :8009.
    cfg_base = str(config_snapshot.get("base_url") or "")
    cfg_host = _host_of(cfg_base)
    cfg_fallback_disabled = config_snapshot.get("fallback_enabled") is False
    config_ok = cfg_host == pilot_host and ":8009" not in cfg_base and cfg_fallback_disabled
    if cfg_host != pilot_host:
        reasons.append(f"config base_url host {cfg_host!r} != pilot host {pilot_host!r}")
    if ":8009" in cfg_base:
        reasons.append("config base_url still references :8009")
    if not cfg_fallback_disabled:
        reasons.append("config fallback_enabled is not False")

    # Leg (b): consumer outbound — no fallback, only the pilot host.
    fallback_count = int(consumer_outbound.get("fallback_count", -1))
    outbound_hosts = [str(h) for h in (consumer_outbound.get("outbound_hosts") or [])]
    hosts_ok = bool(outbound_hosts) and all(h == pilot_host for h in outbound_hosts)
    consumer_outbound_ok = fallback_count == 0 and hosts_ok
    if fallback_count != 0:
        reasons.append(f"consumer fallback_count={fallback_count} (expected 0)")
    if not hosts_ok:
        reasons.append(f"consumer outbound_hosts {outbound_hosts} not all == {pilot_host!r}")

    # Leg (c): owlmlx inbound coverage — every pilot request-id was served.
    served = set(str(r) for r in (owlmlx_inbound.get("served_request_ids") or []))
    pilot_ids = set(str(r) for r in pilot_request_ids)
    missing = sorted(pilot_ids - served)
    owlmlx_inbound_ok = bool(pilot_ids) and not missing
    if not pilot_ids:
        reasons.append("no pilot_request_ids supplied for inbound coverage")
    if missing:
        reasons.append(f"owlmlx inbound log missing request_ids: {missing}")

    proven = config_ok and consumer_outbound_ok and owlmlx_inbound_ok
    return FallbackProof(
        proven=proven,
        config_ok=config_ok,
        consumer_outbound_ok=consumer_outbound_ok,
        owlmlx_inbound_ok=owlmlx_inbound_ok,
        reasons=tuple(reasons),
    )


@dataclass(frozen=True, slots=True)
class WatermarkHealth:
    watermark_red_observed: bool
    classifications_seen: tuple[str, ...]
    interpretation: str


def evaluate_watermark_health(classifications: Sequence[str]) -> WatermarkHealth:
    """Per-session memory-watermark HEALTH gate (constraint #6).

    `watermark_red_observed=False` means "this session did not trigger RED" —
    it is explicitly NOT a sustained-stability conclusion (that is R4 Phase B).
    """
    seen = tuple(dict.fromkeys(str(c).lower() for c in classifications))
    red = any(c in WATERMARK_RED_CLASSIFICATIONS for c in seen)
    interpretation = (
        "RED/FATAL observed in this session — health gate tripped. "
        if red
        else "This session did not trigger RED. "
    ) + "Health gate for THIS pilot session only; NOT a sustained-stability claim (see R4 Phase B / soak)."
    return WatermarkHealth(
        watermark_red_observed=red,
        classifications_seen=seen,
        interpretation=interpretation,
    )


_HONESTY_NOTE = (
    "A `passed` verdict means this ONE controlled pilot session met its gates. "
    "It does NOT claim replacement complete, does NOT flip any default, and "
    "promotes NO capability. The replacement verdict stays `not yet replaceable`."
)


@dataclass(frozen=True, slots=True)
class PilotVerdict:
    verdict: str  # "passed" | "pilot_readiness_failed" | "loop_failed"
    reasons: tuple[str, ...]


def build_pilot_verdict(
    *,
    readiness: ReadinessVerdict,
    tool_lane: ToolLaneVerdict,
    fallback: FallbackProof,
    watermark: WatermarkHealth,
    loop_completed: bool,
) -> PilotVerdict:
    """Synthesize the single honest pilot verdict (precedence-ordered)."""
    if not readiness.ready:
        return PilotVerdict(
            "pilot_readiness_failed",
            tuple(f"readiness:{name}" for name in readiness.failures),
        )

    reasons: list[str] = []
    if not loop_completed:
        reasons.append("agentic loop did not complete (operator-reported)")
    if not tool_lane.passed:
        reasons.extend(f"tool_lane:{name}" for name in tool_lane.failing)
    if not fallback.proven:
        reasons.extend(f"fallback:{reason}" for reason in fallback.reasons)
    if watermark.watermark_red_observed:
        reasons.append("watermark health gate tripped (RED/FATAL this session)")

    if reasons:
        return PilotVerdict("loop_failed", tuple(reasons))
    return PilotVerdict("passed", ())


def _readiness_to_dict(verdict: ReadinessVerdict) -> dict[str, Any]:
    return {
        "verdict": verdict.verdict,
        "ready": verdict.ready,
        "failures": list(verdict.failures),
        "checks": [
            {"name": c.name, "ok": c.ok, "detail": c.detail} for c in verdict.checks
        ],
    }


def build_readiness_artifact(
    *,
    verdict: ReadinessVerdict,
    base_url: str,
    model_id: str,
    owlmlx_commit: str,
    recorded_at: str,
) -> dict[str, Any]:
    return {
        "surface": EVIDENCE_SURFACE,
        "version": EVIDENCE_VERSION,
        "kind": "readiness",
        "recorded_at": recorded_at,
        "verdict": verdict.verdict,
        "readiness": _readiness_to_dict(verdict),
        "reproduction": {
            "base_url": base_url,
            "model_id": model_id,
            "owlmlx_commit": owlmlx_commit,
        },
        "promotes": "nothing",
        "honesty_note": _HONESTY_NOTE,
    }


def build_pilot_artifact(
    *,
    pilot_verdict: PilotVerdict,
    readiness: ReadinessVerdict,
    tool_lane: ToolLaneVerdict,
    fallback: FallbackProof,
    watermark: WatermarkHealth,
    reproduction: Mapping[str, Any],
    recorded_at: str,
) -> dict[str, Any]:
    return {
        "surface": EVIDENCE_SURFACE,
        "version": EVIDENCE_VERSION,
        "kind": "pilot",
        "recorded_at": recorded_at,
        "verdict": pilot_verdict.verdict,
        "verdict_reasons": list(pilot_verdict.reasons),
        "readiness": _readiness_to_dict(readiness),
        "tool_lane": {
            "passed": tool_lane.passed,
            "subgates": dict(tool_lane.subgates),
            "failing": list(tool_lane.failing),
        },
        "fallback": {
            "fallback_used": not fallback.proven,
            "proven_not_used": fallback.proven,
            "config_ok": fallback.config_ok,
            "consumer_outbound_ok": fallback.consumer_outbound_ok,
            "owlmlx_inbound_ok": fallback.owlmlx_inbound_ok,
            "reasons": list(fallback.reasons),
        },
        "watermark": {
            "watermark_red_observed": watermark.watermark_red_observed,
            "classifications_seen": list(watermark.classifications_seen),
            "interpretation": watermark.interpretation,
        },
        "reproduction": dict(reproduction),
        "promotes": "nothing",
        "honesty_note": _HONESTY_NOTE,
    }


def _probe_live(base_url: str, *, model_id: str, timeout_s: float) -> dict[str, Any]:
    base = base_url.rstrip("/")

    hz_status, hz_body = _http_json(method="GET", url=f"{base}/healthz", timeout_s=timeout_s)
    mv_status, mv_body = _http_json(
        method="GET", url=f"{base}/v1/runtime/model-visibility", timeout_s=timeout_s
    )
    om_status, om_body = _http_json(
        method="GET", url=f"{base}/v1/openai/models", timeout_s=timeout_s
    )
    tl_status, tl_body = _http_json(
        method="POST",
        url=f"{base}/v1/chat/completions",
        payload={
            "model": model_id,
            "messages": [{"role": "user", "content": "What is the weather in Paris?"}],
            "tools": [
                {
                    "type": "function",
                    "function": {
                        "name": "get_weather",
                        "description": "Get the weather for a city.",
                        "parameters": {
                            "type": "object",
                            "properties": {"city": {"type": "string"}},
                            "required": ["city"],
                        },
                    },
                }
            ],
            "tool_choice": "required",
            "max_tokens": 64,
            "stream": False,
        },
        timeout_s=timeout_s,
    )
    mon_status, mon_body = _http_json(
        method="GET", url=f"{base}/v1/runtime/monitor/snapshot", timeout_s=timeout_s
    )
    return {
        "healthz": {"status": hz_status, "body": hz_body},
        "model_visibility": {"status": mv_status, "body": mv_body},
        "openai_models": {"status": om_status, "body": om_body},
        "tool_lane": {"status": tl_status, "body": tl_body},
        "monitor": {"status": mon_status, "body": mon_body},
    }


def run_probe_readiness(
    *,
    base_url: str,
    model_id: str,
    owlmlx_commit: str,
    evidence_dir: Path,
    timeout_s: float,
) -> dict[str, Any]:
    probes = _probe_live(base_url, model_id=model_id, timeout_s=timeout_s)
    verdict = evaluate_readiness(probes, model_id=model_id)
    recorded_at = _now_iso_utc()
    artifact = build_readiness_artifact(
        verdict=verdict,
        base_url=base_url,
        model_id=model_id,
        owlmlx_commit=owlmlx_commit,
        recorded_at=recorded_at,
    )
    artifact["probes"] = probes  # raw probe payloads for audit
    safe_model = model_id.strip("/").replace("/", "-")
    filename = f"{_now_compact_utc()}-readiness-{verdict.verdict}-{safe_model}.json"
    _write_json(evidence_dir / filename, artifact)
    return {
        "verdict": verdict.verdict,
        "ready": verdict.ready,
        "failures": list(verdict.failures),
        "artifact_filename": filename,
        "artifact_path": str(evidence_dir / filename),
    }


def _rebuild_readiness_from_artifact(artifact: Mapping[str, Any]) -> ReadinessVerdict:
    payload = artifact.get("readiness") or {}
    checks = tuple(
        ReadinessCheck(c["name"], bool(c["ok"]), dict(c.get("detail") or {}))
        for c in (payload.get("checks") or [])
    )
    return ReadinessVerdict(
        verdict=str(artifact.get("verdict") or payload.get("verdict")),
        ready=bool(payload.get("ready")),
        checks=checks,
        failures=tuple(payload.get("failures") or []),
    )


def run_assemble_evidence(
    *,
    capture_path: Path,
    readiness_artifact_path: Path,
    pilot_base_url: str,
    evidence_dir: Path,
) -> dict[str, Any]:
    capture = json.loads(Path(capture_path).read_text(encoding="utf-8"))
    readiness_artifact = json.loads(
        Path(readiness_artifact_path).read_text(encoding="utf-8")
    )
    readiness = _rebuild_readiness_from_artifact(readiness_artifact)

    tool_lane = evaluate_tool_lane(capture.get("tool_lane_subgates") or {})
    fb = capture.get("fallback") or {}
    reproduction = capture.get("reproduction") or {}
    fallback = evaluate_fallback_proof(
        config_snapshot=fb.get("config_snapshot") or {},
        consumer_outbound=fb.get("consumer_outbound") or {},
        owlmlx_inbound=fb.get("owlmlx_inbound") or {},
        pilot_request_ids=reproduction.get("request_ids") or [],
        pilot_base_url=pilot_base_url,
    )
    watermark = evaluate_watermark_health(capture.get("watermark_classifications") or [])
    pilot_verdict = build_pilot_verdict(
        readiness=readiness,
        tool_lane=tool_lane,
        fallback=fallback,
        watermark=watermark,
        loop_completed=bool(capture.get("loop_completed")),
    )
    recorded_at = _now_iso_utc()
    artifact = build_pilot_artifact(
        pilot_verdict=pilot_verdict,
        readiness=readiness,
        tool_lane=tool_lane,
        fallback=fallback,
        watermark=watermark,
        reproduction=reproduction,
        recorded_at=recorded_at,
    )
    session_id = str(reproduction.get("session_id") or "session")
    filename = f"{_now_compact_utc()}-pilot-{pilot_verdict.verdict}-{session_id}.json"
    _write_json(evidence_dir / filename, artifact)
    _append_jsonl(
        evidence_dir / "pilot-ledger.jsonl",
        {
            "recorded_at": recorded_at,
            "verdict": pilot_verdict.verdict,
            "session_id": session_id,
            "artifact": filename,
        },
    )
    return {
        "verdict": pilot_verdict.verdict,
        "reasons": list(pilot_verdict.reasons),
        "artifact_filename": filename,
        "artifact_path": str(evidence_dir / filename),
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="R4 Phase-1 ops-cutover pilot harness (owlmlx-internal)."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    probe = sub.add_parser(
        "probe-readiness",
        help="Probe a running owlmlx server; emit readiness_passed OR pilot_readiness_failed.",
    )
    probe.add_argument(
        "--base-url",
        default=os.environ.get("OWLMLX_PILOT_BASE_URL", DEFAULT_BASE_URL),
        help="owlmlx base URL (default $OWLMLX_PILOT_BASE_URL or %(default)s; port is NOT a contract).",
    )
    probe.add_argument(
        "--model-id",
        default=os.environ.get("OWLMLX_PILOT_MODEL_ID"),
        required=os.environ.get("OWLMLX_PILOT_MODEL_ID") is None,
        help="Pilot model id (default $OWLMLX_PILOT_MODEL_ID).",
    )
    probe.add_argument("--owlmlx-commit", required=True, help="owlmlx git commit under test.")
    probe.add_argument("--evidence-dir", type=Path, default=DEFAULT_EVIDENCE_DIR)
    probe.add_argument("--timeout-s", type=float, default=60.0)

    assemble = sub.add_parser(
        "assemble-evidence",
        help="Assemble controlled-smoke captures into a pilot verdict artifact.",
    )
    assemble.add_argument("--capture", type=Path, required=True,
                          help="Operator-captured smoke JSON (see runbook).")
    assemble.add_argument("--readiness-artifact", type=Path, required=True,
                          help="The readiness artifact emitted by probe-readiness.")
    assemble.add_argument(
        "--base-url",
        default=os.environ.get("OWLMLX_PILOT_BASE_URL", DEFAULT_BASE_URL),
    )
    assemble.add_argument("--evidence-dir", type=Path, default=DEFAULT_EVIDENCE_DIR)

    args = parser.parse_args(argv)

    if args.command == "probe-readiness":
        result = run_probe_readiness(
            base_url=args.base_url,
            model_id=args.model_id,
            owlmlx_commit=args.owlmlx_commit,
            evidence_dir=args.evidence_dir,
            timeout_s=args.timeout_s,
        )
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0 if result["ready"] else 1

    if args.command == "assemble-evidence":
        result = run_assemble_evidence(
            capture_path=args.capture,
            readiness_artifact_path=args.readiness_artifact,
            pilot_base_url=args.base_url,
            evidence_dir=args.evidence_dir,
        )
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0 if result["verdict"] == "passed" else 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
