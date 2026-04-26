"""Append-only JSONL ledger for ``comparative_evidence_record`` v1 records.

Every emitted record is appended as one JSON object per line. Records may
be superseded by later records but never silently rewritten — the file is
opened in append mode and existing lines are immutable from this module's
perspective.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .comparative_evidence_record import (
    ComparativeEvidenceRecord,
    comparative_evidence_record_to_dict,
)
from .comparative_evidence_schema import (
    SchemaValidationError,
    validate_comparative_evidence_record,
)


class ComparativeEvidenceLedger:
    """Thin wrapper over a JSONL ledger file."""

    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)

    @property
    def path(self) -> Path:
        return self._path

    def exists(self) -> bool:
        return self._path.exists()

    def append(self, record: ComparativeEvidenceRecord) -> dict[str, Any]:
        """Append one validated v1 record to the ledger and return its dict."""

        payload = comparative_evidence_record_to_dict(record)
        validate_comparative_evidence_record(payload)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(payload, sort_keys=True))
            stream.write("\n")
        return payload

    def history(self) -> list[dict[str, Any]]:
        """Return all records in append order. Empty list if file missing."""

        if not self._path.exists():
            return []
        records: list[dict[str, Any]] = []
        with self._path.open("r", encoding="utf-8") as stream:
            for line in stream:
                stripped = line.strip()
                if not stripped:
                    continue
                payload = json.loads(stripped)
                try:
                    validate_comparative_evidence_record(payload)
                except SchemaValidationError:
                    continue
                records.append(payload)
        return records

    def latest(self) -> dict[str, Any] | None:
        """Return the most recent valid record, or ``None`` if none exist."""

        records = self.history()
        return records[-1] if records else None


def still_blocked_payload(*, missing_signal: str, ledger_path: str | None) -> dict[str, Any]:
    """Return the explicit ``still_blocked`` payload used when no record exists."""

    return {
        "surface": "owlmlx.comparative_evidence_record",
        "version": "v1",
        "status": "still_blocked",
        "missing_signal": missing_signal,
        "ledger_path": ledger_path,
        "message": (
            "No comparative_evidence_record v1 has been appended to the ledger yet. "
            "Use scripts/runtime_comparative_evidence.py to append a record before "
            "treating this surface as live."
        ),
    }


def history_envelope(
    *,
    records: list[dict[str, Any]],
    ledger_status: str,
) -> dict[str, Any]:
    """Return the stable history envelope used by the history endpoint."""

    return {
        "surface": "owlmlx.comparative_evidence_record_history",
        "version": "v1",
        "ledger_status": ledger_status,
        "records": records,
    }


__all__ = [
    "ComparativeEvidenceLedger",
    "history_envelope",
    "still_blocked_payload",
]
