"""Runtime-owned multi-model pinning control for owlmlx."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(frozen=True, slots=True)
class MultiModelPinningControl:
    """Stable runtime-owned pinning control truth."""

    status: str
    control_rung: str
    pinning_supported: bool
    ttl_supported: bool
    pinned_model_ids: tuple[str, ...]
    unload_block_visible: bool
    restart_retains_pin_visible: bool
    residual_blocker: str | None
    recommended_next_step: str


def build_multi_model_pinning_control(
    runtime_status: Mapping[str, Any] | None = None,
    *,
    harness_evidence: Mapping[str, Any] | None = None,
) -> MultiModelPinningControl:
    """Build runtime-owned pinning control truth."""

    raw = dict(runtime_status or {})
    governance_policy = dict(raw.get("governance_policy", {}))
    evidence = dict(harness_evidence or {})
    pinning_supported = bool(governance_policy.get("pinning_supported", False))
    ttl_supported = bool(governance_policy.get("ttl_supported", False))
    pinned_model_ids = tuple(str(x) for x in governance_policy.get("pinned_model_ids", []))
    unload_block_visible = bool(evidence.get("unload_block_visible", False))
    restart_retains_pin_visible = bool(evidence.get("restart_retains_pin_visible", False))

    control_rung = "control_absent"
    residual_blocker = "runtime-owned pinning control is not yet present"
    recommended_next_step = "add a minimal runtime-owned pin/unpin control before continuing governance policy closure"

    if pinning_supported:
        control_rung = "control_supported"
        residual_blocker = (
            "pinning support exists, but runtime-owned unload-block and restart-retention evidence are not yet both visible"
        )
        recommended_next_step = (
            "run a pin/unpin harness that proves pinned unload is blocked and restart retains pin state"
        )

    if pinning_supported and unload_block_visible and restart_retains_pin_visible:
        control_rung = "control_implemented"
        if ttl_supported:
            residual_blocker = (
                "pinning now exists and TTL policy also exists; remaining governance policy control is eviction-history governance"
            )
            recommended_next_step = (
                "continue the governance fallback branch with eviction-history governance"
            )
        else:
            residual_blocker = (
                "pinning now exists; remaining governance policy controls are TTL policy and eviction-history governance"
            )
            recommended_next_step = (
                "continue the governance fallback branch with TTL policy or eviction-history governance"
            )

    return MultiModelPinningControl(
        status="partial",
        control_rung=control_rung,
        pinning_supported=pinning_supported,
        ttl_supported=ttl_supported,
        pinned_model_ids=pinned_model_ids,
        unload_block_visible=unload_block_visible,
        restart_retains_pin_visible=restart_retains_pin_visible,
        residual_blocker=residual_blocker,
        recommended_next_step=recommended_next_step,
    )


def multi_model_pinning_control_to_dict(
    control: MultiModelPinningControl,
) -> dict[str, Any]:
    """Serialize runtime-owned pinning control truth."""

    return {
        "contract": {
            "surface": "owlmlx.multi_model_pinning_control",
            "version": "phase45",
            "stable_sections": [
                "summary",
                "pinning",
                "policy_progress",
            ],
        },
        "summary": {
            "status": control.status,
            "control_rung": control.control_rung,
            "residual_blocker": control.residual_blocker,
            "recommended_next_step": control.recommended_next_step,
        },
        "pinning": {
            "pinning_supported": control.pinning_supported,
            "ttl_supported": control.ttl_supported,
            "pinned_model_ids": list(control.pinned_model_ids),
            "unload_block_visible": control.unload_block_visible,
            "restart_retains_pin_visible": control.restart_retains_pin_visible,
        },
        "policy_progress": {
            "remaining_controls": (
                ["eviction_history_governance"]
                if control.control_rung == "control_implemented" and control.ttl_supported
                else (
                    ["ttl_policy", "eviction_history_governance"]
                    if control.control_rung == "control_implemented"
                    else ["pinning", "ttl_policy", "eviction_history_governance"]
                )
            ),
        },
    }
