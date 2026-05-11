from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from owlmlx import build_cache_structural_ingress_seam
from owlmlx.cache_structural_ingress_seam import cache_structural_ingress_seam_to_dict


def test_cache_structural_ingress_seam_defaults_unverified() -> None:
    payload = cache_structural_ingress_seam_to_dict(build_cache_structural_ingress_seam())

    assert payload["contract"]["surface"] == "owlmlx.cache_structural_ingress_seam"
    assert payload["summary"]["seam_rung"] == "structural_ingress_seam_unverified"


def test_cache_structural_ingress_seam_marks_structural_hook_only() -> None:
    payload = cache_structural_ingress_seam_to_dict(
        build_cache_structural_ingress_seam(
            pre_gate_admission_window_seam=SimpleNamespace(
                seam_rung="pre_gate_admission_window_seam_exact"
            ),
            pre_claim_staging_seam_exactness=SimpleNamespace(
                exactness_rung="staging_seam_exact"
            ),
            hook_harness=SimpleNamespace(
                runtime_owned_hook_present=True,
                observed_midflight_staged_count=1,
                observed_total_staged=2,
                observed_total_claimed=2,
                staging_units=(
                    "immutable_request_metadata_snapshot",
                    "ticket_reservation_without_gate_claim",
                    "pre_claim_bounded_admission_bookkeeping",
                ),
                preserved_post_claim_invariants=(
                    "max_concurrent_1_after_gate_claim",
                    "ticketed_fifo_after_gate_claim",
                    "serial_safety_validated_only_after_gate_claim",
                ),
            ),
        )
    )

    assert payload["summary"]["seam_rung"] == "structural_ingress_seam_introduced"
    assert payload["hook"]["runtime_owned_hook_status"] == "bounded_pre_gate_hook_present"
    assert "request aggregation" in payload["summary"]["residual_blocker"]


def test_cache_structural_ingress_seam_module_has_no_platform_dependency() -> None:
    source = Path(__file__).parents[1].joinpath(
        "owlmlx", "cache_structural_ingress_seam.py"
    ).read_text()
    for pattern in ("llm_router", "ops_dashboard", "local-llm-desktop", "AI/Agent"):
        assert pattern not in source
