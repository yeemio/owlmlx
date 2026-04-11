"""Tests for owlmlx.context_concurrency — serving-path concurrency boundary truth."""

from owlmlx.context_concurrency import (
    CONCURRENCY_GATE,
    HIGH_CONTEXT_THRESHOLD_TOKENS,
    VERIFIED_OMLX_VERSION,
    VERIFIED_HARDWARE,
    ConcurrencyGateEntry,
    concurrency_gate_snapshot,
    gate_entry_for_context,
    is_high_context,
    max_concurrency_for_context,
)


# ── Constants ──────────────────────────────────────────────────────────────────


def test_verified_omlx_version() -> None:
    """The verified substrate version is oMLX 0.3.2."""
    assert VERIFIED_OMLX_VERSION == "0.3.2"


def test_verified_hardware() -> None:
    """The verified hardware is Apple M5 Max 128 GB."""
    assert "M5 Max" in VERIFIED_HARDWARE
    assert "128 GB" in VERIFIED_HARDWARE


def test_high_context_threshold_is_49152() -> None:
    """The high-context threshold is 49152 tokens (48K)."""
    assert HIGH_CONTEXT_THRESHOLD_TOKENS == 49152


def test_gate_table_is_immutable() -> None:
    """The gate table is a tuple — cannot be accidentally mutated."""
    assert isinstance(CONCURRENCY_GATE, tuple)


def test_gate_has_four_entries() -> None:
    """The verified gate has exactly 4 tiers."""
    assert len(CONCURRENCY_GATE) == 4


def test_gate_entries_are_frozen() -> None:
    """Gate entries are frozen dataclasses."""
    for entry in CONCURRENCY_GATE:
        assert isinstance(entry, ConcurrencyGateEntry)
        try:
            entry.max_concurrency = 99  # type: ignore[misc]
            assert False, "Should have raised AttributeError"
        except AttributeError:
            pass


def test_gate_sorted_ascending() -> None:
    """Gate entries are sorted by upper_bound_tokens ascending."""
    bounds = [e.upper_bound_tokens for e in CONCURRENCY_GATE]
    assert bounds == sorted(bounds)


def test_all_gate_entries_are_supported() -> None:
    """All current gate tiers are 'supported' (hardware-verified)."""
    for entry in CONCURRENCY_GATE:
        assert entry.tier == "supported"


# ── max_concurrency_for_context ────────────────────────────────────────────────


def test_tiny_context_allows_4_way() -> None:
    """Very small context (1K) allows 4-way concurrency."""
    assert max_concurrency_for_context(1000) == 4


def test_16k_context_allows_4_way() -> None:
    """Exactly 16K tokens allows 4-way concurrency."""
    assert max_concurrency_for_context(16384) == 4


def test_32k_context_allows_4_way() -> None:
    """32K tokens (between 16K and 48K) allows 4-way concurrency."""
    assert max_concurrency_for_context(32768) == 4


def test_48k_context_allows_4_way() -> None:
    """Exactly 48K tokens (49152) allows 4-way concurrency."""
    assert max_concurrency_for_context(49152) == 4


def test_48k_plus_one_requires_serialization() -> None:
    """49153 tokens (just over 48K) requires 1-way serialization."""
    assert max_concurrency_for_context(49153) == 1


def test_100k_context_serialized() -> None:
    """100K tokens requires 1-way serialization."""
    assert max_concurrency_for_context(100000) == 1


def test_131k_context_serialized() -> None:
    """Exactly 131K tokens requires 1-way serialization."""
    assert max_concurrency_for_context(131072) == 1


def test_200k_context_serialized() -> None:
    """200K tokens requires 1-way serialization."""
    assert max_concurrency_for_context(200000) == 1


def test_256k_context_serialized() -> None:
    """Exactly 256K tokens requires 1-way serialization."""
    assert max_concurrency_for_context(262144) == 1


def test_beyond_256k_serialized() -> None:
    """Beyond all defined tiers, fallback is 1-way serialization."""
    assert max_concurrency_for_context(500000) == 1


