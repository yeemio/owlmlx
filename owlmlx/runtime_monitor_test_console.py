"""Runtime-owned monitor and test-console contract builders.

This module keeps the JSON contract builders pure, and owns the append-only
audit registry used by the runtime worker. Model loading/generation is still
performed by the 8066 runtime server, not by OwlOps.
"""

from __future__ import annotations

import json
import threading
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import urlparse
from uuid import uuid4


MONITOR_SNAPSHOT_SURFACE = "owlmlx.runtime.monitor.snapshot"
MONITOR_SAMPLE_SURFACE = "owlmlx.runtime.monitor.sample"
MONITOR_HISTORY_SURFACE = "owlmlx.runtime.monitor.history"
MONITOR_EVENT_SURFACE = "owlmlx.runtime.monitor.event"
TEST_RUN_PREFLIGHT_SURFACE = "owlmlx.runtime.test_run.preflight"
TEST_RUN_INDEX_SURFACE = "owlmlx.runtime.test_run.index"
TEST_RUN_STATUS_SURFACE = "owlmlx.runtime.test_run.status"
TEST_RUN_LAUNCH_SURFACE = "owlmlx.runtime.test_run.launch"
TEST_RUN_ABORT_SURFACE = "owlmlx.runtime.test_run.abort"
TEST_RUN_EVENT_SURFACE = "owlmlx.runtime.test_run.event"
TEST_RUN_AUDIT_ROW_SURFACE = "owlmlx.runtime.test_run.audit_row"
RUNTIME_MONITOR_VERSION = "v1"
TERMINAL_TEST_RUN_STATUSES = {
    "succeeded",
    "failed",
    "error",
    "refused",
    "unsupported",
    "aborted",
}


TEST_PROFILE_CATALOG: dict[str, dict[str, Any]] = {
    "qwen36-27b-decode": {
        "profile_id": "qwen36-27b-decode",
        "model_ids": ("Qwen3.6-27B",),
        "purpose": "isolate_decode_throughput_after_ttft_and_queue_wait",
        "estimated_memory_gb": 48.0,
        "allow_live_launch": True,
    },
    "qwen36-35b-ttft-template": {
        "profile_id": "qwen36-35b-ttft-template",
        "model_ids": ("Qwen3.6-35B-A3B",),
        "purpose": "separate_template_request_mode_from_first_token_latency",
        "estimated_memory_gb": 72.0,
        "allow_live_launch": True,
    },
    "gemma-repetitive-output-template": {
        "profile_id": "gemma-repetitive-output-template",
        "model_ids": ("gemma-4-12B-it", "gemma-4-31B-it"),
        "purpose": "surface_repetitive_or_visible_reasoning_without_hiding_failure",
        "estimated_memory_gb": 60.0,
        "allow_live_launch": True,
    },
    "post-run-health-gate": {
        "profile_id": "post-run-health-gate",
        "model_ids": (
            "Qwen3.6-27B",
            "Qwen3.6-35B-A3B",
            "gemma-4-12B-it",
            "gemma-4-31B-it",
        ),
        "purpose": "prove_repeated_load_generate_unload_leaves_backend_clean",
        "estimated_memory_gb": None,
        "allow_live_launch": True,
    },
}


def _now_iso_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _mapping(value: object) -> dict[str, Any]:
    if isinstance(value, Mapping):
        return dict(value)
    return {}


def _list_of_mappings(value: object) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [dict(item) for item in value if isinstance(item, Mapping)]


def _contract(surface: str) -> dict[str, str]:
    return {"surface": surface, "version": RUNTIME_MONITOR_VERSION}


def _run_id(sampled_at: str) -> str:
    compact = (
        sampled_at.replace("-", "")
        .replace(":", "")
        .replace("T", "T")
        .replace("Z", "Z")
    )
    return f"run_{compact}_{uuid4().hex[:8]}"


def _event_id(run_id: str, sequence: int) -> str:
    return f"{run_id}_{sequence:04d}"


def _positive_float(value: object) -> float | None:
    try:
        number = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
    if number <= 0:
        return None
    return number


def _positive_int(value: object) -> int | None:
    try:
        number = int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
    if number <= 0:
        return None
    return number


def _iso_to_datetime(value: object) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _port_from_url(runtime_url: str) -> int | None:
    parsed = urlparse(runtime_url)
    return parsed.port


def _source(
    *,
    name: str,
    route_or_file: str | None,
    sampled_at: str,
    status: str,
    truth_level: str,
) -> dict[str, Any]:
    return {
        "name": name,
        "route_or_file": route_or_file,
        "sampled_at": sampled_at,
        "status": status,
        "staleness_ms": 0,
        "truth_level": truth_level,
    }


def _latest_records_by_model(records: list[Mapping[str, Any]]) -> dict[str, dict[str, Any]]:
    latest: dict[str, dict[str, Any]] = {}
    for raw in records:
        record = _mapping(raw)
        model_id = str(record.get("model_id") or "")
        if model_id:
            latest[model_id] = record
    return latest


def _visible_model_ids(visibility_contract: Mapping[str, Any] | None) -> list[str]:
    contract = _mapping(visibility_contract)
    visible = contract.get("visible_model_ids")
    if isinstance(visible, list):
        return [str(model_id) for model_id in visible if isinstance(model_id, str)]
    entries = _list_of_mappings(contract.get("entries"))
    return [
        str(entry.get("model_id"))
        for entry in entries
        if entry.get("visible") is True and entry.get("model_id")
    ]


