from __future__ import annotations

from pathlib import Path

from owlmlx.cache_cohort_to_child_exchange_handoff_exactness import (
    CacheCohortToChildExchangeHandoffExactness,
)
from owlmlx.cache_stream_backend_terminal_event_exactness import (
    build_cache_stream_backend_terminal_event_exactness,
    cache_stream_backend_terminal_event_exactness_to_dict,
)
from owlmlx.cache_stream_backend_terminal_event_harness import (
    CacheStreamBackendTerminalEventHarnessResult,
)
from owlmlx.cache_stream_hold_dependency_exactness import (
    CacheStreamHoldDependencyExactness,
)


def test_cache_stream_backend_terminal_event_exactness_defaults_unresolved() -> None:
    payload = cache_stream_backend_terminal_event_exactness_to_dict(
        build_cache_stream_backend_terminal_event_exactness()
    )

    assert (
        payload["contract"]["surface"]
        == "owlmlx.cache_stream_backend_terminal_event_exactness"
    )
    assert payload["summary"]["exactness_rung"] == "stream_backend_terminal_event_unresolved"


def test_cache_stream_backend_terminal_event_exactness_narrows_to_terminal_event_dependency() -> None:
    handoff = CacheCohortToChildExchangeHandoffExactness(
        child_exchange_exactness=object(),  # type: ignore[arg-type]
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
    stream_hold = CacheStreamHoldDependencyExactness(
        cohort_handoff_exactness=handoff,
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
    harness = CacheStreamBackendTerminalEventHarnessResult(
        backend_terminal_event_boundary_visible=True,
        terminal_event_status="backend_terminal_event_serial_boundary_visible",
        second_stream_blocked_before_terminal_window=True,
        second_stream_started_before_first_terminal_event_consumed=True,
        second_stream_started_before_first_iterator_completed=True,
        terminal_window_ms=180,
        first_stream_events=("token", "done"),
        second_stream_events=("token", "done"),
    )

    payload = cache_stream_backend_terminal_event_exactness_to_dict(
        build_cache_stream_backend_terminal_event_exactness(
            stream_hold_exactness=stream_hold,
            backend_terminal_event_harness=harness,
        )
    )

    assert payload["summary"]["exactness_rung"] == "stream_backend_terminal_event_exact"
    assert (
        payload["summary"]["verdict"]
        == "backend_stream_terminal_event_dependency_narrowed"
    )
    assert (
        payload["backend_terminal_event"]["terminal_event_status"]
        == "backend_terminal_event_serial_boundary_visible"
    )
    assert (
        payload["next_active_dependency"]["dependency"]
        == "backend_terminal_payload_commit_dependency"
    )
    assert (
        payload["next_active_dependency"]["status"]
        == "backend_stream_exchange_holds_serial_boundary_until_terminal_payload_commit"
    )


def test_cache_stream_backend_terminal_event_exactness_module_has_no_platform_dependency() -> None:
    source = Path(__file__).parents[1].joinpath(
        "owlmlx", "cache_stream_backend_terminal_event_exactness.py"
    ).read_text()
    for pattern in ["llm_router", "ops_dashboard", "local-llm-desktop", "AI/Agent"]:
        assert pattern not in source
