"""Append-only JSONL ledger for model release-candidate evidence records."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .model_release_candidate_record import (
    ModelReleaseCandidateRecord,
    model_release_candidate_record_to_dict,
)
from .model_release_candidate_schema import (
    MODEL_RELEASE_CANDIDATE_RECORD_HISTORY_SURFACE,
    MODEL_RELEASE_CANDIDATE_RECORD_SURFACE,
    MODEL_RELEASE_CANDIDATE_RECORD_VERSION,
    ModelReleaseCandidateSchemaError,
    validate_model_release_candidate_record,
)


class ModelReleaseCandidateLedger:
    """Thin append-only wrapper around one JSONL ledger."""

    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)

    @property
    def path(self) -> Path:
        return self._path

    def exists(self) -> bool:
        return self._path.exists()

    def append(self, record: ModelReleaseCandidateRecord) -> dict[str, Any]:
        payload = model_release_candidate_record_to_dict(record)
        validate_model_release_candidate_record(payload)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(payload, sort_keys=True))
            stream.write("\n")
        return payload

    def append_many(
        self,
        records: tuple[ModelReleaseCandidateRecord, ...]
        | list[ModelReleaseCandidateRecord],
    ) -> list[dict[str, Any]]:
        return [self.append(record) for record in records]

    def history(self) -> list[dict[str, Any]]:
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
                    validate_model_release_candidate_record(payload)
                except ModelReleaseCandidateSchemaError:
                    continue
                records.append(payload)
        return records

    def latest(self) -> dict[str, Any] | None:
        records = self.history()
        return records[-1] if records else None


def model_release_candidate_still_blocked_payload(
    *,
    missing_signal: str,
    ledger_path: str | None,
) -> dict[str, Any]:
    return {
        "surface": MODEL_RELEASE_CANDIDATE_RECORD_SURFACE,
        "version": MODEL_RELEASE_CANDIDATE_RECORD_VERSION,
        "status": "still_blocked",
        "missing_signal": missing_signal,
        "ledger_path": ledger_path,
        "message": (
            "No model_release_candidate_record v1 is available. Run "
            "scripts/runtime_model_release_candidate.py append-dry-run-matrix "
            "or a live model RC runner before treating this surface as evidence."
        ),
    }


def model_release_candidate_history_envelope(
    *,
    records: list[dict[str, Any]],
    ledger_status: str,
) -> dict[str, Any]:
    return {
        "surface": MODEL_RELEASE_CANDIDATE_RECORD_HISTORY_SURFACE,
        "version": MODEL_RELEASE_CANDIDATE_RECORD_VERSION,
        "ledger_status": ledger_status,
        "records": records,
    }


__all__ = [
    "ModelReleaseCandidateLedger",
    "model_release_candidate_history_envelope",
    "model_release_candidate_still_blocked_payload",
]
