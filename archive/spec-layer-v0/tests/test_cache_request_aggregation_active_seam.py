from __future__ import annotations

from pathlib import Path

from owlmlx import build_cache_request_aggregation_active_seam
from owlmlx.cache_child_exchange_aggregated_dispatch_exactness import (
    CacheChildExchangeAggregatedDispatchExactness,
)
from owlmlx.cache_cohort_to_child_exchange_handoff_exactness import (
    CacheCohortToChildExchangeHandoffExactness,
)
from owlmlx.cache_request_aggregation_active_seam import (
    cache_request_aggregation_active_seam_to_dict,
)
from owlmlx.cache_request_aggregation_window_exactness import CacheRequestAggregationWindowExactness
from owlmlx.cache_request_aggregation_window_reentry import CacheRequestAggregationWindowReentry
from owlmlx.cache_stream_hold_dependency_exactness import (
    CacheStreamHoldDependencyExactness,
)
from owlmlx.cache_stream_backend_terminal_event_exactness import (
    CacheStreamBackendTerminalEventExactness,
)
from owlmlx.cache_stream_backend_terminal_payload_commit_exactness import (
    CacheStreamBackendTerminalPayloadCommitExactness,
)
from owlmlx.cache_stream_backend_terminal_payload_capture_exactness import (
    CacheStreamBackendTerminalPayloadCaptureExactness,
)
from owlmlx.cache_stream_backend_terminal_record_capture_exactness import (
    CacheStreamBackendTerminalRecordCaptureExactness,
)
from owlmlx.cache_stream_backend_terminal_record_prefix_exactness import (
    CacheStreamBackendTerminalRecordPrefixExactness,
)
from owlmlx.cache_stream_backend_terminal_action_discriminant_exactness import (
    CacheStreamBackendTerminalActionDiscriminantExactness,
)
from owlmlx.cache_stream_backend_terminal_notice_capture_exactness import (
    CacheStreamBackendTerminalNoticeCaptureExactness,
)
from owlmlx.cache_stream_backend_terminal_notice_prefix_exactness import (
    CacheStreamBackendTerminalNoticePrefixExactness,
)
from owlmlx.cache_stream_backend_terminal_notice_action_discriminant_exactness import (
    CacheStreamBackendTerminalNoticeActionDiscriminantExactness,
)
from owlmlx.cache_stream_backend_terminal_notice_action_stem_exactness import (
    CacheStreamBackendTerminalNoticeActionStemExactness,
)
from owlmlx.cache_stream_backend_terminal_notice_marker_exactness import (
    CacheStreamBackendTerminalNoticeMarkerExactness,
)
from owlmlx.cache_stream_backend_terminal_notice_marker_prefix_exactness import (
    CacheStreamBackendTerminalNoticeMarkerPrefixExactness,
)
from owlmlx.cache_stream_backend_terminal_notice_marker_stem_exactness import (
    CacheStreamBackendTerminalNoticeMarkerStemExactness,
)
from owlmlx.cache_stream_backend_terminal_notice_marker_discriminant_exactness import (
    CacheStreamBackendTerminalNoticeMarkerDiscriminantExactness,
)
from owlmlx.cache_stream_backend_terminal_notice_marker_key_lead_exactness import (
    CacheStreamBackendTerminalNoticeMarkerKeyLeadExactness,
)
from owlmlx.cache_stream_backend_terminal_notice_leading_discriminator_exactness import (
    CacheStreamBackendTerminalNoticeLeadingDiscriminatorExactness,
)
from owlmlx.cache_stream_backend_terminal_notice_leading_discriminator_prefix_exactness import (
    CacheStreamBackendTerminalNoticeLeadingDiscriminatorPrefixExactness,
)
from owlmlx.cache_stream_backend_terminal_notice_leading_discriminator_stem_exactness import (
    CacheStreamBackendTerminalNoticeLeadingDiscriminatorStemExactness,
)
from owlmlx.cache_stream_backend_terminal_notice_leading_discriminator_discriminant_exactness import (
    CacheStreamBackendTerminalNoticeLeadingDiscriminatorDiscriminantExactness,
)
from owlmlx.cache_stream_backend_terminal_notice_leading_discriminator_marker_exactness import (
    CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerExactness,
)
from owlmlx.cache_stream_backend_terminal_notice_leading_discriminator_marker_prefix_exactness import (
    CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerPrefixExactness,
)
from owlmlx.cache_stream_backend_terminal_notice_leading_discriminator_marker_discriminant_exactness import (
    CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerDiscriminantExactness,
)
from owlmlx.cache_stream_backend_terminal_notice_leading_discriminator_marker_first_unique_boundary_exactness import (
    CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerFirstUniqueBoundaryExactness,
)
from owlmlx.cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_exactness import (
    CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedDiscriminatorExactness,
)
from owlmlx.cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_prefix_exactness import (
    CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedDiscriminatorPrefixExactness,
)
from owlmlx.cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_stem_exactness import (
    CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedDiscriminatorStemExactness,
)
from owlmlx.cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_discriminant_exactness import (
    CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedDiscriminatorDiscriminantExactness,
)
from owlmlx.cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_first_unique_boundary_exactness import (
    CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedDiscriminatorFirstUniqueBoundaryExactness,
)
from owlmlx.cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_exactness import (
    CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedLeadingDiscriminatorExactness,
)
from owlmlx.cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_prefix_exactness import (
    CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedLeadingDiscriminatorPrefixExactness,
)
from owlmlx.cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_stem_exactness import (
    CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedLeadingDiscriminatorStemExactness,
)
from owlmlx.cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_discriminant_exactness import (
    CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedLeadingDiscriminatorDiscriminantExactness,
)
from owlmlx.cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_first_unique_boundary_exactness import (
    CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedLeadingDiscriminatorFirstUniqueBoundaryExactness,
)
from owlmlx.cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_exactness import (
    CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedBoundaryExactness,
)
from owlmlx.cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_prefix_exactness import (
    CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedBoundaryPrefixExactness,
)
from owlmlx.cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_stem_exactness import (
    CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedBoundaryStemExactness,
)
from owlmlx.cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_first_unique_boundary_exactness import (
    CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedBoundaryFirstUniqueBoundaryExactness,
)
from owlmlx.cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_exactness import (
    CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedBoundaryEarlierBoundaryExactness,
)
from owlmlx.cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_earlier_boundary_exactness import (
    CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedBoundaryEarlierEarlierBoundaryExactness,
)
from owlmlx.cache_stream_backend_terminal_notice_leading_discriminator_marker_stem_exactness import (
    CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerStemExactness,
)


def test_cache_request_aggregation_active_seam_defaults_unresolved() -> None:
    payload = cache_request_aggregation_active_seam_to_dict(
        build_cache_request_aggregation_active_seam()
    )

    assert payload["contract"]["surface"] == "owlmlx.cache_request_aggregation_active_seam"


def test_cache_request_aggregation_active_seam_freezes_exact() -> None:
    reentry = CacheRequestAggregationWindowReentry(
        continuous_batching_branch_reduction=object(),
        request_aggregation_window_exactness=object(),
        status="partial",
        reentry_rung="aggregation_reentry_exact",
        selected_reentry_target="request_aggregation_window",
        selected_reentry_target_status="reentered_as_active_cache_subchain",
        preserved_secondary_scheduler_reduction=(
            "shared_prefill_batch_step",
            "interleaved_decode_scheduler",
        ),
        preserved_secondary_runtime_branch="turboquant_preconditions",
        preserved_secondary_runtime_branch_status="preconditions_exact",
        residual_blocker="request aggregation reentered",
        recommended_next_step="active seam",
    )
    exactness = CacheRequestAggregationWindowExactness(
        mechanism_subgap=object(),
        status="partial",
        exactness_rung="aggregation_window_blocker_exact",
        ingress_window_status="missing_pre_gate_admission_window",
        admission_boundary_status="generation_gate_claims_session_before_cohort_formation",
        child_dependency_status="single_request_per_child_exchange_blocks_aggregated_dispatch",
        stream_dependency_status="stream_session_holds_gate_until_completion",
        residual_blocker="request aggregation still blocked",
        recommended_next_step="pre-gate seam",
    )

    payload = cache_request_aggregation_active_seam_to_dict(
        build_cache_request_aggregation_active_seam(
            request_aggregation_window_reentry=reentry,
            request_aggregation_window_exactness=exactness,
        )
    )

    assert payload["summary"]["seam_rung"] == "aggregation_active_seam_exact"
    assert payload["selected_seam"]["seam"] == "pre_gate_admission_window"
    assert payload["preserved_secondary_runtime_branch"]["status"] == "preconditions_exact"


def test_cache_request_aggregation_active_seam_advances_after_window_entry() -> None:
    reentry = CacheRequestAggregationWindowReentry(
        continuous_batching_branch_reduction=object(),
        request_aggregation_window_exactness=object(),
        status="partial",
        reentry_rung="aggregation_reentry_exact",
        selected_reentry_target="request_aggregation_window",
        selected_reentry_target_status="reentered_as_active_cache_subchain",
        preserved_secondary_scheduler_reduction=(
            "shared_prefill_batch_step",
            "interleaved_decode_scheduler",
        ),
        preserved_secondary_runtime_branch="turboquant_preconditions",
        preserved_secondary_runtime_branch_status="preconditions_exact",
        residual_blocker="request aggregation reentered",
        recommended_next_step="active seam",
    )
    exactness = CacheRequestAggregationWindowExactness(
        mechanism_subgap=object(),
        status="partial",
        exactness_rung="aggregation_window_blocker_exact",
        ingress_window_status="bounded_pre_gate_admission_window_present",
        admission_boundary_status="cohort_forms_before_generation_gate_claim",
        child_dependency_status="single_request_per_child_exchange_blocks_aggregated_dispatch",
        stream_dependency_status="stream_session_holds_gate_until_completion",
        residual_blocker="child exchange still blocks",
        recommended_next_step="freeze downstream dependency",
    )
    child_exactness = CacheChildExchangeAggregatedDispatchExactness(
        request_aggregation_window_exactness=exactness,
        status="partial",
        exactness_rung="child_exchange_dependency_exact",
        child_exchange_status="single_request_per_child_exchange_blocks_aggregated_dispatch",
        exchange_shape="single_request_per_exchange",
        next_active_dependency="child_exchange_aggregated_dispatch_dependency",
        next_active_dependency_status="single_request_per_child_exchange_blocks_aggregated_dispatch",
        preserved_stream_dependency_status="stream_session_holds_gate_until_completion",
        residual_blocker="child exchange still blocks",
        recommended_next_step="freeze child exchange",
    )

    payload = cache_request_aggregation_active_seam_to_dict(
        build_cache_request_aggregation_active_seam(
            request_aggregation_window_reentry=reentry,
            request_aggregation_window_exactness=exactness,
            child_exchange_exactness=child_exactness,
        )
    )

    assert payload["summary"]["seam_rung"] == "aggregation_active_seam_exact"
    assert (
        payload["selected_seam"]["seam"]
        == "child_exchange_aggregated_dispatch_dependency"
    )
    assert payload["preserved_secondary_dependencies"] == [
        "stream_session_holds_gate_until_completion"
    ]


def test_cache_request_aggregation_active_seam_advances_after_child_exchange_widening() -> None:
    reentry = CacheRequestAggregationWindowReentry(
        continuous_batching_branch_reduction=object(),
        request_aggregation_window_exactness=object(),
        status="partial",
        reentry_rung="aggregation_reentry_exact",
        selected_reentry_target="request_aggregation_window",
        selected_reentry_target_status="reentered_as_active_cache_subchain",
        preserved_secondary_scheduler_reduction=(
            "shared_prefill_batch_step",
            "interleaved_decode_scheduler",
        ),
        preserved_secondary_runtime_branch="turboquant_preconditions",
        preserved_secondary_runtime_branch_status="preconditions_exact",
        residual_blocker="request aggregation reentered",
        recommended_next_step="active seam",
    )
    exactness = CacheRequestAggregationWindowExactness(
        mechanism_subgap=object(),
        status="partial",
        exactness_rung="aggregation_window_blocker_exact",
        ingress_window_status="bounded_pre_gate_admission_window_present",
        admission_boundary_status="cohort_forms_before_generation_gate_claim",
        child_dependency_status="aggregated_non_stream_child_exchange_visible",
        stream_dependency_status="stream_session_holds_gate_until_completion",
        residual_blocker="cohort handoff still missing",
        recommended_next_step="freeze cohort handoff",
    )
    child_exactness = CacheChildExchangeAggregatedDispatchExactness(
        request_aggregation_window_exactness=exactness,
        status="partial",
        exactness_rung="child_exchange_dependency_exact",
        child_exchange_status="aggregated_non_stream_child_exchange_visible",
        exchange_shape="single_child_exchange_carries_multiple_non_stream_requests",
        next_active_dependency="cohort_to_child_exchange_handoff_dependency",
        next_active_dependency_status="pre_gate_cohort_not_yet_handed_off_to_aggregated_child_exchange",
        preserved_stream_dependency_status="stream_session_holds_gate_until_completion",
        residual_blocker="cohort handoff still missing",
        recommended_next_step="freeze cohort handoff",
    )

    payload = cache_request_aggregation_active_seam_to_dict(
        build_cache_request_aggregation_active_seam(
            request_aggregation_window_reentry=reentry,
            request_aggregation_window_exactness=exactness,
            child_exchange_exactness=child_exactness,
        )
    )

    assert payload["summary"]["seam_rung"] == "aggregation_active_seam_exact"
    assert (
        payload["selected_seam"]["seam"]
        == "cohort_to_child_exchange_handoff_dependency"
    )
    assert (
        payload["selected_seam"]["status"]
        == "pre_gate_cohort_not_yet_handed_off_to_aggregated_child_exchange"
    )
    assert payload["preserved_secondary_dependencies"] == [
        "stream_session_holds_gate_until_completion"
    ]


def test_cache_request_aggregation_active_seam_advances_after_main_path_handoff() -> None:
    reentry = CacheRequestAggregationWindowReentry(
        continuous_batching_branch_reduction=object(),
        request_aggregation_window_exactness=object(),
        status="partial",
        reentry_rung="aggregation_reentry_exact",
        selected_reentry_target="request_aggregation_window",
        selected_reentry_target_status="reentered_as_active_cache_subchain",
        preserved_secondary_scheduler_reduction=(
            "shared_prefill_batch_step",
            "interleaved_decode_scheduler",
        ),
        preserved_secondary_runtime_branch="turboquant_preconditions",
        preserved_secondary_runtime_branch_status="preconditions_exact",
        residual_blocker="request aggregation reentered",
        recommended_next_step="active seam",
    )
    exactness = CacheRequestAggregationWindowExactness(
        mechanism_subgap=object(),
        status="partial",
        exactness_rung="aggregation_window_blocker_exact",
        ingress_window_status="bounded_pre_gate_admission_window_present",
        admission_boundary_status="cohort_forms_before_generation_gate_claim",
        child_dependency_status="cohort_handed_off_to_aggregated_child_exchange_visible",
        stream_dependency_status="stream_session_holds_gate_until_completion",
        residual_blocker="stream hold still blocks",
        recommended_next_step="freeze stream hold",
    )
    child_exactness = CacheChildExchangeAggregatedDispatchExactness(
        request_aggregation_window_exactness=exactness,
        status="partial",
        exactness_rung="child_exchange_dependency_exact",
        child_exchange_status="aggregated_non_stream_child_exchange_visible",
        exchange_shape="single_child_exchange_carries_multiple_non_stream_requests",
        next_active_dependency="cohort_to_child_exchange_handoff_dependency",
        next_active_dependency_status="pre_gate_cohort_not_yet_handed_off_to_aggregated_child_exchange",
        preserved_stream_dependency_status="stream_session_holds_gate_until_completion",
        residual_blocker="cohort handoff still missing",
        recommended_next_step="freeze cohort handoff",
    )
    handoff_exactness = CacheCohortToChildExchangeHandoffExactness(
        child_exchange_exactness=child_exactness,
        status="partial",
        exactness_rung="cohort_to_child_handoff_exact",
        handoff_status="cohort_handed_off_to_aggregated_child_exchange_visible",
        main_path_shape="bounded_pre_gate_cohort_reaches_single_aggregated_non_stream_child_exchange",
        next_active_dependency="stream_session_holds_gate_until_completion",
        next_active_dependency_status="stream_session_holds_gate_until_completion",
        preserved_stream_dependency_status="stream_session_holds_gate_until_completion",
        residual_blocker="stream hold still blocks",
        recommended_next_step="freeze stream hold",
    )

    payload = cache_request_aggregation_active_seam_to_dict(
        build_cache_request_aggregation_active_seam(
            request_aggregation_window_reentry=reentry,
            request_aggregation_window_exactness=exactness,
            child_exchange_exactness=child_exactness,
            cohort_handoff_exactness=handoff_exactness,
        )
    )

    assert payload["summary"]["seam_rung"] == "aggregation_active_seam_exact"
    assert payload["selected_seam"]["seam"] == "stream_session_holds_gate_until_completion"
    assert (
        payload["selected_seam"]["status"]
        == "stream_session_holds_gate_until_completion"
    )
    assert payload["preserved_secondary_dependencies"] == []


