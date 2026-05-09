"""MLX runtime environment probing and selection helpers."""

from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path

from .mlx_lm_backend import MlxLmImportProbeResult, probe_mlx_lm_import


@dataclass(frozen=True, slots=True)
class MlxEnvironmentCandidate:
    """A Python executable candidate for mlx-lm subprocess execution."""

    python_executable: str
    label: str
    execution_mode: str = "default_metal"


@dataclass(frozen=True, slots=True)
class MlxEnvironmentProbe:
    """Probe result for a single Python executable candidate."""

    candidate: MlxEnvironmentCandidate
    result: MlxLmImportProbeResult

    @property
    def usable(self) -> bool:
        return self.result.ok


@dataclass(frozen=True, slots=True)
class MlxEnvironmentSelection:
    """Final selection over a set of candidates."""

    selected: MlxEnvironmentProbe | None
    probes: tuple[MlxEnvironmentProbe, ...]
    message: str

    @property
    def ok(self) -> bool:
        return self.selected is not None


@dataclass(frozen=True, slots=True)
class MlxEnvironmentReadiness:
    """Stable runtime-owned readiness view over MLX subprocess environments."""

    selection: MlxEnvironmentSelection
    include_known_candidates: bool
    preferred_execution_mode: str
    quarantine_count: int
    blocked_reason: str | None

    @property
    def ok(self) -> bool:
        return self.selection.ok


@dataclass(frozen=True, slots=True)
class MlxImportBlockerReport:
    """Stable runtime-owned report for machine-level MLX import blockers."""

    readiness: MlxEnvironmentReadiness
    quarantine_file: str

    @property
    def blocked(self) -> bool:
        return not self.readiness.ok


@dataclass(frozen=True, slots=True)
class MlxCrashReportSummary:
    """Reduced summary over one macOS diagnostic crash report."""

    path: str
    timestamp: str | None
    incident_id: str | None
    signal: str | None
    exception_name: str | None
    exception_message: str | None
    top_symbol: str | None
    mlx_symbol: str | None
    os_version: str | None
    model_code: str | None
    python_path: str | None


@dataclass(frozen=True, slots=True)
class MlxHostForensicsReport:
    """Stable runtime-owned host forensics view for MLX import crashes."""

    readiness: MlxEnvironmentReadiness
    crash_reports: tuple[MlxCrashReportSummary, ...]
    crash_report_directory: str

    @property
    def blocked(self) -> bool:
        return not self.readiness.ok


_KNOWN_UNSAFE_EXECUTABLE_SUFFIXES: tuple[str, ...] = (
    "/AI/llm-infra/.venv/bin/python",
    "/AI/gitrep/owlmlx/.venv/bin/python",
)


def candidate_identity(
    python_executable: str,
    execution_mode: str = "default_metal",
) -> str:
    """Return the stable identity key for one interpreter-mode baseline."""

    normalized = str(Path(python_executable).expanduser())
    return f"{normalized}::{execution_mode}"


def quarantine_file_path() -> Path:
    """Return the persistent quarantine file for unsafe MLX interpreters."""

    override = os.environ.get("OWLMX_MLX_QUARANTINE_PATH")
    if override:
        return Path(override).expanduser()
    return Path.home() / ".owlmlx" / "mlx-unsafe-python.json"


def verified_baseline_file_path() -> Path:
    """Return the persistent registry of verified safe MLX interpreters."""

    override = os.environ.get("OWLMX_MLX_VERIFIED_BASELINES_PATH")
    if override:
        return Path(override).expanduser()
    return Path.home() / ".owlmlx" / "mlx-verified-python.json"


def load_quarantined_pythons(*, path: Path | None = None) -> dict[str, str]:
    """Load persisted unsafe-python quarantine entries."""

    target = path or quarantine_file_path()
    if not target.exists():
        return {}
    try:
        payload = json.loads(target.read_text(encoding="utf-8"))
    except Exception:
        return {}
    entries = payload.get("executables")
    if not isinstance(entries, dict):
        return {}
    normalized: dict[str, str] = {}
    for executable, reason in entries.items():
        if not isinstance(executable, str):
            continue
        if "::" in executable:
            normalized[executable] = str(reason)
            continue
        normalized[candidate_identity(executable)] = str(reason)
    return normalized


