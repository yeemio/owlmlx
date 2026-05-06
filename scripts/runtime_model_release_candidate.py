#!/usr/bin/env python3
"""Operator entry for owlmlx model release-candidate evidence records."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import socket
from pathlib import Path
from typing import Any

from owlmlx.model_profile import model_profile_to_dict, resolve_model_profile
from owlmlx.reasoning_trace_policy import apply_reasoning_trace_policy
from owlmlx.model_release_candidate_ledger import (
    ModelReleaseCandidateLedger,
    model_release_candidate_history_envelope,
    model_release_candidate_still_blocked_payload,
)
from owlmlx.model_release_candidate_record import (
    build_model_release_candidate_record,
    build_dry_run_model_release_candidate_records,
    model_release_candidate_record_to_dict,
)
from owlmlx.model_release_candidate_schema import (
    validate_model_release_candidate_record,
)


DEFAULT_LEDGER_PATH = (
    Path(__file__).resolve().parents[1]
    / "files"
    / "evidence"
    / "owlmlx"
    / "model-release-candidates"
    / "ledger.jsonl"
)

GEMMA_FINAL_ANSWER_ONLY_INSTRUCTION = (
    "Answer with the final answer only. Do not include reasoning, analysis, "
    "hidden thoughts, or channel markers such as <|channel>thought or <think>."
)


def _now_compact_utc() -> str:
    return time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())


def _now_iso_utc() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


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
            payload = json.loads(raw or "{}")
        except json.JSONDecodeError:
            payload = {"raw": raw}
        return int(exc.code), payload
    except (urllib.error.URLError, socket.timeout, TimeoutError) as exc:
        return 0, {"error": str(exc)}


def _stream_http_ndjson(
    *,
    url: str,
    payload: dict[str, Any],
    timeout_s: float,
    artifact_path: Path,
) -> tuple[int, list[dict[str, Any]], float, float | None]:
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=data,
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    started = time.monotonic()
    first_token_ms: float | None = None
    events: list[dict[str, Any]] = []
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with urllib.request.urlopen(request, timeout=timeout_s) as response:
            with artifact_path.open("w", encoding="utf-8") as stream:
                for raw_line in response:
                    line = raw_line.decode("utf-8").strip()
                    if not line:
                        continue
                    try:
                        event = json.loads(line)
                    except json.JSONDecodeError:
                        event = {"event": "decode_error", "raw": line}
                    if (
                        first_token_ms is None
                        and event.get("event") == "token"
                        and str(event.get("text") or "")
                    ):
                        first_token_ms = (time.monotonic() - started) * 1000.0
                    events.append(event)
                    stream.write(json.dumps(event, sort_keys=True))
                    stream.write("\n")
            return int(response.status), events, (time.monotonic() - started) * 1000.0, first_token_ms
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8")
        event = {"event": "http_error", "status": int(exc.code), "raw": raw}
        _append_jsonl(artifact_path, event)
        return int(exc.code), [event], (time.monotonic() - started) * 1000.0, first_token_ms


def _stream_http_openai_chat_sse(
    *,
    url: str,
    model_id: str,
    messages: list[dict[str, str]],
    params: dict[str, Any],
    timeout_s: float,
    artifact_path: Path,
) -> tuple[int, list[dict[str, Any]], float, float | None]:
    """Stream through OpenAI chat completions and normalize to runner events."""

    request_payload: dict[str, Any] = {
        "model": model_id,
        "messages": messages,
        "stream": True,
    }
    request_payload.update(params)
    data = json.dumps(request_payload).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=data,
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    started = time.monotonic()
    first_token_ms: float | None = None
    events: list[dict[str, Any]] = []
    token_count = 0
    finish_reason = "stop"
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with urllib.request.urlopen(request, timeout=timeout_s) as response:
            with artifact_path.open("w", encoding="utf-8") as stream:
                for raw_line in response:
                    line = raw_line.decode("utf-8").strip()
                    if not line:
                        continue
                    if not line.startswith("data: "):
                        event = {"event": "sse_unexpected_line", "raw": line}
                        events.append(event)
                        stream.write(json.dumps(event, sort_keys=True))
                        stream.write("\n")
                        continue
                    data_line = line[len("data: ") :]
                    if data_line == "[DONE]":
                        break
                    try:
                        chunk = json.loads(data_line)
                    except json.JSONDecodeError:
                        event = {"event": "decode_error", "raw": data_line}
                        events.append(event)
                        stream.write(json.dumps(event, sort_keys=True))
                        stream.write("\n")
                        continue
                    choices = chunk.get("choices") if isinstance(chunk, dict) else None
                    choice = choices[0] if isinstance(choices, list) and choices else {}
                    delta = choice.get("delta") if isinstance(choice, dict) else {}
                    text = str(delta.get("content") or "") if isinstance(delta, dict) else ""
                    if choice.get("finish_reason"):
                        finish_reason = str(choice["finish_reason"])
                    if text:
                        token_count += 1
                        if first_token_ms is None:
                            first_token_ms = (time.monotonic() - started) * 1000.0
                        event = {
                            "event": "token",
                            "model_id": model_id,
                            "text": text,
                            "completion_tokens": token_count,
                        }
                        events.append(event)
                        stream.write(json.dumps(event, sort_keys=True))
                        stream.write("\n")
                done = {
                    "event": "done",
                    "model_id": model_id,
                    "completion_tokens": token_count,
                    "finish_reason": finish_reason,
                }
                events.append(done)
                stream.write(json.dumps(done, sort_keys=True))
                stream.write("\n")
            return int(response.status), events, (time.monotonic() - started) * 1000.0, first_token_ms
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8")
        event = {"event": "http_error", "status": int(exc.code), "raw": raw}
        _append_jsonl(artifact_path, event)
        return int(exc.code), [event], (time.monotonic() - started) * 1000.0, first_token_ms


def _discover_listen_pid(runtime_url: str) -> int | None:
    marker = "://"
    if marker not in runtime_url:
        return None
    host_port = runtime_url.split(marker, 1)[1].split("/", 1)[0]
    if ":" not in host_port:
        return None
    port = host_port.rsplit(":", 1)[1]
    if not port.isdigit():
        return None
    result = subprocess.run(
        ["lsof", "-tiTCP:" + port, "-sTCP:LISTEN"],
        check=False,
        capture_output=True,
        text=True,
    )
    for line in result.stdout.splitlines():
        stripped = line.strip()
        if stripped.isdigit():
            return int(stripped)
    return None


def _child_pids(pid: int) -> list[int]:
    result = subprocess.run(
        ["pgrep", "-P", str(pid)],
        check=False,
        capture_output=True,
        text=True,
    )
    children: list[int] = []
    for line in result.stdout.splitlines():
        stripped = line.strip()
        if stripped.isdigit():
            child = int(stripped)
            children.append(child)
            children.extend(_child_pids(child))
    return children


def _rss_bytes_by_pid(pids: list[int]) -> dict[int, int]:
    if not pids:
        return {}
    result = subprocess.run(
        ["ps", "-o", "pid=", "-o", "rss=", "-p", ",".join(str(pid) for pid in pids)],
        check=False,
        capture_output=True,
        text=True,
    )
    rss: dict[int, int] = {}
    for line in result.stdout.splitlines():
        parts = line.split()
        if len(parts) != 2 or not parts[0].isdigit() or not parts[1].isdigit():
            continue
        rss[int(parts[0])] = int(parts[1]) * 1024
    return rss


def _host_memory_bytes() -> int | None:
    result = subprocess.run(
        ["sysctl", "-n", "hw.memsize"],
        check=False,
        capture_output=True,
        text=True,
    )
    raw = result.stdout.strip()
    if raw.isdigit():
        return int(raw)
    return None


class _RssSampler:
    def __init__(self, *, root_pid: int | None, path: Path, interval_s: float) -> None:
        self.root_pid = root_pid
        self.path = path
        self.interval_s = max(float(interval_s), 0.05)
        self.peak_bytes: int | None = None
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._started = 0.0

    def __enter__(self) -> "_RssSampler":
        self._started = time.monotonic()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        return self

    def __exit__(self, *_exc: object) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=2.0)

    def _run(self) -> None:
        while not self._stop.is_set():
            if self.root_pid is None:
                sample = {
                    "elapsed_ms": round((time.monotonic() - self._started) * 1000.0, 3),
                    "root_pid": None,
                    "rss_bytes": None,
                    "pids": [],
                }
            else:
                pids = [self.root_pid, *_child_pids(self.root_pid)]
                by_pid = _rss_bytes_by_pid(pids)
                total = sum(by_pid.values())
                self.peak_bytes = max(self.peak_bytes or 0, total)
                sample = {
                    "elapsed_ms": round((time.monotonic() - self._started) * 1000.0, 3),
                    "root_pid": self.root_pid,
                    "rss_bytes": total,
                    "pids": [
                        {"pid": pid, "rss_bytes": by_pid.get(pid, 0)}
                        for pid in sorted(set(pids))
                    ],
                }
            _append_jsonl(self.path, sample)
            self._stop.wait(self.interval_s)


def _operation_payload(
    *,
    ok: bool,
    detail: str,
    error_code: str | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "status": "pass" if ok else "failed",
        "detail": detail,
    }
    if error_code:
        payload["error_code"] = error_code
    return payload


def _mean(values: list[float]) -> float | None:
    return sum(values) / len(values) if values else None


def _rounded_ms(value: float | None) -> float | None:
    return round(value, 3) if value is not None else None


def _repeat_timing_breakdown(
    *,
    load_elapsed_ms: float,
    stream_wall_ms: float,
    first_token_ms: float | None,
    queue_wait_ms: float | None,
    completion_tokens: int,
) -> dict[str, Any]:
    post_first_token_decode_wall_ms = (
        max(stream_wall_ms - first_token_ms, 0.0)
        if first_token_ms is not None
        else None
    )
    return {
        "load_elapsed_ms": _rounded_ms(load_elapsed_ms),
        "stream_request_wall_ms": _rounded_ms(stream_wall_ms),
        "first_token_latency_ms": _rounded_ms(first_token_ms),
        "post_first_token_decode_wall_ms": _rounded_ms(
            post_first_token_decode_wall_ms
        ),
        "queue_wait_ms": _rounded_ms(queue_wait_ms),
        "completion_tokens": completion_tokens,
        "post_first_token_decode_tokens": max(completion_tokens - 1, 0),
    }


def _classify_output_sanity(
    *,
    generated_texts: list[str],
    generation_results: list[dict[str, Any]],
) -> str:
    """Classify output shape without making a model-quality claim."""

    if not generated_texts:
        return "not_run"
    if any(not text.strip() for text in generated_texts):
        return "empty_text"
    for text, result in zip(generated_texts, generation_results, strict=False):
        done = result.get("done") if isinstance(result, dict) else None
        finish_reason = done.get("finish_reason") if isinstance(done, dict) else None
        trace_policy = apply_reasoning_trace_policy(
            text,
            finish_reason=str(finish_reason) if finish_reason is not None else None,
        )
        if trace_policy.visible_reasoning_trace:
            return trace_policy.output_sanity_label
        if re.search(r"\b(la[\s,.;:!?-]*){6,}\b", text.lower()):
            return "repeated_la_sequence"
        words = re.findall(r"[A-Za-z0-9']+", text.lower())
        if len(words) >= 16:
            for size in range(1, 13):
                chunks = [
                    tuple(words[index : index + size])
                    for index in range(0, len(words) - size + 1, size)
                ]
                sample_size = 8 if size <= 4 else 3
                if (
                    len(chunks) >= sample_size
                    and len(set(chunks[:sample_size])) == 1
                ):
                    return "repetitive_output"
    return "valid_text"


def _derive_quality_caveats(
    *,
    blockers: list[str],
    output_sanity_label: str,
    profile_caveats: list[str] | None = None,
) -> list[str]:
    caveats: list[str] = []
    if output_sanity_label not in {"valid_text", "not_run"}:
        caveats.append(f"output_sanity:{output_sanity_label}")
    caveats.extend(profile_caveats or [])
    caveats.extend(f"blocker:{blocker}" for blocker in blockers)
    return list(dict.fromkeys(caveats))


def _effective_generation_policy(args: argparse.Namespace) -> dict[str, Any]:
    model_profile = resolve_model_profile(args.model_id)
    explicit_request_mode = args.request_mode is not None
    explicit_prompt_template_id = args.prompt_template_id is not None
    legacy_request_mode = "raw_generate_stream"
    legacy_prompt_template_id = (
        "openai_chat_completions_apply_chat_template"
        if args.request_mode == "openai_chat_stream"
        else "operator_prompt_raw"
    )

    request_mode = args.request_mode or legacy_request_mode
    prompt_template_id = args.prompt_template_id or legacy_prompt_template_id
    caveats: list[str] = []
    decision_source = "legacy_cli_default"
    prompt_control: dict[str, Any] | None = None
    stop_token_strings_applied = False
    stop_token_application: dict[str, Any] | None = None

    if args.apply_model_profile_defaults:
        decision_source = "profile_default"
        if model_profile.profile_id in {
            "qwen3_6_text",
            "qwen3_6_moe",
            "gemma4_text",
        }:
            if not explicit_request_mode:
                request_mode = "openai_chat_stream"
            if not explicit_prompt_template_id:
                prompt_template_id = "openai_chat_completions_apply_chat_template"
            if model_profile.profile_id == "gemma4_text":
                prompt_control = {
                    "mode": "final_answer_only_user_prefix",
                    "target": "user_message_content",
                    "instruction": GEMMA_FINAL_ANSWER_ONLY_INSTRUCTION,
                    "status": "experimental_profile_control",
                }
                caveats.append("model_profile:gemma_final_answer_only_prompt_control")
        elif model_profile.profile_id == "deepseek_v4_experimental":
            caveats.append("model_profile:deepseek_v4_experimental_not_routed_to_mainline")
        else:
            caveats.append("model_profile:unknown_model_conservative_defaults")

        caveats.extend(
            f"model_profile:{caveat}" for caveat in model_profile.profile_caveats
        )
        if model_profile.stop_token_strings:
            stop_token_strings_applied = True
            stop_token_application = {
                "target": "http_generation_params.stop",
                "status": "experimental_profile_control",
                "source": "model_profile.stop_token_strings",
            }
            caveats.append("model_profile:profile_stop_tokens_applied_experimental")

    if explicit_request_mode:
        decision_source = "explicit_cli_override"
    if explicit_prompt_template_id:
        caveats.append("model_profile:explicit_prompt_template_id_preserved")

    payload = {
        "profile_applied": bool(args.apply_model_profile_defaults),
        "profile_id": model_profile.profile_id,
        "profile_family": model_profile.profile_family,
        "decision_source": decision_source,
        "request_mode": request_mode,
        "request_mode_source": (
            "explicit_cli" if explicit_request_mode else decision_source
        ),
        "prompt_template_id": prompt_template_id,
        "prompt_template_id_source": (
            "explicit_cli" if explicit_prompt_template_id else decision_source
        ),
        "chat_template_kwargs": (
            dict(model_profile.chat_template_kwargs)
            if args.apply_model_profile_defaults
            else {}
        ),
        "stop_token_strings": list(model_profile.stop_token_strings),
        "stop_token_strings_applied": stop_token_strings_applied,
        "quality_caveats": list(dict.fromkeys(caveats)),
        "unknown_model_conservative": model_profile.profile_id == "unknown",
    }
    if prompt_control is not None:
        payload["prompt_control"] = prompt_control
    if stop_token_application is not None:
        payload["stop_token_application"] = stop_token_application
    return payload


def _chat_messages_for_prompt(
    *,
    prompt: str,
    effective_policy: dict[str, Any],
) -> list[dict[str, str]]:
    prompt_control = effective_policy.get("prompt_control")
    if (
        isinstance(prompt_control, dict)
        and prompt_control.get("mode") == "final_answer_only_user_prefix"
    ):
        instruction = str(prompt_control.get("instruction") or "").strip()
        if instruction:
            return [
                {
                    "role": "user",
                    "content": f"{instruction}\n\nUser request:\n{prompt}",
                }
            ]
    return [{"role": "user", "content": prompt}]


def _load_memory_gb_from_admission(
    *,
    explicit_memory_gb: float | None,
    admission_entry: dict[str, Any],
) -> float | None:
    if explicit_memory_gb is not None:
        return explicit_memory_gb
    raw_known_peak = admission_entry.get("known_peak_resident_set_bytes")
    if not isinstance(raw_known_peak, (int, float)) or raw_known_peak <= 0:
        return None
    return round(float(raw_known_peak) / (1024.0**3), 3)


def _build_live_http_payload(args: argparse.Namespace) -> dict[str, Any]:
    runtime_url = str(args.runtime_url).rstrip("/")
    evidence_dir = Path(args.evidence_dir) if args.evidence_dir else (
        DEFAULT_LEDGER_PATH.parent / f"{_now_compact_utc()}-{args.model_id}"
    )
    evidence_dir.mkdir(parents=True, exist_ok=True)
    model_profile = resolve_model_profile(args.model_id)
    effective_policy = _effective_generation_policy(args)
    runner_config = {
        "runtime_url": runtime_url,
        "model_id": args.model_id,
        "model_profile": model_profile_to_dict(model_profile),
        "prompt": args.prompt,
        "max_tokens": args.max_tokens,
        "repeats": args.repeats,
        "request_mode": effective_policy["request_mode"],
        "prompt_template_id": args.prompt_template_id,
        "host_class": args.host_class,
        "artifact_path": args.artifact_path,
    }
    if args.memory_gb is not None:
        runner_config["memory_gb"] = args.memory_gb
    if args.apply_model_profile_defaults:
        runner_config["effective_generation_policy"] = effective_policy
    _write_json(
        evidence_dir / "runner-config.json",
        runner_config,
    )

    status, visibility = _http_json(
        method="GET",
        url=f"{runtime_url}/v1/openai/models",
        timeout_s=args.http_timeout_s,
    )
    _write_json(evidence_dir / "openai-models.json", {"status": status, "payload": visibility})
    visible_ids = [item.get("id") for item in visibility.get("data", []) if isinstance(item, dict)]
    visibility_status = "visible" if args.model_id in visible_ids else "blocked"

    root_pid = args.rss_root_pid or _discover_listen_pid(runtime_url)
    host_memory = _host_memory_bytes()
    started = time.monotonic()
    repeats_completed = 0
    failure_count = 0
    first_token_values: list[float] = []
    stream_wall_ms_values: list[float] = []
    completion_token_values: list[int] = []
    queue_wait_ms_values: list[float] = []
    load_time_ms_values: list[float] = []
    reload_time_ms_values: list[float] = []
    unload_time_ms_values: list[float] = []
    decode_token_values: list[int] = []
    decode_wall_ms_values: list[float] = []
    generated_texts: list[str] = []
    load_results: list[dict[str, Any]] = []
    reload_results: list[dict[str, Any]] = []
    generation_results: list[dict[str, Any]] = []
    unload_results: list[dict[str, Any]] = []

    blockers: list[str] = [
        "owlops_observation_pending",
        "reference_runtime_comparison_missing",
    ]

    with _RssSampler(
        root_pid=root_pid,
        path=evidence_dir / "process-tree-rss.jsonl",
        interval_s=args.rss_sample_interval_s,
    ) as rss_sampler:
        if visibility_status != "visible":
            failure_count += 1
            blockers.append("runtime_visibility_missing")
        else:
            for index in range(1, int(args.repeats) + 1):
                sample_status, sample_payload = _http_json(
                    method="POST",
                    url=f"{runtime_url}/v1/runtime/host-pressure-sample",
                    timeout_s=args.http_timeout_s,
                )
                _write_json(
                    evidence_dir / f"repeat-{index:02d}-host-pressure-sample.json",
                    {"status": sample_status, "payload": sample_payload},
                )
                if sample_status != 200:
                    failure_count += 1
                    blockers.append("host_pressure_sample_failed")
                    break

                admission_status, admission_payload = _http_json(
                    method="GET",
                    url=(
                        f"{runtime_url}/v1/runtime/model-load-admission?model_id="
                        f"{urllib.parse.quote(args.model_id)}"
                    ),
                    timeout_s=args.http_timeout_s,
                )
                _write_json(
                    evidence_dir / f"repeat-{index:02d}-model-load-admission-before.json",
                    {"status": admission_status, "payload": admission_payload},
                )
                admission_entries = admission_payload.get("entries", [])
                admission_entry = (
                    admission_entries[0]
                    if isinstance(admission_entries, list)
                    and admission_entries
                    and isinstance(admission_entries[0], dict)
                    else {}
                )
                admission_decision = str(
                    admission_entry.get("admission_decision") or "unknown"
                )
                if admission_status != 200:
                    failure_count += 1
                    blockers.append("model_load_admission_unavailable")
                    break
                if admission_decision == "blocked":
                    failure_count += 1
                    blockers.append("model_load_admission_blocked")
                    break
                if admission_decision == "unknown":
                    blockers.append("model_load_admission_unknown")

                load_started = time.monotonic()
                load_memory_gb = _load_memory_gb_from_admission(
                    explicit_memory_gb=args.memory_gb,
                    admission_entry=admission_entry,
                )
                load_request = {
                    "model_id": args.model_id,
                    "memory_gb": load_memory_gb,
                }
                load_status, load_payload = _http_json(
                    method="POST",
                    url=f"{runtime_url}/v1/load",
                    payload=load_request,
                    timeout_s=args.http_timeout_s,
                )
                load_elapsed_ms = (time.monotonic() - load_started) * 1000.0
                load_entry = {
                    "status_code": load_status,
                    "elapsed_ms": round(load_elapsed_ms, 3),
                    "request_payload": load_request,
                    "payload": load_payload,
                }
                _write_json(evidence_dir / f"repeat-{index:02d}-load.json", load_entry)
                if index == 1:
                    load_results.append(load_entry)
                    load_time_ms_values.append(load_elapsed_ms)
                else:
                    reload_results.append(load_entry)
                    reload_time_ms_values.append(load_elapsed_ms)
                if not load_payload.get("ok"):
                    failure_count += 1
                    blockers.append("load_failed" if index == 1 else "reload_failed")
                    break

                params = {"max_tokens": args.max_tokens, "temperature": args.temperature}
                if effective_policy.get("stop_token_strings_applied"):
                    params["stop"] = list(effective_policy["stop_token_strings"])
                stream_artifact = evidence_dir / f"repeat-{index:02d}-stream.ndjson"
                if effective_policy["request_mode"] == "raw_generate_stream":
                    request_payload = {
                        "model_id": args.model_id,
                        "prompt": args.prompt,
                        "params": params,
                    }
                    stream_status, events, stream_wall_ms, first_token_ms = _stream_http_ndjson(
                        url=f"{runtime_url}/v1/generate/stream",
                        payload=request_payload,
                        timeout_s=args.http_timeout_s,
                        artifact_path=stream_artifact,
                    )
                elif effective_policy["request_mode"] == "openai_chat_stream":
                    messages = _chat_messages_for_prompt(
                        prompt=args.prompt,
                        effective_policy=effective_policy,
                    )
                    request_payload = {
                        "model": args.model_id,
                        "messages": messages,
                        "stream": True,
                    }
                    request_payload.update(params)
                    stream_status, events, stream_wall_ms, first_token_ms = _stream_http_openai_chat_sse(
                        url=f"{runtime_url}/v1/chat/completions",
                        model_id=args.model_id,
                        messages=messages,
                        params=params,
                        timeout_s=args.http_timeout_s,
                        artifact_path=stream_artifact,
                    )
                else:  # pragma: no cover - argparse choices guard this.
                    raise ValueError(
                        f"unsupported request_mode: {effective_policy['request_mode']}"
                    )
                done = next((event for event in reversed(events) if event.get("event") == "done"), None)
                token_events = [event for event in events if event.get("event") == "token"]
                text = "".join(str(event.get("text") or "") for event in token_events)
                generated_texts.append(text)
                completion_tokens = (
                    int(done.get("completion_tokens"))
                    if isinstance(done, dict) and isinstance(done.get("completion_tokens"), int)
                    else len(token_events)
                )
                completion_token_values.append(completion_tokens)
                stream_wall_ms_values.append(stream_wall_ms)
                if first_token_ms is not None:
                    first_token_values.append(first_token_ms)
                    decode_wall_ms = max(stream_wall_ms - first_token_ms, 0.0)
                    decode_tokens = max(completion_tokens - 1, 0)
                    if decode_tokens > 0 and decode_wall_ms > 0:
                        decode_token_values.append(decode_tokens)
                        decode_wall_ms_values.append(decode_wall_ms)
                if isinstance(done, dict) and isinstance(done.get("wait_time_s"), (int, float)):
                    queue_wait_ms = float(done["wait_time_s"]) * 1000.0
                    queue_wait_ms_values.append(queue_wait_ms)
                else:
                    queue_wait_ms = None
                generation_entry = {
                    "status_code": stream_status,
                    "elapsed_ms": round(stream_wall_ms, 3),
                    "first_token_latency_ms": (
                        round(first_token_ms, 3) if first_token_ms is not None else None
                    ),
                    "completion_tokens": completion_tokens,
                    "event_count": len(events),
                    "done": done,
                    "request_payload": request_payload,
                    "text_preview": text[:500],
                    "reasoning_trace_policy": apply_reasoning_trace_policy(
                        text,
                        finish_reason=(
                            str(done.get("finish_reason"))
                            if isinstance(done, dict)
                            and done.get("finish_reason") is not None
                            else None
                        ),
                    ).to_dict(),
                    "timing_breakdown": _repeat_timing_breakdown(
                        load_elapsed_ms=load_elapsed_ms,
                        stream_wall_ms=stream_wall_ms,
                        first_token_ms=first_token_ms,
                        queue_wait_ms=queue_wait_ms,
                        completion_tokens=completion_tokens,
                    ),
                }
                _write_json(evidence_dir / f"repeat-{index:02d}-generation.json", generation_entry)
                generation_results.append(generation_entry)
                if stream_status != 200 or done is None:
                    failure_count += 1
                    blockers.append("generation_failed")

                unload_started = time.monotonic()
                unload_status, unload_payload = _http_json(
                    method="POST",
                    url=f"{runtime_url}/v1/unload",
                    payload={"model_id": args.model_id},
                    timeout_s=args.http_timeout_s,
                )
                unload_elapsed_ms = (time.monotonic() - unload_started) * 1000.0
                unload_entry = {
                    "status_code": unload_status,
                    "elapsed_ms": round(unload_elapsed_ms, 3),
                    "payload": unload_payload,
                }
                _write_json(evidence_dir / f"repeat-{index:02d}-unload.json", unload_entry)
                unload_results.append(unload_entry)
                unload_time_ms_values.append(unload_elapsed_ms)
                if not unload_payload.get("ok"):
                    failure_count += 1
                    blockers.append("unload_failed")
                    break
                if stream_status == 200 and done is not None:
                    repeats_completed += 1

    post_health_status, post_health_payload = _http_json(
        method="GET",
        url=f"{runtime_url}/healthz",
        timeout_s=args.http_timeout_s,
    )
    _write_json(
        evidence_dir / "post-run-healthz.json",
        {"status": post_health_status, "payload": post_health_payload},
    )
    post_status_code, post_status_payload = _http_json(
        method="GET",
        url=f"{runtime_url}/v1/runtime/status",
        timeout_s=args.http_timeout_s,
    )
    _write_json(
        evidence_dir / "post-run-runtime-status.json",
        {"status": post_status_code, "payload": post_status_payload},
    )
    status_summary = (
        post_status_payload.get("summary", {})
        if isinstance(post_status_payload, dict)
        else {}
    )
    post_status_backend_healthy = bool(status_summary.get("backend_healthy"))
    post_run_backend_healthy = (
        post_health_status == 200
        and bool(post_health_payload.get("ok"))
        and post_status_code == 200
        and post_status_backend_healthy
    )
    if not post_run_backend_healthy:
        failure_count += 1
        blockers.append("post_run_backend_unhealthy")

    wall_clock_ms = (time.monotonic() - started) * 1000.0
    peak_rss = rss_sampler.peak_bytes
    memory_headroom = (
        max(host_memory - peak_rss, 0)
        if host_memory is not None and peak_rss is not None
        else None
    )
    first_token_latency = _mean(first_token_values)
    total_completion_tokens = sum(completion_token_values)
    total_generation_s = sum(stream_wall_ms_values) / 1000.0
    tokens_per_second = (
        total_completion_tokens / total_generation_s
        if total_completion_tokens > 0 and total_generation_s > 0
        else None
    )
    total_decode_tokens = sum(decode_token_values)
    total_decode_s = sum(decode_wall_ms_values) / 1000.0
    decode_tokens_per_second = (
        total_decode_tokens / total_decode_s
        if total_decode_tokens > 0 and total_decode_s > 0
        else None
    )

    if first_token_latency is None:
        blockers.append("first_token_latency_missing")
    if tokens_per_second is None:
        blockers.append("tokens_per_second_missing")
    if peak_rss is None:
        blockers.append("process_tree_rss_missing")
    if memory_headroom is None:
        blockers.append("memory_headroom_missing")

    def aggregate_operation(
        entries: list[dict[str, Any]],
        *,
        success_detail: str,
        empty_status: str = "failed",
        empty_detail: str = "operation did not run",
    ) -> dict[str, Any]:
        if not entries:
            return {"status": empty_status, "detail": empty_detail}
        if all((entry.get("payload") or {}).get("ok") for entry in entries):
            return {"status": "pass", "detail": success_detail}
        first_failed = next(entry for entry in entries if not (entry.get("payload") or {}).get("ok"))
        payload = first_failed.get("payload") or {}
        result = {
            "status": "failed",
            "detail": str(payload.get("message") or payload.get("raw") or "operation failed"),
        }
        if payload.get("error_code"):
            result["error_code"] = str(payload["error_code"])
        return result

    generation_ok = bool(generation_results) and all(
        entry.get("status_code") == 200 and entry.get("done") is not None
        for entry in generation_results
    )
    load_result = aggregate_operation(
        load_results,
        success_detail=f"initial load completed for {args.model_id}",
    )
    generation_result = (
        {"status": "pass", "detail": f"{repeats_completed} stream generations completed"}
        if generation_ok
        else {"status": "failed", "detail": "stream generation did not complete"}
    )
    unload_result = aggregate_operation(
        unload_results,
        success_detail=f"{len(unload_results)} unload operations completed",
    )
    reload_result = aggregate_operation(
        reload_results,
        success_detail=f"{len(reload_results)} reload operations completed",
        empty_status="not_applicable" if int(args.repeats) < 2 else "failed",
        empty_detail="reload requires at least two repeats",
    )

    output_sanity_label = _classify_output_sanity(
        generated_texts=generated_texts,
        generation_results=generation_results,
    )
    if output_sanity_label == "reasoning_trace_truncated":
        blockers.append("short_generation_quality_inconclusive")
    if failure_count > 0 or repeats_completed < int(args.repeats):
        verdict = "blocked"
        blockers.append("live_repeated_run_incomplete")
    else:
        verdict = "needs_optimization"
    blockers = list(dict.fromkeys(blockers))
    quality_caveats = _derive_quality_caveats(
        blockers=blockers,
        output_sanity_label=output_sanity_label,
        profile_caveats=effective_policy["quality_caveats"],
    )

    record = build_model_release_candidate_record(
        created_at=args.created_at or _now_iso_utc(),
        model_id=args.model_id,
        lane="mainline",
        runtime_url=runtime_url,
        host_class=args.host_class,
        artifact_path=args.artifact_path,
        visibility_status=visibility_status,
        load_result=load_result,
        generation_result=generation_result,
        unload_result=unload_result,
        reload_result=reload_result,
        repeat_count=repeats_completed,
        failure_count=failure_count,
        first_token_latency_ms=(
            round(first_token_latency, 3) if first_token_latency is not None else None
        ),
        tokens_per_second=(
            round(tokens_per_second, 3) if tokens_per_second is not None else None
        ),
        wall_clock_ms=round(wall_clock_ms, 3),
        peak_resident_set_bytes=peak_rss,
        memory_headroom_bytes=memory_headroom,
        output_sanity_label=output_sanity_label,
        owlops_observation_path=str(evidence_dir),
        verdict=verdict,
        blockers=tuple(blockers),
        load_time_ms=_rounded_ms(_mean(load_time_ms_values)),
        reload_time_ms=_rounded_ms(_mean(reload_time_ms_values)),
        unload_time_ms=_rounded_ms(_mean(unload_time_ms_values)),
        queue_wait_ms=_rounded_ms(_mean(queue_wait_ms_values)),
        ttft_ms=_rounded_ms(first_token_latency),
        decode_tokens_per_second=(
            round(decode_tokens_per_second, 3)
            if decode_tokens_per_second is not None
            else None
        ),
        end_to_end_tokens_per_second=(
            round(tokens_per_second, 3) if tokens_per_second is not None else None
        ),
        resident_mode="load_unload_per_repeat",
        prompt_template_id=str(effective_policy["prompt_template_id"]),
        quality_caveats=tuple(quality_caveats),
        memory_peak_source="process_tree_rss",
    )
    payload = model_release_candidate_record_to_dict(record)
    _write_json(evidence_dir / "record.json", payload)
    return payload


def _build_dry_run_payload(args: argparse.Namespace) -> list[dict[str, object]]:
    records = build_dry_run_model_release_candidate_records(
        runtime_url=args.runtime_url,
        host_class=args.host_class,
        created_at=args.created_at,
    )
    return [model_release_candidate_record_to_dict(record) for record in records]


def _load_record_file(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    validate_model_release_candidate_record(payload)
    return payload


def _append_record_payload(ledger: ModelReleaseCandidateLedger, payload: dict[str, Any]) -> dict[str, Any]:
    validate_model_release_candidate_record(payload)
    ledger.path.parent.mkdir(parents=True, exist_ok=True)
    with ledger.path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(payload, sort_keys=True))
        stream.write("\n")
    return payload


def _build_unique_history_from_sources(paths: list[str]) -> list[dict[str, Any]]:
    records_by_key: dict[tuple[str, str], dict[str, Any]] = {}
    ordered_keys: list[tuple[str, str]] = []
    for raw_path in paths:
        path = Path(raw_path)
        candidates: list[dict[str, Any]]
        if path.suffix == ".jsonl":
            candidates = ModelReleaseCandidateLedger(path).history()
        else:
            candidates = [_load_record_file(path)]
        for record in candidates:
            key = (str(record["model_id"]), str(record["created_at"]))
            if key not in records_by_key:
                ordered_keys.append(key)
            records_by_key[key] = record
    return [records_by_key[key] for key in ordered_keys]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Operator entry for owlmlx model release-candidate records."
    )
    parser.add_argument(
        "--ledger-path",
        default=str(DEFAULT_LEDGER_PATH),
        help=(
            "Path to the JSONL ledger file "
            "(default: files/evidence/owlmlx/model-release-candidates/ledger.jsonl)"
        ),
    )
    sub = parser.add_subparsers(dest="command", required=True)

    dry = sub.add_parser(
        "dry-run-matrix",
        help="Print the A0 model RC matrix without appending it",
    )
    dry.add_argument("--runtime-url", default="http://127.0.0.1:8066")
    dry.add_argument("--host-class", default="Mac17,6-arm64-macOS-26.4.1-128GB")
    dry.add_argument("--created-at", default=None)

    append = sub.add_parser(
        "append-dry-run-matrix",
        help="Append the A0 model RC matrix to the JSONL ledger",
    )
    append.add_argument("--runtime-url", default="http://127.0.0.1:8066")
    append.add_argument("--host-class", default="Mac17,6-arm64-macOS-26.4.1-128GB")
    append.add_argument("--created-at", default=None)

    live = sub.add_parser(
        "run-live-http-mainline",
        help="Run one visible mainline model through live HTTP Model RC evidence",
    )
    live.add_argument("--runtime-url", default="http://127.0.0.1:8066")
    live.add_argument("--host-class", default="Mac17,6-arm64-macOS-26.4.1-128GB")
    live.add_argument("--created-at", default=None)
    live.add_argument("--model-id", required=True)
    live.add_argument("--artifact-path", required=True)
    live.add_argument("--prompt", required=True)
    live.add_argument("--max-tokens", type=int, default=16)
    live.add_argument("--temperature", type=float, default=0.0)
    live.add_argument(
        "--request-mode",
        choices=("raw_generate_stream", "openai_chat_stream"),
        default=None,
        help=(
            "HTTP generation path for live evidence. raw_generate_stream keeps "
            "the legacy /v1/generate/stream path; openai_chat_stream routes "
            "through /v1/chat/completions so tokenizer chat templates apply. "
            "When omitted, the legacy default is raw_generate_stream unless "
            "--apply-model-profile-defaults safely selects another path."
        ),
    )
    live.add_argument(
        "--prompt-template-id",
        default=None,
        help="Optional provenance label for the prompt/template path.",
    )
    live.add_argument("--repeats", type=int, default=2)
    live.add_argument("--memory-gb", type=float, default=None)
    live.add_argument("--evidence-dir", default=None)
    live.add_argument("--http-timeout-s", type=float, default=900.0)
    live.add_argument("--rss-root-pid", type=int, default=None)
    live.add_argument("--rss-sample-interval-s", type=float, default=0.5)
    live.add_argument(
        "--apply-model-profile-defaults",
        action="store_true",
        help=(
            "Opt in to owlmlx model-profile defaults for effective request "
            "mode and evidence caveats; explicit CLI request/template choices "
            "are preserved."
        ),
    )

    append_record = sub.add_parser(
        "append-record-file",
        help="Append one schema-valid record JSON file to the JSONL ledger",
    )
    append_record.add_argument("record_path")

    merge = sub.add_parser(
        "merge-ledgers",
        help="Merge record JSON and JSONL inputs into the configured ledger",
    )
    merge.add_argument("paths", nargs="+")
    merge.add_argument(
        "--replace",
        action="store_true",
        help="Replace the output ledger instead of appending to it",
    )

    sub.add_parser("latest", help="Print the latest record or still_blocked payload")
    sub.add_parser("history", help="Print the full history envelope")

    args = parser.parse_args()
    ledger = ModelReleaseCandidateLedger(args.ledger_path)

    if args.command == "dry-run-matrix":
        print(json.dumps(_build_dry_run_payload(args), indent=2, sort_keys=True))
        return 0

    if args.command == "append-dry-run-matrix":
        records = build_dry_run_model_release_candidate_records(
            runtime_url=args.runtime_url,
            host_class=args.host_class,
            created_at=args.created_at,
        )
        payload = ledger.append_many(records)
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0

    if args.command == "run-live-http-mainline":
        payload = ledger.append(
            build_model_release_candidate_record(**{
                key: value
                for key, value in _build_live_http_payload(args).items()
                if key
                not in {
                    "surface",
                    "version",
                }
            })
        )
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0

    if args.command == "append-record-file":
        payload = _append_record_payload(ledger, _load_record_file(args.record_path))
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0

    if args.command == "merge-ledgers":
        records = _build_unique_history_from_sources(args.paths)
        if args.replace and ledger.path.exists():
            ledger.path.unlink()
        payload = [_append_record_payload(ledger, record) for record in records]
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0

    if args.command == "latest":
        latest = ledger.latest()
        if latest is None:
            print(
                json.dumps(
                    model_release_candidate_still_blocked_payload(
                        missing_signal="no_model_release_candidate_record_appended",
                        ledger_path=str(ledger.path),
                    ),
                    indent=2,
                    sort_keys=True,
                )
            )
            return 0
        print(json.dumps(latest, indent=2, sort_keys=True))
        return 0

    if args.command == "history":
        records = ledger.history()
        print(
            json.dumps(
                model_release_candidate_history_envelope(
                    records=records,
                    ledger_status="available" if records else "empty",
                ),
                indent=2,
                sort_keys=True,
            )
        )
        return 0

    parser.error(f"unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
