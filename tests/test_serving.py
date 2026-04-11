"""Tests for owlmlx.serving — generation gate discipline."""

import asyncio
import threading
import time

from owlmlx.serving import GenerationGate, GenerationResult, MAX_GENERATION_CONCURRENCY


def test_max_concurrency_is_one() -> None:
    """The validated safe concurrency is exactly 1."""
    assert MAX_GENERATION_CONCURRENCY == 1


def test_single_generation_passes() -> None:
    """A single generation call succeeds and returns the result."""
    gate = GenerationGate()
    result = gate.execute(lambda: 42)
    assert result.value == 42
    assert result.was_queued is False
    assert result.execution_time_s >= 0
    assert result.wait_time_s >= 0


def test_generation_with_args() -> None:
    """Arguments are forwarded to the generation function."""
    gate = GenerationGate()
    result = gate.execute(lambda x, y: x + y, 3, y=7)
    assert result.value == 10


def test_status_reflects_idle_after_generation() -> None:
    """After generation completes, gate status shows idle."""
    gate = GenerationGate()
    gate.execute(lambda: "hello")
    status = gate.status
    assert status["generation_gate"] == "idle"
    assert status["max_concurrent"] == 1
    assert status["queue_discipline"] == "serial"
    assert status["total_served"] == 1
    assert status["total_queued"] == 1


def test_status_counters_accumulate() -> None:
    """Multiple generations accumulate counters correctly."""
    gate = GenerationGate()
    for _ in range(5):
        gate.execute(lambda: None)
    status = gate.status
    assert status["total_served"] == 5
    assert status["total_queued"] == 5


def test_reset_counters() -> None:
    """reset_counters clears all metrics but not the lock."""
    gate = GenerationGate()
    gate.execute(lambda: None)
    gate.reset_counters()
    status = gate.status
    assert status["total_served"] == 0
    assert status["total_queued"] == 0
    assert status["total_wait_s"] == 0.0


def test_concurrent_callers_are_serialized() -> None:
    """Two concurrent callers are serialized — only one runs at a time.

    This is the core discipline being tested: the gate must prevent
    concurrent generation even when multiple threads try simultaneously.
    """
    gate = GenerationGate()
    execution_log: list[tuple[str, float]] = []
    ready = threading.Event()

    def slow_generate(name: str) -> str:
        execution_log.append((f"{name}_start", time.monotonic()))
        # Signal that we're inside the lock so the other thread can attempt entry
        ready.set()
        time.sleep(0.15)
        execution_log.append((f"{name}_end", time.monotonic()))
        return name

    results: list[GenerationResult | None] = [None, None]

    def run(idx: int, name: str) -> None:
        results[idx] = gate.execute(slow_generate, name)

    t1 = threading.Thread(target=run, args=(0, "A"))
    t1.start()
    # Wait until A is inside the lock, then launch B
    ready.wait(timeout=5)
    t2 = threading.Thread(target=run, args=(1, "B"))
    t2.start()
    # Give B a moment to queue on the lock
    time.sleep(0.02)

    t1.join(timeout=10)
    t2.join(timeout=10)

    # Both must have completed
    assert results[0] is not None
    assert results[1] is not None
    assert results[0].value == "A"
    assert results[1].value == "B"

    # B must have been queued (A was already active)
    assert results[1].was_queued is True

    # Verify non-overlapping execution
    starts = [t for name, t in execution_log if name.endswith("_start")]
    ends = [t for name, t in execution_log if name.endswith("_end")]
    assert len(starts) == 2
    assert len(ends) == 2
    starts.sort()
    ends.sort()
    assert starts[1] >= ends[0], "Generations overlapped — gate failed to serialize"

    # Status should reflect both served
    assert gate.status["total_served"] == 2


def test_generation_exception_does_not_break_gate() -> None:
    """If a generation raises, the gate still releases the lock."""
    gate = GenerationGate()

    try:
        gate.execute(lambda: 1 / 0)
    except ZeroDivisionError:
        pass

    # Gate must still work after the failed generation
    result = gate.execute(lambda: "recovered")
    assert result.value == "recovered"
    assert gate.status["total_served"] == 1  # only the successful one


def test_is_active_property() -> None:
    """is_active reflects whether generation is in progress."""
    gate = GenerationGate()
    assert gate.is_active is False

    active_during: list[bool] = []

    def check_active() -> str:
        active_during.append(gate.is_active)
        return "done"

    gate.execute(check_active)
    assert active_during == [True]
    assert gate.is_active is False


def test_async_execution() -> None:
    """execute_async works correctly in an event loop."""
    gate = GenerationGate()

    async def run() -> GenerationResult:
        return await gate.execute_async(lambda: "async_result")

    result = asyncio.run(run())
    assert result.value == "async_result"
    assert gate.status["total_served"] == 1


def test_stream_session_updates_gate_counters() -> None:
    gate = GenerationGate()

    async def run() -> tuple[bool, float]:
        async with gate.stream_session() as start:
            return start.was_queued, start.wait_time_s

    was_queued, wait_time_s = asyncio.run(run())

    assert was_queued is False
    assert wait_time_s >= 0
    assert gate.status["total_served"] == 1
    assert gate.status["total_queued"] == 1


def test_timing_metadata_is_reasonable() -> None:
    """Execution and wait times are plausible."""
    gate = GenerationGate()
    result = gate.execute(lambda: time.sleep(0.05) or "ok")
    assert result.execution_time_s >= 0.04
    assert result.wait_time_s < 0.05  # should be near-zero for uncontested
    assert gate.status["longest_exec_s"] >= 0.04