def remember_quarantined_python(
    python_executable: str,
    *,
    reason: str,
    execution_mode: str = "default_metal",
    path: Path | None = None,
) -> None:
    """Persist an interpreter-mode pair that aborted during MLX import probing."""

    normalized = candidate_identity(python_executable, execution_mode)
    target = path or quarantine_file_path()
    existing = load_quarantined_pythons(path=target)
    existing[normalized] = reason
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = {"executables": dict(sorted(existing.items()))}
    target.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load_verified_baselines(*, path: Path | None = None) -> tuple[MlxEnvironmentCandidate, ...]:
    """Load persisted verified-safe MLX interpreter baselines."""

    target = path or verified_baseline_file_path()
    if not target.exists():
        return ()
    try:
        payload = json.loads(target.read_text(encoding="utf-8"))
    except Exception:
        return ()
    entries = payload.get("executables")
    if not isinstance(entries, list):
        return ()
    candidates: list[MlxEnvironmentCandidate] = []
    seen: set[str] = set()
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        executable = entry.get("python_executable")
        label = entry.get("label")
        execution_mode = entry.get("execution_mode", "default_metal")
        if (
            not isinstance(executable, str)
            or not isinstance(label, str)
            or not isinstance(execution_mode, str)
        ):
            continue
        normalized = str(Path(executable).expanduser())
        identity = candidate_identity(normalized, execution_mode)
        if identity in seen:
            continue
        seen.add(identity)
        candidates.append(MlxEnvironmentCandidate(normalized, label, execution_mode))
    return tuple(candidates)


def remember_verified_baseline(
    python_executable: str,
    *,
    label: str,
    execution_mode: str = "default_metal",
    path: Path | None = None,
) -> None:
    """Persist a verified-safe MLX interpreter baseline."""

    normalized = str(Path(python_executable).expanduser())
    target = path or verified_baseline_file_path()
    current = list(load_verified_baselines(path=target))
    kept = [
        candidate
        for candidate in current
        if candidate_identity(candidate.python_executable, candidate.execution_mode)
        != candidate_identity(normalized, execution_mode)
    ]
    kept.insert(0, MlxEnvironmentCandidate(normalized, label, execution_mode))
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "executables": [
            {
                "python_executable": candidate.python_executable,
                "label": candidate.label,
                "execution_mode": candidate.execution_mode,
            }
            for candidate in kept
        ]
    }
    target.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def is_known_unsafe_python(python_executable: str) -> bool:
    """Return whether this executable is already known unsafe for default Metal."""

    return is_known_unsafe_python_with_path(python_executable)


def is_known_unsafe_python_with_path(
    python_executable: str,
    *,
    execution_mode: str = "default_metal",
    quarantine_path: Path | None = None,
) -> bool:
    """Return whether this interpreter-mode pair is known unsafe."""

    normalized = str(Path(python_executable).expanduser())
    if execution_mode == "default_metal" and any(
        normalized.endswith(suffix) for suffix in _KNOWN_UNSAFE_EXECUTABLE_SUFFIXES
    ):
        return True
    return candidate_identity(normalized, execution_mode) in load_quarantined_pythons(
        path=quarantine_path
    )


def default_environment_candidates(
    *,
    preferred_execution_mode: str = "default_metal",
) -> tuple[MlxEnvironmentCandidate, ...]:
    """Return the safe default candidate set."""

    candidates: list[MlxEnvironmentCandidate] = []
    seen: set[str] = set()

    for candidate in load_verified_baselines():
        effective_mode = preferred_execution_mode
        identity = candidate_identity(candidate.python_executable, effective_mode)
        if identity in seen or not Path(candidate.python_executable).exists():
            continue
        if is_known_unsafe_python_with_path(
            candidate.python_executable,
            execution_mode=effective_mode,
        ):
            continue
        seen.add(identity)
        candidates.append(
            MlxEnvironmentCandidate(
                candidate.python_executable,
                candidate.label,
                effective_mode,
            )
        )

    current = str(Path(sys.executable).expanduser())
    identity = candidate_identity(current, preferred_execution_mode)
    if identity not in seen and not is_known_unsafe_python_with_path(
        current,
        execution_mode=preferred_execution_mode,
    ):
        candidates.append(
            MlxEnvironmentCandidate(current, "current", preferred_execution_mode)
        )
    return tuple(candidates)


