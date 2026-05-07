"""Runtime-owned active seam selection inside the request-aggregation chain."""

from __future__ import annotations

from dataclasses import dataclass

from .cache_child_exchange_aggregated_dispatch_exactness import (
    CacheChildExchangeAggregatedDispatchExactness,
    build_cache_child_exchange_aggregated_dispatch_exactness,
)
from .cache_cohort_to_child_exchange_handoff_exactness import (
    CacheCohortToChildExchangeHandoffExactness,
    build_cache_cohort_to_child_exchange_handoff_exactness,
)
from .cache_stream_hold_dependency_exactness import (
    CacheStreamHoldDependencyExactness,
    build_cache_stream_hold_dependency_exactness,
)
from .cache_stream_backend_terminal_event_exactness import (
    CacheStreamBackendTerminalEventExactness,
    build_cache_stream_backend_terminal_event_exactness,
)
from .cache_stream_backend_terminal_payload_commit_exactness import (
    CacheStreamBackendTerminalPayloadCommitExactness,
    build_cache_stream_backend_terminal_payload_commit_exactness,
)
from .cache_stream_backend_terminal_payload_capture_exactness import (
    CacheStreamBackendTerminalPayloadCaptureExactness,
    build_cache_stream_backend_terminal_payload_capture_exactness,
)
from .cache_stream_backend_terminal_record_capture_exactness import (
    CacheStreamBackendTerminalRecordCaptureExactness,
    build_cache_stream_backend_terminal_record_capture_exactness,
)
from .cache_stream_backend_terminal_record_prefix_exactness import (
    CacheStreamBackendTerminalRecordPrefixExactness,
    build_cache_stream_backend_terminal_record_prefix_exactness,
)
from .cache_stream_backend_terminal_action_discriminant_exactness import (
    CacheStreamBackendTerminalActionDiscriminantExactness,
    build_cache_stream_backend_terminal_action_discriminant_exactness,
)
from .cache_stream_backend_terminal_notice_capture_exactness import (
    CacheStreamBackendTerminalNoticeCaptureExactness,
    build_cache_stream_backend_terminal_notice_capture_exactness,
)
from .cache_stream_backend_terminal_notice_prefix_exactness import (
    CacheStreamBackendTerminalNoticePrefixExactness,
    build_cache_stream_backend_terminal_notice_prefix_exactness,
)
from .cache_stream_backend_terminal_notice_action_discriminant_exactness import (
    CacheStreamBackendTerminalNoticeActionDiscriminantExactness,
    build_cache_stream_backend_terminal_notice_action_discriminant_exactness,
)
from .cache_stream_backend_terminal_notice_action_stem_exactness import (
    CacheStreamBackendTerminalNoticeActionStemExactness,
    build_cache_stream_backend_terminal_notice_action_stem_exactness,
)
from .cache_stream_backend_terminal_notice_marker_exactness import (
    CacheStreamBackendTerminalNoticeMarkerExactness,
    build_cache_stream_backend_terminal_notice_marker_exactness,
)
from .cache_stream_backend_terminal_notice_marker_prefix_exactness import (
    CacheStreamBackendTerminalNoticeMarkerPrefixExactness,
    build_cache_stream_backend_terminal_notice_marker_prefix_exactness,
)
from .cache_stream_backend_terminal_notice_marker_stem_exactness import (
    CacheStreamBackendTerminalNoticeMarkerStemExactness,
    build_cache_stream_backend_terminal_notice_marker_stem_exactness,
)
from .cache_stream_backend_terminal_notice_marker_discriminant_exactness import (
    CacheStreamBackendTerminalNoticeMarkerDiscriminantExactness,
    build_cache_stream_backend_terminal_notice_marker_discriminant_exactness,
)
from .cache_stream_backend_terminal_notice_marker_key_lead_exactness import (
    CacheStreamBackendTerminalNoticeMarkerKeyLeadExactness,
    build_cache_stream_backend_terminal_notice_marker_key_lead_exactness,
)
from .cache_stream_backend_terminal_notice_leading_discriminator_exactness import (
    CacheStreamBackendTerminalNoticeLeadingDiscriminatorExactness,
    build_cache_stream_backend_terminal_notice_leading_discriminator_exactness,
)
from .cache_stream_backend_terminal_notice_leading_discriminator_prefix_exactness import (
    CacheStreamBackendTerminalNoticeLeadingDiscriminatorPrefixExactness,
    build_cache_stream_backend_terminal_notice_leading_discriminator_prefix_exactness,
)
from .cache_stream_backend_terminal_notice_leading_discriminator_stem_exactness import (
    CacheStreamBackendTerminalNoticeLeadingDiscriminatorStemExactness,
    build_cache_stream_backend_terminal_notice_leading_discriminator_stem_exactness,
)
from .cache_stream_backend_terminal_notice_leading_discriminator_discriminant_exactness import (
    CacheStreamBackendTerminalNoticeLeadingDiscriminatorDiscriminantExactness,
    build_cache_stream_backend_terminal_notice_leading_discriminator_discriminant_exactness,
)
from .cache_stream_backend_terminal_notice_leading_discriminator_marker_exactness import (
    CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerExactness,
    build_cache_stream_backend_terminal_notice_leading_discriminator_marker_exactness,
)
from .cache_stream_backend_terminal_notice_leading_discriminator_marker_prefix_exactness import (
    CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerPrefixExactness,
    build_cache_stream_backend_terminal_notice_leading_discriminator_marker_prefix_exactness,
)
from .cache_stream_backend_terminal_notice_leading_discriminator_marker_discriminant_exactness import (
    CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerDiscriminantExactness,
    build_cache_stream_backend_terminal_notice_leading_discriminator_marker_discriminant_exactness,
)
from .cache_stream_backend_terminal_notice_leading_discriminator_marker_first_unique_boundary_exactness import (
    CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerFirstUniqueBoundaryExactness,
    build_cache_stream_backend_terminal_notice_leading_discriminator_marker_first_unique_boundary_exactness,
)
from .cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_exactness import (
    CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedDiscriminatorExactness,
    build_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_exactness,
)
from .cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_prefix_exactness import (
    CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedDiscriminatorPrefixExactness,
    build_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_prefix_exactness,
)
from .cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_stem_exactness import (
    CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedDiscriminatorStemExactness,
    build_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_stem_exactness,
)
from .cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_discriminant_exactness import (
    CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedDiscriminatorDiscriminantExactness,
    build_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_discriminant_exactness,
)
from .cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_first_unique_boundary_exactness import (
    CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedDiscriminatorFirstUniqueBoundaryExactness,
    build_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_first_unique_boundary_exactness,
)
from .cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_exactness import (
    CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedLeadingDiscriminatorExactness,
    build_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_exactness,
)
from .cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_prefix_exactness import (
    CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedLeadingDiscriminatorPrefixExactness,
    build_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_prefix_exactness,
)
from .cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_stem_exactness import (
    CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedLeadingDiscriminatorStemExactness,
    build_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_stem_exactness,
)
from .cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_discriminant_exactness import (
    CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedLeadingDiscriminatorDiscriminantExactness,
    build_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_discriminant_exactness,
)
from .cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_first_unique_boundary_exactness import (
    CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedLeadingDiscriminatorFirstUniqueBoundaryExactness,
    build_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_first_unique_boundary_exactness,
)
from .cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_exactness import (
    CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedBoundaryExactness,
    build_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_exactness,
)
from .cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_prefix_exactness import (
    CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedBoundaryPrefixExactness,
    build_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_prefix_exactness,
)
from .cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_stem_exactness import (
    CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedBoundaryStemExactness,
    build_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_stem_exactness,
)
from .cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_first_unique_boundary_exactness import (
    CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedBoundaryFirstUniqueBoundaryExactness,
    build_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_first_unique_boundary_exactness,
)
from .cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_exactness import (
    CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedBoundaryEarlierBoundaryExactness,
    build_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_exactness,
)
from .cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_first_unique_boundary_exactness import (
    CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedBoundaryEarlierBoundaryFirstUniqueBoundaryExactness,
    build_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_first_unique_boundary_exactness,
)
from .cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_earlier_boundary_exactness import (
    CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedBoundaryEarlierEarlierBoundaryExactness,
    build_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_earlier_boundary_exactness,
)
from .cache_stream_backend_terminal_notice_leading_discriminator_marker_stem_exactness import (
    CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerStemExactness,
    build_cache_stream_backend_terminal_notice_leading_discriminator_marker_stem_exactness,
)
from .cache_request_aggregation_window_exactness import (
    CacheRequestAggregationWindowExactness,
    build_cache_request_aggregation_window_exactness,
)
from .cache_request_aggregation_window_reentry import (
    CacheRequestAggregationWindowReentry,
    build_cache_request_aggregation_window_reentry,
)


