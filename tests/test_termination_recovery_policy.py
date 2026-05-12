from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from owlmlx.abort_recovery import AbortRecoveryTracker
from owlmlx.memory_budget import MachineMemoryProfile
from owlmlx.runtime import FakeBackend, RuntimeKernel
from owlmlx.runtime.server import create_app
from owlmlx.runtime.types import RuntimeErrorCode, UnloadResult
from owlmlx.termination_recovery_policy import (
    DOMINANT_CAUSE_PRIORITY,
    REQUIRED_DECISION_FIELDS,
    TERMINATION_CAUSE_CLASSES,
    TERMINATION_RECOVERY_ACTIONS,
    TERMINATION_RECOVERY_POLICY_SURFACE,
    build_termination_recovery_policy,
    termination_recovery_policy_to_dict,
)


def _profile() -> MachineMemoryProfile:
    return MachineMemoryProfile(
        system_memory_gb=8.0,
        system_reserve_gb=2.0,
        serving_budget_gb=6.0,
        warning_threshold_gb=5.0,
    )


class _FailingUnloadFakeBackend(FakeBackend):
    def __init__(
        self,
        *,
        fail_unload_for: set[str] | None = None,
        **kwargs: object,
    ) -> None:
        super().__init__(**kwargs)
        self._fail_unload_for = set(fail_unload_for or set())

    def unload(self, model_id: str) -> UnloadResult:
        if model_id in self._fail_unload_for:
            return UnloadResult(
                ok=False,
                message=f"injected backend cleanup failure for {model_id}",
                error_code=RuntimeErrorCode.backend_error,
                model_id=model_id,
                freed_gb=0.0,
            )
        return super().unload(model_id)


class _FailingLoadFakeBackend(FakeBackend):
    def __init__(
        self,
        *,
        fail_load_for: set[str] | None = None,
        **kwargs: object,
    ) -> None:
        super().__init__(**kwargs)
        self._fail_load_for = set(fail_load_for or set())

    def load(self, model_id, *, memory_gb=None):
        if model_id in self._fail_load_for:
            from owlmlx.runtime.types import LoadResult

            return LoadResult(
                ok=False,
                message=f"injected backend load failure for {model_id}",
                error_code=RuntimeErrorCode.backend_error,
            )
        return super().load(model_id, memory_gb=memory_gb)


def _payload(
    runtime_status: dict[str, object] | None = None,
    tracker: AbortRecoveryTracker | None = None,
) -> dict[str, object]:
    snapshot = (tracker or AbortRecoveryTracker()).snapshot()
    return termination_recovery_policy_to_dict(
        build_termination_recovery_policy(
            runtime_status=runtime_status,
            abort_recovery_snapshot=snapshot,
        )
    )


def test_surface_and_vocabulary_are_frozen() -> None:
    payload = _payload(runtime_status={})
    assert payload["contract"]["surface"] == TERMINATION_RECOVERY_POLICY_SURFACE
    assert payload["contract"]["version"] == "v1"
    assert payload["summary"]["supported_causes"] == list(TERMINATION_CAUSE_CLASSES)
    assert payload["summary"]["supported_actions"] == list(TERMINATION_RECOVERY_ACTIONS)


def test_action_vocabulary_is_exactly_four_values() -> None:
    assert set(TERMINATION_RECOVERY_ACTIONS) == {
        "retry",
        "quarantine",
        "surface_to_coordinator",
        "drop",
    }


def test_cause_vocabulary_includes_required_classes() -> None:
    required = {
        "load_failure",
        "oom_class_failure",
        "host_forensics_anomaly",
        "graceful_unload_failure",
        "unknown",
    }
    assert required <= set(TERMINATION_CAUSE_CLASSES)


def test_each_cause_has_exactly_one_action_in_vocabulary() -> None:
    kernel = RuntimeKernel(FakeBackend(), profile=_profile())
    payload = _payload(kernel.status_dict())
    for decision in payload["cause_decisions"]:
        assert decision["next_action"] in TERMINATION_RECOVERY_ACTIONS
        for field in REQUIRED_DECISION_FIELDS:
            assert field in decision, f"missing field: {field}"


def test_clean_runtime_has_no_active_cause() -> None:
    kernel = RuntimeKernel(FakeBackend(), profile=_profile())
    payload = _payload(kernel.status_dict())
    assert payload["summary"]["active_cause_count"] == 0
    assert payload["summary"]["dominant_cause"] == "none_active"
    assert payload["summary"]["dominant_action"] == "no_action_required"
    assert payload["active_causes"] == []