def known_environment_candidates(
    *,
    preferred_execution_mode: str = "default_metal",
) -> tuple[MlxEnvironmentCandidate, ...]:
    """Return broader local candidates for explicit operator diagnostics."""

    baselines = load_verified_baselines()
    values: list[tuple[str, str, str]] = [
        *(
            (
                candidate.python_executable,
                candidate.label,
                preferred_execution_mode,
            )
            for candidate in baselines
        ),
        (sys.executable, "current", preferred_execution_mode),
        ("/Users/yeemio/AI/gitrep/owlmlx/.runtime1-mlx/bin/python", "runtime1-mlx", preferred_execution_mode),
        ("/Users/yeemio/AI/gitrep/owlmlx/.runtime2-mlx/bin/python", "runtime2-mlx", preferred_execution_mode),
        ("/Users/yeemio/AI/llm-infra/.venv/bin/python", "llm-infra", preferred_execution_mode),
        ("/Users/yeemio/AI/gitrep/owlmlx/.venv/bin/python", "owlmlx-venv", preferred_execution_mode),
        ("/opt/homebrew/bin/python3", "homebrew-python3", preferred_execution_mode),
    ]
    seen: set[str] = set()
    candidates: list[MlxEnvironmentCandidate] = []
    for executable, label, execution_mode in values:
        identity = candidate_identity(executable, execution_mode)
        if not executable or identity in seen:
            continue
        seen.add(identity)
        candidates.append(MlxEnvironmentCandidate(executable, label, execution_mode))
    return tuple(candidates)


def probe_mlx_environments(
    candidates: tuple[MlxEnvironmentCandidate, ...],
    *,
    timeout_s: float = 20.0,
    quarantine_path: Path | None = None,
) -> tuple[MlxEnvironmentProbe, ...]:
    """Probe all candidates in order."""

    probes: list[MlxEnvironmentProbe] = []
    for candidate in candidates:
        if is_known_unsafe_python_with_path(
            candidate.python_executable,
            execution_mode=candidate.execution_mode,
            quarantine_path=quarantine_path,
        ):
            reason = load_quarantined_pythons(path=quarantine_path).get(
                candidate_identity(candidate.python_executable, candidate.execution_mode),
                "previous import probe aborted during Metal initialization",
            )
            result = MlxLmImportProbeResult(
                ok=False,
                returncode=-6,
                stdout="",
                stderr=f"known unsafe MLX environment: {reason}",
                message="skipped known unsafe mlx-lm python environment",
            )
        else:
            result = probe_mlx_lm_import(
                python_executable=candidate.python_executable,
                timeout_s=timeout_s,
                execution_mode=candidate.execution_mode,
            )
            if result.returncode == -6:
                remember_quarantined_python(
                    candidate.python_executable,
                    execution_mode=candidate.execution_mode,
                    reason="import probe aborted during Metal initialization",
                    path=quarantine_path,
                )
        probes.append(MlxEnvironmentProbe(candidate=candidate, result=result))
    return tuple(probes)


def select_mlx_environment(
    candidates: tuple[MlxEnvironmentCandidate, ...],
    *,
    timeout_s: float = 20.0,
    quarantine_path: Path | None = None,
) -> MlxEnvironmentSelection:
    """Select the first candidate that can import mlx-lm safely."""

    probes = probe_mlx_environments(
        candidates,
        timeout_s=timeout_s,
        quarantine_path=quarantine_path,
    )
    selected = next((probe for probe in probes if probe.usable), None)
    if selected is not None:
        return MlxEnvironmentSelection(
            selected=selected,
            probes=probes,
            message=(
                "selected mlx environment: "
                f"{selected.candidate.label} ({selected.candidate.python_executable}, "
                f"{selected.candidate.execution_mode})"
            ),
        )
    return MlxEnvironmentSelection(
        selected=None,
        probes=probes,
        message="no usable mlx-lm python environment found",
    )


def probe_to_dict(probe: MlxEnvironmentProbe) -> dict[str, object]:
    """Serialize a single probe result."""

    return {
        "label": probe.candidate.label,
        "python_executable": probe.candidate.python_executable,
        "execution_mode": probe.candidate.execution_mode,
        "usable": probe.usable,
        "returncode": probe.result.returncode,
        "stdout": probe.result.stdout,
        "stderr": probe.result.stderr,
        "message": probe.result.message,
    }


def selection_to_dict(selection: MlxEnvironmentSelection) -> dict[str, object]:
    """Serialize a selection result."""

    return {
        "ok": selection.ok,
        "message": selection.message,
        "selected": (
            probe_to_dict(selection.selected) if selection.selected is not None else None
        ),
        "probes": [probe_to_dict(probe) for probe in selection.probes],
    }