def _visibility_status(
    *,
    model_id: str,
    visibility_contract: Mapping[str, Any] | None,
) -> dict[str, Any]:
    contract = _mapping(visibility_contract)
    entries = _list_of_mappings(contract.get("entries"))
    for entry in entries:
        if str(entry.get("model_id") or "") == model_id:
            if entry.get("visible") is True:
                return {"status": "visible", "source": "runtime_model_visibility"}
            return {
                "status": "blocked",
                "source": "runtime_model_visibility",
                "reason": entry.get("block_reason") or "model_not_visible",
            }
    if model_id in _visible_model_ids(contract):
        return {"status": "visible", "source": "runtime_model_visibility"}
    return {
        "status": "unknown",
        "source": "runtime_model_visibility",
        "reason": "model_visibility_truth_absent",
    }


def _admission_entry(
    *,
    model_id: str,
    model_load_admission: Mapping[str, Any] | None,
) -> dict[str, Any] | None:
    for entry in _list_of_mappings(_mapping(model_load_admission).get("entries")):
        if str(entry.get("model_id") or "") == model_id:
            return entry
    return None


def _test_run_entries(test_runs: Mapping[str, Any] | list[Mapping[str, Any]] | None) -> list[dict[str, Any]]:
    if isinstance(test_runs, list):
        return [dict(run) for run in test_runs if isinstance(run, Mapping)]
    return [_mapping(run) for run in _mapping(test_runs).values()]


def _active_test_run(test_runs: Mapping[str, Any] | list[Mapping[str, Any]] | None) -> dict[str, Any] | None:
    for run in _test_run_entries(test_runs):
        entry = _mapping(run)
        if entry.get("status") in {"preflight", "queued", "running", "aborting"}:
            return entry
    return None


def _event(
    *,
    event_id: str,
    run_id: str,
    event_type: str,
    phase: str,
    severity: str,
    sampled_at: str,
    source: str,
    payload: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "contract": _contract(TEST_RUN_EVENT_SURFACE),
        "event_id": event_id,
        "run_id": run_id,
        "type": event_type,
        "phase": phase,
        "severity": severity,
        "sampled_at": sampled_at,
        "source": source,
        "truth_level": "runtime_owned",
        "payload": dict(payload),
    }


