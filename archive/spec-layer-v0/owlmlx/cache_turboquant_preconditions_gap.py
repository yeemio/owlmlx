"""Runtime-owned exact TurboQuant preconditions gap for the active cache path."""

from __future__ import annotations

from dataclasses import dataclass

from .turboquant_readiness import TurboQuantReadiness, build_turboquant_readiness


@dataclass(frozen=True, slots=True)
class CacheTurboQuantPreconditionsGap:
    """Exact TurboQuant preconditions truth for the active cache path."""

    readiness: TurboQuantReadiness
    status: str
    preconditions_rung: str
    missing_preconditions: tuple[str, ...]
    residual_blocker: str | None
    recommended_next_step: str


def build_cache_turboquant_preconditions_gap(
    *,
    readiness: TurboQuantReadiness | None = None,
) -> CacheTurboQuantPreconditionsGap:
    """Build the exact TurboQuant preconditions gap."""

    turboquant = (
        readiness if isinstance(readiness, TurboQuantReadiness) else build_turboquant_readiness()
    )

    missing: list[str] = []
    if not turboquant.bits_in_cache_key:
        missing.append("bits_in_cache_key")
    if not turboquant.invalidates_on_config_toggle:
        missing.append("invalidates_on_config_toggle")
    if not turboquant.runtime_verified:
        missing.append("runtime_verified")

    preconditions_rung = "preconditions_unresolved"
    residual_blocker = (
        "TurboQuant preconditions are not yet frozen strongly enough on the active cache path"
    )
    recommended_next_step = (
        "freeze cache-key isolation, invalidation-on-toggle, and runtime verification before narrowing TurboQuant work"
    )

    if turboquant.status == "safety_blocked":
        preconditions_rung = "preconditions_exact"
        residual_blocker = (
            "TurboQuant remains exact-but-secondary on this cache branch: "
            + ", ".join(missing)
            + " still prevent safe activation"
        )
        recommended_next_step = (
            "keep TurboQuant exact but secondary on this path until scheduler implementation moves; when revisiting TurboQuant, satisfy the frozen missing preconditions without inflating readiness"
        )
    elif turboquant.status in {"evidence_blocked", "ready_for_controlled_validation"}:
        preconditions_rung = "preconditions_satisfied"
        residual_blocker = None if turboquant.status == "ready_for_controlled_validation" else (
            "TurboQuant preconditions are satisfied; remaining work is now evidence-grade rather than precondition-grade"
        )
        recommended_next_step = (
            "keep TurboQuant preconditions frozen as satisfied and move to runtime evidence or controlled validation as justified"
        )

    return CacheTurboQuantPreconditionsGap(
        readiness=turboquant,
        status="partial",
        preconditions_rung=preconditions_rung,
        missing_preconditions=tuple(missing),
        residual_blocker=residual_blocker,
        recommended_next_step=recommended_next_step,
    )


def cache_turboquant_preconditions_gap_to_dict(
    gap: CacheTurboQuantPreconditionsGap,
) -> dict[str, object]:
    """Serialize the TurboQuant preconditions gap."""

    return {
        "contract": {
            "surface": "owlmlx.cache_turboquant_preconditions_gap",
            "version": "phase45",
            "stable_sections": [
                "summary",
                "missing_preconditions",
            ],
        },
        "summary": {
            "status": gap.status,
            "preconditions_rung": gap.preconditions_rung,
            "residual_blocker": gap.residual_blocker,
            "recommended_next_step": gap.recommended_next_step,
        },
        "missing_preconditions": list(gap.missing_preconditions),
    }
