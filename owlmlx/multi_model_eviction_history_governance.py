"""Runtime-owned eviction-history governance for owlmlx."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(frozen=True, slots=True)
class MultiModelEvictionHistoryGovernance:
    """Stable runtime-owned eviction-history governance truth."""

    status: str
    control_rung: str
    eviction_history_visible: bool
    eviction_history_count: int
    recent_event_kinds: tuple[str, ...]
    unloaded_event_visible: bool
    pinned_skip_event_visible: bool
    residual_blocker: str | None
    recommended_next_step: str


def build_multi_model_eviction_history_governance(
    runtime_status: Mapping[str, Any] | None = None,
) -> MultiModelEvictionHistoryGovernance:
    """Build runtime-owned eviction-history governance truth."""

    raw = dict(runtime_status or {})
    governance_policy = dict(raw.get("governance_policy", {}))
    eviction_history = list(governance_policy.get("recent_eviction_history", []))
    event_kinds = tuple(
        str(entry.get("event"))
        for entry in eviction_history
        if isinstance(entry, Mapping) and entry.get("event") is not None
    )
    eviction_history_visible = bool(governance_policy.get("eviction_history_visible", False))
    eviction_history_count = int(governance_policy.get("eviction_history_count", 0))
    unloaded_event_visible = "ttl_expired_unloaded" in event_kinds
    pinned_skip_event_visible = "ttl_expiry_blocked_by_pinning" in event_kinds

    control_rung = "control_absent"
    residual_blocker = "runtime-owned eviction-history governance is not yet visible"
    recommended_next_step = (
        "record bounded eviction-history events on the runtime-owned path before claiming policy closure"
    )

    if eviction_history_visible:
        control_rung = "history_visible"
        residual_blocker = (
            "eviction history is visible, but both unloaded and pinned-skip policy events are not yet frozen"
        )
        recommended_next_step = (
            "run a governance harness that proves both TTL unload and pinned-expiry skip events land in eviction history"
        )

    if eviction_history_visible and unloaded_event_visible and pinned_skip_event_visible:
        control_rung = "control_implemented"
        residual_blocker = None
        recommended_next_step = (
            "governance fallback policy controls are locally closed; return to supported-host baseline establishment"
        )

    return MultiModelEvictionHistoryGovernance(
        status="partial",
        control_rung=control_rung,
        eviction_history_visible=eviction_history_visible,
        eviction_history_count=eviction_history_count,
        recent_event_kinds=event_kinds,
        unloaded_event_visible=unloaded_event_visible,
        pinned_skip_event_visible=pinned_skip_event_visible,
        residual_blocker=residual_blocker,
        recommended_next_step=recommended_next_step,
    )


def multi_model_eviction_history_governance_to_dict(
    control: MultiModelEvictionHistoryGovernance,
) -> dict[str, Any]:
    """Serialize runtime-owned eviction-history governance truth."""

    return {
        "contract": {
            "surface": "owlmlx.multi_model_eviction_history_governance",
            "version": "phase45",
            "stable_sections": [
                "summary",
                "eviction_history",
                "policy_progress",
            ],
        },
        "summary": {
            "status": control.status,
            "control_rung": control.control_rung,
            "residual_blocker": control.residual_blocker,
            "recommended_next_step": control.recommended_next_step,
        },
        "eviction_history": {
            "eviction_history_visible": control.eviction_history_visible,
            "eviction_history_count": control.eviction_history_count,
            "recent_event_kinds": list(control.recent_event_kinds),
            "unloaded_event_visible": control.unloaded_event_visible,
            "pinned_skip_event_visible": control.pinned_skip_event_visible,
        },
        "policy_progress": {
            "remaining_controls": (
                [] if control.control_rung == "control_implemented" else ["eviction_history_governance"]
            ),
        },
    }