def test_cache_request_aggregation_active_seam_advances_after_stream_hold_narrowing() -> None:
    reentry = CacheRequestAggregationWindowReentry(
        continuous_batching_branch_reduction=object(),
        request_aggregation_window_exactness=object(),
        status="partial",
        reentry_rung="aggregation_reentry_exact",
        selected_reentry_target="request_aggregation_window",
        selected_reentry_target_status="reentered_as_active_cache_subchain",
        preserved_secondary_scheduler_reduction=(
            "shared_prefill_batch_step",
            "interleaved_decode_scheduler",
        ),
        preserved_secondary_runtime_branch="turboquant_preconditions",
        preserved_secondary_runtime_branch_status="preconditions_exact",
        residual_blocker="request aggregation reentered",
        recommended_next_step="active seam",
    )
    exactness = CacheRequestAggregationWindowExactness(
        mechanism_subgap=object(),
        status="partial",
        exactness_rung="aggregation_window_blocker_exact",
        ingress_window_status="bounded_pre_gate_admission_window_present",
        admission_boundary_status="cohort_forms_before_generation_gate_claim",
        child_dependency_status="cohort_handed_off_to_aggregated_child_exchange_visible",
        stream_dependency_status="stream_session_holds_gate_until_completion",
        residual_blocker="stream hold still blocks",
        recommended_next_step="freeze stream hold",
    )
    child_exactness = CacheChildExchangeAggregatedDispatchExactness(
        request_aggregation_window_exactness=exactness,
        status="partial",
        exactness_rung="child_exchange_dependency_exact",
        child_exchange_status="aggregated_non_stream_child_exchange_visible",
        exchange_shape="single_child_exchange_carries_multiple_non_stream_requests",
        next_active_dependency="cohort_to_child_exchange_handoff_dependency",
        next_active_dependency_status="pre_gate_cohort_not_yet_handed_off_to_aggregated_child_exchange",
        preserved_stream_dependency_status="stream_session_holds_gate_until_completion",
        residual_blocker="cohort handoff still missing",
        recommended_next_step="freeze cohort handoff",
    )
    handoff_exactness = CacheCohortToChildExchangeHandoffExactness(
        child_exchange_exactness=child_exactness,
        status="partial",
        exactness_rung="cohort_to_child_handoff_exact",
        handoff_status="cohort_handed_off_to_aggregated_child_exchange_visible",
        main_path_shape="bounded_pre_gate_cohort_reaches_single_aggregated_non_stream_child_exchange",
        next_active_dependency="stream_session_holds_gate_until_completion",
        next_active_dependency_status="stream_session_holds_gate_until_completion",
        preserved_stream_dependency_status="stream_session_holds_gate_until_completion",
        residual_blocker="stream hold still blocks",
        recommended_next_step="freeze stream hold",
    )
    stream_hold_exactness = CacheStreamHoldDependencyExactness(
        cohort_handoff_exactness=handoff_exactness,
        status="partial",
        exactness_rung="stream_hold_dependency_exact",
        verdict="stream_hold_dependency_narrowed",
        hold_status="stream_gate_release_decoupled_from_consumer_completion_visible",
        gate_release_boundary="backend_stream_iterator_completion_before_consumer_drain",
        next_active_dependency="stream_backend_iterator_completion_dependency",
        next_active_dependency_status="stream_backend_iterator_holds_gate_until_completion",
        preserved_non_stream_handoff_status="cohort_handed_off_to_aggregated_child_exchange_visible",
        residual_blocker="stream gate release no longer waits for session completion",
        recommended_next_step="freeze backend iterator completion",
    )

    payload = cache_request_aggregation_active_seam_to_dict(
        build_cache_request_aggregation_active_seam(
            request_aggregation_window_reentry=reentry,
            request_aggregation_window_exactness=exactness,
            child_exchange_exactness=child_exactness,
            cohort_handoff_exactness=handoff_exactness,
            stream_hold_exactness=stream_hold_exactness,
        )
    )

    assert payload["summary"]["seam_rung"] == "aggregation_active_seam_exact"
    assert (
        payload["selected_seam"]["seam"]
        == "stream_backend_iterator_completion_dependency"
    )
    assert (
        payload["selected_seam"]["status"]
        == "stream_backend_iterator_holds_gate_until_completion"
    )
    assert payload["preserved_secondary_dependencies"] == []


def test_cache_request_aggregation_active_seam_advances_after_backend_terminal_event_narrowing() -> None:
    reentry = CacheRequestAggregationWindowReentry(
        continuous_batching_branch_reduction=object(),
        request_aggregation_window_exactness=object(),
        status="partial",
        reentry_rung="aggregation_reentry_exact",
        selected_reentry_target="request_aggregation_window",
        selected_reentry_target_status="reentered_as_active_cache_subchain",
        preserved_secondary_scheduler_reduction=(
            "shared_prefill_batch_step",
            "interleaved_decode_scheduler",
        ),
        preserved_secondary_runtime_branch="turboquant_preconditions",
        preserved_secondary_runtime_branch_status="preconditions_exact",
        residual_blocker="request aggregation reentered",
        recommended_next_step="active seam",
    )
    exactness = CacheRequestAggregationWindowExactness(
        mechanism_subgap=object(),
        status="partial",
        exactness_rung="aggregation_window_blocker_exact",
        ingress_window_status="bounded_pre_gate_admission_window_present",
        admission_boundary_status="cohort_forms_before_generation_gate_claim",
        child_dependency_status="cohort_handed_off_to_aggregated_child_exchange_visible",
        stream_dependency_status="stream_session_holds_gate_until_completion",
        residual_blocker="stream hold still blocks",
        recommended_next_step="freeze stream hold",
    )
    child_exactness = CacheChildExchangeAggregatedDispatchExactness(
        request_aggregation_window_exactness=exactness,
        status="partial",
        exactness_rung="child_exchange_dependency_exact",
        child_exchange_status="aggregated_non_stream_child_exchange_visible",
        exchange_shape="single_child_exchange_carries_multiple_non_stream_requests",
        next_active_dependency="cohort_to_child_exchange_handoff_dependency",
        next_active_dependency_status="pre_gate_cohort_not_yet_handed_off_to_aggregated_child_exchange",
        preserved_stream_dependency_status="stream_session_holds_gate_until_completion",
        residual_blocker="cohort handoff still missing",
        recommended_next_step="freeze cohort handoff",
    )
    handoff_exactness = CacheCohortToChildExchangeHandoffExactness(
        child_exchange_exactness=child_exactness,
        status="partial",
        exactness_rung="cohort_to_child_handoff_exact",
        handoff_status="cohort_handed_off_to_aggregated_child_exchange_visible",
        main_path_shape="bounded_pre_gate_cohort_reaches_single_aggregated_non_stream_child_exchange",
        next_active_dependency="stream_session_holds_gate_until_completion",
        next_active_dependency_status="stream_session_holds_gate_until_completion",
        preserved_stream_dependency_status="stream_session_holds_gate_until_completion",
        residual_blocker="stream hold still blocks",
        recommended_next_step="freeze stream hold",
    )
    stream_hold_exactness = CacheStreamHoldDependencyExactness(
        cohort_handoff_exactness=handoff_exactness,
        status="partial",
        exactness_rung="stream_hold_dependency_exact",
        verdict="stream_hold_dependency_narrowed",
        hold_status="stream_gate_release_decoupled_from_consumer_completion_visible",
        gate_release_boundary="backend_stream_iterator_completion_before_consumer_drain",
        next_active_dependency="stream_backend_iterator_completion_dependency",
        next_active_dependency_status="stream_backend_iterator_holds_gate_until_completion",
        preserved_non_stream_handoff_status="cohort_handed_off_to_aggregated_child_exchange_visible",
        residual_blocker="stream gate release no longer waits for session completion",
        recommended_next_step="freeze backend iterator completion",
    )
    backend_terminal_event_exactness = CacheStreamBackendTerminalEventExactness(
        stream_hold_exactness=stream_hold_exactness,
        status="partial",
        exactness_rung="stream_backend_terminal_event_exact",
        verdict="backend_stream_terminal_event_dependency_narrowed",
        terminal_event_status="backend_terminal_event_serial_boundary_visible",
        exchange_boundary="backend_terminal_payload_commit_before_iterator_terminal_event_delivery",
        next_active_dependency="backend_terminal_payload_commit_dependency",
        next_active_dependency_status="backend_stream_exchange_holds_serial_boundary_until_terminal_payload_commit",
        preserved_non_stream_handoff_status="cohort_handed_off_to_aggregated_child_exchange_visible",
        residual_blocker="backend terminal payload commit now blocks more exactly",
        recommended_next_step="freeze backend terminal payload commit seam",
    )

    payload = cache_request_aggregation_active_seam_to_dict(
        build_cache_request_aggregation_active_seam(
            request_aggregation_window_reentry=reentry,
            request_aggregation_window_exactness=exactness,
            child_exchange_exactness=child_exactness,
            cohort_handoff_exactness=handoff_exactness,
            stream_hold_exactness=stream_hold_exactness,
            stream_backend_terminal_event_exactness=backend_terminal_event_exactness,
        )
    )

    assert payload["summary"]["seam_rung"] == "aggregation_active_seam_exact"
    assert payload["selected_seam"]["seam"] == "backend_terminal_payload_commit_dependency"
    assert (
        payload["selected_seam"]["status"]
        == "backend_stream_exchange_holds_serial_boundary_until_terminal_payload_commit"
    )
    assert payload["preserved_secondary_dependencies"] == []


def test_cache_request_aggregation_active_seam_advances_after_backend_terminal_payload_commit_narrowing() -> None:
    reentry = CacheRequestAggregationWindowReentry(
        continuous_batching_branch_reduction=object(),
        request_aggregation_window_exactness=object(),
        status="partial",
        reentry_rung="aggregation_reentry_exact",
        selected_reentry_target="request_aggregation_window",
        selected_reentry_target_status="reentered_as_active_cache_subchain",
        preserved_secondary_scheduler_reduction=(
            "shared_prefill_batch_step",
            "interleaved_decode_scheduler",
        ),
        preserved_secondary_runtime_branch="turboquant_preconditions",
        preserved_secondary_runtime_branch_status="preconditions_exact",
        residual_blocker="request aggregation reentered",
        recommended_next_step="active seam",
    )
    exactness = CacheRequestAggregationWindowExactness(
        mechanism_subgap=object(),
        status="partial",
        exactness_rung="aggregation_window_blocker_exact",
        ingress_window_status="bounded_pre_gate_admission_window_present",
        admission_boundary_status="cohort_forms_before_generation_gate_claim",
        child_dependency_status="cohort_handed_off_to_aggregated_child_exchange_visible",
        stream_dependency_status="stream_session_holds_gate_until_completion",
        residual_blocker="stream hold still blocks",
        recommended_next_step="freeze stream hold",
    )
    child_exactness = CacheChildExchangeAggregatedDispatchExactness(
        request_aggregation_window_exactness=exactness,
        status="partial",
        exactness_rung="child_exchange_dependency_exact",
        child_exchange_status="aggregated_non_stream_child_exchange_visible",
        exchange_shape="single_child_exchange_carries_multiple_non_stream_requests",
        next_active_dependency="cohort_to_child_exchange_handoff_dependency",
        next_active_dependency_status="pre_gate_cohort_not_yet_handed_off_to_aggregated_child_exchange",
        preserved_stream_dependency_status="stream_session_holds_gate_until_completion",
        residual_blocker="cohort handoff still missing",
        recommended_next_step="freeze cohort handoff",
    )
    handoff_exactness = CacheCohortToChildExchangeHandoffExactness(
        child_exchange_exactness=child_exactness,
        status="partial",
        exactness_rung="cohort_to_child_handoff_exact",
        handoff_status="cohort_handed_off_to_aggregated_child_exchange_visible",
        main_path_shape="bounded_pre_gate_cohort_reaches_single_aggregated_non_stream_child_exchange",
        next_active_dependency="stream_session_holds_gate_until_completion",
        next_active_dependency_status="stream_session_holds_gate_until_completion",
        preserved_stream_dependency_status="stream_session_holds_gate_until_completion",
        residual_blocker="stream hold still blocks",
        recommended_next_step="freeze stream hold",
    )
    stream_hold_exactness = CacheStreamHoldDependencyExactness(
        cohort_handoff_exactness=handoff_exactness,
        status="partial",
        exactness_rung="stream_hold_dependency_exact",
        verdict="stream_hold_dependency_narrowed",
        hold_status="stream_gate_release_decoupled_from_consumer_completion_visible",
        gate_release_boundary="backend_stream_iterator_completion_before_consumer_drain",
        next_active_dependency="stream_backend_iterator_completion_dependency",
        next_active_dependency_status="stream_backend_iterator_holds_gate_until_completion",
        preserved_non_stream_handoff_status="cohort_handed_off_to_aggregated_child_exchange_visible",
        residual_blocker="stream gate release no longer waits for session completion",
        recommended_next_step="freeze backend iterator completion",
    )
    backend_terminal_event_exactness = CacheStreamBackendTerminalEventExactness(
        stream_hold_exactness=stream_hold_exactness,
        status="partial",
        exactness_rung="stream_backend_terminal_event_exact",
        verdict="backend_stream_terminal_event_dependency_narrowed",
        terminal_event_status="backend_terminal_event_serial_boundary_visible",
        exchange_boundary="backend_terminal_payload_commit_before_iterator_terminal_event_delivery",
        next_active_dependency="backend_terminal_payload_commit_dependency",
        next_active_dependency_status="backend_stream_exchange_holds_serial_boundary_until_terminal_payload_commit",
        preserved_non_stream_handoff_status="cohort_handed_off_to_aggregated_child_exchange_visible",
        residual_blocker="backend terminal payload commit now blocks more exactly",
        recommended_next_step="freeze backend terminal payload commit seam",
    )
    backend_terminal_payload_commit_exactness = (
        CacheStreamBackendTerminalPayloadCommitExactness(
            backend_terminal_event_exactness=backend_terminal_event_exactness,
            status="partial",
            exactness_rung="stream_backend_terminal_payload_commit_exact",
            verdict="backend_terminal_payload_commit_dependency_narrowed",
            payload_commit_status="backend_serial_boundary_decoupled_from_terminal_payload_commit_visible",
            exchange_boundary="backend_terminal_payload_capture_before_payload_commit",
            next_active_dependency="backend_terminal_payload_capture_dependency",
            next_active_dependency_status="backend_stream_exchange_holds_serial_boundary_until_terminal_payload_capture",
            preserved_non_stream_handoff_status="cohort_handed_off_to_aggregated_child_exchange_visible",
            residual_blocker="backend terminal payload capture now blocks more exactly",
            recommended_next_step="freeze backend terminal payload capture seam",
        )
    )

    payload = cache_request_aggregation_active_seam_to_dict(
        build_cache_request_aggregation_active_seam(
            request_aggregation_window_reentry=reentry,
            request_aggregation_window_exactness=exactness,
            child_exchange_exactness=child_exactness,
            cohort_handoff_exactness=handoff_exactness,
            stream_hold_exactness=stream_hold_exactness,
            stream_backend_terminal_event_exactness=backend_terminal_event_exactness,
            stream_backend_terminal_payload_commit_exactness=(
                backend_terminal_payload_commit_exactness
            ),
        )
    )

    assert payload["summary"]["seam_rung"] == "aggregation_active_seam_exact"
    assert payload["selected_seam"]["seam"] == "backend_terminal_payload_capture_dependency"
    assert (
        payload["selected_seam"]["status"]
        == "backend_stream_exchange_holds_serial_boundary_until_terminal_payload_capture"
    )
    assert payload["preserved_secondary_dependencies"] == []


