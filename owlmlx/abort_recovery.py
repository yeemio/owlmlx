"""owlmlx serving-path abort recovery state machine.

Defines the runtime substrate truth of whether the MLX/Metal engine
can be trusted after a high-context abort. This is the third and final
module in the substrate boundary trio:

1. memory_budget.py  — can this model fit?
2. context_concurrency.py — how many concurrent requests are safe?
3. abort_recovery.py (this) — after an abort, is the substrate clean?

This is serving-path only. Training abort scenarios are explicitly out
of scope (contract Rule 7).

Runtime truth this module owns:

- Substrate health states: clean / probing / contaminated
- State transition rules (deterministic, testable)
- Abort event recording with bounded history
- Contamination reason semantics
- Recovery-required predicate
- Snapshot for runtime status exposure (no transport state)

What this module does NOT own (stays in router / control-plane):

- httpx health probe execution
- asyncio.create_task() scheduling
- Request blocking enforcement
- API endpoint exposure
- Operator restart orchestration

This module is self-contained. It does not import httpx, asyncio
networking, or any platform module. If llm_router/abort_recovery.py
were deleted, this module would still function (contract Rule 8).

Hardware truth source: Phase 42 R3A verified that after a 256K prefill
abort on oMLX 0.3.2, the scheduler can enter a reschedule loop and
evict the model. The state machine captures this substrate behavior.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from enum import Enum
from typing import Any

from owlmlx.context_concurrency import HIGH_CONTEXT_THRESHOLD_TOKENS


# ── Substrate health states ────────────────────────────────────────────────────

class SubstrateState(str, Enum):
    """Health state of the MLX/Metal substrate after serving operations.

    Values:
        clean: Substrate is healthy and trustworthy for all request types.
        probing: A high-context abort was detected; health verification
            is in progress. The substrate may or may not be trustworthy.
        contaminated: Health verification failed after an abort. The
            substrate is not trustworthy for high-context requests until
            recovery (typically an engine restart + successful probe).
    """

    clean = "clean"
    probing = "probing"
    contaminated = "contaminated"


# ── Abort event record ─────────────────────────────────────────────────────────

@dataclass(frozen=True, slots=True)
class AbortEvent:
    """Record of a single high-context abort.

    This is a runtime event fact — what happened, when, and why.
    No transport or enforcement information.

    Attributes:
        timestamp: Unix timestamp of the abort.
        context_tokens: Estimated context length that triggered the abort.
        error_type: Classification of the failure (e.g., "stream_error").
        detail: Optional short description (truncated to 200 chars).
    """

    timestamp: float
    context_tokens: int
    error_type: str
    detail: str = ""


# ── Configuration ──────────────────────────────────────────────────────────────

MAX_ABORT_HISTORY: int = 20
SNAPSHOT_RECENT_ABORTS: int = 5


# ── State machine ──────────────────────────────────────────────────────────────

class AbortRecoveryTracker:
    """Tracks substrate health after high-context stream aborts.

    State machine:

        CLEAN → (high-context abort) → PROBING
        PROBING → (probe pass) → CLEAN
        PROBING → (probe fail) → CONTAMINATED
        CONTAMINATED → (recovery success) → CLEAN
        CONTAMINATED → (recovery fail) → CONTAMINATED
        Any state → (force clean) → CLEAN

    Sub-threshold aborts (context_tokens <= HIGH_CONTEXT_THRESHOLD_TOKENS)
    are recorded but do not trigger state transitions.

    This class owns no I/O. The caller (router/control-plane) is
    responsible for executing health probes and calling the appropriate
    transition methods based on probe results.
    """

    def __init__(self) -> None:
        self._state: SubstrateState = SubstrateState.clean
        self._abort_history: list[AbortEvent] = []
        self._total_aborts: int = 0
        self._total_high_context_aborts: int = 0
        self._total_recoveries: int = 0
        self._last_probe_at: float = 0.0
        self._last_probe_ok: bool | None = None
        self._last_recovery_at: float = 0.0
        self._contamination_reason: str = ""

    # ── State queries ──────────────────────────────────────────────────

    @property
    def state(self) -> SubstrateState:
        """Current substrate health state."""
        return self._state

    def is_recovery_required(self) -> bool:
        """Whether the substrate requires recovery before high-context work."""
        return self._state == SubstrateState.contaminated

    def is_clean(self) -> bool:
        """Whether the substrate is fully trustworthy."""
        return self._state == SubstrateState.clean

    def is_probing(self) -> bool:
        """Whether a health probe is in progress."""
        return self._state == SubstrateState.probing

    # ── Abort recording ────────────────────────────────────────────────

    def record_abort(
        self,
        context_tokens: int,
        error_type: str,
        detail: str = "",
        *,
        now: float | None = None,
    ) -> bool:
        """Record an abort event. Returns True if this triggers probing.

        Sub-threshold aborts are recorded in history but do NOT trigger
        a state transition. Only aborts above HIGH_CONTEXT_THRESHOLD_TOKENS
        move the state machine to probing.

        Args:
            context_tokens: Estimated context length of the aborted request.
            error_type: Classification of the failure.
            detail: Optional detail string (truncated to 200 chars).
            now: Optional timestamp override (for testing). Defaults to
                time.time().

        Returns:
            True if the abort triggered a probing transition (high-context
            abort while in clean state). False otherwise.
        """
        ts = now if now is not None else time.time()
        event = AbortEvent(
            timestamp=ts,
            context_tokens=context_tokens,
            error_type=error_type,
            detail=detail[:200],
        )
        self._abort_history.append(event)
        if len(self._abort_history) > MAX_ABORT_HISTORY:
            self._abort_history = self._abort_history[-MAX_ABORT_HISTORY:]
        self._total_aborts += 1

        if context_tokens <= HIGH_CONTEXT_THRESHOLD_TOKENS:
            return False

        self._total_high_context_aborts += 1

        if self._state == SubstrateState.contaminated:
            # Already contaminated — don't re-enter probing
            return False

        self._state = SubstrateState.probing
        return True

    # ── Probe result transitions ───────────────────────────────────────

    def apply_probe_result(
        self,
        passed: bool,
        *,
        reason: str = "",
        now: float | None = None,
    ) -> SubstrateState:
        """Apply the result of a health probe to the state machine.

        The caller (router/control-plane) executes the actual probe
        (e.g., httpx request to oMLX). This method only processes
        the boolean result.

        Args:
            passed: True if the health probe succeeded.
            reason: If probe failed, why the substrate is contaminated.
            now: Optional timestamp override.

        Returns:
            The new substrate state after applying the probe result.
        """
        ts = now if now is not None else time.time()
        self._last_probe_at = ts
        self._last_probe_ok = passed

        if passed:
            self._state = SubstrateState.clean
            self._contamination_reason = ""
        else:
            self._state = SubstrateState.contaminated
            self._contamination_reason = (
                reason or "substrate failed health probe after high-context abort"
            )

        return self._state

    # ── Recovery transitions ───────────────────────────────────────────

    def apply_recovery_result(
        self,
        passed: bool,
        *,
        reason: str = "",
        now: float | None = None,
    ) -> SubstrateState:
        """Apply the result of a recovery attempt.

        Called after an external action (e.g., engine restart) followed
        by a health probe. Semantically identical to apply_probe_result
        but also increments recovery counters on success.

        Args:
            passed: True if the recovery probe succeeded.
            reason: If recovery failed, why contamination persists.
            now: Optional timestamp override.

        Returns:
            The new substrate state after the recovery attempt.
        """
        ts = now if now is not None else time.time()
        self._last_probe_at = ts
        self._last_probe_ok = passed

        if passed:
            self._state = SubstrateState.clean
            self._contamination_reason = ""
            self._total_recoveries += 1
            self._last_recovery_at = ts
        else:
            self._state = SubstrateState.contaminated
            self._contamination_reason = (
                reason or "substrate failed health probe during recovery attempt"
            )

        return self._state

    def force_clean(self, *, now: float | None = None) -> str:
        """Operator override: force state to clean without a probe.

        Records the previous state for audit purposes. If transitioning
        from contaminated, increments recovery count.

        Args:
            now: Optional timestamp override.

        Returns:
            The previous state (before forcing clean).
        """
        ts = now if now is not None else time.time()
        previous = self._state.value

        if self._state == SubstrateState.contaminated:
            self._total_recoveries += 1
            self._last_recovery_at = ts

        self._state = SubstrateState.clean
        self._contamination_reason = ""
        return previous

    # ── Status exposure ────────────────────────────────────────────────

    def snapshot(self) -> dict[str, Any]:
        """Return substrate health truth for runtime status exposure.

        This dict contains only runtime truth — no HTTP endpoints, no
        semaphore state, no router enforcement details.

        Returns:
            Dict suitable for embedding in runtime status payloads.
        """
        recent_aborts = [
            {
                "timestamp": e.timestamp,
                "context_tokens": e.context_tokens,
                "error_type": e.error_type,
                "detail": e.detail,
            }
            for e in self._abort_history[-SNAPSHOT_RECENT_ABORTS:]
        ]

        return {
            "state": self._state.value,
            "recovery_required": self.is_recovery_required(),
            "contamination_reason": self._contamination_reason,
            "total_aborts": self._total_aborts,
            "total_high_context_aborts": self._total_high_context_aborts,
            "total_recoveries": self._total_recoveries,
            "last_abort_at": (
                self._abort_history[-1].timestamp if self._abort_history else None
            ),
            "last_probe_at": self._last_probe_at or None,
            "last_probe_ok": self._last_probe_ok,
            "last_recovery_at": self._last_recovery_at or None,
            "recent_aborts": recent_aborts,
            "high_context_threshold_tokens": HIGH_CONTEXT_THRESHOLD_TOKENS,
        }
