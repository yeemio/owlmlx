"""Runtime-owned cache residency/reuse evidence for owlmlx."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from .cache_truth import (
    CacheFlags,
    CacheProfile,
    CacheProfileSnapshot,
    cache_profile_snapshot,
    cache_profile_snapshot_to_dict,
    normalize_cache_flags,
)
from .serving import GenerationGate


@dataclass(frozen=True, slots=True)
class CacheResidencyMetrics:
    """Optional runtime-visible cache evidence metrics."""

    entries: int | None = None
    resident_bytes: int | None = None
    reuse_events: int | None = None
    hit_count: int | None = None
    eviction_events: int | None = None


@dataclass(frozen=True, slots=True)
class CacheResidencyEvidence:
    """Stable runtime-owned evidence for current cache residency/reuse."""

    cache_profile: CacheProfileSnapshot
    requests_served: int
    metrics: CacheResidencyMetrics
    status: str
    evidence_status: str
    blocked_reason: str | None
    recommended_next_step: str


def normalize_cache_residency_metrics(
    raw: CacheResidencyMetrics | Mapping[str, Any] | None,
) -> CacheResidencyMetrics:
    """Normalize optional cache evidence metrics from dict-like inputs."""

    if isinstance(raw, CacheResidencyMetrics):
        return raw
    if raw is None:
        return CacheResidencyMetrics()

    def _int(name: str) -> int | None:
        value = raw.get(name)
        if value is None:
            return None
        return int(value)

    return CacheResidencyMetrics(
        entries=_int("entries"),
        resident_bytes=_int("resident_bytes"),
        reuse_events=_int("reuse_events"),
        hit_count=_int("hit_count"),
        eviction_events=_int("eviction_events"),
    )


def build_cache_residency_evidence(
    *,
    gate: GenerationGate | None = None,
    configured_flags: CacheFlags | Mapping[str, Any] | None = None,
    runtime_profile: str | None = None,
    runtime_flags: CacheFlags | Mapping[str, Any] | None = None,
    metrics: CacheResidencyMetrics | Mapping[str, Any] | None = None,
) -> CacheResidencyEvidence:
    """Build runtime-owned cache residency/reuse evidence."""

    active_gate = gate if gate is not None else GenerationGate()
    snapshot = cache_profile_snapshot(
        configured_flags=configured_flags,
        runtime_profile=runtime_profile,
        runtime_flags=runtime_flags,
    )
    normalized_metrics = normalize_cache_residency_metrics(metrics)
    requests_served = int(active_gate.status.get("total_served", 0))

    runtime_active = (
        snapshot.runtime_profile is CacheProfile.cache_enabled
        and snapshot.restart_required is False
    )
    reuse_visible = (normalized_metrics.reuse_events or 0) > 0 or (
        normalized_metrics.hit_count or 0
    ) > 0
    residency_visible = (
        (normalized_metrics.entries or 0) > 0
        or (normalized_metrics.resident_bytes or 0) > 0
        or (normalized_metrics.eviction_events or 0) > 0
    )

    evidence_status = "no_runtime_evidence"
    blocked_reason = (
        "runtime-owned cache residency and reuse evidence remain below replacement-grade closure"
    )
    recommended_next_step = (
        "add runtime-owned reuse or residency counters from repeated serving before claiming deeper cache closure"
    )

    configured = normalize_cache_flags(configured_flags)
    runtime_visible = runtime_flags is not None or runtime_profile is not None

    if reuse_visible:
        evidence_status = "reuse_signal_visible"
        blocked_reason = (
            "runtime-owned reuse signals are visible, but deeper eviction policy and scheduler depth remain below reference-grade closure"
        )
        recommended_next_step = (
            "add eviction and repeated-serving cache evidence before claiming broader cache/scheduler parity"
        )
    elif residency_visible:
        evidence_status = "residency_signal_visible"
        blocked_reason = (
            "runtime-owned residency is visible, but explicit reuse evidence is still missing"
        )
        recommended_next_step = (
            "add runtime-owned reuse counters or hit evidence before claiming deeper cache closure"
        )
    elif runtime_active and requests_served > 0:
        evidence_status = "profile_active_under_load"
        blocked_reason = (
            "cache-capable runtime profile has served requests, but residency/reuse signals are not yet runtime-visible"
        )
        recommended_next_step = (
            "add runtime-owned residency or reuse counters while the cache-enabled profile is active"
        )
    elif configured.enabled or runtime_visible:
        evidence_status = "configuration_only"
        blocked_reason = (
            "cache profile visibility exists, but runtime-owned serving evidence is still missing"
        )
        recommended_next_step = (
            "collect repeated-serving evidence under the visible cache profile before claiming deeper cache closure"
        )

    return CacheResidencyEvidence(
        cache_profile=snapshot,
        requests_served=requests_served,
        metrics=normalized_metrics,
        status="partial",
        evidence_status=evidence_status,
        blocked_reason=blocked_reason,
        recommended_next_step=recommended_next_step,
    )


def cache_residency_metrics_to_dict(metrics: CacheResidencyMetrics) -> dict[str, Any]:
    """Serialize cache evidence metrics."""

    return {
        "entries": metrics.entries,
        "resident_bytes": metrics.resident_bytes,
        "reuse_events": metrics.reuse_events,
        "hit_count": metrics.hit_count,
        "eviction_events": metrics.eviction_events,
    }


def cache_residency_evidence_to_dict(
    evidence: CacheResidencyEvidence,
) -> dict[str, Any]:
    """Serialize runtime-owned cache residency/reuse evidence."""

    return {
        "contract": {
            "surface": "owlmlx.cache_residency_evidence",
            "version": "phase45",
            "stable_sections": [
                "summary",
                "cache_profile",
                "scheduler_activity",
                "residency_metrics",
            ],
        },
        "summary": {
            "status": evidence.status,
            "evidence_status": evidence.evidence_status,
            "blocked_reason": evidence.blocked_reason,
            "recommended_next_step": evidence.recommended_next_step,
        },
        "cache_profile": cache_profile_snapshot_to_dict(evidence.cache_profile),
        "scheduler_activity": {
            "requests_served": evidence.requests_served,
        },
        "residency_metrics": cache_residency_metrics_to_dict(evidence.metrics),
    }
