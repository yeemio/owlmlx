from __future__ import annotations

from pathlib import Path

from owlmlx import (
    build_cache_admission_hook_safety_contract,
    build_cache_batching_mechanism_subgap,
    build_cache_closure_rung,
    build_cache_continuous_batching_feasibility,
    build_cache_counter_feasibility,
    build_cache_counter_gap,
    build_cache_pre_claim_admission_carrier_construction,
    build_cache_pre_claim_admission_carrier_encoding_exactness,
    build_cache_pre_claim_admission_carrier_field_exactness,
    build_cache_pre_claim_admission_carrier_locality_access_exactness,
    build_cache_pre_claim_admission_carrier_locality_exactness,
    build_cache_pre_claim_admission_carrier_locality_isolation_exactness,
    build_cache_pre_claim_admission_carrier_locality_lifetime_coupling,
    build_cache_pre_claim_admission_carrier_reclaim_reset_exactness,
    build_cache_pre_claim_admission_contract,
    build_cache_pre_claim_inert_state_semantics,
    build_cache_pre_claim_marker_clear_observer_boundary,
    build_cache_pre_claim_marker_encoding_carrier_exactness,
    build_cache_pre_claim_marker_immutability_boundary,
    build_cache_pre_claim_marker_lifetime,
    build_cache_pre_claim_marker_locality_access_exactness,
    build_cache_pre_claim_marker_locality_isolation_exactness,
    build_cache_pre_claim_marker_locality_lifetime_coupling,
    build_cache_pre_claim_marker_payload_shape_exactness,
    build_cache_pre_claim_marker_reader_writer_ownership,
    build_cache_pre_claim_marker_reclaim_reset_exactness,
    build_cache_pre_claim_marker_state_carrier,
    build_cache_pre_claim_marker_storage_locality_exactness,
    build_cache_pre_claim_marker_trigger_inputs,
    build_cache_pre_claim_marker_visibility,
    build_cache_pre_claim_metadata_ticket_ownership,
    build_cache_pre_claim_staging_seam_exactness,
    build_cache_pre_gate_admission_hook_exactness,
    build_cache_pre_gate_cohort_window_feasibility,
    build_cache_repeatability_evidence,
    build_cache_request_aggregation_window_exactness,
    build_cache_scheduler_branch_selection,
    build_cache_scheduler_floor_gap,
    build_cache_scheduler_implementation_backlog,
    build_cache_scheduler_turboquant_split,
    cache_pre_claim_admission_carrier_reclaim_reset_exactness_to_dict,
)


def test_cache_pre_claim_admission_carrier_reclaim_reset_exactness_defaults_to_unresolved() -> None:
    payload = cache_pre_claim_admission_carrier_reclaim_reset_exactness_to_dict(
        build_cache_pre_claim_admission_carrier_reclaim_reset_exactness()
    )

    assert (
        payload["contract"]["surface"]
        == "owlmlx.cache_pre_claim_admission_carrier_reclaim_reset_exactness"
    )
    assert (
        payload["summary"]["exactness_rung"]
        == "admission_carrier_reclaim_reset_unresolved"
    )