class RuntimeTestRunRegistry:
    """Append-only audit-backed registry for runtime test-run attempts.

    The registry records operator intent and worker progress. It does not
    execute model work itself; callers append full-row snapshots as the runtime
    worker advances through load, generate, unload, and evidence phases.
    """

    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)
        self._lock = threading.Lock()

    @property
    def path(self) -> Path:
        return self._path

    def exists(self) -> bool:
        return self._path.exists()

    def _append_snapshot(self, row: Mapping[str, Any]) -> dict[str, Any]:
        snapshot = dict(row)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._lock:
            with self._path.open("a", encoding="utf-8") as stream:
                stream.write(json.dumps(snapshot, sort_keys=True))
                stream.write("\n")
        return snapshot

    def create_launch(
        self,
        *,
        request_payload: Mapping[str, Any],
        preflight: Mapping[str, Any],
        status: str,
        launch_decision: str,
        reason: str,
        sampled_at: str | None = None,
    ) -> dict[str, Any]:
        sampled = sampled_at or _now_iso_utc()
        run_id = _run_id(sampled)
        model_id = str(request_payload.get("model_id") or "")
        profile_id = str(request_payload.get("test_profile_id") or "")
        mode = str(request_payload.get("mode") or "dry_run")
        events = [
            _event(
                event_id=_event_id(run_id, 1),
                run_id=run_id,
                event_type="test_run.preflight_completed",
                phase="preflight",
                severity="info",
                sampled_at=sampled,
                source="runtime_test_run_registry",
                payload={
                    "decision": preflight.get("decision"),
                    "reason": preflight.get("reason"),
                    "read_only": True,
                },
            ),
            _event(
                event_id=_event_id(run_id, 2),
                run_id=run_id,
                event_type="test_run.launch_accepted"
                if launch_decision == "accepted"
                else "test_run.launch_refused",
                phase="launch",
                severity="info" if launch_decision == "accepted" else "warning",
                sampled_at=sampled,
                source="runtime_test_run_registry",
                payload={
                    "launch_decision": launch_decision,
                    "reason": reason,
                    "does_not_touch_legacy_listeners": ["8001", "8009"],
                },
            ),
        ]
        row: dict[str, Any] = {
            "contract": _contract(TEST_RUN_AUDIT_ROW_SURFACE),
            "run_id": run_id,
            "requested_at": sampled,
            "updated_at": sampled,
            "operator": _mapping(request_payload.get("operator")),
            "model_id": model_id,
            "test_profile_id": profile_id,
            "mode": mode,
            "parameters": _mapping(request_payload.get("parameters")),
            "preflight_decision": preflight.get("decision"),
            "preflight_reason": preflight.get("reason"),
            "launch_decision": launch_decision,
            "status": status,
            "phase": "launch",
            "reason": reason,
            "evidence_path": None,
            "model_release_candidate_record_path": None,
            "metrics": {},
            "audit_ledger_path": str(self._path),
            "events": events,
            "policy_boundaries": {
                "does_not_touch_legacy_listeners": ["8001", "8009"],
                "launched_by_runtime": launch_decision == "accepted",
                "abort_is_audited_only": True,
            },
        }
        return self._append_snapshot(row)

    def persist(self, row: Mapping[str, Any]) -> dict[str, Any]:
        return self._append_snapshot(row)

    def update(
        self,
        row: Mapping[str, Any],
        *,
        status: str | None = None,
        phase: str | None = None,
        reason: str | None = None,
        metrics: Mapping[str, Any] | None = None,
        evidence_path: str | None = None,
        extra: Mapping[str, Any] | None = None,
        sampled_at: str | None = None,
    ) -> dict[str, Any]:
        updated = dict(row)
        sampled = sampled_at or _now_iso_utc()
        updated["updated_at"] = sampled
        if status is not None:
            updated["status"] = status
        if phase is not None:
            updated["phase"] = phase
        if reason is not None:
            updated["reason"] = reason
        if metrics is not None:
            updated["metrics"] = dict(metrics)
        if evidence_path is not None:
            updated["evidence_path"] = evidence_path
        if extra is not None:
            updated.update(dict(extra))
        return self._append_snapshot(updated)

    def add_event(
        self,
        row: Mapping[str, Any],
        *,
        event_type: str,
        phase: str,
        severity: str,
        payload: Mapping[str, Any],
        status: str | None = None,
        reason: str | None = None,
        metrics: Mapping[str, Any] | None = None,
        evidence_path: str | None = None,
        extra: Mapping[str, Any] | None = None,
        sampled_at: str | None = None,
    ) -> dict[str, Any]:
        sampled = sampled_at or _now_iso_utc()
        updated = dict(row)
        events = _list_of_mappings(updated.get("events"))
        run_id = str(updated.get("run_id") or "")
        events.append(
            _event(
                event_id=_event_id(run_id, len(events) + 1),
                run_id=run_id,
                event_type=event_type,
                phase=phase,
                severity=severity,
                sampled_at=sampled,
                source="runtime_test_run_worker",
                payload=payload,
            )
        )
        updated["events"] = events
        updated["updated_at"] = sampled
        updated["phase"] = phase
        if status is not None:
            updated["status"] = status
        if reason is not None:
            updated["reason"] = reason
        if metrics is not None:
            updated["metrics"] = dict(metrics)
        if evidence_path is not None:
            updated["evidence_path"] = evidence_path
        if extra is not None:
            updated.update(dict(extra))
        return self._append_snapshot(updated)

    def append_unsupported_launch(
        self,
        *,
        request_payload: Mapping[str, Any],
        preflight: Mapping[str, Any],
        reason: str = "test_run_launch_worker_not_implemented",
        sampled_at: str | None = None,
    ) -> dict[str, Any]:
        sampled = sampled_at or _now_iso_utc()
        run_id = _run_id(sampled)
        model_id = str(request_payload.get("model_id") or "")
        profile_id = str(request_payload.get("test_profile_id") or "")
        mode = str(request_payload.get("mode") or "dry_run")
        events = [
            _event(
                event_id=_event_id(run_id, 1),
                run_id=run_id,
                event_type="test_run.preflight_completed",
                phase="preflight",
                severity="info",
                sampled_at=sampled,
                source="runtime_test_run_registry",
                payload={
                    "decision": preflight.get("decision"),
                    "reason": preflight.get("reason"),
                    "read_only": True,
                },
            ),
            _event(
                event_id=_event_id(run_id, 2),
                run_id=run_id,
                event_type="test_run.launch_unsupported",
                phase="launch",
                severity="warning",
                sampled_at=sampled,
                source="runtime_test_run_registry",
                payload={
                    "launch_decision": "unsupported",
                    "reason": reason,
                    "does_not_load_model": True,
                    "does_not_generate": True,
                },
            ),
        ]
        row: dict[str, Any] = {
            "contract": _contract(TEST_RUN_AUDIT_ROW_SURFACE),
            "run_id": run_id,
            "requested_at": sampled,
            "updated_at": sampled,
            "operator": _mapping(request_payload.get("operator")),
            "model_id": model_id,
            "test_profile_id": profile_id,
            "mode": mode,
            "parameters": _mapping(request_payload.get("parameters")),
            "preflight_decision": preflight.get("decision"),
            "preflight_reason": preflight.get("reason"),
            "launch_decision": "unsupported",
            "status": "unsupported",
            "phase": "launch",
            "reason": reason,
            "evidence_path": None,
            "model_release_candidate_record_path": None,
            "audit_ledger_path": str(self._path),
            "events": events,
            "policy_boundaries": {
                "does_not_load_model": True,
                "does_not_generate": True,
                "does_not_abort_process": True,
                "does_not_touch_legacy_listeners": ["8001", "8009"],
            },
        }
        return self._append_snapshot(row)

    def history(self) -> list[dict[str, Any]]:
        if not self._path.exists():
            return []
        records_by_id: dict[str, dict[str, Any]] = {}
        with self._path.open("r", encoding="utf-8") as stream:
            for line in stream:
                stripped = line.strip()
                if not stripped:
                    continue
                payload = json.loads(stripped)
                if isinstance(payload, Mapping) and payload.get("run_id"):
                    records_by_id[str(payload.get("run_id"))] = dict(payload)
        return list(records_by_id.values())

    def get(self, run_id: str) -> dict[str, Any] | None:
        for record in reversed(self.history()):
            if record.get("run_id") == run_id:
                return record
        return None


