"""Runtime-owned repeated-serving cache evidence for owlmlx."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Protocol

from .cache_residency_evidence import (
    CacheResidencyEvidence,
    build_cache_residency_evidence,
)


class _BackendStatusLike(Protocol):
    detail: dict[str, Any]


@dataclass(frozen=True, slots=True)
class CacheRepeatabilityEvidence:
    """Stable runtime-owned evidence across repeated cache-serving runs."""

    runs_observed: int
    runs_with_runtime_activity: int
    runs_with_residency_signal: int
    runs_with_reuse_signal: int
    runs_with_eviction_signal: int
    backend_reuse_counter: int
    runtime_path_observed: bool
    repeated_generation_models: tuple[str, ...]
    highest_evidence_status: str
    status: str
    repeatability_status: str
    blocked_reason: str | None
    recommended_next_step: str


def _coerce_run(run: CacheResidencyEvidence | Mapping[str, Any]) -> CacheResidencyEvidence:
    if isinstance(run, CacheResidencyEvidence):
        return run

    summary = run.get("summary", {})
    cache_profile = run.get("cache_profile", {})
    metrics = run.get("residency_metrics", {})
    scheduler_activity = run.get("scheduler_activity", {})
    runtime_profile = cache_profile.get("runtime_profile")
    runtime_flags = cache_profile.get("runtime_flags")
    configured_flags = cache_profile.get("active_flags")
    normalized = build_cache_residency_evidence(
        configured_flags=configured_flags,
        runtime_profile=runtime_profile,
        runtime_flags=runtime_flags,
        metrics=metrics,
    )
    return CacheResidencyEvidence(
        cache_profile=normalized.cache_profile,
        requests_served=int(scheduler_activity.get("requests_served", 0)),
        metrics=normalized.metrics,
        status=str(summary.get("status", "partial")),
        evidence_status=str(summary.get("evidence_status", "no_runtime_evidence")),
        blocked_reason=summary.get("blocked_reason"),
        recommended_next_step=str(
            summary.get(
                "recommended_next_step",
                "add repeated-serving cache evidence before claiming deeper cache closure",
            )
        ),
    )


def _backend_detail(
    backend_status: _BackendStatusLike | Mapping[str, Any] | None,
) -> dict[str, Any]:
    if backend_status is None:
        return {}
    if not isinstance(backend_status, Mapping) and hasattr(backend_status, "detail"):
        detail = getattr(backend_status, "detail")
        if isinstance(detail, Mapping):
            return dict(detail)
    detail = backend_status.get("detail")
    if isinstance(detail, Mapping):
        return dict(detail)
    return {}


def build_cache_repeatability_evidence(
    runs: Iterable[CacheResidencyEvidence | Mapping[str, Any]],
    *,
    backend_status: _BackendStatusLike | Mapping[str, Any] | None = None,
) -> CacheRepeatabilityEvidence:
    """Build runtime-owned repeated-serving cache evidence."""

    coerced = tuple(_coerce_run(run) for run in runs)
    detail = _backend_detail(backend_status)
    runtime_observations = detail.get("cache_runtime_observations", {})
    repeated_generation_models = tuple(
        str(model_id)
        for model_id in runtime_observations.get("repeated_generation_models", [])
    )
    runtime_path_observed = bool(runtime_observations.get("persistent_child_reuse_visible"))
    backend_reuse_counter = int(runtime_observations.get("reuse_counter", 0) or 0)
    backend_reuse_visible = bool(
        runtime_observations.get("cache_counter_visibility", {}).get("reuse")
    ) or backend_reuse_counter > 0
    runs_observed = len(coerced)
    runs_with_runtime_activity = sum(1 for run in coerced if run.requests_served > 0)
    runs_with_residency_signal = sum(
        1
        for run in coerced
        if run.evidence_status in {"residency_signal_visible", "reuse_signal_visible"}
    )
    runs_with_reuse_signal = sum(
        1 for run in coerced if run.evidence_status == "reuse_signal_visible"
    )
    runs_with_eviction_signal = sum(
        1
        for run in coerced
        if (run.metrics.eviction_events or 0) > 0
    )

    status_rank = {
        "no_runtime_evidence": 0,
        "configuration_only": 1,
        "profile_active_under_load": 2,
        "residency_signal_visible": 3,
        "reuse_signal_visible": 4,
    }
    highest_evidence_status = "no_runtime_evidence"
    for run in coerced:
        if status_rank.get(run.evidence_status, -1) > status_rank[highest_evidence_status]:
            highest_evidence_status = run.evidence_status

    repeatability_status = "no_repeat_runs"
    blocked_reason = (
        "runtime-owned repeated-serving cache evidence is still below replacement-grade closure"
    )
    recommended_next_step = (
        "collect repeated-serving reuse or eviction evidence from real runtime activity"
    )

    if runs_with_eviction_signal > 0:
        repeatability_status = "repeat_eviction_visible"
        blocked_reason = (
            "repeated-serving eviction evidence is visible, but broader cache/scheduler closure remains below reference-grade parity"
        )
        recommended_next_step = (
            "connect eviction evidence to stronger runtime cache policy and reuse closure"
        )
    elif runs_with_reuse_signal >= 2 or backend_reuse_visible:
        repeatability_status = "repeat_reuse_visible"
        highest_evidence_status = max(
            (highest_evidence_status, "reuse_signal_visible"),
            key=lambda value: status_rank.get(value, -1),
        )
        blocked_reason = (
            "repeated-serving reuse evidence is visible, but eviction depth and broader scheduler closure remain open"
        )
        recommended_next_step = (
            "add repeated-serving eviction evidence before claiming broader cache/scheduler parity"
        )
    elif runs_with_residency_signal >= 2:
        repeatability_status = "repeat_residency_visible"
        blocked_reason = (
            "repeated-serving residency evidence is visible, but explicit repeated reuse evidence is still missing"
        )
        recommended_next_step = (
            "add repeated reuse or hit evidence across repeated runs before claiming deeper cache closure"
        )
    elif runs_with_runtime_activity >= 2:
        repeatability_status = "repeat_profile_active_under_load"
        blocked_reason = (
            "repeated-serving activity exists, but repeated residency/reuse evidence is not yet runtime-visible"
        )
        recommended_next_step = (
            "add repeated-serving residency or reuse counters while the cache-capable profile is active"
        )
    elif runtime_path_observed:
        repeatability_status = "runtime_activity_visible_counter_gap"
        highest_evidence_status = max(
            (highest_evidence_status, "profile_active_under_load"),
            key=lambda value: status_rank.get(value, -1),
        )
        blocked_reason = (
            "active runtime path shows repeated serving through persistent child reuse, but direct cache reuse/eviction counters are not yet runtime-owned"
        )
        recommended_next_step = (
            "add lightweight runtime-owned reuse or eviction counters to the active runtime path before claiming deeper cache closure"
        )

    return CacheRepeatabilityEvidence(
        runs_observed=runs_observed,
        runs_with_runtime_activity=runs_with_runtime_activity,
        runs_with_residency_signal=runs_with_residency_signal,
        runs_with_reuse_signal=runs_with_reuse_signal,
        runs_with_eviction_signal=runs_with_eviction_signal,
        backend_reuse_counter=backend_reuse_counter,
        runtime_path_observed=runtime_path_observed,
        repeated_generation_models=repeated_generation_models,
        highest_evidence_status=highest_evidence_status,
        status="partial",
        repeatability_status=repeatability_status,
        blocked_reason=blocked_reason,
        recommended_next_step=recommended_next_step,
    )


def cache_repeatability_evidence_to_dict(
    evidence: CacheRepeatabilityEvidence,
) -> dict[str, Any]:
    """Serialize runtime-owned repeated-serving cache evidence."""

    return {
        "contract": {
            "surface": "owlmlx.cache_repeatability_evidence",
            "version": "phase45",
            "stable_sections": [
                "summary",
                "run_counts",
            ],
        },
        "summary": {
            "status": evidence.status,
            "repeatability_status": evidence.repeatability_status,
            "highest_evidence_status": evidence.highest_evidence_status,
            "blocked_reason": evidence.blocked_reason,
            "recommended_next_step": evidence.recommended_next_step,
        },
        "run_counts": {
            "runs_observed": evidence.runs_observed,
            "runs_with_runtime_activity": evidence.runs_with_runtime_activity,
            "runs_with_residency_signal": evidence.runs_with_residency_signal,
            "runs_with_reuse_signal": evidence.runs_with_reuse_signal,
            "runs_with_eviction_signal": evidence.runs_with_eviction_signal,
            "backend_reuse_counter": evidence.backend_reuse_counter,
            "runtime_path_observed": evidence.runtime_path_observed,
            "repeated_generation_models": list(evidence.repeated_generation_models),
        },
    }
