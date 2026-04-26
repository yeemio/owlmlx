from __future__ import annotations

import asyncio
import threading
import time

from owlmlx.serving import GenerationGate, PreGateAdmissionMetadata


def _meta(*, request_kind: str, model_id: str, stream: bool = False) -> PreGateAdmissionMetadata:
    return PreGateAdmissionMetadata(
        request_kind=request_kind,
        model_id=model_id,
        stream=stream,
        prompt_chars=5,
        message_count=0,
    )


def test_generation_gate_status_exposes_bounded_pre_gate_hook() -> None:
    gate = GenerationGate()

    status = gate.status

    assert status["max_concurrent"] == 1
    assert status["queue_policy"] == "ticketed_fifo"
    assert status["pre_gate_admission"]["hook_status"] == "present"
    assert status["pre_gate_admission"]["hook_boundary"] == "before_whole_request_gate_claim"
    assert (
        status["pre_gate_admission"]["hook_mode"]
        == "bounded_runtime_owned_cohort_window"
    )
    assert status["pre_gate_admission"]["aggregation_scope"] == "pre_claim_window_only"
    assert status["pre_gate_admission"]["staging_units"] == [
        "immutable_request_metadata_snapshot",
        "ticket_reservation_without_gate_claim",
        "bounded_pre_claim_cohort_window_membership",
        "pre_claim_bounded_admission_bookkeeping",
    ]


def test_pre_gate_hook_exists_before_claim_without_reopening_post_claim_invariants() -> None:
    gate = GenerationGate()
    entered = threading.Event()
    release = threading.Event()
    results: dict[str, object] = {}

    def slow() -> str:
        entered.set()
        assert release.wait(timeout=1.0)
        return "slow"

    def fast() -> str:
        return "fast"

    def run_first() -> None:
        results["first"] = gate.execute_with_admission(
            _meta(request_kind="generate", model_id="model-a"),
            slow,
        )

    def run_second() -> None:
        results["second"] = gate.execute_with_admission(
            _meta(request_kind="generate", model_id="model-a"),
            fast,
        )

    first = threading.Thread(target=run_first)
    second = threading.Thread(target=run_second)
    first.start()
    time.sleep(0.005)
    second.start()
    assert entered.wait(timeout=1.0)

    deadline = time.monotonic() + 1.0
    midflight = None
    while time.monotonic() < deadline:
        status = gate.status
        if (
            status["generation_gate"] == "active"
            and status["pre_gate_admission"]["peak_cohort_size"] >= 2
            and status["pre_gate_admission"]["total_staged"] >= 2
        ):
            midflight = status
            break
        time.sleep(0.01)

    assert midflight is not None
    assert midflight["generation_gate"] == "active"
    assert midflight["pre_gate_admission"]["hook_boundary"] == "before_whole_request_gate_claim"
    assert midflight["pre_gate_admission"]["cohort_window_status"] in {
        "open_for_join",
        "closed_waiting_gate_claim",
    }
    assert midflight["pre_gate_admission"]["cohort_count"] >= 1
    assert midflight["pre_gate_admission"]["peak_cohort_size"] >= 2
    assert midflight["pre_gate_admission"]["total_staged"] >= 2
    assert midflight["pre_gate_admission"]["preserved_post_claim_invariants"] == [
        "max_concurrent_1_after_gate_claim",
        "ticketed_fifo_after_gate_claim",
        "serial_safety_validated_only_after_gate_claim",
    ]

    release.set()
    first.join(timeout=1.0)
    second.join(timeout=1.0)

    final = gate.status
    first_result = results["first"]
    second_result = results["second"]
    assert final["max_concurrent"] == 1
    assert final["queue_policy"] == "ticketed_fifo"
    assert final["total_served"] == 2
    assert final["pre_gate_admission"]["staged_count"] == 0
    assert final["pre_gate_admission"]["total_staged"] == 2
    assert final["pre_gate_admission"]["total_claimed"] == 2
    assert final["pre_gate_admission"]["total_discarded"] == 0
    assert final["pre_gate_admission"]["total_cohorts_formed"] >= 1
    assert final["pre_gate_admission"]["peak_cohort_size"] >= 2
    assert getattr(first_result, "was_queued") is False
    assert getattr(second_result, "was_queued") is True


def test_stream_session_with_admission_marks_pre_gate_wait_as_queued() -> None:
    gate = GenerationGate()
    entered = threading.Event()
    release = threading.Event()
    starts: list[object] = []

    async def hold_stream() -> None:
        async with gate.stream_session_with_admission(
            _meta(request_kind="stream", model_id="model-a", stream=True)
        ) as start:
            starts.append(start)
            entered.set()
            await asyncio.to_thread(release.wait, 1.0)

    async def queued_stream() -> None:
        async with gate.stream_session_with_admission(
            _meta(request_kind="stream", model_id="model-a", stream=True)
        ) as start:
            starts.append(start)

    async def run_pair() -> None:
        first = asyncio.create_task(hold_stream())
        await asyncio.to_thread(entered.wait, 1.0)
        second = asyncio.create_task(queued_stream())
        await asyncio.sleep(0.05)
        release.set()
        await asyncio.gather(first, second)

    asyncio.run(run_pair())

    assert len(starts) == 2
    assert starts[0].was_queued is False
    assert starts[1].was_queued is True
