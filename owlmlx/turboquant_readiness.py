"""Runtime-owned TurboQuant safety/readiness for owlmlx."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from .cache_repeatability_evidence import (
    CacheRepeatabilityEvidence,
    build_cache_repeatability_evidence,
    cache_repeatability_evidence_to_dict,
)
from .cache_truth import (
    TurboQuantCacheSafety,
    turboquant_cache_safety,
    turboquant_cache_safety_to_dict,
)


@dataclass(frozen=True, slots=True)
class TurboQuantReadiness:
    """Stable runtime-owned TurboQuant readiness decision."""

    safety: TurboQuantCacheSafety
    repeatability: CacheRepeatabilityEvidence
    bits_in_cache_key: bool
    invalidates_on_config_toggle: bool
    runtime_verified: bool
    status: str
    ready: bool
    blocked_reason: str | None
    recommended_next_step: str


def _coerce_repeatability(
    repeatability: CacheRepeatabilityEvidence | Mapping[str, Any] | None,
) -> CacheRepeatabilityEvidence:
    if isinstance(repeatability, CacheRepeatabilityEvidence):
        return repeatability
    if repeatability is None:
        return build_cache_repeatability_evidence([])
    summary = repeatability.get("summary")
    run_counts = repeatability.get("run_counts")
    if isinstance(summary, Mapping) and isinstance(run_counts, Mapping):
        return CacheRepeatabilityEvidence(
            runs_observed=int(run_counts.get("runs_observed", 0)),
            runs_with_runtime_activity=int(run_counts.get("runs_with_runtime_activity", 0)),
            runs_with_residency_signal=int(run_counts.get("runs_with_residency_signal", 0)),
            runs_with_reuse_signal=int(run_counts.get("runs_with_reuse_signal", 0)),
            runs_with_eviction_signal=int(run_counts.get("runs_with_eviction_signal", 0)),
            backend_reuse_counter=int(run_counts.get("backend_reuse_counter", 0)),
            runtime_path_observed=bool(run_counts.get("runtime_path_observed", False)),
            repeated_generation_models=tuple(
                str(model_id)
                for model_id in run_counts.get("repeated_generation_models", [])
            ),
            highest_evidence_status=str(
                summary.get("highest_evidence_status", "no_runtime_evidence")
            ),
            status=str(summary.get("status", "partial")),
            repeatability_status=str(
                summary.get("repeatability_status", "no_repeat_runs")
            ),
            blocked_reason=summary.get("blocked_reason"),
            recommended_next_step=str(
                summary.get(
                    "recommended_next_step",
                    "collect repeated-serving reuse or eviction evidence from real runtime activity",
                )
            ),
        )
    return build_cache_repeatability_evidence([], backend_status=repeatability)


def build_turboquant_readiness(
    *,
    bits_in_cache_key: bool = False,
    invalidates_on_config_toggle: bool = False,
    runtime_verified: bool = False,
    repeatability: CacheRepeatabilityEvidence | Mapping[str, Any] | None = None,
) -> TurboQuantReadiness:
    """Build runtime-owned TurboQuant readiness."""

    safety = turboquant_cache_safety(
        bits_in_cache_key=bits_in_cache_key,
        invalidates_on_config_toggle=invalidates_on_config_toggle,
        runtime_verified=runtime_verified,
    )
    repeatability_evidence = _coerce_repeatability(repeatability)

    if not safety.can_activate:
        return TurboQuantReadiness(
            safety=safety,
            repeatability=repeatability_evidence,
            bits_in_cache_key=bits_in_cache_key,
            invalidates_on_config_toggle=invalidates_on_config_toggle,
            runtime_verified=runtime_verified,
            status="safety_blocked",
            ready=False,
            blocked_reason=(
                "TurboQuant remains safety-blocked until cache keys, invalidation, and runtime verification are all satisfied"
            ),
            recommended_next_step=(
                "verify cache-key isolation, cache invalidation on config toggle, and runtime support before controlled TurboQuant validation"
            ),
        )

    if repeatability_evidence.repeatability_status in {
        "repeat_reuse_visible",
        "repeat_eviction_visible",
    }:
        return TurboQuantReadiness(
            safety=safety,
            repeatability=repeatability_evidence,
            bits_in_cache_key=bits_in_cache_key,
            invalidates_on_config_toggle=invalidates_on_config_toggle,
            runtime_verified=runtime_verified,
            status="ready_for_controlled_validation",
            ready=True,
            blocked_reason=None,
            recommended_next_step=(
                "run controlled TurboQuant validation on the cache-capable runtime path"
            ),
        )

    return TurboQuantReadiness(
        safety=safety,
        repeatability=repeatability_evidence,
        bits_in_cache_key=bits_in_cache_key,
        invalidates_on_config_toggle=invalidates_on_config_toggle,
        runtime_verified=runtime_verified,
        status="evidence_blocked",
        ready=False,
        blocked_reason=(
            "TurboQuant safety preconditions are satisfied, but repeated-serving cache evidence is still too shallow"
        ),
        recommended_next_step=(
            "collect repeated-serving reuse or eviction evidence before attempting controlled TurboQuant validation"
        ),
    )


def turboquant_readiness_to_dict(readiness: TurboQuantReadiness) -> dict[str, Any]:
    """Serialize runtime-owned TurboQuant readiness."""

    return {
        "contract": {
            "surface": "owlmlx.turboquant_readiness",
            "version": "phase45",
            "stable_sections": [
                "summary",
                "turboquant_cache_safety",
                "cache_repeatability",
            ],
        },
        "summary": {
            "status": readiness.status,
            "ready": readiness.ready,
            "blocked_reason": readiness.blocked_reason,
            "recommended_next_step": readiness.recommended_next_step,
        },
        "turboquant_cache_safety": turboquant_cache_safety_to_dict(readiness.safety),
        "preconditions": {
            "bits_in_cache_key": readiness.bits_in_cache_key,
            "invalidates_on_config_toggle": readiness.invalidates_on_config_toggle,
            "runtime_verified": readiness.runtime_verified,
        },
        "cache_repeatability": cache_repeatability_evidence_to_dict(
            readiness.repeatability
        )["summary"],
    }