def build_monitor_sample(
    snapshot: Mapping[str, Any],
    *,
    source: str,
    sampled_at: str | None = None,
) -> dict[str, Any]:
    """Build a compact runtime-owned trend sample from a monitor snapshot."""

    sample_time = sampled_at or str(snapshot.get("sampled_at") or _now_iso_utc())
    service = _mapping(snapshot.get("service"))
    workload = _mapping(snapshot.get("workload"))
    resources = _mapping(snapshot.get("resources"))
    budget = _mapping(resources.get("budget"))
    host_pressure = _mapping(resources.get("host_pressure"))
    models = _mapping(snapshot.get("models"))
    test_runs = _mapping(snapshot.get("test_runs"))
    release_candidates = _mapping(snapshot.get("release_candidates"))
    loaded_models = models.get("loaded_models")
    visible_model_ids = models.get("visible_model_ids")
    utilization = _positive_float(budget.get("utilization"))
    return {
        "contract": _contract(MONITOR_SAMPLE_SURFACE),
        "sample_id": f"sample_{sample_time.replace('-', '').replace(':', '')}_{uuid4().hex[:8]}",
        "sampled_at": sample_time,
        "runtime_url": snapshot.get("runtime_url"),
        "source": source,
        "truth_level": "runtime_owned",
        "service": {
            "ok": service.get("ok"),
            "readiness": service.get("readiness"),
            "health_classification": service.get("health_classification"),
            "active_model_id": service.get("active_model_id"),
            "model_count": service.get("model_count"),
        },
        "workload": {
            "active_run_id": workload.get("active_run_id"),
            "generation_gate": workload.get("generation_gate"),
            "queue_size": workload.get("queue_size"),
            "queue_policy": workload.get("queue_policy"),
            "longest_execution_s": workload.get("longest_execution_s"),
            "total_served": workload.get("total_served"),
            "current_phase": workload.get("current_phase"),
            "block_reason": workload.get("block_reason"),
        },
        "resources": {
            "loaded_gb": resources.get("loaded_gb") or budget.get("loaded_gb"),
            "available_gb": resources.get("available_gb") or budget.get("available_gb"),
            "serving_budget_gb": budget.get("serving_budget_gb"),
            "budget_utilization_pct": (utilization * 100.0) if utilization is not None else None,
            "pressure_classification": resources.get("pressure_classification"),
            "host_pressure_classification": host_pressure.get("classification"),
            "host_free_percent": host_pressure.get("free_percent"),
            "host_free_gb": host_pressure.get("free_gb"),
            "wired_gb": host_pressure.get("wired_gb"),
            "compressor_gb": host_pressure.get("compressor_gb"),
        },
        "models": {
            "loaded_model_count": len(loaded_models) if isinstance(loaded_models, list) else None,
            "visible_model_count": len(visible_model_ids) if isinstance(visible_model_ids, list) else None,
        },
        "test_runs": {
            "active_run_id": test_runs.get("active_run_id"),
            "known_run_count": test_runs.get("known_run_count"),
            "audit_ledger_status": test_runs.get("audit_ledger_status"),
        },
        "release_candidates": {
            "history_count": release_candidates.get("history_count"),
            "latest_model_count": release_candidates.get("latest_model_count"),
            "ledger_status": release_candidates.get("ledger_status"),
        },
        "policy_boundaries": {
            "does_not_load_model": True,
            "does_not_generate": True,
            "does_not_abort_process": True,
            "compact_sample_only": True,
        },
    }