def test_cache_request_aggregation_active_seam_advances_after_backend_terminal_payload_capture_narrowing() -> None:
    reentry = CacheRequestAggregationWindowReentry(
        continuous_batching_branch_reduction=object(),
        request_aggregation_window_exactness=object(),
        status="partial",
        reentry_rung="aggregation_reentry_exact",
        selected_reentry_target="request_aggregation_window",
        selected_reentry_target_status="reentered_as_active_cache_subchain",
        preserved_secondary_scheduler_reduction=(
            "shared_prefill_batch_step",
            "interleaved_decode_scheduler",
        ),
        preserved_secondary_runtime_branch="turboquant_preconditions",
        preserved_secondary_runtime_branch_status="preconditions_exact",
        residual_blocker="request aggregation reentered",
        recommended_next_step="active seam",
    )
    exactness = CacheRequestAggregationWindowExactness(
        mechanism_subgap=object(),
        status="partial",
        exactness_rung="aggregation_window_blocker_exact",
        ingress_window_status="bounded_pre_gate_admission_window_present",
        admission_boundary_status="cohort_forms_before_generation_gate_claim",
        child_dependency_status="cohort_handed_off_to_aggregated_child_exchange_visible",
        stream_dependency_status="stream_session_holds_gate_until_completion",
        residual_blocker="stream hold still blocks",
        recommended_next_step="freeze stream hold",
    )
    child_exactness = CacheChildExchangeAggregatedDispatchExactness(
        request_aggregation_window_exactness=exactness,
        status="partial",
        exactness_rung="child_exchange_dependency_exact",
        child_exchange_status="aggregated_non_stream_child_exchange_visible",
        exchange_shape="single_child_exchange_carries_multiple_non_stream_requests",
        next_active_dependency="cohort_to_child_exchange_handoff_dependency",
        next_active_dependency_status="pre_gate_cohort_not_yet_handed_off_to_aggregated_child_exchange",
        preserved_stream_dependency_status="stream_session_holds_gate_until_completion",
        residual_blocker="cohort handoff still missing",
        recommended_next_step="freeze cohort handoff",
    )
    handoff_exactness = CacheCohortToChildExchangeHandoffExactness(
        child_exchange_exactness=child_exactness,
        status="partial",
        exactness_rung="cohort_to_child_handoff_exact",
        handoff_status="cohort_handed_off_to_aggregated_child_exchange_visible",
        main_path_shape="bounded_pre_gate_cohort_reaches_single_aggregated_non_stream_child_exchange",
        next_active_dependency="stream_session_holds_gate_until_completion",
        next_active_dependency_status="stream_session_holds_gate_until_completion",
        preserved_stream_dependency_status="stream_session_holds_gate_until_completion",
        residual_blocker="stream hold still blocks",
        recommended_next_step="freeze stream hold",
    )
    stream_hold_exactness = CacheStreamHoldDependencyExactness(
        cohort_handoff_exactness=handoff_exactness,
        status="partial",
        exactness_rung="stream_hold_dependency_exact",
        verdict="stream_hold_dependency_narrowed",
        hold_status="stream_gate_release_decoupled_from_consumer_completion_visible",
        gate_release_boundary="backend_stream_iterator_completion_before_consumer_drain",
        next_active_dependency="stream_backend_iterator_completion_dependency",
        next_active_dependency_status="stream_backend_iterator_holds_gate_until_completion",
        preserved_non_stream_handoff_status="cohort_handed_off_to_aggregated_child_exchange_visible",
        residual_blocker="stream gate release no longer waits for session completion",
        recommended_next_step="freeze backend iterator completion",
    )
    backend_terminal_event_exactness = CacheStreamBackendTerminalEventExactness(
        stream_hold_exactness=stream_hold_exactness,
        status="partial",
        exactness_rung="stream_backend_terminal_event_exact",
        verdict="backend_stream_terminal_event_dependency_narrowed",
        terminal_event_status="backend_terminal_event_serial_boundary_visible",
        exchange_boundary="backend_terminal_payload_commit_before_iterator_terminal_event_delivery",
        next_active_dependency="backend_terminal_payload_commit_dependency",
        next_active_dependency_status="backend_stream_exchange_holds_serial_boundary_until_terminal_payload_commit",
        preserved_non_stream_handoff_status="cohort_handed_off_to_aggregated_child_exchange_visible",
        residual_blocker="backend terminal payload commit now blocks more exactly",
        recommended_next_step="freeze backend terminal payload commit seam",
    )
    backend_terminal_payload_commit_exactness = (
        CacheStreamBackendTerminalPayloadCommitExactness(
            backend_terminal_event_exactness=backend_terminal_event_exactness,
            status="partial",
            exactness_rung="stream_backend_terminal_payload_commit_exact",
            verdict="backend_terminal_payload_commit_dependency_narrowed",
            payload_commit_status="backend_serial_boundary_decoupled_from_terminal_payload_commit_visible",
            exchange_boundary="backend_terminal_payload_capture_before_payload_commit",
            next_active_dependency="backend_terminal_payload_capture_dependency",
            next_active_dependency_status="backend_stream_exchange_holds_serial_boundary_until_terminal_payload_capture",
            preserved_non_stream_handoff_status="cohort_handed_off_to_aggregated_child_exchange_visible",
            residual_blocker="backend terminal payload capture now blocks more exactly",
            recommended_next_step="freeze backend terminal payload capture seam",
        )
    )
    backend_terminal_payload_capture_exactness = (
        CacheStreamBackendTerminalPayloadCaptureExactness(
            backend_terminal_payload_commit_exactness=(
                backend_terminal_payload_commit_exactness
            ),
            status="partial",
            exactness_rung="stream_backend_terminal_payload_capture_exact",
            verdict="backend_terminal_payload_capture_dependency_narrowed",
            payload_capture_status="backend_serial_boundary_decoupled_from_terminal_payload_capture_visible",
            exchange_boundary="backend_terminal_record_capture_before_payload_decode",
            next_active_dependency="backend_terminal_record_capture_dependency",
            next_active_dependency_status="backend_stream_exchange_holds_serial_boundary_until_terminal_record_capture",
            preserved_non_stream_handoff_status="cohort_handed_off_to_aggregated_child_exchange_visible",
            residual_blocker="backend terminal record capture now blocks more exactly",
            recommended_next_step="freeze backend terminal record capture seam",
        )
    )

    payload = cache_request_aggregation_active_seam_to_dict(
        build_cache_request_aggregation_active_seam(
            request_aggregation_window_reentry=reentry,
            request_aggregation_window_exactness=exactness,
            child_exchange_exactness=child_exactness,
            cohort_handoff_exactness=handoff_exactness,
            stream_hold_exactness=stream_hold_exactness,
            stream_backend_terminal_event_exactness=backend_terminal_event_exactness,
            stream_backend_terminal_payload_commit_exactness=(
                backend_terminal_payload_commit_exactness
            ),
            stream_backend_terminal_payload_capture_exactness=(
                backend_terminal_payload_capture_exactness
            ),
        )
    )

    assert payload["summary"]["seam_rung"] == "aggregation_active_seam_exact"
    assert payload["selected_seam"]["seam"] == "backend_terminal_record_capture_dependency"
    assert (
        payload["selected_seam"]["status"]
        == "backend_stream_exchange_holds_serial_boundary_until_terminal_record_capture"
    )
    assert payload["preserved_secondary_dependencies"] == []


def test_cache_request_aggregation_active_seam_advances_after_backend_terminal_record_capture_narrowing() -> None:
    reentry = CacheRequestAggregationWindowReentry(
        continuous_batching_branch_reduction=object(),
        request_aggregation_window_exactness=object(),
        status="partial",
        reentry_rung="aggregation_reentry_exact",
        selected_reentry_target="request_aggregation_window",
        selected_reentry_target_status="reentered_as_active_cache_subchain",
        preserved_secondary_scheduler_reduction=(
            "shared_prefill_batch_step",
            "interleaved_decode_scheduler",
        ),
        preserved_secondary_runtime_branch="turboquant_preconditions",
        preserved_secondary_runtime_branch_status="preconditions_exact",
        residual_blocker="request aggregation reentered",
        recommended_next_step="active seam",
    )
    exactness = CacheRequestAggregationWindowExactness(
        mechanism_subgap=object(),
        status="partial",
        exactness_rung="aggregation_window_blocker_exact",
        ingress_window_status="bounded_pre_gate_admission_window_present",
        admission_boundary_status="cohort_forms_before_generation_gate_claim",
        child_dependency_status="cohort_handed_off_to_aggregated_child_exchange_visible",
        stream_dependency_status="stream_session_holds_gate_until_completion",
        residual_blocker="stream hold still blocks",
        recommended_next_step="freeze stream hold",
    )
    child_exactness = CacheChildExchangeAggregatedDispatchExactness(
        request_aggregation_window_exactness=exactness,
        status="partial",
        exactness_rung="child_exchange_dependency_exact",
        child_exchange_status="aggregated_non_stream_child_exchange_visible",
        exchange_shape="single_child_exchange_carries_multiple_non_stream_requests",
        next_active_dependency="cohort_to_child_exchange_handoff_dependency",
        next_active_dependency_status="pre_gate_cohort_not_yet_handed_off_to_aggregated_child_exchange",
        preserved_stream_dependency_status="stream_session_holds_gate_until_completion",
        residual_blocker="cohort handoff still missing",
        recommended_next_step="freeze cohort handoff",
    )
    handoff_exactness = CacheCohortToChildExchangeHandoffExactness(
        child_exchange_exactness=child_exactness,
        status="partial",
        exactness_rung="cohort_to_child_handoff_exact",
        handoff_status="cohort_handed_off_to_aggregated_child_exchange_visible",
        main_path_shape="bounded_pre_gate_cohort_reaches_single_aggregated_non_stream_child_exchange",
        next_active_dependency="stream_session_holds_gate_until_completion",
        next_active_dependency_status="stream_session_holds_gate_until_completion",
        preserved_stream_dependency_status="stream_session_holds_gate_until_completion",
        residual_blocker="stream hold still blocks",
        recommended_next_step="freeze stream hold",
    )
    stream_hold_exactness = CacheStreamHoldDependencyExactness(
        cohort_handoff_exactness=handoff_exactness,
        status="partial",
        exactness_rung="stream_hold_dependency_exact",
        verdict="stream_hold_dependency_narrowed",
        hold_status="stream_gate_release_decoupled_from_consumer_completion_visible",
        gate_release_boundary="backend_stream_iterator_completion_before_consumer_drain",
        next_active_dependency="stream_backend_iterator_completion_dependency",
        next_active_dependency_status="stream_backend_iterator_holds_gate_until_completion",
        preserved_non_stream_handoff_status="cohort_handed_off_to_aggregated_child_exchange_visible",
        residual_blocker="stream gate release no longer waits for session completion",
        recommended_next_step="freeze backend iterator completion",
    )
    backend_terminal_event_exactness = CacheStreamBackendTerminalEventExactness(
        stream_hold_exactness=stream_hold_exactness,
        status="partial",
        exactness_rung="stream_backend_terminal_event_exact",
        verdict="backend_stream_terminal_event_dependency_narrowed",
        terminal_event_status="backend_terminal_event_serial_boundary_visible",
        exchange_boundary="backend_terminal_payload_commit_before_iterator_terminal_event_delivery",
        next_active_dependency="backend_terminal_payload_commit_dependency",
        next_active_dependency_status="backend_stream_exchange_holds_serial_boundary_until_terminal_payload_commit",
        preserved_non_stream_handoff_status="cohort_handed_off_to_aggregated_child_exchange_visible",
        residual_blocker="backend terminal payload commit now blocks more exactly",
        recommended_next_step="freeze backend terminal payload commit seam",
    )
    backend_terminal_payload_commit_exactness = (
        CacheStreamBackendTerminalPayloadCommitExactness(
            backend_terminal_event_exactness=backend_terminal_event_exactness,
            status="partial",
            exactness_rung="stream_backend_terminal_payload_commit_exact",
            verdict="backend_terminal_payload_commit_dependency_narrowed",
            payload_commit_status="backend_serial_boundary_decoupled_from_terminal_payload_commit_visible",
            exchange_boundary="backend_terminal_payload_capture_before_payload_commit",
            next_active_dependency="backend_terminal_payload_capture_dependency",
            next_active_dependency_status="backend_stream_exchange_holds_serial_boundary_until_terminal_payload_capture",
            preserved_non_stream_handoff_status="cohort_handed_off_to_aggregated_child_exchange_visible",
            residual_blocker="backend terminal payload capture now blocks more exactly",
            recommended_next_step="freeze backend terminal payload capture seam",
        )
    )
    backend_terminal_payload_capture_exactness = (
        CacheStreamBackendTerminalPayloadCaptureExactness(
            backend_terminal_payload_commit_exactness=(
                backend_terminal_payload_commit_exactness
            ),
            status="partial",
            exactness_rung="stream_backend_terminal_payload_capture_exact",
            verdict="backend_terminal_payload_capture_dependency_narrowed",
            payload_capture_status="backend_serial_boundary_decoupled_from_terminal_payload_capture_visible",
            exchange_boundary="backend_terminal_record_capture_before_payload_decode",
            next_active_dependency="backend_terminal_record_capture_dependency",
            next_active_dependency_status="backend_stream_exchange_holds_serial_boundary_until_terminal_record_capture",
            preserved_non_stream_handoff_status="cohort_handed_off_to_aggregated_child_exchange_visible",
            residual_blocker="backend terminal record capture now blocks more exactly",
            recommended_next_step="freeze backend terminal record capture seam",
        )
    )
    backend_terminal_record_capture_exactness = (
        CacheStreamBackendTerminalRecordCaptureExactness(
            backend_terminal_payload_capture_exactness=(
                backend_terminal_payload_capture_exactness
            ),
            status="partial",
            exactness_rung="stream_backend_terminal_record_capture_exact",
            verdict="backend_terminal_record_capture_dependency_narrowed",
            record_capture_status="backend_serial_boundary_decoupled_from_terminal_record_capture_visible",
            exchange_boundary="backend_terminal_record_prefix_detected_before_record_capture",
            next_active_dependency="backend_terminal_record_prefix_dependency",
            next_active_dependency_status="backend_stream_exchange_holds_serial_boundary_until_terminal_record_prefix_detection",
            preserved_non_stream_handoff_status="cohort_handed_off_to_aggregated_child_exchange_visible",
            residual_blocker="backend terminal record prefix now blocks more exactly",
            recommended_next_step="freeze backend terminal record prefix seam",
        )
    )

    payload = cache_request_aggregation_active_seam_to_dict(
        build_cache_request_aggregation_active_seam(
            request_aggregation_window_reentry=reentry,
            request_aggregation_window_exactness=exactness,
            child_exchange_exactness=child_exactness,
            cohort_handoff_exactness=handoff_exactness,
            stream_hold_exactness=stream_hold_exactness,
            stream_backend_terminal_event_exactness=backend_terminal_event_exactness,
            stream_backend_terminal_payload_commit_exactness=(
                backend_terminal_payload_commit_exactness
            ),
            stream_backend_terminal_payload_capture_exactness=(
                backend_terminal_payload_capture_exactness
            ),
            stream_backend_terminal_record_capture_exactness=(
                backend_terminal_record_capture_exactness
            ),
        )
    )

    assert payload["summary"]["seam_rung"] == "aggregation_active_seam_exact"
    assert payload["selected_seam"]["seam"] == "backend_terminal_record_prefix_dependency"
    assert (
        payload["selected_seam"]["status"]
        == "backend_stream_exchange_holds_serial_boundary_until_terminal_record_prefix_detection"
    )
    assert payload["preserved_secondary_dependencies"] == []


