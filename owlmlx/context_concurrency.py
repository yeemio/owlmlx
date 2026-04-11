"""owlmlx serving-path context concurrency boundary truth.

Defines the hardware-verified concurrency boundaries for the MLX/Metal
substrate on the current machine class. These boundaries describe how
many concurrent inference requests the substrate can safely handle at
different context lengths.

This is serving-path only. Training concurrency is explicitly out of
scope (contract Rule 7: no training path smuggling).

Runtime truth this module owns:

- Concurrency gate table: context length → max concurrent requests
- High-context threshold: above this, serialized execution required
- Gate lookup: pure function from context tokens to concurrency limit
- Gate snapshot: complete boundary truth for status exposure
- Runtime version identity for the verified substrate

What this module does NOT own (stays in router / enforcement layer):

- asyncio.Semaphore acquisition at request dispatch time
- Active/served request counters
- Timeout handling for lock acquisition
- Token estimation from HTTP payloads
- HTTP endpoint transport

This module is self-contained. It does not import any platform module.
If llm_router/context_concurrency_policy.py were deleted, this module
would still function. That is the absorption criterion (contract Rule 8).

Hardware truth source: Verified on Apple M5 Max, 128 GB unified memory,
oMLX 0.3.2 (Phase 41 verification).

  - oMLX 0.3.2:  ≤48K tokens → 4-way supported,  >48K → 1-way only
  - oMLX 0.3.0:  ≤16K → 4-way, ≤48K → 1-way (superseded by 0.3.2)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


# ── Verified substrate identity ────────────────────────────────────────────────

VERIFIED_OMLX_VERSION: str = "0.3.2"
VERIFIED_HARDWARE: str = "Apple M5 Max, 128 GB unified memory"


# ── Gate table ─────────────────────────────────────────────────────────────────
# Each entry: (upper_bound_tokens, max_concurrency, label, tier)
#
# Semantics: if context_tokens <= upper_bound_tokens, this row applies.
# Rows are ordered ascending by upper_bound_tokens.
# The gate is exhaustive — if no row matches, the fallback is 1-way.

@dataclass(frozen=True, slots=True)
class ConcurrencyGateEntry:
    """One row in the concurrency gate table.

    Attributes:
        upper_bound_tokens: Maximum context length (inclusive) for this tier.
        max_concurrency: Maximum safe concurrent requests at this context length.
        label: Human-readable label (e.g., "≤48K").
        tier: Verification tier ("supported", "experimental", etc.).
    """

    upper_bound_tokens: int
    max_concurrency: int
    label: str
    tier: str


# The canonical gate table, verified on oMLX 0.3.2 / M5 Max 128 GB.
CONCURRENCY_GATE: tuple[ConcurrencyGateEntry, ...] = (
    ConcurrencyGateEntry(upper_bound_tokens=16384,  max_concurrency=4, label="≤16K",  tier="supported"),
    ConcurrencyGateEntry(upper_bound_tokens=49152,  max_concurrency=4, label="≤48K",  tier="supported"),
    ConcurrencyGateEntry(upper_bound_tokens=131072, max_concurrency=1, label="≤131K", tier="supported"),
    ConcurrencyGateEntry(upper_bound_tokens=262144, max_concurrency=1, label="≤256K", tier="supported"),
)

# Above this threshold, high-context serialization is required.
HIGH_CONTEXT_THRESHOLD_TOKENS: int = 49152


def max_concurrency_for_context(context_tokens: int) -> int:
    """Return the maximum safe concurrent requests for a given context length.

    This is a pure function. It takes a token count and returns an integer.
    No I/O, no state, no platform dependencies.

    Args:
        context_tokens: Estimated input context length in tokens.

    Returns:
        Maximum number of concurrent inference requests that the substrate
        can safely handle at this context length.
    """
    for entry in CONCURRENCY_GATE:
        if context_tokens <= entry.upper_bound_tokens:
            return entry.max_concurrency
    # Beyond all defined tiers: safe fallback is serialized
    return 1


def gate_entry_for_context(context_tokens: int) -> dict[str, Any]:
    """Return the full gate entry for a given context length.

    Returns a dict with max_concurrency, label, and tier — the complete
    boundary truth for this context size.

    Args:
        context_tokens: Estimated input context length in tokens.

    Returns:
        Dict with keys: max_concurrency, label, tier.
    """
    for entry in CONCURRENCY_GATE:
        if context_tokens <= entry.upper_bound_tokens:
            return {
                "max_concurrency": entry.max_concurrency,
                "label": entry.label,
                "tier": entry.tier,
            }
    return {"max_concurrency": 1, "label": ">256K", "tier": "supported"}


def is_high_context(context_tokens: int) -> bool:
    """Return whether this context length requires high-context serialization.

    Above HIGH_CONTEXT_THRESHOLD_TOKENS, the substrate cannot safely
    handle multiple concurrent requests — they must be serialized.

    Args:
        context_tokens: Estimated input context length in tokens.

    Returns:
        True if high-context lock is required.
    """
    return context_tokens > HIGH_CONTEXT_THRESHOLD_TOKENS


def concurrency_gate_snapshot() -> dict[str, Any]:
    """Return the complete concurrency gate truth for status exposure.

    This dict is intended to be embedded in runtime status payloads or
    exposed via API endpoints. It describes the full boundary truth
    without any enforcement state (no active counts, no semaphore state).

    Returns:
        Dict with verified substrate identity and gate table.
    """
    return {
        "omlx_version": VERIFIED_OMLX_VERSION,
        "hardware": VERIFIED_HARDWARE,
        "high_context_threshold_tokens": HIGH_CONTEXT_THRESHOLD_TOKENS,
        "gate": {
            entry.label: {
                "upper_bound_tokens": entry.upper_bound_tokens,
                "max_concurrency": entry.max_concurrency,
                "tier": entry.tier,
            }
            for entry in CONCURRENCY_GATE
        },
    }
