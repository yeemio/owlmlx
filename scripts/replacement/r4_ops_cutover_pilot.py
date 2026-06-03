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


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="R4 Phase-1 ops-cutover pilot harness (owlmlx-internal)."
    )
    parser.add_subparsers(dest="command", required=True)
    parser.parse_args(argv)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