def test_graceful_unload_failure_consumes_reclaim_barrier_event() -> None:
    kernel = RuntimeKernel(
        _FailingUnloadFakeBackend(fail_unload_for={"fake-a"}),
        profile=_profile(),
    )
    kernel.load_model("fake-a", memory_gb=1.0)
    kernel.unload_model("fake-a")  # records failed_unload event

    payload = _payload(kernel.status_dict())
    decisions = {d["termination_cause_class"]: d for d in payload["cause_decisions"]}
    graceful = decisions["graceful_unload_failure"]
    assert graceful["active"] is True
    assert graceful["next_action"] == "quarantine"
    assert graceful["source_signal"] == "owlmlx.settle_barrier_event"
    assert any(
        sig.get("operation") == "explicit_unload"
        for sig in graceful["detected_signals"]
    )
    assert "auto_resolve" in graceful["resolution_rule"]
    assert payload["summary"]["dominant_cause"] == "graceful_unload_failure"
    assert payload["summary"]["dominant_action"] == "quarantine"


def test_oom_class_failure_classified_when_budget_exceeded() -> None:
    kernel = RuntimeKernel(
        FakeBackend(default_memory_gb=100.0),
        profile=_profile(),
    )
    result = kernel.load_model("too-big", memory_gb=100.0)
    assert result.ok is False
    assert result.error_code is RuntimeErrorCode.memory_budget_exceeded

    payload = _payload(kernel.status_dict())
    decisions = {d["termination_cause_class"]: d for d in payload["cause_decisions"]}
    oom = decisions["oom_class_failure"]
    assert oom["active"] is True
    assert oom["next_action"] == "surface_to_coordinator"
    assert any(
        sig.get("error_code") == "memory_budget_exceeded"
        for sig in oom["detected_signals"]
    )

    load = decisions["load_failure"]
    # OOM-class events must NOT be classified as generic load_failure.
    assert load["active"] is False


def test_load_failure_classified_when_backend_fails() -> None:
    kernel = RuntimeKernel(
        _FailingLoadFakeBackend(fail_load_for={"broken"}),
        profile=_profile(),
    )
    result = kernel.load_model("broken", memory_gb=1.0)
    assert result.ok is False
    assert result.error_code is RuntimeErrorCode.backend_error

    payload = _payload(kernel.status_dict())
    decisions = {d["termination_cause_class"]: d for d in payload["cause_decisions"]}
    assert decisions["load_failure"]["active"] is True
    assert decisions["load_failure"]["next_action"] == "retry"
    assert decisions["oom_class_failure"]["active"] is False


def test_load_failure_does_not_use_restart_exhausted_models_alone() -> None:
    """Pre-flight notes established that restart_exhausted_models is
    session-death-specific, NOT a general load-failure signal. The policy
    must only classify load_failure from operation-boundary load events."""

    runtime_status = {
        "summary": {"backend_healthy": True},
        "restart": {
            "restartable_models": [],
            "restart_exhausted_models": ["session-dead-model"],
            "auto_restart_dead_session": False,
        },
    }
    payload = _payload(runtime_status=runtime_status)
    decisions = {d["termination_cause_class"]: d for d in payload["cause_decisions"]}
    assert decisions["load_failure"]["active"] is False
    assert decisions["oom_class_failure"]["active"] is False


def test_host_forensics_anomaly_when_substrate_contaminated() -> None:
    payload = termination_recovery_policy_to_dict(
        build_termination_recovery_policy(
            runtime_status={
                "summary": {"backend_healthy": True},
                "restart": {"restart_exhausted_models": []},
            },
            abort_recovery_snapshot={
                "state": "contaminated",
                "recovery_required": True,
                "contamination_reason": "injected for test",
            },
        )
    )
    decisions = {d["termination_cause_class"]: d for d in payload["cause_decisions"]}
    host = decisions["host_forensics_anomaly"]
    assert host["active"] is True
    assert host["next_action"] == "surface_to_coordinator"
    assert any(
        "automatic_retry" in forbidden
        for forbidden in host["forbidden_automation"]
    )


def test_host_forensics_anomaly_when_backend_unhealthy() -> None:
    payload = _payload(
        runtime_status={
            "summary": {"backend_healthy": False},
            "restart": {"restart_exhausted_models": []},
        }
    )
    decisions = {d["termination_cause_class"]: d for d in payload["cause_decisions"]}
    host = decisions["host_forensics_anomaly"]
    assert host["active"] is True
    assert host["next_action"] == "surface_to_coordinator"


