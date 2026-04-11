"""owlmlx runtime health semantics.

Defines the canonical vocabulary for runtime health states and provides
pure derivation functions that combine individual signals into composite
health assessments. This is the fourth module in the substrate truth family:

1. memory_budget.py     — can this model fit?
2. context_concurrency.py — how many concurrent requests are safe?
3. abort_recovery.py    — after an abort, is the substrate clean?
4. runtime_health.py (this) — overall, is the runtime ready to serve?

This module owns:

- Load state labels (is the model in memory?)
- Inference health labels (is the backend serving?)
- Wait tier labels (how long until this model can serve?)
- Truth level labels (how confident is the load state assessment?)
- Runtime readiness labels (composite: can the runtime serve right now?)
- Platform status labels (system-wide: healthy / degraded / unavailable)
- Pure derivation functions for all composite labels
- Normalization functions (raw string → canonical enum)

What this module does NOT own (stays in platform):

- HTTP health probes, socket checks, tmux session detection
- Backend-specific introspection (oMLX engine_pool, vLLM model lists)
- Memory heuristics for partial loading
- Preflight check execution and recovery actions
- Dashboard rendering and API endpoint transport
- Restart / auto-heal policy decisions

This module is self-contained. It does not import httpx, asyncio
networking, subprocess, or any platform module.
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from owlmlx.abort_recovery import SubstrateState


# ── Load state ─────────────────────────────────────────────────────────────────

class LoadState(str, Enum):
    """Whether a model is loaded into backend memory.

    Phase 22 5-tier system. Determined by platform probing, but the
    semantic definitions are runtime truth.

    Values:
        true_loaded: Backend confirms this specific model is loaded and
            available for inference. Strongest signal.
        inferred_loaded: Backend is serving and indirect evidence suggests
            this model is loaded (e.g., router reports it, memory heuristic
            matches), but per-model confirmation is unavailable.
        cold: Backend is reachable and serving, but this model is NOT
            currently loaded. Loading it will take time.
        unavailable: Backend is down or unreachable. Cannot determine
            whether the model is loaded.
        unknown: No signal available (e.g., router not responding).
            Weaker than unavailable because we can't even tell if the
            backend exists.
    """

    true_loaded = "true_loaded"
    inferred_loaded = "inferred_loaded"
    cold = "cold"
    unavailable = "unavailable"
    unknown = "unknown"


# ── Inference health ───────────────────────────────────────────────────────────

class InferenceHealth(str, Enum):
    """Whether a backend can currently perform inference.

    Determined by platform probing (API calls), but the label meanings
    are runtime truth.

    Values:
        serving: Backend API is responsive and inference is ready.
            At least one model is loaded and completions succeed.
        stale: Backend process is alive and reachable, but inference
            is broken — typically loaded_count == 0 (oMLX evicted models)
            or health check reports unhealthy.
        reachable_not_serving: Port is open and backend responds to
            basic requests, but it is not in a state to serve inference
            (e.g., no models configured, startup incomplete).
        down: Backend port is not open. Process may not be running.
        not_applicable: Not an inference backend (e.g., router,
            dashboard, auxiliary services).
    """

    serving = "serving"
    stale = "stale"
    reachable_not_serving = "reachable_not_serving"
    down = "down"
    not_applicable = "not_applicable"


# ── Wait tier ──────────────────────────────────────────────────────────────────

class WaitTier(str, Enum):
    """How long a user should expect to wait before a model can serve.

    Derived from load state and model characteristics. No probing needed
    to compute this — it's a pure semantic derivation.

    Values:
        ready_now: Model is loaded and backend is serving. No wait.
        short_wait: Backend is up but model needs loading. Small model
            (< 30 GB), so load time is brief.
        long_wait: Backend is up but model needs loading. Large model
            (>= 30 GB), so load time is significant.
        background_only: Model is designated as lab/background-only.
            Not intended for interactive use regardless of load state.
        currently_unavailable: Backend is down or model state unknown.
            Cannot estimate wait time.
    """

    ready_now = "ready_now"
    short_wait = "short_wait"
    long_wait = "long_wait"
    background_only = "background_only"
    currently_unavailable = "currently_unavailable"


# ── Truth level ────────────────────────────────────────────────────────────────

class TruthLevel(str, Enum):
    """Confidence level of the load state assessment.

    Values:
        true: Backend provides per-model confirmation of loaded state.
            Strongest evidence.
        inferred: Load state is estimated from indirect signals (router
            model list, memory heuristics, loaded_count without per-model
            breakdown).
        unavailable: Backend is unreachable; no load state signal at all.
    """

    true = "true"
    inferred = "inferred"
    unavailable = "unavailable"


# ── Runtime readiness (composite) ──────────────────────────────────────────────

class RuntimeReadiness(str, Enum):
    """Composite assessment: can this runtime serve right now?

    Derived from load state, inference health, and substrate signals
    (abort recovery state). This is the highest-level per-runtime health
    label that owlmlx defines.

    Values:
        ready: Model loaded, backend serving, substrate clean.
            Full inference capability.
        degraded: Partially functional — backend is stale, model is
            cold, or inference health is uncertain. May serve some
            requests but not at full capability.
        blocked: Cannot serve. Substrate contaminated (abort recovery),
            backend down, or model unavailable. Requires intervention.
        probing: Health verification in progress after a substrate event.
            Readiness is uncertain until probe completes.
        unknown: Insufficient signal to determine readiness.
    """

    ready = "ready"
    degraded = "degraded"
    blocked = "blocked"
    probing = "probing"
    unknown = "unknown"


# ── Platform status (system-wide) ──────────────────────────────────────────────

class PlatformStatus(str, Enum):
    """System-wide platform health assessment.

    Aggregated from backend health, preflight checks, and service
    availability. The platform performs the aggregation; owlmlx defines
    what the labels mean.

    Values:
        healthy: All stable backends up, default model set, all
            preflight checks pass. Full platform capability.
        degraded: Some backends down, some checks failing, or
            configuration incomplete. Platform is partially usable.
        unavailable: No backends responding, platform likely not started
            or in a catastrophic failure state.
    """

    healthy = "healthy"
    degraded = "degraded"
    unavailable = "unavailable"


# ── Constants ──────────────────────────────────────────────────────────────────

LARGE_MODEL_MEMORY_THRESHOLD_GB: float = 30.0
"""Models >= this size get long_wait instead of short_wait when cold."""


# ── Normalization functions ────────────────────────────────────────────────────

def normalize_load_state(raw: str) -> LoadState:
    """Normalize a raw load state string to a canonical LoadState.

    Accepts any valid LoadState value string. Returns LoadState.unknown
    for unrecognized values.
    """
    try:
        return LoadState(raw)
    except ValueError:
        return LoadState.unknown


def normalize_inference_health(raw: str) -> InferenceHealth:
    """Normalize a raw inference health string to canonical InferenceHealth.

    Returns InferenceHealth.down for unrecognized values.
    """
    try:
        return InferenceHealth(raw)
    except ValueError:
        return InferenceHealth.down


def normalize_truth_level(raw: str) -> TruthLevel:
    """Normalize a raw truth level string to canonical TruthLevel.

    Returns TruthLevel.unavailable for unrecognized values.
    """
    try:
        return TruthLevel(raw)
    except ValueError:
        return TruthLevel.unavailable


# ── Derivation functions ───────────────────────────────────────────────────────

def is_model_ready(
    load_state: LoadState | str,
    inference_health: InferenceHealth | str,
) -> bool:
    """Whether a model is ready for immediate inference.

    A model is ready when it is loaded (true or inferred) AND the
    backend is actively serving.
    """
    ls = normalize_load_state(load_state) if isinstance(load_state, str) else load_state
    ih = normalize_inference_health(inference_health) if isinstance(inference_health, str) else inference_health
    return (
        ls in (LoadState.true_loaded, LoadState.inferred_loaded)
        and ih == InferenceHealth.serving
    )


def derive_wait_tier(
    load_state: LoadState | str,
    *,
    memory_gb: float = 0.0,
    is_lab: bool = False,
) -> WaitTier:
    """Derive wait tier from load state and model characteristics.

    Args:
        load_state: Current load state of the model.
        memory_gb: Model memory footprint in GB. Used to distinguish
            short_wait from long_wait for cold models.
        is_lab: Whether the model is designated as lab/background-only.

    Returns:
        The appropriate WaitTier.
    """
    ls = normalize_load_state(load_state) if isinstance(load_state, str) else load_state

    if is_lab:
        return WaitTier.background_only
    if ls in (LoadState.true_loaded, LoadState.inferred_loaded):
        return WaitTier.ready_now
    if ls == LoadState.cold:
        return WaitTier.long_wait if memory_gb >= LARGE_MODEL_MEMORY_THRESHOLD_GB else WaitTier.short_wait
    return WaitTier.currently_unavailable


def derive_runtime_readiness(
    load_state: LoadState | str,
    inference_health: InferenceHealth | str,
    substrate_state: SubstrateState | str | None = None,
) -> RuntimeReadiness:
    """Derive composite runtime readiness from component signals.

    Combines load state, inference health, and substrate abort recovery
    state into a single readiness assessment.

    Priority order:
    1. Substrate contaminated → blocked
    2. Substrate probing → probing
    3. Backend down or model unavailable → blocked
    4. Model loaded + backend serving → ready
    5. Backend stale or model cold → degraded
    6. Otherwise → unknown

    Args:
        load_state: Current model load state.
        inference_health: Current backend inference health.
        substrate_state: Abort recovery substrate state (optional).
            If None, substrate is assumed clean.

    Returns:
        The composite RuntimeReadiness.
    """
    ls = normalize_load_state(load_state) if isinstance(load_state, str) else load_state
    ih = normalize_inference_health(inference_health) if isinstance(inference_health, str) else inference_health

    # Normalize substrate state
    ss: SubstrateState | None = None
    if substrate_state is not None:
        if isinstance(substrate_state, str):
            try:
                ss = SubstrateState(substrate_state)
            except ValueError:
                ss = None
        else:
            ss = substrate_state

    # 1. Substrate signals take priority
    if ss == SubstrateState.contaminated:
        return RuntimeReadiness.blocked
    if ss == SubstrateState.probing:
        return RuntimeReadiness.probing

    # 2. Backend/model availability
    if ls == LoadState.unknown:
        return RuntimeReadiness.unknown
    if ls == LoadState.unavailable or ih == InferenceHealth.down:
        return RuntimeReadiness.blocked

    # 3. Fully ready
    if ls in (LoadState.true_loaded, LoadState.inferred_loaded) and ih == InferenceHealth.serving:
        return RuntimeReadiness.ready

    # 4. Degraded states
    if ih == InferenceHealth.stale:
        return RuntimeReadiness.degraded
    if ih == InferenceHealth.reachable_not_serving:
        return RuntimeReadiness.degraded
    if ls == LoadState.cold:
        return RuntimeReadiness.degraded

    return RuntimeReadiness.unknown


def derive_block_reason(
    *,
    substrate_state: SubstrateState | str | None = None,
    inference_health: InferenceHealth | str | None = None,
    load_state: LoadState | str | None = None,
    budget_feasible: bool | None = None,
) -> str | None:
    """Derive a human-readable block reason from component signals.

    Returns None if no blocking condition is detected.

    Args:
        substrate_state: Abort recovery state. Contaminated = blocked.
        inference_health: Backend inference health. Down = blocked.
        load_state: Model load state. Unavailable = blocked.
        budget_feasible: Whether the model fits in memory budget.
            False = blocked.

    Returns:
        A short reason string, or None if not blocked.
    """
    if substrate_state is not None:
        ss = SubstrateState(substrate_state) if isinstance(substrate_state, str) else substrate_state
        if ss == SubstrateState.contaminated:
            return "substrate contaminated after high-context abort"

    if budget_feasible is False:
        return "model exceeds memory budget"

    if inference_health is not None:
        ih = InferenceHealth(inference_health) if isinstance(inference_health, str) else inference_health
        if ih == InferenceHealth.down:
            return "backend is down"

    if load_state is not None:
        ls = LoadState(load_state) if isinstance(load_state, str) else load_state
        if ls == LoadState.unavailable:
            return "backend unreachable"

    return None


def derive_platform_status(
    *,
    check_statuses: list[str],
    up_stable_backends: int,
) -> PlatformStatus:
    """Derive system-wide platform status from preflight check results.

    The platform executes the checks; this function only interprets the
    results into a canonical status.

    Args:
        check_statuses: List of status strings from preflight checks.
            Expected values: "pass", "fail", "warn", "partial".
        up_stable_backends: Number of stable backends that are up.

    Returns:
        The platform-wide health status.
    """
    if "fail" in check_statuses and up_stable_backends == 0:
        return PlatformStatus.unavailable
    if "fail" in check_statuses or "partial" in check_statuses or "warn" in check_statuses:
        return PlatformStatus.degraded
    return PlatformStatus.healthy


def runtime_health_snapshot(
    *,
    load_state: LoadState | str,
    inference_health: InferenceHealth | str,
    truth_level: TruthLevel | str,
    substrate_state: SubstrateState | str | None = None,
    memory_gb: float = 0.0,
    is_lab: bool = False,
    budget_feasible: bool | None = None,
) -> dict[str, Any]:
    """Build a runtime health snapshot from component signals.

    Computes all derived fields (readiness, wait_tier, block_reason,
    is_ready) from the provided raw signals. No I/O performed.

    Returns:
        Dict with canonical health fields. No transport state.
    """
    ls = normalize_load_state(load_state) if isinstance(load_state, str) else load_state
    ih = normalize_inference_health(inference_health) if isinstance(inference_health, str) else inference_health
    tl = normalize_truth_level(truth_level) if isinstance(truth_level, str) else truth_level

    readiness = derive_runtime_readiness(ls, ih, substrate_state)
    wait_tier = derive_wait_tier(ls, memory_gb=memory_gb, is_lab=is_lab)
    ready = is_model_ready(ls, ih)
    block_reason = derive_block_reason(
        substrate_state=substrate_state,
        inference_health=ih,
        load_state=ls,
        budget_feasible=budget_feasible,
    )

    return {
        "load_state": ls.value,
        "inference_health": ih.value,
        "truth_level": tl.value,
        "readiness": readiness.value,
        "wait_tier": wait_tier.value,
        "is_ready": ready,
        "block_reason": block_reason,
    }