class RuntimeMonitorTrendRegistry:
    """Runtime-owned rolling JSONL store for monitor trend samples."""

    def __init__(self, path: str | Path, *, max_rows: int = 20160) -> None:
        self._path = Path(path)
        self._max_rows = max(1, max_rows)
        self._lock = threading.Lock()

    @property
    def path(self) -> Path:
        return self._path

    @property
    def max_rows(self) -> int:
        return self._max_rows

    def append_snapshot(
        self,
        snapshot: Mapping[str, Any],
        *,
        source: str,
        sampled_at: str | None = None,
    ) -> dict[str, Any]:
        sample = build_monitor_sample(snapshot, source=source, sampled_at=sampled_at)
        self._append_sample(sample)
        return sample

    def append_error(
        self,
        *,
        runtime_url: str,
        source: str,
        error: str,
        sampled_at: str | None = None,
    ) -> dict[str, Any]:
        sample_time = sampled_at or _now_iso_utc()
        sample = {
            "contract": _contract(MONITOR_SAMPLE_SURFACE),
            "sample_id": f"sample_{sample_time.replace('-', '').replace(':', '')}_{uuid4().hex[:8]}",
            "sampled_at": sample_time,
            "runtime_url": runtime_url,
            "source": source,
            "truth_level": "runtime_owned",
            "status": "sample_error",
            "error": error,
            "policy_boundaries": {
                "does_not_load_model": True,
                "does_not_generate": True,
                "does_not_abort_process": True,
            },
        }
        self._append_sample(sample)
        return sample

    def history(self, *, limit: int = 720, window_s: int | None = None) -> list[dict[str, Any]]:
        rows = self._read_all()
        if window_s is not None:
            cutoff = datetime.now(timezone.utc) - timedelta(seconds=window_s)
            rows = [
                row
                for row in rows
                if (sampled := _iso_to_datetime(row.get("sampled_at"))) is not None
                and sampled >= cutoff
            ]
        return rows[-max(1, limit):]

    def envelope(
        self,
        *,
        limit: int = 720,
        window_s: int | None = None,
        sampled_at: str | None = None,
    ) -> dict[str, Any]:
        rows = self.history(limit=limit, window_s=window_s)
        return {
            "contract": _contract(MONITOR_HISTORY_SURFACE),
            "sampled_at": sampled_at or _now_iso_utc(),
            "status": "available" if rows else "empty",
            "ledger_status": "available",
            "ledger_path": str(self._path),
            "history_count": len(rows),
            "limit": limit,
            "window_s": window_s,
            "samples": rows,
            "retention": {
                "max_rows": self._max_rows,
                "storage": "rolling_jsonl",
            },
            "metrics_catalog": [
                "service.readiness",
                "service.health_classification",
                "resources.host_free_percent",
                "resources.host_free_gb",
                "resources.available_gb",
                "resources.budget_utilization_pct",
                "workload.queue_size",
                "workload.longest_execution_s",
                "test_runs.known_run_count",
                "release_candidates.history_count",
            ],
            "policy_boundaries": {
                "read_only": True,
                "runtime_owned_history": True,
                "does_not_load_model": True,
                "does_not_generate": True,
                "does_not_abort_process": True,
            },
        }

    def _append_sample(self, sample: Mapping[str, Any]) -> None:
        snapshot = dict(sample)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._lock:
            with self._path.open("a", encoding="utf-8") as stream:
                stream.write(json.dumps(snapshot, sort_keys=True))
                stream.write("\n")
            self._compact_if_needed_locked()

    def _read_all(self) -> list[dict[str, Any]]:
        if not self._path.exists():
            return []
        rows: list[dict[str, Any]] = []
        with self._lock:
            with self._path.open("r", encoding="utf-8") as stream:
                for line in stream:
                    stripped = line.strip()
                    if not stripped:
                        continue
                    try:
                        payload = json.loads(stripped)
                    except json.JSONDecodeError:
                        continue
                    if isinstance(payload, Mapping):
                        rows.append(dict(payload))
        rows.sort(key=lambda row: str(row.get("sampled_at") or ""))
        return rows

    def _compact_if_needed_locked(self) -> None:
        if not self._path.exists():
            return
        with self._path.open("r", encoding="utf-8") as stream:
            lines = [line for line in stream if line.strip()]
        if len(lines) <= self._max_rows + 100:
            return
        suffix = lines[-self._max_rows :]
        tmp_path = self._path.with_suffix(self._path.suffix + ".tmp")
        with tmp_path.open("w", encoding="utf-8") as stream:
            stream.writelines(suffix)
        tmp_path.replace(self._path)


def _health_classification(runtime_status: Mapping[str, Any]) -> str:
    summary = _mapping(runtime_status.get("summary"))
    backend = _mapping(runtime_status.get("backend"))
    backend_detail = _mapping(backend.get("detail"))
    backend_healthy = bool(summary.get("backend_healthy", backend.get("healthy")))
    readiness = str(summary.get("readiness") or "")
    active_model_id = runtime_status.get("active_model_id")
    model_count = int(_mapping(runtime_status.get("inventory")).get("model_count") or 0)
    backend_error = backend_detail.get("last_error")
    if (
        backend_healthy
        and readiness == "degraded"
        and active_model_id is None
        and model_count == 0
        and backend_error is None
    ):
        return "healthy_clean_idle"
    if backend_healthy and readiness == "ready":
        return "healthy_serving"
    if backend_healthy:
        return "degraded"
    return "unhealthy"


def _release_candidate_summary(
    *,
    records: list[Mapping[str, Any]],
    ledger_status: str,
    ledger_path: str | None,
) -> dict[str, Any]:
    latest = _latest_records_by_model(records)
    latest_by_model: dict[str, dict[str, Any]] = {}
    for model_id, record in latest.items():
        latest_by_model[model_id] = {
            "model_id": model_id,
            "created_at": record.get("created_at"),
            "verdict": record.get("verdict"),
            "blockers": list(record.get("blockers") or []),
            "quality_caveats": list(record.get("quality_caveats") or []),
            "evidence_path": record.get("owlops_observation_path"),
            "first_token_latency_ms": record.get("first_token_latency_ms"),
            "ttft_ms": record.get("ttft_ms"),
            "decode_tokens_per_second": record.get("decode_tokens_per_second"),
            "tokens_per_second": record.get("tokens_per_second"),
            "post_run_health": record.get("post_run_health"),
            "memory_peak_source": record.get("memory_peak_source"),
        }
    return {
        "ledger_status": ledger_status,
        "ledger_path": ledger_path,
        "history_count": len(records),
        "latest_model_count": len(latest_by_model),
        "latest_by_model": latest_by_model,
        "latest_records": list(latest_by_model.values()),
        "truth_level": "runtime_owned" if ledger_status != "not_connected" else "unsupported",
    }