def test_unknown_when_runtime_status_is_missing() -> None:
    payload = _payload(runtime_status=None)
    decisions = {d["termination_cause_class"]: d for d in payload["cause_decisions"]}
    assert decisions["unknown"]["active"] is True
    assert decisions["unknown"]["next_action"] == "surface_to_coordinator"
    assert payload["summary"]["dominant_cause"] == "unknown"


def test_dominant_cause_priority_host_forensics_first() -> None:
    """When multiple causes are active, host_forensics_anomaly wins."""

    kernel = RuntimeKernel(
        _FailingUnloadFakeBackend(fail_unload_for={"fake-a"}),
        profile=_profile(),
    )
    kernel.load_model("fake-a", memory_gb=1.0)
    kernel.unload_model("fake-a")  # graceful_unload_failure active

    snapshot = {
        "state": "contaminated",
        "recovery_required": True,
        "contamination_reason": "injected for priority test",
    }
    payload = termination_recovery_policy_to_dict(
        build_termination_recovery_policy(
            runtime_status=kernel.status_dict(),
            abort_recovery_snapshot=snapshot,
        )
    )
    assert payload["summary"]["dominant_cause"] == "host_forensics_anomaly"
    assert "host_forensics_anomaly" in payload["active_causes"]
    assert "graceful_unload_failure" in payload["active_causes"]
    # Host forensics is first in DOMINANT_CAUSE_PRIORITY
    assert DOMINANT_CAUSE_PRIORITY[0] == "host_forensics_anomaly"


def test_resolution_rule_recorded_for_every_cause() -> None:
    payload = _payload(runtime_status={})
    for decision in payload["cause_decisions"]:
        assert decision["resolution_rule"], (
            f"cause {decision['termination_cause_class']} missing resolution_rule"
        )


def test_resolution_does_not_happen_from_final_status_alone() -> None:
    """Just observing clean status after unrelated cleanup must NOT resolve
    the prior failed-unload event."""

    kernel = RuntimeKernel(
        _FailingUnloadFakeBackend(fail_unload_for={"fake-a"}),
        profile=_profile(),
    )
    kernel.load_model("fake-a", memory_gb=1.0)
    kernel.unload_model("fake-a")  # records event

    # Some unrelated cleanup happens (load+unload of a different model).
    kernel.load_model("fake-b", memory_gb=1.0)
    kernel.unload_model("fake-b")  # success on fake-b doesn't affect fake-a

    payload = _payload(kernel.status_dict())
    decisions = {d["termination_cause_class"]: d for d in payload["cause_decisions"]}
    # Event for fake-a is still unresolved.
    assert decisions["graceful_unload_failure"]["active"] is True


def test_successful_same_model_followup_unload_resolves_event() -> None:
    """Auto-resolution: successful follow-up unload of the same model id
    resolves the prior failed-unload event."""

    backend = _FailingUnloadFakeBackend(fail_unload_for={"fake-a"})
    kernel = RuntimeKernel(backend, profile=_profile())
    kernel.load_model("fake-a", memory_gb=1.0)
    kernel.unload_model("fake-a")  # records event

    # Operator fixed the underlying issue: clear the injection.
    backend._fail_unload_for.clear()
    kernel.unload_model("fake-a")  # success now

    payload = _payload(kernel.status_dict())
    decisions = {d["termination_cause_class"]: d for d in payload["cause_decisions"]}
    assert decisions["graceful_unload_failure"]["active"] is False


def test_successful_same_model_load_resolves_load_failure_event() -> None:
    backend = _FailingLoadFakeBackend(fail_load_for={"flaky"})
    kernel = RuntimeKernel(backend, profile=_profile())
    kernel.load_model("flaky", memory_gb=1.0)  # records load_failure event

    backend._fail_load_for.clear()
    result = kernel.load_model("flaky", memory_gb=1.0)
    assert result.ok is True

    payload = _payload(kernel.status_dict())
    decisions = {d["termination_cause_class"]: d for d in payload["cause_decisions"]}
    assert decisions["load_failure"]["active"] is False


