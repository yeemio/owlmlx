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
    staged_monotonic_s: float
    cohort_id: int
    claim_ticket: int
    joined_open_cohort: bool
    cohort_payload: Any | None = None


@dataclass(slots=True)
class _PreGateCohortState:
    cohort_id: int
    opened_at_s: float
    closes_at_s: float
    reservation_tickets: list[int] = field(default_factory=list)
    open_for_join: bool = True


@dataclass(slots=True)
class _CohortDispatchState:
    cohort_id: int
    reservation_tickets: list[int] = field(default_factory=list)
    claim_tickets: list[int] = field(default_factory=list)
    leader_reservation_ticket: int | None = None
    first_claim_ticket: int | None = None
    started: bool = False
    completed: bool = False
    remaining_consumers: int = 0
    result_values: dict[int, Any] = field(default_factory=dict)
    wait_times_by_reservation: dict[int, float] = field(default_factory=dict)
    queued_by_reservation: dict[int, bool] = field(default_factory=dict)
    execution_time_s: float = 0.0
    error: BaseException | None = None


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
        self._skipped_tickets: set[int] = set()
        self._next_pre_gate_ticket = 0
        self._next_pre_gate_cohort_id = 0
        self._waiters = 0
        self._total_served = 0
        self._total_queued = 0
        self._total_wait_s = 0.0
        self._total_exec_s = 0.0
        self._longest_wait_s = 0.0
        self._longest_exec_s = 0.0
        self._pre_gate_capacity = 32
        self._pre_gate_window_s = 0.02
        self._pre_gate_staged: dict[int, _PreGateAdmissionState] = {}
        self._pre_gate_cohorts: dict[int, _PreGateCohortState] = {}
        self._cohort_dispatches: dict[int, _CohortDispatchState] = {}
        self._reservation_to_cohort_id: dict[int, int] = {}
        self._open_pre_gate_cohort_id: int | None = None
        self._pre_gate_total_staged = 0
        self._pre_gate_total_claimed = 0
        self._pre_gate_total_discarded = 0
        self._pre_gate_total_cohorts = 0
        self._pre_gate_peak_staged = 0
        self._pre_gate_peak_cohort_size = 0
        self._pre_gate_total_window_wait_s = 0.0
        self._pre_gate_longest_window_wait_s = 0.0
        self._pre_gate_total_handoffs = 0
        self._pre_gate_active_handoff_request_count = 0
        self._pre_gate_last_handoff_request_count = 0

    def stage_admission(
        self,
        metadata: PreGateAdmissionMetadata,
        *,
        payload: Any | None = None,
    ) -> PreGateAdmissionReservation:
        """Reserve a bounded inert pre-gate admission slot.

        This is the only new pre-claim structure introduced by the runtime:
        immutable request metadata plus bounded cohort-window membership before
        whole-request gate claim.
        """

        with self._condition:
            while len(self._pre_gate_staged) >= self._pre_gate_capacity:
                self._condition.wait()
            now = time.monotonic()
            cohort = self._cohort_for_new_reservation_locked(now)
            joined_open_cohort = bool(cohort.reservation_tickets)
            dispatch = self._cohort_dispatches[cohort.cohort_id]
            reservation = PreGateAdmissionReservation(
                reservation_ticket=self._next_pre_gate_ticket,
                metadata=metadata,
                staged_at_s=round(now, 4),
            )
            claim_ticket = self._next_ticket
            self._next_pre_gate_ticket += 1
            self._next_ticket += 1
            self._total_queued += 1
            cohort.reservation_tickets.append(reservation.reservation_ticket)
            self._pre_gate_peak_cohort_size = max(
                self._pre_gate_peak_cohort_size,
                len(cohort.reservation_tickets),
            )
            self._pre_gate_staged[reservation.reservation_ticket] = _PreGateAdmissionState(
                reservation=reservation,
                staged_monotonic_s=now,
                cohort_id=cohort.cohort_id,
                claim_ticket=claim_ticket,
                joined_open_cohort=joined_open_cohort,
                cohort_payload=payload,
            )
            dispatch.reservation_tickets.append(reservation.reservation_ticket)
            dispatch.claim_tickets.append(claim_ticket)
            if dispatch.leader_reservation_ticket is None:
                dispatch.leader_reservation_ticket = reservation.reservation_ticket
                dispatch.first_claim_ticket = claim_ticket
            dispatch.remaining_consumers = len(dispatch.reservation_tickets)
            self._reservation_to_cohort_id[reservation.reservation_ticket] = cohort.cohort_id
            self._pre_gate_total_staged += 1
            self._pre_gate_peak_staged = max(
                self._pre_gate_peak_staged,
                len(self._pre_gate_staged),
            )
            self._condition.notify_all()
        return reservation

    def _cohort_for_new_reservation_locked(self, now: float) -> _PreGateCohortState:
        self._seal_expired_open_cohort_locked(now)
        cohort: _PreGateCohortState | None = None
        if self._open_pre_gate_cohort_id is not None:
            cohort = self._pre_gate_cohorts.get(self._open_pre_gate_cohort_id)
        if cohort is None or not cohort.open_for_join:
            cohort = _PreGateCohortState(
                cohort_id=self._next_pre_gate_cohort_id,
                opened_at_s=round(now, 4),
                closes_at_s=now + self._pre_gate_window_s,
            )
            self._next_pre_gate_cohort_id += 1
            self._pre_gate_cohorts[cohort.cohort_id] = cohort
            self._cohort_dispatches[cohort.cohort_id] = _CohortDispatchState(
                cohort_id=cohort.cohort_id
            )
            self._open_pre_gate_cohort_id = cohort.cohort_id
            self._pre_gate_total_cohorts += 1
        return cohort

    def _seal_expired_open_cohort_locked(self, now: float | None = None) -> None:
        if self._open_pre_gate_cohort_id is None:
            return
        cohort = self._pre_gate_cohorts.get(self._open_pre_gate_cohort_id)
        if cohort is None:
            self._open_pre_gate_cohort_id = None
            return
        current_time = time.monotonic() if now is None else now
        if cohort.open_for_join and current_time >= cohort.closes_at_s:
            cohort.open_for_join = False
            self._open_pre_gate_cohort_id = None

    def _await_cohort_window(self, reservation_ticket: int) -> float:
        wait_started = time.monotonic()
        with self._condition:
            while True:
                state = self._pre_gate_staged.get(reservation_ticket)
                if state is None:
                    break
                cohort = self._pre_gate_cohorts.get(state.cohort_id)
                if cohort is None:
                    break
                now = time.monotonic()
                if cohort.open_for_join:
                    remaining = cohort.closes_at_s - now
                    if remaining > 0:
                        self._condition.wait(timeout=remaining)
                        continue
                    cohort.open_for_join = False
                    if self._open_pre_gate_cohort_id == cohort.cohort_id:
                        self._open_pre_gate_cohort_id = None
                    self._condition.notify_all()
                break
        waited = time.monotonic() - wait_started
        with self._condition:
            self._pre_gate_total_window_wait_s += waited
            self._pre_gate_longest_window_wait_s = max(
                self._pre_gate_longest_window_wait_s,
                waited,
            )
        return waited

    def _cohort_dispatch_for_reservation_locked(
        self,
        reservation_ticket: int,
    ) -> _CohortDispatchState | None:
        cohort_id = self._reservation_to_cohort_id.get(reservation_ticket)
        if cohort_id is None:
            return None
        return self._cohort_dispatches.get(cohort_id)

    def _claim_cohort_admission_locked(self, reservation_tickets: tuple[int, ...]) -> None:
        claimed_count = 0
        for reservation_ticket in reservation_tickets:
            state = self._pre_gate_staged.pop(reservation_ticket, None)
            if state is None:
                continue
            cohort = self._pre_gate_cohorts.get(state.cohort_id)
            if cohort is not None and reservation_ticket in cohort.reservation_tickets:
                cohort.reservation_tickets.remove(reservation_ticket)
                if not cohort.reservation_tickets:
                    self._pre_gate_cohorts.pop(cohort.cohort_id, None)
                    if self._open_pre_gate_cohort_id == cohort.cohort_id:
                        self._open_pre_gate_cohort_id = None
            claimed_count += 1
        if claimed_count:
            self._pre_gate_total_claimed += claimed_count
            self._condition.notify_all()

    def _consume_cohort_dispatch_locked(
        self,
        reservation_ticket: int,
    ) -> tuple[Any, float, float, bool, BaseException | None]:
        dispatch = self._cohort_dispatch_for_reservation_locked(reservation_ticket)
        if dispatch is None:
            raise RuntimeError("cohort dispatch disappeared before result consumption")
        value = dispatch.result_values.get(reservation_ticket)
        wait_time = dispatch.wait_times_by_reservation.get(reservation_ticket, 0.0)
        was_queued = dispatch.queued_by_reservation.get(reservation_ticket, False)
        error = dispatch.error
        dispatch.remaining_consumers = max(dispatch.remaining_consumers - 1, 0)
        if dispatch.remaining_consumers == 0:
            self._cohort_dispatches.pop(dispatch.cohort_id, None)
            for ticket in dispatch.reservation_tickets:
                self._reservation_to_cohort_id.pop(ticket, None)
        return value, wait_time, dispatch.execution_time_s, was_queued, error

    def _claim_admission(self, reservation_ticket: int) -> None:
        with self._condition:
            state = self._pre_gate_staged.pop(reservation_ticket, None)
            if state is not None:
                self._remove_from_cohort_locked(state)
                self._pre_gate_total_claimed += 1
                self._condition.notify_all()

    def discard_admission(self, reservation_ticket: int) -> None:
        with self._condition:
            state = self._pre_gate_staged.pop(reservation_ticket, None)
            if state is not None:
                self._remove_from_cohort_locked(state)
                self._skip_ticket_locked(state.claim_ticket)
                self._pre_gate_total_discarded += 1
                self._condition.notify_all()

    def _remove_from_cohort_locked(self, state: _PreGateAdmissionState) -> None:
        reservation_ticket = state.reservation.reservation_ticket
        self._reservation_to_cohort_id.pop(reservation_ticket, None)
        cohort = self._pre_gate_cohorts.get(state.cohort_id)
        if cohort is None:
            dispatch = self._cohort_dispatches.get(state.cohort_id)
            if dispatch is not None and not dispatch.started:
                self._remove_from_dispatch_locked(dispatch, reservation_ticket)
            return
        if reservation_ticket in cohort.reservation_tickets:
            cohort.reservation_tickets.remove(reservation_ticket)
        dispatch = self._cohort_dispatches.get(state.cohort_id)
        if dispatch is not None and not dispatch.started:
            self._remove_from_dispatch_locked(dispatch, reservation_ticket)
        if not cohort.reservation_tickets:
            self._pre_gate_cohorts.pop(cohort.cohort_id, None)
            if self._open_pre_gate_cohort_id == cohort.cohort_id:
                self._open_pre_gate_cohort_id = None
            if dispatch is not None and not dispatch.started and not dispatch.reservation_tickets:
                self._cohort_dispatches.pop(cohort.cohort_id, None)

    def _remove_from_dispatch_locked(
        self,
        dispatch: _CohortDispatchState,
        reservation_ticket: int,
    ) -> None:
        if reservation_ticket not in dispatch.reservation_tickets:
            return
        index = dispatch.reservation_tickets.index(reservation_ticket)
        dispatch.reservation_tickets.pop(index)
        dispatch.claim_tickets.pop(index)
        dispatch.remaining_consumers = len(dispatch.reservation_tickets)
        if dispatch.reservation_tickets:
            dispatch.leader_reservation_ticket = dispatch.reservation_tickets[0]
            dispatch.first_claim_ticket = dispatch.claim_tickets[0]
        else:
            dispatch.leader_reservation_ticket = None
            dispatch.first_claim_ticket = None

    def _skip_ticket_locked(self, ticket: int) -> None:
        self._skipped_tickets.add(ticket)
        self._advance_serving_ticket_locked()

    def _advance_serving_ticket_locked(self) -> None:
        while self._serving_ticket in self._skipped_tickets:
            self._skipped_tickets.remove(self._serving_ticket)
            self._serving_ticket += 1

    def _ticket_for_reservation(self, reservation_ticket: int) -> int | None:
        with self._condition:
            state = self._pre_gate_staged.get(reservation_ticket)
            if state is None:
                return None
            return state.claim_ticket

    def _reservation_joined_open_cohort(self, reservation_ticket: int) -> bool:
        with self._condition:
            state = self._pre_gate_staged.get(reservation_ticket)
            if state is None:
                return False
            return state.joined_open_cohort

    def _begin_turn(self) -> tuple[bool, float, float]:
        """Claim the next FIFO execution slot and return queue metadata."""
        with self._condition:
            ticket = self._next_ticket
            self._next_ticket += 1
            self._total_queued += 1
        return self._begin_turn_for_ticket(ticket)

    def _begin_turn_for_ticket(self, ticket: int) -> tuple[bool, float, float]:
        """Wait for the provided FIFO execution slot and return queue metadata."""
        enqueue_time = time.monotonic()
        with self._condition:
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

    def _finish_claimed_turn(
        self,
        *,
        exec_start: float,
        wait_times: tuple[float, ...],
        served_count: int,
        claim_ticket_count: int,
    ) -> float:
        """Release the current FIFO slot and update gate metrics."""
        exec_time = time.monotonic() - exec_start
        longest_wait = max(wait_times, default=0.0)
        with self._condition:
            if served_count > 0:
                self._total_served += served_count
            self._active = False
            self._serving_ticket += claim_ticket_count
            self._advance_serving_ticket_locked()
            self._total_wait_s += sum(wait_times)
            self._total_exec_s += exec_time * max(served_count, 1)
            self._longest_wait_s = max(self._longest_wait_s, longest_wait)
            self._longest_exec_s = max(self._longest_exec_s, exec_time)
            self._condition.notify_all()
        return exec_time

    def _finish_turn(self, *, exec_start: float, wait_time: float, served: bool) -> float:
        return self._finish_claimed_turn(
            exec_start=exec_start,
            wait_times=(wait_time,),
            served_count=1 if served else 0,
            claim_ticket_count=1,
        )

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
            claim_ticket = self._ticket_for_reservation(reservation.reservation_ticket)
            if claim_ticket is None:
                raise RuntimeError("pre-gate reservation disappeared before claim")
            joined_open_cohort = self._reservation_joined_open_cohort(
                reservation.reservation_ticket
            )
            cohort_wait = self._await_cohort_window(reservation.reservation_ticket)
            was_queued, gate_wait, exec_start = self._begin_turn_for_ticket(claim_ticket)
            was_queued = was_queued or joined_open_cohort
            wait_time = cohort_wait + gate_wait
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

    def execute_cohort_with_admission(
        self,
        metadata: PreGateAdmissionMetadata,
        request_payload: Any,
        single_fn: Callable[[Any], T],
        cohort_fn: Callable[[tuple[Any, ...]], tuple[T, ...]],
    ) -> GenerationResult:
        """Execute a bounded non-stream cohort without reopening post-claim invariants."""

        reservation = self.stage_admission(metadata, payload=request_payload)
        self._await_cohort_window(reservation.reservation_ticket)
        with self._condition:
            dispatch = self._cohort_dispatch_for_reservation_locked(
                reservation.reservation_ticket
            )
            if dispatch is None:
                raise RuntimeError("cohort dispatch disappeared before handoff")
            is_leader = dispatch.leader_reservation_ticket == reservation.reservation_ticket
            if not is_leader:
                while not dispatch.completed and dispatch.error is None:
                    self._condition.wait()
                value, wait_time, exec_time, was_queued, error = (
                    self._consume_cohort_dispatch_locked(reservation.reservation_ticket)
                )
                if error is not None:
                    raise error
                return GenerationResult(
                    value=value,
                    wait_time_s=round(wait_time, 4),
                    execution_time_s=round(exec_time, 4),
                    was_queued=was_queued,
                )

            dispatch.started = True
            reservation_tickets = tuple(dispatch.reservation_tickets)
            staged_states = tuple(
                self._pre_gate_staged[ticket] for ticket in reservation_tickets
            )
            if dispatch.first_claim_ticket is None:
                raise RuntimeError("cohort dispatch missing first claim ticket")

        leader_was_queued, gate_wait, exec_start = self._begin_turn_for_ticket(
            dispatch.first_claim_ticket
        )
        claim_waits = {
            state.reservation.reservation_ticket: max(
                exec_start - state.staged_monotonic_s,
                0.0,
            )
            for state in staged_states
        }
        queued_by_reservation = {
            state.reservation.reservation_ticket: (
                state.joined_open_cohort or leader_was_queued
            )
            for state in staged_states
        }
        reservation_tickets = tuple(
            state.reservation.reservation_ticket for state in staged_states
        )
        cohort_size = len(reservation_tickets)
        with self._condition:
            self._claim_cohort_admission_locked(reservation_tickets)
            if cohort_size > 1:
                self._pre_gate_total_handoffs += 1
                self._pre_gate_active_handoff_request_count = cohort_size
                self._pre_gate_last_handoff_request_count = cohort_size

        try:
            payloads = tuple(state.cohort_payload for state in staged_states)
            if cohort_size <= 1:
                values = (single_fn(payloads[0]),)
            else:
                values = tuple(cohort_fn(payloads))
            if len(values) != cohort_size:
                raise RuntimeError(
                    "cohort handoff returned a mismatched number of results"
                )
            exec_time = self._finish_claimed_turn(
                exec_start=exec_start,
                wait_times=tuple(claim_waits[ticket] for ticket in reservation_tickets),
                served_count=cohort_size,
                claim_ticket_count=cohort_size,
            )
        except BaseException as error:
            exec_time = self._finish_claimed_turn(
                exec_start=exec_start,
                wait_times=tuple(claim_waits[ticket] for ticket in reservation_tickets),
                served_count=0,
                claim_ticket_count=cohort_size,
            )
            with self._condition:
                if cohort_size > 1:
                    self._pre_gate_active_handoff_request_count = 0
                dispatch = self._cohort_dispatch_for_reservation_locked(
                    reservation.reservation_ticket
                )
                if dispatch is None:
                    raise RuntimeError("cohort dispatch disappeared after failure") from error
                dispatch.wait_times_by_reservation = dict(claim_waits)
                dispatch.queued_by_reservation = dict(queued_by_reservation)
                dispatch.execution_time_s = exec_time
                dispatch.error = error
                dispatch.completed = True
                self._condition.notify_all()
                _, wait_time, shared_exec_time, was_queued, shared_error = (
                    self._consume_cohort_dispatch_locked(reservation.reservation_ticket)
                )
            if shared_error is not None:
                raise shared_error
            raise error

        with self._condition:
            if cohort_size > 1:
                self._pre_gate_active_handoff_request_count = 0
            dispatch = self._cohort_dispatch_for_reservation_locked(
                reservation.reservation_ticket
            )
            if dispatch is None:
                raise RuntimeError("cohort dispatch disappeared after execution")
            dispatch.result_values = {
                ticket: value for ticket, value in zip(reservation_tickets, values)
            }
            dispatch.wait_times_by_reservation = dict(claim_waits)
            dispatch.queued_by_reservation = dict(queued_by_reservation)
            dispatch.execution_time_s = exec_time
            dispatch.completed = True
            self._condition.notify_all()
            value, wait_time, shared_exec_time, was_queued, error = (
                self._consume_cohort_dispatch_locked(reservation.reservation_ticket)
            )
        if error is not None:
            raise error
        return GenerationResult(
            value=value,
            wait_time_s=round(wait_time, 4),
            execution_time_s=round(shared_exec_time, 4),
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

    async def execute_async_cohort_with_admission(
        self,
        metadata: PreGateAdmissionMetadata,
        request_payload: Any,
        single_fn: Callable[[Any], T],
        cohort_fn: Callable[[tuple[Any, ...]], tuple[T, ...]],
    ) -> GenerationResult:
        """Async executor path for bounded non-stream cohort handoff."""

        loop = asyncio.get_running_loop()
        runner = partial(
            self.execute_cohort_with_admission,
            metadata,
            request_payload,
            single_fn,
            cohort_fn,
        )
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
            claim_ticket = await loop.run_in_executor(
                None, self._ticket_for_reservation, reservation.reservation_ticket
            )
            if claim_ticket is None:
                raise RuntimeError("pre-gate reservation disappeared before claim")
            joined_open_cohort = await loop.run_in_executor(
                None,
                self._reservation_joined_open_cohort,
                reservation.reservation_ticket,
            )
            cohort_wait = await loop.run_in_executor(
                None, self._await_cohort_window, reservation.reservation_ticket
            )
            was_queued, wait_time, exec_start = await loop.run_in_executor(
                None, self._begin_turn_for_ticket, claim_ticket
            )
            was_queued = was_queued or joined_open_cohort
            wait_time += cohort_wait
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
            self._seal_expired_open_cohort_locked()
            open_cohort = (
                self._pre_gate_cohorts.get(self._open_pre_gate_cohort_id)
                if self._open_pre_gate_cohort_id is not None
                else None
            )
            staged_cohort_count = sum(
                1
                for cohort in self._pre_gate_cohorts.values()
                if cohort.reservation_tickets
            )
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
                    "hook_mode": "bounded_runtime_owned_cohort_window",
                    "capacity": self._pre_gate_capacity,
                    "window_ms": int(self._pre_gate_window_s * 1000),
                    "cohort_window_status": (
                        "open_for_join"
                        if open_cohort is not None and open_cohort.reservation_tickets
                        else "closed_waiting_gate_claim"
                        if self._pre_gate_staged
                        else "idle"
                    ),
                    "cohort_count": staged_cohort_count,
                    "open_cohort_size": (
                        len(open_cohort.reservation_tickets) if open_cohort is not None else 0
                    ),
                    "peak_cohort_size": self._pre_gate_peak_cohort_size,
                    "total_cohorts_formed": self._pre_gate_total_cohorts,
                    "total_window_wait_s": round(self._pre_gate_total_window_wait_s, 3),
                    "longest_window_wait_s": round(
                        self._pre_gate_longest_window_wait_s, 3
                    ),
                    "cohort_handoff_status": (
                        "active_to_aggregated_child_exchange"
                        if self._pre_gate_active_handoff_request_count > 0
                        else "visible"
                        if self._pre_gate_total_handoffs > 0
                        else "not_visible"
                    ),
                    "active_handoff_request_count": (
                        self._pre_gate_active_handoff_request_count
                    ),
                    "last_handoff_request_count": (
                        self._pre_gate_last_handoff_request_count
                    ),
                    "total_handoffs": self._pre_gate_total_handoffs,
                    "aggregation_scope": "pre_claim_window_only",
                    "staged_count": len(self._pre_gate_staged),
                    "peak_staged_count": self._pre_gate_peak_staged,
                    "total_staged": self._pre_gate_total_staged,
                    "total_claimed": self._pre_gate_total_claimed,
                    "total_discarded": self._pre_gate_total_discarded,
                    "staging_units": [
                        "immutable_request_metadata_snapshot",
                        "ticket_reservation_without_gate_claim",
                        "bounded_pre_claim_cohort_window_membership",
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
            self._pre_gate_total_cohorts = len(self._pre_gate_cohorts)
            self._pre_gate_peak_staged = len(self._pre_gate_staged)
            self._pre_gate_peak_cohort_size = max(
                (len(cohort.reservation_tickets) for cohort in self._pre_gate_cohorts.values()),
                default=0,
            )
            self._pre_gate_total_window_wait_s = 0.0
            self._pre_gate_longest_window_wait_s = 0.0
            self._pre_gate_total_handoffs = 0
            self._pre_gate_active_handoff_request_count = 0
            self._pre_gate_last_handoff_request_count = 0
