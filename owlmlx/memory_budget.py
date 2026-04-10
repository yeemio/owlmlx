"""owlmlx serving-path memory budget truth.

Defines the runtime substrate fact of how much memory is available for
model serving on this machine class, and whether a given model load
will fit within that budget.

This is serving-path only. Training memory concerns are explicitly out
of scope for this module — training budget management is a deferred
capability (see program contract: training stays deferred).

Runtime truth this module owns:

- Machine memory class identification (e.g., 128 GB Apple Silicon)
- System reserve calculation (memory unavailable for model serving)
- Usable model-serving budget derivation
- Warning threshold for approaching budget limit
- Pure "will it fit?" evaluation given current loaded memory
- Budget snapshot for runtime status exposure

This module is self-contained. It does not import any platform module.
If the platform control_service.py were deleted, this module would
still function. That is the absorption criterion (contract Rule 8).

Hardware truth source: Verified on Apple M5 Max, 128 GB unified memory,
oMLX 0.3.2. The 12 GB system reserve is empirically established — macOS
and system services consume approximately this amount under model-serving
workloads.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


# ── Machine profile constants ──────────────────────────────────────────────────
# These describe the hardware truth of a specific machine class.
# When owlmlx runs on different hardware, a new profile can be added.

DEFAULT_SYSTEM_MEMORY_GB: float = 128.0
DEFAULT_SYSTEM_RESERVE_GB: float = 12.0
DEFAULT_SERVING_BUDGET_GB: float = DEFAULT_SYSTEM_MEMORY_GB - DEFAULT_SYSTEM_RESERVE_GB  # 116.0
DEFAULT_WARNING_THRESHOLD_GB: float = 100.0


class BudgetVerdict(str, Enum):
    """Result of a memory budget evaluation.

    Values:
        fits: The requested load fits within budget.
        fits_warning: The requested load fits but crosses the warning threshold.
        exceeds: The requested load would exceed the budget.
    """

    fits = "fits"
    fits_warning = "fits_warning"
    exceeds = "exceeds"


@dataclass(frozen=True, slots=True)
class MachineMemoryProfile:
    """Describes the memory truth of a specific machine class.

    This is runtime substrate truth — a fact about the hardware, not a
    policy decision. The profile says "this machine has X GB, the OS
    takes Y GB, so Z GB is available for model serving."

    Attributes:
        system_memory_gb: Total physical memory (e.g., 128.0).
        system_reserve_gb: Memory reserved for OS and system services.
        serving_budget_gb: Memory available for model serving
            (system_memory_gb - system_reserve_gb).
        warning_threshold_gb: Memory level at which a warning is raised
            (models still load, but operator is alerted).
    """

    system_memory_gb: float
    system_reserve_gb: float
    serving_budget_gb: float
    warning_threshold_gb: float

    def __post_init__(self) -> None:
        if self.system_memory_gb <= 0:
            raise ValueError(f"system_memory_gb must be positive, got {self.system_memory_gb}")
        if self.system_reserve_gb < 0:
            raise ValueError(f"system_reserve_gb must be non-negative, got {self.system_reserve_gb}")
        if self.serving_budget_gb <= 0:
            raise ValueError(f"serving_budget_gb must be positive, got {self.serving_budget_gb}")
        if self.serving_budget_gb > self.system_memory_gb:
            raise ValueError(
                f"serving_budget_gb ({self.serving_budget_gb}) cannot exceed "
                f"system_memory_gb ({self.system_memory_gb})"
            )
        if self.warning_threshold_gb < 0:
            raise ValueError(
                f"warning_threshold_gb must be non-negative, got {self.warning_threshold_gb}"
            )


def default_machine_profile() -> MachineMemoryProfile:
    """Return the default machine profile for the current verified hardware.

    This is the M5 Max 128 GB profile validated in production serving.
    """
    return MachineMemoryProfile(
        system_memory_gb=DEFAULT_SYSTEM_MEMORY_GB,
        system_reserve_gb=DEFAULT_SYSTEM_RESERVE_GB,
        serving_budget_gb=DEFAULT_SERVING_BUDGET_GB,
        warning_threshold_gb=DEFAULT_WARNING_THRESHOLD_GB,
    )


@dataclass(frozen=True, slots=True)
class BudgetEvaluation:
    """Result of evaluating whether a model load fits the memory budget.

    This is a pure computation result — no side effects, no platform
    dependencies, no policy enforcement. The caller (platform control
    plane) decides what to do with the verdict.

    Attributes:
        verdict: Whether the load fits, fits with warning, or exceeds.
        currently_loaded_gb: Memory currently occupied by loaded models.
        requested_gb: Memory the requested model would consume.
        projected_gb: Total memory if the load proceeds.
        budget_gb: The serving budget limit.
        headroom_gb: Remaining budget after projected load (negative if exceeds).
        message: Human-readable summary.
    """

    verdict: BudgetVerdict
    currently_loaded_gb: float
    requested_gb: float
    projected_gb: float
    budget_gb: float
    headroom_gb: float
    message: str


def evaluate_model_fit(
    *,
    requested_gb: float,
    currently_loaded_gb: float = 0.0,
    profile: MachineMemoryProfile | None = None,
) -> BudgetEvaluation:
    """Evaluate whether a model fits the serving memory budget.

    This is a pure function. It takes numbers in, returns a verdict out.
    No file I/O, no network calls, no platform imports.

    Args:
        requested_gb: Memory the model to be loaded would consume (GB).
        currently_loaded_gb: Memory already occupied by serving models (GB).
        profile: Machine memory profile. Uses default if not provided.

    Returns:
        BudgetEvaluation with verdict and detailed breakdown.
    """
    if profile is None:
        profile = default_machine_profile()

    projected = currently_loaded_gb + requested_gb
    headroom = profile.serving_budget_gb - projected

    if projected > profile.serving_budget_gb:
        verdict = BudgetVerdict.exceeds
        message = (
            f"loading {requested_gb:.1f}G would exceed serving budget: "
            f"{currently_loaded_gb:.1f}G loaded + {requested_gb:.1f}G requested "
            f"= {projected:.1f}G > {profile.serving_budget_gb:.1f}G limit"
        )
    elif projected > profile.warning_threshold_gb:
        verdict = BudgetVerdict.fits_warning
        message = (
            f"loading {requested_gb:.1f}G approaches budget limit: "
            f"{projected:.1f}G projected of {profile.serving_budget_gb:.1f}G budget "
            f"({headroom:.1f}G headroom)"
        )
    else:
        verdict = BudgetVerdict.fits
        message = (
            f"loading {requested_gb:.1f}G fits within budget: "
            f"{projected:.1f}G projected of {profile.serving_budget_gb:.1f}G budget "
            f"({headroom:.1f}G headroom)"
        )

    return BudgetEvaluation(
        verdict=verdict,
        currently_loaded_gb=currently_loaded_gb,
        requested_gb=requested_gb,
        projected_gb=round(projected, 2),
        budget_gb=profile.serving_budget_gb,
        headroom_gb=round(headroom, 2),
        message=message,
    )


def budget_snapshot(
    *,
    currently_loaded_gb: float = 0.0,
    profile: MachineMemoryProfile | None = None,
) -> dict[str, Any]:
    """Return a budget truth snapshot for runtime status exposure.

    This dict is intended to be embedded in runtime status payloads.
    It exposes honest memory budget truth without policy decisions.

    Args:
        currently_loaded_gb: Memory occupied by currently loaded models.
        profile: Machine memory profile. Uses default if not provided.

    Returns:
        Dict suitable for inclusion in runtime status payloads.
    """
    if profile is None:
        profile = default_machine_profile()

    available = profile.serving_budget_gb - currently_loaded_gb
    utilization = (
        round(currently_loaded_gb / profile.serving_budget_gb, 3)
        if profile.serving_budget_gb > 0
        else 0.0
    )

    return {
        "system_memory_gb": profile.system_memory_gb,
        "system_reserve_gb": profile.system_reserve_gb,
        "serving_budget_gb": profile.serving_budget_gb,
        "warning_threshold_gb": profile.warning_threshold_gb,
        "currently_loaded_gb": round(currently_loaded_gb, 2),
        "available_gb": round(available, 2),
        "utilization": utilization,
    }
