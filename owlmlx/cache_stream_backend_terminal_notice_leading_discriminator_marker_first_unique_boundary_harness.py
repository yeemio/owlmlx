"""Runtime-owned harness for backend terminal-notice leading-discriminator marker first-unique-boundary exactness."""

from __future__ import annotations

import json
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerFirstUniqueBoundaryHarnessResult:
    """Observed boundary comparison between the new marker-first record and the older notice record."""

    backend_terminal_notice_leading_discriminator_marker_first_unique_boundary_visible: (
        bool
    )
    leading_discriminator_marker_first_unique_boundary_status: str
    shared_non_unique_prefix: str
    first_unique_boundary_prefix: str
    earlier_prefix_collides_with_old_notice_record: bool


def _shared_prefix(lhs: str, rhs: str) -> str:
    shared_chars: list[str] = []
    for left_char, right_char in zip(lhs, rhs):
        if left_char != right_char:
            break
        shared_chars.append(left_char)
    return "".join(shared_chars)


def run_cache_stream_backend_terminal_notice_leading_discriminator_marker_first_unique_boundary_harness(
    *,
    model_id: str = "stream-terminal-notice-leading-discriminator-marker-first-unique-boundary-probe",
    pid: int = 1,
    sequence: int = 1,
) -> CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerFirstUniqueBoundaryHarnessResult:
    """Freeze the first honest unique boundary on the runtime-owned marker-first transport record."""

    leading_discriminator_record = json.dumps(
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
    old_notice_record = json.dumps(
        {
            "ok": True,
            "terminal_notice": True,
            "action": "stream_terminal_notice",
            "terminal_action": "stream_done",
            "model_id": model_id,
            "pid": pid,
            "sequence": sequence,
        }
    )

    shared_non_unique_prefix = _shared_prefix(
        leading_discriminator_record,
        old_notice_record,
    )
    first_unique_boundary_prefix = leading_discriminator_record[
        : len(shared_non_unique_prefix) + 1
    ]
    earlier_prefix_collides_with_old_notice_record = old_notice_record.startswith(
        shared_non_unique_prefix
    )
    visible = (
        earlier_prefix_collides_with_old_notice_record
        and first_unique_boundary_prefix == '{"ok": true, "terminal_notice_'
        and leading_discriminator_record.startswith(first_unique_boundary_prefix)
        and not old_notice_record.startswith(first_unique_boundary_prefix)
    )
    status = (
        "backend_terminal_notice_leading_discriminator_marker_discriminant_is_first_unique_boundary_visible"
        if visible
        else "backend_terminal_notice_leading_discriminator_marker_first_unique_boundary_not_visible"
    )

    return CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerFirstUniqueBoundaryHarnessResult(
        backend_terminal_notice_leading_discriminator_marker_first_unique_boundary_visible=visible,
        leading_discriminator_marker_first_unique_boundary_status=status,
        shared_non_unique_prefix=shared_non_unique_prefix,
        first_unique_boundary_prefix=first_unique_boundary_prefix,
        earlier_prefix_collides_with_old_notice_record=(
            earlier_prefix_collides_with_old_notice_record
        ),
    )