def build_monitor_snapshot(
    *,
    runtime_status: Mapping[str, Any],
    runtime_url: str,
    visibility_contract: Mapping[str, Any] | None,
    model_load_admission: Mapping[str, Any] | None,
    model_release_candidate_records: list[Mapping[str, Any]] | None,
    model_release_candidate_ledger_status: str,
    model_release_candidate_ledger_path: str | None,
    test_runs: Mapping[str, Any] | None = None,
    test_run_audit_ledger_status: str = "unsupported",
    test_run_audit_ledger_path: str | None = None,
    sampled_at: str | None = None,
) -> dict[str, Any]:
    """Build a normalized monitor snapshot from existing runtime truth."""

    sampled = sampled_at or _now_iso_utc()
    status = _mapping(runtime_status)
    summary = _mapping(status.get("summary"))
    backend = _mapping(status.get("backend"))
    backend_detail = _mapping(backend.get("detail"))
    inventory = _mapping(status.get("inventory"))
    budget = _mapping(status.get("budget"))
    health = _mapping(status.get("health"))
    generation_gate = _mapping(status.get("generation_gate"))
    host_pressure = _mapping(status.get("host_pressure"))
    load_failure = _mapping(status.get("load_failure"))
    cooldown = _mapping(status.get("memory_pressure_cooldown"))
    reclaim_barrier = _mapping(status.get("reclaim_barrier"))
    restart = _mapping(status.get("restart"))
    active_run = _active_test_run(test_runs)
    health_classification = _health_classification(status)
    visible_model_ids = _visible_model_ids(visibility_contract)
    admission = _mapping(model_load_admission)
    records = list(model_release_candidate_records or [])

    service = {
        "runtime": "owlmlx",
        "runtime_url": runtime_url,
        "port": _port_from_url(runtime_url),
        "ok": bool(summary.get("backend_healthy", backend.get("healthy"))),
        "readiness": summary.get("readiness") or health.get("readiness"),
        "health_classification": health_classification,
        "clean_idle_degraded": health_classification == "healthy_clean_idle",
        "active_model_id": status.get("active_model_id"),
        "model_count": inventory.get("model_count", summary.get("model_count", 0)),
        "listener": {"status": "live_http", "process_identity": "unsupported"},
        "staleness": {"status": "sampled_now", "staleness_ms": 0},
    }
    workload = {
        "active_run_id": active_run.get("run_id") if active_run else None,
        "generation_gate": generation_gate.get("generation_gate", "unknown"),
        "queue_size": generation_gate.get("waiters"),
        "queue_policy": generation_gate.get("queue_policy"),
        "longest_execution_s": generation_gate.get("longest_exec_s"),
        "total_served": generation_gate.get("total_served"),
        "current_phase": active_run.get("phase") if active_run else "idle",
        "block_reason": health.get("block_reason"),
    }
    release_candidates = _release_candidate_summary(
        records=records,
        ledger_status=model_release_candidate_ledger_status,
        ledger_path=model_release_candidate_ledger_path,
    )
    run_entries = _test_run_entries(test_runs)
    return {
        "contract": _contract(MONITOR_SNAPSHOT_SURFACE),
        "sampled_at": sampled,
        "runtime_url": runtime_url,
        "service": service,
        "backend": {
            "backend_name": backend.get("backend_name"),
            "healthy": backend.get("healthy"),
            "persistent_child": backend_detail.get("persistent_child", False),
            "child_health": backend_detail.get("child_health", {}),
            "backend_error": backend_detail.get("last_error"),
            "last_failure_class": backend_detail.get("last_failure_class"),
            "loaded_models": list(backend.get("loaded_models") or []),
            "unsupported_fields": ["process_identity"],
        },
        "models": {
            "active_model_id": status.get("active_model_id"),
            "model_count": inventory.get("model_count", 0),
            "loaded_models": list(backend.get("loaded_models") or []),
            "visible_model_ids": visible_model_ids,
            "model_visibility": _mapping(visibility_contract),
            "model_load_admission_summary": _mapping(admission.get("summary")),
        },
        "workload": workload,
        "resources": {
            "budget": budget,
            "loaded_gb": budget.get("loaded_gb"),
            "available_gb": budget.get("available_gb"),
            "host_pressure": host_pressure,
            "cooldown": cooldown,
            "pressure_classification": host_pressure.get("classification", "unknown"),
        },
        "recovery": {
            "load_failure": load_failure,
            "reclaim_barrier": reclaim_barrier,
            "restartability": restart,
            "termination_recovery": {"status": "unsupported"},
        },
        "release_candidates": release_candidates,
        "test_runs": {
            "status": "partial",
            "active_run_id": active_run.get("run_id") if active_run else None,
            "known_run_count": len(run_entries),
            "recent_runs": run_entries[-20:],
            "audit_ledger_status": test_run_audit_ledger_status,
            "audit_ledger_path": test_run_audit_ledger_path,
            "policy_boundaries": {
                "does_not_launch_from_snapshot": True,
                "audit_ledger_not_wired": test_run_audit_ledger_status == "not_connected",
            },
        },
        "sources": [
            _source(
                name="healthz",
                route_or_file="/healthz",
                sampled_at=sampled,
                status="available",
                truth_level="runtime_owned",
            ),
            _source(
                name="runtime_status",
                route_or_file="/v1/runtime/status",
                sampled_at=sampled,
                status="available",
                truth_level="runtime_owned",
            ),
            _source(
                name="model_visibility",
                route_or_file="/v1/runtime/model-visibility",
                sampled_at=sampled,
                status="available" if visibility_contract else "unknown",
                truth_level="runtime_owned",
            ),
            _source(
                name="model_load_admission",
                route_or_file="/v1/runtime/model-load-admission",
                sampled_at=sampled,
                status=_mapping(admission.get("summary")).get("ledger_status", "unknown"),
                truth_level="runtime_owned",
            ),
            _source(
                name="model_release_candidate_ledger",
                route_or_file=model_release_candidate_ledger_path,
                sampled_at=sampled,
                status=model_release_candidate_ledger_status,
                truth_level=release_candidates["truth_level"],
            ),
            _source(
                name="runtime_test_runs",
                route_or_file="in_memory_first_slice",
                sampled_at=sampled,
                status="partial",
                truth_level="runtime_owned",
            ),
        ],
    }