def test_cache_request_aggregation_active_seam_advances_after_backend_terminal_record_prefix_narrowing(
) -> None:
    reentry = CacheRequestAggregationWindowReentry(
        continuous_batching_branch_reduction=object(),
        request_aggregation_window_exactness=object(),
        status="partial",
        reentry_rung="aggregation_reentry_exact",
        selected_reentry_target="request_aggregation_window",
        selected_reentry_target_status="reentered_as_active_cache_subchain",
        preserved_secondary_scheduler_reduction=(
            "shared_prefill_batch_step",
            "interleaved_decode_scheduler",
        ),
        preserved_secondary_runtime_branch="turboquant_preconditions",
        preserved_secondary_runtime_branch_status="preconditions_exact",
        residual_blocker="request aggregation reentered",
        recommended_next_step="active seam",
    )
    exactness = CacheRequestAggregationWindowExactness(
        mechanism_subgap=object(),
        status="partial",
        exactness_rung="aggregation_window_blocker_exact",
        ingress_window_status="bounded_pre_gate_admission_window_present",
        admission_boundary_status="cohort_forms_before_generation_gate_claim",
        child_dependency_status="single_request_per_child_exchange_blocks_aggregated_dispatch",
        stream_dependency_status="stream_session_holds_gate_until_completion",
        residual_blocker="window already entered",
        recommended_next_step="freeze child dependency",
    )
    child_exactness = CacheChildExchangeAggregatedDispatchExactness(
        request_aggregation_window_exactness=exactness,
        status="partial",
        exactness_rung="child_exchange_dependency_exact",
        child_exchange_status="aggregated_non_stream_child_exchange_visible",
        exchange_shape="single_aggregated_non_stream_child_exchange",
        next_active_dependency="child_exchange_aggregated_dispatch_dependency",
        next_active_dependency_status="aggregated_non_stream_child_exchange_visible",
        preserved_stream_dependency_status="stream_session_holds_gate_until_completion",
        residual_blocker="stream still blocks",
        recommended_next_step="freeze cohort handoff",
    )
    handoff_exactness = CacheCohortToChildExchangeHandoffExactness(
        child_exchange_exactness=child_exactness,
        status="partial",
        exactness_rung="cohort_to_child_handoff_exact",
        handoff_status="cohort_handed_off_to_aggregated_child_exchange_visible",
        main_path_shape="bounded_pre_gate_cohort_reaches_single_aggregated_non_stream_child_exchange",
        next_active_dependency="stream_session_holds_gate_until_completion",
        next_active_dependency_status="stream_session_holds_gate_until_completion",
        preserved_stream_dependency_status="stream_session_holds_gate_until_completion",
        residual_blocker="stream hold still blocks",
        recommended_next_step="freeze stream hold",
    )
    stream_hold_exactness = CacheStreamHoldDependencyExactness(
        cohort_handoff_exactness=handoff_exactness,
        status="partial",
        exactness_rung="stream_hold_dependency_exact",
        verdict="stream_hold_dependency_narrowed",
        hold_status="stream_gate_release_decoupled_from_consumer_completion_visible",
        gate_release_boundary="backend_stream_iterator_completion_before_consumer_drain",
        next_active_dependency="stream_backend_iterator_completion_dependency",
        next_active_dependency_status="stream_backend_iterator_holds_gate_until_completion",
        preserved_non_stream_handoff_status="cohort_handed_off_to_aggregated_child_exchange_visible",
        residual_blocker="stream gate release no longer waits for session completion",
        recommended_next_step="freeze backend iterator completion",
    )
    backend_terminal_event_exactness = CacheStreamBackendTerminalEventExactness(
        stream_hold_exactness=stream_hold_exactness,
        status="partial",
        exactness_rung="stream_backend_terminal_event_exact",
        verdict="backend_stream_terminal_event_dependency_narrowed",
        terminal_event_status="backend_terminal_event_serial_boundary_visible",
        exchange_boundary="backend_terminal_payload_commit_before_iterator_terminal_event_delivery",
        next_active_dependency="backend_terminal_payload_commit_dependency",
        next_active_dependency_status="backend_stream_exchange_holds_serial_boundary_until_terminal_payload_commit",
        preserved_non_stream_handoff_status="cohort_handed_off_to_aggregated_child_exchange_visible",
        residual_blocker="backend terminal payload commit now blocks more exactly",
        recommended_next_step="freeze backend terminal payload commit seam",
    )
    backend_terminal_payload_commit_exactness = (
        CacheStreamBackendTerminalPayloadCommitExactness(
            backend_terminal_event_exactness=backend_terminal_event_exactness,
            status="partial",
            exactness_rung="stream_backend_terminal_payload_commit_exact",
            verdict="backend_terminal_payload_commit_dependency_narrowed",
            payload_commit_status="backend_serial_boundary_decoupled_from_terminal_payload_commit_visible",
            exchange_boundary="backend_terminal_payload_capture_before_payload_commit",
            next_active_dependency="backend_terminal_payload_capture_dependency",
            next_active_dependency_status="backend_stream_exchange_holds_serial_boundary_until_terminal_payload_capture",
            preserved_non_stream_handoff_status="cohort_handed_off_to_aggregated_child_exchange_visible",
            residual_blocker="backend terminal payload capture now blocks more exactly",
            recommended_next_step="freeze backend terminal payload capture seam",
        )
    )
    backend_terminal_payload_capture_exactness = (
        CacheStreamBackendTerminalPayloadCaptureExactness(
            backend_terminal_payload_commit_exactness=(
                backend_terminal_payload_commit_exactness
            ),
            status="partial",
            exactness_rung="stream_backend_terminal_payload_capture_exact",
            verdict="backend_terminal_payload_capture_dependency_narrowed",
            payload_capture_status="backend_serial_boundary_decoupled_from_terminal_payload_capture_visible",
            exchange_boundary="backend_terminal_record_capture_before_payload_decode",
            next_active_dependency="backend_terminal_record_capture_dependency",
            next_active_dependency_status="backend_stream_exchange_holds_serial_boundary_until_terminal_record_capture",
            preserved_non_stream_handoff_status="cohort_handed_off_to_aggregated_child_exchange_visible",
            residual_blocker="backend terminal record capture now blocks more exactly",
            recommended_next_step="freeze backend terminal record capture seam",
        )
    )
    backend_terminal_record_capture_exactness = (
        CacheStreamBackendTerminalRecordCaptureExactness(
            backend_terminal_payload_capture_exactness=(
                backend_terminal_payload_capture_exactness
            ),
            status="partial",
            exactness_rung="stream_backend_terminal_record_capture_exact",
            verdict="backend_terminal_record_capture_dependency_narrowed",
            record_capture_status="backend_serial_boundary_decoupled_from_terminal_record_capture_visible",
            exchange_boundary="backend_terminal_record_prefix_detected_before_record_capture",
            next_active_dependency="backend_terminal_record_prefix_dependency",
            next_active_dependency_status="backend_stream_exchange_holds_serial_boundary_until_terminal_record_prefix_detection",
            preserved_non_stream_handoff_status="cohort_handed_off_to_aggregated_child_exchange_visible",
            residual_blocker="backend terminal record prefix now blocks more exactly",
            recommended_next_step="freeze backend terminal record prefix seam",
        )
    )
    backend_terminal_record_prefix_exactness = (
        CacheStreamBackendTerminalRecordPrefixExactness(
            backend_terminal_record_capture_exactness=(
                backend_terminal_record_capture_exactness
            ),
            status="partial",
            exactness_rung="stream_backend_terminal_record_prefix_exact",
            verdict="backend_terminal_record_prefix_dependency_narrowed",
            prefix_status="backend_serial_boundary_decoupled_from_terminal_record_prefix_detection_visible",
            exchange_boundary="backend_terminal_action_discriminant_detected_before_full_record_prefix",
            next_active_dependency="backend_terminal_action_discriminant_dependency",
            next_active_dependency_status="backend_stream_exchange_holds_serial_boundary_until_terminal_action_discriminant_detection",
            preserved_non_stream_handoff_status="cohort_handed_off_to_aggregated_child_exchange_visible",
            residual_blocker="backend terminal action discriminant now blocks more exactly",
            recommended_next_step="freeze backend terminal action discriminant seam",
        )
    )

    payload = cache_request_aggregation_active_seam_to_dict(
        build_cache_request_aggregation_active_seam(
            request_aggregation_window_reentry=reentry,
            request_aggregation_window_exactness=exactness,
            child_exchange_exactness=child_exactness,
            cohort_handoff_exactness=handoff_exactness,
            stream_hold_exactness=stream_hold_exactness,
            stream_backend_terminal_event_exactness=backend_terminal_event_exactness,
            stream_backend_terminal_payload_commit_exactness=(
                backend_terminal_payload_commit_exactness
            ),
            stream_backend_terminal_payload_capture_exactness=(
                backend_terminal_payload_capture_exactness
            ),
            stream_backend_terminal_record_capture_exactness=(
                backend_terminal_record_capture_exactness
            ),
            stream_backend_terminal_record_prefix_exactness=(
                backend_terminal_record_prefix_exactness
            ),
        )
    )

    assert payload["summary"]["seam_rung"] == "aggregation_active_seam_exact"
    assert payload["selected_seam"]["seam"] == "backend_terminal_action_discriminant_dependency"
    assert (
        payload["selected_seam"]["status"]
        == "backend_stream_exchange_holds_serial_boundary_until_terminal_action_discriminant_detection"
    )
    assert payload["preserved_secondary_dependencies"] == []


def test_cache_request_aggregation_active_seam_advances_after_backend_terminal_action_discriminant_narrowing(
) -> None:
    reentry = CacheRequestAggregationWindowReentry(
        continuous_batching_branch_reduction=object(),
        request_aggregation_window_exactness=object(),
        status="partial",
        reentry_rung="aggregation_reentry_exact",
        selected_reentry_target="request_aggregation_window",
        selected_reentry_target_status="reentered_as_active_cache_subchain",
        preserved_secondary_scheduler_reduction=(
            "shared_prefill_batch_step",
            "interleaved_decode_scheduler",
        ),
        preserved_secondary_runtime_branch="turboquant_preconditions",
        preserved_secondary_runtime_branch_status="preconditions_exact",
        residual_blocker="request aggregation reentered",
        recommended_next_step="active seam",
    )
    exactness = CacheRequestAggregationWindowExactness(
        mechanism_subgap=object(),
        status="partial",
        exactness_rung="aggregation_window_blocker_exact",
        ingress_window_status="bounded_pre_gate_admission_window_present",
        admission_boundary_status="cohort_forms_before_generation_gate_claim",
        child_dependency_status="single_request_per_child_exchange_blocks_aggregated_dispatch",
        stream_dependency_status="stream_session_holds_gate_until_completion",
        residual_blocker="window already entered",
        recommended_next_step="freeze child dependency",
    )
    child_exactness = CacheChildExchangeAggregatedDispatchExactness(
        request_aggregation_window_exactness=exactness,
        status="partial",
        exactness_rung="child_exchange_dependency_exact",
        child_exchange_status="aggregated_non_stream_child_exchange_visible",
        exchange_shape="single_aggregated_non_stream_child_exchange",
        next_active_dependency="child_exchange_aggregated_dispatch_dependency",
        next_active_dependency_status="aggregated_non_stream_child_exchange_visible",
        preserved_stream_dependency_status="stream_session_holds_gate_until_completion",
        residual_blocker="stream still blocks",
        recommended_next_step="freeze cohort handoff",
    )
    handoff_exactness = CacheCohortToChildExchangeHandoffExactness(
        child_exchange_exactness=child_exactness,
        status="partial",
        exactness_rung="cohort_to_child_handoff_exact",
        handoff_status="cohort_handed_off_to_aggregated_child_exchange_visible",
        main_path_shape="bounded_pre_gate_cohort_reaches_single_aggregated_non_stream_child_exchange",
        next_active_dependency="stream_session_holds_gate_until_completion",
        next_active_dependency_status="stream_session_holds_gate_until_completion",
        preserved_stream_dependency_status="stream_session_holds_gate_until_completion",
        residual_blocker="stream hold still blocks",
        recommended_next_step="freeze stream hold",
    )
    stream_hold_exactness = CacheStreamHoldDependencyExactness(
        cohort_handoff_exactness=handoff_exactness,
        status="partial",
        exactness_rung="stream_hold_dependency_exact",
        verdict="stream_hold_dependency_narrowed",
        hold_status="stream_gate_release_decoupled_from_consumer_completion_visible",
        gate_release_boundary="backend_stream_iterator_completion_before_consumer_drain",
        next_active_dependency="stream_backend_iterator_completion_dependency",
        next_active_dependency_status="stream_backend_iterator_holds_gate_until_completion",
        preserved_non_stream_handoff_status="cohort_handed_off_to_aggregated_child_exchange_visible",
        residual_blocker="stream gate release no longer waits for session completion",
        recommended_next_step="freeze backend iterator completion",
    )
    backend_terminal_event_exactness = CacheStreamBackendTerminalEventExactness(
        stream_hold_exactness=stream_hold_exactness,
        status="partial",
        exactness_rung="stream_backend_terminal_event_exact",
        verdict="backend_stream_terminal_event_dependency_narrowed",
        terminal_event_status="backend_terminal_event_serial_boundary_visible",
        exchange_boundary="backend_terminal_payload_commit_before_iterator_terminal_event_delivery",
        next_active_dependency="backend_terminal_payload_commit_dependency",
        next_active_dependency_status="backend_stream_exchange_holds_serial_boundary_until_terminal_payload_commit",
        preserved_non_stream_handoff_status="cohort_handed_off_to_aggregated_child_exchange_visible",
        residual_blocker="backend terminal payload commit now blocks more exactly",
        recommended_next_step="freeze backend terminal payload commit seam",
    )
    backend_terminal_payload_commit_exactness = (
        CacheStreamBackendTerminalPayloadCommitExactness(
            backend_terminal_event_exactness=backend_terminal_event_exactness,
            status="partial",
            exactness_rung="stream_backend_terminal_payload_commit_exact",
            verdict="backend_terminal_payload_commit_dependency_narrowed",
            payload_commit_status="backend_serial_boundary_decoupled_from_terminal_payload_commit_visible",
            exchange_boundary="backend_terminal_payload_capture_before_payload_commit",
            next_active_dependency="backend_terminal_payload_capture_dependency",
            next_active_dependency_status="backend_stream_exchange_holds_serial_boundary_until_terminal_payload_capture",
            preserved_non_stream_handoff_status="cohort_handed_off_to_aggregated_child_exchange_visible",
            residual_blocker="backend terminal payload capture now blocks more exactly",
            recommended_next_step="freeze backend terminal payload capture seam",
        )
    )
    backend_terminal_payload_capture_exactness = (
        CacheStreamBackendTerminalPayloadCaptureExactness(
            backend_terminal_payload_commit_exactness=(
                backend_terminal_payload_commit_exactness
            ),
            status="partial",
            exactness_rung="stream_backend_terminal_payload_capture_exact",
            verdict="backend_terminal_payload_capture_dependency_narrowed",
            payload_capture_status="backend_serial_boundary_decoupled_from_terminal_payload_capture_visible",
            exchange_boundary="backend_terminal_record_capture_before_payload_decode",
            next_active_dependency="backend_terminal_record_capture_dependency",
            next_active_dependency_status="backend_stream_exchange_holds_serial_boundary_until_terminal_record_capture",
            preserved_non_stream_handoff_status="cohort_handed_off_to_aggregated_child_exchange_visible",
            residual_blocker="backend terminal record capture now blocks more exactly",
            recommended_next_step="freeze backend terminal record capture seam",
        )
    )
    backend_terminal_record_capture_exactness = (
        CacheStreamBackendTerminalRecordCaptureExactness(
            backend_terminal_payload_capture_exactness=(
                backend_terminal_payload_capture_exactness
            ),
            status="partial",
            exactness_rung="stream_backend_terminal_record_capture_exact",
            verdict="backend_terminal_record_capture_dependency_narrowed",
            record_capture_status="backend_serial_boundary_decoupled_from_terminal_record_capture_visible",
            exchange_boundary="backend_terminal_record_prefix_detected_before_record_capture",
            next_active_dependency="backend_terminal_record_prefix_dependency",
            next_active_dependency_status="backend_stream_exchange_holds_serial_boundary_until_terminal_record_prefix_detection",
            preserved_non_stream_handoff_status="cohort_handed_off_to_aggregated_child_exchange_visible",
            residual_blocker="backend terminal record prefix now blocks more exactly",
            recommended_next_step="freeze backend terminal record prefix seam",
        )
    )
    backend_terminal_record_prefix_exactness = (
        CacheStreamBackendTerminalRecordPrefixExactness(
            backend_terminal_record_capture_exactness=(
                backend_terminal_record_capture_exactness
            ),
            status="partial",
            exactness_rung="stream_backend_terminal_record_prefix_exact",
            verdict="backend_terminal_record_prefix_dependency_narrowed",
            prefix_status="backend_serial_boundary_decoupled_from_terminal_record_prefix_detection_visible",
            exchange_boundary="backend_terminal_action_discriminant_detected_before_full_record_prefix",
            next_active_dependency="backend_terminal_action_discriminant_dependency",
            next_active_dependency_status="backend_stream_exchange_holds_serial_boundary_until_terminal_action_discriminant_detection",
            preserved_non_stream_handoff_status="cohort_handed_off_to_aggregated_child_exchange_visible",
            residual_blocker="backend terminal action discriminant now blocks more exactly",
            recommended_next_step="freeze backend terminal action discriminant seam",
        )
    )
    backend_terminal_action_discriminant_exactness = (
        CacheStreamBackendTerminalActionDiscriminantExactness(
            backend_terminal_record_prefix_exactness=(
                backend_terminal_record_prefix_exactness
            ),
            status="partial",
            exactness_rung="stream_backend_terminal_action_discriminant_exact",
            verdict="backend_terminal_action_discriminant_dependency_narrowed",
            action_discriminant_status="backend_serial_boundary_decoupled_from_terminal_action_discriminant_detection_visible",
            exchange_boundary="backend_terminal_notice_captured_before_terminal_action_discriminant_detection",
            next_active_dependency="backend_terminal_notice_capture_dependency",
            next_active_dependency_status="backend_stream_exchange_holds_serial_boundary_until_terminal_notice_capture",
            preserved_non_stream_handoff_status="cohort_handed_off_to_aggregated_child_exchange_visible",
            residual_blocker="backend terminal notice now blocks more exactly",
            recommended_next_step="freeze backend terminal notice seam",
        )
    )

    payload = cache_request_aggregation_active_seam_to_dict(
        build_cache_request_aggregation_active_seam(
            request_aggregation_window_reentry=reentry,
            request_aggregation_window_exactness=exactness,
            child_exchange_exactness=child_exactness,
            cohort_handoff_exactness=handoff_exactness,
            stream_hold_exactness=stream_hold_exactness,
            stream_backend_terminal_event_exactness=backend_terminal_event_exactness,
            stream_backend_terminal_payload_commit_exactness=(
                backend_terminal_payload_commit_exactness
            ),
            stream_backend_terminal_payload_capture_exactness=(
                backend_terminal_payload_capture_exactness
            ),
            stream_backend_terminal_record_capture_exactness=(
                backend_terminal_record_capture_exactness
            ),
            stream_backend_terminal_record_prefix_exactness=(
                backend_terminal_record_prefix_exactness
            ),
            stream_backend_terminal_action_discriminant_exactness=(
                backend_terminal_action_discriminant_exactness
            ),
        )
    )

    assert payload["summary"]["seam_rung"] == "aggregation_active_seam_exact"
    assert payload["selected_seam"]["seam"] == "backend_terminal_notice_capture_dependency"
    assert (
        payload["selected_seam"]["status"]
        == "backend_stream_exchange_holds_serial_boundary_until_terminal_notice_capture"
    )
    assert payload["preserved_secondary_dependencies"] == []


