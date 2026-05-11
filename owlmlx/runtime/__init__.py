"""Executable runtime kernel package for owlmlx.

After Stage 1 c2 scrub: only sibling-module imports (`from .X`).
Parent-package spec re-exports removed; consumers should import
spec modules directly from `owlmlx.X` when needed.
"""

from .backends import FakeBackend, RuntimeBackend
from .first_smoke_decision import LargeWeightFirstSmokeDecision, build_large_weight_first_smoke_decision, first_smoke_decision_to_dict
from .host_stability import HostStableExecutionStatus, build_host_stable_execution_status, host_stability_to_dict
from .kernel import RuntimeKernel
from .mlx_environment import MlxEnvironmentCandidate, MlxCrashReportSummary, MlxImportBlockerReport, MlxEnvironmentProbe, MlxEnvironmentReadiness, MlxEnvironmentSelection, MlxHostForensicsReport, blocker_report_to_dict, build_mlx_host_forensics_report, build_mlx_environment_readiness, build_mlx_import_blocker_report, crash_report_to_dict, default_environment_candidates, find_recent_mlx_crash_reports, host_forensics_to_dict, load_verified_baselines, known_environment_candidates, parse_mlx_crash_report, probe_mlx_environments, probe_to_dict, remember_verified_baseline, readiness_to_dict, select_mlx_environment, selection_to_dict, verified_baseline_file_path
from .mlx_lm_backend import MlxLmBackend
from .mlx_lm_subprocess_backend import MlxLmSubprocessBackend
from .specimen_gate import LargeWeightSpecimenGate, SpecimenPathAssessment, assess_specimen_path, build_large_weight_specimen_gate, specimen_gate_to_dict
from .types import BackendStatus, ChatTurn, GenerateResult, LoadResult, LoadedModelInfo, RestartResult, RuntimeErrorCode, RuntimeOperationResult, RuntimeStatus, StreamEvent, UnloadResult

__all__ = [
    "BackendStatus",
    "ChatTurn",
    "FakeBackend",
    "GenerateResult",
    "HostStableExecutionStatus",
    "LargeWeightFirstSmokeDecision",
    "LargeWeightSpecimenGate",
    "LoadResult",
    "LoadedModelInfo",
    "MlxCrashReportSummary",
    "MlxEnvironmentCandidate",
    "MlxEnvironmentProbe",
    "MlxEnvironmentReadiness",
    "MlxEnvironmentSelection",
    "MlxHostForensicsReport",
    "MlxImportBlockerReport",
    "MlxLmBackend",
    "MlxLmSubprocessBackend",
    "RestartResult",
    "RuntimeBackend",
    "RuntimeErrorCode",
    "RuntimeKernel",
    "RuntimeOperationResult",
    "RuntimeStatus",
    "SpecimenPathAssessment",
    "StreamEvent",
    "UnloadResult",
    "assess_specimen_path",
    "blocker_report_to_dict",
    "build_host_stable_execution_status",
    "build_large_weight_first_smoke_decision",
    "build_large_weight_specimen_gate",
    "build_mlx_environment_readiness",
    "build_mlx_host_forensics_report",
    "build_mlx_import_blocker_report",
    "crash_report_to_dict",
    "default_environment_candidates",
    "find_recent_mlx_crash_reports",
    "first_smoke_decision_to_dict",
    "host_forensics_to_dict",
    "host_stability_to_dict",
    "known_environment_candidates",
    "load_verified_baselines",
    "parse_mlx_crash_report",
    "probe_mlx_environments",
    "probe_to_dict",
    "readiness_to_dict",
    "remember_verified_baseline",
    "select_mlx_environment",
    "selection_to_dict",
    "specimen_gate_to_dict",
    "verified_baseline_file_path",
]
