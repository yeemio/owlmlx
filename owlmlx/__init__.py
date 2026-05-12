"""owlmlx runtime helpers.

Public API surface. After Stage 1 the spec-as-code layer is archived;
only imports from runtime-reachable modules remain.
"""

from .abort_recovery import MAX_ABORT_HISTORY, SNAPSHOT_RECENT_ABORTS, AbortEvent, AbortRecoveryTracker, SubstrateState
from .cache_truth import CACHE_CLI_FLAGS, CACHE_ENV_KEYS, HIGH_TURBOQUANT_CACHE_SAFETY_RISK, SAFE_TURBOQUANT_ADOPTION_REQUIREMENTS, CacheFlags, CacheProfile, CacheProfileSnapshot, TurboQuantCacheSafety, cache_flags_to_dict, cache_profile_from_flags, cache_profile_snapshot, cache_profile_snapshot_to_dict, cache_restart_required, extract_cache_cli_flags, normalize_cache_flags, normalize_cache_profile, turboquant_cache_safety, turboquant_cache_safety_to_dict
from .cache_scheduler_status import CacheSchedulerStatus, build_cache_scheduler_status, cache_scheduler_status_to_dict
from .context_concurrency import CONCURRENCY_GATE, HIGH_CONTEXT_THRESHOLD_TOKENS, ConcurrencyGateEntry, concurrency_gate_snapshot, gate_entry_for_context, is_high_context, max_concurrency_for_context
from .memory_budget import BudgetEvaluation, BudgetVerdict, MachineMemoryProfile, budget_snapshot, default_machine_profile, evaluate_model_fit
from .memory_watermark import GREEN_CEILING, MemoryWatermark, RED_CEILING, WATERMARK_THRESHOLDS, WatermarkAction, YELLOW_CEILING
from .model_inventory import LoadedModelEntry, ModelInventorySnapshot, inventory_budget_check, inventory_currently_loaded_gb, inventory_entry_for_model, inventory_health_snapshot, inventory_load_state_for_model, inventory_model_ids, inventory_to_dict, inventory_truth_level_for_model, normalize_inventory_entry, normalize_inventory_snapshot
from .model_lineage import LINEAGE_REQUIRED_FIELDS, RELAXED_LINEAGE_FIELDS, STRICT_LINEAGE_STATES, LineageChangeType, LineageValidationResult, ModelLineage, TruthInheritance, TruthInheritanceLevel, derive_lineage_change_type, derive_truth_inheritance, lineage_from_artifact_metadata, model_lineage_to_dict, normalize_model_lineage, truth_inheritance_for_change, validate_model_lineage
from .runtime import BackendStatus, FakeBackend, LoadResult, MlxEnvironmentCandidate, MlxEnvironmentProbe, MlxEnvironmentSelection, MlxLmBackend, MlxLmSubprocessBackend, RuntimeBackend, RuntimeErrorCode, RuntimeKernel, UnloadResult, default_environment_candidates, known_environment_candidates, probe_mlx_environments, probe_to_dict, select_mlx_environment, selection_to_dict
from .serving import GenerationGate, GenerationResult, MAX_GENERATION_CONCURRENCY

__all__ = [
    "AbortEvent",
    "AbortRecoveryTracker",
    "BudgetEvaluation",
    "BudgetVerdict",
    "GREEN_CEILING",
    "MemoryWatermark",
    "RED_CEILING",
    "WATERMARK_THRESHOLDS",
    "WatermarkAction",
    "YELLOW_CEILING",
    "CACHE_CLI_FLAGS",
    "CACHE_ENV_KEYS",
    "CONCURRENCY_GATE",
    "CacheFlags",
    "CacheProfile",
    "CacheProfileSnapshot",
    "CacheSchedulerStatus",
    "ConcurrencyGateEntry",
    "GenerationGate",
    "GenerationResult",
    "HIGH_CONTEXT_THRESHOLD_TOKENS",
    "HIGH_TURBOQUANT_CACHE_SAFETY_RISK",
    "LINEAGE_REQUIRED_FIELDS",
    "LineageChangeType",
    "LineageValidationResult",
    "LoadedModelEntry",
    "MAX_ABORT_HISTORY",
    "MAX_GENERATION_CONCURRENCY",
    "MachineMemoryProfile",
    "ModelInventorySnapshot",
    "ModelLineage",
    "RELAXED_LINEAGE_FIELDS",
    "SAFE_TURBOQUANT_ADOPTION_REQUIREMENTS",
    "SNAPSHOT_RECENT_ABORTS",
    "STRICT_LINEAGE_STATES",
    "SubstrateState",
    "TruthInheritance",
    "TruthInheritanceLevel",
    "TurboQuantCacheSafety",
    "budget_snapshot",
    "build_cache_scheduler_status",
    "cache_flags_to_dict",
    "cache_profile_from_flags",
    "cache_profile_snapshot",
    "cache_profile_snapshot_to_dict",
    "cache_restart_required",
    "cache_scheduler_status_to_dict",
    "concurrency_gate_snapshot",
    "default_machine_profile",
    "derive_lineage_change_type",
    "derive_truth_inheritance",
    "evaluate_model_fit",
    "extract_cache_cli_flags",
    "gate_entry_for_context",
    "inventory_budget_check",
    "inventory_currently_loaded_gb",
    "inventory_entry_for_model",
    "inventory_health_snapshot",
    "inventory_load_state_for_model",
    "inventory_model_ids",
    "inventory_to_dict",
    "inventory_truth_level_for_model",
    "is_high_context",
    "lineage_from_artifact_metadata",
    "max_concurrency_for_context",
    "model_lineage_to_dict",
    "normalize_cache_flags",
    "normalize_cache_profile",
    "normalize_inventory_entry",
    "normalize_inventory_snapshot",
    "normalize_model_lineage",
    "truth_inheritance_for_change",
    "turboquant_cache_safety",
    "turboquant_cache_safety_to_dict",
    "validate_model_lineage",
]
