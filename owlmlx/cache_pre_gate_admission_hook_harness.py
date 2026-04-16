"""Runtime-owned harness for the bounded pre-gate admission hook experiment."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass

from .memory_budget import MachineMemoryProfile


@dataclass(frozen=True, slots=True)
class PreGateAdmissionHookHarnessResult:
    """Observed runtime truth for the structural ingress seam experiment."""

    runtime_owned_hook_present: bool
    hook_boundary: str
    hook_mode: str
    observed_midflight_staged_count: int
    observed_total_staged: int
    observed_total_claimed: int
    observed_total_discarded: int
    staging_units: tuple[str, ...]
    preserved_post_claim_invariants: tuple[str, ...]


def _profile() -> MachineMemoryProfile:
    return MachineMemoryProfile(
        system_memory_gb=8.0,
        system_reserve_gb=2.0,
        serving_budget_gb=6.0,
        warning_threshold_gb=5.0,
    )


def run_pre_gate_admission_hook_harness() -> PreGateAdmissionHookHarnessResult:
    """Observe the bounded pre-gate admission hook on the active runtime path."""

    from .runtime.backends import FakeBackend
    from .runtime.kernel import RuntimeKernel

    kernel = RuntimeKernel(
        FakeBackend(default_memory_gb=1.0, generate_delay_s=0.05),
        profile=_profile(),
    )
    kernel.load_model("cache-hook-probe")

    async def observe() -> dict[str, object]:
        first = asyncio.create_task(kernel.generate("one"))
        await asyncio.sleep(0.01)
        second = asyncio.create_task(kernel.generate("two"))
        await asyncio.sleep(0.01)
        mid = kernel.status_dict()["generation_gate"]["pre_gate_admission"]
        await asyncio.gather(first, second)
        final = kernel.status_dict()["generation_gate"]["pre_gate_admission"]
        return {"mid": mid, "final": final}

    observed = asyncio.run(observe())
    mid = observed["mid"]
    final = observed["final"]
    return PreGateAdmissionHookHarnessResult(
        runtime_owned_hook_present=mid["hook_status"] == "present",
        hook_boundary=str(mid["hook_boundary"]),
        hook_mode=str(mid["hook_mode"]),
        observed_midflight_staged_count=int(mid["staged_count"]),
        observed_total_staged=int(final["total_staged"]),
        observed_total_claimed=int(final["total_claimed"]),
        observed_total_discarded=int(final["total_discarded"]),
        staging_units=tuple(str(item) for item in mid["staging_units"]),
        preserved_post_claim_invariants=tuple(
            str(item) for item in mid["preserved_post_claim_invariants"]
        ),
    )