def test_cache_pre_claim_admission_carrier_reclaim_reset_exactness_freezes_exact_boundary() -> None:
    backend_status = {
        "detail": {
            "cache_runtime_observations": {
                "persistent_child_reuse_visible": True,
                "reuse_counter": 1,
                "cache_counter_visibility": {
                    "residency": False,
                    "reuse": True,
                    "eviction": False,
                },
            }
        }
    }
    repeatability = build_cache_repeatability_evidence([], backend_status=backend_status)
    closure = build_cache_closure_rung(repeatability=repeatability)
    counter_gap = build_cache_counter_gap(
        closure=closure,
        backend_observations=backend_status["detail"]["cache_runtime_observations"],
    )
    counter_feasibility = build_cache_counter_feasibility(counter_gap=counter_gap)
    split = build_cache_scheduler_turboquant_split(
        counter_feasibility=counter_feasibility,
        scheduler=closure.scheduler,
        turboquant=closure.turboquant,
    )
    floor_gap = build_cache_scheduler_floor_gap(split=split)
    backlog = build_cache_scheduler_implementation_backlog(floor_gap=floor_gap)
    branch_selection = build_cache_scheduler_branch_selection(
        scheduler_backlog=backlog
    )
    feasibility = build_cache_continuous_batching_feasibility(
        branch_selection=branch_selection
    )
    mechanism_subgap = build_cache_batching_mechanism_subgap(
        feasibility=feasibility
    )
    aggregation_exactness = build_cache_request_aggregation_window_exactness(
        mechanism_subgap=mechanism_subgap
    )
    cohort_window_feasibility = build_cache_pre_gate_cohort_window_feasibility(
        aggregation_exactness=aggregation_exactness
    )
    admission_hook_exactness = build_cache_pre_gate_admission_hook_exactness(
        cohort_window_feasibility=cohort_window_feasibility
    )
    safety_contract = build_cache_admission_hook_safety_contract(
        admission_hook_exactness=admission_hook_exactness
    )
    pre_claim_contract = build_cache_pre_claim_admission_contract(
        safety_contract=safety_contract
    )
    staging_seam_exactness = build_cache_pre_claim_staging_seam_exactness(
        pre_claim_contract=pre_claim_contract
    )
    ownership = build_cache_pre_claim_metadata_ticket_ownership(
        staging_seam_exactness=staging_seam_exactness
    )
    inert_state = build_cache_pre_claim_inert_state_semantics(
        metadata_ticket_ownership=ownership,
        cohort_window_feasibility=cohort_window_feasibility,
    )
    marker_lifetime = build_cache_pre_claim_marker_lifetime(
        inert_state_semantics=inert_state
    )
    marker_visibility = build_cache_pre_claim_marker_visibility(
        marker_lifetime=marker_lifetime
    )
    trigger_inputs = build_cache_pre_claim_marker_trigger_inputs(
        marker_visibility=marker_visibility
    )
    reader_writer = build_cache_pre_claim_marker_reader_writer_ownership(
        trigger_inputs=trigger_inputs
    )
    state_carrier = build_cache_pre_claim_marker_state_carrier(
        reader_writer_ownership=reader_writer
    )
    clear_observer = build_cache_pre_claim_marker_clear_observer_boundary(
        state_carrier=state_carrier
    )
    immutability = build_cache_pre_claim_marker_immutability_boundary(
        clear_observer_boundary=clear_observer
    )
    payload_shape = build_cache_pre_claim_marker_payload_shape_exactness(
        immutability_boundary=immutability
    )
    encoding_carrier = build_cache_pre_claim_marker_encoding_carrier_exactness(
        payload_shape=payload_shape
    )
    storage_locality = build_cache_pre_claim_marker_storage_locality_exactness(
        encoding_carrier=encoding_carrier
    )
    locality_access = build_cache_pre_claim_marker_locality_access_exactness(
        storage_locality=storage_locality
    )
    locality_isolation = build_cache_pre_claim_marker_locality_isolation_exactness(
        locality_access=locality_access
    )
    locality_lifetime = build_cache_pre_claim_marker_locality_lifetime_coupling(
        locality_isolation=locality_isolation
    )
    marker_reclaim_reset = build_cache_pre_claim_marker_reclaim_reset_exactness(
        locality_lifetime_coupling=locality_lifetime
    )
    construction = build_cache_pre_claim_admission_carrier_construction(
        reclaim_reset=marker_reclaim_reset
    )
    field_exactness = build_cache_pre_claim_admission_carrier_field_exactness(
        construction=construction
    )
    encoding = build_cache_pre_claim_admission_carrier_encoding_exactness(
        field_exactness=field_exactness
    )
    carrier_locality = build_cache_pre_claim_admission_carrier_locality_exactness(
        encoding_exactness=encoding
    )
    carrier_access = build_cache_pre_claim_admission_carrier_locality_access_exactness(
        locality_exactness=carrier_locality
    )
    carrier_isolation = build_cache_pre_claim_admission_carrier_locality_isolation_exactness(
        locality_access=carrier_access
    )
    carrier_lifetime = build_cache_pre_claim_admission_carrier_locality_lifetime_coupling(
        locality_isolation=carrier_isolation
    )

    payload = cache_pre_claim_admission_carrier_reclaim_reset_exactness_to_dict(
        build_cache_pre_claim_admission_carrier_reclaim_reset_exactness(
            locality_lifetime_coupling=carrier_lifetime
        )
    )

    assert (
        payload["summary"]["exactness_rung"]
        == "admission_carrier_reclaim_reset_exact"
    )
    assert (
        payload["reclaim_reset_boundary"]["reclaim_reset_status"]
        == "reclaim_resets_bounded_inert_carrier_to_fully_empty_state_before_reuse"
    )
    assert (
        "reclaim_clears_inert_carrier_presence_to_empty_state"
        in payload["reclaim_reset_boundary"]["allowed_reset_semantics"]
    )
    assert (
        "no_reuse_with_stale_carrier_history"
        in payload["forbidden_reset_expansions"]
    )


def test_cache_pre_claim_admission_carrier_reclaim_reset_exactness_module_has_no_platform_dependency() -> None:
    source = Path(__file__).parents[1].joinpath(
        "owlmlx", "cache_pre_claim_admission_carrier_reclaim_reset_exactness.py"
    ).read_text()
    forbidden = [
        "llm_router",
        "ops_dashboard",
        "local-llm-desktop",
        "AI/Agent",
    ]
    for pattern in forbidden:
        assert pattern not in source