@dataclass(frozen=True, slots=True)
class CacheRequestAggregationActiveSeam:
    """Exact active seam selection after request aggregation has re-entered."""

    request_aggregation_window_reentry: CacheRequestAggregationWindowReentry
    request_aggregation_window_exactness: CacheRequestAggregationWindowExactness
    child_exchange_exactness: CacheChildExchangeAggregatedDispatchExactness
    cohort_handoff_exactness: CacheCohortToChildExchangeHandoffExactness
    stream_hold_exactness: CacheStreamHoldDependencyExactness
    stream_backend_terminal_event_exactness: CacheStreamBackendTerminalEventExactness
    stream_backend_terminal_payload_commit_exactness: (
        CacheStreamBackendTerminalPayloadCommitExactness
    )
    stream_backend_terminal_payload_capture_exactness: (
        CacheStreamBackendTerminalPayloadCaptureExactness
    )
    stream_backend_terminal_record_capture_exactness: (
        CacheStreamBackendTerminalRecordCaptureExactness
    )
    stream_backend_terminal_record_prefix_exactness: (
        CacheStreamBackendTerminalRecordPrefixExactness
    )
    stream_backend_terminal_action_discriminant_exactness: (
        CacheStreamBackendTerminalActionDiscriminantExactness
    )
    stream_backend_terminal_notice_capture_exactness: (
        CacheStreamBackendTerminalNoticeCaptureExactness
    )
    stream_backend_terminal_notice_prefix_exactness: (
        CacheStreamBackendTerminalNoticePrefixExactness
    )
    stream_backend_terminal_notice_action_discriminant_exactness: (
        CacheStreamBackendTerminalNoticeActionDiscriminantExactness
    )
    stream_backend_terminal_notice_action_stem_exactness: (
        CacheStreamBackendTerminalNoticeActionStemExactness
    )
    stream_backend_terminal_notice_marker_exactness: (
        CacheStreamBackendTerminalNoticeMarkerExactness
    )
    stream_backend_terminal_notice_marker_prefix_exactness: (
        CacheStreamBackendTerminalNoticeMarkerPrefixExactness
    )
    stream_backend_terminal_notice_marker_stem_exactness: (
        CacheStreamBackendTerminalNoticeMarkerStemExactness
    )
    stream_backend_terminal_notice_marker_discriminant_exactness: (
        CacheStreamBackendTerminalNoticeMarkerDiscriminantExactness
    )
    stream_backend_terminal_notice_marker_key_lead_exactness: (
        CacheStreamBackendTerminalNoticeMarkerKeyLeadExactness
    )
    stream_backend_terminal_notice_leading_discriminator_exactness: (
        CacheStreamBackendTerminalNoticeLeadingDiscriminatorExactness
    )
    stream_backend_terminal_notice_leading_discriminator_prefix_exactness: (
        CacheStreamBackendTerminalNoticeLeadingDiscriminatorPrefixExactness
    )
    stream_backend_terminal_notice_leading_discriminator_stem_exactness: (
        CacheStreamBackendTerminalNoticeLeadingDiscriminatorStemExactness
    )
    stream_backend_terminal_notice_leading_discriminator_discriminant_exactness: (
        CacheStreamBackendTerminalNoticeLeadingDiscriminatorDiscriminantExactness
    )
    stream_backend_terminal_notice_leading_discriminator_marker_exactness: (
        CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerExactness
    )
    stream_backend_terminal_notice_leading_discriminator_marker_prefix_exactness: (
        CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerPrefixExactness
    )
    stream_backend_terminal_notice_leading_discriminator_marker_discriminant_exactness: (
        CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerDiscriminantExactness
    )
    stream_backend_terminal_notice_leading_discriminator_marker_first_unique_boundary_exactness: (
        CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerFirstUniqueBoundaryExactness
    )
    stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_exactness: (
        CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedDiscriminatorExactness
    )
    stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_prefix_exactness: (
        CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedDiscriminatorPrefixExactness
    )
    stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_stem_exactness: (
        CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedDiscriminatorStemExactness
    )
    stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_discriminant_exactness: (
        CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedDiscriminatorDiscriminantExactness
    )
    stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_first_unique_boundary_exactness: (
        CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedDiscriminatorFirstUniqueBoundaryExactness
    )
    stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_exactness: (
        CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedLeadingDiscriminatorExactness
    )
    stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_prefix_exactness: (
        CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedLeadingDiscriminatorPrefixExactness
    )
    stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_stem_exactness: (
        CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedLeadingDiscriminatorStemExactness
    )
    stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_discriminant_exactness: (
        CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedLeadingDiscriminatorDiscriminantExactness
    )
    stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_first_unique_boundary_exactness: (
        CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedLeadingDiscriminatorFirstUniqueBoundaryExactness
    )
    stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_exactness: (
        CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedBoundaryExactness
    )
    stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_prefix_exactness: (
        CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedBoundaryPrefixExactness
    )
    stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_stem_exactness: (
        CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedBoundaryStemExactness
    )
    stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_first_unique_boundary_exactness: (
        CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedBoundaryFirstUniqueBoundaryExactness
    )
    stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_exactness: (
        CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedBoundaryEarlierBoundaryExactness
    )
    stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_first_unique_boundary_exactness: (
        CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedBoundaryEarlierBoundaryFirstUniqueBoundaryExactness
    )
    stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_earlier_boundary_exactness: (
        CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedBoundaryEarlierEarlierBoundaryExactness
    )
    stream_backend_terminal_notice_leading_discriminator_marker_stem_exactness: (
        CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerStemExactness
    )
    status: str
    seam_rung: str
    selected_seam: str
    selected_seam_status: str
    preserved_secondary_dependencies: tuple[str, ...]
    preserved_secondary_runtime_branch: str
    preserved_secondary_runtime_branch_status: str
    residual_blocker: str | None
    recommended_next_step: str


