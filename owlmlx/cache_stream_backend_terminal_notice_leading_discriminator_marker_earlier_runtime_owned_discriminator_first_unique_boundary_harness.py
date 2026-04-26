"""Runtime-owned harness for earlier runtime-owned discriminator first-unique-boundary exactness."""

from __future__ import annotations

import json
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedDiscriminatorFirstUniqueBoundaryHarnessResult:
    """Observed first honest unique boundary on the earlier runtime-owned discriminator record."""

    backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_first_unique_boundary_visible: (
        bool
    )
    leading_discriminator_marker_earlier_runtime_owned_discriminator_first_unique_boundary_status: (
        str
    )
    shared_non_unique_prefix: str
    first_honest_unique_boundary_prefix: str
    earlier_literal_prefix_is_not_runtime_owned_boundary: bool


def _shared_prefix(lhs: str, rhs: str) -> str:
    shared_chars: list[str] = []
    for left_char, right_char in zip(lhs, rhs):
        if left_char != right_char:
            break
        shared_chars.append(left_char)
    return "".join(shared_chars)


def run_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_first_unique_boundary_harness(
    *,
    model_id: str = "stream-terminal-notice-leading-discriminator-marker-earlier-runtime-owned-discriminator-first-unique-boundary-probe",
    pid: int = 1,
    sequence: int = 1,
) -> CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedDiscriminatorFirstUniqueBoundaryHarnessResult:
    """Freeze whether the earlier runtime-owned discriminator discriminant is already the first honest unique boundary."""

    earlier_runtime_owned_discriminator_record = json.dumps(
        {
            "ok": True,
            "runtime_owned_terminal_notice_discriminator": True,
            "action": "stream_runtime_owned_terminal_notice_discriminator",
            "terminal_action": "stream_done",
            "model_id": model_id,
            "pid": pid,
            "sequence": sequence,
        }
    )
    current_marker_first_record = json.dumps(
        {
            "ok": True,
            "terminal_notice_lead": True,
            "action": "stream_terminal_notice_lead",
            "terminal_action": "stream_done",
            "model_id": model_id,
            "pid": pid,
            "sequence": sequence,
        }
    )

    shared_non_unique_prefix = _shared_prefix(
        earlier_runtime_owned_discriminator_record,
        current_marker_first_record,
    )
    first_honest_unique_boundary_prefix = (
        '{"ok": true, "runtime_owned_terminal_notice_'
    )
    earlier_literal_prefix_is_not_runtime_owned_boundary = (
        shared_non_unique_prefix == '{"ok": true, "'
    )
    visible = (
        earlier_literal_prefix_is_not_runtime_owned_boundary
        and earlier_runtime_owned_discriminator_record.startswith(
            first_honest_unique_boundary_prefix
        )
        and not current_marker_first_record.startswith(
            first_honest_unique_boundary_prefix
        )
    )
    status = (
        "backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_discriminant_is_first_honest_unique_boundary_visible"
        if visible
        else "backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_first_unique_boundary_not_visible"
    )

    return CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedDiscriminatorFirstUniqueBoundaryHarnessResult(
        backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_first_unique_boundary_visible=visible,
        leading_discriminator_marker_earlier_runtime_owned_discriminator_first_unique_boundary_status=status,
        shared_non_unique_prefix=shared_non_unique_prefix,
        first_honest_unique_boundary_prefix=first_honest_unique_boundary_prefix,
        earlier_literal_prefix_is_not_runtime_owned_boundary=(
            earlier_literal_prefix_is_not_runtime_owned_boundary
        ),
    )
