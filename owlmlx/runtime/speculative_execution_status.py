"""Runtime-owned `speculative_execution_status` contract surface.

Implements F-1.2 (endpoint stub) per docs/architect/design/F-1-spec.md:
- §4.1 identity / placement
- §4.5 day-one method vocabulary
- §4.11.1 spec-disabled default payload shape

F-1.3 (kernel observe_* APIs that overlay live runner state) belongs to a
separate code-grade slice and is intentionally NOT wired here. The payload
produced today is the §4.11.1 "spec explicitly disabled (default)" shape,
unconditionally.

The `assistant_drafter` method's status is read live from
`owlmlx.gemma4_mtp_drafter.GEMMA4_MTP_CAPABILITY_LABEL` via attribute access
at call time so tests / future capability promotions are reflected without a
process restart.
"""

from __future__ import annotations

from typing import Any

from owlmlx import gemma4_mtp_drafter as _drafter_module


SPECULATIVE_EXECUTION_STATUS_SURFACE = "owlmlx.speculative_execution_status"
SPECULATIVE_EXECUTION_STATUS_VERSION = "v1"


def _day_one_method_vocabulary() -> list[dict[str, Any]]:
    """Build the day-one `available_methods` list.

    The `assistant_drafter` status is read live from
    `GEMMA4_MTP_CAPABILITY_LABEL` (attribute access on the module object, not
    a bound import) so monkeypatching the constant in tests propagates
    without needing to reimport.
    """
    return [
        {
            "method": "native_mtp",
            "status": "not_implemented",
            "notes": "DS4 MTP weights absent or stripped (see D3)",
        },
        {
            "method": "assistant_drafter",
            "status": _drafter_module.GEMMA4_MTP_CAPABILITY_LABEL,
            "notes": "deferred_cli_per_request via mlx_vlm",
        },
        {
            "method": "draft_model",
            "status": "not_implemented",
            "notes": None,
        },
        {
            "method": "eagle",
            "status": "not_implemented",
            "notes": None,
        },
        {
            "method": "ngram",
            "status": "not_implemented",
            "notes": "F-2 candidate",
        },
    ]


def build_speculative_execution_status_payload() -> dict[str, Any]:
    """Build the §4.11.1 spec-disabled default payload.

    F-1.2 returns this shape unconditionally. F-1.3 will extend this
    function (additive: optional `live_state` parameter) to overlay runner
    observation state per §4.11.2.
    """
    return {
        "surface": SPECULATIVE_EXECUTION_STATUS_SURFACE,
        "version": SPECULATIVE_EXECUTION_STATUS_VERSION,
        "method": None,
        "capability_label": "disabled",
        "runner_status": "unloaded",
        "missing_reason": "spec_explicitly_disabled",
        "available_methods": _day_one_method_vocabulary(),
    }
