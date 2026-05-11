"""Runtime-owned harness for earlier-runtime-owned earlier-boundary first-unique-boundary exactness."""

from __future__ import annotations

import json
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedBoundaryEarlierBoundaryFirstUniqueBoundaryHarnessResult:
    """Observed first honest unique boundary on the new earlier-boundary record."""

    backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_first_unique_boundary_visible: (
        bool
    )
    leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_first_unique_boundary_status: (
        str
    )
    shared_non_unique_prefix: str
    first_honest_unique_boundary_prefix: str
    earlier_literal_prefix_is_not_runtime_owned_earlier_boundary: bool


def _shared_prefix(lhs: str, rhs: str) -> str:
    shared_chars: list[str] = []
    for left_char, right_char in zip(lhs, rhs):
        if left_char != right_char:
            break
        shared_chars.append(left_char)
    return "".join(shared_chars)


def run_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_first_unique_boundary_harness(
    *,
    model_id: str = "stream-terminal-notice-leading-discriminator-marker-earlier-runtime-owned-boundary-earlier-boundary-first-unique-boundary-probe",
    pid: int = 1,
    sequence: int = 1,
) -> CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedBoundaryEarlierBoundaryFirstUniqueBoundaryHarnessResult:
    """Freeze whether the new earlier-boundary record's earlier-boundary key is already the first honest unique boundary."""

    earlier_runtime_owned_earlier_boundary_record = json.dumps(
        {
            "ok": True,
            "runtime_owned_terminal_earlier_boundary": True,
            "action": "stream_runtime_owned_terminal_earlier_boundary",
            "terminal_action": "stream_done",
            "model_id": model_id,
            "pid": pid,
            "sequence": sequence,
        }
    )
    earlier_runtime_owned_boundary_record = json.dumps(
        {
            "ok": True,
            "runtime_owned_terminal_boundary": True,
            "action": "stream_runtime_owned_terminal_boundary",
            "terminal_action": "stream_done",
            "model_id": model_id,
            "pid": pid,
            "sequence": sequence,
        }
    )

    shared_non_unique_prefix = _shared_prefix(
        earlier_runtime_owned_earlier_boundary_record,
        earlier_runtime_owned_boundary_record,
    )
    first_honest_unique_boundary_prefix = '{"ok": true, "runtime_owned_terminal_earlier_b'
    earlier_literal_prefix_is_not_runtime_owned_earlier_boundary = (
        shared_non_unique_prefix == '{"ok": true, "runtime_owned_terminal_'
    )
    visible = (
        earlier_literal_prefix_is_not_runtime_owned_earlier_boundary
        and earlier_runtime_owned_earlier_boundary_record.startswith(
            first_honest_unique_boundary_prefix
        )
        and not earlier_runtime_owned_boundary_record.startswith(
            first_honest_unique_boundary_prefix
        )
    )
    status = (
        "backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_is_first_honest_unique_boundary_visible"
        if visible
        else "backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_first_unique_boundary_not_visible"
    )

    return CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedBoundaryEarlierBoundaryFirstUniqueBoundaryHarnessResult(
        backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_first_unique_boundary_visible=visible,
        leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_first_unique_boundary_status=status,
        shared_non_unique_prefix=shared_non_unique_prefix,
        first_honest_unique_boundary_prefix=first_honest_unique_boundary_prefix,
        earlier_literal_prefix_is_not_runtime_owned_earlier_boundary=(
            earlier_literal_prefix_is_not_runtime_owned_earlier_boundary
        ),
    )
