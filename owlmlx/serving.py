"""owlmlx large-weight path serving discipline.

Implements the queue-based single-worker generation pattern validated
through the K-Q4c/K-Q4d experiment line.

Runtime truth this module enforces:

- Same-process parallel generation is unsafe on MLX/Metal (substrate
  thread-safety limitation, not specimen-specific)
- Generation concurrency boundary = 1
- Queue-based serialized serving is the only viable production pattern
- Multi-process isolation bypasses the crash but is not cost-effective

This is an owlmlx-owned runtime responsibility. The platform shell may
host the HTTP transport layer, but the generation discipline belongs here.
"""

from __future__ import annotations

import asyncio
import threading
import time
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from functools import partial
from typing import Any, AsyncIterator, Callable, TypeVar

T = TypeVar("T")

# The only validated safe value. K-Q4c proved concurrency >= 2 crashes.
MAX_GENERATION_CONCURRENCY = 1


@dataclass(slots=True)
class GenerationResult:
    """Result wrapper from a gated generation call."""

    value: Any
    wait_time_s: float
    execution_time_s: float
    was_queued: bool


@dataclass(frozen=True, slots=True)
class PreGateAdmissionMetadata:
    """Immutable metadata allowed to exist before whole-request gate claim."""

    request_kind: str
    model_id: str | None
    stream: bool
    prompt_chars: int
    message_count: int


@dataclass(frozen=True, slots=True)
class PreGateAdmissionReservation:
    """Bounded pre-gate admission reservation.

    This reservation is inert by design. It exists only before whole-request
    gate claim and carries no execution rights.
    """

    reservation_ticket: int
    metadata: PreGateAdmissionMetadata
    staged_at_s: float


@dataclass(slots=True)
class _PreGateAdmissionState:
    reservation: PreGateAdmissionReservation


