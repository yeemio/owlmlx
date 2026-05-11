"""Tests for the prefix-cache feasibility probe — Campaign 2."""

from __future__ import annotations

from owlmlx.prefix_cache_feasibility_probe import (
    prefix_cache_feasibility_to_dict,
    run_prefix_cache_feasibility_probe,
)


def test_probe_runs_without_error():
    report = run_prefix_cache_feasibility_probe()
    assert report.feasibility in {"feasible", "partial", "absent"}


def test_probe_lru_primitives_present():
    """On this host mlx_lm is installed; key primitives must be importable."""
    report = run_prefix_cache_feasibility_probe()
    assert report.lru_prompt_cache_importable
    assert report.lru_has_fetch
    assert report.lru_has_insert
    assert report.prompt_trie_importable
    assert report.trie_has_search


def test_probe_instantiation_and_round_trip():
    """LRUPromptCache can be constructed and survives an insert+fetch cycle."""
    report = run_prefix_cache_feasibility_probe()
    assert report.instantiation_ok
    assert report.insert_fetch_round_trip_ok


def test_probe_reports_feasible():
    report = run_prefix_cache_feasibility_probe()
    assert report.feasibility == "feasible"


def test_probe_to_dict_shape():
    report = run_prefix_cache_feasibility_probe()
    d = prefix_cache_feasibility_to_dict(report)
    assert d["surface"] == "owlmlx.prefix_cache_feasibility_probe"
    assert d["feasibility"] == "feasible"
    assert d["implementation_claim"] is False
    assert d["cross_request_reuse_implemented"] is False
    assert "primitives" in d
    assert "smoke" in d
    assert d["smoke"]["insert_fetch_round_trip_ok"] is True