def test_cache_request_aggregation_active_seam_advances_after_backend_terminal_notice_capture_narrowing(
) -> None:
    reentry = CacheRequestAggregationWindowReentry(
        continuous_batching_branch_reduction=object(),
        request_aggregation_window_exactness=object(),
        status="partial",
        reentry_rung="aggregation_reentry_exact",
        selected_reentry_target="request_aggregation_window",
        selected_reentry_target_status="reentered_as_active_cache_subchain",
        preserved_secondary_scheduler_reduction=(
            "shared_prefill_batch_step",
            "interleaved_decode_scheduler",
        ),
        preserved_secondary_runtime_branch="turboquant_preconditions",
        preserved_secondary_runtime_branch_status="preconditions_exact",
        residual_blocker="request aggregation reentered",
        recommended_next_step="active seam",
    )
    exactness = CacheRequestAggregationWindowExactness(
        mechanism_subgap=object(),
        status="partial",
        exactness_rung="aggregation_window_blocker_exact",
        ingress_window_status="bounded_request_aggregation_window_present_before_gate_claim",
        admission_boundary_status="bounded_cohort_window_precedes_whole_request_gate_claim_without_gate_transfer",
        child_dependency_status="single_request_per_child_exchange_blocks_aggregated_dispatch",
        stream_dependency_status="stream_session_holds_gate_until_completion",
        residual_blocker="request aggregation still blocked",
        recommended_next_step="pre-gate seam",
    )
    child_exactness = CacheChildExchangeAggregatedDispatchExactness(
        request_aggregation_window_exactness=exactness,
        status="partial",
        exactness_rung="child_exchange_dependency_exact",
        child_exchange_status="aggregated_non_stream_child_exchange_visible",
        exchange_shape="single_aggregated_non_stream_child_exchange",
        next_active_dependency="child_exchange_aggregated_dispatch_dependency",
        next_active_dependency_status="aggregated_non_stream_child_exchange_visible",
        preserved_stream_dependency_status="stream_session_holds_gate_until_completion",
        residual_blocker="cohort handoff still blocks",
        recommended_next_step="freeze cohort handoff",
    )
    handoff_exactness = CacheCohortToChildExchangeHandoffExactness(
        child_exchange_exactness=child_exactness,
        status="partial",
        exactness_rung="cohort_to_child_handoff_exact",
        handoff_status="cohort_handed_off_to_aggregated_child_exchange_visible",
        main_path_shape="bounded_pre_gate_cohort_reaches_single_aggregated_non_stream_child_exchange",
        next_active_dependency="stream_backend_iterator_completion_dependency",
        next_active_dependency_status="stream_backend_iterator_holds_gate_until_completion",
        preserved_stream_dependency_status="stream_session_holds_gate_until_completion",
        residual_blocker="stream hold now blocks more exactly",
        recommended_next_step="freeze stream hold",
    )
    stream_hold_exactness = CacheStreamHoldDependencyExactness(
        cohort_handoff_exactness=handoff_exactness,
        status="partial",
        exactness_rung="stream_hold_dependency_exact",
        verdict="stream_hold_dependency_narrowed",
        hold_status="stream_gate_release_decoupled_from_consumer_completion_visible",
        gate_release_boundary="backend_stream_iterator_completion_before_consumer_drain",
        next_active_dependency="stream_backend_iterator_completion_dependency",
        next_active_dependency_status="stream_backend_iterator_holds_gate_until_completion",
        preserved_non_stream_handoff_status="cohort_handed_off_to_aggregated_child_exchange_visible",
        residual_blocker="backend iterator still blocks",
        recommended_next_step="freeze backend iterator seam",
    )
    backend_terminal_event_exactness = CacheStreamBackendTerminalEventExactness(
        stream_hold_exactness=stream_hold_exactness,
        status="partial",
        exactness_rung="stream_backend_terminal_event_exact",
        verdict="backend_stream_terminal_event_dependency_narrowed",
        terminal_event_status="backend_terminal_event_serial_boundary_visible",
        exchange_boundary="backend_terminal_payload_commit_before_iterator_terminal_event_delivery",
        next_active_dependency="backend_terminal_payload_commit_dependency",
        next_active_dependency_status="backend_stream_exchange_holds_serial_boundary_until_terminal_payload_commit",
        preserved_non_stream_handoff_status="cohort_handed_off_to_aggregated_child_exchange_visible",
        residual_blocker="backend terminal payload commit now blocks more exactly",
        recommended_next_step="freeze backend terminal payload commit seam",
    )
    backend_terminal_payload_commit_exactness = (
        CacheStreamBackendTerminalPayloadCommitExactness(
            backend_terminal_event_exactness=backend_terminal_event_exactness,
            status="partial",
            exactness_rung="stream_backend_terminal_payload_commit_exact",
            verdict="backend_terminal_payload_commit_dependency_narrowed",
            payload_commit_status="backend_serial_boundary_decoupled_from_terminal_payload_commit_visible",
            exchange_boundary="backend_terminal_payload_capture_before_payload_commit",
            next_active_dependency="backend_terminal_payload_capture_dependency",
            next_active_dependency_status="backend_stream_exchange_holds_serial_boundary_until_terminal_payload_capture",
            preserved_non_stream_handoff_status="cohort_handed_off_to_aggregated_child_exchange_visible",
            residual_blocker="backend terminal payload capture now blocks more exactly",
            recommended_next_step="freeze backend terminal payload capture seam",
        )
    )
    backend_terminal_payload_capture_exactness = (
        CacheStreamBackendTerminalPayloadCaptureExactness(
            backend_terminal_payload_commit_exactness=(
                backend_terminal_payload_commit_exactness
            ),
            status="partial",
            exactness_rung="stream_backend_terminal_payload_capture_exact",
            verdict="backend_terminal_payload_capture_dependency_narrowed",
            payload_capture_status="backend_serial_boundary_decoupled_from_terminal_payload_capture_visible",
            exchange_boundary="backend_terminal_record_capture_before_payload_decode",
            next_active_dependency="backend_terminal_record_capture_dependency",
            next_active_dependency_status="backend_stream_exchange_holds_serial_boundary_until_terminal_record_capture",
            preserved_non_stream_handoff_status="cohort_handed_off_to_aggregated_child_exchange_visible",
            residual_blocker="backend terminal record capture now blocks more exactly",
            recommended_next_step="freeze backend terminal record capture seam",
        )
    )
    backend_terminal_record_capture_exactness = (
        CacheStreamBackendTerminalRecordCaptureExactness(
            backend_terminal_payload_capture_exactness=(
                backend_terminal_payload_capture_exactness
            ),
            status="partial",
            exactness_rung="stream_backend_terminal_record_capture_exact",
            verdict="backend_terminal_record_capture_dependency_narrowed",
            record_capture_status="backend_serial_boundary_decoupled_from_terminal_record_capture_visible",
            exchange_boundary="backend_terminal_record_prefix_detected_before_record_capture",
            next_active_dependency="backend_terminal_record_prefix_dependency",
            next_active_dependency_status="backend_stream_exchange_holds_serial_boundary_until_terminal_record_prefix_detection",
            preserved_non_stream_handoff_status="cohort_handed_off_to_aggregated_child_exchange_visible",
            residual_blocker="backend terminal record prefix now blocks more exactly",
            recommended_next_step="freeze backend terminal record prefix seam",
        )
    )
    backend_terminal_record_prefix_exactness = (
        CacheStreamBackendTerminalRecordPrefixExactness(
            backend_terminal_record_capture_exactness=(
                backend_terminal_record_capture_exactness
            ),
            status="partial",
            exactness_rung="stream_backend_terminal_record_prefix_exact",
            verdict="backend_terminal_record_prefix_dependency_narrowed",
            prefix_status="backend_serial_boundary_decoupled_from_terminal_record_prefix_detection_visible",
            exchange_boundary="backend_terminal_action_discriminant_detected_before_full_record_prefix",
            next_active_dependency="backend_terminal_action_discriminant_dependency",
            next_active_dependency_status="backend_stream_exchange_holds_serial_boundary_until_terminal_action_discriminant_detection",
            preserved_non_stream_handoff_status="cohort_handed_off_to_aggregated_child_exchange_visible",
            residual_blocker="backend terminal action discriminant now blocks more exactly",
            recommended_next_step="freeze backend terminal action discriminant seam",
        )
    )
    backend_terminal_action_discriminant_exactness = (
        CacheStreamBackendTerminalActionDiscriminantExactness(
            backend_terminal_record_prefix_exactness=(
                backend_terminal_record_prefix_exactness
            ),
            status="partial",
            exactness_rung="stream_backend_terminal_action_discriminant_exact",
            verdict="backend_terminal_action_discriminant_dependency_narrowed",
            action_discriminant_status="backend_serial_boundary_decoupled_from_terminal_action_discriminant_detection_visible",
            exchange_boundary="backend_terminal_notice_captured_before_terminal_action_discriminant_detection",
            next_active_dependency="backend_terminal_notice_capture_dependency",
            next_active_dependency_status="backend_stream_exchange_holds_serial_boundary_until_terminal_notice_capture",
            preserved_non_stream_handoff_status="cohort_handed_off_to_aggregated_child_exchange_visible",
            residual_blocker="backend terminal notice now blocks more exactly",
            recommended_next_step="freeze backend terminal notice seam",
        )
    )
    backend_terminal_notice_capture_exactness = (
        CacheStreamBackendTerminalNoticeCaptureExactness(
            backend_terminal_action_discriminant_exactness=(
                backend_terminal_action_discriminant_exactness
            ),
            status="partial",
            exactness_rung="stream_backend_terminal_notice_capture_exact",
            verdict="backend_terminal_notice_capture_dependency_narrowed",
            notice_capture_status="backend_serial_boundary_decoupled_from_terminal_notice_capture_visible",
            exchange_boundary="backend_terminal_notice_prefix_detected_before_notice_capture",
            next_active_dependency="backend_terminal_notice_prefix_dependency",
            next_active_dependency_status="backend_stream_exchange_holds_serial_boundary_until_terminal_notice_prefix_detection",
            preserved_non_stream_handoff_status="cohort_handed_off_to_aggregated_child_exchange_visible",
            residual_blocker="backend terminal notice prefix now blocks more exactly",
            recommended_next_step="freeze backend terminal notice prefix seam",
        )
    )

    payload = cache_request_aggregation_active_seam_to_dict(
        build_cache_request_aggregation_active_seam(
            request_aggregation_window_reentry=reentry,
            request_aggregation_window_exactness=exactness,
            child_exchange_exactness=child_exactness,
            cohort_handoff_exactness=handoff_exactness,
            stream_hold_exactness=stream_hold_exactness,
            stream_backend_terminal_event_exactness=backend_terminal_event_exactness,
            stream_backend_terminal_payload_commit_exactness=(
                backend_terminal_payload_commit_exactness
            ),
            stream_backend_terminal_payload_capture_exactness=(
                backend_terminal_payload_capture_exactness
            ),
            stream_backend_terminal_record_capture_exactness=(
                backend_terminal_record_capture_exactness
            ),
            stream_backend_terminal_record_prefix_exactness=(
                backend_terminal_record_prefix_exactness
            ),
            stream_backend_terminal_action_discriminant_exactness=(
                backend_terminal_action_discriminant_exactness
            ),
            stream_backend_terminal_notice_capture_exactness=(
                backend_terminal_notice_capture_exactness
            ),
        )
    )

    assert payload["summary"]["seam_rung"] == "aggregation_active_seam_exact"
    assert payload["selected_seam"]["seam"] == "backend_terminal_notice_prefix_dependency"
    assert (
        payload["selected_seam"]["status"]
        == "backend_stream_exchange_holds_serial_boundary_until_terminal_notice_prefix_detection"
    )
    assert payload["preserved_secondary_dependencies"] == []


