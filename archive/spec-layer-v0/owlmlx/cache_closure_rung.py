"""Runtime-owned cache closure rung for owlmlx."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from .cache_repeatability_evidence import (
    CacheRepeatabilityEvidence,
    build_cache_repeatability_evidence,
    cache_repeatability_evidence_to_dict,
)
from .cache_residency_evidence import (
    CacheResidencyEvidence,
    build_cache_residency_evidence,
    cache_residency_evidence_to_dict,
)
from .cache_scheduler_status import (
    CacheSchedulerStatus,
    build_cache_scheduler_status,
    cache_scheduler_status_to_dict,
)
from .turboquant_readiness import (
    TurboQuantReadiness,
    build_turboquant_readiness,
    turboquant_readiness_to_dict,
)


@dataclass(frozen=True, slots=True)
class CacheClosureRung:
    """Stable runtime-owned cache closure summary."""

    scheduler: CacheSchedulerStatus
    residency: CacheResidencyEvidence
    repeatability: CacheRepeatabilityEvidence
    turboquant: TurboQuantReadiness
    status: str
    closure_rung: str
    blocked_reason: str | None
    recommended_next_step: str


def _scheduler(
    value: CacheSchedulerStatus | Mapping[str, Any] | None,
) -> CacheSchedulerStatus:
    if isinstance(value, CacheSchedulerStatus):
        return value
    return build_cache_scheduler_status()


def _residency(
    value: CacheResidencyEvidence | Mapping[str, Any] | None,
) -> CacheResidencyEvidence:
    if isinstance(value, CacheResidencyEvidence):
        return value
    if isinstance(value, Mapping):
        summary = value.get("summary")
        cache_profile = value.get("cache_profile")
        metrics = value.get("residency_metrics")
        scheduler_activity = value.get("scheduler_activity")
        if (
            isinstance(summary, Mapping)
            and isinstance(cache_profile, Mapping)
            and isinstance(metrics, Mapping)
            and isinstance(scheduler_activity, Mapping)
        ):
            normalized = build_cache_residency_evidence(
                configured_flags=cache_profile.get("active_flags"),
                runtime_profile=cache_profile.get("runtime_profile"),
                runtime_flags=cache_profile.get("runtime_flags"),
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
                        "add runtime-owned cache residency and reuse evidence before claiming deeper cache closure",
                    )
                ),
            )
    return build_cache_residency_evidence()


def _repeatability(
    value: CacheRepeatabilityEvidence | Mapping[str, Any] | None,
) -> CacheRepeatabilityEvidence:
    if isinstance(value, CacheRepeatabilityEvidence):
        return value
    if isinstance(value, Mapping):
        return build_cache_repeatability_evidence([], backend_status=value)
    return build_cache_repeatability_evidence([])


def _turboquant(
    value: TurboQuantReadiness | Mapping[str, Any] | None,
    *,
    repeatability: CacheRepeatabilityEvidence,
) -> TurboQuantReadiness:
    if isinstance(value, TurboQuantReadiness):
        return value
    if isinstance(value, Mapping):
        summary = value.get("summary")
        safety = value.get("turboquant_cache_safety")
        if isinstance(summary, Mapping) and isinstance(safety, Mapping):
            return build_turboquant_readiness(
                bits_in_cache_key=bool(safety.get("can_activate", False)),
                invalidates_on_config_toggle=bool(safety.get("can_activate", False)),
                runtime_verified=bool(safety.get("can_activate", False)),
                repeatability={
                    "summary": value.get("cache_repeatability", {}),
                    "run_counts": {
                        "runs_observed": repeatability.runs_observed,
                        "runs_with_runtime_activity": repeatability.runs_with_runtime_activity,
                        "runs_with_residency_signal": repeatability.runs_with_residency_signal,
                        "runs_with_reuse_signal": repeatability.runs_with_reuse_signal,
                        "runs_with_eviction_signal": repeatability.runs_with_eviction_signal,
                        "runtime_path_observed": repeatability.runtime_path_observed,
                        "repeated_generation_models": list(
                            repeatability.repeated_generation_models
                        ),
                    },
                },
            )
    return build_turboquant_readiness(repeatability=repeatability)


def build_cache_closure_rung(
    *,
    scheduler: CacheSchedulerStatus | Mapping[str, Any] | None = None,
    residency: CacheResidencyEvidence | Mapping[str, Any] | None = None,
    repeatability: CacheRepeatabilityEvidence | Mapping[str, Any] | None = None,
    turboquant: TurboQuantReadiness | Mapping[str, Any] | None = None,
) -> CacheClosureRung:
    """Build the current runtime-owned cache closure rung."""

    scheduler_status = _scheduler(scheduler)
    residency_evidence = _residency(residency)
    repeatability_evidence = _repeatability(repeatability)
    turboquant_readiness = _turboquant(
        turboquant,
        repeatability=repeatability_evidence,
    )

    closure_rung = "truth_only"
    blocked_reason = (
        "owlmlx still lacks runtime-owned cache evidence beyond truth surfaces"
    )
    recommended_next_step = (
        "promote cache residency or repeatability evidence before claiming a stronger cache closure level"
    )

    if residency_evidence.evidence_status != "no_runtime_evidence":
        closure_rung = "evidence_visible"
        blocked_reason = (
            "owlmlx has one-shot cache evidence, but repeated-serving closure is still below reference-grade depth"
        )
        recommended_next_step = (
            "promote repeated-serving cache evidence before claiming stronger cache closure"
        )

    if repeatability_evidence.repeatability_status != "no_repeat_runs":
        closure_rung = "repeatability_visible"
        blocked_reason = (
            "owlmlx now owns repeated-serving cache evidence, but direct runtime-owned reuse/eviction counters and deeper scheduler depth remain open"
        )
        recommended_next_step = (
            "freeze the exact counter gap or add lightweight runtime-owned reuse/eviction counters"
        )
    if repeatability_evidence.repeatability_status == "repeat_reuse_visible":
        blocked_reason = (
            "owlmlx now owns repeated-serving reuse evidence, but runtime-owned residency/eviction counters and deeper scheduler depth remain open"
        )
        recommended_next_step = (
            "freeze the exact remaining counter gap or add one more lightweight runtime-owned counter before claiming stronger cache closure"
        )
    if repeatability_evidence.repeatability_status == "repeat_eviction_visible":
        blocked_reason = (
            "owlmlx now owns repeated-serving reuse and eviction evidence, but scheduler depth and TurboQuant validation still remain below stronger closure"
        )
        recommended_next_step = (
            "advance scheduler depth or satisfy TurboQuant validation preconditions before claiming stronger cache closure"
        )

    if turboquant_readiness.status in {
        "evidence_blocked",
        "ready_for_controlled_validation",
    }:
        closure_rung = "turboquant_safety_ready"
        blocked_reason = (
            "TurboQuant safety preconditions are satisfied, but broader cache closure still remains partial"
        )
        recommended_next_step = (
            "advance repeated-serving cache evidence until TurboQuant can be validated without overclaiming parity"
        )

    if (
        repeatability_evidence.repeatability_status in {
            "repeat_reuse_visible",
            "repeat_eviction_visible",
        }
        and turboquant_readiness.status == "ready_for_controlled_validation"
    ):
        closure_rung = "partial_closure"
        blocked_reason = (
            "owlmlx has repeated-serving reuse or eviction evidence plus TurboQuant readiness, but scheduler depth remains serial and still below reference-grade parity"
        )
        recommended_next_step = (
            "switch the dominant gap to multi-model governance or deeper scheduler/runtime closure work"
        )

    return CacheClosureRung(
        scheduler=scheduler_status,
        residency=residency_evidence,
        repeatability=repeatability_evidence,
        turboquant=turboquant_readiness,
        status="partial",
        closure_rung=closure_rung,
        blocked_reason=blocked_reason,
        recommended_next_step=recommended_next_step,
    )


def cache_closure_rung_to_dict(rung: CacheClosureRung) -> dict[str, Any]:
    """Serialize runtime-owned cache closure rung."""

    return {
        "contract": {
            "surface": "owlmlx.cache_closure_rung",
            "version": "phase45",
            "stable_sections": [
                "summary",
                "scheduler",
                "residency",
                "repeatability",
                "turboquant",
            ],
        },
        "summary": {
            "status": rung.status,
            "closure_rung": rung.closure_rung,
            "blocked_reason": rung.blocked_reason,
            "recommended_next_step": rung.recommended_next_step,
        },
        "scheduler": cache_scheduler_status_to_dict(rung.scheduler)["summary"],
        "residency": cache_residency_evidence_to_dict(rung.residency)["summary"],
        "repeatability": cache_repeatability_evidence_to_dict(rung.repeatability)["summary"],
        "turboquant": turboquant_readiness_to_dict(rung.turboquant)["summary"],
    }
