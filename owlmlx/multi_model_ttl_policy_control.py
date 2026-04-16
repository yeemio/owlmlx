"""Runtime-owned multi-model TTL policy control for owlmlx."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(frozen=True, slots=True)
class MultiModelTTLPolicyControl:
    """Stable runtime-owned TTL policy control truth."""

    status: str
    control_rung: str
    ttl_supported: bool
    ttl_policy_mode: str | None
    ttl_model_ids: tuple[str, ...]
    ttl_expired_model_ids: tuple[str, ...]
    sweep_unloaded_visible: bool
    pinned_expiry_block_visible: bool
    residual_blocker: str | None
    recommended_next_step: str


def build_multi_model_ttl_policy_control(
    runtime_status: Mapping[str, Any] | None = None,
    *,
    harness_evidence: Mapping[str, Any] | None = None,
) -> MultiModelTTLPolicyControl:
    """Build runtime-owned TTL policy control truth."""

    raw = dict(runtime_status or {})
    governance_policy = dict(raw.get("governance_policy", {}))
    evidence = dict(harness_evidence or {})
    ttl_supported = bool(governance_policy.get("ttl_supported", False))
    ttl_policy_mode = governance_policy.get("ttl_policy_mode")
    ttl_model_ids = tuple(str(x) for x in governance_policy.get("ttl_model_ids", []))
    ttl_expired_model_ids = tuple(
        str(x) for x in governance_policy.get("ttl_expired_model_ids", [])
    )
    sweep_unloaded_visible = bool(evidence.get("sweep_unloaded_visible", False))
    pinned_expiry_block_visible = bool(evidence.get("pinned_expiry_block_visible", False))

    control_rung = "control_absent"
    residual_blocker = "runtime-owned TTL policy control is not yet present"
    recommended_next_step = (
        "add a minimal runtime-owned TTL policy before continuing governance policy closure"
    )

    if ttl_supported:
        control_rung = "control_supported"
        residual_blocker = (
            "TTL policy support exists, but runtime-owned expiry sweep evidence is not yet visible"
        )
        recommended_next_step = (
            "run a TTL harness that proves expired models can be swept and pinned expiry remains blocked"
        )

    if ttl_supported and sweep_unloaded_visible and pinned_expiry_block_visible:
        control_rung = "control_implemented"
        residual_blocker = (
            "TTL policy now exists; remaining governance policy control is eviction-history governance"
        )
        recommended_next_step = (
            "continue the governance fallback branch with eviction-history governance"
        )

    return MultiModelTTLPolicyControl(
        status="partial",
        control_rung=control_rung,
        ttl_supported=ttl_supported,
        ttl_policy_mode=str(ttl_policy_mode) if ttl_policy_mode is not None else None,
        ttl_model_ids=ttl_model_ids,
        ttl_expired_model_ids=ttl_expired_model_ids,
        sweep_unloaded_visible=sweep_unloaded_visible,
        pinned_expiry_block_visible=pinned_expiry_block_visible,
        residual_blocker=residual_blocker,
        recommended_next_step=recommended_next_step,
    )


def multi_model_ttl_policy_control_to_dict(
    control: MultiModelTTLPolicyControl,
) -> dict[str, Any]:
    """Serialize runtime-owned TTL policy control truth."""

    return {
        "contract": {
            "surface": "owlmlx.multi_model_ttl_policy_control",
            "version": "phase45",
            "stable_sections": [
                "summary",
                "ttl_policy",
                "policy_progress",
            ],
        },
        "summary": {
            "status": control.status,
            "control_rung": control.control_rung,
            "residual_blocker": control.residual_blocker,
            "recommended_next_step": control.recommended_next_step,
        },
        "ttl_policy": {
            "ttl_supported": control.ttl_supported,
            "ttl_policy_mode": control.ttl_policy_mode,
            "ttl_model_ids": list(control.ttl_model_ids),
            "ttl_expired_model_ids": list(control.ttl_expired_model_ids),
            "sweep_unloaded_visible": control.sweep_unloaded_visible,
            "pinned_expiry_block_visible": control.pinned_expiry_block_visible,
        },
        "policy_progress": {
            "remaining_controls": (
                ["eviction_history_governance"]
                if control.control_rung == "control_implemented"
                else ["ttl_policy", "eviction_history_governance"]
            ),
        },
    }
