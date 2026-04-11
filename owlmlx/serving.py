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
        self._lock = threading.Lock()
        self._active = False
        self._total_served = 0
        self._total_queued = 0
        self._total_wait_s = 0.0
        self._total_exec_s = 0.0
        self._longest_wait_s = 0.0
        self._longest_exec_s = 0.0

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
        enqueue_time = time.monotonic()
        self._total_queued += 1
        was_queued = self._active

        with self._lock:
            wait_time = time.monotonic() - enqueue_time
            self._active = True
            exec_start = time.monotonic()
            try:
                result = fn(*args, **kwargs)
                self._total_served += 1
            finally:
                exec_time = time.monotonic() - exec_start
                self._active = False
                self._total_wait_s += wait_time
                self._total_exec_s += exec_time
                self._longest_wait_s = max(self._longest_wait_s, wait_time)
                self._longest_exec_s = max(self._longest_exec_s, exec_time)

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

    @asynccontextmanager
    async def stream_session(self) -> AsyncIterator[GenerationResult]:
        """Hold GenerationGate for the full lifetime of a streaming response."""

        enqueue_time = time.monotonic()
        self._total_queued += 1
        was_queued = self._active
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, self._lock.acquire)
        wait_time = time.monotonic() - enqueue_time
        exec_start = time.monotonic()
        self._active = True
        try:
            yield GenerationResult(
                value=None,
                wait_time_s=round(wait_time, 4),
                execution_time_s=0.0,
                was_queued=was_queued,
            )
            self._total_served += 1
        finally:
            exec_time = time.monotonic() - exec_start
            self._active = False
            self._total_wait_s += wait_time
            self._total_exec_s += exec_time
            self._longest_wait_s = max(self._longest_wait_s, wait_time)
            self._longest_exec_s = max(self._longest_exec_s, exec_time)
            self._lock.release()

    @property
    def is_active(self) -> bool:
        """Whether a generation is currently in progress."""
        return self._active

    @property
    def status(self) -> dict[str, Any]:
        """Return gate status for runtime truth exposure.

        This dict is intended to be embedded in path-level runtime status
        payloads. It exposes honest serving discipline truth.
        """
        return {
            "generation_gate": "active" if self._active else "idle",
            "max_concurrent": MAX_GENERATION_CONCURRENCY,
            "queue_discipline": "serial",
            "total_served": self._total_served,
            "total_queued": self._total_queued,
            "total_wait_s": round(self._total_wait_s, 3),
            "total_exec_s": round(self._total_exec_s, 3),
            "longest_wait_s": round(self._longest_wait_s, 3),
            "longest_exec_s": round(self._longest_exec_s, 3),
        }

    def reset_counters(self) -> None:
        """Reset serving counters. Does not affect the lock state."""
        self._total_served = 0
        self._total_queued = 0
        self._total_wait_s = 0.0
        self._total_exec_s = 0.0
        self._longest_wait_s = 0.0
        self._longest_exec_s = 0.0