def test_cache_request_aggregation_active_seam_advances_after_backend_terminal_notice_action_discriminant_narrowing(
) -> None:
    reentry = CacheRequestAggregationWindowReentry(
        continuous_batching_branch_reduction=object(),
        request_aggregation_window_exactness=object(),
        status="partial",
        reentry_rung="aggregation_reentry_exact",
        selected_reentry_target="request_aggregation_window",
        selected_reentry_target_status="reentered_as_active_cache_subchain",
        preserved_secondary_scheduler_reduction=(
            "shared_prefill_batch_step",
            "interleaved_decode_scheduler",
        ),
        preserved_secondary_runtime_branch="turboquant_preconditions",
        preserved_secondary_runtime_branch_status="preconditions_exact",
        residual_blocker="request aggregation reentered",
        recommended_next_step="active seam",
    )
    exactness = CacheRequestAggregationWindowExactness(
        mechanism_subgap=object(),
        status="partial",
        exactness_rung="aggregation_window_blocker_exact",
        ingress_window_status="bounded_request_aggregation_window_present_before_gate_claim",
        admission_boundary_status="bounded_cohort_window_precedes_whole_request_gate_claim_without_gate_transfer",
        child_dependency_status="single_request_per_child_exchange_blocks_aggregated_dispatch",
        stream_dependency_status="stream_session_holds_gate_until_completion",
        residual_blocker="request aggregation still blocked",
        recommended_next_step="pre-gate seam",
    )
    child_exactness = CacheChildExchangeAggregatedDispatchExactness(
        request_aggregation_window_exactness=exactness,
        status="partial",
        exactness_rung="child_exchange_dependency_exact",
        child_exchange_status="aggregated_non_stream_child_exchange_visible",
        exchange_shape="single_aggregated_non_stream_child_exchange",
        next_active_dependency="child_exchange_aggregated_dispatch_dependency",
        next_active_dependency_status="aggregated_non_stream_child_exchange_visible",
        preserved_stream_dependency_status="stream_session_holds_gate_until_completion",
        residual_blocker="cohort handoff still blocks",
        recommended_next_step="freeze cohort handoff",
    )
    handoff_exactness = CacheCohortToChildExchangeHandoffExactness(
        child_exchange_exactness=child_exactness,
        status="partial",
        exactness_rung="cohort_to_child_handoff_exact",
        handoff_status="cohort_handed_off_to_aggregated_child_exchange_visible",
        main_path_shape="bounded_pre_gate_cohort_reaches_single_aggregated_non_stream_child_exchange",
        next_active_dependency="stream_backend_iterator_completion_dependency",
        next_active_dependency_status="stream_backend_iterator_holds_gate_until_completion",
        preserved_stream_dependency_status="stream_session_holds_gate_until_completion",
        residual_blocker="stream hold now blocks more exactly",
        recommended_next_step="freeze stream hold",
    )
    stream_hold_exactness = CacheStreamHoldDependencyExactness(
        cohort_handoff_exactness=handoff_exactness,
        status="partial",
        exactness_rung="stream_hold_dependency_exact",
        verdict="stream_hold_dependency_narrowed",
        hold_status="stream_gate_release_decoupled_from_consumer_completion_visible",
        gate_release_boundary="backend_stream_iterator_completion_before_consumer_drain",
        next_active_dependency="stream_backend_iterator_completion_dependency",
        next_active_dependency_status="stream_backend_iterator_holds_gate_until_completion",
        preserved_non_stream_handoff_status="cohort_handed_off_to_aggregated_child_exchange_visible",
        residual_blocker="backend iterator still blocks",
        recommended_next_step="freeze backend iterator seam",
    )
    backend_terminal_event_exactness = CacheStreamBackendTerminalEventExactness(
        stream_hold_exactness=stream_hold_exactness,
        status="partial",
        exactness_rung="stream_backend_terminal_event_exact",
        verdict="backend_stream_terminal_event_dependency_narrowed",
        terminal_event_status="backend_terminal_event_serial_boundary_visible",
        exchange_boundary="backend_terminal_payload_commit_before_iterator_terminal_event_delivery",
        next_active_dependency="backend_terminal_payload_commit_dependency",
        next_active_dependency_status="backend_stream_exchange_holds_serial_boundary_until_terminal_payload_commit",
        preserved_non_stream_handoff_status="cohort_handed_off_to_aggregated_child_exchange_visible",
        residual_blocker="backend terminal payload commit now blocks more exactly",
        recommended_next_step="freeze backend terminal payload commit seam",
    )
    backend_terminal_payload_commit_exactness = (
        CacheStreamBackendTerminalPayloadCommitExactness(
            backend_terminal_event_exactness=backend_terminal_event_exactness,
            status="partial",
            exactness_rung="stream_backend_terminal_payload_commit_exact",
            verdict="backend_terminal_payload_commit_dependency_narrowed",
            payload_commit_status="backend_serial_boundary_decoupled_from_terminal_payload_commit_visible",
            exchange_boundary="backend_terminal_payload_capture_before_payload_commit",
            next_active_dependency="backend_terminal_payload_capture_dependency",
            next_active_dependency_status="backend_stream_exchange_holds_serial_boundary_until_terminal_payload_capture",
            preserved_non_stream_handoff_status="cohort_handed_off_to_aggregated_child_exchange_visible",
            residual_blocker="backend terminal payload capture now blocks more exactly",
            recommended_next_step="freeze backend terminal payload capture seam",
        )
    )
    backend_terminal_payload_capture_exactness = (
        CacheStreamBackendTerminalPayloadCaptureExactness(
            backend_terminal_payload_commit_exactness=(
                backend_terminal_payload_commit_exactness
            ),
            status="partial",
            exactness_rung="stream_backend_terminal_payload_capture_exact",
            verdict="backend_terminal_payload_capture_dependency_narrowed",
            payload_capture_status="backend_serial_boundary_decoupled_from_terminal_payload_capture_visible",
            exchange_boundary="backend_terminal_record_capture_before_payload_decode",
            next_active_dependency="backend_terminal_record_capture_dependency",
            next_active_dependency_status="backend_stream_exchange_holds_serial_boundary_until_terminal_record_capture",
            preserved_non_stream_handoff_status="cohort_handed_off_to_aggregated_child_exchange_visible",
            residual_blocker="backend terminal record capture now blocks more exactly",
            recommended_next_step="freeze backend terminal record capture seam",
        )
    )
    backend_terminal_record_capture_exactness = (
        CacheStreamBackendTerminalRecordCaptureExactness(
            backend_terminal_payload_capture_exactness=(
                backend_terminal_payload_capture_exactness
            ),
            status="partial",
            exactness_rung="stream_backend_terminal_record_capture_exact",
            verdict="backend_terminal_record_capture_dependency_narrowed",
            record_capture_status="backend_serial_boundary_decoupled_from_terminal_record_capture_visible",
            exchange_boundary="backend_terminal_record_prefix_detected_before_record_capture",
            next_active_dependency="backend_terminal_record_prefix_dependency",
            next_active_dependency_status="backend_stream_exchange_holds_serial_boundary_until_terminal_record_prefix_detection",
            preserved_non_stream_handoff_status="cohort_handed_off_to_aggregated_child_exchange_visible",
            residual_blocker="backend terminal record prefix now blocks more exactly",
            recommended_next_step="freeze backend terminal record prefix seam",
        )
    )
    backend_terminal_record_prefix_exactness = (
        CacheStreamBackendTerminalRecordPrefixExactness(
            backend_terminal_record_capture_exactness=(
                backend_terminal_record_capture_exactness
            ),
            status="partial",
            exactness_rung="stream_backend_terminal_record_prefix_exact",
            verdict="backend_terminal_record_prefix_dependency_narrowed",
            prefix_status="backend_serial_boundary_decoupled_from_terminal_record_prefix_detection_visible",
            exchange_boundary="backend_terminal_action_discriminant_detected_before_full_record_prefix",
            next_active_dependency="backend_terminal_action_discriminant_dependency",
            next_active_dependency_status="backend_stream_exchange_holds_serial_boundary_until_terminal_action_discriminant_detection",
            preserved_non_stream_handoff_status="cohort_handed_off_to_aggregated_child_exchange_visible",
            residual_blocker="backend terminal action discriminant now blocks more exactly",
            recommended_next_step="freeze backend terminal action discriminant seam",
        )
    )
    backend_terminal_action_discriminant_exactness = (
        CacheStreamBackendTerminalActionDiscriminantExactness(
            backend_terminal_record_prefix_exactness=(
                backend_terminal_record_prefix_exactness
            ),
            status="partial",
            exactness_rung="stream_backend_terminal_action_discriminant_exact",
            verdict="backend_terminal_action_discriminant_dependency_narrowed",
            action_discriminant_status="backend_serial_boundary_decoupled_from_terminal_action_discriminant_detection_visible",
            exchange_boundary="backend_terminal_notice_captured_before_terminal_action_discriminant_detection",
            next_active_dependency="backend_terminal_notice_capture_dependency",
            next_active_dependency_status="backend_stream_exchange_holds_serial_boundary_until_terminal_notice_capture",
            preserved_non_stream_handoff_status="cohort_handed_off_to_aggregated_child_exchange_visible",
            residual_blocker="backend terminal notice now blocks more exactly",
            recommended_next_step="freeze backend terminal notice seam",
        )
    )
    backend_terminal_notice_capture_exactness = (
        CacheStreamBackendTerminalNoticeCaptureExactness(
            backend_terminal_action_discriminant_exactness=(
                backend_terminal_action_discriminant_exactness
            ),
            status="partial",
            exactness_rung="stream_backend_terminal_notice_capture_exact",
            verdict="backend_terminal_notice_capture_dependency_narrowed",
            notice_capture_status="backend_serial_boundary_decoupled_from_terminal_notice_capture_visible",
            exchange_boundary="backend_terminal_notice_prefix_detected_before_notice_capture",
            next_active_dependency="backend_terminal_notice_prefix_dependency",
            next_active_dependency_status="backend_stream_exchange_holds_serial_boundary_until_terminal_notice_prefix_detection",
            preserved_non_stream_handoff_status="cohort_handed_off_to_aggregated_child_exchange_visible",
            residual_blocker="backend terminal notice prefix now blocks more exactly",
            recommended_next_step="freeze backend terminal notice prefix seam",
        )
    )
    backend_terminal_notice_prefix_exactness = (
        CacheStreamBackendTerminalNoticePrefixExactness(
            backend_terminal_notice_capture_exactness=(
                backend_terminal_notice_capture_exactness
            ),
            status="partial",
            exactness_rung="stream_backend_terminal_notice_prefix_exact",
            verdict="backend_terminal_notice_prefix_dependency_narrowed",
            notice_prefix_status="backend_serial_boundary_decoupled_from_terminal_notice_prefix_detection_visible",
            exchange_boundary="backend_terminal_notice_action_discriminant_detected_before_notice_prefix",
            next_active_dependency="backend_terminal_notice_action_discriminant_dependency",
            next_active_dependency_status="backend_stream_exchange_holds_serial_boundary_until_terminal_notice_action_discriminant_detection",
            preserved_non_stream_handoff_status="cohort_handed_off_to_aggregated_child_exchange_visible",
            residual_blocker="backend terminal notice action discriminant now blocks more exactly",
            recommended_next_step="freeze backend terminal notice action discriminant seam",
        )
    )
    backend_terminal_notice_action_discriminant_exactness = (
        CacheStreamBackendTerminalNoticeActionDiscriminantExactness(
            backend_terminal_notice_prefix_exactness=(
                backend_terminal_notice_prefix_exactness
            ),
            status="partial",
            exactness_rung="stream_backend_terminal_notice_action_discriminant_exact",
            verdict="backend_terminal_notice_action_discriminant_dependency_narrowed",
            notice_action_discriminant_status="backend_serial_boundary_decoupled_from_terminal_notice_action_discriminant_detection_visible",
            exchange_boundary="backend_terminal_notice_action_stem_detected_before_notice_action_discriminant",
            next_active_dependency="backend_terminal_notice_action_stem_dependency",
            next_active_dependency_status="backend_stream_exchange_holds_serial_boundary_until_terminal_notice_action_stem_detection",
            preserved_non_stream_handoff_status="cohort_handed_off_to_aggregated_child_exchange_visible",
            residual_blocker="backend terminal notice action stem now blocks more exactly",
            recommended_next_step="freeze backend terminal notice action stem seam",
        )
    )
    backend_terminal_notice_action_stem_exactness = (
        CacheStreamBackendTerminalNoticeActionStemExactness(
            backend_terminal_notice_action_discriminant_exactness=(
                backend_terminal_notice_action_discriminant_exactness
            ),
            status="partial",
            exactness_rung="stream_backend_terminal_notice_action_stem_exact",
            verdict="backend_terminal_notice_action_stem_dependency_narrowed",
            notice_action_stem_status="backend_serial_boundary_decoupled_from_terminal_notice_action_stem_detection_visible",
            exchange_boundary="backend_terminal_notice_marker_detected_before_notice_action_stem",
            next_active_dependency="backend_terminal_notice_marker_dependency",
            next_active_dependency_status="backend_stream_exchange_holds_serial_boundary_until_terminal_notice_marker_detection",
            preserved_non_stream_handoff_status="cohort_handed_off_to_aggregated_child_exchange_visible",
            residual_blocker="backend terminal notice marker now blocks more exactly",
            recommended_next_step="freeze backend terminal notice marker seam",
        )
    )
    backend_terminal_notice_marker_exactness = (
        CacheStreamBackendTerminalNoticeMarkerExactness(
            backend_terminal_notice_action_stem_exactness=(
                backend_terminal_notice_action_stem_exactness
            ),
            status="partial",
            exactness_rung="stream_backend_terminal_notice_marker_exact",
            verdict="backend_terminal_notice_marker_dependency_narrowed",
            notice_marker_status="backend_serial_boundary_decoupled_from_terminal_notice_marker_detection_visible",
            exchange_boundary="backend_terminal_notice_marker_prefix_detected_before_notice_marker_detection",
            next_active_dependency="backend_terminal_notice_marker_prefix_dependency",
            next_active_dependency_status="backend_stream_exchange_holds_serial_boundary_until_terminal_notice_marker_prefix_detection",
            preserved_non_stream_handoff_status="cohort_handed_off_to_aggregated_child_exchange_visible",
            residual_blocker="backend terminal notice marker prefix now blocks more exactly",
            recommended_next_step="freeze backend terminal notice marker prefix seam",
        )
    )
    backend_terminal_notice_marker_prefix_exactness = (
        CacheStreamBackendTerminalNoticeMarkerPrefixExactness(
            backend_terminal_notice_marker_exactness=(
                backend_terminal_notice_marker_exactness
            ),
            status="partial",
            exactness_rung="stream_backend_terminal_notice_marker_prefix_exact",
            verdict="backend_terminal_notice_marker_prefix_dependency_narrowed",
            notice_marker_prefix_status="backend_serial_boundary_decoupled_from_terminal_notice_marker_prefix_detection_visible",
            exchange_boundary="backend_terminal_notice_marker_stem_detected_before_notice_marker_prefix_detection",
            next_active_dependency="backend_terminal_notice_marker_stem_dependency",
            next_active_dependency_status="backend_stream_exchange_holds_serial_boundary_until_terminal_notice_marker_stem_detection",
            preserved_non_stream_handoff_status="cohort_handed_off_to_aggregated_child_exchange_visible",
            residual_blocker="backend terminal notice marker stem now blocks more exactly",
            recommended_next_step="freeze backend terminal notice marker stem seam",
        )
    )
    backend_terminal_notice_marker_stem_exactness = (
        CacheStreamBackendTerminalNoticeMarkerStemExactness(
            backend_terminal_notice_marker_prefix_exactness=(
                backend_terminal_notice_marker_prefix_exactness
            ),
            status="partial",
            exactness_rung="stream_backend_terminal_notice_marker_stem_exact",
            verdict="backend_terminal_notice_marker_stem_dependency_narrowed",
            notice_marker_stem_status="backend_serial_boundary_decoupled_from_terminal_notice_marker_stem_detection_visible",
            exchange_boundary="backend_terminal_notice_marker_discriminant_detected_before_notice_marker_stem_detection",
            next_active_dependency="backend_terminal_notice_marker_discriminant_dependency",
            next_active_dependency_status="backend_stream_exchange_holds_serial_boundary_until_terminal_notice_marker_discriminant_detection",
            preserved_non_stream_handoff_status="cohort_handed_off_to_aggregated_child_exchange_visible",
            residual_blocker="backend terminal notice marker discriminant now blocks more exactly",
            recommended_next_step="freeze backend terminal notice marker discriminant seam",
        )
    )
    backend_terminal_notice_marker_discriminant_exactness = (
        CacheStreamBackendTerminalNoticeMarkerDiscriminantExactness(
            backend_terminal_notice_marker_stem_exactness=(
                backend_terminal_notice_marker_stem_exactness
            ),
            status="partial",
            exactness_rung="stream_backend_terminal_notice_marker_discriminant_exact",
            verdict="backend_terminal_notice_marker_discriminant_dependency_narrowed",
            notice_marker_discriminant_status="backend_serial_boundary_decoupled_from_terminal_notice_marker_discriminant_detection_visible",
            exchange_boundary="backend_terminal_notice_marker_key_lead_detected_before_notice_marker_discriminant_detection",
            next_active_dependency="backend_terminal_notice_marker_key_lead_dependency",
            next_active_dependency_status="backend_stream_exchange_holds_serial_boundary_until_terminal_notice_marker_key_lead_detection",
            preserved_non_stream_handoff_status="cohort_handed_off_to_aggregated_child_exchange_visible",
            residual_blocker="backend terminal notice marker key lead now blocks more exactly",
            recommended_next_step="freeze backend terminal notice marker key lead seam",
        )
    )
    backend_terminal_notice_marker_key_lead_exactness = (
        CacheStreamBackendTerminalNoticeMarkerKeyLeadExactness(
            backend_terminal_notice_marker_discriminant_exactness=(
                backend_terminal_notice_marker_discriminant_exactness
            ),
            status="partial",
            exactness_rung="stream_backend_terminal_notice_marker_key_lead_exact",
            verdict="backend_terminal_notice_marker_key_lead_dependency_still_blocked",
            notice_marker_key_lead_status="backend_stream_exchange_holds_serial_boundary_until_terminal_notice_marker_key_lead_detection_visible",
            exchange_boundary="backend_terminal_notice_marker_key_lead_is_first_unique_notice_marker_boundary_visible",
            next_active_dependency="backend_terminal_notice_marker_key_lead_dependency",
            next_active_dependency_status="backend_stream_exchange_holds_serial_boundary_until_terminal_notice_marker_key_lead_detection",
            preserved_non_stream_handoff_status="cohort_handed_off_to_aggregated_child_exchange_visible",
            residual_blocker="backend terminal notice marker key lead remains the first unique boundary",
            recommended_next_step="freeze backend terminal notice marker key lead seam honestly",
        )
    )
    backend_terminal_notice_leading_discriminator_exactness = (
        CacheStreamBackendTerminalNoticeLeadingDiscriminatorExactness(
            backend_terminal_notice_marker_key_lead_exactness=(
                backend_terminal_notice_marker_key_lead_exactness
            ),
            status="partial",
            exactness_rung="stream_backend_terminal_notice_leading_discriminator_exact",
            verdict="backend_terminal_notice_leading_discriminator_dependency_introduced",
            leading_discriminator_status="backend_stream_exchange_holds_serial_boundary_until_terminal_notice_leading_discriminator_detection_visible",
            exchange_boundary="backend_terminal_notice_leading_discriminator_detected_before_notice_marker_key_lead_detection",
            next_active_dependency="backend_terminal_notice_leading_discriminator_dependency",
            next_active_dependency_status="backend_stream_exchange_holds_serial_boundary_until_terminal_notice_leading_discriminator_detection",
            preserved_non_stream_handoff_status="cohort_handed_off_to_aggregated_child_exchange_visible",
            residual_blocker="backend terminal notice leading discriminator now blocks more exactly",
            recommended_next_step="freeze backend terminal notice leading discriminator seam",
        )
    )
    backend_terminal_notice_leading_discriminator_prefix_exactness = (
        CacheStreamBackendTerminalNoticeLeadingDiscriminatorPrefixExactness(
            backend_terminal_notice_leading_discriminator_exactness=(
                backend_terminal_notice_leading_discriminator_exactness
            ),
            status="partial",
            exactness_rung="stream_backend_terminal_notice_leading_discriminator_prefix_exact",
            verdict="backend_terminal_notice_leading_discriminator_dependency_narrowed",
            leading_discriminator_prefix_status="backend_serial_boundary_decoupled_from_terminal_notice_leading_discriminator_detection_visible",
            exchange_boundary="backend_terminal_notice_leading_discriminator_prefix_detected_before_notice_leading_discriminator_detection",
            next_active_dependency="backend_terminal_notice_leading_discriminator_prefix_dependency",
            next_active_dependency_status="backend_stream_exchange_holds_serial_boundary_until_terminal_notice_leading_discriminator_prefix_detection",
            preserved_non_stream_handoff_status="cohort_handed_off_to_aggregated_child_exchange_visible",
            residual_blocker="backend terminal notice leading discriminator prefix now blocks more exactly",
            recommended_next_step="freeze backend terminal notice leading discriminator prefix seam",
        )
    )
    backend_terminal_notice_leading_discriminator_stem_exactness = (
        CacheStreamBackendTerminalNoticeLeadingDiscriminatorStemExactness(
            backend_terminal_notice_leading_discriminator_prefix_exactness=(
                backend_terminal_notice_leading_discriminator_prefix_exactness
            ),
            status="partial",
            exactness_rung="stream_backend_terminal_notice_leading_discriminator_stem_exact",
            verdict="backend_terminal_notice_leading_discriminator_prefix_dependency_narrowed",
            leading_discriminator_stem_status="backend_serial_boundary_decoupled_from_terminal_notice_leading_discriminator_prefix_detection_visible",
            exchange_boundary="backend_terminal_notice_leading_discriminator_stem_detected_before_notice_leading_discriminator_prefix_detection",
            next_active_dependency="backend_terminal_notice_leading_discriminator_stem_dependency",
            next_active_dependency_status="backend_stream_exchange_holds_serial_boundary_until_terminal_notice_leading_discriminator_stem_detection",
            preserved_non_stream_handoff_status="cohort_handed_off_to_aggregated_child_exchange_visible",
            residual_blocker="backend terminal notice leading discriminator stem now blocks more exactly",
            recommended_next_step="freeze backend terminal notice leading discriminator stem seam",
        )
    )
    backend_terminal_notice_leading_discriminator_discriminant_exactness = (
        CacheStreamBackendTerminalNoticeLeadingDiscriminatorDiscriminantExactness(
            backend_terminal_notice_leading_discriminator_stem_exactness=(
                backend_terminal_notice_leading_discriminator_stem_exactness
            ),
            status="partial",
            exactness_rung="stream_backend_terminal_notice_leading_discriminator_discriminant_exact",
            verdict="backend_terminal_notice_leading_discriminator_stem_dependency_narrowed",
            leading_discriminator_discriminant_status="backend_serial_boundary_decoupled_from_terminal_notice_leading_discriminator_stem_detection_visible",
            exchange_boundary="backend_terminal_notice_leading_discriminator_discriminant_detected_before_notice_leading_discriminator_stem_detection",
            next_active_dependency="backend_terminal_notice_leading_discriminator_discriminant_dependency",
            next_active_dependency_status="backend_stream_exchange_holds_serial_boundary_until_terminal_notice_leading_discriminator_discriminant_detection",
            preserved_non_stream_handoff_status="cohort_handed_off_to_aggregated_child_exchange_visible",
            residual_blocker="backend terminal notice leading discriminator discriminant now blocks more exactly",
            recommended_next_step="freeze backend terminal notice leading discriminator discriminant seam",
        )
    )
    backend_terminal_notice_leading_discriminator_marker_exactness = (
        CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerExactness(
            backend_terminal_notice_leading_discriminator_discriminant_exactness=(
                backend_terminal_notice_leading_discriminator_discriminant_exactness
            ),
            status="partial",
            exactness_rung="stream_backend_terminal_notice_leading_discriminator_marker_exact",
            verdict="backend_terminal_notice_leading_discriminator_discriminant_dependency_narrowed",
            leading_discriminator_marker_status="backend_serial_boundary_decoupled_from_terminal_notice_leading_discriminator_discriminant_detection_visible",
            exchange_boundary="backend_terminal_notice_leading_discriminator_marker_detected_before_notice_leading_discriminator_discriminant_detection",
            next_active_dependency="backend_terminal_notice_leading_discriminator_marker_dependency",
            next_active_dependency_status="backend_stream_exchange_holds_serial_boundary_until_terminal_notice_leading_discriminator_marker_detection",
            preserved_non_stream_handoff_status="cohort_handed_off_to_aggregated_child_exchange_visible",
            residual_blocker="backend terminal notice leading discriminator marker now blocks more exactly",
            recommended_next_step="freeze backend terminal notice leading discriminator marker seam",
        )
    )
    backend_terminal_notice_leading_discriminator_marker_prefix_exactness = (
        CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerPrefixExactness(
            backend_terminal_notice_leading_discriminator_marker_exactness=(
                backend_terminal_notice_leading_discriminator_marker_exactness
            ),
            status="partial",
            exactness_rung="stream_backend_terminal_notice_leading_discriminator_marker_prefix_exact",
            verdict="backend_terminal_notice_leading_discriminator_marker_dependency_narrowed",
            leading_discriminator_marker_prefix_status="backend_serial_boundary_decoupled_from_terminal_notice_leading_discriminator_marker_detection_visible",
            exchange_boundary="backend_terminal_notice_leading_discriminator_marker_prefix_detected_before_notice_leading_discriminator_marker_detection",
            next_active_dependency="backend_terminal_notice_leading_discriminator_marker_prefix_dependency",
            next_active_dependency_status="backend_stream_exchange_holds_serial_boundary_until_terminal_notice_leading_discriminator_marker_prefix_detection",
            preserved_non_stream_handoff_status="cohort_handed_off_to_aggregated_child_exchange_visible",
            residual_blocker="backend terminal notice leading discriminator marker prefix now blocks more exactly",
            recommended_next_step="freeze backend terminal notice leading discriminator marker stem seam",
        )
    )
    backend_terminal_notice_leading_discriminator_marker_stem_exactness = (
        CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerStemExactness(
            backend_terminal_notice_leading_discriminator_marker_prefix_exactness=(
                backend_terminal_notice_leading_discriminator_marker_prefix_exactness
            ),
            status="partial",
            exactness_rung="stream_backend_terminal_notice_leading_discriminator_marker_stem_exact",
            verdict="backend_terminal_notice_leading_discriminator_marker_prefix_dependency_narrowed",
            leading_discriminator_marker_stem_status="backend_serial_boundary_decoupled_from_terminal_notice_leading_discriminator_marker_prefix_detection_visible",
            exchange_boundary="backend_terminal_notice_leading_discriminator_marker_stem_detected_before_notice_leading_discriminator_marker_prefix_detection",
            next_active_dependency="backend_terminal_notice_leading_discriminator_marker_stem_dependency",
            next_active_dependency_status="backend_stream_exchange_holds_serial_boundary_until_terminal_notice_leading_discriminator_marker_stem_detection",
            preserved_non_stream_handoff_status="cohort_handed_off_to_aggregated_child_exchange_visible",
            residual_blocker="backend terminal notice leading discriminator marker stem now blocks more exactly",
            recommended_next_step="freeze backend terminal notice leading discriminator marker discriminant seam",
        )
    )
    backend_terminal_notice_leading_discriminator_marker_discriminant_exactness = (
        CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerDiscriminantExactness(
            backend_terminal_notice_leading_discriminator_marker_stem_exactness=(
                backend_terminal_notice_leading_discriminator_marker_stem_exactness
            ),
            status="partial",
            exactness_rung="stream_backend_terminal_notice_leading_discriminator_marker_discriminant_exact",
            verdict="backend_terminal_notice_leading_discriminator_marker_stem_dependency_narrowed",
            leading_discriminator_marker_discriminant_status="backend_serial_boundary_decoupled_from_terminal_notice_leading_discriminator_marker_stem_detection_visible",
            exchange_boundary="backend_terminal_notice_leading_discriminator_marker_discriminant_detected_before_notice_leading_discriminator_marker_stem_detection",
            next_active_dependency="backend_terminal_notice_leading_discriminator_marker_discriminant_dependency",
            next_active_dependency_status="backend_stream_exchange_holds_serial_boundary_until_terminal_notice_leading_discriminator_marker_discriminant_detection",
            preserved_non_stream_handoff_status="cohort_handed_off_to_aggregated_child_exchange_visible",
            residual_blocker="backend terminal notice leading discriminator marker discriminant now blocks more exactly",
            recommended_next_step="freeze backend terminal notice leading discriminator marker first unique boundary seam",
        )
    )
    backend_terminal_notice_leading_discriminator_marker_first_unique_boundary_exactness = (
        CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerFirstUniqueBoundaryExactness(
            backend_terminal_notice_leading_discriminator_marker_discriminant_exactness=(
                backend_terminal_notice_leading_discriminator_marker_discriminant_exactness
            ),
            status="partial",
            exactness_rung="stream_backend_terminal_notice_leading_discriminator_marker_first_unique_boundary_exact",
            verdict="backend_terminal_notice_leading_discriminator_marker_discriminant_dependency_still_blocked",
            leading_discriminator_marker_first_unique_boundary_status="backend_stream_exchange_holds_serial_boundary_until_terminal_notice_leading_discriminator_marker_discriminant_detection_visible",
            exchange_boundary="backend_terminal_notice_leading_discriminator_marker_discriminant_is_first_unique_boundary_visible",
            next_active_dependency="backend_terminal_notice_leading_discriminator_marker_discriminant_dependency",
            next_active_dependency_status="backend_stream_exchange_holds_serial_boundary_until_terminal_notice_leading_discriminator_marker_discriminant_detection",
            preserved_non_stream_handoff_status="cohort_handed_off_to_aggregated_child_exchange_visible",
            residual_blocker="backend terminal notice leading discriminator marker discriminant remains the first honest unique boundary",
            recommended_next_step="freeze backend terminal notice leading discriminator marker discriminant seam honestly",
        )
    )
    backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_exactness = (
        CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedDiscriminatorExactness(
            backend_terminal_notice_leading_discriminator_marker_first_unique_boundary_exactness=(
                backend_terminal_notice_leading_discriminator_marker_first_unique_boundary_exactness
            ),
            status="partial",
            exactness_rung="stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_exact",
            verdict="backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_introduced",
            earlier_runtime_owned_discriminator_status="backend_stream_exchange_holds_serial_boundary_until_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_detection_visible",
            exchange_boundary="backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_detected_before_notice_leading_discriminator_marker_discriminant_detection",
            next_active_dependency="backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_dependency",
            next_active_dependency_status="backend_stream_exchange_holds_serial_boundary_until_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_detection",
            preserved_non_stream_handoff_status="cohort_handed_off_to_aggregated_child_exchange_visible",
            residual_blocker="owlmlx now owns a new earlier runtime-owned terminal-notice discriminator record ahead of the current marker-discriminant seam",
            recommended_next_step="freeze backend terminal notice leading discriminator marker earlier runtime-owned discriminator seam",
        )
    )
    backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_prefix_exactness = (
        CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedDiscriminatorPrefixExactness(
            backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_exactness=(
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_exactness
            ),
            status="partial",
            exactness_rung="stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_prefix_exact",
            verdict="backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_dependency_narrowed",
            earlier_runtime_owned_discriminator_prefix_status="backend_serial_boundary_decoupled_from_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_detection_visible",
            exchange_boundary="backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_prefix_detected_before_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_detection",
            next_active_dependency="backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_prefix_dependency",
            next_active_dependency_status="backend_stream_exchange_holds_serial_boundary_until_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_prefix_detection",
            preserved_non_stream_handoff_status="cohort_handed_off_to_aggregated_child_exchange_visible",
            residual_blocker="the remaining exact stream seam is now closer than full earlier-runtime-owned-discriminator detection",
            recommended_next_step="freeze backend terminal notice leading discriminator marker earlier runtime-owned discriminator prefix seam",
        )
    )
    backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_stem_exactness = (
        CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedDiscriminatorStemExactness(
            backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_prefix_exactness=(
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_prefix_exactness
            ),
            status="partial",
            exactness_rung="stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_stem_exact",
            verdict="backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_prefix_dependency_narrowed",
            earlier_runtime_owned_discriminator_stem_status="backend_serial_boundary_decoupled_from_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_prefix_detection_visible",
            exchange_boundary="backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_stem_detected_before_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_prefix_detection",
            next_active_dependency="backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_stem_dependency",
            next_active_dependency_status="backend_stream_exchange_holds_serial_boundary_until_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_stem_detection",
            preserved_non_stream_handoff_status="cohort_handed_off_to_aggregated_child_exchange_visible",
            residual_blocker="the remaining exact stream seam is now closer than earlier-runtime-owned-discriminator prefix detection",
            recommended_next_step="freeze backend terminal notice leading discriminator marker earlier runtime-owned discriminator stem seam",
        )
    )
    backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_discriminant_exactness = (
        CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedDiscriminatorDiscriminantExactness(
            backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_stem_exactness=(
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_stem_exactness
            ),
            status="partial",
            exactness_rung="stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_discriminant_exact",
            verdict="backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_stem_dependency_narrowed",
            earlier_runtime_owned_discriminator_discriminant_status="backend_serial_boundary_decoupled_from_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_stem_detection_visible",
            exchange_boundary="backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_discriminant_detected_before_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_stem_detection",
            next_active_dependency="backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_discriminant_dependency",
            next_active_dependency_status="backend_stream_exchange_holds_serial_boundary_until_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_discriminant_detection",
            preserved_non_stream_handoff_status="cohort_handed_off_to_aggregated_child_exchange_visible",
            residual_blocker="the remaining exact stream seam is now closer than earlier-runtime-owned-discriminator stem detection",
            recommended_next_step="freeze backend terminal notice leading discriminator marker earlier runtime-owned discriminator first-unique-boundary seam",
        )
    )
    backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_first_unique_boundary_exactness = (
        CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedDiscriminatorFirstUniqueBoundaryExactness(
            backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_discriminant_exactness=(
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_discriminant_exactness
            ),
            status="partial",
            exactness_rung="stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_first_unique_boundary_exact",
            verdict="backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_discriminant_dependency_still_blocked",
            earlier_runtime_owned_discriminator_first_unique_boundary_status="backend_stream_exchange_holds_serial_boundary_until_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_discriminant_detection_visible",
            exchange_boundary="backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_discriminant_is_first_honest_unique_boundary_visible",
            next_active_dependency="backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_discriminant_dependency",
            next_active_dependency_status="backend_stream_exchange_holds_serial_boundary_until_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_discriminant_detection",
            preserved_non_stream_handoff_status="cohort_handed_off_to_aggregated_child_exchange_visible",
            residual_blocker="backend terminal notice leading discriminator marker earlier runtime-owned discriminator discriminant is already the first honest unique boundary on the newer runtime-owned record",
            recommended_next_step="introduce one new earlier runtime-owned boundary ahead of this first honest unique boundary",
        )
    )
    backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_exactness = (
        CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedLeadingDiscriminatorExactness(
            backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_first_unique_boundary_exactness=(
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_first_unique_boundary_exactness
            ),
            status="partial",
            exactness_rung="stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_exact",
            verdict="backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_introduced",
            earlier_runtime_owned_leading_discriminator_status="backend_stream_exchange_holds_serial_boundary_until_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_detection_visible",
            exchange_boundary="backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_detected_before_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_discriminant_detection",
            next_active_dependency="backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_dependency",
            next_active_dependency_status="backend_stream_exchange_holds_serial_boundary_until_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_detection",
            preserved_non_stream_handoff_status="cohort_handed_off_to_aggregated_child_exchange_visible",
            residual_blocker="one new earlier runtime-owned leading discriminator record now blocks more exactly",
            recommended_next_step="freeze backend terminal notice leading discriminator marker earlier runtime-owned leading discriminator seam",
        )
    )
    backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_prefix_exactness = (
        CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedLeadingDiscriminatorPrefixExactness(
            backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_exactness=(
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_exactness
            ),
            status="partial",
            exactness_rung="stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_prefix_exact",
            verdict="backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_dependency_narrowed",
            earlier_runtime_owned_leading_discriminator_prefix_status="backend_serial_boundary_decoupled_from_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_detection_visible",
            exchange_boundary="backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_prefix_detected_before_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_detection",
            next_active_dependency="backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_prefix_dependency",
            next_active_dependency_status="backend_stream_exchange_holds_serial_boundary_until_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_prefix_detection",
            preserved_non_stream_handoff_status="cohort_handed_off_to_aggregated_child_exchange_visible",
            residual_blocker="earlier runtime-owned leading discriminator prefix now blocks more exactly",
            recommended_next_step="freeze backend terminal notice leading discriminator marker earlier runtime-owned leading discriminator stem seam",
        )
    )
    backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_stem_exactness = (
        CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedLeadingDiscriminatorStemExactness(
            backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_prefix_exactness=(
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_prefix_exactness
            ),
            status="partial",
            exactness_rung="stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_stem_exact",
            verdict="backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_prefix_dependency_narrowed",
            earlier_runtime_owned_leading_discriminator_stem_status="backend_serial_boundary_decoupled_from_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_prefix_detection_visible",
            exchange_boundary="backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_stem_detected_before_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_prefix_detection",
            next_active_dependency="backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_stem_dependency",
            next_active_dependency_status="backend_stream_exchange_holds_serial_boundary_until_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_stem_detection",
            preserved_non_stream_handoff_status="cohort_handed_off_to_aggregated_child_exchange_visible",
            residual_blocker="earlier runtime-owned leading discriminator stem now blocks more exactly",
            recommended_next_step="freeze backend terminal notice leading discriminator marker earlier runtime-owned leading discriminator discriminant seam",
        )
    )
    backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_discriminant_exactness = (
        CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedLeadingDiscriminatorDiscriminantExactness(
            backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_stem_exactness=(
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_stem_exactness
            ),
            status="partial",
            exactness_rung="stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_discriminant_exact",
            verdict="backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_stem_dependency_narrowed",
            earlier_runtime_owned_leading_discriminator_discriminant_status="backend_serial_boundary_decoupled_from_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_stem_detection_visible",
            exchange_boundary="backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_discriminant_detected_before_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_stem_detection",
            next_active_dependency="backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_discriminant_dependency",
            next_active_dependency_status="backend_stream_exchange_holds_serial_boundary_until_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_discriminant_detection",
            preserved_non_stream_handoff_status="cohort_handed_off_to_aggregated_child_exchange_visible",
            residual_blocker="earlier runtime-owned leading discriminator discriminant now blocks more exactly",
            recommended_next_step="freeze backend terminal notice leading discriminator marker earlier runtime-owned leading discriminator first-unique-boundary seam",
        )
    )
    backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_first_unique_boundary_exactness = (
        CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedLeadingDiscriminatorFirstUniqueBoundaryExactness(
            backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_discriminant_exactness=(
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_discriminant_exactness
            ),
            status="partial",
            exactness_rung="stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_first_unique_boundary_exact",
            verdict="backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_discriminant_dependency_still_blocked",
            earlier_runtime_owned_leading_discriminator_first_unique_boundary_status="backend_stream_exchange_holds_serial_boundary_until_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_discriminant_detection_visible",
            exchange_boundary="backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_discriminant_is_first_honest_unique_boundary_visible",
            next_active_dependency="backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_discriminant_dependency",
            next_active_dependency_status="backend_stream_exchange_holds_serial_boundary_until_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_discriminant_detection",
            preserved_non_stream_handoff_status="cohort_handed_off_to_aggregated_child_exchange_visible",
            residual_blocker="backend terminal notice leading discriminator marker earlier runtime-owned leading discriminator discriminant is already the first honest unique boundary on the newer runtime-owned leading discriminator record",
            recommended_next_step="introduce one new earlier runtime-owned boundary ahead of this first honest unique boundary",
        )
    )
    backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_exactness = (
        CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedBoundaryExactness(
            backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_first_unique_boundary_exactness=(
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_first_unique_boundary_exactness
            ),
            status="partial",
            exactness_rung="stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_exact",
            verdict="backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_introduced",
            earlier_runtime_owned_boundary_status="backend_stream_exchange_holds_serial_boundary_until_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_detection_visible",
            exchange_boundary="backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_detected_before_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_discriminant_detection",
            next_active_dependency="backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_dependency",
            next_active_dependency_status="backend_stream_exchange_holds_serial_boundary_until_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_detection",
            preserved_non_stream_handoff_status="cohort_handed_off_to_aggregated_child_exchange_visible",
            residual_blocker="owlmlx now owns one new earlier runtime-owned boundary record ahead of the newer runtime-owned leading-discriminator record on this path",
            recommended_next_step="treat backend terminal notice leading discriminator marker earlier runtime-owned boundary detection as the current exact stream dependency",
        )
    )
    backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_prefix_exactness = (
        CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedBoundaryPrefixExactness(
            backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_exactness=(
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_exactness
            ),
            status="partial",
            exactness_rung="stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_prefix_exact",
            verdict="backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_dependency_narrowed",
            earlier_runtime_owned_boundary_prefix_status="backend_serial_boundary_decoupled_from_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_detection_visible",
            exchange_boundary="backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_prefix_detected_before_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_detection",
            next_active_dependency="backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_prefix_dependency",
            next_active_dependency_status="backend_stream_exchange_holds_serial_boundary_until_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_prefix_detection",
            preserved_non_stream_handoff_status="cohort_handed_off_to_aggregated_child_exchange_visible",
            residual_blocker="the remaining exact stream seam is now closer than full earlier-runtime-owned-boundary detection on this path",
            recommended_next_step="treat backend terminal notice leading discriminator marker earlier runtime-owned boundary prefix detection as the current exact stream dependency",
        )
    )
    backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_stem_exactness = (
        CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedBoundaryStemExactness(
            backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_prefix_exactness=(
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_prefix_exactness
            ),
            status="partial",
            exactness_rung="stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_stem_exact",
            verdict="backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_prefix_dependency_narrowed",
            earlier_runtime_owned_boundary_stem_status="backend_serial_boundary_decoupled_from_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_prefix_detection_visible",
            exchange_boundary="backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_stem_detected_before_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_prefix_detection",
            next_active_dependency="backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_stem_dependency",
            next_active_dependency_status="backend_stream_exchange_holds_serial_boundary_until_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_stem_detection",
            preserved_non_stream_handoff_status="cohort_handed_off_to_aggregated_child_exchange_visible",
            residual_blocker="the remaining exact stream seam is now closer than earlier-runtime-owned-boundary prefix detection on this path",
            recommended_next_step="treat backend terminal notice leading discriminator marker earlier runtime-owned boundary stem detection as the current exact stream dependency",
        )
    )
    backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_first_unique_boundary_exactness = (
        CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedBoundaryFirstUniqueBoundaryExactness(
            backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_stem_exactness=(
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_stem_exactness
            ),
            status="partial",
            exactness_rung="stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_first_unique_boundary_exact",
            verdict="backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_stem_dependency_still_blocked",
            earlier_runtime_owned_boundary_first_unique_boundary_status="backend_stream_exchange_holds_serial_boundary_until_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_stem_detection_visible",
            exchange_boundary="backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_stem_is_first_honest_unique_boundary_visible",
            next_active_dependency="backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_stem_dependency",
            next_active_dependency_status="backend_stream_exchange_holds_serial_boundary_until_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_stem_detection",
            preserved_non_stream_handoff_status="cohort_handed_off_to_aggregated_child_exchange_visible",
            residual_blocker="the remaining exact stream seam stays at earlier-runtime-owned-boundary stem detection on this path: the literal prefix before runtime_owned_terminal_b is not yet an honest runtime-owned transport boundary, so earlier-runtime-owned-boundary stem detection is already the first honest unique boundary on the newer runtime-owned boundary record and no earlier live seam is yet available",
            recommended_next_step="either keep backend-terminal notice leading-discriminator marker earlier-runtime-owned-boundary stem detection frozen as the current exact seam or introduce one new earlier runtime-owned boundary ahead of this first honest unique boundary without widening the claim into stream interleaving, continuous batching, or cache parity",
        )
    )
    backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_exactness = (
        CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedBoundaryEarlierBoundaryExactness(
            backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_first_unique_boundary_exactness=(
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_first_unique_boundary_exactness
            ),
            status="partial",
            exactness_rung="stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_exact",
            verdict="backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_introduced",
            earlier_runtime_owned_boundary_earlier_boundary_status="backend_stream_exchange_holds_serial_boundary_until_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_detection_visible",
            exchange_boundary="backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_detected_before_boundary_stem_detection",
            next_active_dependency="backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_dependency",
            next_active_dependency_status="backend_stream_exchange_holds_serial_boundary_until_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_detection",
            preserved_non_stream_handoff_status="cohort_handed_off_to_aggregated_child_exchange_visible",
            residual_blocker="owlmlx now owns one distinct earlier runtime-owned boundary record ahead of the current earlier-runtime-owned-boundary stem seam: a second backend stream request can be written once child stdout reaches runtime_owned_terminal_earlier_boundary and before child stdout reaches runtime_owned_terminal_b, so the remaining exact stream seam now sits at earlier-runtime-owned-boundary earlier-boundary detection",
            recommended_next_step="treat backend terminal notice leading discriminator marker earlier runtime-owned boundary earlier-boundary detection as the current exact stream dependency",
        )
    )

    payload = cache_request_aggregation_active_seam_to_dict(
        build_cache_request_aggregation_active_seam(
            request_aggregation_window_reentry=reentry,
            request_aggregation_window_exactness=exactness,
            child_exchange_exactness=child_exactness,
            cohort_handoff_exactness=handoff_exactness,
            stream_hold_exactness=stream_hold_exactness,
            stream_backend_terminal_event_exactness=backend_terminal_event_exactness,
            stream_backend_terminal_payload_commit_exactness=(
                backend_terminal_payload_commit_exactness
            ),
            stream_backend_terminal_payload_capture_exactness=(
                backend_terminal_payload_capture_exactness
            ),
            stream_backend_terminal_record_capture_exactness=(
                backend_terminal_record_capture_exactness
            ),
            stream_backend_terminal_record_prefix_exactness=(
                backend_terminal_record_prefix_exactness
            ),
            stream_backend_terminal_action_discriminant_exactness=(
                backend_terminal_action_discriminant_exactness
            ),
            stream_backend_terminal_notice_capture_exactness=(
                backend_terminal_notice_capture_exactness
            ),
            stream_backend_terminal_notice_prefix_exactness=(
                backend_terminal_notice_prefix_exactness
            ),
            stream_backend_terminal_notice_action_discriminant_exactness=(
                backend_terminal_notice_action_discriminant_exactness
            ),
            stream_backend_terminal_notice_action_stem_exactness=(
                backend_terminal_notice_action_stem_exactness
            ),
            stream_backend_terminal_notice_marker_exactness=(
                backend_terminal_notice_marker_exactness
            ),
            stream_backend_terminal_notice_marker_prefix_exactness=(
                backend_terminal_notice_marker_prefix_exactness
            ),
            stream_backend_terminal_notice_marker_stem_exactness=(
                backend_terminal_notice_marker_stem_exactness
            ),
            stream_backend_terminal_notice_marker_discriminant_exactness=(
                backend_terminal_notice_marker_discriminant_exactness
            ),
            stream_backend_terminal_notice_marker_key_lead_exactness=(
                backend_terminal_notice_marker_key_lead_exactness
            ),
            stream_backend_terminal_notice_leading_discriminator_exactness=(
                backend_terminal_notice_leading_discriminator_exactness
            ),
            stream_backend_terminal_notice_leading_discriminator_prefix_exactness=(
                backend_terminal_notice_leading_discriminator_prefix_exactness
            ),
            stream_backend_terminal_notice_leading_discriminator_stem_exactness=(
                backend_terminal_notice_leading_discriminator_stem_exactness
            ),
            stream_backend_terminal_notice_leading_discriminator_discriminant_exactness=(
                backend_terminal_notice_leading_discriminator_discriminant_exactness
            ),
            stream_backend_terminal_notice_leading_discriminator_marker_exactness=(
                backend_terminal_notice_leading_discriminator_marker_exactness
            ),
            stream_backend_terminal_notice_leading_discriminator_marker_prefix_exactness=(
                backend_terminal_notice_leading_discriminator_marker_prefix_exactness
            ),
            stream_backend_terminal_notice_leading_discriminator_marker_discriminant_exactness=(
                backend_terminal_notice_leading_discriminator_marker_discriminant_exactness
            ),
            stream_backend_terminal_notice_leading_discriminator_marker_first_unique_boundary_exactness=(
                backend_terminal_notice_leading_discriminator_marker_first_unique_boundary_exactness
            ),
            stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_exactness=(
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_exactness
            ),
            stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_prefix_exactness=(
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_prefix_exactness
            ),
            stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_stem_exactness=(
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_stem_exactness
            ),
            stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_discriminant_exactness=(
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_discriminant_exactness
            ),
            stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_first_unique_boundary_exactness=(
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_first_unique_boundary_exactness
            ),
            stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_exactness=(
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_exactness
            ),
            stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_prefix_exactness=(
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_prefix_exactness
            ),
            stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_stem_exactness=(
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_stem_exactness
            ),
            stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_discriminant_exactness=(
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_discriminant_exactness
            ),
            stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_first_unique_boundary_exactness=(
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_first_unique_boundary_exactness
            ),
            stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_exactness=(
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_exactness
            ),
            stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_prefix_exactness=(
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_prefix_exactness
            ),
            stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_stem_exactness=(
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_stem_exactness
            ),
            stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_first_unique_boundary_exactness=(
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_first_unique_boundary_exactness
            ),
            stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_exactness=(
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_exactness
            ),
            stream_backend_terminal_notice_leading_discriminator_marker_stem_exactness=(
                backend_terminal_notice_leading_discriminator_marker_stem_exactness
            ),
        )
    )

    assert payload["summary"]["seam_rung"] == "aggregation_active_seam_exact"
    assert (
        payload["selected_seam"]["seam"]
        == "backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_dependency"
    )
    assert (
        payload["selected_seam"]["status"]
        == "backend_stream_exchange_holds_serial_boundary_until_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_detection"
    )
    assert "distinct earlier runtime-owned boundary" in payload["summary"]["residual_blocker"]
    assert "runtime_owned_terminal_earlier_boundary" in payload["summary"]["residual_blocker"]
    assert "runtime_owned_terminal_b" in payload["summary"]["residual_blocker"]
    assert payload["preserved_secondary_dependencies"] == []


