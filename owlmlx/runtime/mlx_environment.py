"""MLX runtime environment probing and selection helpers."""

from __future__ import annotations

import sys
from dataclasses import dataclass

from .mlx_lm_backend import MlxLmImportProbeResult, probe_mlx_lm_import


@dataclass(frozen=True, slots=True)
class MlxEnvironmentCandidate:
    """A Python executable candidate for mlx-lm subprocess execution."""

    python_executable: str
    label: str


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


def default_environment_candidates() -> tuple[MlxEnvironmentCandidate, ...]:
    """Return the safe default candidate set.

    Default probing must not touch known MLX-oriented virtualenvs automatically.
    Some local environments are already known to abort inside Metal initialization
    during ``import mlx_lm``. Those candidates remain available through the
    explicit helper below, but the default path stays conservative.
    """

    return (
        MlxEnvironmentCandidate(sys.executable, "current"),
    )


def known_environment_candidates() -> tuple[MlxEnvironmentCandidate, ...]:
    """Return broader local candidates for explicit operator diagnostics."""

    values: list[tuple[str, str]] = [
        (sys.executable, "current"),
        ("/Users/yeemio/AI/llm-infra/.venv/bin/python", "llm-infra"),
        ("/Users/yeemio/AI/gitrep/owlmlx/.venv/bin/python", "owlmlx-venv"),
        ("/opt/homebrew/bin/python3", "homebrew-python3"),
    ]
    seen: set[str] = set()
    candidates: list[MlxEnvironmentCandidate] = []
    for executable, label in values:
        if not executable or executable in seen:
            continue
        seen.add(executable)
        candidates.append(
            MlxEnvironmentCandidate(
                python_executable=executable,
                label=label,
            )
        )
    return tuple(candidates)


def probe_mlx_environments(
    candidates: tuple[MlxEnvironmentCandidate, ...],
    *,
    timeout_s: float = 20.0,
) -> tuple[MlxEnvironmentProbe, ...]:
    """Probe all candidates in order."""

    probes: list[MlxEnvironmentProbe] = []
    for candidate in candidates:
        result = probe_mlx_lm_import(
            python_executable=candidate.python_executable,
            timeout_s=timeout_s,
        )
        probes.append(MlxEnvironmentProbe(candidate=candidate, result=result))
    return tuple(probes)


def select_mlx_environment(
    candidates: tuple[MlxEnvironmentCandidate, ...],
    *,
    timeout_s: float = 20.0,
) -> MlxEnvironmentSelection:
    """Select the first candidate that can import mlx-lm safely."""

    probes = probe_mlx_environments(candidates, timeout_s=timeout_s)
    selected = next((probe for probe in probes if probe.usable), None)
    if selected is not None:
        return MlxEnvironmentSelection(
            selected=selected,
            probes=probes,
            message=(
                "selected mlx environment: "
                f"{selected.candidate.label} ({selected.candidate.python_executable})"
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