def _profile_accepts_model(profile: Mapping[str, Any], model_id: str) -> bool:
    requested = model_id.casefold()
    return requested in {str(item).casefold() for item in profile.get("model_ids", ())}


def _selected_profile(profile_id: str) -> dict[str, Any] | None:
    profile = TEST_PROFILE_CATALOG.get(profile_id)
    return dict(profile) if profile is not None else None


def _preflight_decision(
    *,
    profile: Mapping[str, Any] | None,
    model_id: str,
    active_run: Mapping[str, Any] | None,
    generation_gate: Mapping[str, Any],
    backend_healthy: bool,
    visibility: Mapping[str, Any],
    admission_entry: Mapping[str, Any] | None,
    host_pressure: Mapping[str, Any],
) -> tuple[str, str]:
    if profile is None:
        return "reject", "unknown_test_profile"
    if not _profile_accepts_model(profile, model_id):
        return "reject", "profile_model_mismatch"
    if active_run is not None:
        return "defer", "active_test_run_in_progress"
    if generation_gate.get("generation_gate") == "active" or int(generation_gate.get("waiters") or 0) > 0:
        return "defer", "generation_gate_busy"
    if not backend_healthy:
        return "reject", "backend_unhealthy"
    if visibility.get("status") == "blocked":
        return "reject", "model_not_visible"
    if visibility.get("status") != "visible":
        return "unknown", "model_visibility_truth_absent"
    host_pressure_class = str(host_pressure.get("classification") or "unknown")
    if host_pressure_class == "host_pressure_block":
        return "reject", "host_pressure_admission_barrier_active"
    if host_pressure_class == "host_pressure_warn":
        return "defer", "host_pressure_warning_threshold_reached"
    if host_pressure_class in {"unknown", "not_sampled"}:
        return "unknown", "host_pressure_sample_missing"
    if admission_entry is None:
        return "unknown", "model_load_admission_truth_absent"
    admission_decision = str(admission_entry.get("admission_decision") or "unknown")
    reason_code = str(admission_entry.get("reason_code") or "model_load_admission_unknown")
    if admission_decision == "blocked":
        return "reject", reason_code
    if admission_decision == "warn":
        return "defer", reason_code
    if admission_decision == "unknown":
        return "unknown", reason_code
    if admission_decision in {"admit", "already_loaded"}:
        return "admit", reason_code
    return "unknown", "model_load_admission_truth_absent"


def build_test_run_preflight(
    *,
    request_payload: Mapping[str, Any],
    runtime_status: Mapping[str, Any],
    visibility_contract: Mapping[str, Any] | None,
    model_load_admission: Mapping[str, Any] | None,
    test_runs: Mapping[str, Any] | None = None,
    runtime_url: str = "http://127.0.0.1:8066",
    sampled_at: str | None = None,
) -> dict[str, Any]:
    """Build a read-only test-run preflight result."""

    sampled = sampled_at or _now_iso_utc()
    status = _mapping(runtime_status)
    model_id = str(request_payload.get("model_id") or "")
    profile_id = str(request_payload.get("test_profile_id") or "")
    mode = str(request_payload.get("mode") or "dry_run")
    parameters = _mapping(request_payload.get("parameters"))
    selected_profile = _selected_profile(profile_id)
    active_run = _active_test_run(test_runs)
    summary = _mapping(status.get("summary"))
    backend = _mapping(status.get("backend"))
    generation_gate = _mapping(status.get("generation_gate"))
    host_pressure = _mapping(status.get("host_pressure"))
    visibility = _visibility_status(
        model_id=model_id,
        visibility_contract=visibility_contract,
    )
    admission_entry = _admission_entry(
        model_id=model_id,
        model_load_admission=model_load_admission,
    )
    backend_healthy = bool(summary.get("backend_healthy", backend.get("healthy")))
    decision, reason = _preflight_decision(
        profile=selected_profile,
        model_id=model_id,
        active_run=active_run,
        generation_gate=generation_gate,
        backend_healthy=backend_healthy,
        visibility=visibility,
        admission_entry=admission_entry,
        host_pressure=host_pressure,
    )
    estimated_memory = parameters.get("memory_gb")
    if estimated_memory is None and selected_profile is not None:
        estimated_memory = selected_profile.get("estimated_memory_gb")
    return {
        "contract": _contract(TEST_RUN_PREFLIGHT_SURFACE),
        "sampled_at": sampled,
        "runtime_url": runtime_url,
        "decision": decision,
        "reason": reason,
        "service_readiness": {
            "backend_healthy": backend_healthy,
            "readiness": summary.get("readiness") or _mapping(status.get("health")).get("readiness"),
            "health_classification": _health_classification(status),
        },
        "active_run_state": {
            "has_active_run": active_run is not None,
            "run_id": active_run.get("run_id") if active_run else None,
            "status": active_run.get("status") if active_run else "idle",
            "phase": active_run.get("phase") if active_run else "idle",
        },
        "model_visibility": visibility,
        "model_load_admission": dict(admission_entry) if admission_entry is not None else {
            "status": "unknown",
            "reason": "model_load_admission_truth_absent",
        },
        "host_pressure": host_pressure,
        "serving_budget": _mapping(status.get("budget")),
        "generation_gate": generation_gate,
        "estimated_memory_gb": estimated_memory,
        "selected_profile": selected_profile or {
            "profile_id": profile_id,
            "status": "unsupported",
        },
        "would_write_evidence_to": (
            "files/evidence/owlmlx/runtime-test-runs/"
            f"{profile_id or 'unknown-profile'}/{model_id or 'unknown-model'}"
        ),
        "required_operator_confirmation": {
            "required": mode == "live",
            "reason": "live_runtime_test_launch" if mode == "live" else "not_required_for_preflight",
        },
        "policy_boundaries": {
            "read_only": True,
            "does_not_load_model": True,
            "does_not_generate": True,
            "does_not_abort": True,
            "unknown_when_truth_source_absent": True,
        },
    }


