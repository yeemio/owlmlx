"""Runtime-owned cache/scheduler depth status for owlmlx."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from .cache_truth import (
    CacheFlags,
    CacheProfileSnapshot,
    TurboQuantCacheSafety,
    cache_profile_snapshot,
    cache_profile_snapshot_to_dict,
    normalize_cache_flags,
    turboquant_cache_safety,
    turboquant_cache_safety_to_dict,
)
from .serving import GenerationGate


@dataclass(frozen=True, slots=True)
class CacheSchedulerStatus:
    """Stable runtime-owned status for current cache/scheduler depth."""

    cache_profile: CacheProfileSnapshot
    turboquant_safety: TurboQuantCacheSafety
    scheduler_status: dict[str, Any]
    status: str
    scheduler_depth: str
    cache_depth: str
    blocked_reason: str | None
    recommended_next_step: str


def build_cache_scheduler_status(
    *,
    gate: GenerationGate | None = None,
    configured_flags: CacheFlags | Mapping[str, Any] | None = None,
    runtime_profile: str | None = None,
    runtime_flags: CacheFlags | Mapping[str, Any] | None = None,
    bits_in_cache_key: bool = False,
    invalidates_on_config_toggle: bool = False,
    runtime_verified: bool = False,
) -> CacheSchedulerStatus:
    """Build the current runtime-owned cache/scheduler status."""

    active_gate = gate if gate is not None else GenerationGate()
    snapshot = cache_profile_snapshot(
        configured_flags=configured_flags,
        runtime_profile=runtime_profile,
        runtime_flags=runtime_flags,
    )
    safety = turboquant_cache_safety(
        bits_in_cache_key=bits_in_cache_key,
        invalidates_on_config_toggle=invalidates_on_config_toggle,
        runtime_verified=runtime_verified,
    )
    scheduler_status = dict(active_gate.status)

    configured = normalize_cache_flags(configured_flags)
    runtime_cache_visible = runtime_flags is not None or runtime_profile is not None
    cache_depth = "truth_only"
    if configured.enabled or runtime_cache_visible:
        cache_depth = "profile_visible"

    return CacheSchedulerStatus(
        cache_profile=snapshot,
        turboquant_safety=safety,
        scheduler_status=scheduler_status,
        status="partial",
        scheduler_depth="serial_single_worker",
        cache_depth=cache_depth,
        blocked_reason=(
            "runtime-owned cache reuse, eviction, and deeper scheduler behavior remain below reference-grade closure"
        ),
        recommended_next_step=(
            "add runtime-owned cache residency/reuse evidence before claiming deeper cache/scheduler parity"
        ),
    )


def cache_scheduler_status_to_dict(status: CacheSchedulerStatus) -> dict[str, Any]:
    """Serialize cache/scheduler depth status."""

    return {
        "contract": {
            "surface": "owlmlx.cache_scheduler_status",
            "version": "phase45",
            "stable_sections": [
                "summary",
                "scheduler",
                "cache_profile",
                "turboquant_cache_safety",
            ],
        },
        "summary": {
            "status": status.status,
            "scheduler_depth": status.scheduler_depth,
            "cache_depth": status.cache_depth,
            "blocked_reason": status.blocked_reason,
            "recommended_next_step": status.recommended_next_step,
        },
        "scheduler": {
            "mode": "serial_single_worker",
            "continuous_batching": False,
            **status.scheduler_status,
        },
        "cache_profile": cache_profile_snapshot_to_dict(status.cache_profile),
        "turboquant_cache_safety": turboquant_cache_safety_to_dict(
            status.turboquant_safety
        ),
    }

