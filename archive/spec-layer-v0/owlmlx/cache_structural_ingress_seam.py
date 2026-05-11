"""Runtime-owned structural ingress seam truth for bounded pre-gate admission."""

from __future__ import annotations

from dataclasses import dataclass

from .cache_pre_claim_staging_seam_exactness import (
    CachePreClaimStagingSeamExactness,
    build_cache_pre_claim_staging_seam_exactness,
)
from .cache_pre_gate_admission_window_seam import (
    CachePreGateAdmissionWindowSeam,
    build_cache_pre_gate_admission_window_seam,
)
from .cache_pre_gate_admission_hook_harness import PreGateAdmissionHookHarnessResult


@dataclass(frozen=True, slots=True)
class CacheStructuralIngressSeam:
    """Structural ingress seam truth after the first bounded hook experiment."""

    pre_gate_admission_window_seam: CachePreGateAdmissionWindowSeam
    pre_claim_staging_seam_exactness: CachePreClaimStagingSeamExactness
    hook_harness: PreGateAdmissionHookHarnessResult | None
    status: str
    seam_rung: str
    runtime_owned_hook_status: str
    boundary_status: str
    staging_units: tuple[str, ...]
    preserved_post_claim_invariants: tuple[str, ...]
    residual_blocker: str | None
    recommended_next_step: str


def build_cache_structural_ingress_seam(
    *,
    pre_gate_admission_window_seam: CachePreGateAdmissionWindowSeam | None = None,
    pre_claim_staging_seam_exactness: CachePreClaimStagingSeamExactness | None = None,
    hook_harness: PreGateAdmissionHookHarnessResult | None = None,
) -> CacheStructuralIngressSeam:
    """Build structural ingress seam truth for the bounded hook experiment."""

    seam = (
        pre_gate_admission_window_seam
        if isinstance(pre_gate_admission_window_seam, CachePreGateAdmissionWindowSeam)
        or getattr(pre_gate_admission_window_seam, "seam_rung", None) is not None
        else build_cache_pre_gate_admission_window_seam()
    )
    staging = (
        pre_claim_staging_seam_exactness
        if isinstance(pre_claim_staging_seam_exactness, CachePreClaimStagingSeamExactness)
        or getattr(pre_claim_staging_seam_exactness, "exactness_rung", None) is not None
        else build_cache_pre_claim_staging_seam_exactness()
    )

    seam_rung = "structural_ingress_seam_unverified"
    runtime_owned_hook_status = "not_verified"
    boundary_status = "not_verified"
    staging_units: tuple[str, ...] = ()
    preserved_post_claim_invariants: tuple[str, ...] = ()
    residual_blocker = (
        "the bounded pre-gate admission hook experiment is not yet verified on the runtime path"
    )
    recommended_next_step = (
        "verify a runtime-owned bounded pre-gate admission hook before upgrading cache truth beyond seam exactness"
    )

    if (
        hook_harness is not None
        and hook_harness.runtime_owned_hook_present
        and hook_harness.observed_midflight_staged_count >= 1
        and hook_harness.observed_total_staged >= 2
        and hook_harness.observed_total_claimed >= 2
    ):
        seam_rung = "structural_ingress_seam_introduced"
        runtime_owned_hook_status = "bounded_pre_gate_hook_present"
        boundary_status = "hook_stops_before_whole_request_gate_claim"
        staging_units = hook_harness.staging_units
        preserved_post_claim_invariants = hook_harness.preserved_post_claim_invariants
        residual_blocker = (
            "a structural runtime-owned ingress seam now exists before whole-request gate claim, and it remains bounded to immutable metadata, ticket reservation, and pre-claim admission bookkeeping only; request aggregation, continuous batching, child parallelism, and cache parity remain unsupported"
        )
        recommended_next_step = (
            "treat cache as structural ingress seam introduced only; any later cohort/admission work must stay bounded before gate claim and must not reopen post-claim serial invariants"
        )

    return CacheStructuralIngressSeam(
        pre_gate_admission_window_seam=seam,
        pre_claim_staging_seam_exactness=staging,
        hook_harness=hook_harness,
        status="partial",
        seam_rung=seam_rung,
        runtime_owned_hook_status=runtime_owned_hook_status,
        boundary_status=boundary_status,
        staging_units=staging_units,
        preserved_post_claim_invariants=preserved_post_claim_invariants,
        residual_blocker=residual_blocker,
        recommended_next_step=recommended_next_step,
    )


def cache_structural_ingress_seam_to_dict(
    seam: CacheStructuralIngressSeam,
) -> dict[str, object]:
    """Serialize structural ingress seam truth."""

    return {
        "contract": {
            "surface": "owlmlx.cache_structural_ingress_seam",
            "version": "phase45",
            "stable_sections": [
                "summary",
                "hook",
                "preserved_post_claim_invariants",
            ],
        },
        "summary": {
            "status": seam.status,
            "seam_rung": seam.seam_rung,
            "residual_blocker": seam.residual_blocker,
            "recommended_next_step": seam.recommended_next_step,
        },
        "hook": {
            "runtime_owned_hook_status": seam.runtime_owned_hook_status,
            "boundary_status": seam.boundary_status,
            "staging_units": list(seam.staging_units),
        },
        "preserved_post_claim_invariants": list(seam.preserved_post_claim_invariants),
    }