def build_mlx_environment_readiness(
    *,
    include_known_candidates: bool = False,
    preferred_execution_mode: str = "default_metal",
    timeout_s: float = 20.0,
    quarantine_path: Path | None = None,
) -> MlxEnvironmentReadiness:
    """Build a stable MLX environment readiness view."""

    candidates = (
        known_environment_candidates(preferred_execution_mode=preferred_execution_mode)
        if include_known_candidates
        else default_environment_candidates(preferred_execution_mode=preferred_execution_mode)
    )
    selection = select_mlx_environment(
        candidates,
        timeout_s=timeout_s,
        quarantine_path=quarantine_path,
    )
    quarantine = load_quarantined_pythons(path=quarantine_path)
    blocked_reason: str | None = None
    if not selection.ok:
        if not candidates:
            blocked_reason = "no safe default mlx-lm python candidates available"
        else:
            blocked_reason = "no usable mlx-lm python environment found"
    return MlxEnvironmentReadiness(
        selection=selection,
        include_known_candidates=include_known_candidates,
        preferred_execution_mode=preferred_execution_mode,
        quarantine_count=len(quarantine),
        blocked_reason=blocked_reason,
    )


def readiness_to_dict(readiness: MlxEnvironmentReadiness) -> dict[str, object]:
    """Serialize MLX environment readiness as a stable upstream contract."""

    selected = readiness.selection.selected
    return {
        "contract": {
            "surface": "owlmlx.mlx_environment",
            "version": "stabilization2",
            "stable_sections": [
                "summary",
                "selection",
                "quarantine",
            ],
            "diagnostic_sections": [
                "probes",
            ],
        },
        "summary": {
            "readiness": "ready" if readiness.ok else "blocked",
            "message": readiness.selection.message,
            "blocked_reason": readiness.blocked_reason,
            "include_known_candidates": readiness.include_known_candidates,
            "preferred_execution_mode": readiness.preferred_execution_mode,
            "candidate_count": len(readiness.selection.probes),
        },
        "selection": {
            "ok": readiness.ok,
            "selected_label": selected.candidate.label if selected is not None else None,
            "execution_mode": (
                selected.candidate.execution_mode if selected is not None else None
            ),
            "python_executable": (
                selected.candidate.python_executable if selected is not None else None
            ),
        },
        "quarantine": {
            "count": readiness.quarantine_count,
        },
        "probes": [probe_to_dict(probe) for probe in readiness.selection.probes],
    }


def build_mlx_import_blocker_report(
    *,
    include_known_candidates: bool = True,
    preferred_execution_mode: str = "default_metal",
    timeout_s: float = 20.0,
    quarantine_path: Path | None = None,
) -> MlxImportBlockerReport:
    """Build a stable machine-level MLX import blocker report."""

    readiness = build_mlx_environment_readiness(
        include_known_candidates=include_known_candidates,
        preferred_execution_mode=preferred_execution_mode,
        timeout_s=timeout_s,
        quarantine_path=quarantine_path,
    )
    return MlxImportBlockerReport(
        readiness=readiness,
        quarantine_file=str(quarantine_path or quarantine_file_path()),
    )


def blocker_report_to_dict(report: MlxImportBlockerReport) -> dict[str, object]:
    """Serialize the machine-level MLX import blocker report."""

    readiness = readiness_to_dict(report.readiness)
    return {
        "contract": {
            "surface": "owlmlx.mlx_blocker_report",
            "version": "stabilization2",
            "stable_sections": [
                "summary",
                "readiness",
                "quarantine",
            ],
            "diagnostic_sections": [
                "readiness.probes",
            ],
        },
        "summary": {
            "blocked": report.blocked,
            "blocked_reason": report.readiness.blocked_reason,
            "quarantined_executables": report.readiness.quarantine_count,
        },
        "readiness": readiness,
        "quarantine": {
            "file": report.quarantine_file,
        },
    }


def default_crash_report_directory() -> Path:
    """Return the default macOS crash report directory."""

    return Path.home() / "Library" / "Logs" / "DiagnosticReports"


def _extract_path_from_used_images(images: object, image_name: str) -> str | None:
    if not isinstance(images, list):
        return None
    for image in images:
        if not isinstance(image, dict):
            continue
        if image.get("name") == image_name and isinstance(image.get("path"), str):
            return str(image["path"])
    return None


