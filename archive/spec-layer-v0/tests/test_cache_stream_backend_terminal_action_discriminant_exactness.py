from __future__ import annotations

from pathlib import Path

from owlmlx.cache_stream_backend_terminal_action_discriminant_exactness import (
    build_cache_stream_backend_terminal_action_discriminant_exactness,
    cache_stream_backend_terminal_action_discriminant_exactness_to_dict,
)
from owlmlx.cache_stream_backend_terminal_action_discriminant_harness import (
    CacheStreamBackendTerminalActionDiscriminantHarnessResult,
)
from owlmlx.cache_stream_backend_terminal_event_exactness import (
    CacheStreamBackendTerminalEventExactness,
)
from owlmlx.cache_stream_backend_terminal_payload_capture_exactness import (
    CacheStreamBackendTerminalPayloadCaptureExactness,
)
from owlmlx.cache_stream_backend_terminal_payload_commit_exactness import (
    CacheStreamBackendTerminalPayloadCommitExactness,
)
from owlmlx.cache_stream_backend_terminal_record_capture_exactness import (
    CacheStreamBackendTerminalRecordCaptureExactness,
)
from owlmlx.cache_stream_backend_terminal_record_prefix_exactness import (
    CacheStreamBackendTerminalRecordPrefixExactness,
)
from owlmlx.cache_stream_hold_dependency_exactness import (
    CacheStreamHoldDependencyExactness,
)


def test_cache_stream_backend_terminal_action_discriminant_exactness_defaults_unresolved() -> None:
    payload = cache_stream_backend_terminal_action_discriminant_exactness_to_dict(
        build_cache_stream_backend_terminal_action_discriminant_exactness()
    )

    assert (
        payload["contract"]["surface"]
        == "owlmlx.cache_stream_backend_terminal_action_discriminant_exactness"
    )
    assert (
        payload["summary"]["exactness_rung"]
        == "stream_backend_terminal_action_discriminant_unresolved"
    )