def build_test_run_index(
    *,
    test_runs: Mapping[str, Any] | list[Mapping[str, Any]] | None = None,
    audit_ledger_status: str = "unsupported",
    audit_ledger_path: str | None = None,
    sampled_at: str | None = None,
) -> dict[str, Any]:
    sampled = sampled_at or _now_iso_utc()
    runs = _test_run_entries(test_runs)
    return {
        "contract": _contract(TEST_RUN_INDEX_SURFACE),
        "sampled_at": sampled,
        "status": "partial",
        "runs": runs[-50:],
        "audit_ledger_status": audit_ledger_status,
        "audit_ledger_path": audit_ledger_path,
        "policy_boundaries": {"read_only": True},
    }


def build_test_run_status(
    *,
    run_id: str,
    test_runs: Mapping[str, Any] | list[Mapping[str, Any]] | None = None,
    sampled_at: str | None = None,
) -> dict[str, Any]:
    sampled = sampled_at or _now_iso_utc()
    run: dict[str, Any] | None = None
    for entry in reversed(_test_run_entries(test_runs)):
        if entry.get("run_id") == run_id:
            run = entry
            break
    if run is None:
        return {
            "contract": _contract(TEST_RUN_STATUS_SURFACE),
            "sampled_at": sampled,
            "status": "not_found",
            "run_id": run_id,
            "reason": "runtime_test_run_not_found",
        }
    return {
        "contract": _contract(TEST_RUN_STATUS_SURFACE),
        "sampled_at": sampled,
        "status": run.get("status", "unknown"),
        "run": dict(run),
    }


def build_test_run_events(
    *,
    run_id: str,
    test_runs: Mapping[str, Any] | list[Mapping[str, Any]] | None = None,
    sampled_at: str | None = None,
) -> dict[str, Any]:
    sampled = sampled_at or _now_iso_utc()
    status = build_test_run_status(
        run_id=run_id,
        test_runs=test_runs,
        sampled_at=sampled,
    )
    if status.get("status") == "not_found":
        return {
            "contract": _contract(TEST_RUN_EVENT_SURFACE),
            "sampled_at": sampled,
            "status": "not_found",
            "run_id": run_id,
            "reason": "runtime_test_run_not_found",
            "events": [],
        }
    run = _mapping(status.get("run"))
    events = _list_of_mappings(run.get("events"))
    return {
        "contract": _contract(TEST_RUN_EVENT_SURFACE),
        "sampled_at": sampled,
        "status": "available",
        "run_id": run_id,
        "events": events,
        "event_count": len(events),
        "stream_mode": "finite_replay",
    }


def unsupported_operation_payload(
    *,
    surface: str,
    unsupported_feature: str,
    reason: str,
    run_id: str | None = None,
    sampled_at: str | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "contract": _contract(surface),
        "sampled_at": sampled_at or _now_iso_utc(),
        "status": "unsupported",
        "unsupported_feature": unsupported_feature,
        "reason": reason,
        "policy_boundaries": {
            "does_not_load_model": True,
            "does_not_generate": True,
            "does_not_abort_process": True,
            "does_not_touch_legacy_listeners": ["8001", "8009"],
        },
    }
    if run_id is not None:
        payload["run_id"] = run_id
    return payload


__all__ = [
    "MONITOR_EVENT_SURFACE",
    "MONITOR_HISTORY_SURFACE",
    "MONITOR_SAMPLE_SURFACE",
    "MONITOR_SNAPSHOT_SURFACE",
    "RUNTIME_MONITOR_VERSION",
    "RuntimeMonitorTrendRegistry",
    "RuntimeTestRunRegistry",
    "TERMINAL_TEST_RUN_STATUSES",
    "TEST_PROFILE_CATALOG",
    "TEST_RUN_ABORT_SURFACE",
    "TEST_RUN_AUDIT_ROW_SURFACE",
    "TEST_RUN_EVENT_SURFACE",
    "TEST_RUN_INDEX_SURFACE",
    "TEST_RUN_LAUNCH_SURFACE",
    "TEST_RUN_PREFLIGHT_SURFACE",
    "TEST_RUN_STATUS_SURFACE",
    "build_monitor_sample",
    "build_monitor_snapshot",
    "build_test_run_index",
    "build_test_run_events",
    "build_test_run_preflight",
    "build_test_run_status",
    "unsupported_operation_payload",
]
