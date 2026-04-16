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
from .cache_scheduler_turboquant_branch_reselection import (
    CacheSchedulerTurboQuantBranchReselection,
    build_cache_scheduler_turboquant_branch_reselection,
)
from .cache_continuous_batching_branch_reduction import (
    CacheContinuousBatchingBranchReduction,
    build_cache_continuous_batching_branch_reduction,
)
from .cache_request_aggregation_window_reentry import (
    CacheRequestAggregationWindowReentry,
    build_cache_request_aggregation_window_reentry,
)
from .cache_request_aggregation_active_seam import (
    CacheRequestAggregationActiveSeam,
    build_cache_request_aggregation_active_seam,
)
from .cache_pre_gate_admission_window_seam import (
    CachePreGateAdmissionWindowSeam,
    build_cache_pre_gate_admission_window_seam,
)
from .cache_structural_ingress_seam import (
    CacheStructuralIngressSeam,
    build_cache_structural_ingress_seam,
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
from .cache_pre_gate_admission_hook_exactness import (
    CachePreGateAdmissionHookExactness,
    build_cache_pre_gate_admission_hook_exactness,
)
from .cache_admission_hook_safety_contract import (
    CacheAdmissionHookSafetyContract,
    build_cache_admission_hook_safety_contract,
)
from .cache_pre_claim_admission_contract import (
    CachePreClaimAdmissionContract,
    build_cache_pre_claim_admission_contract,
)
from .cache_pre_claim_staging_seam_exactness import (
    CachePreClaimStagingSeamExactness,
    build_cache_pre_claim_staging_seam_exactness,
)
from .cache_pre_claim_metadata_ticket_ownership import (
    CachePreClaimMetadataTicketOwnership,
    build_cache_pre_claim_metadata_ticket_ownership,
)
from .cache_pre_claim_inert_state_semantics import (
    CachePreClaimInertStateSemantics,
    build_cache_pre_claim_inert_state_semantics,
)
from .cache_pre_claim_marker_lifetime import (
    CachePreClaimMarkerLifetime,
    build_cache_pre_claim_marker_lifetime,
)
from .cache_pre_claim_marker_visibility import (
    CachePreClaimMarkerVisibility,
    build_cache_pre_claim_marker_visibility,
)
from .cache_pre_claim_marker_trigger_inputs import (
    CachePreClaimMarkerTriggerInputs,
    build_cache_pre_claim_marker_trigger_inputs,
)
from .cache_pre_claim_marker_reader_writer_ownership import (
    CachePreClaimMarkerReaderWriterOwnership,
    build_cache_pre_claim_marker_reader_writer_ownership,
)
from .cache_pre_claim_marker_state_carrier import (
    CachePreClaimMarkerStateCarrier,
    build_cache_pre_claim_marker_state_carrier,
)
from .cache_pre_claim_marker_clear_observer_boundary import (
    CachePreClaimMarkerClearObserverBoundary,
    build_cache_pre_claim_marker_clear_observer_boundary,
)
from .cache_pre_claim_marker_immutability_boundary import (
    CachePreClaimMarkerImmutabilityBoundary,
    build_cache_pre_claim_marker_immutability_boundary,
)
from .cache_pre_claim_marker_payload_shape_exactness import (
    CachePreClaimMarkerPayloadShapeExactness,
    build_cache_pre_claim_marker_payload_shape_exactness,
)
from .cache_pre_claim_marker_encoding_carrier_exactness import (
    CachePreClaimMarkerEncodingCarrierExactness,
    build_cache_pre_claim_marker_encoding_carrier_exactness,
)
from .cache_pre_claim_marker_storage_locality_exactness import (
    CachePreClaimMarkerStorageLocalityExactness,
    build_cache_pre_claim_marker_storage_locality_exactness,
)
from .cache_pre_claim_marker_locality_access_exactness import (
    CachePreClaimMarkerLocalityAccessExactness,
    build_cache_pre_claim_marker_locality_access_exactness,
)
from .cache_pre_claim_marker_locality_isolation_exactness import (
    CachePreClaimMarkerLocalityIsolationExactness,
    build_cache_pre_claim_marker_locality_isolation_exactness,
)
from .cache_pre_claim_marker_locality_lifetime_coupling import (
    CachePreClaimMarkerLocalityLifetimeCoupling,
    build_cache_pre_claim_marker_locality_lifetime_coupling,
)
from .cache_pre_claim_marker_reclaim_reset_exactness import (
    CachePreClaimMarkerReclaimResetExactness,
    build_cache_pre_claim_marker_reclaim_reset_exactness,
)
from .cache_pre_claim_admission_carrier_construction import (
    CachePreClaimAdmissionCarrierConstruction,
    build_cache_pre_claim_admission_carrier_construction,
)
from .cache_pre_claim_admission_carrier_field_exactness import (
    CachePreClaimAdmissionCarrierFieldExactness,
    build_cache_pre_claim_admission_carrier_field_exactness,
)
from .cache_pre_claim_admission_carrier_encoding_exactness import (
    CachePreClaimAdmissionCarrierEncodingExactness,
    build_cache_pre_claim_admission_carrier_encoding_exactness,
)
from .cache_pre_claim_admission_carrier_locality_exactness import (
    CachePreClaimAdmissionCarrierLocalityExactness,
    build_cache_pre_claim_admission_carrier_locality_exactness,
)
from .cache_pre_claim_admission_carrier_locality_access_exactness import (
    CachePreClaimAdmissionCarrierLocalityAccessExactness,
    build_cache_pre_claim_admission_carrier_locality_access_exactness,
)
from .cache_pre_claim_admission_carrier_locality_isolation_exactness import (
    CachePreClaimAdmissionCarrierLocalityIsolationExactness,
    build_cache_pre_claim_admission_carrier_locality_isolation_exactness,
)
from .cache_pre_claim_admission_carrier_locality_lifetime_coupling import (
    CachePreClaimAdmissionCarrierLocalityLifetimeCoupling,
    build_cache_pre_claim_admission_carrier_locality_lifetime_coupling,
)
from .cache_pre_claim_admission_carrier_reclaim_reset_exactness import (
    CachePreClaimAdmissionCarrierReclaimResetExactness,
    build_cache_pre_claim_admission_carrier_reclaim_reset_exactness,
)
from .cache_pre_claim_admission_carrier_branch_reselection import (
    CachePreClaimAdmissionCarrierBranchReselection,
    build_cache_pre_claim_admission_carrier_branch_reselection,
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
            "tests/test_cache_scheduler_turboquant_branch_reselection.py",
            "tests/test_cache_continuous_batching_branch_reduction.py",
            "tests/test_cache_request_aggregation_window_reentry.py",
            "tests/test_cache_request_aggregation_active_seam.py",
            "tests/test_cache_pre_gate_admission_window_seam.py",
            "tests/test_cache_pre_gate_admission_hook_harness.py",
            "tests/test_cache_structural_ingress_seam.py",
            "tests/test_cache_continuous_batching_feasibility.py",
            "tests/test_cache_batching_mechanism_subgap.py",
            "tests/test_cache_request_aggregation_window_exactness.py",
            "tests/test_cache_pre_gate_cohort_window_feasibility.py",
            "tests/test_cache_pre_gate_admission_hook_exactness.py",
            "tests/test_cache_admission_hook_safety_contract.py",
            "tests/test_cache_pre_claim_admission_contract.py",
            "tests/test_cache_pre_claim_staging_seam_exactness.py",
            "tests/test_cache_pre_claim_metadata_ticket_ownership.py",
            "tests/test_cache_pre_claim_inert_state_semantics.py",
            "tests/test_cache_pre_claim_marker_lifetime.py",
            "tests/test_cache_pre_claim_marker_visibility.py",
            "tests/test_cache_pre_claim_marker_trigger_inputs.py",
            "tests/test_cache_pre_claim_marker_reader_writer_ownership.py",
            "tests/test_cache_pre_claim_marker_state_carrier.py",
            "tests/test_cache_pre_claim_marker_clear_observer_boundary.py",
            "tests/test_cache_pre_claim_marker_immutability_boundary.py",
            "tests/test_cache_pre_claim_marker_payload_shape_exactness.py",
            "tests/test_cache_pre_claim_marker_encoding_carrier_exactness.py",
            "tests/test_cache_pre_claim_marker_storage_locality_exactness.py",
            "tests/test_cache_pre_claim_marker_locality_access_exactness.py",
            "tests/test_cache_pre_claim_marker_locality_isolation_exactness.py",
            "tests/test_cache_pre_claim_marker_locality_lifetime_coupling.py",
            "tests/test_cache_pre_claim_marker_reclaim_reset_exactness.py",
            "tests/test_cache_pre_claim_admission_carrier_construction.py",
            "tests/test_cache_pre_claim_admission_carrier_field_exactness.py",
            "tests/test_cache_pre_claim_admission_carrier_encoding_exactness.py",
            "tests/test_cache_pre_claim_admission_carrier_locality_exactness.py",
            "tests/test_cache_pre_claim_admission_carrier_locality_access_exactness.py",
            "tests/test_cache_pre_claim_admission_carrier_locality_isolation_exactness.py",
            "tests/test_cache_pre_claim_admission_carrier_locality_lifetime_coupling.py",
            "tests/test_cache_pre_claim_admission_carrier_reclaim_reset_exactness.py",
            "tests/test_cache_pre_claim_admission_carrier_branch_reselection.py",
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
            "scripts/runtime_cache_scheduler_turboquant_branch_reselection.py",
            "scripts/runtime_cache_continuous_batching_branch_reduction.py",
            "scripts/runtime_cache_request_aggregation_window_reentry.py",
            "scripts/runtime_cache_request_aggregation_active_seam.py",
            "scripts/runtime_cache_pre_gate_admission_window_seam.py",
            "scripts/runtime_cache_structural_ingress_seam.py",
            "scripts/runtime_cache_continuous_batching_feasibility.py",
            "scripts/runtime_cache_batching_mechanism_subgap.py",
            "scripts/runtime_cache_request_aggregation_window_exactness.py",
            "scripts/runtime_cache_pre_gate_cohort_window_feasibility.py",
            "scripts/runtime_cache_pre_gate_admission_hook_exactness.py",
            "scripts/runtime_cache_admission_hook_safety_contract.py",
            "scripts/runtime_cache_pre_claim_admission_contract.py",
            "scripts/runtime_cache_pre_claim_staging_seam_exactness.py",
            "scripts/runtime_cache_pre_claim_metadata_ticket_ownership.py",
            "scripts/runtime_cache_pre_claim_inert_state_semantics.py",
            "scripts/runtime_cache_pre_claim_marker_lifetime.py",
            "scripts/runtime_cache_pre_claim_marker_visibility.py",
            "scripts/runtime_cache_pre_claim_marker_trigger_inputs.py",
            "scripts/runtime_cache_pre_claim_marker_reader_writer_ownership.py",
            "scripts/runtime_cache_pre_claim_marker_state_carrier.py",
            "scripts/runtime_cache_pre_claim_marker_clear_observer_boundary.py",
            "scripts/runtime_cache_pre_claim_marker_immutability_boundary.py",
            "scripts/runtime_cache_pre_claim_marker_payload_shape_exactness.py",
            "scripts/runtime_cache_pre_claim_marker_encoding_carrier_exactness.py",
            "scripts/runtime_cache_pre_claim_marker_storage_locality_exactness.py",
            "scripts/runtime_cache_pre_claim_marker_locality_access_exactness.py",
            "scripts/runtime_cache_pre_claim_marker_locality_isolation_exactness.py",
            "scripts/runtime_cache_pre_claim_marker_locality_lifetime_coupling.py",
            "scripts/runtime_cache_pre_claim_marker_reclaim_reset_exactness.py",
            "scripts/runtime_cache_pre_claim_admission_carrier_construction.py",
            "scripts/runtime_cache_pre_claim_admission_carrier_field_exactness.py",
            "scripts/runtime_cache_pre_claim_admission_carrier_encoding_exactness.py",
            "scripts/runtime_cache_pre_claim_admission_carrier_locality_exactness.py",
            "scripts/runtime_cache_pre_claim_admission_carrier_locality_access_exactness.py",
            "scripts/runtime_cache_pre_claim_admission_carrier_locality_isolation_exactness.py",
            "scripts/runtime_cache_pre_claim_admission_carrier_locality_lifetime_coupling.py",
            "scripts/runtime_cache_pre_claim_admission_carrier_reclaim_reset_exactness.py",
            "scripts/runtime_cache_pre_claim_admission_carrier_branch_reselection.py",
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
            "tests/test_multi_model_ttl_policy_control.py",
            "tests/test_multi_model_eviction_history_governance.py",
            "tests/test_runtime_kernel.py",
        ],
        "scripts": [
            "scripts/runtime_multi_model_governance_status.py",
            "scripts/runtime_multi_model_governance_controls.py",
            "scripts/runtime_multi_model_governance_transition_ledger.py",
            "scripts/runtime_multi_model_governance_policy_gap.py",
            "scripts/runtime_multi_model_ttl_policy_control.py",
            "scripts/runtime_multi_model_eviction_history_governance.py",
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
    "cache_scheduler_depth_scheduler_turboquant_branch_reselection": "owlmlx.cache_scheduler_turboquant_branch_reselection",
    "cache_scheduler_depth_continuous_batching_branch_reduction": "owlmlx.cache_continuous_batching_branch_reduction",
    "cache_scheduler_depth_request_aggregation_window_reentry": "owlmlx.cache_request_aggregation_window_reentry",
    "cache_scheduler_depth_request_aggregation_active_seam": "owlmlx.cache_request_aggregation_active_seam",
    "cache_scheduler_depth_pre_gate_admission_window_seam": "owlmlx.cache_pre_gate_admission_window_seam",
    "cache_scheduler_depth_structural_ingress_seam": "owlmlx.cache_structural_ingress_seam",
    "cache_scheduler_depth_continuous_batching_feasibility": "owlmlx.cache_continuous_batching_feasibility",
    "cache_scheduler_depth_batching_mechanism_subgap": "owlmlx.cache_batching_mechanism_subgap",
    "cache_scheduler_depth_request_aggregation_window_exactness": "owlmlx.cache_request_aggregation_window_exactness",
    "cache_scheduler_depth_pre_gate_cohort_window_feasibility": "owlmlx.cache_pre_gate_cohort_window_feasibility",
    "cache_scheduler_depth_pre_gate_admission_hook_exactness": "owlmlx.cache_pre_gate_admission_hook_exactness",
    "cache_scheduler_depth_admission_hook_safety_contract": "owlmlx.cache_admission_hook_safety_contract",
    "cache_scheduler_depth_pre_claim_admission_contract": "owlmlx.cache_pre_claim_admission_contract",
    "cache_scheduler_depth_pre_claim_staging_seam_exactness": "owlmlx.cache_pre_claim_staging_seam_exactness",
    "cache_scheduler_depth_pre_claim_metadata_ticket_ownership": "owlmlx.cache_pre_claim_metadata_ticket_ownership",
    "cache_scheduler_depth_pre_claim_inert_state_semantics": "owlmlx.cache_pre_claim_inert_state_semantics",
    "cache_scheduler_depth_pre_claim_marker_lifetime": "owlmlx.cache_pre_claim_marker_lifetime",
    "cache_scheduler_depth_pre_claim_marker_visibility": "owlmlx.cache_pre_claim_marker_visibility",
    "cache_scheduler_depth_pre_claim_marker_trigger_inputs": "owlmlx.cache_pre_claim_marker_trigger_inputs",
    "cache_scheduler_depth_pre_claim_marker_reader_writer_ownership": "owlmlx.cache_pre_claim_marker_reader_writer_ownership",
    "cache_scheduler_depth_pre_claim_marker_state_carrier": "owlmlx.cache_pre_claim_marker_state_carrier",
    "cache_scheduler_depth_pre_claim_marker_clear_observer_boundary": "owlmlx.cache_pre_claim_marker_clear_observer_boundary",
    "cache_scheduler_depth_pre_claim_marker_immutability_boundary": "owlmlx.cache_pre_claim_marker_immutability_boundary",
    "cache_scheduler_depth_pre_claim_marker_payload_shape_exactness": "owlmlx.cache_pre_claim_marker_payload_shape_exactness",
    "cache_scheduler_depth_pre_claim_marker_encoding_carrier_exactness": "owlmlx.cache_pre_claim_marker_encoding_carrier_exactness",
    "cache_scheduler_depth_pre_claim_marker_storage_locality_exactness": "owlmlx.cache_pre_claim_marker_storage_locality_exactness",
    "cache_scheduler_depth_pre_claim_marker_locality_access_exactness": "owlmlx.cache_pre_claim_marker_locality_access_exactness",
    "cache_scheduler_depth_pre_claim_marker_locality_isolation_exactness": "owlmlx.cache_pre_claim_marker_locality_isolation_exactness",
    "cache_scheduler_depth_pre_claim_marker_locality_lifetime_coupling": "owlmlx.cache_pre_claim_marker_locality_lifetime_coupling",
    "cache_scheduler_depth_pre_claim_marker_reclaim_reset_exactness": "owlmlx.cache_pre_claim_marker_reclaim_reset_exactness",
    "cache_scheduler_depth_pre_claim_admission_carrier_construction": "owlmlx.cache_pre_claim_admission_carrier_construction",
    "cache_scheduler_depth_pre_claim_admission_carrier_field_exactness": "owlmlx.cache_pre_claim_admission_carrier_field_exactness",
    "cache_scheduler_depth_pre_claim_admission_carrier_encoding_exactness": "owlmlx.cache_pre_claim_admission_carrier_encoding_exactness",
    "cache_scheduler_depth_pre_claim_admission_carrier_locality_exactness": "owlmlx.cache_pre_claim_admission_carrier_locality_exactness",
    "cache_scheduler_depth_pre_claim_admission_carrier_locality_access_exactness": "owlmlx.cache_pre_claim_admission_carrier_locality_access_exactness",
    "cache_scheduler_depth_pre_claim_admission_carrier_locality_isolation_exactness": "owlmlx.cache_pre_claim_admission_carrier_locality_isolation_exactness",
    "cache_scheduler_depth_pre_claim_admission_carrier_locality_lifetime_coupling": "owlmlx.cache_pre_claim_admission_carrier_locality_lifetime_coupling",
    "cache_scheduler_depth_pre_claim_admission_carrier_reclaim_reset_exactness": "owlmlx.cache_pre_claim_admission_carrier_reclaim_reset_exactness",
    "cache_scheduler_depth_pre_claim_admission_carrier_branch_reselection": "owlmlx.cache_pre_claim_admission_carrier_branch_reselection",
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
    cache_scheduler_turboquant_branch_reselection: CacheSchedulerTurboQuantBranchReselection
    cache_continuous_batching_branch_reduction: CacheContinuousBatchingBranchReduction
    cache_request_aggregation_window_reentry: CacheRequestAggregationWindowReentry
    cache_request_aggregation_active_seam: CacheRequestAggregationActiveSeam
    cache_pre_gate_admission_window_seam: CachePreGateAdmissionWindowSeam
    cache_structural_ingress_seam: CacheStructuralIngressSeam
    cache_continuous_batching_feasibility: CacheContinuousBatchingFeasibility
    cache_batching_mechanism_subgap: CacheBatchingMechanismSubgap
    cache_request_aggregation_window_exactness: CacheRequestAggregationWindowExactness
    cache_pre_gate_cohort_window_feasibility: CachePreGateCohortWindowFeasibility
    cache_pre_gate_admission_hook_exactness: CachePreGateAdmissionHookExactness
    cache_admission_hook_safety_contract: CacheAdmissionHookSafetyContract
    cache_pre_claim_admission_contract: CachePreClaimAdmissionContract
    cache_pre_claim_staging_seam_exactness: CachePreClaimStagingSeamExactness
    cache_pre_claim_metadata_ticket_ownership: CachePreClaimMetadataTicketOwnership
    cache_pre_claim_inert_state_semantics: CachePreClaimInertStateSemantics
    cache_pre_claim_marker_lifetime: CachePreClaimMarkerLifetime
    cache_pre_claim_marker_visibility: CachePreClaimMarkerVisibility
    cache_pre_claim_marker_trigger_inputs: CachePreClaimMarkerTriggerInputs
    cache_pre_claim_marker_reader_writer_ownership: CachePreClaimMarkerReaderWriterOwnership
    cache_pre_claim_marker_state_carrier: CachePreClaimMarkerStateCarrier
    cache_pre_claim_marker_clear_observer_boundary: CachePreClaimMarkerClearObserverBoundary
    cache_pre_claim_marker_immutability_boundary: CachePreClaimMarkerImmutabilityBoundary
    cache_pre_claim_marker_payload_shape_exactness: CachePreClaimMarkerPayloadShapeExactness
    cache_pre_claim_marker_encoding_carrier_exactness: CachePreClaimMarkerEncodingCarrierExactness
    cache_pre_claim_marker_storage_locality_exactness: CachePreClaimMarkerStorageLocalityExactness
    cache_pre_claim_marker_locality_access_exactness: CachePreClaimMarkerLocalityAccessExactness
    cache_pre_claim_marker_locality_isolation_exactness: CachePreClaimMarkerLocalityIsolationExactness
    cache_pre_claim_marker_locality_lifetime_coupling: CachePreClaimMarkerLocalityLifetimeCoupling
    cache_pre_claim_marker_reclaim_reset_exactness: CachePreClaimMarkerReclaimResetExactness
    cache_pre_claim_admission_carrier_construction: CachePreClaimAdmissionCarrierConstruction
    cache_pre_claim_admission_carrier_field_exactness: CachePreClaimAdmissionCarrierFieldExactness
    cache_pre_claim_admission_carrier_encoding_exactness: CachePreClaimAdmissionCarrierEncodingExactness
    cache_pre_claim_admission_carrier_locality_exactness: CachePreClaimAdmissionCarrierLocalityExactness
    cache_pre_claim_admission_carrier_locality_access_exactness: CachePreClaimAdmissionCarrierLocalityAccessExactness
    cache_pre_claim_admission_carrier_locality_isolation_exactness: CachePreClaimAdmissionCarrierLocalityIsolationExactness
    cache_pre_claim_admission_carrier_locality_lifetime_coupling: CachePreClaimAdmissionCarrierLocalityLifetimeCoupling
    cache_pre_claim_admission_carrier_reclaim_reset_exactness: CachePreClaimAdmissionCarrierReclaimResetExactness
    cache_pre_claim_admission_carrier_branch_reselection: CachePreClaimAdmissionCarrierBranchReselection
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


def _coerce_cache_scheduler_turboquant_branch_reselection(
    value: CacheSchedulerTurboQuantBranchReselection | None,
    *,
    cache_pre_claim_admission_carrier_branch_reselection: CachePreClaimAdmissionCarrierBranchReselection,
    cache_scheduler_branch_selection: CacheSchedulerBranchSelection,
    cache_turboquant_preconditions_gap: CacheTurboQuantPreconditionsGap,
) -> CacheSchedulerTurboQuantBranchReselection:
    if isinstance(value, CacheSchedulerTurboQuantBranchReselection):
        return value
    return build_cache_scheduler_turboquant_branch_reselection(
        carrier_branch_reselection=cache_pre_claim_admission_carrier_branch_reselection,
        scheduler_branch_selection=cache_scheduler_branch_selection,
        turboquant_preconditions_gap=cache_turboquant_preconditions_gap,
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


def _coerce_cache_continuous_batching_branch_reduction(
    value: CacheContinuousBatchingBranchReduction | None,
    *,
    cache_scheduler_turboquant_branch_reselection: CacheSchedulerTurboQuantBranchReselection,
    cache_batching_mechanism_subgap: CacheBatchingMechanismSubgap,
) -> CacheContinuousBatchingBranchReduction:
    if isinstance(value, CacheContinuousBatchingBranchReduction):
        return value
    return build_cache_continuous_batching_branch_reduction(
        scheduler_turboquant_branch_reselection=cache_scheduler_turboquant_branch_reselection,
        batching_mechanism_subgap=cache_batching_mechanism_subgap,
    )


def _coerce_cache_request_aggregation_window_reentry(
    value: CacheRequestAggregationWindowReentry | None,
    *,
    cache_continuous_batching_branch_reduction: CacheContinuousBatchingBranchReduction,
    cache_request_aggregation_window_exactness: CacheRequestAggregationWindowExactness,
) -> CacheRequestAggregationWindowReentry:
    if isinstance(value, CacheRequestAggregationWindowReentry):
        return value
    return build_cache_request_aggregation_window_reentry(
        continuous_batching_branch_reduction=cache_continuous_batching_branch_reduction,
        request_aggregation_window_exactness=cache_request_aggregation_window_exactness,
    )


def _coerce_cache_request_aggregation_active_seam(
    value: CacheRequestAggregationActiveSeam | None,
    *,
    cache_request_aggregation_window_reentry: CacheRequestAggregationWindowReentry,
    cache_request_aggregation_window_exactness: CacheRequestAggregationWindowExactness,
) -> CacheRequestAggregationActiveSeam:
    if isinstance(value, CacheRequestAggregationActiveSeam):
        return value
    return build_cache_request_aggregation_active_seam(
        request_aggregation_window_reentry=cache_request_aggregation_window_reentry,
        request_aggregation_window_exactness=cache_request_aggregation_window_exactness,
    )


def _coerce_cache_pre_gate_admission_window_seam(
    value: CachePreGateAdmissionWindowSeam | None,
    *,
    cache_request_aggregation_active_seam: CacheRequestAggregationActiveSeam,
    cache_pre_gate_admission_hook_exactness: CachePreGateAdmissionHookExactness,
) -> CachePreGateAdmissionWindowSeam:
    if isinstance(value, CachePreGateAdmissionWindowSeam):
        return value
    return build_cache_pre_gate_admission_window_seam(
        request_aggregation_active_seam=cache_request_aggregation_active_seam,
        pre_gate_admission_hook_exactness=cache_pre_gate_admission_hook_exactness,
    )


def _coerce_cache_structural_ingress_seam(
    value: CacheStructuralIngressSeam | None,
    *,
    cache_pre_gate_admission_window_seam: CachePreGateAdmissionWindowSeam,
    cache_pre_claim_staging_seam_exactness: CachePreClaimStagingSeamExactness,
) -> CacheStructuralIngressSeam:
    if isinstance(value, CacheStructuralIngressSeam):
        return value
    return build_cache_structural_ingress_seam(
        pre_gate_admission_window_seam=cache_pre_gate_admission_window_seam,
        pre_claim_staging_seam_exactness=cache_pre_claim_staging_seam_exactness,
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


def _coerce_cache_pre_gate_admission_hook_exactness(
    value: CachePreGateAdmissionHookExactness | None,
    *,
    cache_pre_gate_cohort_window_feasibility: CachePreGateCohortWindowFeasibility,
) -> CachePreGateAdmissionHookExactness:
    if isinstance(value, CachePreGateAdmissionHookExactness):
        return value
    return build_cache_pre_gate_admission_hook_exactness(
        cohort_window_feasibility=cache_pre_gate_cohort_window_feasibility
    )


def _coerce_cache_admission_hook_safety_contract(
    value: CacheAdmissionHookSafetyContract | None,
    *,
    cache_pre_gate_admission_hook_exactness: CachePreGateAdmissionHookExactness,
) -> CacheAdmissionHookSafetyContract:
    if isinstance(value, CacheAdmissionHookSafetyContract):
        return value
    return build_cache_admission_hook_safety_contract(
        admission_hook_exactness=cache_pre_gate_admission_hook_exactness
    )


def _coerce_cache_pre_claim_admission_contract(
    value: CachePreClaimAdmissionContract | None,
    *,
    cache_admission_hook_safety_contract: CacheAdmissionHookSafetyContract,
) -> CachePreClaimAdmissionContract:
    if isinstance(value, CachePreClaimAdmissionContract):
        return value
    return build_cache_pre_claim_admission_contract(
        safety_contract=cache_admission_hook_safety_contract
    )


def _coerce_cache_pre_claim_staging_seam_exactness(
    value: CachePreClaimStagingSeamExactness | None,
    *,
    cache_pre_claim_admission_contract: CachePreClaimAdmissionContract,
) -> CachePreClaimStagingSeamExactness:
    if isinstance(value, CachePreClaimStagingSeamExactness):
        return value
    return build_cache_pre_claim_staging_seam_exactness(
        pre_claim_contract=cache_pre_claim_admission_contract
    )


def _coerce_cache_pre_claim_metadata_ticket_ownership(
    value: CachePreClaimMetadataTicketOwnership | None,
    *,
    cache_pre_claim_staging_seam_exactness: CachePreClaimStagingSeamExactness,
) -> CachePreClaimMetadataTicketOwnership:
    if isinstance(value, CachePreClaimMetadataTicketOwnership):
        return value
    return build_cache_pre_claim_metadata_ticket_ownership(
        staging_seam_exactness=cache_pre_claim_staging_seam_exactness
    )


def _coerce_cache_pre_claim_inert_state_semantics(
    value: CachePreClaimInertStateSemantics | None,
    *,
    cache_pre_claim_metadata_ticket_ownership: CachePreClaimMetadataTicketOwnership,
    cache_pre_gate_cohort_window_feasibility: CachePreGateCohortWindowFeasibility,
) -> CachePreClaimInertStateSemantics:
    if isinstance(value, CachePreClaimInertStateSemantics):
        return value
    return build_cache_pre_claim_inert_state_semantics(
        metadata_ticket_ownership=cache_pre_claim_metadata_ticket_ownership,
        cohort_window_feasibility=cache_pre_gate_cohort_window_feasibility,
    )


def _coerce_cache_pre_claim_marker_lifetime(
    value: CachePreClaimMarkerLifetime | None,
    *,
    cache_pre_claim_inert_state_semantics: CachePreClaimInertStateSemantics,
) -> CachePreClaimMarkerLifetime:
    if isinstance(value, CachePreClaimMarkerLifetime):
        return value
    return build_cache_pre_claim_marker_lifetime(
        inert_state_semantics=cache_pre_claim_inert_state_semantics
    )


def _coerce_cache_pre_claim_marker_visibility(
    value: CachePreClaimMarkerVisibility | None,
    *,
    cache_pre_claim_marker_lifetime: CachePreClaimMarkerLifetime,
) -> CachePreClaimMarkerVisibility:
    if isinstance(value, CachePreClaimMarkerVisibility):
        return value
    return build_cache_pre_claim_marker_visibility(
        marker_lifetime=cache_pre_claim_marker_lifetime
    )


def _coerce_cache_pre_claim_marker_trigger_inputs(
    value: CachePreClaimMarkerTriggerInputs | None,
    *,
    cache_pre_claim_marker_visibility: CachePreClaimMarkerVisibility,
) -> CachePreClaimMarkerTriggerInputs:
    if isinstance(value, CachePreClaimMarkerTriggerInputs):
        return value
    return build_cache_pre_claim_marker_trigger_inputs(
        marker_visibility=cache_pre_claim_marker_visibility
    )


def _coerce_cache_pre_claim_marker_reader_writer_ownership(
    value: CachePreClaimMarkerReaderWriterOwnership | None,
    *,
    cache_pre_claim_marker_trigger_inputs: CachePreClaimMarkerTriggerInputs,
) -> CachePreClaimMarkerReaderWriterOwnership:
    if isinstance(value, CachePreClaimMarkerReaderWriterOwnership):
        return value
    return build_cache_pre_claim_marker_reader_writer_ownership(
        trigger_inputs=cache_pre_claim_marker_trigger_inputs
    )


def _coerce_cache_pre_claim_marker_state_carrier(
    value: CachePreClaimMarkerStateCarrier | None,
    *,
    cache_pre_claim_marker_reader_writer_ownership: CachePreClaimMarkerReaderWriterOwnership,
) -> CachePreClaimMarkerStateCarrier:
    if isinstance(value, CachePreClaimMarkerStateCarrier):
        return value
    return build_cache_pre_claim_marker_state_carrier(
        reader_writer_ownership=cache_pre_claim_marker_reader_writer_ownership
    )


def _coerce_cache_pre_claim_marker_clear_observer_boundary(
    value: CachePreClaimMarkerClearObserverBoundary | None,
    *,
    cache_pre_claim_marker_state_carrier: CachePreClaimMarkerStateCarrier,
) -> CachePreClaimMarkerClearObserverBoundary:
    if isinstance(value, CachePreClaimMarkerClearObserverBoundary):
        return value
    return build_cache_pre_claim_marker_clear_observer_boundary(
        state_carrier=cache_pre_claim_marker_state_carrier
    )


def _coerce_cache_pre_claim_marker_immutability_boundary(
    value: CachePreClaimMarkerImmutabilityBoundary | None,
    *,
    cache_pre_claim_marker_clear_observer_boundary: CachePreClaimMarkerClearObserverBoundary,
) -> CachePreClaimMarkerImmutabilityBoundary:
    if isinstance(value, CachePreClaimMarkerImmutabilityBoundary):
        return value
    return build_cache_pre_claim_marker_immutability_boundary(
        clear_observer_boundary=cache_pre_claim_marker_clear_observer_boundary
    )


def _coerce_cache_pre_claim_marker_payload_shape_exactness(
    value: CachePreClaimMarkerPayloadShapeExactness | None,
    *,
    cache_pre_claim_marker_immutability_boundary: CachePreClaimMarkerImmutabilityBoundary,
) -> CachePreClaimMarkerPayloadShapeExactness:
    if isinstance(value, CachePreClaimMarkerPayloadShapeExactness):
        return value
    return build_cache_pre_claim_marker_payload_shape_exactness(
        immutability_boundary=cache_pre_claim_marker_immutability_boundary
    )


def _coerce_cache_pre_claim_marker_encoding_carrier_exactness(
    value: CachePreClaimMarkerEncodingCarrierExactness | None,
    *,
    cache_pre_claim_marker_payload_shape_exactness: CachePreClaimMarkerPayloadShapeExactness,
) -> CachePreClaimMarkerEncodingCarrierExactness:
    if isinstance(value, CachePreClaimMarkerEncodingCarrierExactness):
        return value
    return build_cache_pre_claim_marker_encoding_carrier_exactness(
        payload_shape=cache_pre_claim_marker_payload_shape_exactness
    )


def _coerce_cache_pre_claim_marker_storage_locality_exactness(
    value: CachePreClaimMarkerStorageLocalityExactness | None,
    *,
    cache_pre_claim_marker_encoding_carrier_exactness: CachePreClaimMarkerEncodingCarrierExactness,
) -> CachePreClaimMarkerStorageLocalityExactness:
    if isinstance(value, CachePreClaimMarkerStorageLocalityExactness):
        return value
    return build_cache_pre_claim_marker_storage_locality_exactness(
        encoding_carrier=cache_pre_claim_marker_encoding_carrier_exactness
    )


def _coerce_cache_pre_claim_marker_locality_access_exactness(
    value: CachePreClaimMarkerLocalityAccessExactness | None,
    *,
    cache_pre_claim_marker_storage_locality_exactness: CachePreClaimMarkerStorageLocalityExactness,
) -> CachePreClaimMarkerLocalityAccessExactness:
    if isinstance(value, CachePreClaimMarkerLocalityAccessExactness):
        return value
    return build_cache_pre_claim_marker_locality_access_exactness(
        storage_locality=cache_pre_claim_marker_storage_locality_exactness
    )


def _coerce_cache_pre_claim_marker_locality_isolation_exactness(
    value: CachePreClaimMarkerLocalityIsolationExactness | None,
    *,
    cache_pre_claim_marker_locality_access_exactness: CachePreClaimMarkerLocalityAccessExactness,
) -> CachePreClaimMarkerLocalityIsolationExactness:
    if isinstance(value, CachePreClaimMarkerLocalityIsolationExactness):
        return value
    return build_cache_pre_claim_marker_locality_isolation_exactness(
        locality_access=cache_pre_claim_marker_locality_access_exactness
    )


def _coerce_cache_pre_claim_marker_locality_lifetime_coupling(
    value: CachePreClaimMarkerLocalityLifetimeCoupling | None,
    *,
    cache_pre_claim_marker_locality_isolation_exactness: CachePreClaimMarkerLocalityIsolationExactness,
) -> CachePreClaimMarkerLocalityLifetimeCoupling:
    if isinstance(value, CachePreClaimMarkerLocalityLifetimeCoupling):
        return value
    return build_cache_pre_claim_marker_locality_lifetime_coupling(
        locality_isolation=cache_pre_claim_marker_locality_isolation_exactness
    )


def _coerce_cache_pre_claim_marker_reclaim_reset_exactness(
    value: CachePreClaimMarkerReclaimResetExactness | None,
    *,
    cache_pre_claim_marker_locality_lifetime_coupling: CachePreClaimMarkerLocalityLifetimeCoupling,
) -> CachePreClaimMarkerReclaimResetExactness:
    if isinstance(value, CachePreClaimMarkerReclaimResetExactness):
        return value
    return build_cache_pre_claim_marker_reclaim_reset_exactness(
        locality_lifetime_coupling=cache_pre_claim_marker_locality_lifetime_coupling
    )


def _coerce_cache_pre_claim_admission_carrier_construction(
    value: CachePreClaimAdmissionCarrierConstruction | None,
    *,
    cache_pre_claim_marker_reclaim_reset_exactness: CachePreClaimMarkerReclaimResetExactness,
) -> CachePreClaimAdmissionCarrierConstruction:
    if isinstance(value, CachePreClaimAdmissionCarrierConstruction):
        return value
    return build_cache_pre_claim_admission_carrier_construction(
        reclaim_reset=cache_pre_claim_marker_reclaim_reset_exactness
    )


def _coerce_cache_pre_claim_admission_carrier_field_exactness(
    value: CachePreClaimAdmissionCarrierFieldExactness | None,
    *,
    cache_pre_claim_admission_carrier_construction: CachePreClaimAdmissionCarrierConstruction,
) -> CachePreClaimAdmissionCarrierFieldExactness:
    if isinstance(value, CachePreClaimAdmissionCarrierFieldExactness):
        return value
    return build_cache_pre_claim_admission_carrier_field_exactness(
        construction=cache_pre_claim_admission_carrier_construction
    )


def _coerce_cache_pre_claim_admission_carrier_encoding_exactness(
    value: CachePreClaimAdmissionCarrierEncodingExactness | None,
    *,
    cache_pre_claim_admission_carrier_field_exactness: CachePreClaimAdmissionCarrierFieldExactness,
) -> CachePreClaimAdmissionCarrierEncodingExactness:
    if isinstance(value, CachePreClaimAdmissionCarrierEncodingExactness):
        return value
    return build_cache_pre_claim_admission_carrier_encoding_exactness(
        field_exactness=cache_pre_claim_admission_carrier_field_exactness
    )


def _coerce_cache_pre_claim_admission_carrier_locality_exactness(
    value: CachePreClaimAdmissionCarrierLocalityExactness | None,
    *,
    cache_pre_claim_admission_carrier_encoding_exactness: CachePreClaimAdmissionCarrierEncodingExactness,
) -> CachePreClaimAdmissionCarrierLocalityExactness:
    if isinstance(value, CachePreClaimAdmissionCarrierLocalityExactness):
        return value
    return build_cache_pre_claim_admission_carrier_locality_exactness(
        encoding_exactness=cache_pre_claim_admission_carrier_encoding_exactness
    )


def _coerce_cache_pre_claim_admission_carrier_locality_access_exactness(
    value: CachePreClaimAdmissionCarrierLocalityAccessExactness | None,
    *,
    cache_pre_claim_admission_carrier_locality_exactness: CachePreClaimAdmissionCarrierLocalityExactness,
) -> CachePreClaimAdmissionCarrierLocalityAccessExactness:
    if isinstance(value, CachePreClaimAdmissionCarrierLocalityAccessExactness):
        return value
    return build_cache_pre_claim_admission_carrier_locality_access_exactness(
        locality_exactness=cache_pre_claim_admission_carrier_locality_exactness
    )


def _coerce_cache_pre_claim_admission_carrier_locality_isolation_exactness(
    value: CachePreClaimAdmissionCarrierLocalityIsolationExactness | None,
    *,
    cache_pre_claim_admission_carrier_locality_access_exactness: CachePreClaimAdmissionCarrierLocalityAccessExactness,
) -> CachePreClaimAdmissionCarrierLocalityIsolationExactness:
    if isinstance(value, CachePreClaimAdmissionCarrierLocalityIsolationExactness):
        return value
    return build_cache_pre_claim_admission_carrier_locality_isolation_exactness(
        locality_access=cache_pre_claim_admission_carrier_locality_access_exactness
    )


def _coerce_cache_pre_claim_admission_carrier_locality_lifetime_coupling(
    value: CachePreClaimAdmissionCarrierLocalityLifetimeCoupling | None,
    *,
    cache_pre_claim_admission_carrier_locality_isolation_exactness: CachePreClaimAdmissionCarrierLocalityIsolationExactness,
) -> CachePreClaimAdmissionCarrierLocalityLifetimeCoupling:
    if isinstance(value, CachePreClaimAdmissionCarrierLocalityLifetimeCoupling):
        return value
    return build_cache_pre_claim_admission_carrier_locality_lifetime_coupling(
        locality_isolation=cache_pre_claim_admission_carrier_locality_isolation_exactness
    )


def _coerce_cache_pre_claim_admission_carrier_reclaim_reset_exactness(
    value: CachePreClaimAdmissionCarrierReclaimResetExactness | None,
    *,
    cache_pre_claim_admission_carrier_locality_lifetime_coupling: CachePreClaimAdmissionCarrierLocalityLifetimeCoupling,
) -> CachePreClaimAdmissionCarrierReclaimResetExactness:
    if isinstance(value, CachePreClaimAdmissionCarrierReclaimResetExactness):
        return value
    return build_cache_pre_claim_admission_carrier_reclaim_reset_exactness(
        locality_lifetime_coupling=cache_pre_claim_admission_carrier_locality_lifetime_coupling
    )


def _coerce_cache_pre_claim_admission_carrier_branch_reselection(
    value: CachePreClaimAdmissionCarrierBranchReselection | None,
    *,
    cache_pre_claim_admission_carrier_reclaim_reset_exactness: CachePreClaimAdmissionCarrierReclaimResetExactness,
) -> CachePreClaimAdmissionCarrierBranchReselection:
    if isinstance(value, CachePreClaimAdmissionCarrierBranchReselection):
        return value
    return build_cache_pre_claim_admission_carrier_branch_reselection(
        reclaim_reset_exactness=cache_pre_claim_admission_carrier_reclaim_reset_exactness
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
    cache_scheduler_turboquant_branch_reselection: CacheSchedulerTurboQuantBranchReselection | None = None,
    cache_continuous_batching_branch_reduction: CacheContinuousBatchingBranchReduction | None = None,
    cache_request_aggregation_window_reentry: CacheRequestAggregationWindowReentry | None = None,
    cache_request_aggregation_active_seam: CacheRequestAggregationActiveSeam | None = None,
    cache_pre_gate_admission_window_seam: CachePreGateAdmissionWindowSeam | None = None,
    cache_structural_ingress_seam: CacheStructuralIngressSeam | None = None,
    cache_continuous_batching_feasibility: CacheContinuousBatchingFeasibility | None = None,
    cache_batching_mechanism_subgap: CacheBatchingMechanismSubgap | None = None,
    cache_request_aggregation_window_exactness: CacheRequestAggregationWindowExactness | None = None,
    cache_pre_gate_cohort_window_feasibility: CachePreGateCohortWindowFeasibility | None = None,
    cache_pre_gate_admission_hook_exactness: CachePreGateAdmissionHookExactness | None = None,
    cache_admission_hook_safety_contract: CacheAdmissionHookSafetyContract | None = None,
    cache_pre_claim_admission_contract: CachePreClaimAdmissionContract | None = None,
    cache_pre_claim_staging_seam_exactness: CachePreClaimStagingSeamExactness | None = None,
    cache_pre_claim_metadata_ticket_ownership: CachePreClaimMetadataTicketOwnership | None = None,
    cache_pre_claim_inert_state_semantics: CachePreClaimInertStateSemantics | None = None,
    cache_pre_claim_marker_lifetime: CachePreClaimMarkerLifetime | None = None,
    cache_pre_claim_marker_visibility: CachePreClaimMarkerVisibility | None = None,
    cache_pre_claim_marker_trigger_inputs: CachePreClaimMarkerTriggerInputs | None = None,
    cache_pre_claim_marker_reader_writer_ownership: CachePreClaimMarkerReaderWriterOwnership | None = None,
    cache_pre_claim_marker_state_carrier: CachePreClaimMarkerStateCarrier | None = None,
    cache_pre_claim_marker_clear_observer_boundary: CachePreClaimMarkerClearObserverBoundary | None = None,
    cache_pre_claim_marker_immutability_boundary: CachePreClaimMarkerImmutabilityBoundary | None = None,
    cache_pre_claim_marker_payload_shape_exactness: CachePreClaimMarkerPayloadShapeExactness | None = None,
    cache_pre_claim_marker_encoding_carrier_exactness: CachePreClaimMarkerEncodingCarrierExactness | None = None,
    cache_pre_claim_marker_storage_locality_exactness: CachePreClaimMarkerStorageLocalityExactness | None = None,
    cache_pre_claim_marker_locality_access_exactness: CachePreClaimMarkerLocalityAccessExactness | None = None,
    cache_pre_claim_marker_locality_isolation_exactness: CachePreClaimMarkerLocalityIsolationExactness | None = None,
    cache_pre_claim_marker_locality_lifetime_coupling: CachePreClaimMarkerLocalityLifetimeCoupling | None = None,
    cache_pre_claim_marker_reclaim_reset_exactness: CachePreClaimMarkerReclaimResetExactness | None = None,
    cache_pre_claim_admission_carrier_construction: CachePreClaimAdmissionCarrierConstruction | None = None,
    cache_pre_claim_admission_carrier_field_exactness: CachePreClaimAdmissionCarrierFieldExactness | None = None,
    cache_pre_claim_admission_carrier_encoding_exactness: CachePreClaimAdmissionCarrierEncodingExactness | None = None,
    cache_pre_claim_admission_carrier_locality_exactness: CachePreClaimAdmissionCarrierLocalityExactness | None = None,
    cache_pre_claim_admission_carrier_locality_access_exactness: CachePreClaimAdmissionCarrierLocalityAccessExactness | None = None,
    cache_pre_claim_admission_carrier_locality_isolation_exactness: CachePreClaimAdmissionCarrierLocalityIsolationExactness | None = None,
    cache_pre_claim_admission_carrier_locality_lifetime_coupling: CachePreClaimAdmissionCarrierLocalityLifetimeCoupling | None = None,
    cache_pre_claim_admission_carrier_reclaim_reset_exactness: CachePreClaimAdmissionCarrierReclaimResetExactness | None = None,
    cache_pre_claim_admission_carrier_branch_reselection: CachePreClaimAdmissionCarrierBranchReselection | None = None,
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
    cache_pre_gate_admission_hook_exactness_status = (
        _coerce_cache_pre_gate_admission_hook_exactness(
            cache_pre_gate_admission_hook_exactness,
            cache_pre_gate_cohort_window_feasibility=cache_pre_gate_cohort_window_feasibility_status,
        )
    )
    cache_admission_hook_safety_contract_status = (
        _coerce_cache_admission_hook_safety_contract(
            cache_admission_hook_safety_contract,
            cache_pre_gate_admission_hook_exactness=cache_pre_gate_admission_hook_exactness_status,
        )
    )
    cache_pre_claim_admission_contract_status = (
        _coerce_cache_pre_claim_admission_contract(
            cache_pre_claim_admission_contract,
            cache_admission_hook_safety_contract=cache_admission_hook_safety_contract_status,
        )
    )
    cache_pre_claim_staging_seam_exactness_status = (
        _coerce_cache_pre_claim_staging_seam_exactness(
            cache_pre_claim_staging_seam_exactness,
            cache_pre_claim_admission_contract=cache_pre_claim_admission_contract_status,
        )
    )
    cache_pre_claim_metadata_ticket_ownership_status = (
        _coerce_cache_pre_claim_metadata_ticket_ownership(
            cache_pre_claim_metadata_ticket_ownership,
            cache_pre_claim_staging_seam_exactness=cache_pre_claim_staging_seam_exactness_status,
        )
    )
    cache_pre_claim_inert_state_semantics_status = (
        _coerce_cache_pre_claim_inert_state_semantics(
            cache_pre_claim_inert_state_semantics,
            cache_pre_claim_metadata_ticket_ownership=cache_pre_claim_metadata_ticket_ownership_status,
            cache_pre_gate_cohort_window_feasibility=cache_pre_gate_cohort_window_feasibility_status,
        )
    )
    cache_pre_claim_marker_lifetime_status = _coerce_cache_pre_claim_marker_lifetime(
        cache_pre_claim_marker_lifetime,
        cache_pre_claim_inert_state_semantics=cache_pre_claim_inert_state_semantics_status,
    )
    cache_pre_claim_marker_visibility_status = _coerce_cache_pre_claim_marker_visibility(
        cache_pre_claim_marker_visibility,
        cache_pre_claim_marker_lifetime=cache_pre_claim_marker_lifetime_status,
    )
    cache_pre_claim_marker_trigger_inputs_status = _coerce_cache_pre_claim_marker_trigger_inputs(
        cache_pre_claim_marker_trigger_inputs,
        cache_pre_claim_marker_visibility=cache_pre_claim_marker_visibility_status,
    )
    cache_pre_claim_marker_reader_writer_ownership_status = (
        _coerce_cache_pre_claim_marker_reader_writer_ownership(
            cache_pre_claim_marker_reader_writer_ownership,
            cache_pre_claim_marker_trigger_inputs=cache_pre_claim_marker_trigger_inputs_status,
        )
    )
    cache_pre_claim_marker_state_carrier_status = (
        _coerce_cache_pre_claim_marker_state_carrier(
            cache_pre_claim_marker_state_carrier,
            cache_pre_claim_marker_reader_writer_ownership=cache_pre_claim_marker_reader_writer_ownership_status,
        )
    )
    cache_pre_claim_marker_clear_observer_boundary_status = (
        _coerce_cache_pre_claim_marker_clear_observer_boundary(
            cache_pre_claim_marker_clear_observer_boundary,
            cache_pre_claim_marker_state_carrier=cache_pre_claim_marker_state_carrier_status,
        )
    )
    cache_pre_claim_marker_immutability_boundary_status = (
        _coerce_cache_pre_claim_marker_immutability_boundary(
            cache_pre_claim_marker_immutability_boundary,
            cache_pre_claim_marker_clear_observer_boundary=cache_pre_claim_marker_clear_observer_boundary_status,
        )
    )
    cache_pre_claim_marker_payload_shape_exactness_status = (
        _coerce_cache_pre_claim_marker_payload_shape_exactness(
            cache_pre_claim_marker_payload_shape_exactness,
            cache_pre_claim_marker_immutability_boundary=cache_pre_claim_marker_immutability_boundary_status,
        )
    )
    cache_pre_claim_marker_encoding_carrier_exactness_status = (
        _coerce_cache_pre_claim_marker_encoding_carrier_exactness(
            cache_pre_claim_marker_encoding_carrier_exactness,
            cache_pre_claim_marker_payload_shape_exactness=cache_pre_claim_marker_payload_shape_exactness_status,
        )
    )
    cache_pre_claim_marker_storage_locality_exactness_status = (
        _coerce_cache_pre_claim_marker_storage_locality_exactness(
            cache_pre_claim_marker_storage_locality_exactness,
            cache_pre_claim_marker_encoding_carrier_exactness=cache_pre_claim_marker_encoding_carrier_exactness_status,
        )
    )
    cache_pre_claim_marker_locality_access_exactness_status = (
        _coerce_cache_pre_claim_marker_locality_access_exactness(
            cache_pre_claim_marker_locality_access_exactness,
            cache_pre_claim_marker_storage_locality_exactness=cache_pre_claim_marker_storage_locality_exactness_status,
        )
    )
    cache_pre_claim_marker_locality_isolation_exactness_status = (
        _coerce_cache_pre_claim_marker_locality_isolation_exactness(
            cache_pre_claim_marker_locality_isolation_exactness,
            cache_pre_claim_marker_locality_access_exactness=cache_pre_claim_marker_locality_access_exactness_status,
        )
    )
    cache_pre_claim_marker_locality_lifetime_coupling_status = (
        _coerce_cache_pre_claim_marker_locality_lifetime_coupling(
            cache_pre_claim_marker_locality_lifetime_coupling,
            cache_pre_claim_marker_locality_isolation_exactness=cache_pre_claim_marker_locality_isolation_exactness_status,
        )
    )
    cache_pre_claim_marker_reclaim_reset_exactness_status = (
        _coerce_cache_pre_claim_marker_reclaim_reset_exactness(
            cache_pre_claim_marker_reclaim_reset_exactness,
            cache_pre_claim_marker_locality_lifetime_coupling=cache_pre_claim_marker_locality_lifetime_coupling_status,
        )
    )
    cache_pre_claim_admission_carrier_construction_status = (
        _coerce_cache_pre_claim_admission_carrier_construction(
            cache_pre_claim_admission_carrier_construction,
            cache_pre_claim_marker_reclaim_reset_exactness=cache_pre_claim_marker_reclaim_reset_exactness_status,
        )
    )
    cache_pre_claim_admission_carrier_field_exactness_status = (
        _coerce_cache_pre_claim_admission_carrier_field_exactness(
            cache_pre_claim_admission_carrier_field_exactness,
            cache_pre_claim_admission_carrier_construction=cache_pre_claim_admission_carrier_construction_status,
        )
    )
    cache_pre_claim_admission_carrier_encoding_exactness_status = (
        _coerce_cache_pre_claim_admission_carrier_encoding_exactness(
            cache_pre_claim_admission_carrier_encoding_exactness,
            cache_pre_claim_admission_carrier_field_exactness=cache_pre_claim_admission_carrier_field_exactness_status,
        )
    )
    cache_pre_claim_admission_carrier_locality_exactness_status = (
        _coerce_cache_pre_claim_admission_carrier_locality_exactness(
            cache_pre_claim_admission_carrier_locality_exactness,
            cache_pre_claim_admission_carrier_encoding_exactness=cache_pre_claim_admission_carrier_encoding_exactness_status,
        )
    )
    cache_pre_claim_admission_carrier_locality_access_exactness_status = (
        _coerce_cache_pre_claim_admission_carrier_locality_access_exactness(
            cache_pre_claim_admission_carrier_locality_access_exactness,
            cache_pre_claim_admission_carrier_locality_exactness=cache_pre_claim_admission_carrier_locality_exactness_status,
        )
    )
    cache_pre_claim_admission_carrier_locality_isolation_exactness_status = (
        _coerce_cache_pre_claim_admission_carrier_locality_isolation_exactness(
            cache_pre_claim_admission_carrier_locality_isolation_exactness,
            cache_pre_claim_admission_carrier_locality_access_exactness=cache_pre_claim_admission_carrier_locality_access_exactness_status,
        )
    )
    cache_pre_claim_admission_carrier_locality_lifetime_coupling_status = (
        _coerce_cache_pre_claim_admission_carrier_locality_lifetime_coupling(
            cache_pre_claim_admission_carrier_locality_lifetime_coupling,
            cache_pre_claim_admission_carrier_locality_isolation_exactness=cache_pre_claim_admission_carrier_locality_isolation_exactness_status,
        )
    )
    cache_pre_claim_admission_carrier_reclaim_reset_exactness_status = (
        _coerce_cache_pre_claim_admission_carrier_reclaim_reset_exactness(
            cache_pre_claim_admission_carrier_reclaim_reset_exactness,
            cache_pre_claim_admission_carrier_locality_lifetime_coupling=cache_pre_claim_admission_carrier_locality_lifetime_coupling_status,
        )
    )
    cache_pre_claim_admission_carrier_branch_reselection_status = (
        _coerce_cache_pre_claim_admission_carrier_branch_reselection(
            cache_pre_claim_admission_carrier_branch_reselection,
            cache_pre_claim_admission_carrier_reclaim_reset_exactness=cache_pre_claim_admission_carrier_reclaim_reset_exactness_status,
        )
    )
    cache_turboquant_preconditions_gap_status = (
        _coerce_cache_turboquant_preconditions_gap(
            cache_turboquant_preconditions_gap,
            cache_closure=cache_status,
        )
    )
    cache_scheduler_turboquant_branch_reselection_status = (
        _coerce_cache_scheduler_turboquant_branch_reselection(
            cache_scheduler_turboquant_branch_reselection,
            cache_pre_claim_admission_carrier_branch_reselection=cache_pre_claim_admission_carrier_branch_reselection_status,
            cache_scheduler_branch_selection=cache_scheduler_branch_selection_status,
            cache_turboquant_preconditions_gap=cache_turboquant_preconditions_gap_status,
        )
    )
    cache_continuous_batching_branch_reduction_status = (
        _coerce_cache_continuous_batching_branch_reduction(
            cache_continuous_batching_branch_reduction,
            cache_scheduler_turboquant_branch_reselection=cache_scheduler_turboquant_branch_reselection_status,
            cache_batching_mechanism_subgap=cache_batching_mechanism_subgap_status,
        )
    )
    cache_request_aggregation_window_reentry_status = (
        _coerce_cache_request_aggregation_window_reentry(
            cache_request_aggregation_window_reentry,
            cache_continuous_batching_branch_reduction=cache_continuous_batching_branch_reduction_status,
            cache_request_aggregation_window_exactness=cache_request_aggregation_window_exactness_status,
        )
    )
    cache_request_aggregation_active_seam_status = (
        _coerce_cache_request_aggregation_active_seam(
            cache_request_aggregation_active_seam,
            cache_request_aggregation_window_reentry=cache_request_aggregation_window_reentry_status,
            cache_request_aggregation_window_exactness=cache_request_aggregation_window_exactness_status,
        )
    )
    cache_pre_gate_admission_window_seam_status = (
        _coerce_cache_pre_gate_admission_window_seam(
            cache_pre_gate_admission_window_seam,
            cache_request_aggregation_active_seam=cache_request_aggregation_active_seam_status,
            cache_pre_gate_admission_hook_exactness=cache_pre_gate_admission_hook_exactness_status,
        )
    )
    cache_structural_ingress_seam_status = _coerce_cache_structural_ingress_seam(
        cache_structural_ingress_seam,
        cache_pre_gate_admission_window_seam=cache_pre_gate_admission_window_seam_status,
        cache_pre_claim_staging_seam_exactness=cache_pre_claim_staging_seam_exactness_status,
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
    elif (
        dominant_next_gap == "multi_model_lifecycle_governance"
        and governance_policy_gap.policy_gap_rung == "policy_gap_reduced"
    ):
        if governance_policy_gap.absent_policy_controls == ("eviction_history_governance",):
            recommended_next_step = (
                "treat governance as the active fallback branch on this host: runtime pinning and TTL policy now exist, so continue with eviction-history governance instead of reopening cache widening"
            )
        else:
            recommended_next_step = (
                "treat governance as the active fallback branch on this host: runtime pinning now exists, so continue with TTL policy or eviction-history governance instead of reopening cache widening"
            )
    elif (
        dominant_next_gap == "host_stable_execution"
        and governance_policy_gap.policy_gap_rung == "policy_gap_closed"
    ):
        blocked_reason = (
            "runtime-owned evidence has expanded and local governance fallback policy controls are now closed, but owlmlx still remains below reference-grade stability because supported-host heavy-weight proof is still externally blocked and cache remains frozen at a structural seam"
        )
        recommended_next_step = (
            "local governance fallback is now exhausted on this host; return to supported-host baseline establishment and do not reopen cache widening without fresh authorization"
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
                if (
                    cache_structural_ingress_seam_status.seam_rung
                    == "structural_ingress_seam_introduced"
                ):
                    recommended_next_step = (
                        "treat cache as structural ingress seam introduced only; the bounded pre-gate hook now exists before whole-request gate claim, but request aggregation, continuous batching, child parallelism, stream-path rewrites, and cache parity remain out of scope for this round, while the governance policy gap and supported-host blocker remain exact"
                    )
                elif (
                    cache_pre_gate_admission_window_seam_status.seam_rung
                    == "pre_gate_admission_window_seam_exact"
                ):
                    recommended_next_step = (
                        "treat cache as pre-gate admission-window seam work on this path; request aggregation remains the active cache subchain, the active seam is now the missing bounded pre-gate admission hook before whole-request gate claim, child exchange and stream hold stay secondary, TurboQuant remains exact-but-secondary, and the governance policy gap and supported-host blocker remain exact"
                    )
                elif (
                    cache_request_aggregation_active_seam_status.seam_rung
                    == "aggregation_active_seam_exact"
                ):
                    recommended_next_step = (
                        "treat cache as request-aggregation active-seam work on this path; request_aggregation_window remains the active cache subchain, the active seam is now the missing pre-gate admission window before whole-request gate claim, child exchange and stream hold stay secondary, TurboQuant remains exact-but-secondary, and the governance policy gap and supported-host blocker remain exact"
                    )
                elif (
                    cache_request_aggregation_window_reentry_status.reentry_rung
                    == "aggregation_reentry_exact"
                ):
                    recommended_next_step = (
                        "treat cache as request-aggregation-window reentry work on this path; scheduler depth remains the selected cache branch, continuous batching remains the selected scheduler sub-branch, request_aggregation_window is now the active reentered cache subchain, shared_prefill_batch_step and interleaved_decode_scheduler stay secondary, TurboQuant remains exact-but-secondary, and the governance policy gap and supported-host blocker remain exact"
                    )
                elif (
                    cache_continuous_batching_branch_reduction_status.reduction_rung
                    == "continuous_batching_branch_exact"
                ):
                    recommended_next_step = (
                        "treat cache as continuous-batching reduction work on this path; scheduler depth remains the selected cache branch, continuous batching remains the selected scheduler sub-branch, request_aggregation_window is now the next exact reduction target, shared_prefill_batch_step and interleaved_decode_scheduler stay secondary until aggregated admission exists, TurboQuant remains exact-but-secondary, and the governance policy gap and supported-host blocker remain exact"
                    )
                elif (
                    cache_scheduler_turboquant_branch_reselection_status.reselection_rung
                    == "scheduler_turboquant_branch_exact"
                ):
                    recommended_next_step = (
                        "treat cache as scheduler-depth work on this path; the carrier-local exactness chain is complete, scheduler depth is reselected as the next honest cache branch, TurboQuant stays exact-but-secondary, post-claim max_concurrent=1 and ticketed FIFO remain unchanged, the child protocol and stream path still assume one request at a time, multi-worker depth stays secondary pending concurrency revalidation, and the governance policy gap and supported-host blocker remain exact"
                    )
                elif (
                    cache_pre_claim_admission_carrier_branch_reselection_status.reselection_rung
                    == "carrier_branch_reselection_exact"
                ):
                    recommended_next_step = (
                        "treat cache as scheduler-vs-TurboQuant branch reselection work on this path; the admission-carrier exactness chain is now complete, so any next cache reduction must move outside the carrier-local branch without weakening the already-frozen ingress invariants, post-claim max_concurrent=1 and ticketed FIFO remain unchanged, the child protocol and stream path still assume one request at a time, multi-worker depth stays secondary pending concurrency revalidation, TurboQuant preconditions remain exact-but-secondary, and the governance policy gap and supported-host blocker remain exact"
                    )
                elif (
                    cache_pre_claim_admission_carrier_reclaim_reset_exactness_status.exactness_rung
                    == "admission_carrier_reclaim_reset_exact"
                ):
                    recommended_next_step = (
                        "treat cache as admission-carrier branch reselection work on this path; the bounded inert pre-claim carrier now resets to a fully empty inert state before any later reuse, no prior request history or execution-bearing residue may survive reclaim, ticket reservation must remain observational-only, immutable request metadata must remain read-only, post-claim max_concurrent=1 and ticketed FIFO must remain unchanged, the child protocol and stream path still assume one request at a time, multi-worker depth stays secondary pending concurrency revalidation, TurboQuant preconditions are also exact-but-secondary, and the governance policy gap and supported-host blocker remain exact"
                    )
                elif (
                    cache_pre_claim_admission_carrier_locality_lifetime_coupling_status.exactness_rung
                    == "admission_carrier_locality_lifetime_coupling_exact"
                ):
                    recommended_next_step = (
                        "treat cache as admission-carrier reclaim-reset exactness work on this path; the bounded inert pre-claim carrier is now coupled only to its own staged-request lifetime before claim, reclaimed only by same-request pre-claim discard or gate-claim expiry transition, may not survive into cross-request reuse or retained scheduler/backend/stream lifetime, only staged metadata snapshot building, observational ticket reservation, same-request pre-claim drop/cancel reset, and same-request pre-claim discard observation may reach it, the carrier remains isolated per staged request and lives only in single-request staged locality adjacent to metadata/ticket state, ticket reservation must remain observational-only, immutable request metadata must remain read-only, post-claim max_concurrent=1 and ticketed FIFO must remain unchanged, the child protocol and stream path still assume one request at a time, multi-worker depth stays secondary pending concurrency revalidation, TurboQuant preconditions are also exact-but-secondary, and the governance policy gap and supported-host blocker remain exact"
                    )
                elif (
                    cache_pre_claim_admission_carrier_locality_isolation_exactness_status.exactness_rung
                    == "admission_carrier_locality_isolation_exact"
                ):
                    recommended_next_step = (
                        "treat cache as admission-carrier locality-lifetime coupling work on this path; the bounded inert pre-claim carrier now remains isolated per staged request before claim, no shared scheduler/backend/stream pending-state carrier locality or cross-request carrier merge may exist, only staged metadata snapshot building, observational ticket reservation, same-request pre-claim drop/cancel reset, and same-request pre-claim discard observation may reach it, the carrier still lives only in single-request staged locality adjacent to metadata/ticket state, ticket reservation must remain observational-only, immutable request metadata must remain read-only, post-claim max_concurrent=1 and ticketed FIFO must remain unchanged, the child protocol and stream path still assume one request at a time, multi-worker depth stays secondary pending concurrency revalidation, TurboQuant preconditions are also exact-but-secondary, and the governance policy gap and supported-host blocker remain exact"
                    )
                elif (
                    cache_pre_claim_admission_carrier_locality_access_exactness_status.exactness_rung
                    == "admission_carrier_locality_access_exact"
                ):
                    recommended_next_step = (
                        "treat cache as admission-carrier locality-isolation exactness work on this path; only staged metadata snapshot building, observational ticket reservation, same-request pre-claim drop/cancel reset, and same-request pre-claim discard observation may reach the bounded inert pre-claim carrier before claim, queue/cohort scheduler, child/backend payload, stream-handle, and execution-entitlement paths may not access it, the carrier still lives only in single-request staged locality adjacent to metadata/ticket state, ticket reservation must remain observational-only, immutable request metadata must remain read-only, post-claim max_concurrent=1 and ticketed FIFO must remain unchanged, the child protocol and stream path still assume one request at a time, multi-worker depth stays secondary pending concurrency revalidation, TurboQuant preconditions are also exact-but-secondary, and the governance policy gap and supported-host blocker remain exact"
                    )
                elif (
                    cache_pre_claim_admission_carrier_locality_exactness_status.exactness_rung
                    == "admission_carrier_locality_exact"
                ):
                    recommended_next_step = (
                        "treat cache as admission-carrier locality-access exactness work on this path; the bounded inert pre-claim carrier may now live only in single-request staged locality adjacent to metadata/ticket state and outside queue, scheduler, child/stream, and execution-owned locality, ticket reservation must remain observational-only, immutable request metadata must remain read-only, post-claim max_concurrent=1 and ticketed FIFO must remain unchanged, the child protocol and stream path still assume one request at a time, multi-worker depth stays secondary pending concurrency revalidation, TurboQuant preconditions are also exact-but-secondary, and the governance policy gap and supported-host blocker remain exact"
                    )
                elif (
                    cache_pre_claim_admission_carrier_encoding_exactness_status.exactness_rung
                    == "admission_carrier_encoding_exact"
                ):
                    recommended_next_step = (
                        "treat cache as admission-carrier locality exactness work on this path; a bounded pre-claim carrier now encodes immutable request metadata, observational ticket reservation, and a fully reset inert marker presence bit only as one inert pre-claim record, no queue identity, scheduler priority, batch membership, child/stream attachment, or execution-bearing encoding may exist before claim, ticket reservation must remain observational-only, immutable request metadata must remain read-only, post-claim max_concurrent=1 and ticketed FIFO must remain unchanged, the child protocol and stream path still assume one request at a time, multi-worker depth stays secondary pending concurrency revalidation, TurboQuant preconditions are also exact-but-secondary, and the governance policy gap and supported-host blocker remain exact"
                    )
                elif (
                    cache_pre_claim_admission_carrier_field_exactness_status.exactness_rung
                    == "admission_carrier_field_exact"
                ):
                    recommended_next_step = (
                        "treat cache as admission-carrier field-encoding exactness work on this path; a bounded pre-claim carrier is now frozen to immutable request metadata, observational ticket reservation, and a fully reset inert marker presence bit only, no queue identity, scheduler priority, batch membership, child/stream attachment, or execution-bearing field may exist before claim, ticket reservation must remain observational-only, immutable request metadata must remain read-only, post-claim max_concurrent=1 and ticketed FIFO must remain unchanged, the child protocol and stream path still assume one request at a time, multi-worker depth stays secondary pending concurrency revalidation, TurboQuant preconditions are also exact-but-secondary, and the governance policy gap and supported-host blocker remain exact"
                    )
                elif (
                    cache_pre_claim_admission_carrier_construction_status.exactness_rung
                    == "admission_carrier_construction_exact"
                ):
                    recommended_next_step = (
                        "treat cache as admission-carrier field exactness work on this path; any bounded pre-claim carrier is now frozen to immutable request metadata, observational ticket reservation, and a fully reset inert marker slot only, no queue-owned or execution-bearing carrier may exist before claim, ticket reservation must remain observational-only, immutable request metadata must remain read-only, post-claim max_concurrent=1 and ticketed FIFO must remain unchanged, the child protocol and stream path still assume one request at a time, multi-worker depth stays secondary pending concurrency revalidation, TurboQuant preconditions are also exact-but-secondary, and the governance policy gap and supported-host blocker remain exact"
                    )
                elif (
                    cache_pre_claim_marker_reclaim_reset_exactness_status.exactness_rung
                    == "reclaim_reset_exact"
                ):
                    recommended_next_step = (
                        "treat cache as pre-claim admission-carrier construction work on this path; reclaim now resets the adjacent marker slot to a fully inert empty state before any later reuse, no stale history or execution-bearing residue may survive reclaim, ticket reservation must remain observational-only, immutable request metadata must remain read-only, post-claim max_concurrent=1 and ticketed FIFO must remain unchanged, the child protocol and stream path still assume one request at a time, multi-worker depth stays secondary pending concurrency revalidation, TurboQuant preconditions are also exact-but-secondary, and the governance policy gap and supported-host blocker remain exact"
                    )
                elif (
                    cache_pre_claim_marker_locality_lifetime_coupling_status.exactness_rung
                    == "locality_lifetime_coupling_exact"
                ):
                    recommended_next_step = (
                        "treat cache as marker reclaim-reset exactness work on this path; isolated marker locality is now coupled only to its own staged-request lifetime, reclaim may occur only by same-request pre-claim discard or gate-claim expiry, no cross-request slot reuse or scheduler/backend/stream-retained lifetime may exist before claim, ticket reservation must remain observational-only, immutable request metadata must remain read-only, post-claim max_concurrent=1 and ticketed FIFO must remain unchanged, the child protocol and stream path still assume one request at a time, multi-worker depth stays secondary pending concurrency revalidation, TurboQuant preconditions are also exact-but-secondary, and the governance policy gap and supported-host blocker remain exact"
                    )
                elif (
                    cache_pre_claim_marker_locality_isolation_exactness_status.exactness_rung
                    == "locality_isolation_exact"
                ):
                    recommended_next_step = (
                        "treat cache as marker locality-lifetime coupling work on this path; the adjacent inert marker slot is now isolated per staged request, no shared pending-state locality may exist before whole-request gate claim, ticket reservation must remain observational-only, immutable request metadata must remain read-only, post-claim max_concurrent=1 and ticketed FIFO must remain unchanged, the child protocol and stream path still assume one request at a time, multi-worker depth stays secondary pending concurrency revalidation, TurboQuant preconditions are also exact-but-secondary, and the governance policy gap and supported-host blocker remain exact"
                    )
                elif (
                    cache_pre_claim_marker_locality_access_exactness_status.exactness_rung
                    == "locality_access_exact"
                ):
                    recommended_next_step = (
                        "treat cache as marker locality-isolation work on this path; only explicit pre-claim drop/cancel logic, gate-claim expiry, and pre-claim discard observation may reach the adjacent inert marker slot, no scheduler or backend path may access it before whole-request gate claim, ticket reservation must remain observational-only, immutable request metadata must remain read-only, post-claim max_concurrent=1 and ticketed FIFO must remain unchanged, the child protocol and stream path still assume one request at a time, multi-worker depth stays secondary pending concurrency revalidation, TurboQuant preconditions are also exact-but-secondary, and the governance policy gap and supported-host blocker remain exact"
                    )
                elif (
                    cache_pre_claim_marker_storage_locality_exactness_status.exactness_rung
                    == "storage_locality_exact"
                ):
                    recommended_next_step = (
                        "treat cache as marker locality-access work on this path; the inert boolean marker slot now lives only adjacent to staged metadata and outside ticket identity, no queue or scheduler locality may own it before whole-request gate claim, ticket reservation must remain observational-only, immutable request metadata must remain read-only, post-claim max_concurrent=1 and ticketed FIFO must remain unchanged, the child protocol and stream path still assume one request at a time, multi-worker depth stays secondary pending concurrency revalidation, TurboQuant preconditions are also exact-but-secondary, and the governance policy gap and supported-host blocker remain exact"
                    )
                elif (
                    cache_pre_claim_marker_encoding_carrier_exactness_status.exactness_rung
                    == "encoding_carrier_exact"
                ):
                    recommended_next_step = (
                        "treat cache as marker storage-locality work on this path; pre-claim marker presence now lives only in one inert boolean slot, no queue or ticket identity may be encoded before whole-request gate claim, ticket reservation must remain observational-only, immutable request metadata must remain read-only, post-claim max_concurrent=1 and ticketed FIFO must remain unchanged, the child protocol and stream path still assume one request at a time, multi-worker depth stays secondary pending concurrency revalidation, TurboQuant preconditions are also exact-but-secondary, and the governance policy gap and supported-host blocker remain exact"
                    )
                elif (
                    cache_pre_claim_marker_payload_shape_exactness_status.exactness_rung
                    == "payload_shape_exact"
                ):
                    recommended_next_step = (
                        "treat cache as marker encoding work on this path; pre-claim marker state now collapses to pure presence/absence only, no reason-code or priority payload may exist before whole-request gate claim, ticket reservation must remain observational-only, immutable request metadata must remain read-only, post-claim max_concurrent=1 and ticketed FIFO must remain unchanged, the child protocol and stream path still assume one request at a time, multi-worker depth stays secondary pending concurrency revalidation, TurboQuant preconditions are also exact-but-secondary, and the governance policy gap and supported-host blocker remain exact"
                    )
                elif (
                    cache_pre_claim_marker_immutability_boundary_status.exactness_rung
                    == "immutability_boundary_exact"
                ):
                    recommended_next_step = (
                        "treat cache as marker payload-shape work on this path; marker state may only change by clear-only semantics before whole-request gate claim, no pre-claim path may rewrite payload or priority, ticket reservation must remain observational-only, immutable request metadata must remain read-only, post-claim max_concurrent=1 and ticketed FIFO must remain unchanged, the child protocol and stream path still assume one request at a time, multi-worker depth stays secondary pending concurrency revalidation, TurboQuant preconditions are also exact-but-secondary, and the governance policy gap and supported-host blocker remain exact"
                    )
                elif (
                    cache_pre_claim_marker_clear_observer_boundary_status.exactness_rung
                    == "clear_observer_boundary_exact"
                ):
                    recommended_next_step = (
                        "treat cache as marker immutability work on this path; only explicit pre-claim drop/cancel logic and gate-claim expiry may clear the inert marker carrier, pre-claim discard may only observe it, no pre-claim path may acquire hidden marker mutation rights beyond clear-only semantics, ticket reservation must remain observational-only, immutable request metadata must remain read-only before whole-request gate claim, post-claim max_concurrent=1 and ticketed FIFO must remain unchanged, the child protocol and stream path still assume one request at a time, multi-worker depth stays secondary pending concurrency revalidation, TurboQuant preconditions are also exact-but-secondary, and the governance policy gap and supported-host blocker remain exact"
                    )
                else:
                    recommended_next_step = (
                        "treat cache as marker clear-observer boundary work on this path; only explicit pre-claim drop/cancel logic and gate-claim expiry may clear the inert marker carrier, pre-claim discard may only observe it, marker clear ownership may not leak into scheduler selection or execution routing, ticket reservation must remain observational-only, immutable request metadata must remain read-only before whole-request gate claim, post-claim max_concurrent=1 and ticketed FIFO must remain unchanged, the child protocol and stream path still assume one request at a time, multi-worker depth stays secondary pending concurrency revalidation, TurboQuant preconditions are also exact-but-secondary, and the governance policy gap and supported-host blocker remain exact"
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
        cache_scheduler_turboquant_branch_reselection=cache_scheduler_turboquant_branch_reselection_status,
        cache_continuous_batching_branch_reduction=cache_continuous_batching_branch_reduction_status,
        cache_request_aggregation_window_reentry=cache_request_aggregation_window_reentry_status,
        cache_request_aggregation_active_seam=cache_request_aggregation_active_seam_status,
        cache_pre_gate_admission_window_seam=cache_pre_gate_admission_window_seam_status,
        cache_structural_ingress_seam=cache_structural_ingress_seam_status,
        cache_continuous_batching_feasibility=cache_continuous_batching_feasibility_status,
        cache_batching_mechanism_subgap=cache_batching_mechanism_subgap_status,
        cache_request_aggregation_window_exactness=cache_request_aggregation_window_exactness_status,
        cache_pre_gate_cohort_window_feasibility=cache_pre_gate_cohort_window_feasibility_status,
        cache_pre_gate_admission_hook_exactness=cache_pre_gate_admission_hook_exactness_status,
        cache_admission_hook_safety_contract=cache_admission_hook_safety_contract_status,
        cache_pre_claim_admission_contract=cache_pre_claim_admission_contract_status,
        cache_pre_claim_staging_seam_exactness=cache_pre_claim_staging_seam_exactness_status,
        cache_pre_claim_metadata_ticket_ownership=cache_pre_claim_metadata_ticket_ownership_status,
        cache_pre_claim_inert_state_semantics=cache_pre_claim_inert_state_semantics_status,
        cache_pre_claim_marker_lifetime=cache_pre_claim_marker_lifetime_status,
        cache_pre_claim_marker_visibility=cache_pre_claim_marker_visibility_status,
        cache_pre_claim_marker_trigger_inputs=cache_pre_claim_marker_trigger_inputs_status,
        cache_pre_claim_marker_reader_writer_ownership=cache_pre_claim_marker_reader_writer_ownership_status,
        cache_pre_claim_marker_state_carrier=cache_pre_claim_marker_state_carrier_status,
        cache_pre_claim_marker_clear_observer_boundary=cache_pre_claim_marker_clear_observer_boundary_status,
        cache_pre_claim_marker_immutability_boundary=cache_pre_claim_marker_immutability_boundary_status,
        cache_pre_claim_marker_payload_shape_exactness=cache_pre_claim_marker_payload_shape_exactness_status,
        cache_pre_claim_marker_encoding_carrier_exactness=cache_pre_claim_marker_encoding_carrier_exactness_status,
        cache_pre_claim_marker_storage_locality_exactness=cache_pre_claim_marker_storage_locality_exactness_status,
        cache_pre_claim_marker_locality_access_exactness=cache_pre_claim_marker_locality_access_exactness_status,
        cache_pre_claim_marker_locality_isolation_exactness=cache_pre_claim_marker_locality_isolation_exactness_status,
        cache_pre_claim_marker_locality_lifetime_coupling=cache_pre_claim_marker_locality_lifetime_coupling_status,
        cache_pre_claim_marker_reclaim_reset_exactness=cache_pre_claim_marker_reclaim_reset_exactness_status,
        cache_pre_claim_admission_carrier_construction=cache_pre_claim_admission_carrier_construction_status,
        cache_pre_claim_admission_carrier_field_exactness=cache_pre_claim_admission_carrier_field_exactness_status,
        cache_pre_claim_admission_carrier_encoding_exactness=cache_pre_claim_admission_carrier_encoding_exactness_status,
        cache_pre_claim_admission_carrier_locality_exactness=cache_pre_claim_admission_carrier_locality_exactness_status,
        cache_pre_claim_admission_carrier_locality_access_exactness=cache_pre_claim_admission_carrier_locality_access_exactness_status,
        cache_pre_claim_admission_carrier_locality_isolation_exactness=cache_pre_claim_admission_carrier_locality_isolation_exactness_status,
        cache_pre_claim_admission_carrier_locality_lifetime_coupling=cache_pre_claim_admission_carrier_locality_lifetime_coupling_status,
        cache_pre_claim_admission_carrier_reclaim_reset_exactness=cache_pre_claim_admission_carrier_reclaim_reset_exactness_status,
        cache_pre_claim_admission_carrier_branch_reselection=cache_pre_claim_admission_carrier_branch_reselection_status,
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
    if ledger.multi_model_governance_policy_gap.policy_gap_rung in {
        "policy_gap_exact",
        "policy_gap_reduced",
        "policy_gap_closed",
    }:
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
    if (
        ledger.cache_pre_gate_admission_hook_exactness.exactness_rung
        == "admission_hook_blocker_exact"
    ):
        cache_surface = _CONTRACT_SURFACES[
            "cache_scheduler_depth_pre_gate_admission_hook_exactness"
        ]
        cache_closure_level = (
            ledger.cache_pre_gate_admission_hook_exactness.exactness_rung
        )
        cache_blocked_reason = (
            ledger.cache_pre_gate_admission_hook_exactness.residual_blocker
        )
    if (
        ledger.cache_admission_hook_safety_contract.contract_rung
        == "safety_contract_exact"
    ):
        cache_surface = _CONTRACT_SURFACES[
            "cache_scheduler_depth_admission_hook_safety_contract"
        ]
        cache_closure_level = (
            ledger.cache_admission_hook_safety_contract.contract_rung
        )
        cache_blocked_reason = (
            ledger.cache_admission_hook_safety_contract.residual_blocker
        )
    if (
        ledger.cache_pre_claim_admission_contract.contract_rung
        == "pre_claim_contract_exact"
    ):
        cache_surface = _CONTRACT_SURFACES[
            "cache_scheduler_depth_pre_claim_admission_contract"
        ]
        cache_closure_level = (
            ledger.cache_pre_claim_admission_contract.contract_rung
        )
        cache_blocked_reason = (
            ledger.cache_pre_claim_admission_contract.residual_blocker
        )
    if (
        ledger.cache_pre_claim_staging_seam_exactness.exactness_rung
        == "staging_seam_exact"
    ):
        cache_surface = _CONTRACT_SURFACES[
            "cache_scheduler_depth_pre_claim_staging_seam_exactness"
        ]
        cache_closure_level = (
            ledger.cache_pre_claim_staging_seam_exactness.exactness_rung
        )
        cache_blocked_reason = (
            ledger.cache_pre_claim_staging_seam_exactness.residual_blocker
        )
    if (
        ledger.cache_pre_claim_metadata_ticket_ownership.exactness_rung
        == "ownership_boundary_exact"
    ):
        cache_surface = _CONTRACT_SURFACES[
            "cache_scheduler_depth_pre_claim_metadata_ticket_ownership"
        ]
        cache_closure_level = (
            ledger.cache_pre_claim_metadata_ticket_ownership.exactness_rung
        )
        cache_blocked_reason = (
            ledger.cache_pre_claim_metadata_ticket_ownership.residual_blocker
        )
    if (
        ledger.cache_pre_claim_inert_state_semantics.exactness_rung
        == "inert_state_semantics_exact"
    ):
        cache_surface = _CONTRACT_SURFACES[
            "cache_scheduler_depth_pre_claim_inert_state_semantics"
        ]
        cache_closure_level = (
            ledger.cache_pre_claim_inert_state_semantics.exactness_rung
        )
        cache_blocked_reason = (
            ledger.cache_pre_claim_inert_state_semantics.residual_blocker
        )
    if ledger.cache_pre_claim_marker_lifetime.exactness_rung == "marker_lifetime_exact":
        cache_surface = _CONTRACT_SURFACES[
            "cache_scheduler_depth_pre_claim_marker_lifetime"
        ]
        cache_closure_level = ledger.cache_pre_claim_marker_lifetime.exactness_rung
        cache_blocked_reason = ledger.cache_pre_claim_marker_lifetime.residual_blocker
    if ledger.cache_pre_claim_marker_visibility.exactness_rung == "marker_visibility_exact":
        cache_surface = _CONTRACT_SURFACES[
            "cache_scheduler_depth_pre_claim_marker_visibility"
        ]
        cache_closure_level = ledger.cache_pre_claim_marker_visibility.exactness_rung
        cache_blocked_reason = ledger.cache_pre_claim_marker_visibility.residual_blocker
    if ledger.cache_pre_claim_marker_trigger_inputs.exactness_rung == "trigger_inputs_exact":
        cache_surface = _CONTRACT_SURFACES[
            "cache_scheduler_depth_pre_claim_marker_trigger_inputs"
        ]
        cache_closure_level = ledger.cache_pre_claim_marker_trigger_inputs.exactness_rung
        cache_blocked_reason = ledger.cache_pre_claim_marker_trigger_inputs.residual_blocker
    if (
        ledger.cache_pre_claim_marker_reader_writer_ownership.exactness_rung
        == "reader_writer_ownership_exact"
    ):
        cache_surface = _CONTRACT_SURFACES[
            "cache_scheduler_depth_pre_claim_marker_reader_writer_ownership"
        ]
        cache_closure_level = (
            ledger.cache_pre_claim_marker_reader_writer_ownership.exactness_rung
        )
        cache_blocked_reason = (
            ledger.cache_pre_claim_marker_reader_writer_ownership.residual_blocker
        )
    if ledger.cache_pre_claim_marker_state_carrier.exactness_rung == "state_carrier_exact":
        cache_surface = _CONTRACT_SURFACES[
            "cache_scheduler_depth_pre_claim_marker_state_carrier"
        ]
        cache_closure_level = ledger.cache_pre_claim_marker_state_carrier.exactness_rung
        cache_blocked_reason = ledger.cache_pre_claim_marker_state_carrier.residual_blocker
    if (
        ledger.cache_pre_claim_marker_clear_observer_boundary.exactness_rung
        == "clear_observer_boundary_exact"
    ):
        cache_surface = _CONTRACT_SURFACES[
            "cache_scheduler_depth_pre_claim_marker_clear_observer_boundary"
        ]
        cache_closure_level = (
            ledger.cache_pre_claim_marker_clear_observer_boundary.exactness_rung
        )
        cache_blocked_reason = (
            ledger.cache_pre_claim_marker_clear_observer_boundary.residual_blocker
        )
    if (
        ledger.cache_pre_claim_marker_immutability_boundary.exactness_rung
        == "immutability_boundary_exact"
    ):
        cache_surface = _CONTRACT_SURFACES[
            "cache_scheduler_depth_pre_claim_marker_immutability_boundary"
        ]
        cache_closure_level = (
            ledger.cache_pre_claim_marker_immutability_boundary.exactness_rung
        )
        cache_blocked_reason = (
            ledger.cache_pre_claim_marker_immutability_boundary.residual_blocker
        )
    if (
        ledger.cache_pre_claim_marker_payload_shape_exactness.exactness_rung
        == "payload_shape_exact"
    ):
        cache_surface = _CONTRACT_SURFACES[
            "cache_scheduler_depth_pre_claim_marker_payload_shape_exactness"
        ]
        cache_closure_level = (
            ledger.cache_pre_claim_marker_payload_shape_exactness.exactness_rung
        )
        cache_blocked_reason = (
            ledger.cache_pre_claim_marker_payload_shape_exactness.residual_blocker
        )
    if (
        ledger.cache_pre_claim_marker_encoding_carrier_exactness.exactness_rung
        == "encoding_carrier_exact"
    ):
        cache_surface = _CONTRACT_SURFACES[
            "cache_scheduler_depth_pre_claim_marker_encoding_carrier_exactness"
        ]
        cache_closure_level = (
            ledger.cache_pre_claim_marker_encoding_carrier_exactness.exactness_rung
        )
        cache_blocked_reason = (
            ledger.cache_pre_claim_marker_encoding_carrier_exactness.residual_blocker
        )
    if (
        ledger.cache_pre_claim_marker_storage_locality_exactness.exactness_rung
        == "storage_locality_exact"
    ):
        cache_surface = _CONTRACT_SURFACES[
            "cache_scheduler_depth_pre_claim_marker_storage_locality_exactness"
        ]
        cache_closure_level = (
            ledger.cache_pre_claim_marker_storage_locality_exactness.exactness_rung
        )
        cache_blocked_reason = (
            ledger.cache_pre_claim_marker_storage_locality_exactness.residual_blocker
        )
    if (
        ledger.cache_pre_claim_marker_locality_access_exactness.exactness_rung
        == "locality_access_exact"
    ):
        cache_surface = _CONTRACT_SURFACES[
            "cache_scheduler_depth_pre_claim_marker_locality_access_exactness"
        ]
        cache_closure_level = (
            ledger.cache_pre_claim_marker_locality_access_exactness.exactness_rung
        )
        cache_blocked_reason = (
            ledger.cache_pre_claim_marker_locality_access_exactness.residual_blocker
        )
    if (
        ledger.cache_pre_claim_marker_locality_isolation_exactness.exactness_rung
        == "locality_isolation_exact"
    ):
        cache_surface = _CONTRACT_SURFACES[
            "cache_scheduler_depth_pre_claim_marker_locality_isolation_exactness"
        ]
        cache_closure_level = (
            ledger.cache_pre_claim_marker_locality_isolation_exactness.exactness_rung
        )
        cache_blocked_reason = (
            ledger.cache_pre_claim_marker_locality_isolation_exactness.residual_blocker
        )
    if (
        ledger.cache_pre_claim_marker_locality_lifetime_coupling.exactness_rung
        == "locality_lifetime_coupling_exact"
    ):
        cache_surface = _CONTRACT_SURFACES[
            "cache_scheduler_depth_pre_claim_marker_locality_lifetime_coupling"
        ]
        cache_closure_level = (
            ledger.cache_pre_claim_marker_locality_lifetime_coupling.exactness_rung
        )
        cache_blocked_reason = (
            ledger.cache_pre_claim_marker_locality_lifetime_coupling.residual_blocker
        )
    if (
        ledger.cache_pre_claim_marker_reclaim_reset_exactness.exactness_rung
        == "reclaim_reset_exact"
    ):
        cache_surface = _CONTRACT_SURFACES[
            "cache_scheduler_depth_pre_claim_marker_reclaim_reset_exactness"
        ]
        cache_closure_level = (
            ledger.cache_pre_claim_marker_reclaim_reset_exactness.exactness_rung
        )
        cache_blocked_reason = (
            ledger.cache_pre_claim_marker_reclaim_reset_exactness.residual_blocker
        )
    if (
        ledger.cache_pre_claim_admission_carrier_construction.exactness_rung
        == "admission_carrier_construction_exact"
    ):
        cache_surface = _CONTRACT_SURFACES[
            "cache_scheduler_depth_pre_claim_admission_carrier_construction"
        ]
        cache_closure_level = (
            ledger.cache_pre_claim_admission_carrier_construction.exactness_rung
        )
        cache_blocked_reason = (
            ledger.cache_pre_claim_admission_carrier_construction.residual_blocker
        )
    if (
        ledger.cache_pre_claim_admission_carrier_field_exactness.exactness_rung
        == "admission_carrier_field_exact"
    ):
        cache_surface = _CONTRACT_SURFACES[
            "cache_scheduler_depth_pre_claim_admission_carrier_field_exactness"
        ]
        cache_closure_level = (
            ledger.cache_pre_claim_admission_carrier_field_exactness.exactness_rung
        )
        cache_blocked_reason = (
            ledger.cache_pre_claim_admission_carrier_field_exactness.residual_blocker
        )
    if (
        ledger.cache_pre_claim_admission_carrier_encoding_exactness.exactness_rung
        == "admission_carrier_encoding_exact"
    ):
        cache_surface = _CONTRACT_SURFACES[
            "cache_scheduler_depth_pre_claim_admission_carrier_encoding_exactness"
        ]
        cache_closure_level = (
            ledger.cache_pre_claim_admission_carrier_encoding_exactness.exactness_rung
        )
        cache_blocked_reason = (
            ledger.cache_pre_claim_admission_carrier_encoding_exactness.residual_blocker
        )
    if (
        ledger.cache_pre_claim_admission_carrier_locality_exactness.exactness_rung
        == "admission_carrier_locality_exact"
    ):
        cache_surface = _CONTRACT_SURFACES[
            "cache_scheduler_depth_pre_claim_admission_carrier_locality_exactness"
        ]
        cache_closure_level = (
            ledger.cache_pre_claim_admission_carrier_locality_exactness.exactness_rung
        )
        cache_blocked_reason = (
            ledger.cache_pre_claim_admission_carrier_locality_exactness.residual_blocker
        )
    if (
        ledger.cache_pre_claim_admission_carrier_locality_access_exactness.exactness_rung
        == "admission_carrier_locality_access_exact"
    ):
        cache_surface = _CONTRACT_SURFACES[
            "cache_scheduler_depth_pre_claim_admission_carrier_locality_access_exactness"
        ]
        cache_closure_level = (
            ledger.cache_pre_claim_admission_carrier_locality_access_exactness.exactness_rung
        )
        cache_blocked_reason = (
            ledger.cache_pre_claim_admission_carrier_locality_access_exactness.residual_blocker
        )
    if (
        ledger.cache_pre_claim_admission_carrier_locality_isolation_exactness.exactness_rung
        == "admission_carrier_locality_isolation_exact"
    ):
        cache_surface = _CONTRACT_SURFACES[
            "cache_scheduler_depth_pre_claim_admission_carrier_locality_isolation_exactness"
        ]
        cache_closure_level = (
            ledger.cache_pre_claim_admission_carrier_locality_isolation_exactness.exactness_rung
        )
        cache_blocked_reason = (
            ledger.cache_pre_claim_admission_carrier_locality_isolation_exactness.residual_blocker
        )
    if (
        ledger.cache_pre_claim_admission_carrier_locality_lifetime_coupling.exactness_rung
        == "admission_carrier_locality_lifetime_coupling_exact"
    ):
        cache_surface = _CONTRACT_SURFACES[
            "cache_scheduler_depth_pre_claim_admission_carrier_locality_lifetime_coupling"
        ]
        cache_closure_level = (
            ledger.cache_pre_claim_admission_carrier_locality_lifetime_coupling.exactness_rung
        )
        cache_blocked_reason = (
            ledger.cache_pre_claim_admission_carrier_locality_lifetime_coupling.residual_blocker
        )
    if (
        ledger.cache_pre_claim_admission_carrier_reclaim_reset_exactness.exactness_rung
        == "admission_carrier_reclaim_reset_exact"
    ):
        cache_surface = _CONTRACT_SURFACES[
            "cache_scheduler_depth_pre_claim_admission_carrier_reclaim_reset_exactness"
        ]
        cache_closure_level = (
            ledger.cache_pre_claim_admission_carrier_reclaim_reset_exactness.exactness_rung
        )
        cache_blocked_reason = (
            ledger.cache_pre_claim_admission_carrier_reclaim_reset_exactness.residual_blocker
        )
    if (
        ledger.cache_pre_claim_admission_carrier_branch_reselection.reselection_rung
        == "carrier_branch_reselection_exact"
    ):
        cache_surface = _CONTRACT_SURFACES[
            "cache_scheduler_depth_pre_claim_admission_carrier_branch_reselection"
        ]
        cache_closure_level = (
            ledger.cache_pre_claim_admission_carrier_branch_reselection.reselection_rung
        )
        cache_blocked_reason = (
            ledger.cache_pre_claim_admission_carrier_branch_reselection.residual_blocker
        )
    if (
        ledger.cache_scheduler_turboquant_branch_reselection.reselection_rung
        == "scheduler_turboquant_branch_exact"
    ):
        cache_surface = _CONTRACT_SURFACES[
            "cache_scheduler_depth_scheduler_turboquant_branch_reselection"
        ]
        cache_closure_level = (
            ledger.cache_scheduler_turboquant_branch_reselection.reselection_rung
        )
        cache_blocked_reason = (
            ledger.cache_scheduler_turboquant_branch_reselection.residual_blocker
        )
    if (
        ledger.cache_continuous_batching_branch_reduction.reduction_rung
        == "continuous_batching_branch_exact"
    ):
        cache_surface = _CONTRACT_SURFACES[
            "cache_scheduler_depth_continuous_batching_branch_reduction"
        ]
        cache_closure_level = (
            ledger.cache_continuous_batching_branch_reduction.reduction_rung
        )
        cache_blocked_reason = (
            ledger.cache_continuous_batching_branch_reduction.residual_blocker
        )
    if (
        ledger.cache_request_aggregation_window_reentry.reentry_rung
        == "aggregation_reentry_exact"
    ):
        cache_surface = _CONTRACT_SURFACES[
            "cache_scheduler_depth_request_aggregation_window_reentry"
        ]
        cache_closure_level = (
            ledger.cache_request_aggregation_window_reentry.reentry_rung
        )
        cache_blocked_reason = (
            ledger.cache_request_aggregation_window_reentry.residual_blocker
        )
    if (
        ledger.cache_request_aggregation_active_seam.seam_rung
        == "aggregation_active_seam_exact"
    ):
        cache_surface = _CONTRACT_SURFACES[
            "cache_scheduler_depth_request_aggregation_active_seam"
        ]
        cache_closure_level = (
            ledger.cache_request_aggregation_active_seam.seam_rung
        )
        cache_blocked_reason = (
            ledger.cache_request_aggregation_active_seam.residual_blocker
        )
    if (
        ledger.cache_pre_gate_admission_window_seam.seam_rung
        == "pre_gate_admission_window_seam_exact"
    ):
        cache_surface = _CONTRACT_SURFACES[
            "cache_scheduler_depth_pre_gate_admission_window_seam"
        ]
        cache_closure_level = (
            ledger.cache_pre_gate_admission_window_seam.seam_rung
        )
        cache_blocked_reason = (
            ledger.cache_pre_gate_admission_window_seam.residual_blocker
        )
    if (
        ledger.cache_structural_ingress_seam.seam_rung
        == "structural_ingress_seam_introduced"
    ):
        cache_surface = _CONTRACT_SURFACES[
            "cache_scheduler_depth_structural_ingress_seam"
        ]
        cache_closure_level = ledger.cache_structural_ingress_seam.seam_rung
        cache_blocked_reason = ledger.cache_structural_ingress_seam.residual_blocker

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