def test_explicit_resolve_reclaim_barrier_event_marks_resolved() -> None:
    kernel = RuntimeKernel(
        _FailingUnloadFakeBackend(fail_unload_for={"fake-a"}),
        profile=_profile(),
    )
    kernel.load_model("fake-a", memory_gb=1.0)
    kernel.unload_model("fake-a")
    event_id = kernel._reclaim_barrier_events[-1]["event_id"]

    result = kernel.resolve_reclaim_barrier_event(event_id)
    assert result["ok"] is True
    assert result["already_resolved"] is False

    # Calling again is idempotent.
    result_again = kernel.resolve_reclaim_barrier_event(event_id)
    assert result_again["ok"] is True
    assert result_again["already_resolved"] is True

    payload = _payload(kernel.status_dict())
    decisions = {d["termination_cause_class"]: d for d in payload["cause_decisions"]}
    assert decisions["graceful_unload_failure"]["active"] is False


def test_explicit_resolve_unknown_event_id_returns_error() -> None:
    kernel = RuntimeKernel(FakeBackend(), profile=_profile())
    result = kernel.resolve_reclaim_barrier_event(99999)
    assert result["ok"] is False
    assert result["error_code"] == "reclaim_barrier_event_not_found"


def test_termination_recovery_policy_route_returns_payload() -> None:
    client = TestClient(create_app(RuntimeKernel(FakeBackend(), profile=_profile())))
    response = client.get("/v1/runtime/termination-recovery-policy")
    assert response.status_code == 200
    payload = response.json()
    assert payload["contract"]["surface"] == TERMINATION_RECOVERY_POLICY_SURFACE
    assert payload["summary"]["supported_actions"] == list(TERMINATION_RECOVERY_ACTIONS)


def test_recovery_supervisor_still_reports_hard_barrier_when_event_unresolved() -> None:
    from owlmlx.recovery_supervisor import (
        build_recovery_supervisor_contract,
        recovery_supervisor_contract_to_dict,
    )

    kernel = RuntimeKernel(
        _FailingUnloadFakeBackend(fail_unload_for={"fake-a"}),
        profile=_profile(),
    )
    kernel.load_model("fake-a", memory_gb=1.0)
    kernel.unload_model("fake-a")

    recovery = recovery_supervisor_contract_to_dict(
        build_recovery_supervisor_contract(
            runtime_status=kernel.status_dict(),
            abort_recovery_snapshot=kernel.abort_recovery.snapshot(),
        )
    )
    assert recovery["barrier"]["hard_recovery_barrier"] is True


def test_admission_still_rejects_via_recovery_hard_barrier() -> None:
    from owlmlx.scheduler_admission import (
        build_scheduler_admission_contract,
        scheduler_admission_contract_to_dict,
    )

    kernel = RuntimeKernel(
        _FailingUnloadFakeBackend(fail_unload_for={"fake-a"}),
        profile=_profile(),
    )
    kernel.load_model("fake-a", memory_gb=1.0)
    kernel.unload_model("fake-a")

    payload = scheduler_admission_contract_to_dict(
        build_scheduler_admission_contract(
            runtime_status=kernel.status_dict(),
            request_class="interactive",
            abort_recovery_snapshot=kernel.abort_recovery.snapshot(),
        )
    )
    assert payload["summary"]["admission_decision"] == "rejected"


def test_orchestration_status_still_reports_recovery_bottleneck() -> None:
    from owlmlx.orchestration_status import (
        build_orchestration_status,
        orchestration_status_to_dict,
    )

    kernel = RuntimeKernel(
        _FailingUnloadFakeBackend(fail_unload_for={"fake-a"}),
        profile=_profile(),
    )
    kernel.load_model("fake-a", memory_gb=1.0)
    kernel.unload_model("fake-a")

    payload = orchestration_status_to_dict(
        build_orchestration_status(
            runtime_status=kernel.status_dict(),
            abort_recovery_snapshot=kernel.abort_recovery.snapshot(),
        )
    )
    assert payload["summary"]["bottleneck_layer"] == "recovery"


def test_termination_recovery_policy_module_has_no_platform_dependency() -> None:
    source = (
        Path(__file__).parents[1]
        / "owlmlx"
        / "termination_recovery_policy.py"
    ).read_text()
    forbidden = ["llm_router", "ops_dashboard", "AI/Agent", "owlops", "owlcoda"]
    for pattern in forbidden:
        assert pattern not in source


def test_drop_action_is_in_vocabulary_but_unused_today() -> None:
    """The frozen vocabulary includes `drop`; no current required cause
    class maps to it. Document this explicitly via missing_signals."""

    payload = _payload(runtime_status={})
    actions_used = {d["next_action"] for d in payload["cause_decisions"]}
    assert "drop" not in actions_used
    assert "drop" in TERMINATION_RECOVERY_ACTIONS
    assert any(
        signal["layer"] == "drop" for signal in payload["missing_signals"]
    )