def build_cache_request_aggregation_active_seam(
    *,
    request_aggregation_window_reentry: CacheRequestAggregationWindowReentry | None = None,
    request_aggregation_window_exactness: CacheRequestAggregationWindowExactness | None = None,
    child_exchange_exactness: CacheChildExchangeAggregatedDispatchExactness | None = None,
    cohort_handoff_exactness: CacheCohortToChildExchangeHandoffExactness | None = None,
    stream_hold_exactness: CacheStreamHoldDependencyExactness | None = None,
    stream_backend_terminal_event_exactness: CacheStreamBackendTerminalEventExactness | None = None,
    stream_backend_terminal_payload_commit_exactness: CacheStreamBackendTerminalPayloadCommitExactness | None = None,
    stream_backend_terminal_payload_capture_exactness: CacheStreamBackendTerminalPayloadCaptureExactness | None = None,
    stream_backend_terminal_record_capture_exactness: CacheStreamBackendTerminalRecordCaptureExactness | None = None,
    stream_backend_terminal_record_prefix_exactness: CacheStreamBackendTerminalRecordPrefixExactness | None = None,
    stream_backend_terminal_action_discriminant_exactness: CacheStreamBackendTerminalActionDiscriminantExactness | None = None,
    stream_backend_terminal_notice_capture_exactness: CacheStreamBackendTerminalNoticeCaptureExactness | None = None,
    stream_backend_terminal_notice_prefix_exactness: CacheStreamBackendTerminalNoticePrefixExactness | None = None,
    stream_backend_terminal_notice_action_discriminant_exactness: CacheStreamBackendTerminalNoticeActionDiscriminantExactness | None = None,
    stream_backend_terminal_notice_action_stem_exactness: CacheStreamBackendTerminalNoticeActionStemExactness | None = None,
    stream_backend_terminal_notice_marker_exactness: CacheStreamBackendTerminalNoticeMarkerExactness | None = None,
    stream_backend_terminal_notice_marker_prefix_exactness: CacheStreamBackendTerminalNoticeMarkerPrefixExactness | None = None,
    stream_backend_terminal_notice_marker_stem_exactness: CacheStreamBackendTerminalNoticeMarkerStemExactness | None = None,
    stream_backend_terminal_notice_marker_discriminant_exactness: CacheStreamBackendTerminalNoticeMarkerDiscriminantExactness | None = None,
    stream_backend_terminal_notice_marker_key_lead_exactness: CacheStreamBackendTerminalNoticeMarkerKeyLeadExactness | None = None,
    stream_backend_terminal_notice_leading_discriminator_exactness: CacheStreamBackendTerminalNoticeLeadingDiscriminatorExactness | None = None,
    stream_backend_terminal_notice_leading_discriminator_prefix_exactness: CacheStreamBackendTerminalNoticeLeadingDiscriminatorPrefixExactness | None = None,
    stream_backend_terminal_notice_leading_discriminator_stem_exactness: CacheStreamBackendTerminalNoticeLeadingDiscriminatorStemExactness | None = None,
    stream_backend_terminal_notice_leading_discriminator_discriminant_exactness: CacheStreamBackendTerminalNoticeLeadingDiscriminatorDiscriminantExactness | None = None,
    stream_backend_terminal_notice_leading_discriminator_marker_exactness: CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerExactness | None = None,
    stream_backend_terminal_notice_leading_discriminator_marker_prefix_exactness: CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerPrefixExactness | None = None,
    stream_backend_terminal_notice_leading_discriminator_marker_discriminant_exactness: CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerDiscriminantExactness | None = None,
    stream_backend_terminal_notice_leading_discriminator_marker_first_unique_boundary_exactness: CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerFirstUniqueBoundaryExactness | None = None,
    stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_exactness: CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedDiscriminatorExactness | None = None,
    stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_prefix_exactness: CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedDiscriminatorPrefixExactness | None = None,
    stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_stem_exactness: CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedDiscriminatorStemExactness | None = None,
    stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_discriminant_exactness: CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedDiscriminatorDiscriminantExactness | None = None,
    stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_first_unique_boundary_exactness: CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedDiscriminatorFirstUniqueBoundaryExactness | None = None,
    stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_exactness: CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedLeadingDiscriminatorExactness | None = None,
    stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_prefix_exactness: CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedLeadingDiscriminatorPrefixExactness | None = None,
    stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_stem_exactness: CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedLeadingDiscriminatorStemExactness | None = None,
    stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_discriminant_exactness: CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedLeadingDiscriminatorDiscriminantExactness | None = None,
    stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_first_unique_boundary_exactness: CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedLeadingDiscriminatorFirstUniqueBoundaryExactness | None = None,
    stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_exactness: CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedBoundaryExactness | None = None,
    stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_prefix_exactness: CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedBoundaryPrefixExactness | None = None,
    stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_stem_exactness: CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedBoundaryStemExactness | None = None,
    stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_first_unique_boundary_exactness: CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedBoundaryFirstUniqueBoundaryExactness | None = None,
    stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_exactness: CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedBoundaryEarlierBoundaryExactness | None = None,
    stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_first_unique_boundary_exactness: CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedBoundaryEarlierBoundaryFirstUniqueBoundaryExactness | None = None,
    stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_earlier_boundary_exactness: CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedBoundaryEarlierEarlierBoundaryExactness | None = None,
    stream_backend_terminal_notice_leading_discriminator_marker_stem_exactness: CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerStemExactness | None = None,
) -> CacheRequestAggregationActiveSeam:
    """Build the exact active seam inside the request-aggregation chain."""

    reentry = (
        request_aggregation_window_reentry
        if isinstance(request_aggregation_window_reentry, CacheRequestAggregationWindowReentry)
        else build_cache_request_aggregation_window_reentry()
    )
    exactness = (
        request_aggregation_window_exactness
        if isinstance(request_aggregation_window_exactness, CacheRequestAggregationWindowExactness)
        else build_cache_request_aggregation_window_exactness()
    )
    child_exactness = (
        child_exchange_exactness
        if isinstance(
            child_exchange_exactness,
            CacheChildExchangeAggregatedDispatchExactness,
        )
        else build_cache_child_exchange_aggregated_dispatch_exactness(
            request_aggregation_window_exactness=exactness
        )
    )
    handoff_exactness = (
        cohort_handoff_exactness
        if isinstance(
            cohort_handoff_exactness,
            CacheCohortToChildExchangeHandoffExactness,
        )
        else build_cache_cohort_to_child_exchange_handoff_exactness(
            child_exchange_exactness=child_exactness
        )
    )
    has_explicit_stream_exactness = isinstance(
        stream_hold_exactness,
        CacheStreamHoldDependencyExactness,
    )
    stream_exactness = (
        stream_hold_exactness
        if has_explicit_stream_exactness
        else build_cache_stream_hold_dependency_exactness(
            cohort_handoff_exactness=handoff_exactness
        )
    )
    has_explicit_backend_terminal_event_exactness = isinstance(
        stream_backend_terminal_event_exactness,
        CacheStreamBackendTerminalEventExactness,
    )
    backend_terminal_event_exactness = (
        stream_backend_terminal_event_exactness
        if has_explicit_backend_terminal_event_exactness
        else build_cache_stream_backend_terminal_event_exactness(
            stream_hold_exactness=stream_exactness
        )
    )
    has_explicit_backend_terminal_payload_commit_exactness = isinstance(
        stream_backend_terminal_payload_commit_exactness,
        CacheStreamBackendTerminalPayloadCommitExactness,
    )
    backend_terminal_payload_commit_exactness = (
        stream_backend_terminal_payload_commit_exactness
        if has_explicit_backend_terminal_payload_commit_exactness
        else build_cache_stream_backend_terminal_payload_commit_exactness(
            backend_terminal_event_exactness=backend_terminal_event_exactness
        )
    )
    has_explicit_backend_terminal_payload_capture_exactness = isinstance(
        stream_backend_terminal_payload_capture_exactness,
        CacheStreamBackendTerminalPayloadCaptureExactness,
    )
    backend_terminal_payload_capture_exactness = (
        stream_backend_terminal_payload_capture_exactness
        if has_explicit_backend_terminal_payload_capture_exactness
        else build_cache_stream_backend_terminal_payload_capture_exactness(
            backend_terminal_payload_commit_exactness=(
                backend_terminal_payload_commit_exactness
            )
        )
    )
    has_explicit_backend_terminal_record_capture_exactness = isinstance(
        stream_backend_terminal_record_capture_exactness,
        CacheStreamBackendTerminalRecordCaptureExactness,
    )
    backend_terminal_record_capture_exactness = (
        stream_backend_terminal_record_capture_exactness
        if has_explicit_backend_terminal_record_capture_exactness
        else build_cache_stream_backend_terminal_record_capture_exactness(
            backend_terminal_payload_capture_exactness=(
                backend_terminal_payload_capture_exactness
            )
        )
    )
    has_explicit_backend_terminal_record_prefix_exactness = isinstance(
        stream_backend_terminal_record_prefix_exactness,
        CacheStreamBackendTerminalRecordPrefixExactness,
    )
    backend_terminal_record_prefix_exactness = (
        stream_backend_terminal_record_prefix_exactness
        if has_explicit_backend_terminal_record_prefix_exactness
        else build_cache_stream_backend_terminal_record_prefix_exactness(
            backend_terminal_record_capture_exactness=(
                backend_terminal_record_capture_exactness
            )
        )
    )
    has_explicit_backend_terminal_action_discriminant_exactness = isinstance(
        stream_backend_terminal_action_discriminant_exactness,
        CacheStreamBackendTerminalActionDiscriminantExactness,
    )
    backend_terminal_action_discriminant_exactness = (
        stream_backend_terminal_action_discriminant_exactness
        if has_explicit_backend_terminal_action_discriminant_exactness
        else build_cache_stream_backend_terminal_action_discriminant_exactness(
            backend_terminal_record_prefix_exactness=(
                backend_terminal_record_prefix_exactness
            )
        )
    )
    has_explicit_backend_terminal_notice_capture_exactness = isinstance(
        stream_backend_terminal_notice_capture_exactness,
        CacheStreamBackendTerminalNoticeCaptureExactness,
    )
    backend_terminal_notice_capture_exactness = (
        stream_backend_terminal_notice_capture_exactness
        if has_explicit_backend_terminal_notice_capture_exactness
        else build_cache_stream_backend_terminal_notice_capture_exactness(
            backend_terminal_action_discriminant_exactness=(
                backend_terminal_action_discriminant_exactness
            )
        )
    )
    has_explicit_backend_terminal_notice_prefix_exactness = isinstance(
        stream_backend_terminal_notice_prefix_exactness,
        CacheStreamBackendTerminalNoticePrefixExactness,
    )
    has_explicit_backend_terminal_notice_action_discriminant_exactness = isinstance(
        stream_backend_terminal_notice_action_discriminant_exactness,
        CacheStreamBackendTerminalNoticeActionDiscriminantExactness,
    )
    has_explicit_backend_terminal_notice_action_stem_exactness = isinstance(
        stream_backend_terminal_notice_action_stem_exactness,
        CacheStreamBackendTerminalNoticeActionStemExactness,
    )
    has_explicit_backend_terminal_notice_marker_exactness = isinstance(
        stream_backend_terminal_notice_marker_exactness,
        CacheStreamBackendTerminalNoticeMarkerExactness,
    )
    has_explicit_backend_terminal_notice_marker_prefix_exactness = isinstance(
        stream_backend_terminal_notice_marker_prefix_exactness,
        CacheStreamBackendTerminalNoticeMarkerPrefixExactness,
    )
    has_explicit_backend_terminal_notice_marker_stem_exactness = isinstance(
        stream_backend_terminal_notice_marker_stem_exactness,
        CacheStreamBackendTerminalNoticeMarkerStemExactness,
    )
    has_explicit_backend_terminal_notice_marker_discriminant_exactness = isinstance(
        stream_backend_terminal_notice_marker_discriminant_exactness,
        CacheStreamBackendTerminalNoticeMarkerDiscriminantExactness,
    )
    has_explicit_backend_terminal_notice_marker_key_lead_exactness = isinstance(
        stream_backend_terminal_notice_marker_key_lead_exactness,
        CacheStreamBackendTerminalNoticeMarkerKeyLeadExactness,
    )
    has_explicit_backend_terminal_notice_leading_discriminator_exactness = isinstance(
        stream_backend_terminal_notice_leading_discriminator_exactness,
        CacheStreamBackendTerminalNoticeLeadingDiscriminatorExactness,
    )
    has_explicit_backend_terminal_notice_leading_discriminator_prefix_exactness = isinstance(
        stream_backend_terminal_notice_leading_discriminator_prefix_exactness,
        CacheStreamBackendTerminalNoticeLeadingDiscriminatorPrefixExactness,
    )
    has_explicit_backend_terminal_notice_leading_discriminator_stem_exactness = isinstance(
        stream_backend_terminal_notice_leading_discriminator_stem_exactness,
        CacheStreamBackendTerminalNoticeLeadingDiscriminatorStemExactness,
    )
    has_explicit_backend_terminal_notice_leading_discriminator_discriminant_exactness = isinstance(
        stream_backend_terminal_notice_leading_discriminator_discriminant_exactness,
        CacheStreamBackendTerminalNoticeLeadingDiscriminatorDiscriminantExactness,
    )
    has_explicit_backend_terminal_notice_leading_discriminator_marker_exactness = isinstance(
        stream_backend_terminal_notice_leading_discriminator_marker_exactness,
        CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerExactness,
    )
    has_explicit_backend_terminal_notice_leading_discriminator_marker_prefix_exactness = isinstance(
        stream_backend_terminal_notice_leading_discriminator_marker_prefix_exactness,
        CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerPrefixExactness,
    )
    has_explicit_backend_terminal_notice_leading_discriminator_marker_discriminant_exactness = isinstance(
        stream_backend_terminal_notice_leading_discriminator_marker_discriminant_exactness,
        CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerDiscriminantExactness,
    )
    has_explicit_backend_terminal_notice_leading_discriminator_marker_first_unique_boundary_exactness = isinstance(
        stream_backend_terminal_notice_leading_discriminator_marker_first_unique_boundary_exactness,
        CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerFirstUniqueBoundaryExactness,
    )
    has_explicit_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_exactness = isinstance(
        stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_exactness,
        CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedDiscriminatorExactness,
    )
    has_explicit_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_prefix_exactness = isinstance(
        stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_prefix_exactness,
        CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedDiscriminatorPrefixExactness,
    )
    has_explicit_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_stem_exactness = isinstance(
        stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_stem_exactness,
        CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedDiscriminatorStemExactness,
    )
    has_explicit_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_discriminant_exactness = isinstance(
        stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_discriminant_exactness,
        CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedDiscriminatorDiscriminantExactness,
    )
    has_explicit_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_first_unique_boundary_exactness = isinstance(
        stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_first_unique_boundary_exactness,
        CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedDiscriminatorFirstUniqueBoundaryExactness,
    )
    has_explicit_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_exactness = isinstance(
        stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_exactness,
        CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedLeadingDiscriminatorExactness,
    )
    has_explicit_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_prefix_exactness = isinstance(
        stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_prefix_exactness,
        CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedLeadingDiscriminatorPrefixExactness,
    )
    has_explicit_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_stem_exactness = isinstance(
        stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_stem_exactness,
        CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedLeadingDiscriminatorStemExactness,
    )
    has_explicit_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_discriminant_exactness = isinstance(
        stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_discriminant_exactness,
        CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedLeadingDiscriminatorDiscriminantExactness,
    )
    has_explicit_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_first_unique_boundary_exactness = isinstance(
        stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_first_unique_boundary_exactness,
        CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedLeadingDiscriminatorFirstUniqueBoundaryExactness,
    )
    has_explicit_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_exactness = isinstance(
        stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_exactness,
        CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedBoundaryExactness,
    )
    has_explicit_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_prefix_exactness = isinstance(
        stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_prefix_exactness,
        CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedBoundaryPrefixExactness,
    )
    has_explicit_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_stem_exactness = isinstance(
        stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_stem_exactness,
        CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedBoundaryStemExactness,
    )
    has_explicit_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_first_unique_boundary_exactness = isinstance(
        stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_first_unique_boundary_exactness,
        CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedBoundaryFirstUniqueBoundaryExactness,
    )
    has_explicit_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_exactness = isinstance(
        stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_exactness,
        CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedBoundaryEarlierBoundaryExactness,
    )
    has_explicit_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_first_unique_boundary_exactness = isinstance(
        stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_first_unique_boundary_exactness,
        CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedBoundaryEarlierBoundaryFirstUniqueBoundaryExactness,
    )
    has_explicit_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_earlier_boundary_exactness = isinstance(
        stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_earlier_boundary_exactness,
        CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedBoundaryEarlierEarlierBoundaryExactness,
    )
    has_explicit_backend_terminal_notice_leading_discriminator_marker_stem_exactness = isinstance(
        stream_backend_terminal_notice_leading_discriminator_marker_stem_exactness,
        CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerStemExactness,
    )
    backend_terminal_notice_prefix_exactness = (
        stream_backend_terminal_notice_prefix_exactness
        if has_explicit_backend_terminal_notice_prefix_exactness
        else build_cache_stream_backend_terminal_notice_prefix_exactness(
            backend_terminal_notice_capture_exactness=(
                backend_terminal_notice_capture_exactness
            )
        )
    )
    backend_terminal_notice_action_discriminant_exactness = (
        stream_backend_terminal_notice_action_discriminant_exactness
        if has_explicit_backend_terminal_notice_action_discriminant_exactness
        else build_cache_stream_backend_terminal_notice_action_discriminant_exactness(
            backend_terminal_notice_prefix_exactness=(
                backend_terminal_notice_prefix_exactness
            )
        )
    )
    backend_terminal_notice_action_stem_exactness = (
        stream_backend_terminal_notice_action_stem_exactness
        if has_explicit_backend_terminal_notice_action_stem_exactness
        else build_cache_stream_backend_terminal_notice_action_stem_exactness(
            backend_terminal_notice_action_discriminant_exactness=(
                backend_terminal_notice_action_discriminant_exactness
            )
        )
    )
    backend_terminal_notice_marker_exactness = (
        stream_backend_terminal_notice_marker_exactness
        if has_explicit_backend_terminal_notice_marker_exactness
        else build_cache_stream_backend_terminal_notice_marker_exactness(
            backend_terminal_notice_action_stem_exactness=(
                backend_terminal_notice_action_stem_exactness
            )
        )
    )
    backend_terminal_notice_marker_prefix_exactness = (
        stream_backend_terminal_notice_marker_prefix_exactness
        if has_explicit_backend_terminal_notice_marker_prefix_exactness
        else build_cache_stream_backend_terminal_notice_marker_prefix_exactness(
            backend_terminal_notice_marker_exactness=(
                backend_terminal_notice_marker_exactness
            )
        )
    )
    backend_terminal_notice_marker_stem_exactness = (
        stream_backend_terminal_notice_marker_stem_exactness
        if has_explicit_backend_terminal_notice_marker_stem_exactness
        else build_cache_stream_backend_terminal_notice_marker_stem_exactness(
            backend_terminal_notice_marker_prefix_exactness=(
                backend_terminal_notice_marker_prefix_exactness
            )
        )
    )
    backend_terminal_notice_marker_discriminant_exactness = (
        stream_backend_terminal_notice_marker_discriminant_exactness
        if has_explicit_backend_terminal_notice_marker_discriminant_exactness
        else build_cache_stream_backend_terminal_notice_marker_discriminant_exactness(
            backend_terminal_notice_marker_stem_exactness=(
                backend_terminal_notice_marker_stem_exactness
            )
        )
    )
    backend_terminal_notice_marker_key_lead_exactness = (
        stream_backend_terminal_notice_marker_key_lead_exactness
        if has_explicit_backend_terminal_notice_marker_key_lead_exactness
        else build_cache_stream_backend_terminal_notice_marker_key_lead_exactness(
            backend_terminal_notice_marker_discriminant_exactness=(
                backend_terminal_notice_marker_discriminant_exactness
            )
        )
    )
    backend_terminal_notice_leading_discriminator_exactness = (
        stream_backend_terminal_notice_leading_discriminator_exactness
        if has_explicit_backend_terminal_notice_leading_discriminator_exactness
        else build_cache_stream_backend_terminal_notice_leading_discriminator_exactness(
            backend_terminal_notice_marker_key_lead_exactness=(
                backend_terminal_notice_marker_key_lead_exactness
            )
        )
    )
    backend_terminal_notice_leading_discriminator_prefix_exactness = (
        stream_backend_terminal_notice_leading_discriminator_prefix_exactness
        if has_explicit_backend_terminal_notice_leading_discriminator_prefix_exactness
        else build_cache_stream_backend_terminal_notice_leading_discriminator_prefix_exactness(
            backend_terminal_notice_leading_discriminator_exactness=(
                backend_terminal_notice_leading_discriminator_exactness
            )
        )
    )
    backend_terminal_notice_leading_discriminator_stem_exactness = (
        stream_backend_terminal_notice_leading_discriminator_stem_exactness
        if has_explicit_backend_terminal_notice_leading_discriminator_stem_exactness
        else build_cache_stream_backend_terminal_notice_leading_discriminator_stem_exactness(
            backend_terminal_notice_leading_discriminator_prefix_exactness=(
                backend_terminal_notice_leading_discriminator_prefix_exactness
            )
        )
    )
    backend_terminal_notice_leading_discriminator_discriminant_exactness = (
        stream_backend_terminal_notice_leading_discriminator_discriminant_exactness
        if has_explicit_backend_terminal_notice_leading_discriminator_discriminant_exactness
        else build_cache_stream_backend_terminal_notice_leading_discriminator_discriminant_exactness(
            backend_terminal_notice_leading_discriminator_stem_exactness=(
                backend_terminal_notice_leading_discriminator_stem_exactness
            )
        )
    )
    backend_terminal_notice_leading_discriminator_marker_exactness = (
        stream_backend_terminal_notice_leading_discriminator_marker_exactness
        if has_explicit_backend_terminal_notice_leading_discriminator_marker_exactness
        else build_cache_stream_backend_terminal_notice_leading_discriminator_marker_exactness(
            backend_terminal_notice_leading_discriminator_discriminant_exactness=(
                backend_terminal_notice_leading_discriminator_discriminant_exactness
            )
        )
    )
    backend_terminal_notice_leading_discriminator_marker_prefix_exactness = (
        stream_backend_terminal_notice_leading_discriminator_marker_prefix_exactness
        if has_explicit_backend_terminal_notice_leading_discriminator_marker_prefix_exactness
        else build_cache_stream_backend_terminal_notice_leading_discriminator_marker_prefix_exactness(
            backend_terminal_notice_leading_discriminator_marker_exactness=(
                backend_terminal_notice_leading_discriminator_marker_exactness
            )
        )
    )
    backend_terminal_notice_leading_discriminator_marker_stem_exactness = (
        stream_backend_terminal_notice_leading_discriminator_marker_stem_exactness
        if has_explicit_backend_terminal_notice_leading_discriminator_marker_stem_exactness
        else build_cache_stream_backend_terminal_notice_leading_discriminator_marker_stem_exactness(
            backend_terminal_notice_leading_discriminator_marker_prefix_exactness=(
                backend_terminal_notice_leading_discriminator_marker_prefix_exactness
            )
        )
    )
    backend_terminal_notice_leading_discriminator_marker_discriminant_exactness = (
        stream_backend_terminal_notice_leading_discriminator_marker_discriminant_exactness
        if has_explicit_backend_terminal_notice_leading_discriminator_marker_discriminant_exactness
        else build_cache_stream_backend_terminal_notice_leading_discriminator_marker_discriminant_exactness(
            backend_terminal_notice_leading_discriminator_marker_stem_exactness=(
                backend_terminal_notice_leading_discriminator_marker_stem_exactness
            )
        )
    )
    backend_terminal_notice_leading_discriminator_marker_first_unique_boundary_exactness = (
        stream_backend_terminal_notice_leading_discriminator_marker_first_unique_boundary_exactness
        if has_explicit_backend_terminal_notice_leading_discriminator_marker_first_unique_boundary_exactness
        else build_cache_stream_backend_terminal_notice_leading_discriminator_marker_first_unique_boundary_exactness(
            backend_terminal_notice_leading_discriminator_marker_discriminant_exactness=(
                backend_terminal_notice_leading_discriminator_marker_discriminant_exactness
            )
        )
    )
    backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_exactness = (
        stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_exactness
        if has_explicit_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_exactness
        else build_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_exactness(
            backend_terminal_notice_leading_discriminator_marker_first_unique_boundary_exactness=(
                backend_terminal_notice_leading_discriminator_marker_first_unique_boundary_exactness
            )
        )
    )
    backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_prefix_exactness = (
        stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_prefix_exactness
        if has_explicit_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_prefix_exactness
        else build_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_prefix_exactness(
            backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_exactness=(
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_exactness
            )
        )
    )
    backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_stem_exactness = (
        stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_stem_exactness
        if has_explicit_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_stem_exactness
        else build_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_stem_exactness(
            backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_prefix_exactness=(
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_prefix_exactness
            )
        )
    )
    backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_discriminant_exactness = (
        stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_discriminant_exactness
        if has_explicit_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_discriminant_exactness
        else build_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_discriminant_exactness(
            backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_stem_exactness=(
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_stem_exactness
            )
        )
    )
    backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_first_unique_boundary_exactness = (
        stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_first_unique_boundary_exactness
        if has_explicit_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_first_unique_boundary_exactness
        else build_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_first_unique_boundary_exactness(
            backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_discriminant_exactness=(
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_discriminant_exactness
            )
        )
    )
    backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_exactness = (
        stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_exactness
        if has_explicit_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_exactness
        else build_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_exactness(
            backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_first_unique_boundary_exactness=(
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_first_unique_boundary_exactness
            )
        )
    )
    backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_prefix_exactness = (
        stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_prefix_exactness
        if has_explicit_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_prefix_exactness
        else build_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_prefix_exactness(
            backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_exactness=(
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_exactness
            )
        )
    )
    backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_stem_exactness = (
        stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_stem_exactness
        if has_explicit_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_stem_exactness
        else build_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_stem_exactness(
            backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_prefix_exactness=(
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_prefix_exactness
            )
        )
    )
    backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_discriminant_exactness = (
        stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_discriminant_exactness
        if has_explicit_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_discriminant_exactness
        else build_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_discriminant_exactness(
            backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_stem_exactness=(
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_stem_exactness
            )
        )
    )
    backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_first_unique_boundary_exactness = (
        stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_first_unique_boundary_exactness
        if has_explicit_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_first_unique_boundary_exactness
        else build_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_first_unique_boundary_exactness(
            backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_discriminant_exactness=(
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_discriminant_exactness
            )
        )
    )
    backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_exactness = (
        stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_exactness
        if has_explicit_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_exactness
        else build_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_exactness(
            backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_first_unique_boundary_exactness=(
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_first_unique_boundary_exactness
            )
        )
    )
    backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_prefix_exactness = (
        stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_prefix_exactness
        if has_explicit_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_prefix_exactness
        else build_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_prefix_exactness(
            backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_exactness=(
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_exactness
            )
        )
    )
    backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_stem_exactness = (
        stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_stem_exactness
        if has_explicit_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_stem_exactness
        else build_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_stem_exactness(
            backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_prefix_exactness=(
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_prefix_exactness
            )
        )
    )
    backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_first_unique_boundary_exactness = (
        stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_first_unique_boundary_exactness
        if has_explicit_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_first_unique_boundary_exactness
        else build_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_first_unique_boundary_exactness(
            backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_stem_exactness=(
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_stem_exactness
            )
        )
    )
    backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_exactness = (
        stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_exactness
        if has_explicit_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_exactness
        else build_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_exactness(
            backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_first_unique_boundary_exactness=(
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_first_unique_boundary_exactness
            )
        )
    )
    backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_first_unique_boundary_exactness = (
        stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_first_unique_boundary_exactness
        if has_explicit_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_first_unique_boundary_exactness
        else build_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_first_unique_boundary_exactness(
            backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_exactness=(
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_exactness
            )
        )
    )
    backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_earlier_boundary_exactness = (
        stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_earlier_boundary_exactness
        if has_explicit_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_earlier_boundary_exactness
        else build_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_earlier_boundary_exactness(
            backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_first_unique_boundary_exactness=(
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_first_unique_boundary_exactness
            )
        )
    )

    seam_rung = "aggregation_active_seam_unresolved"
    selected_seam = "request_aggregation_not_yet_reentered"
    selected_seam_status = "not_selected"
    preserved_secondary_dependencies = ("request_aggregation_not_yet_reentered",)
    preserved_secondary_runtime_branch = "request_aggregation_not_yet_reentered"
    preserved_secondary_runtime_branch_status = "not_selected"
    residual_blocker = (
        "request-aggregation active seam is not yet exact because request-aggregation reentry is not frozen strongly enough"
    )
    recommended_next_step = (
        "freeze request-aggregation reentry before selecting the active seam inside the request-aggregation chain"
    )

    if (
        reentry.reentry_rung == "aggregation_reentry_exact"
        and reentry.selected_reentry_target == "request_aggregation_window"
        and exactness.exactness_rung == "aggregation_window_blocker_exact"
    ):
        seam_rung = "aggregation_active_seam_exact"
        preserved_secondary_dependencies = ()
        preserved_secondary_runtime_branch = "turboquant_preconditions"
        preserved_secondary_runtime_branch_status = (
            reentry.preserved_secondary_runtime_branch_status
        )
        if exactness.ingress_window_status == "missing_pre_gate_admission_window":
            selected_seam = "pre_gate_admission_window"
            selected_seam_status = exactness.ingress_window_status
            preserved_secondary_dependencies = (
                "single_request_per_child_exchange_blocks_aggregated_dispatch",
                "stream_session_holds_gate_until_completion",
            )
            residual_blocker = (
                "request aggregation now reduces to its active seam on this path: a missing pre-gate admission window before whole-request gate claim, while child exchange, stream hold, and TurboQuant remain secondary"
            )
            recommended_next_step = (
                "continue with the pre-gate admission window seam as the active request-aggregation reduction target without reopening scheduler-branch or carrier-local exactness"
            )
        else:
            selected_seam = child_exactness.next_active_dependency
            selected_seam_status = child_exactness.next_active_dependency_status
            preserved_secondary_dependencies = (
                child_exactness.preserved_stream_dependency_status,
            )
            if (
                handoff_exactness.exactness_rung == "cohort_to_child_handoff_exact"
                and handoff_exactness.handoff_status
                == "cohort_handed_off_to_aggregated_child_exchange_visible"
            ):
                selected_seam = handoff_exactness.next_active_dependency
                selected_seam_status = handoff_exactness.next_active_dependency_status
                preserved_secondary_dependencies = ()
                residual_blocker = (
                    "request aggregation now reduces beyond the non-stream cohort handoff on this path: a bounded pre-gate cohort already reaches one aggregated non-stream child exchange while preserving post-claim serial safety, so stream-session hold becomes the next active dependency and TurboQuant remains exact-but-secondary"
                )
                recommended_next_step = (
                    "freeze the stream-session hold dependency next without reopening non-stream cohort handoff, child exchange capability, or continuous batching"
                )
                if (
                    has_explicit_stream_exactness
                    and stream_exactness.exactness_rung == "stream_hold_dependency_exact"
                ):
                    selected_seam = stream_exactness.next_active_dependency
                    selected_seam_status = stream_exactness.next_active_dependency_status
                    residual_blocker = stream_exactness.residual_blocker
                    recommended_next_step = stream_exactness.recommended_next_step
                if (
                    has_explicit_backend_terminal_event_exactness
                    and backend_terminal_event_exactness.exactness_rung
                    == "stream_backend_terminal_event_exact"
                ):
                    selected_seam = (
                        backend_terminal_event_exactness.next_active_dependency
                    )
                    selected_seam_status = (
                        backend_terminal_event_exactness.next_active_dependency_status
                    )
                    residual_blocker = (
                        backend_terminal_event_exactness.residual_blocker
                    )
                    recommended_next_step = (
                        backend_terminal_event_exactness.recommended_next_step
                    )
                if (
                    has_explicit_backend_terminal_payload_commit_exactness
                    and backend_terminal_payload_commit_exactness.exactness_rung
                    == "stream_backend_terminal_payload_commit_exact"
                ):
                    selected_seam = (
                        backend_terminal_payload_commit_exactness.next_active_dependency
                    )
                    selected_seam_status = (
                        backend_terminal_payload_commit_exactness.next_active_dependency_status
                    )
                    residual_blocker = (
                        backend_terminal_payload_commit_exactness.residual_blocker
                    )
                    recommended_next_step = (
                        backend_terminal_payload_commit_exactness.recommended_next_step
                    )
                if (
                    has_explicit_backend_terminal_payload_capture_exactness
                    and backend_terminal_payload_capture_exactness.exactness_rung
                    == "stream_backend_terminal_payload_capture_exact"
                ):
                    selected_seam = (
                        backend_terminal_payload_capture_exactness.next_active_dependency
                    )
                    selected_seam_status = (
                        backend_terminal_payload_capture_exactness.next_active_dependency_status
                    )
                    residual_blocker = (
                        backend_terminal_payload_capture_exactness.residual_blocker
                    )
                    recommended_next_step = (
                        backend_terminal_payload_capture_exactness.recommended_next_step
                    )
                if (
                    has_explicit_backend_terminal_record_capture_exactness
                    and backend_terminal_record_capture_exactness.exactness_rung
                    == "stream_backend_terminal_record_capture_exact"
                ):
                    selected_seam = (
                        backend_terminal_record_capture_exactness.next_active_dependency
                    )
                    selected_seam_status = (
                        backend_terminal_record_capture_exactness.next_active_dependency_status
                    )
                    residual_blocker = (
                        backend_terminal_record_capture_exactness.residual_blocker
                    )
                    recommended_next_step = (
                        backend_terminal_record_capture_exactness.recommended_next_step
                    )
                if (
                    has_explicit_backend_terminal_record_prefix_exactness
                    and backend_terminal_record_prefix_exactness.exactness_rung
                    == "stream_backend_terminal_record_prefix_exact"
                ):
                    selected_seam = (
                        backend_terminal_record_prefix_exactness.next_active_dependency
                    )
                    selected_seam_status = (
                        backend_terminal_record_prefix_exactness.next_active_dependency_status
                    )
                    residual_blocker = (
                        backend_terminal_record_prefix_exactness.residual_blocker
                    )
                    recommended_next_step = (
                        backend_terminal_record_prefix_exactness.recommended_next_step
                    )
                if (
                    has_explicit_backend_terminal_action_discriminant_exactness
                    and backend_terminal_action_discriminant_exactness.exactness_rung
                    == "stream_backend_terminal_action_discriminant_exact"
                ):
                    selected_seam = (
                        backend_terminal_action_discriminant_exactness.next_active_dependency
                    )
                    selected_seam_status = (
                        backend_terminal_action_discriminant_exactness.next_active_dependency_status
                    )
                    residual_blocker = (
                        backend_terminal_action_discriminant_exactness.residual_blocker
                    )
                    recommended_next_step = (
                        backend_terminal_action_discriminant_exactness.recommended_next_step
                    )
                if (
                    has_explicit_backend_terminal_notice_capture_exactness
                    and backend_terminal_notice_capture_exactness.exactness_rung
                    == "stream_backend_terminal_notice_capture_exact"
                ):
                    selected_seam = (
                        backend_terminal_notice_capture_exactness.next_active_dependency
                    )
                    selected_seam_status = (
                        backend_terminal_notice_capture_exactness.next_active_dependency_status
                    )
                    residual_blocker = (
                        backend_terminal_notice_capture_exactness.residual_blocker
                    )
                    recommended_next_step = (
                        backend_terminal_notice_capture_exactness.recommended_next_step
                    )
                if (
                    has_explicit_backend_terminal_notice_prefix_exactness
                    and backend_terminal_notice_prefix_exactness.exactness_rung
                    == "stream_backend_terminal_notice_prefix_exact"
                ):
                    selected_seam = (
                        backend_terminal_notice_prefix_exactness.next_active_dependency
                    )
                    selected_seam_status = (
                        backend_terminal_notice_prefix_exactness.next_active_dependency_status
                    )
                    residual_blocker = (
                        backend_terminal_notice_prefix_exactness.residual_blocker
                    )
                    recommended_next_step = (
                        backend_terminal_notice_prefix_exactness.recommended_next_step
                    )
                if (
                    has_explicit_backend_terminal_notice_action_discriminant_exactness
                    and backend_terminal_notice_action_discriminant_exactness.exactness_rung
                    == "stream_backend_terminal_notice_action_discriminant_exact"
                ):
                    selected_seam = (
                        backend_terminal_notice_action_discriminant_exactness.next_active_dependency
                    )
                    selected_seam_status = (
                        backend_terminal_notice_action_discriminant_exactness.next_active_dependency_status
                    )
                    residual_blocker = (
                        backend_terminal_notice_action_discriminant_exactness.residual_blocker
                    )
                    recommended_next_step = (
                        backend_terminal_notice_action_discriminant_exactness.recommended_next_step
                    )
                if (
                    has_explicit_backend_terminal_notice_action_stem_exactness
                    and backend_terminal_notice_action_stem_exactness.exactness_rung
                    == "stream_backend_terminal_notice_action_stem_exact"
                ):
                    selected_seam = (
                        backend_terminal_notice_action_stem_exactness.next_active_dependency
                    )
                    selected_seam_status = (
                        backend_terminal_notice_action_stem_exactness.next_active_dependency_status
                    )
                    residual_blocker = (
                        backend_terminal_notice_action_stem_exactness.residual_blocker
                    )
                    recommended_next_step = (
                        backend_terminal_notice_action_stem_exactness.recommended_next_step
                    )
                if (
                    has_explicit_backend_terminal_notice_marker_exactness
                    and backend_terminal_notice_marker_exactness.exactness_rung
                    == "stream_backend_terminal_notice_marker_exact"
                ):
                    selected_seam = (
                        backend_terminal_notice_marker_exactness.next_active_dependency
                    )
                    selected_seam_status = (
                        backend_terminal_notice_marker_exactness.next_active_dependency_status
                    )
                    residual_blocker = (
                        backend_terminal_notice_marker_exactness.residual_blocker
                    )
                    recommended_next_step = (
                        backend_terminal_notice_marker_exactness.recommended_next_step
                    )
                if (
                    has_explicit_backend_terminal_notice_marker_prefix_exactness
                    and backend_terminal_notice_marker_prefix_exactness.exactness_rung
                    == "stream_backend_terminal_notice_marker_prefix_exact"
                ):
                    selected_seam = (
                        backend_terminal_notice_marker_prefix_exactness.next_active_dependency
                    )
                    selected_seam_status = (
                        backend_terminal_notice_marker_prefix_exactness.next_active_dependency_status
                    )
                    residual_blocker = (
                        backend_terminal_notice_marker_prefix_exactness.residual_blocker
                    )
                    recommended_next_step = (
                        backend_terminal_notice_marker_prefix_exactness.recommended_next_step
                    )
                if (
                    has_explicit_backend_terminal_notice_marker_stem_exactness
                    and backend_terminal_notice_marker_stem_exactness.exactness_rung
                    == "stream_backend_terminal_notice_marker_stem_exact"
                ):
                    selected_seam = (
                        backend_terminal_notice_marker_stem_exactness.next_active_dependency
                    )
                    selected_seam_status = (
                        backend_terminal_notice_marker_stem_exactness.next_active_dependency_status
                    )
                    residual_blocker = (
                        backend_terminal_notice_marker_stem_exactness.residual_blocker
                    )
                    recommended_next_step = (
                        backend_terminal_notice_marker_stem_exactness.recommended_next_step
                    )
                if (
                    has_explicit_backend_terminal_notice_marker_discriminant_exactness
                    and backend_terminal_notice_marker_discriminant_exactness.exactness_rung
                    == "stream_backend_terminal_notice_marker_discriminant_exact"
                ):
                    selected_seam = (
                        backend_terminal_notice_marker_discriminant_exactness.next_active_dependency
                    )
                    selected_seam_status = (
                        backend_terminal_notice_marker_discriminant_exactness.next_active_dependency_status
                    )
                    residual_blocker = (
                        backend_terminal_notice_marker_discriminant_exactness.residual_blocker
                    )
                    recommended_next_step = (
                        backend_terminal_notice_marker_discriminant_exactness.recommended_next_step
                    )
                if (
                    has_explicit_backend_terminal_notice_marker_key_lead_exactness
                    and backend_terminal_notice_marker_key_lead_exactness.exactness_rung
                    == "stream_backend_terminal_notice_marker_key_lead_exact"
                ):
                    selected_seam = (
                        backend_terminal_notice_marker_key_lead_exactness.next_active_dependency
                    )
                    selected_seam_status = (
                        backend_terminal_notice_marker_key_lead_exactness.next_active_dependency_status
                    )
                    residual_blocker = (
                        backend_terminal_notice_marker_key_lead_exactness.residual_blocker
                    )
                    recommended_next_step = (
                        backend_terminal_notice_marker_key_lead_exactness.recommended_next_step
                    )
                if (
                    has_explicit_backend_terminal_notice_leading_discriminator_exactness
                    and backend_terminal_notice_leading_discriminator_exactness.exactness_rung
                    == "stream_backend_terminal_notice_leading_discriminator_exact"
                ):
                    selected_seam = (
                        backend_terminal_notice_leading_discriminator_exactness.next_active_dependency
                    )
                    selected_seam_status = (
                        backend_terminal_notice_leading_discriminator_exactness.next_active_dependency_status
                    )
                    residual_blocker = (
                        backend_terminal_notice_leading_discriminator_exactness.residual_blocker
                    )
                    recommended_next_step = (
                        backend_terminal_notice_leading_discriminator_exactness.recommended_next_step
                    )
                if (
                    has_explicit_backend_terminal_notice_leading_discriminator_prefix_exactness
                    and backend_terminal_notice_leading_discriminator_prefix_exactness.exactness_rung
                    == "stream_backend_terminal_notice_leading_discriminator_prefix_exact"
                ):
                    selected_seam = (
                        backend_terminal_notice_leading_discriminator_prefix_exactness.next_active_dependency
                    )
                    selected_seam_status = (
                        backend_terminal_notice_leading_discriminator_prefix_exactness.next_active_dependency_status
                    )
                    residual_blocker = (
                        backend_terminal_notice_leading_discriminator_prefix_exactness.residual_blocker
                    )
                    recommended_next_step = (
                        backend_terminal_notice_leading_discriminator_prefix_exactness.recommended_next_step
                    )
                if (
                    has_explicit_backend_terminal_notice_leading_discriminator_stem_exactness
                    and backend_terminal_notice_leading_discriminator_stem_exactness.exactness_rung
                    == "stream_backend_terminal_notice_leading_discriminator_stem_exact"
                ):
                    selected_seam = (
                        backend_terminal_notice_leading_discriminator_stem_exactness.next_active_dependency
                    )
                    selected_seam_status = (
                        backend_terminal_notice_leading_discriminator_stem_exactness.next_active_dependency_status
                    )
                    residual_blocker = (
                        backend_terminal_notice_leading_discriminator_stem_exactness.residual_blocker
                    )
                    recommended_next_step = (
                        backend_terminal_notice_leading_discriminator_stem_exactness.recommended_next_step
                    )
                if (
                    has_explicit_backend_terminal_notice_leading_discriminator_discriminant_exactness
                    and backend_terminal_notice_leading_discriminator_discriminant_exactness.exactness_rung
                    == "stream_backend_terminal_notice_leading_discriminator_discriminant_exact"
                ):
                    selected_seam = (
                        backend_terminal_notice_leading_discriminator_discriminant_exactness.next_active_dependency
                    )
                    selected_seam_status = (
                        backend_terminal_notice_leading_discriminator_discriminant_exactness.next_active_dependency_status
                    )
                    residual_blocker = (
                        backend_terminal_notice_leading_discriminator_discriminant_exactness.residual_blocker
                    )
                    recommended_next_step = (
                        backend_terminal_notice_leading_discriminator_discriminant_exactness.recommended_next_step
                    )
                if (
                    has_explicit_backend_terminal_notice_leading_discriminator_marker_exactness
                    and backend_terminal_notice_leading_discriminator_marker_exactness.exactness_rung
                    == "stream_backend_terminal_notice_leading_discriminator_marker_exact"
                ):
                    selected_seam = (
                        backend_terminal_notice_leading_discriminator_marker_exactness.next_active_dependency
                    )
                    selected_seam_status = (
                        backend_terminal_notice_leading_discriminator_marker_exactness.next_active_dependency_status
                    )
                    residual_blocker = (
                        backend_terminal_notice_leading_discriminator_marker_exactness.residual_blocker
                    )
                    recommended_next_step = (
                        backend_terminal_notice_leading_discriminator_marker_exactness.recommended_next_step
                    )
                if (
                    has_explicit_backend_terminal_notice_leading_discriminator_marker_prefix_exactness
                    and backend_terminal_notice_leading_discriminator_marker_prefix_exactness.exactness_rung
                    == "stream_backend_terminal_notice_leading_discriminator_marker_prefix_exact"
                ):
                    selected_seam = (
                        backend_terminal_notice_leading_discriminator_marker_prefix_exactness.next_active_dependency
                    )
                    selected_seam_status = (
                        backend_terminal_notice_leading_discriminator_marker_prefix_exactness.next_active_dependency_status
                    )
                    residual_blocker = (
                        backend_terminal_notice_leading_discriminator_marker_prefix_exactness.residual_blocker
                    )
                    recommended_next_step = (
                        backend_terminal_notice_leading_discriminator_marker_prefix_exactness.recommended_next_step
                    )
                if (
                    has_explicit_backend_terminal_notice_leading_discriminator_marker_stem_exactness
                    and backend_terminal_notice_leading_discriminator_marker_stem_exactness.exactness_rung
                    == "stream_backend_terminal_notice_leading_discriminator_marker_stem_exact"
                ):
                    selected_seam = (
                        backend_terminal_notice_leading_discriminator_marker_stem_exactness.next_active_dependency
                    )
                    selected_seam_status = (
                        backend_terminal_notice_leading_discriminator_marker_stem_exactness.next_active_dependency_status
                    )
                    residual_blocker = (
                        backend_terminal_notice_leading_discriminator_marker_stem_exactness.residual_blocker
                    )
                    recommended_next_step = (
                        backend_terminal_notice_leading_discriminator_marker_stem_exactness.recommended_next_step
                    )
                if (
                    has_explicit_backend_terminal_notice_leading_discriminator_marker_discriminant_exactness
                    and backend_terminal_notice_leading_discriminator_marker_discriminant_exactness.exactness_rung
                    == "stream_backend_terminal_notice_leading_discriminator_marker_discriminant_exact"
                ):
                    selected_seam = (
                        backend_terminal_notice_leading_discriminator_marker_discriminant_exactness.next_active_dependency
                    )
                    selected_seam_status = (
                        backend_terminal_notice_leading_discriminator_marker_discriminant_exactness.next_active_dependency_status
                    )
                    residual_blocker = (
                        backend_terminal_notice_leading_discriminator_marker_discriminant_exactness.residual_blocker
                    )
                    recommended_next_step = (
                        backend_terminal_notice_leading_discriminator_marker_discriminant_exactness.recommended_next_step
                    )
                if (
                    backend_terminal_notice_leading_discriminator_marker_first_unique_boundary_exactness.exactness_rung
                    == "stream_backend_terminal_notice_leading_discriminator_marker_first_unique_boundary_exact"
                ):
                    selected_seam = (
                        backend_terminal_notice_leading_discriminator_marker_first_unique_boundary_exactness.next_active_dependency
                    )
                    selected_seam_status = (
                        backend_terminal_notice_leading_discriminator_marker_first_unique_boundary_exactness.next_active_dependency_status
                    )
                    residual_blocker = (
                        backend_terminal_notice_leading_discriminator_marker_first_unique_boundary_exactness.residual_blocker
                    )
                    recommended_next_step = (
                        backend_terminal_notice_leading_discriminator_marker_first_unique_boundary_exactness.recommended_next_step
                    )
                if (
                    backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_exactness.exactness_rung
                    == "stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_exact"
                ):
                    selected_seam = (
                        backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_exactness.next_active_dependency
                    )
                    selected_seam_status = (
                        backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_exactness.next_active_dependency_status
                    )
                    residual_blocker = (
                        backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_exactness.residual_blocker
                    )
                    recommended_next_step = (
                        backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_exactness.recommended_next_step
                    )
                if (
                    backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_prefix_exactness.exactness_rung
                    == "stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_prefix_exact"
                ):
                    selected_seam = (
                        backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_prefix_exactness.next_active_dependency
                    )
                    selected_seam_status = (
                        backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_prefix_exactness.next_active_dependency_status
                    )
                    residual_blocker = (
                        backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_prefix_exactness.residual_blocker
                    )
                    recommended_next_step = (
                        backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_prefix_exactness.recommended_next_step
                    )
                if (
                    backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_stem_exactness.exactness_rung
                    == "stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_stem_exact"
                ):
                    selected_seam = (
                        backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_stem_exactness.next_active_dependency
                    )
                    selected_seam_status = (
                        backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_stem_exactness.next_active_dependency_status
                    )
                    residual_blocker = (
                        backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_stem_exactness.residual_blocker
                    )
                    recommended_next_step = (
                        backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_stem_exactness.recommended_next_step
                    )
                if (
                    backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_discriminant_exactness.exactness_rung
                    == "stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_discriminant_exact"
                ):
                    selected_seam = (
                        backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_discriminant_exactness.next_active_dependency
                    )
                    selected_seam_status = (
                        backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_discriminant_exactness.next_active_dependency_status
                    )
                    residual_blocker = (
                        backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_discriminant_exactness.residual_blocker
                    )
                    recommended_next_step = (
                        backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_discriminant_exactness.recommended_next_step
                    )
                if (
                    backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_first_unique_boundary_exactness.exactness_rung
                    == "stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_first_unique_boundary_exact"
                ):
                    selected_seam = (
                        backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_first_unique_boundary_exactness.next_active_dependency
                    )
                    selected_seam_status = (
                        backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_first_unique_boundary_exactness.next_active_dependency_status
                    )
                    residual_blocker = (
                        backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_first_unique_boundary_exactness.residual_blocker
                    )
                    recommended_next_step = (
                        backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_first_unique_boundary_exactness.recommended_next_step
                    )
                if (
                    backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_exactness.exactness_rung
                    == "stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_exact"
                ):
                    selected_seam = (
                        backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_exactness.next_active_dependency
                    )
                    selected_seam_status = (
                        backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_exactness.next_active_dependency_status
                    )
                    residual_blocker = (
                        backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_exactness.residual_blocker
                    )
                    recommended_next_step = (
                        backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_exactness.recommended_next_step
                    )
                if (
                    backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_prefix_exactness.exactness_rung
                    == "stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_prefix_exact"
                ):
                    selected_seam = (
                        backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_prefix_exactness.next_active_dependency
                    )
                    selected_seam_status = (
                        backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_prefix_exactness.next_active_dependency_status
                    )
                    residual_blocker = (
                        backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_prefix_exactness.residual_blocker
                    )
                    recommended_next_step = (
                        backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_prefix_exactness.recommended_next_step
                    )
                if (
                    backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_stem_exactness.exactness_rung
                    == "stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_stem_exact"
                ):
                    selected_seam = (
                        backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_stem_exactness.next_active_dependency
                    )
                    selected_seam_status = (
                        backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_stem_exactness.next_active_dependency_status
                    )
                    residual_blocker = (
                        backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_stem_exactness.residual_blocker
                    )
                    recommended_next_step = (
                        backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_stem_exactness.recommended_next_step
                    )
                if (
                    backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_discriminant_exactness.exactness_rung
                    == "stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_discriminant_exact"
                ):
                    selected_seam = (
                        backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_discriminant_exactness.next_active_dependency
                    )
                    selected_seam_status = (
                        backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_discriminant_exactness.next_active_dependency_status
                    )
                    residual_blocker = (
                        backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_discriminant_exactness.residual_blocker
                    )
                    recommended_next_step = (
                        backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_discriminant_exactness.recommended_next_step
                    )
                if (
                    backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_first_unique_boundary_exactness.exactness_rung
                    == "stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_first_unique_boundary_exact"
                ):
                    selected_seam = (
                        backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_first_unique_boundary_exactness.next_active_dependency
                    )
                    selected_seam_status = (
                        backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_first_unique_boundary_exactness.next_active_dependency_status
                    )
                    residual_blocker = (
                        backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_first_unique_boundary_exactness.residual_blocker
                    )
                    recommended_next_step = (
                        backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_first_unique_boundary_exactness.recommended_next_step
                    )
                if (
                    backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_exactness.exactness_rung
                    == "stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_exact"
                ):
                    selected_seam = (
                        backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_exactness.next_active_dependency
                    )
                    selected_seam_status = (
                        backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_exactness.next_active_dependency_status
                    )
                    residual_blocker = (
                        backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_exactness.residual_blocker
                    )
                    recommended_next_step = (
                        backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_exactness.recommended_next_step
                    )
                if (
                    backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_prefix_exactness.exactness_rung
                    == "stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_prefix_exact"
                ):
                    selected_seam = (
                        backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_prefix_exactness.next_active_dependency
                    )
                    selected_seam_status = (
                        backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_prefix_exactness.next_active_dependency_status
                    )
                    residual_blocker = (
                        backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_prefix_exactness.residual_blocker
                    )
                    recommended_next_step = (
                        backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_prefix_exactness.recommended_next_step
                    )
                if (
                    backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_stem_exactness.exactness_rung
                    == "stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_stem_exact"
                ):
                    selected_seam = (
                        backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_stem_exactness.next_active_dependency
                    )
                    selected_seam_status = (
                        backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_stem_exactness.next_active_dependency_status
                    )
                    residual_blocker = (
                        backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_stem_exactness.residual_blocker
                    )
                    recommended_next_step = (
                        backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_stem_exactness.recommended_next_step
                    )
                if (
                    backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_first_unique_boundary_exactness.exactness_rung
                    == "stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_first_unique_boundary_exact"
                ):
                    selected_seam = (
                        backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_first_unique_boundary_exactness.next_active_dependency
                    )
                    selected_seam_status = (
                        backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_first_unique_boundary_exactness.next_active_dependency_status
                    )
                    residual_blocker = (
                        backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_first_unique_boundary_exactness.residual_blocker
                    )
                    recommended_next_step = (
                        backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_first_unique_boundary_exactness.recommended_next_step
                    )
                if (
                    backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_exactness.exactness_rung
                    == "stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_exact"
                ):
                    selected_seam = (
                        backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_exactness.next_active_dependency
                    )
                    selected_seam_status = (
                        backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_exactness.next_active_dependency_status
                    )
                    residual_blocker = (
                        backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_exactness.residual_blocker
                    )
                    recommended_next_step = (
                        backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_exactness.recommended_next_step
                    )
                if (
                    backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_first_unique_boundary_exactness.exactness_rung
                    == "stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_first_unique_boundary_exact"
                ):
                    selected_seam = (
                        backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_first_unique_boundary_exactness.next_active_dependency
                    )
                    selected_seam_status = (
                        backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_first_unique_boundary_exactness.next_active_dependency_status
                    )
                    residual_blocker = (
                        backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_first_unique_boundary_exactness.residual_blocker
                    )
                    recommended_next_step = (
                        backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_first_unique_boundary_exactness.recommended_next_step
                    )
                if (
                    backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_earlier_boundary_exactness.exactness_rung
                    == "stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_earlier_boundary_exact"
                    and backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_earlier_boundary_exactness.verdict
                    == "backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_earlier_boundary_introduced"
                ):
                    selected_seam = (
                        backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_earlier_boundary_exactness.next_active_dependency
                    )
                    selected_seam_status = (
                        backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_earlier_boundary_exactness.next_active_dependency_status
                    )
                    residual_blocker = (
                        backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_earlier_boundary_exactness.residual_blocker
                    )
                    recommended_next_step = (
                        backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_earlier_boundary_exactness.recommended_next_step
                    )
            elif (
                child_exactness.child_exchange_status
                == "aggregated_non_stream_child_exchange_visible"
            ):
                residual_blocker = (
                    "request aggregation now reduces beyond child exchange on this path: a bounded pre-gate admission window already forms cohorts before whole-request gate claim and one non-stream child exchange can carry multiple requests, but the main serving path still does not hand off that bounded cohort into the aggregated child exchange while stream hold stays secondary and TurboQuant remains exact-but-secondary"
                )
                recommended_next_step = (
                    "freeze the cohort-to-child handoff dependency next without reopening ingress or child-exchange capability truth; keep child widening non-stream only, preserve post-claim serial invariants, and do not inflate this into stream rewrite or continuous batching"
                )
            else:
                residual_blocker = (
                    "request aggregation now reduces beyond ingress on this path: a bounded pre-gate admission window already forms cohorts before whole-request gate claim, but child exchange still remains one-request-per-exchange while stream hold stays secondary and TurboQuant remains exact-but-secondary"
                )
                recommended_next_step = (
                    "freeze the next request-aggregation dependency on this path without reopening ingress-window truth; keep the bounded cohort window pre-claim only, preserve post-claim serial invariants, and do not inflate this into stream rewrite or continuous batching"
                )

    return CacheRequestAggregationActiveSeam(
        request_aggregation_window_reentry=reentry,
        request_aggregation_window_exactness=exactness,
        child_exchange_exactness=child_exactness,
        cohort_handoff_exactness=handoff_exactness,
        stream_hold_exactness=stream_exactness,
        stream_backend_terminal_event_exactness=backend_terminal_event_exactness,
        stream_backend_terminal_payload_commit_exactness=(
            backend_terminal_payload_commit_exactness
        ),
        stream_backend_terminal_payload_capture_exactness=(
            backend_terminal_payload_capture_exactness
        ),
        stream_backend_terminal_record_capture_exactness=(
            backend_terminal_record_capture_exactness
        ),
        stream_backend_terminal_record_prefix_exactness=(
            backend_terminal_record_prefix_exactness
        ),
        stream_backend_terminal_action_discriminant_exactness=(
            backend_terminal_action_discriminant_exactness
        ),
        stream_backend_terminal_notice_capture_exactness=(
            backend_terminal_notice_capture_exactness
        ),
        stream_backend_terminal_notice_prefix_exactness=(
            backend_terminal_notice_prefix_exactness
        ),
        stream_backend_terminal_notice_action_discriminant_exactness=(
            backend_terminal_notice_action_discriminant_exactness
        ),
        stream_backend_terminal_notice_action_stem_exactness=(
            backend_terminal_notice_action_stem_exactness
        ),
        stream_backend_terminal_notice_marker_exactness=(
            backend_terminal_notice_marker_exactness
        ),
        stream_backend_terminal_notice_marker_prefix_exactness=(
            backend_terminal_notice_marker_prefix_exactness
        ),
        stream_backend_terminal_notice_marker_stem_exactness=(
            backend_terminal_notice_marker_stem_exactness
        ),
        stream_backend_terminal_notice_marker_discriminant_exactness=(
            backend_terminal_notice_marker_discriminant_exactness
        ),
        stream_backend_terminal_notice_marker_key_lead_exactness=(
            backend_terminal_notice_marker_key_lead_exactness
        ),
        stream_backend_terminal_notice_leading_discriminator_exactness=(
            backend_terminal_notice_leading_discriminator_exactness
        ),
        stream_backend_terminal_notice_leading_discriminator_prefix_exactness=(
            backend_terminal_notice_leading_discriminator_prefix_exactness
        ),
        stream_backend_terminal_notice_leading_discriminator_stem_exactness=(
            backend_terminal_notice_leading_discriminator_stem_exactness
        ),
        stream_backend_terminal_notice_leading_discriminator_discriminant_exactness=(
            backend_terminal_notice_leading_discriminator_discriminant_exactness
        ),
        stream_backend_terminal_notice_leading_discriminator_marker_exactness=(
            backend_terminal_notice_leading_discriminator_marker_exactness
        ),
        stream_backend_terminal_notice_leading_discriminator_marker_prefix_exactness=(
            backend_terminal_notice_leading_discriminator_marker_prefix_exactness
        ),
        stream_backend_terminal_notice_leading_discriminator_marker_discriminant_exactness=(
            backend_terminal_notice_leading_discriminator_marker_discriminant_exactness
        ),
        stream_backend_terminal_notice_leading_discriminator_marker_first_unique_boundary_exactness=(
            backend_terminal_notice_leading_discriminator_marker_first_unique_boundary_exactness
        ),
        stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_exactness=(
            backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_exactness
        ),
        stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_prefix_exactness=(
            backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_prefix_exactness
        ),
        stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_stem_exactness=(
            backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_stem_exactness
        ),
        stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_discriminant_exactness=(
            backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_discriminant_exactness
        ),
        stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_first_unique_boundary_exactness=(
            backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_first_unique_boundary_exactness
        ),
        stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_exactness=(
            backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_exactness
        ),
        stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_prefix_exactness=(
            backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_prefix_exactness
        ),
        stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_stem_exactness=(
            backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_stem_exactness
        ),
        stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_discriminant_exactness=(
            backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_discriminant_exactness
        ),
        stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_first_unique_boundary_exactness=(
            backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_first_unique_boundary_exactness
        ),
        stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_exactness=(
            backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_exactness
        ),
        stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_prefix_exactness=(
            backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_prefix_exactness
        ),
        stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_stem_exactness=(
            backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_stem_exactness
        ),
        stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_first_unique_boundary_exactness=(
            backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_first_unique_boundary_exactness
        ),
        stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_exactness=(
            backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_exactness
        ),
        stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_first_unique_boundary_exactness=(
            backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_first_unique_boundary_exactness
        ),
        stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_earlier_boundary_exactness=(
            backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_earlier_boundary_exactness
        ),
        stream_backend_terminal_notice_leading_discriminator_marker_stem_exactness=(
            backend_terminal_notice_leading_discriminator_marker_stem_exactness
        ),
        status="partial",
        seam_rung=seam_rung,
        selected_seam=selected_seam,
        selected_seam_status=selected_seam_status,
        preserved_secondary_dependencies=preserved_secondary_dependencies,
        preserved_secondary_runtime_branch=preserved_secondary_runtime_branch,
        preserved_secondary_runtime_branch_status=preserved_secondary_runtime_branch_status,
        residual_blocker=residual_blocker,
        recommended_next_step=recommended_next_step,
    )


def cache_request_aggregation_active_seam_to_dict(
    seam: CacheRequestAggregationActiveSeam,
) -> dict[str, object]:
    """Serialize request-aggregation active seam truth."""

    return {
        "contract": {
            "surface": "owlmlx.cache_request_aggregation_active_seam",
            "version": "phase45",
            "stable_sections": [
                "summary",
                "selected_seam",
                "preserved_secondary_dependencies",
                "preserved_secondary_runtime_branch",
            ],
        },
        "summary": {
            "status": seam.status,
            "seam_rung": seam.seam_rung,
            "residual_blocker": seam.residual_blocker,
            "recommended_next_step": seam.recommended_next_step,
        },
        "selected_seam": {
            "seam": seam.selected_seam,
            "status": seam.selected_seam_status,
        },
        "preserved_secondary_dependencies": list(seam.preserved_secondary_dependencies),
        "preserved_secondary_runtime_branch": {
            "branch": seam.preserved_secondary_runtime_branch,
            "status": seam.preserved_secondary_runtime_branch_status,
        },
    }