class GenerationGate:
    """Enforces single-worker generation discipline for large-weight paths.

    This gate ensures that only one generation call executes at a time,
    regardless of how many requests arrive concurrently. Concurrent
    callers block (queue) until the active generation completes.

    Why this exists (validated, not theoretical):

    - MLX Metal operations are not thread-safe for concurrent forward
      passes — concurrent generation causes immediate engine crash
      (K-Q4c: 2 concurrent requests → process crash at 0.4s)
    - Multi-process isolation works but costs 2× memory for ~1.1×
      throughput (K-Q4d: Metal GPU contention)
    - Single-worker queue-based serving is the only viable production
      pattern for large-weight models on Apple Silicon

    This is path-level truth, not specimen-specific.
    """

    def __init__(self) -> None:
        self._condition = threading.Condition()
        self._active = False
        self._next_ticket = 0
        self._serving_ticket = 0
        self._next_pre_gate_ticket = 0
        self._waiters = 0
        self._total_served = 0
        self._total_queued = 0
        self._total_wait_s = 0.0
        self._total_exec_s = 0.0
        self._longest_wait_s = 0.0
        self._longest_exec_s = 0.0
        self._pre_gate_capacity = 32
        self._pre_gate_staged: dict[int, _PreGateAdmissionState] = {}
        self._pre_gate_total_staged = 0
        self._pre_gate_total_claimed = 0
        self._pre_gate_total_discarded = 0
        self._pre_gate_peak_staged = 0

    def stage_admission(
        self,
        metadata: PreGateAdmissionMetadata,
    ) -> PreGateAdmissionReservation:
        """Reserve a bounded inert pre-gate admission slot.

        This is the only new pre-claim structure introduced by the runtime:
        immutable request metadata plus observational ticket reservation before
        whole-request gate claim.
        """

        with self._condition:
            while len(self._pre_gate_staged) >= self._pre_gate_capacity:
                self._condition.wait()
            reservation = PreGateAdmissionReservation(
                reservation_ticket=self._next_pre_gate_ticket,
                metadata=metadata,
                staged_at_s=round(time.monotonic(), 4),
            )
            self._next_pre_gate_ticket += 1
            self._pre_gate_staged[reservation.reservation_ticket] = _PreGateAdmissionState(
                reservation=reservation
            )
            self._pre_gate_total_staged += 1
            self._pre_gate_peak_staged = max(
                self._pre_gate_peak_staged,
                len(self._pre_gate_staged),
            )
            self._condition.notify_all()
        return reservation

    def _claim_admission(self, reservation_ticket: int) -> None:
        with self._condition:
            state = self._pre_gate_staged.pop(reservation_ticket, None)
            if state is not None:
                self._pre_gate_total_claimed += 1
                self._condition.notify_all()

    def discard_admission(self, reservation_ticket: int) -> None:
        with self._condition:
            state = self._pre_gate_staged.pop(reservation_ticket, None)
            if state is not None:
                self._pre_gate_total_discarded += 1
                self._condition.notify_all()

    def _begin_turn(self) -> tuple[bool, float, float]:
        """Claim the next FIFO execution slot and return queue metadata."""
        enqueue_time = time.monotonic()
        with self._condition:
            ticket = self._next_ticket
            self._next_ticket += 1
            self._total_queued += 1
            was_queued = self._active or ticket != self._serving_ticket
            self._waiters += 1
            try:
                while self._active or ticket != self._serving_ticket:
                    self._condition.wait()
                wait_time = time.monotonic() - enqueue_time
                self._active = True
            finally:
                self._waiters -= 1
        return was_queued, wait_time, time.monotonic()

    def _finish_turn(self, *, exec_start: float, wait_time: float, served: bool) -> float:
        """Release the current FIFO slot and update gate metrics."""
        exec_time = time.monotonic() - exec_start
        with self._condition:
            if served:
                self._total_served += 1
            self._active = False
            self._serving_ticket += 1
            self._total_wait_s += wait_time
            self._total_exec_s += exec_time
            self._longest_wait_s = max(self._longest_wait_s, wait_time)
            self._longest_exec_s = max(self._longest_exec_s, exec_time)
            self._condition.notify_all()
        return exec_time

    def execute(self, fn: Callable[..., T], *args: Any, **kwargs: Any) -> GenerationResult:
        """Execute a generation function under the gate lock (blocking).

        If another generation is in progress, the caller blocks until it
        completes. This is the intended behavior — queuing is the serving
        discipline, not a bug.

        Args:
            fn: The generation callable (e.g., engine.generate).
            *args: Positional arguments passed to fn.
            **kwargs: Keyword arguments passed to fn.

        Returns:
            GenerationResult with the return value and timing metadata.
        """
        was_queued, wait_time, exec_start = self._begin_turn()
        served = False
        try:
            result = fn(*args, **kwargs)
            served = True
        finally:
            exec_time = self._finish_turn(
                exec_start=exec_start,
                wait_time=wait_time,
                served=served,
            )

        return GenerationResult(
            value=result,
            wait_time_s=round(wait_time, 4),
            execution_time_s=round(exec_time, 4),
            was_queued=was_queued,
        )

    def execute_with_admission(
        self,
        metadata: PreGateAdmissionMetadata,
        fn: Callable[..., T],
        *args: Any,
        **kwargs: Any,
    ) -> GenerationResult:
        """Execute under the gate after bounded pre-gate admission staging."""

        reservation = self.stage_admission(metadata)
        claimed = False
        began_turn = False
        was_queued = False
        wait_time = 0.0
        exec_start: float | None = None
        served = False
        try:
            was_queued, wait_time, exec_start = self._begin_turn()
            began_turn = True
            self._claim_admission(reservation.reservation_ticket)
            claimed = True
            result = fn(*args, **kwargs)
            served = True
        finally:
            if not claimed:
                self.discard_admission(reservation.reservation_ticket)
            exec_time = 0.0
            if began_turn and exec_start is not None:
                exec_time = self._finish_turn(
                    exec_start=exec_start,
                    wait_time=wait_time,
                    served=served,
                )

        return GenerationResult(
            value=result,
            wait_time_s=round(wait_time, 4),
            execution_time_s=round(exec_time, 4),
            was_queued=was_queued,
        )

    async def execute_async(
        self, fn: Callable[..., T], *args: Any, **kwargs: Any
    ) -> GenerationResult:
        """Execute a generation function via thread-pool executor under gate lock.

        This is the pattern for async HTTP servers (e.g., FastAPI with
        uvicorn). The event loop stays responsive for health probes while
        generation runs in the executor thread behind the gate.

        Args:
            fn: The generation callable.
            *args: Positional arguments passed to fn.
            **kwargs: Keyword arguments passed to fn.

        Returns:
            GenerationResult with the return value and timing metadata.
        """
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self.execute, fn, *args, **kwargs)

    async def execute_async_with_admission(
        self,
        metadata: PreGateAdmissionMetadata,
        fn: Callable[..., T],
        *args: Any,
        **kwargs: Any,
    ) -> GenerationResult:
        """Async executor path with bounded pre-gate admission staging."""

        loop = asyncio.get_running_loop()
        runner = partial(self.execute_with_admission, metadata, fn, *args, **kwargs)
        return await loop.run_in_executor(None, runner)

    @asynccontextmanager
    async def stream_session(self) -> AsyncIterator[GenerationResult]:
        """Hold GenerationGate for the full lifetime of a streaming response."""

        loop = asyncio.get_running_loop()
        was_queued, wait_time, exec_start = await loop.run_in_executor(
            None, self._begin_turn
        )
        try:
            yield GenerationResult(
                value=None,
                wait_time_s=round(wait_time, 4),
                execution_time_s=0.0,
                was_queued=was_queued,
            )
        finally:
            self._finish_turn(exec_start=exec_start, wait_time=wait_time, served=True)

    @asynccontextmanager
    async def stream_session_with_admission(
        self,
        metadata: PreGateAdmissionMetadata,
    ) -> AsyncIterator[GenerationResult]:
        """Hold GenerationGate after bounded pre-gate admission staging."""

        loop = asyncio.get_running_loop()
        reservation = await loop.run_in_executor(None, self.stage_admission, metadata)
        claimed = False
        began_turn = False
        was_queued = False
        wait_time = 0.0
        exec_start: float | None = None
        try:
            was_queued, wait_time, exec_start = await loop.run_in_executor(
                None, self._begin_turn
            )
            began_turn = True
            await loop.run_in_executor(
                None, self._claim_admission, reservation.reservation_ticket
            )
            claimed = True
            yield GenerationResult(
                value=None,
                wait_time_s=round(wait_time, 4),
                execution_time_s=0.0,
                was_queued=was_queued,
            )
        finally:
            if not claimed:
                await loop.run_in_executor(
                    None, self.discard_admission, reservation.reservation_ticket
                )
            if began_turn and exec_start is not None:
                self._finish_turn(exec_start=exec_start, wait_time=wait_time, served=True)

    @property
    def is_active(self) -> bool:
        """Whether a generation is currently in progress."""
        with self._condition:
            return self._active

    @property
    def status(self) -> dict[str, Any]:
        """Return gate status for runtime truth exposure.

        This dict is intended to be embedded in path-level runtime status
        payloads. It exposes honest serving discipline truth.
        """
        with self._condition:
            return {
                "generation_gate": "active" if self._active else "idle",
                "max_concurrent": MAX_GENERATION_CONCURRENCY,
                "queue_discipline": "serial",
                "queue_policy": "ticketed_fifo",
                "waiters": self._waiters,
                "total_served": self._total_served,
                "total_queued": self._total_queued,
                "total_wait_s": round(self._total_wait_s, 3),
                "total_exec_s": round(self._total_exec_s, 3),
                "longest_wait_s": round(self._longest_wait_s, 3),
                "longest_exec_s": round(self._longest_exec_s, 3),
                "pre_gate_admission": {
                    "hook_status": "present",
                    "hook_boundary": "before_whole_request_gate_claim",
                    "hook_mode": "bounded_runtime_owned_staging",
                    "capacity": self._pre_gate_capacity,
                    "staged_count": len(self._pre_gate_staged),
                    "peak_staged_count": self._pre_gate_peak_staged,
                    "total_staged": self._pre_gate_total_staged,
                    "total_claimed": self._pre_gate_total_claimed,
                    "total_discarded": self._pre_gate_total_discarded,
                    "staging_units": [
                        "immutable_request_metadata_snapshot",
                        "ticket_reservation_without_gate_claim",
                        "pre_claim_bounded_admission_bookkeeping",
                    ],
                    "preserved_post_claim_invariants": [
                        "max_concurrent_1_after_gate_claim",
                        "ticketed_fifo_after_gate_claim",
                        "serial_safety_validated_only_after_gate_claim",
                    ],
                    "forbidden_expansions": [
                        "no_bypass_of_whole_request_gate_claim",
                        "no_post_claim_reordering",
                        "no_post_claim_parallel_generation",
                        "no_child_exchange_from_pre_claim_hook",
                        "no_stream_rewrite_from_pre_claim_hook",
                    ],
                },
            }

    def reset_counters(self) -> None:
        """Reset serving counters. Does not affect the lock state."""
        with self._condition:
            self._total_served = 0
            self._total_queued = 0
            self._total_wait_s = 0.0
            self._total_exec_s = 0.0
            self._longest_wait_s = 0.0
            self._longest_exec_s = 0.0
            self._pre_gate_total_staged = 0
            self._pre_gate_total_claimed = 0
            self._pre_gate_total_discarded = 0
            self._pre_gate_peak_staged = len(self._pre_gate_staged)
