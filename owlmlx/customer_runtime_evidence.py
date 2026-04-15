"""Runtime-owned customer runtime evidence ledger for owlmlx."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .cache_closure_rung import CacheClosureRung, build_cache_closure_rung
from .cache_counter_gap import CacheCounterGap, build_cache_counter_gap
from .cache_counter_feasibility import (
    CacheCounterFeasibility,
    build_cache_counter_feasibility,
)
from .cache_scheduler_turboquant_split import (
    CacheSchedulerTurboQuantSplit,
    build_cache_scheduler_turboquant_split,
)
from .cache_scheduler_floor_gap import (
    CacheSchedulerFloorGap,
    build_cache_scheduler_floor_gap,
)
from .cache_scheduler_implementation_backlog import (
    CacheSchedulerImplementationBacklog,
    build_cache_scheduler_implementation_backlog,
)
from .cache_scheduler_branch_selection import (
    CacheSchedulerBranchSelection,
    build_cache_scheduler_branch_selection,
)
from .cache_continuous_batching_feasibility import (
    CacheContinuousBatchingFeasibility,
    build_cache_continuous_batching_feasibility,
)
from .cache_batching_mechanism_subgap import (
    CacheBatchingMechanismSubgap,
    build_cache_batching_mechanism_subgap,
)
from .cache_request_aggregation_window_exactness import (
    CacheRequestAggregationWindowExactness,
    build_cache_request_aggregation_window_exactness,
)
from .cache_pre_gate_cohort_window_feasibility import (
    CachePreGateCohortWindowFeasibility,
    build_cache_pre_gate_cohort_window_feasibility,
)
from .cache_turboquant_preconditions_gap import (
    CacheTurboQuantPreconditionsGap,
    build_cache_turboquant_preconditions_gap,
)
from .dominant_gap_reselection import (
    DominantGapReselection,
    build_dominant_gap_reselection,
)
from .heavy_weight_repeatability_status import (
    HeavyWeightRuntimeRepeatabilityStatus,
    build_heavy_weight_runtime_repeatability_status,
)
from .multi_model_governance_status import (
    MultiModelGovernanceStatus,
    build_multi_model_governance_status,
)
from .multi_model_governance_controls import (
    MultiModelGovernanceControls,
    build_multi_model_governance_controls,
)
from .multi_model_governance_transition_ledger import (
    MultiModelGovernanceTransitionLedger,
    build_multi_model_governance_transition_ledger,
)
from .multi_model_governance_policy_gap import (
    MultiModelGovernancePolicyGap,
    build_multi_model_governance_policy_gap,
)


def build_host_stable_execution_status(**kwargs: Any) -> object:
    """Lazy wrapper kept at module scope to avoid runtime package import cycles."""

    from .runtime.host_stability import build_host_stable_execution_status as _build

    return _build(**kwargs)

_VERIFICATION_ASSETS: dict[str, dict[str, list[str]]] = {
    "host_stable_execution": {
        "tests": [
            "tests/test_host_stability.py",
            "tests/test_mlx_environment.py",
            "tests/test_mlx_host_forensics.py",
        ],
        "scripts": [
            "scripts/runtime_host_stable_execution_status.py",
        ],
    },
    "cache_scheduler_depth": {
        "tests": [
            "tests/test_cache_closure_rung.py",
            "tests/test_cache_counter_gap.py",
            "tests/test_cache_counter_feasibility.py",
            "tests/test_cache_scheduler_turboquant_split.py",
            "tests/test_cache_scheduler_floor_gap.py",
            "tests/test_cache_scheduler_implementation_backlog.py",
            "tests/test_cache_scheduler_branch_selection.py",
            "tests/test_cache_continuous_batching_feasibility.py",
            "tests/test_cache_batching_mechanism_subgap.py",
            "tests/test_cache_request_aggregation_window_exactness.py",
            "tests/test_cache_pre_gate_cohort_window_feasibility.py",
            "tests/test_cache_turboquant_preconditions_gap.py",
            "tests/test_cache_repeatability_evidence.py",
            "tests/test_turboquant_readiness.py",
            "tests/test_mlx_lm_subprocess_backend.py",
        ],
        "scripts": [
            "scripts/runtime_cache_runtime_observation_harness.py",
            "scripts/runtime_cache_closure_rung.py",
            "scripts/runtime_cache_counter_gap.py",
            "scripts/runtime_cache_counter_feasibility.py",
            "scripts/runtime_cache_scheduler_turboquant_split.py",
            "scripts/runtime_cache_scheduler_floor_gap.py",
            "scripts/runtime_cache_scheduler_implementation_backlog.py",
            "scripts/runtime_cache_scheduler_branch_selection.py",
            "scripts/runtime_cache_continuous_batching_feasibility.py",
            "scripts/runtime_cache_batching_mechanism_subgap.py",
            "scripts/runtime_cache_request_aggregation_window_exactness.py",
            "scripts/runtime_cache_pre_gate_cohort_window_feasibility.py",
            "scripts/runtime_cache_turboquant_preconditions_gap.py",
            "scripts/runtime_turboquant_readiness.py",
        ],
    },
    "multi_model_lifecycle_governance": {
        "tests": [
            "tests/test_multi_model_governance_status.py",
            "tests/test_multi_model_governance_controls.py",
            "tests/test_multi_model_governance_transition_ledger.py",
            "tests/test_multi_model_governance_policy_gap.py",
            "tests/test_runtime_kernel.py",
        ],
        "scripts": [
            "scripts/runtime_multi_model_governance_status.py",
            "scripts/runtime_multi_model_governance_controls.py",
            "scripts/runtime_multi_model_governance_transition_ledger.py",
            "scripts/runtime_multi_model_governance_policy_gap.py",
        ],
    },
    "heavy_weight_runtime_repeatability": {
        "tests": [
            "tests/test_heavy_weight_repeatability_status.py",
            "tests/test_first_smoke_decision.py",
            "tests/test_specimen_gate.py",
        ],
        "scripts": [
            "scripts/runtime_heavy_weight_repeatability_status.py",
        ],
    },
}

_CONTRACT_SURFACES = {
    "host_stable_execution": "owlmlx.host_stable_execution",
    "cache_scheduler_depth": "owlmlx.cache_closure_rung",
    "cache_scheduler_depth_counter_gap": "owlmlx.cache_counter_gap",
    "cache_scheduler_depth_counter_feasibility": "owlmlx.cache_counter_feasibility",
    "cache_scheduler_depth_split": "owlmlx.cache_scheduler_turboquant_split",
    "cache_scheduler_depth_scheduler_floor": "owlmlx.cache_scheduler_floor_gap",
    "cache_scheduler_depth_scheduler_backlog": "owlmlx.cache_scheduler_implementation_backlog",
    "cache_scheduler_depth_scheduler_branch_selection": "owlmlx.cache_scheduler_branch_selection",
    "cache_scheduler_depth_continuous_batching_feasibility": "owlmlx.cache_continuous_batching_feasibility",
    "cache_scheduler_depth_batching_mechanism_subgap": "owlmlx.cache_batching_mechanism_subgap",
    "cache_scheduler_depth_request_aggregation_window_exactness": "owlmlx.cache_request_aggregation_window_exactness",
    "cache_scheduler_depth_pre_gate_cohort_window_feasibility": "owlmlx.cache_pre_gate_cohort_window_feasibility",
    "cache_scheduler_depth_turboquant_preconditions": "owlmlx.cache_turboquant_preconditions_gap",
    "multi_model_lifecycle_governance_controls": (
        "owlmlx.multi_model_governance_controls"
    ),
    "multi_model_lifecycle_governance_transition_ledger": (
        "owlmlx.multi_model_governance_transition_ledger"
    ),
    "multi_model_lifecycle_governance_policy_gap": (
        "owlmlx.multi_model_governance_policy_gap"
    ),
    "heavy_weight_runtime_repeatability": "owlmlx.heavy_weight_runtime_repeatability",
}


@dataclass(frozen=True, slots=True)
class CustomerRuntimeEvidenceLedger:
    """Stable runtime-owned evidence ledger for customer-grade runtime claims."""

    host_stability: object
    cache_closure: CacheClosureRung
    cache_counter_gap: CacheCounterGap
    cache_counter_feasibility: CacheCounterFeasibility
    cache_scheduler_turboquant_split: CacheSchedulerTurboQuantSplit
    cache_scheduler_floor_gap: CacheSchedulerFloorGap
    cache_scheduler_implementation_backlog: CacheSchedulerImplementationBacklog
    cache_scheduler_branch_selection: CacheSchedulerBranchSelection
    cache_continuous_batching_feasibility: CacheContinuousBatchingFeasibility
    cache_batching_mechanism_subgap: CacheBatchingMechanismSubgap
    cache_request_aggregation_window_exactness: CacheRequestAggregationWindowExactness
    cache_pre_gate_cohort_window_feasibility: CachePreGateCohortWindowFeasibility
    cache_turboquant_preconditions_gap: CacheTurboQuantPreconditionsGap
    dominant_gap_reselection: DominantGapReselection
    multi_model_governance: MultiModelGovernanceStatus
    multi_model_governance_controls: MultiModelGovernanceControls
    multi_model_governance_transition_ledger: MultiModelGovernanceTransitionLedger
    multi_model_governance_policy_gap: MultiModelGovernancePolicyGap
    heavy_weight_repeatability: HeavyWeightRuntimeRepeatabilityStatus
    status: str
    evidence_label: str
    externally_blocked_gaps: tuple[str, ...]
    internally_open_gaps: tuple[str, ...]
    dominant_next_gap: str
    exact_external_blocker: str | None
    blocked_reason: str | None
    recommended_next_step: str


def _coerce_host_status(
    value: object | None,
    *,
    include_known_candidates: bool,
    timeout_s: float,
    quarantine_path: Path | None,
    crash_report_directory: Path | None,
    crash_limit: int,
) -> object:
    if value is not None:
        return value
    return build_host_stable_execution_status(
        include_known_candidates=include_known_candidates,
        timeout_s=timeout_s,
        quarantine_path=quarantine_path,
        crash_report_directory=crash_report_directory,
        crash_limit=crash_limit,
    )


def _coerce_cache_closure(
    value: CacheClosureRung | None,
) -> CacheClosureRung:
    if isinstance(value, CacheClosureRung):
        return value
    return build_cache_closure_rung()


def _coerce_cache_counter_gap(
    value: CacheCounterGap | None,
    *,
    cache_closure: CacheClosureRung,
) -> CacheCounterGap:
    if isinstance(value, CacheCounterGap):
        return value
    return build_cache_counter_gap(closure=cache_closure)


def _coerce_cache_counter_feasibility(
    value: CacheCounterFeasibility | None,
    *,
    cache_counter_gap: CacheCounterGap,
) -> CacheCounterFeasibility:
    if isinstance(value, CacheCounterFeasibility):
        return value
    return build_cache_counter_feasibility(counter_gap=cache_counter_gap)


def _coerce_cache_scheduler_turboquant_split(
    value: CacheSchedulerTurboQuantSplit | None,
    *,
    cache_counter_feasibility: CacheCounterFeasibility,
    cache_closure: CacheClosureRung,
) -> CacheSchedulerTurboQuantSplit:
    if isinstance(value, CacheSchedulerTurboQuantSplit):
        return value
    scheduler = getattr(cache_closure, "scheduler", None)
    turboquant = getattr(cache_closure, "turboquant", None)
    return build_cache_scheduler_turboquant_split(
        counter_feasibility=cache_counter_feasibility,
        scheduler=scheduler,
        turboquant=turboquant,
    )


def _coerce_cache_scheduler_floor_gap(
    value: CacheSchedulerFloorGap | None,
    *,
    cache_scheduler_turboquant_split: CacheSchedulerTurboQuantSplit,
) -> CacheSchedulerFloorGap:
    if isinstance(value, CacheSchedulerFloorGap):
        return value
    return build_cache_scheduler_floor_gap(split=cache_scheduler_turboquant_split)


def _coerce_cache_scheduler_implementation_backlog(
    value: CacheSchedulerImplementationBacklog | None,
    *,
    cache_scheduler_floor_gap: CacheSchedulerFloorGap,
) -> CacheSchedulerImplementationBacklog:
    if isinstance(value, CacheSchedulerImplementationBacklog):
        return value
    return build_cache_scheduler_implementation_backlog(
        floor_gap=cache_scheduler_floor_gap
    )


def _coerce_cache_scheduler_branch_selection(
    value: CacheSchedulerBranchSelection | None,
    *,
    cache_scheduler_implementation_backlog: CacheSchedulerImplementationBacklog,
) -> CacheSchedulerBranchSelection:
    if isinstance(value, CacheSchedulerBranchSelection):
        return value
    return build_cache_scheduler_branch_selection(
        scheduler_backlog=cache_scheduler_implementation_backlog
    )


def _coerce_cache_continuous_batching_feasibility(
    value: CacheContinuousBatchingFeasibility | None,
    *,
    cache_scheduler_branch_selection: CacheSchedulerBranchSelection,
) -> CacheContinuousBatchingFeasibility:
    if isinstance(value, CacheContinuousBatchingFeasibility):
        return value
    return build_cache_continuous_batching_feasibility(
        branch_selection=cache_scheduler_branch_selection
    )


def _coerce_cache_batching_mechanism_subgap(
    value: CacheBatchingMechanismSubgap | None,
    *,
    cache_continuous_batching_feasibility: CacheContinuousBatchingFeasibility,
) -> CacheBatchingMechanismSubgap:
    if isinstance(value, CacheBatchingMechanismSubgap):
        return value
    return build_cache_batching_mechanism_subgap(
        feasibility=cache_continuous_batching_feasibility
    )


def _coerce_cache_request_aggregation_window_exactness(
    value: CacheRequestAggregationWindowExactness | None,
    *,
    cache_batching_mechanism_subgap: CacheBatchingMechanismSubgap,
) -> CacheRequestAggregationWindowExactness:
    if isinstance(value, CacheRequestAggregationWindowExactness):
        return value
    return build_cache_request_aggregation_window_exactness(
        mechanism_subgap=cache_batching_mechanism_subgap
    )


def _coerce_cache_pre_gate_cohort_window_feasibility(
    value: CachePreGateCohortWindowFeasibility | None,
    *,
    cache_request_aggregation_window_exactness: CacheRequestAggregationWindowExactness,
) -> CachePreGateCohortWindowFeasibility:
    if isinstance(value, CachePreGateCohortWindowFeasibility):
        return value
    return build_cache_pre_gate_cohort_window_feasibility(
        aggregation_exactness=cache_request_aggregation_window_exactness
    )


def _coerce_cache_turboquant_preconditions_gap(
    value: CacheTurboQuantPreconditionsGap | None,
    *,
    cache_closure: CacheClosureRung,
) -> CacheTurboQuantPreconditionsGap:
    if isinstance(value, CacheTurboQuantPreconditionsGap):
        return value
    return build_cache_turboquant_preconditions_gap(
        readiness=getattr(cache_closure, "turboquant", None)
    )


def _coerce_dominant_gap_reselection(
    value: DominantGapReselection | None,
    *,
    cache_scheduler_implementation_backlog: CacheSchedulerImplementationBacklog,
    cache_turboquant_preconditions_gap: CacheTurboQuantPreconditionsGap,
    multi_model_governance_policy_gap: MultiModelGovernancePolicyGap,
    heavy_weight_repeatability: HeavyWeightRuntimeRepeatabilityStatus,
) -> DominantGapReselection:
    if isinstance(value, DominantGapReselection):
        return value
    return build_dominant_gap_reselection(
        cache_scheduler_backlog=cache_scheduler_implementation_backlog,
        cache_turboquant_preconditions=cache_turboquant_preconditions_gap,
        governance_policy_gap=multi_model_governance_policy_gap,
        heavy_weight_repeatability=heavy_weight_repeatability,
    )


def _coerce_governance(
    value: MultiModelGovernanceStatus | None,
) -> MultiModelGovernanceStatus:
    if isinstance(value, MultiModelGovernanceStatus):
        return value
    return build_multi_model_governance_status()


def _coerce_governance_controls(
    value: MultiModelGovernanceControls | None,
) -> MultiModelGovernanceControls:
    if isinstance(value, MultiModelGovernanceControls):
        return value
    return build_multi_model_governance_controls()


def _coerce_governance_transition_ledger(
    value: MultiModelGovernanceTransitionLedger | None,
) -> MultiModelGovernanceTransitionLedger:
    if isinstance(value, MultiModelGovernanceTransitionLedger):
        return value
    return build_multi_model_governance_transition_ledger()


def _coerce_governance_policy_gap(
    value: MultiModelGovernancePolicyGap | None,
    *,
    controls: MultiModelGovernanceControls,
    transition_ledger: MultiModelGovernanceTransitionLedger,
) -> MultiModelGovernancePolicyGap:
    if isinstance(value, MultiModelGovernancePolicyGap):
        return value
    if hasattr(value, "policy_gap_rung"):
        return MultiModelGovernancePolicyGap(
            controls=controls,
            transition_ledger=transition_ledger,
            status=str(getattr(value, "status", "partial")),
            policy_gap_rung=str(
                getattr(value, "policy_gap_rung", "observation_gap_open")
            ),
            residual_blocker=getattr(value, "residual_blocker", None),
            recommended_next_step=str(
                getattr(
                    value,
                    "recommended_next_step",
                    "finish freezing runtime-owned governance observations before reducing the residual policy gap",
                )
            ),
            observed_runtime_behavior_frozen=bool(
                getattr(value, "observed_runtime_behavior_frozen", False)
            ),
            absent_policy_controls=tuple(
                getattr(
                    value,
                    "absent_policy_controls",
                    getattr(value, "policy_controls_absent", ()),
                )
            ),
            present_policy_controls=tuple(
                getattr(value, "present_policy_controls", ())
            ),
        )
    return build_multi_model_governance_policy_gap(
        controls=controls,
        transition_ledger=transition_ledger,
    )


def _coerce_heavy_weight(
    value: HeavyWeightRuntimeRepeatabilityStatus | None,
    *,
    specimen_path: str | None,
    include_known_candidates: bool,
    timeout_s: float,
    quarantine_path: Path | None,
    crash_report_directory: Path | None,
    crash_limit: int,
) -> HeavyWeightRuntimeRepeatabilityStatus:
    if isinstance(value, HeavyWeightRuntimeRepeatabilityStatus):
        return value
    if specimen_path is None:
        raise ValueError(
            "specimen_path is required when heavy_weight_repeatability is not provided"
        )
    return build_heavy_weight_runtime_repeatability_status(
        specimen_path=specimen_path,
        include_known_candidates=include_known_candidates,
        timeout_s=timeout_s,
        quarantine_path=quarantine_path,
        crash_report_directory=crash_report_directory,
        crash_limit=crash_limit,
    )


def _gap_entry(
    *,
    gap_id: str,
    surface: str,
    summary_status: str,
    closure_level: str,
    externally_blocked: bool,
    blocked_reason: str | None,
) -> dict[str, Any]:
    assets = _VERIFICATION_ASSETS[gap_id]
    return {
        "gap_id": gap_id,
        "contract_surface": surface,
        "contract_visible": True,
        "verification_visible": True,
        "verification": assets,
        "summary_status": summary_status,
        "closure_level": closure_level,
        "externally_blocked": externally_blocked,
        "blocked_reason": blocked_reason,
    }


def build_customer_runtime_evidence(
    *,
    specimen_path: str | None = None,
    host_stability: HostStableExecutionStatus | None = None,
    cache_closure: CacheClosureRung | None = None,
    cache_counter_gap: CacheCounterGap | None = None,
    cache_counter_feasibility: CacheCounterFeasibility | None = None,
    cache_scheduler_turboquant_split: CacheSchedulerTurboQuantSplit | None = None,
    cache_scheduler_floor_gap: CacheSchedulerFloorGap | None = None,
    cache_scheduler_implementation_backlog: CacheSchedulerImplementationBacklog | None = None,
    cache_scheduler_branch_selection: CacheSchedulerBranchSelection | None = None,
    cache_continuous_batching_feasibility: CacheContinuousBatchingFeasibility | None = None,
    cache_batching_mechanism_subgap: CacheBatchingMechanismSubgap | None = None,
    cache_request_aggregation_window_exactness: CacheRequestAggregationWindowExactness | None = None,
    cache_pre_gate_cohort_window_feasibility: CachePreGateCohortWindowFeasibility | None = None,
    cache_turboquant_preconditions_gap: CacheTurboQuantPreconditionsGap | None = None,
    dominant_gap_reselection: DominantGapReselection | None = None,
    multi_model_governance: MultiModelGovernanceStatus | None = None,
    multi_model_governance_controls: MultiModelGovernanceControls | None = None,
    multi_model_governance_transition_ledger: MultiModelGovernanceTransitionLedger | None = None,
    multi_model_governance_policy_gap: MultiModelGovernancePolicyGap | None = None,
    heavy_weight_repeatability: HeavyWeightRuntimeRepeatabilityStatus | None = None,
    include_known_candidates: bool = True,
    timeout_s: float = 20.0,
    quarantine_path: Path | None = None,
    crash_report_directory: Path | None = None,
    crash_limit: int = 5,
) -> CustomerRuntimeEvidenceLedger:
    """Build the runtime-owned customer evidence ledger."""

    host_status = _coerce_host_status(
        host_stability,
        include_known_candidates=include_known_candidates,
        timeout_s=timeout_s,
        quarantine_path=quarantine_path,
        crash_report_directory=crash_report_directory,
        crash_limit=crash_limit,
    )
    cache_status = _coerce_cache_closure(cache_closure)
    cache_counter_gap_status = _coerce_cache_counter_gap(
        cache_counter_gap,
        cache_closure=cache_status,
    )
    cache_counter_feasibility_status = _coerce_cache_counter_feasibility(
        cache_counter_feasibility,
        cache_counter_gap=cache_counter_gap_status,
    )
    cache_scheduler_turboquant_split_status = _coerce_cache_scheduler_turboquant_split(
        cache_scheduler_turboquant_split,
        cache_counter_feasibility=cache_counter_feasibility_status,
        cache_closure=cache_status,
    )
    cache_scheduler_floor_gap_status = _coerce_cache_scheduler_floor_gap(
        cache_scheduler_floor_gap,
        cache_scheduler_turboquant_split=cache_scheduler_turboquant_split_status,
    )
    cache_scheduler_implementation_backlog_status = (
        _coerce_cache_scheduler_implementation_backlog(
            cache_scheduler_implementation_backlog,
            cache_scheduler_floor_gap=cache_scheduler_floor_gap_status,
        )
    )
    cache_scheduler_branch_selection_status = _coerce_cache_scheduler_branch_selection(
        cache_scheduler_branch_selection,
        cache_scheduler_implementation_backlog=cache_scheduler_implementation_backlog_status,
    )
    cache_continuous_batching_feasibility_status = (
        _coerce_cache_continuous_batching_feasibility(
            cache_continuous_batching_feasibility,
            cache_scheduler_branch_selection=cache_scheduler_branch_selection_status,
        )
    )
    cache_batching_mechanism_subgap_status = _coerce_cache_batching_mechanism_subgap(
        cache_batching_mechanism_subgap,
        cache_continuous_batching_feasibility=cache_continuous_batching_feasibility_status,
    )
    cache_request_aggregation_window_exactness_status = (
        _coerce_cache_request_aggregation_window_exactness(
            cache_request_aggregation_window_exactness,
            cache_batching_mechanism_subgap=cache_batching_mechanism_subgap_status,
        )
    )
    cache_pre_gate_cohort_window_feasibility_status = (
        _coerce_cache_pre_gate_cohort_window_feasibility(
            cache_pre_gate_cohort_window_feasibility,
            cache_request_aggregation_window_exactness=cache_request_aggregation_window_exactness_status,
        )
    )
    cache_turboquant_preconditions_gap_status = (
        _coerce_cache_turboquant_preconditions_gap(
            cache_turboquant_preconditions_gap,
            cache_closure=cache_status,
        )
    )
    governance_status = _coerce_governance(multi_model_governance)
    governance_controls = _coerce_governance_controls(multi_model_governance_controls)
    governance_transition_ledger = _coerce_governance_transition_ledger(
        multi_model_governance_transition_ledger
    )
    governance_policy_gap = _coerce_governance_policy_gap(
        multi_model_governance_policy_gap,
        controls=governance_controls,
        transition_ledger=governance_transition_ledger,
    )
    heavy_weight_status = _coerce_heavy_weight(
        heavy_weight_repeatability,
        specimen_path=specimen_path,
        include_known_candidates=include_known_candidates,
        timeout_s=timeout_s,
        quarantine_path=quarantine_path,
        crash_report_directory=crash_report_directory,
        crash_limit=crash_limit,
    )
    dominant_gap_reselection_status = _coerce_dominant_gap_reselection(
        dominant_gap_reselection,
        cache_scheduler_implementation_backlog=cache_scheduler_implementation_backlog_status,
        cache_turboquant_preconditions_gap=cache_turboquant_preconditions_gap_status,
        multi_model_governance_policy_gap=governance_policy_gap,
        heavy_weight_repeatability=heavy_weight_status,
    )

    externally_blocked: list[str] = []
    internally_open: list[str] = []

    if host_status.status == "host_blocked_move_validation":
        externally_blocked.append("host_stable_execution")
    elif not host_status.ready:
        internally_open.append("host_stable_execution")

    if cache_status.closure_rung != "partial_closure":
        internally_open.append("cache_scheduler_depth")
    else:
        internally_open.append("cache_scheduler_depth")

    if governance_controls.controls_rung != "partial_closure":
        internally_open.append("multi_model_lifecycle_governance")
    else:
        internally_open.append("multi_model_lifecycle_governance")

    if heavy_weight_status.repeatability_rung == "local_blocked":
        externally_blocked.append("heavy_weight_runtime_repeatability")
    elif heavy_weight_status.repeatability_rung != "supported_host_repeatability_visible":
        internally_open.append("heavy_weight_runtime_repeatability")

    evidence_label = "early_formal_runtime"
    if (
        not externally_blocked
        and cache_status.closure_rung == "partial_closure"
        and governance_policy_gap.policy_gap_rung == "policy_gap_exact"
    ):
        evidence_label = "runtime_evidence_expanding"
    if (
        not externally_blocked
        and cache_status.closure_rung == "partial_closure"
        and governance_policy_gap.policy_gap_rung == "policy_gap_exact"
        and heavy_weight_status.repeatability_rung
        == "supported_host_repeatability_visible"
    ):
        evidence_label = "approaching_reference_grade_stability"

    exact_external_blocker = None
    if "heavy_weight_runtime_repeatability" in externally_blocked:
        exact_external_blocker = (
            "supported host/system image with one verified-safe MLX baseline is still required for repeated heavy-weight runtime proof"
        )
    elif "host_stable_execution" in externally_blocked:
        exact_external_blocker = (
            "current host still lacks one verified-safe MLX baseline for deeper replacement-grade validation"
        )

    dominant_next_gap = dominant_gap_reselection_status.selected_gap
    if not internally_open and externally_blocked:
        dominant_next_gap = "heavy_weight_runtime_repeatability"

    blocked_reason = (
        "runtime-owned evidence has expanded, but owlmlx still remains below reference-grade stability because supported-host heavy-weight proof and deeper governance/cache closure remain open"
    )
    recommended_next_step = (
        "close deeper multi-model governance controls locally while keeping the supported-host heavy-weight blocker exact"
    )
    if not internally_open and externally_blocked:
        recommended_next_step = (
            "move repeated heavy-weight validation to a supported host before raising customer-runtime claims"
        )
    if not externally_blocked and evidence_label == "approaching_reference_grade_stability":
        blocked_reason = (
            "customer-runtime evidence is expanding, but final reference-grade closure still requires stronger long-run proof before any readiness inflation"
        )
        recommended_next_step = (
            "promote repeated heavy-weight validation and stronger long-run runtime proof before changing the customer-facing posture"
        )
    elif dominant_next_gap == "cache_scheduler_depth":
        if (
            cache_counter_feasibility_status.feasibility_rung
            == "counter_ownership_exact"
        ):
            if (
                cache_scheduler_implementation_backlog_status.backlog_rung
                == "implementation_gap_exact"
            ):
                recommended_next_step = (
                    "treat cache as pre-gate admission-hook work on this path; request_aggregation_window is now exact, but owlmlx still has no runtime-owned cohort window before whole-request gate claim, the child protocol and stream path still assume one request at a time, multi-worker depth stays secondary pending concurrency revalidation, TurboQuant preconditions are also exact-but-secondary, and the governance policy gap and supported-host blocker remain exact"
                )
            elif cache_scheduler_floor_gap_status.floor_rung == "serial_floor_exact":
                recommended_next_step = (
                    "treat cache as scheduler-implementation work on this path; the active floor is still serial_single_worker, TurboQuant stays exact but secondary, and the governance policy gap and supported-host blocker remain exact"
                )
            elif (
                cache_scheduler_turboquant_split_status.split_rung == "split_exact"
                and cache_scheduler_turboquant_split_status.dominant_cache_branch
                == "turboquant_preconditions"
            ):
                recommended_next_step = (
                    "treat cache as TurboQuant-preconditions work on this path without regressing the already-frozen scheduler truth, while the governance policy gap and supported-host blocker remain exact"
                )
            else:
                recommended_next_step = (
                    "treat cache as a scheduler-depth/TurboQuant closure problem on this path; residency and eviction counters are not runtime-owned here, while the governance policy gap and supported-host blocker remain exact"
                )
        else:
            recommended_next_step = (
                "treat cache as an exact counter-grade gap: add one lightweight runtime-owned residency/reuse/eviction counter or deepen scheduler behavior while keeping the governance policy gap and supported-host blocker exact"
            )

    return CustomerRuntimeEvidenceLedger(
        host_stability=host_status,
        cache_closure=cache_status,
        cache_counter_gap=cache_counter_gap_status,
        cache_counter_feasibility=cache_counter_feasibility_status,
        cache_scheduler_turboquant_split=cache_scheduler_turboquant_split_status,
        cache_scheduler_floor_gap=cache_scheduler_floor_gap_status,
        cache_scheduler_implementation_backlog=cache_scheduler_implementation_backlog_status,
        cache_scheduler_branch_selection=cache_scheduler_branch_selection_status,
        cache_continuous_batching_feasibility=cache_continuous_batching_feasibility_status,
        cache_batching_mechanism_subgap=cache_batching_mechanism_subgap_status,
        cache_request_aggregation_window_exactness=cache_request_aggregation_window_exactness_status,
        cache_pre_gate_cohort_window_feasibility=cache_pre_gate_cohort_window_feasibility_status,
        cache_turboquant_preconditions_gap=cache_turboquant_preconditions_gap_status,
        dominant_gap_reselection=dominant_gap_reselection_status,
        multi_model_governance=governance_status,
        multi_model_governance_controls=governance_controls,
        multi_model_governance_transition_ledger=governance_transition_ledger,
        multi_model_governance_policy_gap=governance_policy_gap,
        heavy_weight_repeatability=heavy_weight_status,
        status="partial",
        evidence_label=evidence_label,
        externally_blocked_gaps=tuple(externally_blocked),
        internally_open_gaps=tuple(internally_open),
        dominant_next_gap=dominant_next_gap,
        exact_external_blocker=exact_external_blocker,
        blocked_reason=blocked_reason,
        recommended_next_step=recommended_next_step,
    )


def customer_runtime_evidence_to_dict(
    ledger: CustomerRuntimeEvidenceLedger,
) -> dict[str, Any]:
    """Serialize the runtime-owned customer evidence ledger."""

    governance_surface = _CONTRACT_SURFACES["multi_model_lifecycle_governance_controls"]
    governance_closure_level = ledger.multi_model_governance_controls.controls_rung
    governance_blocked_reason = ledger.multi_model_governance_controls.blocked_reason
    if ledger.multi_model_governance_policy_gap.policy_gap_rung == "policy_gap_exact":
        governance_surface = _CONTRACT_SURFACES[
            "multi_model_lifecycle_governance_policy_gap"
        ]
        governance_closure_level = ledger.multi_model_governance_policy_gap.policy_gap_rung
        governance_blocked_reason = (
            ledger.multi_model_governance_policy_gap.residual_blocker
        )
    elif ledger.multi_model_governance_transition_ledger.ledger_rung != "no_transition_runs":
        governance_surface = _CONTRACT_SURFACES[
            "multi_model_lifecycle_governance_transition_ledger"
        ]
        governance_closure_level = (
            ledger.multi_model_governance_transition_ledger.ledger_rung
        )
        governance_blocked_reason = (
            ledger.multi_model_governance_transition_ledger.blocked_reason
        )

    cache_surface = _CONTRACT_SURFACES["cache_scheduler_depth"]
    cache_closure_level = ledger.cache_closure.closure_rung
    cache_blocked_reason = ledger.cache_closure.blocked_reason
    if ledger.cache_counter_gap.counter_gap_rung == "counter_gap_exact":
        cache_surface = _CONTRACT_SURFACES["cache_scheduler_depth_counter_gap"]
        cache_closure_level = ledger.cache_counter_gap.counter_gap_rung
        cache_blocked_reason = ledger.cache_counter_gap.residual_blocker
    if ledger.cache_counter_feasibility.feasibility_rung == "counter_ownership_exact":
        cache_surface = _CONTRACT_SURFACES["cache_scheduler_depth_counter_feasibility"]
        cache_closure_level = ledger.cache_counter_feasibility.feasibility_rung
        cache_blocked_reason = ledger.cache_counter_feasibility.residual_blocker
    if ledger.cache_scheduler_turboquant_split.split_rung == "split_exact":
        cache_surface = _CONTRACT_SURFACES["cache_scheduler_depth_split"]
        cache_closure_level = ledger.cache_scheduler_turboquant_split.split_rung
        cache_blocked_reason = ledger.cache_scheduler_turboquant_split.residual_blocker
    if ledger.cache_scheduler_floor_gap.floor_rung == "serial_floor_exact":
        cache_surface = _CONTRACT_SURFACES["cache_scheduler_depth_scheduler_floor"]
        cache_closure_level = ledger.cache_scheduler_floor_gap.floor_rung
        cache_blocked_reason = ledger.cache_scheduler_floor_gap.residual_blocker
    if (
        ledger.cache_scheduler_implementation_backlog.backlog_rung
        == "implementation_gap_exact"
    ):
        cache_surface = _CONTRACT_SURFACES["cache_scheduler_depth_scheduler_backlog"]
        cache_closure_level = ledger.cache_scheduler_implementation_backlog.backlog_rung
        cache_blocked_reason = (
            ledger.cache_scheduler_implementation_backlog.residual_blocker
        )
    if (
        ledger.cache_scheduler_branch_selection.selection_rung
        == "branch_selection_exact"
    ):
        cache_surface = _CONTRACT_SURFACES[
            "cache_scheduler_depth_scheduler_branch_selection"
        ]
        cache_closure_level = ledger.cache_scheduler_branch_selection.selection_rung
        cache_blocked_reason = ledger.cache_scheduler_branch_selection.residual_blocker
    if (
        ledger.cache_continuous_batching_feasibility.feasibility_rung
        == "feasibility_blocker_exact"
    ):
        cache_surface = _CONTRACT_SURFACES[
            "cache_scheduler_depth_continuous_batching_feasibility"
        ]
        cache_closure_level = (
            ledger.cache_continuous_batching_feasibility.feasibility_rung
        )
        cache_blocked_reason = (
            ledger.cache_continuous_batching_feasibility.residual_blocker
        )
    if ledger.cache_batching_mechanism_subgap.subgap_rung == "mechanism_subgap_exact":
        cache_surface = _CONTRACT_SURFACES[
            "cache_scheduler_depth_batching_mechanism_subgap"
        ]
        cache_closure_level = ledger.cache_batching_mechanism_subgap.subgap_rung
        cache_blocked_reason = ledger.cache_batching_mechanism_subgap.residual_blocker
    if (
        ledger.cache_request_aggregation_window_exactness.exactness_rung
        == "aggregation_window_blocker_exact"
    ):
        cache_surface = _CONTRACT_SURFACES[
            "cache_scheduler_depth_request_aggregation_window_exactness"
        ]
        cache_closure_level = (
            ledger.cache_request_aggregation_window_exactness.exactness_rung
        )
        cache_blocked_reason = (
            ledger.cache_request_aggregation_window_exactness.residual_blocker
        )
    if (
        ledger.cache_pre_gate_cohort_window_feasibility.feasibility_rung
        == "cohort_window_boundary_exact"
    ):
        cache_surface = _CONTRACT_SURFACES[
            "cache_scheduler_depth_pre_gate_cohort_window_feasibility"
        ]
        cache_closure_level = (
            ledger.cache_pre_gate_cohort_window_feasibility.feasibility_rung
        )
        cache_blocked_reason = (
            ledger.cache_pre_gate_cohort_window_feasibility.residual_blocker
        )

    gap_evidence = [
        _gap_entry(
            gap_id="host_stable_execution",
            surface=_CONTRACT_SURFACES["host_stable_execution"],
            summary_status=ledger.host_stability.status,
            closure_level=ledger.host_stability.status,
            externally_blocked="host_stable_execution" in ledger.externally_blocked_gaps,
            blocked_reason=ledger.host_stability.blocked_reason,
        ),
        _gap_entry(
            gap_id="cache_scheduler_depth",
            surface=cache_surface,
            summary_status=ledger.cache_closure.status,
            closure_level=cache_closure_level,
            externally_blocked=False,
            blocked_reason=cache_blocked_reason,
        ),
        _gap_entry(
            gap_id="multi_model_lifecycle_governance",
            surface=governance_surface,
            summary_status=ledger.multi_model_governance_controls.status,
            closure_level=governance_closure_level,
            externally_blocked=False,
            blocked_reason=governance_blocked_reason,
        ),
        _gap_entry(
            gap_id="heavy_weight_runtime_repeatability",
            surface=_CONTRACT_SURFACES["heavy_weight_runtime_repeatability"],
            summary_status=ledger.heavy_weight_repeatability.status,
            closure_level=ledger.heavy_weight_repeatability.repeatability_rung,
            externally_blocked=(
                "heavy_weight_runtime_repeatability" in ledger.externally_blocked_gaps
            ),
            blocked_reason=ledger.heavy_weight_repeatability.blocked_reason,
        ),
    ]

    return {
        "contract": {
            "surface": "owlmlx.customer_runtime_evidence",
            "version": "phase45",
            "stable_sections": [
                "summary",
                "gap_evidence",
                "next_step",
            ],
        },
        "summary": {
            "status": ledger.status,
            "evidence_label": ledger.evidence_label,
            "contract_gap_count": len(gap_evidence),
            "runnable_verification_gap_count": len(gap_evidence),
            "externally_blocked_gaps": list(ledger.externally_blocked_gaps),
            "internally_open_gaps": list(ledger.internally_open_gaps),
            "blocked_reason": ledger.blocked_reason,
            "recommended_next_step": ledger.recommended_next_step,
        },
        "gap_evidence": gap_evidence,
        "next_step": {
            "dominant_next_gap": ledger.dominant_next_gap,
            "exact_external_blocker": ledger.exact_external_blocker,
        },
    }
