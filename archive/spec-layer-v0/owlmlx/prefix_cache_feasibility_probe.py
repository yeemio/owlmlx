"""Prefix-cache feasibility probe — Campaign 2 surface.

Documents and introspects the mlx_lm prefix-cache primitives that would
support cross-request KV cache reuse if wired into the native backend.

This is a feasibility probe, not an implementation claim. It confirms:
  - LRUPromptCache is importable and instantiable
  - PromptTrie is importable and has .search()
  - can_trim_prompt_cache / trim_prompt_cache are present

Cross-request prefix reuse is NOT implemented. See CacheManager docstring
§(b) for the extension point. This probe surfaces what MLX-LM provides.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class PrefixCacheFeasibilityReport:
    """Immutable report of mlx_lm prefix-cache primitive availability."""

    lru_prompt_cache_importable: bool
    prompt_trie_importable: bool
    can_trim_importable: bool
    lru_has_fetch: bool
    lru_has_insert: bool
    lru_has_trim_to: bool
    trie_has_search: bool
    instantiation_ok: bool           # LRUPromptCache(max_size=4) succeeded
    insert_fetch_round_trip_ok: bool # insert then fetch returns a result
    feasibility: str                 # "feasible" | "partial" | "absent"
    notes: tuple[str, ...]


def run_prefix_cache_feasibility_probe() -> PrefixCacheFeasibilityReport:
    """Probe mlx_lm for prefix-cache primitives; return a feasibility report."""

    lru_importable = False
    trie_importable = False
    can_trim_importable = False
    lru_has_fetch = False
    lru_has_insert = False
    lru_has_trim_to = False
    trie_has_search = False
    instantiation_ok = False
    insert_fetch_ok = False
    notes: list[str] = []

    try:
        from mlx_lm.models.cache import LRUPromptCache  # type: ignore[import]
        lru_importable = True
        lru_has_fetch = callable(getattr(LRUPromptCache, "fetch_nearest_cache", None))
        lru_has_insert = callable(getattr(LRUPromptCache, "insert_cache", None))
        lru_has_trim_to = callable(getattr(LRUPromptCache, "trim_to", None))
    except ImportError:
        notes.append("mlx_lm.models.cache.LRUPromptCache not importable")

    try:
        from mlx_lm.models.cache import PromptTrie  # type: ignore[import]
        trie_importable = True
        trie_has_search = callable(getattr(PromptTrie, "search", None))
    except ImportError:
        notes.append("mlx_lm.models.cache.PromptTrie not importable")

    try:
        from mlx_lm.models.cache import can_trim_prompt_cache  # type: ignore[import]
        can_trim_importable = callable(can_trim_prompt_cache)
    except ImportError:
        notes.append("mlx_lm.models.cache.can_trim_prompt_cache not importable")

    if lru_importable and lru_has_fetch and lru_has_insert:
        try:
            from mlx_lm.models.cache import LRUPromptCache  # type: ignore[import]
            lru = LRUPromptCache(max_size=4)
            instantiation_ok = True
            # Sentinel object used as the model key — no actual MLX weights loaded.
            _sentinel = object()
            tokens = [1, 2, 3, 4, 5]
            lru.insert_cache(_sentinel, tokens, [], cache_type="assistant")
            result = lru.fetch_nearest_cache(_sentinel, tokens)
            insert_fetch_ok = result is not None
            if insert_fetch_ok:
                notes.append("LRUPromptCache insert+fetch round-trip confirmed")
        except Exception as exc:
            notes.append(f"LRUPromptCache instantiation or round-trip failed: {exc}")

    cap_count = sum([lru_importable, trie_importable, can_trim_importable,
                     lru_has_fetch, lru_has_insert, trie_has_search,
                     instantiation_ok, insert_fetch_ok])
    if cap_count >= 7:
        feasibility = "feasible"
    elif cap_count >= 3:
        feasibility = "partial"
    else:
        feasibility = "absent"

    return PrefixCacheFeasibilityReport(
        lru_prompt_cache_importable=lru_importable,
        prompt_trie_importable=trie_importable,
        can_trim_importable=can_trim_importable,
        lru_has_fetch=lru_has_fetch,
        lru_has_insert=lru_has_insert,
        lru_has_trim_to=lru_has_trim_to,
        trie_has_search=trie_has_search,
        instantiation_ok=instantiation_ok,
        insert_fetch_round_trip_ok=insert_fetch_ok,
        feasibility=feasibility,
        notes=tuple(notes),
    )


def prefix_cache_feasibility_to_dict(report: PrefixCacheFeasibilityReport) -> dict[str, Any]:
    return {
        "surface": "owlmlx.prefix_cache_feasibility_probe",
        "feasibility": report.feasibility,
        "primitives": {
            "lru_prompt_cache_importable": report.lru_prompt_cache_importable,
            "prompt_trie_importable": report.prompt_trie_importable,
            "can_trim_importable": report.can_trim_importable,
            "lru_has_fetch_nearest_cache": report.lru_has_fetch,
            "lru_has_insert_cache": report.lru_has_insert,
            "lru_has_trim_to": report.lru_has_trim_to,
            "trie_has_search": report.trie_has_search,
        },
        "smoke": {
            "instantiation_ok": report.instantiation_ok,
            "insert_fetch_round_trip_ok": report.insert_fetch_round_trip_ok,
        },
        "notes": list(report.notes),
        "implementation_claim": False,
        "cross_request_reuse_implemented": False,
    }


__all__ = [
    "PrefixCacheFeasibilityReport",
    "run_prefix_cache_feasibility_probe",
    "prefix_cache_feasibility_to_dict",
]