def test_cache_request_aggregation_active_seam_advances_after_earlier_earlier_boundary_introduction() -> None:
    reentry = CacheRequestAggregationWindowReentry(
        continuous_batching_branch_reduction=object(),
        request_aggregation_window_exactness=object(),
        status="partial",
        reentry_rung="aggregation_reentry_exact",
        selected_reentry_target="request_aggregation_window",
        selected_reentry_target_status="reentered_as_active_cache_subchain",
        preserved_secondary_scheduler_reduction=(
            "shared_prefill_batch_step",
            "interleaved_decode_scheduler",
        ),
        preserved_secondary_runtime_branch="turboquant_preconditions",
        preserved_secondary_runtime_branch_status="preconditions_exact",
        residual_blocker="request aggregation reentered",
        recommended_next_step="active seam",
    )
    exactness = CacheRequestAggregationWindowExactness(
        mechanism_subgap=object(),
        status="partial",
        exactness_rung="aggregation_window_blocker_exact",
        ingress_window_status="bounded_pre_gate_admission_window_present",
        admission_boundary_status="cohort_forms_before_generation_gate_claim",
        child_dependency_status="cohort_handed_off_to_aggregated_child_exchange_visible",
        stream_dependency_status="stream_session_holds_gate_until_completion",
        residual_blocker="stream hold still blocks",
        recommended_next_step="freeze stream hold",
    )
    child_exactness = CacheChildExchangeAggregatedDispatchExactness(
        request_aggregation_window_exactness=exactness,
        status="partial",
        exactness_rung="child_exchange_dependency_exact",
        child_exchange_status="aggregated_non_stream_child_exchange_visible",
        exchange_shape="single_child_exchange_carries_multiple_non_stream_requests",
        next_active_dependency="cohort_to_child_exchange_handoff_dependency",
        next_active_dependency_status="pre_gate_cohort_not_yet_handed_off_to_aggregated_child_exchange",
        preserved_stream_dependency_status="stream_session_holds_gate_until_completion",
        residual_blocker="cohort handoff still missing",
        recommended_next_step="freeze cohort handoff",
    )
    handoff_exactness = CacheCohortToChildExchangeHandoffExactness(
        child_exchange_exactness=child_exactness,
        status="partial",
        exactness_rung="cohort_to_child_handoff_exact",
        handoff_status="cohort_handed_off_to_aggregated_child_exchange_visible",
        main_path_shape="bounded_pre_gate_cohort_reaches_single_aggregated_non_stream_child_exchange",
        next_active_dependency="stream_session_holds_gate_until_completion",
        next_active_dependency_status="stream_session_holds_gate_until_completion",
        preserved_stream_dependency_status="stream_session_holds_gate_until_completion",
        residual_blocker="stream hold still blocks",
        recommended_next_step="freeze stream hold",
    )
    stream_hold_exactness = CacheStreamHoldDependencyExactness(
        cohort_handoff_exactness=handoff_exactness,
        status="partial",
        exactness_rung="stream_hold_dependency_exact",
        verdict="stream_hold_dependency_narrowed",
        hold_status="stream_gate_release_decoupled_from_consumer_completion_visible",
        gate_release_boundary="backend_stream_iterator_completion_before_consumer_drain",
        next_active_dependency="stream_backend_iterator_completion_dependency",
        next_active_dependency_status="stream_backend_iterator_holds_gate_until_completion",
        preserved_non_stream_handoff_status="cohort_handed_off_to_aggregated_child_exchange_visible",
        residual_blocker="stream gate release no longer waits for session completion",
        recommended_next_step="freeze backend iterator completion",
    )
    earlier_earlier_exactness = (
        CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedBoundaryEarlierEarlierBoundaryExactness(
            backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_first_unique_boundary_exactness=object(),  # type: ignore[arg-type]
            status="partial",
            exactness_rung="stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_earlier_boundary_exact",
            verdict="backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_earlier_boundary_introduced",
            earlier_runtime_owned_boundary_earlier_earlier_boundary_status="backend_stream_exchange_holds_serial_boundary_until_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_earlier_boundary_detection_visible",
            exchange_boundary="backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_earlier_boundary_detected_before_earlier_boundary_detection",
            next_active_dependency="backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_earlier_boundary_dependency",
            next_active_dependency_status="backend_stream_exchange_holds_serial_boundary_until_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_earlier_boundary_detection",
            preserved_non_stream_handoff_status="cohort_handed_off_to_aggregated_child_exchange_visible",
            residual_blocker="owlmlx now owns one distinct earlier-earlier runtime-owned boundary record ahead of the current earlier-runtime-owned-boundary earlier-boundary seam",
            recommended_next_step="treat earlier-earlier boundary detection as the current exact stream dependency",
        )
    )

    payload = cache_request_aggregation_active_seam_to_dict(
        build_cache_request_aggregation_active_seam(
            request_aggregation_window_reentry=reentry,
            request_aggregation_window_exactness=exactness,
            child_exchange_exactness=child_exactness,
            cohort_handoff_exactness=handoff_exactness,
            stream_hold_exactness=stream_hold_exactness,
            stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_earlier_boundary_exactness=(
                earlier_earlier_exactness
            ),
        )
    )

    assert (
        payload["selected_seam"]["seam"]
        == "backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_earlier_boundary_dependency"
    )
    assert (
        payload["selected_seam"]["status"]
        == "backend_stream_exchange_holds_serial_boundary_until_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_earlier_boundary_detection"
    )
    assert "earlier-earlier runtime-owned boundary" in payload["summary"]["residual_blocker"]


def test_cache_request_aggregation_active_seam_module_has_no_platform_dependency() -> None:
    source = Path(__file__).parents[1].joinpath(
        "owlmlx", "cache_request_aggregation_active_seam.py"
    ).read_text()
    for pattern in ["llm_router", "ops_dashboard", "local-llm-desktop", "AI/Agent"]:
        assert pattern not in source
