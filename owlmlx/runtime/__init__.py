"""Executable runtime kernel package for owlmlx."""

from .backends import FakeBackend, RuntimeBackend
from .kernel import RuntimeKernel
from .mlx_environment import (
    MlxEnvironmentCandidate,
    MlxEnvironmentProbe,
    MlxEnvironmentSelection,
    default_environment_candidates,
    known_environment_candidates,
    probe_mlx_environments,
    probe_to_dict,
    select_mlx_environment,
    selection_to_dict,
)
from .mlx_lm_backend import MlxLmBackend
from .mlx_lm_subprocess_backend import MlxLmSubprocessBackend
from .types import (
    BackendStatus,
    GenerateResult,
    LoadResult,
    LoadedModelInfo,
    RestartResult,
    RuntimeErrorCode,
    RuntimeOperationResult,
    RuntimeStatus,
    StreamEvent,
    UnloadResult,
)

__all__ = [
    "BackendStatus",
    "FakeBackend",
    "GenerateResult",
    "LoadResult",
    "LoadedModelInfo",
    "RestartResult",
    "MlxEnvironmentCandidate",
    "MlxEnvironmentProbe",
    "MlxEnvironmentSelection",
    "MlxLmBackend",
    "MlxLmSubprocessBackend",
    "RuntimeBackend",
    "RuntimeErrorCode",
    "RuntimeKernel",
    "RuntimeOperationResult",
    "RuntimeStatus",
    "StreamEvent",
    "UnloadResult",
    "default_environment_candidates",
    "known_environment_candidates",
    "probe_mlx_environments",
    "probe_to_dict",
    "select_mlx_environment",
    "selection_to_dict",
]
