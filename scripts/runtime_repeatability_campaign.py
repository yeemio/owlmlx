"""Repeatability campaign runner for host-stable Model RC evidence.

Loads a model once, runs N generations, collects per-repeat timing and RSS,
computes RepeatabilityStatistics, and appends a Model RC ledger record with
variance fields. Designed for Campaign 1: Host-Stable Repeatability.

Usage:
    uv run python scripts/runtime_repeatability_campaign.py run \\
        --model-id Qwen3.6-27B \\
        --artifact-path /path/to/weights \\
        --repeat-count 20 \\
        --prompt "What is 2+2?" \\
        --ledger-path files/evidence/owlmlx/model-release-candidates/cumulative-ledger.jsonl

Hard rules (see coordinator-checkpoint-internal-replacement-grade-runtime-depth.md):
- N < 5: campaign_label=smoke
- 5 <= N < 20: campaign_label=repeatability_candidate
- N >= 20: campaign_label=repeatability_evidence (only this counts as evidence)
- Dirty post-run health: immediate blocker, no stability claim
- prefill_ms captured per repeat from first token event on /v1/generate/stream
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from owlmlx.model_release_candidate_ledger import ModelReleaseCandidateLedger
from owlmlx.model_release_candidate_record import build_model_release_candidate_record
from owlmlx.repeatability_statistics import (
    RepeatRunSample,
    compute_repeatability_statistics,
    repeatability_statistics_to_dict,
)


# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------

def _http_json(
    method: str,
    url: str,
    payload: dict[str, Any] | None = None,
    timeout_s: float = 120.0,
) -> tuple[int, Any]:
    data = json.dumps(payload).encode() if payload is not None else None
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout_s) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as exc:
        try:
            body = json.loads(exc.read())
        except Exception:
            body = {"detail": str(exc)}
        return exc.code, body
    except Exception as exc:
        return 0, {"detail": str(exc)}


def _http_ndjson_stream(
    url: str,
    payload: dict[str, Any],
    timeout_s: float = 180.0,
) -> list[dict[str, Any]]:
    """POST to an NDJSON streaming endpoint; return all parsed event dicts."""
    data = json.dumps(payload).encode()
    headers = {"Content-Type": "application/json"}
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    events: list[dict[str, Any]] = []
    try:
        with urllib.request.urlopen(req, timeout=timeout_s) as resp:
            for raw_line in resp:
                line = raw_line.strip()
                if not line:
                    continue
                try:
                    events.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    except Exception as exc:
        events.append({"event": "error", "detail": {"message": str(exc)}})
    return events


def _now_iso_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _rounded_ms(v: float | None) -> float | None:
    return round(v, 3) if v is not None else None


# ---------------------------------------------------------------------------
# Per-repeat stream parsing
# ---------------------------------------------------------------------------

def _parse_stream_events(
    events: list[dict[str, Any]],
) -> dict[str, Any]:
    """Extract timing and content from a /v1/generate/stream NDJSON event list."""
    text_parts: list[str] = []
    first_token_ms: float | None = None
    prefill_ms: float | None = None
    completion_tokens = 0
    finish_reason: str | None = None
    queue_wait_ms: float | None = None
    stream_start_wall: float | None = None
    stream_end_wall: float | None = None
    error_detail: str | None = None

    stream_start_wall = time.monotonic()
    for event in events:
        evt = event.get("event", "")
        if evt == "token":
            if first_token_ms is None:
                first_token_ms = (time.monotonic() - stream_start_wall) * 1000.0
            if event.get("prefill_ms") is not None and prefill_ms is None:
                prefill_ms = float(event["prefill_ms"])
            if event.get("wait_time_s") is not None and queue_wait_ms is None:
                queue_wait_ms = float(event["wait_time_s"]) * 1000.0
            ct = event.get("completion_tokens")
            if ct is not None:
                completion_tokens = int(ct)
            text_parts.append(event.get("text", ""))
        elif evt == "done":
            stream_end_wall = time.monotonic()
            finish_reason = event.get("finish_reason")

        elif evt == "error":
            detail = event.get("detail", {})
            error_detail = detail.get("message", "unknown error") if isinstance(detail, dict) else str(detail)

    wall_ms = (
        (stream_end_wall - stream_start_wall) * 1000.0
        if stream_end_wall is not None
        else None
    )
    decode_tokens = max(completion_tokens - 1, 0)
    decode_wall_ms = (
        max(wall_ms - (first_token_ms or 0.0), 0.0)
        if wall_ms is not None and first_token_ms is not None
        else None
    )
    decode_tps = (
        decode_tokens / (decode_wall_ms / 1000.0)
        if decode_tokens > 0 and decode_wall_ms and decode_wall_ms > 0
        else None
    )

    return {
        "text": "".join(text_parts),
        "first_token_ms": _rounded_ms(first_token_ms),
        "prefill_ms": _rounded_ms(prefill_ms),
        "wall_ms": _rounded_ms(wall_ms),
        "decode_tps": _rounded_ms(decode_tps),
        "queue_wait_ms": _rounded_ms(queue_wait_ms),
        "completion_tokens": completion_tokens,
        "finish_reason": finish_reason,
        "error": error_detail,
    }


# ---------------------------------------------------------------------------
# Campaign label
# ---------------------------------------------------------------------------

def _campaign_label(n: int) -> str:
    if n < 5:
        return "smoke"
    if n < 20:
        return "repeatability_candidate"
    return "repeatability_evidence"


# ---------------------------------------------------------------------------
# Post-run health check
# ---------------------------------------------------------------------------

def _check_health(server_url: str, timeout_s: float = 30.0) -> dict[str, Any]:
    status, payload = _http_json("GET", f"{server_url}/healthz", timeout_s=timeout_s)
    return {"status_code": status, "payload": payload}


def _health_is_clean(health: dict[str, Any]) -> bool:
    if health["status_code"] != 200:
        return False
    payload = health["payload"]
    return (
        payload.get("ok") is True
        and payload.get("active_model_id") is None
    )


# ---------------------------------------------------------------------------
# Campaign run function (pure-ish, exposed for testing)
# ---------------------------------------------------------------------------

def run_campaign(
    *,
    server_url: str,
    model_id: str,
    artifact_path: str,
    repeat_count: int,
    prompt: str,
    max_tokens: int = 64,
    temperature: float = 0.0,
    memory_gb: float | None = None,
    host_class: str = "Mac17,6-arm64-macOS-26.4.1-128GB",
    http_timeout_s: float = 180.0,
) -> dict[str, Any]:
    """Run N generations and return a result dict ready for ledger writing.

    Returns a dict with:
      - ``record_kwargs``: kwargs for ``build_model_release_candidate_record``
      - ``repeatability_stats_dict``: serialized RepeatabilityStatistics
      - ``campaign_label``: smoke / repeatability_candidate / repeatability_evidence
      - ``error``: str | None
    """
    campaign_label = _campaign_label(repeat_count)
    samples: list[RepeatRunSample] = []
    per_repeat_results: list[dict[str, Any]] = []
    failure_count = 0
    blockers: list[str] = []

    # Pre-flight: server health
    pre_health = _check_health(server_url, timeout_s=http_timeout_s)
    if pre_health["status_code"] != 200:
        return {
            "record_kwargs": None,
            "repeatability_stats_dict": None,
            "campaign_label": campaign_label,
            "error": f"pre-flight health check failed: {pre_health}",
        }

    # Load
    load_payload: dict[str, Any] = {"model_id": model_id}
    if memory_gb is not None:
        load_payload["memory_gb"] = memory_gb
    if artifact_path:
        load_payload["artifact_path"] = artifact_path
    load_status, load_resp = _http_json(
        "POST", f"{server_url}/v1/load", load_payload, timeout_s=http_timeout_s
    )
    load_result = {
        "status": "pass" if load_status == 200 else "fail",
        "detail": load_resp.get("detail", "") if isinstance(load_resp, dict) else str(load_resp),
    }
    if load_status != 200:
        blockers.append("load_failed")
        return {
            "record_kwargs": None,
            "repeatability_stats_dict": None,
            "campaign_label": campaign_label,
            "error": f"load failed: {load_status} {load_resp}",
        }

    # N generations
    repeat_started = _now_iso_utc()
    for index in range(1, repeat_count + 1):
        gen_payload = {
            "model_id": model_id,
            "prompt": prompt,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        events = _http_ndjson_stream(
            f"{server_url}/v1/generate/stream",
            gen_payload,
            timeout_s=http_timeout_s,
        )
        parsed = _parse_stream_events(events)
        parsed["repeat_index"] = index
        per_repeat_results.append(parsed)

        if parsed["error"]:
            failure_count += 1
            blockers.append("generation_error")
        else:
            rss_health = _check_health(server_url, timeout_s=30.0)
            rss_bytes = rss_health["payload"].get("rss_bytes") if rss_health["status_code"] == 200 else None
            samples.append(
                RepeatRunSample(
                    ttft_ms=parsed["first_token_ms"],
                    decode_tps=parsed["decode_tps"],
                    wall_ms=parsed["wall_ms"],
                    rss_bytes=int(rss_bytes) if rss_bytes is not None else None,
                )
            )

    # Unload
    unload_status, unload_resp = _http_json(
        "POST",
        f"{server_url}/v1/unload",
        {"model_id": model_id},
        timeout_s=http_timeout_s,
    )
    unload_result = {
        "status": "pass" if unload_status == 200 else "fail",
        "detail": unload_resp.get("detail", "") if isinstance(unload_resp, dict) else str(unload_resp),
    }
    if unload_status != 200:
        blockers.append("unload_failed")

    # Post-run health
    post_health = _check_health(server_url, timeout_s=http_timeout_s)
    post_health_clean = _health_is_clean(post_health)
    if not post_health_clean:
        blockers.append("post_run_health_dirty")

    # Variance statistics
    stats = compute_repeatability_statistics(samples)
    stats_dict = repeatability_statistics_to_dict(stats)

    # Aggregate timing (mean of successful repeats)
    successful = [r for r in per_repeat_results if not r["error"]]
    mean_ttft = (
        sum(r["first_token_ms"] for r in successful if r["first_token_ms"] is not None)
        / len([r for r in successful if r["first_token_ms"] is not None])
        if any(r["first_token_ms"] is not None for r in successful)
        else None
    )
    mean_prefill = (
        sum(r["prefill_ms"] for r in successful if r["prefill_ms"] is not None)
        / len([r for r in successful if r["prefill_ms"] is not None])
        if any(r["prefill_ms"] is not None for r in successful)
        else None
    )
    total_tokens = sum(r["completion_tokens"] for r in successful)
    total_wall_s = sum((r["wall_ms"] or 0.0) / 1000.0 for r in successful)
    tps = total_tokens / total_wall_s if total_tokens > 0 and total_wall_s > 0 else None

    # Output sanity: check final generated text
    last_text = successful[-1]["text"] if successful else ""
    output_sanity_label = "ok" if last_text.strip() else "empty_output"

    # Verdict
    verdict: str
    if failure_count > 0 or not post_health_clean:
        verdict = "blocked"
        blockers.append("live_repeated_run_incomplete")
    elif stats.stability_label == "insufficient_samples":
        verdict = "needs_optimization"
        blockers.append("insufficient_samples_for_stability_claim")
    elif stats.stability_label == "unstable":
        verdict = "needs_optimization"
        blockers.append("high_variance_unstable")
    else:
        verdict = "needs_optimization"

    blockers = list(dict.fromkeys(blockers))

    record_kwargs: dict[str, Any] = dict(
        created_at=_now_iso_utc(),
        model_id=model_id,
        lane="mainline",
        runtime_url=server_url,
        host_class=host_class,
        artifact_path=artifact_path,
        visibility_status="visible",
        load_result=load_result,
        generation_result={
            "status": "pass" if successful else "fail",
            "detail": f"{len(successful)}/{repeat_count} repeats succeeded",
        },
        unload_result=unload_result,
        reload_result={"status": "not_run", "detail": "single-load campaign"},
        repeat_count=len(successful),
        failure_count=failure_count,
        first_token_latency_ms=_rounded_ms(mean_ttft),
        tokens_per_second=_rounded_ms(tps),
        wall_clock_ms=_rounded_ms(total_wall_s * 1000.0),
        peak_resident_set_bytes=stats.rss_bytes_max,
        memory_headroom_bytes=None,
        output_sanity_label=output_sanity_label,
        owlops_observation_path="files/evidence/owlmlx/model-release-candidates/repeatability-campaign",
        verdict=verdict,
        blockers=tuple(blockers),
        ttft_ms=_rounded_ms(mean_ttft),
        runtime_prefill_phase_ms=_rounded_ms(mean_prefill),
        repeatability_n=len(samples),
        repeatability_ttft_ms_stddev=_rounded_ms(stats.ttft_ms_stddev),
        repeatability_decode_tps_stddev=_rounded_ms(stats.decode_tps_stddev),
        repeatability_rss_bytes_max=stats.rss_bytes_max,
        repeatability_stability_label=stats.stability_label,
    )

    return {
        "record_kwargs": record_kwargs,
        "repeatability_stats_dict": stats_dict,
        "campaign_label": campaign_label,
        "per_repeat_results": per_repeat_results,
        "post_health_clean": post_health_clean,
        "error": None,
    }


# ---------------------------------------------------------------------------
# Ledger write
# ---------------------------------------------------------------------------

def write_to_ledger(record_kwargs: dict[str, Any], ledger_path: str) -> None:
    record = build_model_release_candidate_record(**record_kwargs)
    ModelReleaseCandidateLedger(ledger_path).append(record)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _cmd_run(args: argparse.Namespace) -> int:
    print(
        f"[repeatability-campaign] model={args.model_id} "
        f"N={args.repeat_count} url={args.server_url}"
    )
    label = _campaign_label(args.repeat_count)
    if args.repeat_count < 20:
        print(
            f"[repeatability-campaign] WARNING: N={args.repeat_count} < 20; "
            f"campaign_label='{label}' (not repeatability_evidence)"
        )

    result = run_campaign(
        server_url=args.server_url,
        model_id=args.model_id,
        artifact_path=args.artifact_path or "",
        repeat_count=args.repeat_count,
        prompt=args.prompt,
        max_tokens=args.max_tokens,
        temperature=args.temperature,
        memory_gb=args.memory_gb,
        host_class=args.host_class,
        http_timeout_s=args.http_timeout_s,
    )

    if result["error"]:
        print(f"[repeatability-campaign] FAILED: {result['error']}", file=sys.stderr)
        return 1

    stats = result["repeatability_stats_dict"]
    print(f"[repeatability-campaign] n={stats['n']} "
          f"stability={stats['stability_label']}")
    print(f"  ttft: mean={stats['ttft_ms']['mean']} "
          f"stddev={stats['ttft_ms']['stddev']} "
          f"min={stats['ttft_ms']['min']} max={stats['ttft_ms']['max']}")
    print(f"  tps:  mean={stats['decode_tps']['mean']} "
          f"stddev={stats['decode_tps']['stddev']}")
    print(f"  post_health_clean={result['post_health_clean']}")
    print(f"  campaign_label={result['campaign_label']}")

    if args.ledger_path:
        rk = result["record_kwargs"]
        write_to_ledger(rk, args.ledger_path)
        print(f"[repeatability-campaign] appended to ledger: {args.ledger_path}")
        print(f"  verdict={rk['verdict']} blockers={rk['blockers']}")
        print(f"  repeatability_stability_label={rk['repeatability_stability_label']}")
        if rk.get("runtime_prefill_phase_ms") is not None:
            print(f"  mean_prefill_ms={rk['runtime_prefill_phase_ms']}")

    if result["campaign_label"] != "repeatability_evidence":
        print(
            f"[repeatability-campaign] NOTE: N={args.repeat_count} "
            f"produces '{result['campaign_label']}', not 'repeatability_evidence'. "
            "Re-run with --repeat-count 20 for campaign-grade evidence."
        )

    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Model RC repeatability campaign runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="command", required=True)

    run_p = sub.add_parser("run", help="Run a repeatability campaign")
    run_p.add_argument("--server-url", default="http://127.0.0.1:8066")
    run_p.add_argument("--model-id", required=True)
    run_p.add_argument("--artifact-path", default=None)
    run_p.add_argument("--repeat-count", type=int, default=2)
    run_p.add_argument(
        "--prompt",
        default="Describe the most important property of prime numbers in one sentence.",
    )
    run_p.add_argument("--max-tokens", type=int, default=64)
    run_p.add_argument("--temperature", type=float, default=0.0)
    run_p.add_argument("--memory-gb", type=float, default=None)
    run_p.add_argument(
        "--host-class", default="Mac17,6-arm64-macOS-26.4.1-128GB"
    )
    run_p.add_argument("--ledger-path", default=None)
    run_p.add_argument("--http-timeout-s", type=float, default=180.0)
    run_p.set_defaults(func=_cmd_run)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
