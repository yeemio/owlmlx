"""Executable runtime kernel package for owlmlx."""

from ..cache_residency_evidence import (
    CacheResidencyEvidence,
    CacheResidencyMetrics,
    build_cache_residency_evidence,
    cache_residency_evidence_to_dict,
    cache_residency_metrics_to_dict,
    normalize_cache_residency_metrics,
)
from ..cache_repeatability_evidence import (
    CacheRepeatabilityEvidence,
    build_cache_repeatability_evidence,
    cache_repeatability_evidence_to_dict,
)
from ..cache_closure_rung import (
    CacheClosureRung,
    build_cache_closure_rung,
    cache_closure_rung_to_dict,
)
from ..cache_counter_gap import (
    CacheCounterGap,
    build_cache_counter_gap,
    cache_counter_gap_to_dict,
)
from ..cache_counter_feasibility import (
    CacheCounterFeasibility,
    build_cache_counter_feasibility,
    cache_counter_feasibility_to_dict,
)
from ..cache_scheduler_turboquant_split import (
    CacheSchedulerTurboQuantSplit,
    build_cache_scheduler_turboquant_split,
    cache_scheduler_turboquant_split_to_dict,
)
from ..cache_scheduler_floor_gap import (
    CacheSchedulerFloorGap,
    build_cache_scheduler_floor_gap,
    cache_scheduler_floor_gap_to_dict,
)
from ..cache_scheduler_implementation_backlog import (
    CacheSchedulerImplementationBacklog,
    build_cache_scheduler_implementation_backlog,
    cache_scheduler_implementation_backlog_to_dict,
)
from ..cache_scheduler_branch_selection import (
    CacheSchedulerBranchSelection,
    build_cache_scheduler_branch_selection,
    cache_scheduler_branch_selection_to_dict,
)
from ..cache_scheduler_turboquant_branch_reselection import (
    CacheSchedulerTurboQuantBranchReselection,
    build_cache_scheduler_turboquant_branch_reselection,
    cache_scheduler_turboquant_branch_reselection_to_dict,
)
from ..cache_continuous_batching_branch_reduction import (
    CacheContinuousBatchingBranchReduction,
    build_cache_continuous_batching_branch_reduction,
    cache_continuous_batching_branch_reduction_to_dict,
)
from ..cache_request_aggregation_window_reentry import (
    CacheRequestAggregationWindowReentry,
    build_cache_request_aggregation_window_reentry,
    cache_request_aggregation_window_reentry_to_dict,
)
from ..cache_request_aggregation_active_seam import (
    CacheRequestAggregationActiveSeam,
    build_cache_request_aggregation_active_seam,
    cache_request_aggregation_active_seam_to_dict,
)
from ..cache_pre_gate_admission_window_seam import (
    CachePreGateAdmissionWindowSeam,
    build_cache_pre_gate_admission_window_seam,
    cache_pre_gate_admission_window_seam_to_dict,
)
from ..cache_structural_ingress_seam import (
    CacheStructuralIngressSeam,
    build_cache_structural_ingress_seam,
    cache_structural_ingress_seam_to_dict,
)
from ..cache_continuous_batching_feasibility import (
    CacheContinuousBatchingFeasibility,
    build_cache_continuous_batching_feasibility,
    cache_continuous_batching_feasibility_to_dict,
)
from ..cache_batching_mechanism_subgap import (
    CacheBatchingMechanismSubgap,
    build_cache_batching_mechanism_subgap,
    cache_batching_mechanism_subgap_to_dict,
)
from ..cache_request_aggregation_window_exactness import (
    CacheRequestAggregationWindowExactness,
    build_cache_request_aggregation_window_exactness,
    cache_request_aggregation_window_exactness_to_dict,
)
from ..cache_pre_gate_cohort_window_feasibility import (
    CachePreGateCohortWindowFeasibility,
    build_cache_pre_gate_cohort_window_feasibility,
    cache_pre_gate_cohort_window_feasibility_to_dict,
)
from ..cache_pre_gate_admission_hook_exactness import (
    CachePreGateAdmissionHookExactness,
    build_cache_pre_gate_admission_hook_exactness,
    cache_pre_gate_admission_hook_exactness_to_dict,
)
from ..cache_admission_hook_safety_contract import (
    CacheAdmissionHookSafetyContract,
    build_cache_admission_hook_safety_contract,
    cache_admission_hook_safety_contract_to_dict,
)
from ..cache_pre_claim_admission_contract import (
    CachePreClaimAdmissionContract,
    build_cache_pre_claim_admission_contract,
    cache_pre_claim_admission_contract_to_dict,
)
from ..cache_pre_claim_staging_seam_exactness import (
    CachePreClaimStagingSeamExactness,
    build_cache_pre_claim_staging_seam_exactness,
    cache_pre_claim_staging_seam_exactness_to_dict,
)
from ..cache_pre_claim_metadata_ticket_ownership import (
    CachePreClaimMetadataTicketOwnership,
    build_cache_pre_claim_metadata_ticket_ownership,
    cache_pre_claim_metadata_ticket_ownership_to_dict,
)
from ..cache_pre_claim_inert_state_semantics import (
    CachePreClaimInertStateSemantics,
    build_cache_pre_claim_inert_state_semantics,
    cache_pre_claim_inert_state_semantics_to_dict,
)
from ..cache_pre_claim_marker_lifetime import (
    CachePreClaimMarkerLifetime,
    build_cache_pre_claim_marker_lifetime,
    cache_pre_claim_marker_lifetime_to_dict,
)
from ..cache_pre_claim_marker_visibility import (
    CachePreClaimMarkerVisibility,
    build_cache_pre_claim_marker_visibility,
    cache_pre_claim_marker_visibility_to_dict,
)
from ..cache_pre_claim_marker_trigger_inputs import (
    CachePreClaimMarkerTriggerInputs,
    build_cache_pre_claim_marker_trigger_inputs,
    cache_pre_claim_marker_trigger_inputs_to_dict,
)
from ..cache_pre_claim_marker_reader_writer_ownership import (
    CachePreClaimMarkerReaderWriterOwnership,
    build_cache_pre_claim_marker_reader_writer_ownership,
    cache_pre_claim_marker_reader_writer_ownership_to_dict,
)
from ..cache_pre_claim_marker_state_carrier import (
    CachePreClaimMarkerStateCarrier,
    build_cache_pre_claim_marker_state_carrier,
    cache_pre_claim_marker_state_carrier_to_dict,
)
from ..cache_pre_claim_marker_clear_observer_boundary import (
    CachePreClaimMarkerClearObserverBoundary,
    build_cache_pre_claim_marker_clear_observer_boundary,
    cache_pre_claim_marker_clear_observer_boundary_to_dict,
)
from ..cache_pre_claim_marker_immutability_boundary import (
    CachePreClaimMarkerImmutabilityBoundary,
    build_cache_pre_claim_marker_immutability_boundary,
    cache_pre_claim_marker_immutability_boundary_to_dict,
)
from ..cache_pre_claim_marker_payload_shape_exactness import (
    CachePreClaimMarkerPayloadShapeExactness,
    build_cache_pre_claim_marker_payload_shape_exactness,
    cache_pre_claim_marker_payload_shape_exactness_to_dict,
)
from ..cache_pre_claim_marker_encoding_carrier_exactness import (
    CachePreClaimMarkerEncodingCarrierExactness,
    build_cache_pre_claim_marker_encoding_carrier_exactness,
    cache_pre_claim_marker_encoding_carrier_exactness_to_dict,
)
from ..cache_pre_claim_marker_storage_locality_exactness import (
    CachePreClaimMarkerStorageLocalityExactness,
    build_cache_pre_claim_marker_storage_locality_exactness,
    cache_pre_claim_marker_storage_locality_exactness_to_dict,
)
from ..cache_pre_claim_marker_locality_access_exactness import (
    CachePreClaimMarkerLocalityAccessExactness,
    build_cache_pre_claim_marker_locality_access_exactness,
    cache_pre_claim_marker_locality_access_exactness_to_dict,
)
from ..cache_pre_claim_marker_locality_isolation_exactness import (
    CachePreClaimMarkerLocalityIsolationExactness,
    build_cache_pre_claim_marker_locality_isolation_exactness,
    cache_pre_claim_marker_locality_isolation_exactness_to_dict,
)
from ..cache_pre_claim_marker_locality_lifetime_coupling import (
    CachePreClaimMarkerLocalityLifetimeCoupling,
    build_cache_pre_claim_marker_locality_lifetime_coupling,
    cache_pre_claim_marker_locality_lifetime_coupling_to_dict,
)
from ..cache_pre_claim_marker_reclaim_reset_exactness import (
    CachePreClaimMarkerReclaimResetExactness,
    build_cache_pre_claim_marker_reclaim_reset_exactness,
    cache_pre_claim_marker_reclaim_reset_exactness_to_dict,
)
from ..cache_pre_claim_admission_carrier_construction import (
    CachePreClaimAdmissionCarrierConstruction,
    build_cache_pre_claim_admission_carrier_construction,
    cache_pre_claim_admission_carrier_construction_to_dict,
)
from ..cache_pre_claim_admission_carrier_field_exactness import (
    CachePreClaimAdmissionCarrierFieldExactness,
    build_cache_pre_claim_admission_carrier_field_exactness,
    cache_pre_claim_admission_carrier_field_exactness_to_dict,
)
from ..cache_pre_claim_admission_carrier_encoding_exactness import (
    CachePreClaimAdmissionCarrierEncodingExactness,
    build_cache_pre_claim_admission_carrier_encoding_exactness,
    cache_pre_claim_admission_carrier_encoding_exactness_to_dict,
)
from ..cache_pre_claim_admission_carrier_locality_exactness import (
    CachePreClaimAdmissionCarrierLocalityExactness,
    build_cache_pre_claim_admission_carrier_locality_exactness,
    cache_pre_claim_admission_carrier_locality_exactness_to_dict,
)
from ..cache_pre_claim_admission_carrier_locality_access_exactness import (
    CachePreClaimAdmissionCarrierLocalityAccessExactness,
    build_cache_pre_claim_admission_carrier_locality_access_exactness,
    cache_pre_claim_admission_carrier_locality_access_exactness_to_dict,
)
from ..cache_pre_claim_admission_carrier_locality_isolation_exactness import (
    CachePreClaimAdmissionCarrierLocalityIsolationExactness,
    build_cache_pre_claim_admission_carrier_locality_isolation_exactness,
    cache_pre_claim_admission_carrier_locality_isolation_exactness_to_dict,
)
from ..cache_pre_claim_admission_carrier_locality_lifetime_coupling import (
    CachePreClaimAdmissionCarrierLocalityLifetimeCoupling,
    build_cache_pre_claim_admission_carrier_locality_lifetime_coupling,
    cache_pre_claim_admission_carrier_locality_lifetime_coupling_to_dict,
)
from ..cache_pre_claim_admission_carrier_reclaim_reset_exactness import (
    CachePreClaimAdmissionCarrierReclaimResetExactness,
    build_cache_pre_claim_admission_carrier_reclaim_reset_exactness,
    cache_pre_claim_admission_carrier_reclaim_reset_exactness_to_dict,
)
from ..cache_pre_claim_admission_carrier_branch_reselection import (
    CachePreClaimAdmissionCarrierBranchReselection,
    build_cache_pre_claim_admission_carrier_branch_reselection,
    cache_pre_claim_admission_carrier_branch_reselection_to_dict,
)
from ..cache_turboquant_preconditions_gap import (
    CacheTurboQuantPreconditionsGap,
    build_cache_turboquant_preconditions_gap,
    cache_turboquant_preconditions_gap_to_dict,
)
from ..dominant_gap_reselection import (
    DominantGapReselection,
    build_dominant_gap_reselection,
    dominant_gap_reselection_to_dict,
)
from ..multi_model_governance_status import (
    MultiModelGovernanceStatus,
    build_multi_model_governance_status,
    multi_model_governance_status_to_dict,
)
from ..multi_model_governance_controls import (
    MultiModelGovernanceControls,
    build_multi_model_governance_controls,
    multi_model_governance_controls_to_dict,
)
from ..multi_model_governance_transition_ledger import (
    MultiModelGovernanceTransitionLedger,
    build_multi_model_governance_transition_ledger,
    multi_model_governance_transition_ledger_to_dict,
)
from ..multi_model_governance_policy_gap import (
    MultiModelGovernancePolicyGap,
    build_multi_model_governance_policy_gap,
    multi_model_governance_policy_gap_to_dict,
)
from ..multi_model_pinning_control import (
    MultiModelPinningControl,
    build_multi_model_pinning_control,
    multi_model_pinning_control_to_dict,
)
from ..multi_model_ttl_policy_control import (
    MultiModelTTLPolicyControl,
    build_multi_model_ttl_policy_control,
    multi_model_ttl_policy_control_to_dict,
)
from ..multi_model_eviction_history_governance import (
    MultiModelEvictionHistoryGovernance,
    build_multi_model_eviction_history_governance,
    multi_model_eviction_history_governance_to_dict,
)
from ..heavy_weight_repeatability_status import (
    HeavyWeightRuntimeRepeatabilityStatus,
    build_heavy_weight_runtime_repeatability_status,
    heavy_weight_repeatability_status_to_dict,
)
from ..customer_runtime_evidence import (
    CustomerRuntimeEvidenceLedger,
    build_customer_runtime_evidence,
    customer_runtime_evidence_to_dict,
)
from ..cache_scheduler_status import (
    CacheSchedulerStatus,
    build_cache_scheduler_status,
    cache_scheduler_status_to_dict,
)
from ..turboquant_readiness import (
    TurboQuantReadiness,
    build_turboquant_readiness,
    turboquant_readiness_to_dict,
)
from .backends import FakeBackend, RuntimeBackend
from .first_smoke_decision import (
    LargeWeightFirstSmokeDecision,
    build_large_weight_first_smoke_decision,
    first_smoke_decision_to_dict,
)
from .host_stability import (
    HostStableExecutionStatus,
    build_host_stable_execution_status,
    host_stability_to_dict,
)
from .kernel import RuntimeKernel
from .mlx_environment import (
    MlxEnvironmentCandidate,
    MlxCrashReportSummary,
    MlxImportBlockerReport,
    MlxEnvironmentProbe,
    MlxEnvironmentReadiness,
    MlxEnvironmentSelection,
    MlxHostForensicsReport,
    blocker_report_to_dict,
    build_mlx_host_forensics_report,
    build_mlx_environment_readiness,
    build_mlx_import_blocker_report,
    crash_report_to_dict,
    default_environment_candidates,
    find_recent_mlx_crash_reports,
    host_forensics_to_dict,
    load_verified_baselines,
    known_environment_candidates,
    parse_mlx_crash_report,
    probe_mlx_environments,
    probe_to_dict,
    remember_verified_baseline,
    readiness_to_dict,
    select_mlx_environment,
    selection_to_dict,
    verified_baseline_file_path,
)
from .mlx_lm_backend import MlxLmBackend
from .mlx_lm_subprocess_backend import MlxLmSubprocessBackend
from .specimen_gate import (
    LargeWeightSpecimenGate,
    SpecimenPathAssessment,
    assess_specimen_path,
    build_large_weight_specimen_gate,
    specimen_gate_to_dict,
)
from .types import (
    BackendStatus,
    ChatTurn,
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
    "CacheResidencyEvidence",
    "CacheResidencyMetrics",
    "CacheRepeatabilityEvidence",
    "CacheCounterGap",
    "CacheCounterFeasibility",
    "CacheSchedulerTurboQuantSplit",
    "CacheSchedulerFloorGap",
    "CacheSchedulerImplementationBacklog",
    "CacheSchedulerBranchSelection",
    "CacheSchedulerTurboQuantBranchReselection",
    "CacheContinuousBatchingBranchReduction",
    "CacheRequestAggregationWindowReentry",
    "CacheRequestAggregationActiveSeam",
    "CachePreGateAdmissionWindowSeam",
    "CacheContinuousBatchingFeasibility",
    "CacheBatchingMechanismSubgap",
    "CacheRequestAggregationWindowExactness",
    "CachePreGateCohortWindowFeasibility",
    "CachePreGateAdmissionHookExactness",
    "CacheAdmissionHookSafetyContract",
    "CachePreClaimAdmissionContract",
    "CachePreClaimStagingSeamExactness",
    "CachePreClaimMetadataTicketOwnership",
    "CachePreClaimInertStateSemantics",
    "CachePreClaimMarkerLifetime",
    "CachePreClaimMarkerVisibility",
    "CachePreClaimMarkerTriggerInputs",
    "CachePreClaimMarkerReaderWriterOwnership",
    "CachePreClaimMarkerStateCarrier",
    "CachePreClaimMarkerClearObserverBoundary",
    "CachePreClaimMarkerImmutabilityBoundary",
    "CachePreClaimMarkerPayloadShapeExactness",
    "CachePreClaimMarkerEncodingCarrierExactness",
    "CachePreClaimMarkerStorageLocalityExactness",
    "CachePreClaimMarkerLocalityAccessExactness",
    "CachePreClaimMarkerLocalityIsolationExactness",
    "CachePreClaimMarkerLocalityLifetimeCoupling",
    "CachePreClaimMarkerReclaimResetExactness",
    "CachePreClaimAdmissionCarrierConstruction",
    "CachePreClaimAdmissionCarrierFieldExactness",
    "CachePreClaimAdmissionCarrierEncodingExactness",
    "CachePreClaimAdmissionCarrierLocalityExactness",
    "CachePreClaimAdmissionCarrierLocalityAccessExactness",
    "CachePreClaimAdmissionCarrierLocalityIsolationExactness",
    "CachePreClaimAdmissionCarrierLocalityLifetimeCoupling",
    "CachePreClaimAdmissionCarrierReclaimResetExactness",
    "CachePreClaimAdmissionCarrierBranchReselection",
    "CacheTurboQuantPreconditionsGap",
    "DominantGapReselection",
    "CacheClosureRung",
    "CacheSchedulerStatus",
    "HeavyWeightRuntimeRepeatabilityStatus",
    "CustomerRuntimeEvidenceLedger",
    "MultiModelGovernanceStatus",
    "MultiModelGovernanceControls",
    "MultiModelGovernanceTransitionLedger",
    "MultiModelGovernancePolicyGap",
    "ChatTurn",
    "FakeBackend",
    "GenerateResult",
    "LoadResult",
    "HostStableExecutionStatus",
    "LargeWeightFirstSmokeDecision",
    "LoadedModelInfo",
    "LargeWeightSpecimenGate",
    "MlxCrashReportSummary",
    "RestartResult",
    "MlxEnvironmentCandidate",
    "MlxImportBlockerReport",
    "MlxEnvironmentProbe",
    "MlxEnvironmentReadiness",
    "MlxEnvironmentSelection",
    "MlxHostForensicsReport",
    "MlxLmBackend",
    "MlxLmSubprocessBackend",
    "RuntimeBackend",
    "RuntimeErrorCode",
    "RuntimeKernel",
    "RuntimeOperationResult",
    "RuntimeStatus",
    "SpecimenPathAssessment",
    "StreamEvent",
    "TurboQuantReadiness",
    "UnloadResult",
    "assess_specimen_path",
    "blocker_report_to_dict",
    "build_cache_residency_evidence",
    "build_cache_repeatability_evidence",
    "build_cache_counter_gap",
    "build_cache_counter_feasibility",
    "build_cache_scheduler_turboquant_split",
    "build_cache_scheduler_floor_gap",
    "build_cache_scheduler_implementation_backlog",
    "build_cache_scheduler_branch_selection",
    "build_cache_scheduler_turboquant_branch_reselection",
    "build_cache_continuous_batching_branch_reduction",
    "build_cache_request_aggregation_window_reentry",
    "build_cache_request_aggregation_active_seam",
    "build_cache_pre_gate_admission_window_seam",
    "build_cache_structural_ingress_seam",
    "build_cache_continuous_batching_feasibility",
    "build_cache_batching_mechanism_subgap",
    "build_cache_request_aggregation_window_exactness",
    "build_cache_pre_gate_cohort_window_feasibility",
    "build_cache_pre_gate_admission_hook_exactness",
    "build_cache_admission_hook_safety_contract",
    "build_cache_pre_claim_admission_contract",
    "build_cache_pre_claim_staging_seam_exactness",
    "build_cache_pre_claim_metadata_ticket_ownership",
    "build_cache_pre_claim_inert_state_semantics",
    "build_cache_pre_claim_marker_lifetime",
    "build_cache_pre_claim_marker_visibility",
    "build_cache_pre_claim_marker_trigger_inputs",
    "build_cache_pre_claim_marker_reader_writer_ownership",
    "build_cache_pre_claim_marker_state_carrier",
    "build_cache_pre_claim_marker_clear_observer_boundary",
    "build_cache_pre_claim_marker_immutability_boundary",
    "build_cache_pre_claim_marker_payload_shape_exactness",
    "build_cache_pre_claim_marker_encoding_carrier_exactness",
    "build_cache_pre_claim_marker_storage_locality_exactness",
    "build_cache_pre_claim_marker_locality_access_exactness",
    "build_cache_pre_claim_marker_locality_isolation_exactness",
    "build_cache_pre_claim_marker_locality_lifetime_coupling",
    "build_cache_pre_claim_marker_reclaim_reset_exactness",
    "build_cache_pre_claim_admission_carrier_construction",
    "build_cache_pre_claim_admission_carrier_field_exactness",
    "build_cache_pre_claim_admission_carrier_encoding_exactness",
    "build_cache_pre_claim_admission_carrier_locality_exactness",
    "build_cache_pre_claim_admission_carrier_reclaim_reset_exactness",
    "build_cache_pre_claim_admission_carrier_branch_reselection",
    "build_cache_turboquant_preconditions_gap",
    "build_dominant_gap_reselection",
    "build_cache_closure_rung",
    "build_cache_scheduler_status",
    "build_heavy_weight_runtime_repeatability_status",
    "build_customer_runtime_evidence",
    "build_multi_model_governance_status",
    "build_multi_model_governance_controls",
    "build_multi_model_governance_transition_ledger",
    "build_multi_model_governance_policy_gap",
    "build_multi_model_pinning_control",
    "build_multi_model_ttl_policy_control",
    "build_multi_model_eviction_history_governance",
    "build_mlx_host_forensics_report",
    "build_large_weight_specimen_gate",
    "build_large_weight_first_smoke_decision",
    "build_host_stable_execution_status",
    "build_mlx_environment_readiness",
    "build_mlx_import_blocker_report",
    "build_turboquant_readiness",
    "crash_report_to_dict",
    "default_environment_candidates",
    "first_smoke_decision_to_dict",
    "host_stability_to_dict",
    "find_recent_mlx_crash_reports",
    "host_forensics_to_dict",
    "load_verified_baselines",
    "known_environment_candidates",
    "normalize_cache_residency_metrics",
    "parse_mlx_crash_report",
    "probe_mlx_environments",
    "probe_to_dict",
    "remember_verified_baseline",
    "readiness_to_dict",
    "cache_residency_evidence_to_dict",
    "cache_residency_metrics_to_dict",
    "cache_repeatability_evidence_to_dict",
    "cache_counter_gap_to_dict",
    "cache_counter_feasibility_to_dict",
    "cache_scheduler_turboquant_split_to_dict",
    "cache_scheduler_floor_gap_to_dict",
    "cache_scheduler_implementation_backlog_to_dict",
    "cache_scheduler_branch_selection_to_dict",
    "cache_scheduler_turboquant_branch_reselection_to_dict",
    "cache_continuous_batching_branch_reduction_to_dict",
    "cache_request_aggregation_window_reentry_to_dict",
    "cache_request_aggregation_active_seam_to_dict",
    "cache_pre_gate_admission_window_seam_to_dict",
    "cache_structural_ingress_seam_to_dict",
    "cache_continuous_batching_feasibility_to_dict",
    "cache_batching_mechanism_subgap_to_dict",
    "cache_request_aggregation_window_exactness_to_dict",
    "cache_pre_gate_cohort_window_feasibility_to_dict",
    "cache_pre_gate_admission_hook_exactness_to_dict",
    "cache_admission_hook_safety_contract_to_dict",
    "cache_pre_claim_admission_contract_to_dict",
    "cache_pre_claim_staging_seam_exactness_to_dict",
    "cache_pre_claim_metadata_ticket_ownership_to_dict",
    "cache_pre_claim_inert_state_semantics_to_dict",
    "cache_pre_claim_marker_lifetime_to_dict",
    "cache_pre_claim_marker_visibility_to_dict",
    "cache_pre_claim_marker_trigger_inputs_to_dict",
    "cache_pre_claim_marker_reader_writer_ownership_to_dict",
    "cache_pre_claim_marker_state_carrier_to_dict",
    "cache_pre_claim_marker_clear_observer_boundary_to_dict",
    "cache_pre_claim_marker_immutability_boundary_to_dict",
    "cache_pre_claim_marker_payload_shape_exactness_to_dict",
    "cache_pre_claim_marker_encoding_carrier_exactness_to_dict",
    "cache_pre_claim_marker_storage_locality_exactness_to_dict",
    "cache_pre_claim_marker_locality_access_exactness_to_dict",
    "cache_pre_claim_marker_locality_isolation_exactness_to_dict",
    "cache_pre_claim_marker_locality_lifetime_coupling_to_dict",
    "cache_pre_claim_marker_reclaim_reset_exactness_to_dict",
    "cache_pre_claim_admission_carrier_construction_to_dict",
    "cache_pre_claim_admission_carrier_field_exactness_to_dict",
    "cache_pre_claim_admission_carrier_encoding_exactness_to_dict",
    "cache_pre_claim_admission_carrier_locality_exactness_to_dict",
    "cache_pre_claim_admission_carrier_reclaim_reset_exactness_to_dict",
    "cache_pre_claim_admission_carrier_branch_reselection_to_dict",
    "cache_turboquant_preconditions_gap_to_dict",
    "dominant_gap_reselection_to_dict",
    "cache_closure_rung_to_dict",
    "cache_scheduler_status_to_dict",
    "heavy_weight_repeatability_status_to_dict",
    "customer_runtime_evidence_to_dict",
    "multi_model_governance_status_to_dict",
    "multi_model_governance_controls_to_dict",
    "multi_model_governance_transition_ledger_to_dict",
    "multi_model_governance_policy_gap_to_dict",
    "multi_model_pinning_control_to_dict",
    "multi_model_ttl_policy_control_to_dict",
    "multi_model_eviction_history_governance_to_dict",
    "select_mlx_environment",
    "selection_to_dict",
    "specimen_gate_to_dict",
    "turboquant_readiness_to_dict",
    "verified_baseline_file_path",
]