def parse_mlx_crash_report(path: Path) -> MlxCrashReportSummary | None:
    """Parse one `.ips` crash report if it matches the MLX import crash signature."""

    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except Exception:
        return None
    if len(lines) < 2:
        return None
    try:
        header = json.loads(lines[0])
        body = json.loads("\n".join(lines[1:]))
    except Exception:
        return None

    exception = body.get("exceptionReason", {})
    backtrace = body.get("lastExceptionBacktrace", [])
    if not isinstance(exception, dict) or not isinstance(backtrace, list):
        return None

    exception_name = exception.get("name")
    composed_message = exception.get("composed_message")
    mlx_symbol = next(
        (
            str(frame.get("symbol"))
            for frame in backtrace
            if isinstance(frame, dict)
            and isinstance(frame.get("symbol"), str)
            and "mlx::core::metal::Device::Device()" in str(frame.get("symbol"))
        ),
        None,
    )
    if exception_name != "NSRangeException" and mlx_symbol is None:
        return None

    top_symbol = None
    if backtrace and isinstance(backtrace[0], dict):
        symbol = backtrace[0].get("symbol")
        if isinstance(symbol, str):
            top_symbol = symbol

    signal = None
    if isinstance(body.get("exception"), dict):
        signal_value = body["exception"].get("signal")
        if isinstance(signal_value, str):
            signal = signal_value

    return MlxCrashReportSummary(
        path=str(path),
        timestamp=header.get("timestamp") if isinstance(header.get("timestamp"), str) else None,
        incident_id=header.get("incident_id") if isinstance(header.get("incident_id"), str) else None,
        signal=signal,
        exception_name=exception_name if isinstance(exception_name, str) else None,
        exception_message=composed_message if isinstance(composed_message, str) else None,
        top_symbol=top_symbol,
        mlx_symbol=mlx_symbol,
        os_version=header.get("os_version") if isinstance(header.get("os_version"), str) else None,
        model_code=body.get("modelCode") if isinstance(body.get("modelCode"), str) else None,
        python_path=_extract_path_from_used_images(body.get("usedImages"), "Python"),
    )


def find_recent_mlx_crash_reports(
    *,
    crash_report_directory: Path | None = None,
    limit: int = 5,
) -> tuple[MlxCrashReportSummary, ...]:
    """Return recent MLX import crash reports from local macOS diagnostics."""

    target = crash_report_directory or default_crash_report_directory()
    if not target.exists():
        return ()
    candidates = sorted(target.glob("Python-*.ips"), key=lambda p: p.stat().st_mtime, reverse=True)
    summaries: list[MlxCrashReportSummary] = []
    for candidate in candidates:
        parsed = parse_mlx_crash_report(candidate)
        if parsed is None:
            continue
        summaries.append(parsed)
        if len(summaries) >= limit:
            break
    return tuple(summaries)


def crash_report_to_dict(report: MlxCrashReportSummary) -> dict[str, object]:
    """Serialize one crash report summary."""

    return {
        "path": report.path,
        "timestamp": report.timestamp,
        "incident_id": report.incident_id,
        "signal": report.signal,
        "exception_name": report.exception_name,
        "exception_message": report.exception_message,
        "top_symbol": report.top_symbol,
        "mlx_symbol": report.mlx_symbol,
        "os_version": report.os_version,
        "model_code": report.model_code,
        "python_path": report.python_path,
    }


def build_mlx_host_forensics_report(
    *,
    include_known_candidates: bool = True,
    preferred_execution_mode: str = "default_metal",
    timeout_s: float = 20.0,
    quarantine_path: Path | None = None,
    crash_report_directory: Path | None = None,
    crash_limit: int = 5,
) -> MlxHostForensicsReport:
    """Build a host-level MLX crash forensics report."""

    readiness = build_mlx_environment_readiness(
        include_known_candidates=include_known_candidates,
        preferred_execution_mode=preferred_execution_mode,
        timeout_s=timeout_s,
        quarantine_path=quarantine_path,
    )
    return MlxHostForensicsReport(
        readiness=readiness,
        crash_reports=find_recent_mlx_crash_reports(
            crash_report_directory=crash_report_directory,
            limit=crash_limit,
        ),
        crash_report_directory=str(crash_report_directory or default_crash_report_directory()),
    )


def host_forensics_to_dict(report: MlxHostForensicsReport) -> dict[str, object]:
    """Serialize host-level MLX crash forensics report."""

    return {
        "contract": {
            "surface": "owlmlx.mlx_host_forensics",
            "version": "stabilization2",
            "stable_sections": [
                "summary",
                "readiness",
                "crash_reports",
            ],
            "diagnostic_sections": [],
        },
        "summary": {
            "blocked": report.blocked,
            "crash_report_count": len(report.crash_reports),
            "crash_report_directory": report.crash_report_directory,
        },
        "readiness": readiness_to_dict(report.readiness),
        "crash_reports": [crash_report_to_dict(item) for item in report.crash_reports],
    }