def test_cache_stream_backend_terminal_action_discriminant_exactness_narrows_to_terminal_notice_capture_dependency() -> None:
    stream_hold = CacheStreamHoldDependencyExactness(
        cohort_handoff_exactness=object(),  # type: ignore[arg-type]
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
    terminal_event_exactness = CacheStreamBackendTerminalEventExactness(
        stream_hold_exactness=stream_hold,
        status="partial",
        exactness_rung="stream_backend_terminal_event_exact",
        verdict="backend_stream_terminal_event_dependency_narrowed",
        terminal_event_status="backend_terminal_event_serial_boundary_visible",
        exchange_boundary="backend_terminal_payload_commit_before_iterator_terminal_event_delivery",
        next_active_dependency="backend_terminal_payload_commit_dependency",
        next_active_dependency_status="backend_stream_exchange_holds_serial_boundary_until_terminal_payload_commit",
        preserved_non_stream_handoff_status="cohort_handed_off_to_aggregated_child_exchange_visible",
        residual_blocker="payload commit now blocks more exactly",
        recommended_next_step="freeze terminal payload commit seam",
    )
    payload_commit_exactness = CacheStreamBackendTerminalPayloadCommitExactness(
        backend_terminal_event_exactness=terminal_event_exactness,
        status="partial",
        exactness_rung="stream_backend_terminal_payload_commit_exact",
        verdict="backend_terminal_payload_commit_dependency_narrowed",
        payload_commit_status="backend_serial_boundary_decoupled_from_terminal_payload_commit_visible",
        exchange_boundary="backend_terminal_payload_capture_before_payload_commit",
        next_active_dependency="backend_terminal_payload_capture_dependency",
        next_active_dependency_status="backend_stream_exchange_holds_serial_boundary_until_terminal_payload_capture",
        preserved_non_stream_handoff_status="cohort_handed_off_to_aggregated_child_exchange_visible",
        residual_blocker="payload capture now blocks more exactly",
        recommended_next_step="freeze terminal payload capture seam",
    )
    payload_capture_exactness = CacheStreamBackendTerminalPayloadCaptureExactness(
        backend_terminal_payload_commit_exactness=payload_commit_exactness,
        status="partial",
        exactness_rung="stream_backend_terminal_payload_capture_exact",
        verdict="backend_terminal_payload_capture_dependency_narrowed",
        payload_capture_status="backend_serial_boundary_decoupled_from_terminal_payload_capture_visible",
        exchange_boundary="backend_terminal_record_capture_before_payload_decode",
        next_active_dependency="backend_terminal_record_capture_dependency",
        next_active_dependency_status="backend_stream_exchange_holds_serial_boundary_until_terminal_record_capture",
        preserved_non_stream_handoff_status="cohort_handed_off_to_aggregated_child_exchange_visible",
        residual_blocker="record capture now blocks more exactly",
        recommended_next_step="freeze terminal record capture seam",
    )
    record_capture_exactness = CacheStreamBackendTerminalRecordCaptureExactness(
        backend_terminal_payload_capture_exactness=payload_capture_exactness,
        status="partial",
        exactness_rung="stream_backend_terminal_record_capture_exact",
        verdict="backend_terminal_record_capture_dependency_narrowed",
        record_capture_status="backend_serial_boundary_decoupled_from_terminal_record_capture_visible",
        exchange_boundary="backend_terminal_record_prefix_detected_before_record_capture",
        next_active_dependency="backend_terminal_record_prefix_dependency",
        next_active_dependency_status="backend_stream_exchange_holds_serial_boundary_until_terminal_record_prefix_detection",
        preserved_non_stream_handoff_status="cohort_handed_off_to_aggregated_child_exchange_visible",
        residual_blocker="record prefix now blocks more exactly",
        recommended_next_step="freeze terminal record prefix seam",
    )
    record_prefix_exactness = CacheStreamBackendTerminalRecordPrefixExactness(
        backend_terminal_record_capture_exactness=record_capture_exactness,
        status="partial",
        exactness_rung="stream_backend_terminal_record_prefix_exact",
        verdict="backend_terminal_record_prefix_dependency_narrowed",
        prefix_status="backend_serial_boundary_decoupled_from_terminal_record_prefix_detection_visible",
        exchange_boundary="backend_terminal_action_discriminant_detected_before_full_record_prefix",
        next_active_dependency="backend_terminal_action_discriminant_dependency",
        next_active_dependency_status="backend_stream_exchange_holds_serial_boundary_until_terminal_action_discriminant_detection",
        preserved_non_stream_handoff_status="cohort_handed_off_to_aggregated_child_exchange_visible",
        residual_blocker="action discriminant now blocks more exactly",
        recommended_next_step="freeze terminal action discriminant seam",
    )
    harness = CacheStreamBackendTerminalActionDiscriminantHarnessResult(
        backend_terminal_action_discriminant_boundary_visible=True,
        action_discriminant_status="backend_terminal_action_discriminant_boundary_visible",
        second_stream_blocked_before_terminal_window=True,
        second_stream_request_written_before_first_terminal_action_discriminant_detected=True,
        second_stream_request_written_before_first_terminal_event_consumed=True,
        terminal_window_ms=180,
        first_stream_events=("token", "done"),
        second_stream_events=("token", "done"),
    )

    payload = cache_stream_backend_terminal_action_discriminant_exactness_to_dict(
        build_cache_stream_backend_terminal_action_discriminant_exactness(
            backend_terminal_record_prefix_exactness=record_prefix_exactness,
            backend_terminal_action_discriminant_harness=harness,
        )
    )

    assert (
        payload["summary"]["exactness_rung"]
        == "stream_backend_terminal_action_discriminant_exact"
    )
    assert (
        payload["summary"]["verdict"]
        == "backend_terminal_action_discriminant_dependency_narrowed"
    )
    assert (
        payload["next_active_dependency"]["dependency"]
        == "backend_terminal_notice_capture_dependency"
    )
    assert (
        payload["next_active_dependency"]["status"]
        == "backend_stream_exchange_holds_serial_boundary_until_terminal_notice_capture"
    )


def test_cache_stream_backend_terminal_action_discriminant_exactness_module_has_no_platform_dependency() -> None:
    source = Path(__file__).parents[1].joinpath(
        "owlmlx", "cache_stream_backend_terminal_action_discriminant_exactness.py"
    ).read_text()
    for pattern in ["llm_router", "ops_dashboard", "local-llm-desktop", "AI/Agent"]:
        assert pattern not in source
