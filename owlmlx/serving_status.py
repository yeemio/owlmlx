"""owlmlx large-weight path serving status builder.

Produces an owlmlx-schema-compliant runtime status payload for
large-weight serving paths. Composes:

- generation gate discipline status
- memory snapshot (active, peak, budget)
- lifecycle and posture (tier, interactive status, lifecycle mode)
- serving identity (path-level, not specimen-level)

This is the owlmlx-owned shape of "what does a running large-weight
engine look like". The platform shell fills in specimen-specific detail
(model name, cache internals, baselines) on top of this base.
"""

from __future__ import annotations

import time
from typing import Any, Optional

from .serving import GenerationGate


def build_large_weight_serving_status(
    *,
    gate: GenerationGate,
    active_memory_bytes: int,
    peak_memory_bytes: int,
    memory_budget_gb: float,
    start_time: Optional[float] = None,
    tier: str = "background",
    interactive_status: str = "background_only",
    lifecycle_mode: str = "manual_start",
    extra: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """Build the path-level serving status payload.

    This is the owlmlx-owned status shape. It includes everything the
    runtime owns — generation discipline, memory truth, lifecycle — and
    nothing specimen-specific (no model name, no cache internals, no
    hardcoded baselines).

    The platform shell or specimen adapter can merge specimen-specific
    fields on top of this dict.

    Args:
        gate: The GenerationGate controlling this serving path.
        active_memory_bytes: Current MLX active memory in bytes.
        peak_memory_bytes: Peak MLX memory in bytes.
        memory_budget_gb: Configured memory budget in GB.
        start_time: Server start time (time.time()). If provided,
            uptime_s is calculated.
        tier: Serving tier classification.
        interactive_status: Whether the path supports interactive use.
        lifecycle_mode: How the runtime is started/stopped.
        extra: Optional dict of additional fields to merge (specimen-
            specific detail added by the shell).

    Returns:
        owlmlx-schema-compliant status dict.
    """
    status: dict[str, Any] = {
        "status": "ok",
        "runtime": "owlmlx",
        "tier": tier,
        "interactive_status": interactive_status,
        "lifecycle_mode": lifecycle_mode,
        "memory": {
            "active_bytes": active_memory_bytes,
            "peak_bytes": peak_memory_bytes,
            "budget_gb": memory_budget_gb,
            "utilization": round(
                active_memory_bytes / (memory_budget_gb * (1 << 30)), 3
            )
            if memory_budget_gb > 0
            else None,
        },
        "generation": gate.status,
    }

    if start_time is not None:
        status["uptime_s"] = int(time.time() - start_time)

    if extra:
        status.update(extra)

    return status


def merge_specimen_identity(
    base_status: dict[str, Any],
    *,
    model: str,
    path_variant: str,
    **specimen_fields: Any,
) -> dict[str, Any]:
    """Merge specimen-specific identity into an owlmlx base status.

    This is how the platform shell adds "which model is actually running"
    on top of the owlmlx-owned serving status shape.

    The result is a complete status payload suitable for /healthz and
    /v1/status endpoints.

    Args:
        base_status: The dict returned by build_large_weight_serving_status.
        model: Specimen model name (e.g., "Kimi-K2.5-3bit").
        path_variant: Specimen path variant (e.g., "expert-sharded").
        **specimen_fields: Any additional specimen-specific fields
            (cache, baselines, layout, etc.).

    Returns:
        Complete status dict with both path-level and specimen-level truth.
    """
    merged = dict(base_status)
    merged["model"] = model
    merged["path_variant"] = path_variant
    merged.update(specimen_fields)
    return merged