def test_zero_context_allows_4_way() -> None:
    """Zero tokens (e.g., empty prompt) still uses the first tier."""
    assert max_concurrency_for_context(0) == 4


# ── gate_entry_for_context ─────────────────────────────────────────────────────


def test_gate_entry_small_context() -> None:
    """Small context returns full gate entry with label and tier."""
    entry = gate_entry_for_context(1000)
    assert entry["max_concurrency"] == 4
    assert entry["label"] == "≤16K"
    assert entry["tier"] == "supported"


def test_gate_entry_between_16k_and_48k() -> None:
    """Context between 16K and 48K returns the ≤48K tier."""
    entry = gate_entry_for_context(30000)
    assert entry["max_concurrency"] == 4
    assert entry["label"] == "≤48K"


def test_gate_entry_high_context() -> None:
    """High context returns 1-way serialized entry."""
    entry = gate_entry_for_context(60000)
    assert entry["max_concurrency"] == 1
    assert entry["label"] == "≤131K"


def test_gate_entry_beyond_all_tiers() -> None:
    """Beyond all tiers returns fallback with >256K label."""
    entry = gate_entry_for_context(500000)
    assert entry["max_concurrency"] == 1
    assert entry["label"] == ">256K"


# ── is_high_context ────────────────────────────────────────────────────────────


def test_at_threshold_is_not_high_context() -> None:
    """Exactly at threshold (49152) is NOT high context (it's ≤48K)."""
    assert is_high_context(49152) is False


def test_above_threshold_is_high_context() -> None:
    """One token above threshold IS high context."""
    assert is_high_context(49153) is True


def test_small_context_is_not_high_context() -> None:
    """Small context is not high context."""
    assert is_high_context(1000) is False


def test_very_large_context_is_high_context() -> None:
    """Very large context is high context."""
    assert is_high_context(300000) is True


# ── concurrency_gate_snapshot ──────────────────────────────────────────────────


def test_snapshot_has_required_fields() -> None:
    """Snapshot includes version, hardware, threshold, and gate."""
    snap = concurrency_gate_snapshot()
    assert snap["omlx_version"] == "0.3.2"
    assert "M5 Max" in snap["hardware"]
    assert snap["high_context_threshold_tokens"] == 49152
    assert "gate" in snap


def test_snapshot_gate_has_all_tiers() -> None:
    """Snapshot gate contains all defined tier labels."""
    snap = concurrency_gate_snapshot()
    gate = snap["gate"]
    assert "≤16K" in gate
    assert "≤48K" in gate
    assert "≤131K" in gate
    assert "≤256K" in gate


def test_snapshot_gate_tier_structure() -> None:
    """Each gate tier in snapshot has upper_bound, max_concurrency, and tier."""
    snap = concurrency_gate_snapshot()
    for label, tier_data in snap["gate"].items():
        assert "upper_bound_tokens" in tier_data
        assert "max_concurrency" in tier_data
        assert "tier" in tier_data


def test_snapshot_has_no_enforcement_state() -> None:
    """Snapshot must NOT contain enforcement state (active counts, semaphores)."""
    snap = concurrency_gate_snapshot()
    # These belong in the router's enforcement layer, not in truth
    assert "active" not in snap
    assert "high_context_active" not in snap
    assert "total_high_context_served" not in snap
    assert "total_standard_served" not in snap


# ── Pure function guarantees ───────────────────────────────────────────────────


def test_max_concurrency_is_pure() -> None:
    """Same input always produces same output."""
    assert max_concurrency_for_context(30000) == max_concurrency_for_context(30000)
    assert max_concurrency_for_context(60000) == max_concurrency_for_context(60000)


def test_gate_entry_is_pure() -> None:
    """Same input always produces identical gate entries."""
    e1 = gate_entry_for_context(30000)
    e2 = gate_entry_for_context(30000)
    assert e1 == e2


def test_snapshot_is_deterministic() -> None:
    """Snapshot is deterministic — no mutable state leaks."""
    s1 = concurrency_gate_snapshot()
    s2 = concurrency_gate_snapshot()
    assert s1 == s2
