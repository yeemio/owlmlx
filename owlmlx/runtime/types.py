"""Runtime kernel data contracts.

These are executable-runtime contracts, not standalone schema extraction.
They are used by RuntimeKernel and backend adapters to exchange load,
generation, unload, and status results.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


@dataclass(frozen=True, slots=True)
class ChatTurn:
    """A structured chat message passed through runtime layers."""

    role: str
    content: str

    def __post_init__(self) -> None:
        if not self.role:
            raise ValueError("role must be non-empty")
        if not self.content:
            raise ValueError("content must be non-empty")


class RuntimeErrorCode(str, Enum):
    """Canonical runtime operation error codes."""

    model_not_loaded = "model_not_loaded"
    model_already_loaded = "model_already_loaded"
    model_not_found = "model_not_found"
    memory_budget_exceeded = "memory_budget_exceeded"
    backend_error = "backend_error"
    invalid_request = "invalid_request"
    model_pinned = "model_pinned"


@dataclass(frozen=True, slots=True)
class LoadedModelInfo:
    """A model currently loaded by a runtime backend."""

    model_id: str
    memory_gb: float
    backend: str
    loaded_at: float | None = None

    def __post_init__(self) -> None:
        if not self.model_id:
            raise ValueError("model_id must be non-empty")
        object.__setattr__(self, "memory_gb", max(float(self.memory_gb or 0.0), 0.0))


@dataclass(frozen=True, slots=True)
class RuntimeOperationResult:
    """Base result shape for runtime operations."""

    ok: bool
    message: str
    error_code: RuntimeErrorCode | None = None
    detail: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class LoadResult(RuntimeOperationResult):
    """Result of loading a model."""

    model: LoadedModelInfo | None = None


@dataclass(frozen=True, slots=True)
class GenerateResult(RuntimeOperationResult):
    """Result of a generation call."""

    model_id: str | None = None
    text: str = ""
    finish_reason: str | None = None
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    wait_time_s: float | None = None
    execution_time_s: float | None = None
    was_queued: bool = False


@dataclass(frozen=True, slots=True)
class StreamEvent:
    """A single event emitted during streaming generation."""

    event: str
    model_id: str | None = None
    text: str = ""
    error_code: RuntimeErrorCode | None = None
    finish_reason: str | None = None
    sequence: int | None = None
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    wait_time_s: float | None = None
    execution_time_s: float | None = None
    was_queued: bool = False
    detail: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class StreamStart:
    """Queue timing metadata for a streaming generation session."""

    wait_time_s: float
    was_queued: bool


@dataclass(frozen=True, slots=True)
class UnloadResult(RuntimeOperationResult):
    """Result of unloading a model."""

    model_id: str | None = None
    freed_gb: float = 0.0


@dataclass(frozen=True, slots=True)
class RestartResult(RuntimeOperationResult):
    """Result of restarting a loaded model."""

    model_id: str | None = None
    restarted_model: LoadedModelInfo | None = None
    stage: str | None = None
    retryable: bool | None = None


@dataclass(frozen=True, slots=True)
class PinResult(RuntimeOperationResult):
    """Result of pinning or unpinning a loaded model."""

    model_id: str | None = None
    pinned: bool | None = None


@dataclass(frozen=True, slots=True)
class TTLPolicyResult(RuntimeOperationResult):
    """Result of configuring or clearing a model TTL policy."""

    model_id: str | None = None
    ttl_enabled: bool | None = None
    ttl_seconds: float | None = None


@dataclass(frozen=True, slots=True)
class TTLSweepResult(RuntimeOperationResult):
    """Result of explicitly sweeping expired TTL-controlled models."""

    scanned_model_count: int = 0
    expired_model_ids: tuple[str, ...] = ()
    unloaded_model_ids: tuple[str, ...] = ()
    skipped_pinned_model_ids: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class BackendStatus:
    """Backend status snapshot used by RuntimeKernel."""

    backend_name: str
    healthy: bool
    loaded_models: tuple[LoadedModelInfo, ...] = ()
    detail: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class RuntimeStatus:
    """RuntimeKernel status snapshot."""

    backend: BackendStatus
    inventory: dict[str, Any]
    budget: dict[str, Any]
    health: dict[str, Any]
    generation_gate: dict[str, Any]
    active_model_id: str | None
