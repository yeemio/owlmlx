from __future__ import annotations

from pathlib import Path

from owlmlx.cache_stream_backend_terminal_event_exactness import (
    CacheStreamBackendTerminalEventExactness,
)
from owlmlx.cache_stream_backend_terminal_payload_capture_exactness import (
    build_cache_stream_backend_terminal_payload_capture_exactness,
    cache_stream_backend_terminal_payload_capture_exactness_to_dict,
)
from owlmlx.cache_stream_backend_terminal_payload_capture_harness import (
    CacheStreamBackendTerminalPayloadCaptureHarnessResult,
)
from owlmlx.cache_stream_backend_terminal_payload_commit_exactness import (
    CacheStreamBackendTerminalPayloadCommitExactness,
)
from owlmlx.cache_stream_hold_dependency_exactness import (
    CacheStreamHoldDependencyExactness,
)


def test_cache_stream_backend_terminal_payload_capture_exactness_defaults_unresolved() -> None:
    payload = cache_stream_backend_terminal_payload_capture_exactness_to_dict(
        build_cache_stream_backend_terminal_payload_capture_exactness()
    )

    assert (
        payload["contract"]["surface"]
        == "owlmlx.cache_stream_backend_terminal_payload_capture_exactness"
    )
    assert (
        payload["summary"]["exactness_rung"]
        == "stream_backend_terminal_payload_capture_unresolved"
    )


def test_cache_stream_backend_terminal_payload_capture_exactness_narrows_to_terminal_record_dependency() -> None:
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
    harness = CacheStreamBackendTerminalPayloadCaptureHarnessResult(
        backend_terminal_payload_capture_boundary_visible=True,
        payload_capture_status="backend_terminal_payload_capture_boundary_visible",
        second_stream_blocked_before_terminal_window=True,
        second_stream_started_before_first_terminal_payload_captured=True,
        second_stream_started_before_first_terminal_event_consumed=True,
        terminal_window_ms=180,
        first_stream_events=("token", "done"),
        second_stream_events=("token", "done"),
    )

    payload = cache_stream_backend_terminal_payload_capture_exactness_to_dict(
        build_cache_stream_backend_terminal_payload_capture_exactness(
            backend_terminal_payload_commit_exactness=payload_commit_exactness,
            backend_terminal_payload_capture_harness=harness,
        )
    )

    assert (
        payload["summary"]["exactness_rung"]
        == "stream_backend_terminal_payload_capture_exact"
    )
    assert (
        payload["summary"]["verdict"]
        == "backend_terminal_payload_capture_dependency_narrowed"
    )
    assert (
        payload["next_active_dependency"]["dependency"]
        == "backend_terminal_record_capture_dependency"
    )
    assert (
        payload["next_active_dependency"]["status"]
        == "backend_stream_exchange_holds_serial_boundary_until_terminal_record_capture"
    )


def test_cache_stream_backend_terminal_payload_capture_exactness_module_has_no_platform_dependency() -> None:
    source = Path(__file__).parents[1].joinpath(
        "owlmlx", "cache_stream_backend_terminal_payload_capture_exactness.py"
    ).read_text()
    for pattern in ["llm_router", "ops_dashboard", "local-llm-desktop", "AI/Agent"]:
        assert pattern not in source
