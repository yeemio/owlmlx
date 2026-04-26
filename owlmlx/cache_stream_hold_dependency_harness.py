"""Runtime-owned harness for exact stream-hold dependency observation."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CacheStreamHoldDependencyHarnessResult:
    """Observed stream gate-release behavior on the active runtime path."""

    hold_dependency_narrowed: bool
    hold_verdict: str
    hold_status: str
    gate_release_boundary: str
    second_stream_started_before_first_consumer_completed: bool
    max_concurrent: int
    queue_policy: str
    gate_total_served: int
    gate_total_queued: int
    preserved_post_claim_invariants: tuple[str, ...]
    first_stream_events: tuple[str, ...]
    second_stream_events: tuple[str, ...]


def run_cache_stream_hold_dependency_harness(
    *,
    prompts: tuple[str, str] = ("stream-hold-a", "stream-hold-b"),
) -> CacheStreamHoldDependencyHarnessResult:
    """Observe whether stream gate release still waits for consumer completion."""

    from .runtime import FakeBackend, RuntimeKernel

    kernel = RuntimeKernel(FakeBackend(default_memory_gb=1.0))
    loaded = kernel.load_model("stream-hold-probe", memory_gb=1.0)
    if not loaded.ok:
        raise RuntimeError(f"stream hold harness load failed: {loaded.message}")

    async def observe() -> tuple[
        bool,
        dict[str, object],
        tuple[str, ...],
        tuple[str, ...],
    ]:
        first_has_started = asyncio.Event()
        first_may_finish = asyncio.Event()
        first_consumer_completed = asyncio.Event()
        second_has_started = asyncio.Event()
        first_events: list[str] = []
        second_events: list[str] = []

        async def consume_first() -> None:
            stream = kernel.generate_stream(prompts[0], model_id="stream-hold-probe")
            first_event = await anext(stream)
            first_events.append(first_event.event)
            first_has_started.set()
            await first_may_finish.wait()
            async for event in stream:
                first_events.append(event.event)
            first_consumer_completed.set()

        async def consume_second() -> None:
            async for event in kernel.generate_stream(
                prompts[1],
                model_id="stream-hold-probe",
            ):
                second_events.append(event.event)
                if not second_has_started.is_set():
                    second_has_started.set()

        first_task = asyncio.create_task(consume_first())
        await first_has_started.wait()
        await asyncio.sleep(0.05)
        second_task = asyncio.create_task(consume_second())

        try:
            await asyncio.wait_for(second_has_started.wait(), timeout=0.2)
            second_started_early = not first_consumer_completed.is_set()
        except TimeoutError:
            second_started_early = False

        status_before_release = kernel.status_dict()["generation_gate"]
        first_may_finish.set()
        await asyncio.gather(first_task, second_task)
        return (
            second_started_early,
            status_before_release,
            tuple(first_events),
            tuple(second_events),
        )

    try:
        (
            second_started_early,
            gate_status,
            first_stream_events,
            second_stream_events,
        ) = asyncio.run(observe())
        pre_gate = dict(gate_status.get("pre_gate_admission", {}))
        return CacheStreamHoldDependencyHarnessResult(
            hold_dependency_narrowed=second_started_early,
            hold_verdict=(
                "stream_hold_dependency_narrowed"
                if second_started_early
                else "stream_hold_dependency_still_blocked"
            ),
            hold_status=(
                "stream_gate_release_decoupled_from_consumer_completion_visible"
                if second_started_early
                else "stream_session_holds_gate_until_completion"
            ),
            gate_release_boundary=(
                "backend_stream_iterator_completion_before_consumer_drain"
                if second_started_early
                else "stream_session_completion"
            ),
            second_stream_started_before_first_consumer_completed=second_started_early,
            max_concurrent=int(gate_status.get("max_concurrent", 0) or 0),
            queue_policy=str(gate_status.get("queue_policy") or "unknown"),
            gate_total_served=int(gate_status.get("total_served", 0) or 0),
            gate_total_queued=int(gate_status.get("total_queued", 0) or 0),
            preserved_post_claim_invariants=tuple(
                str(item)
                for item in pre_gate.get("preserved_post_claim_invariants", ())
            ),
            first_stream_events=first_stream_events,
            second_stream_events=second_stream_events,
        )
    finally:
        kernel.unload_model("stream-hold-probe")
