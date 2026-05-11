# Stage 1 Archive Manifest

Branch: `refactor/stage-1-archive-spec-layer`

## Methodology

1. Built import graph from every `.py` in `owlmlx/` (193 top-level modules).
2. Computed transitive closure FROM `owlmlx/runtime/*.py`.
3. Modules in closure = LIVE (kept).
4. Modules outside closure = DEAD (archive candidates).
5. Scanned `tests/` and `scripts/` for references to dead modules.

Baseline test collection (pre-archive): **1501 tests collected**.

## Headline numbers

| Asset | Before | After Stage 1 | Archived |
|---|---|---|---|
| `owlmlx/*.py` top-level modules | 193 | 36 | **157** |
| `owlmlx/*.py` LOC | ≈48,800 (top-level) | ≈15,332 | **33,468** |
| Tests (files) | 222 | 64 | **158** |
| Test LOC | 49,453 | ≈23,603 | **25,850** |
| Scripts (files) | 125 | 54 | **71** |
| Script LOC | 24,998 | ≈8,305 | **16,693** |

**Total LOC moving to `archive/spec-layer-v0/`: 76,011**

Notes:
- `runtime/` (17 files, 12,949 LOC) untouched.
- `pyproject.toml` will exclude `archive/` from the published package.
- `archive/` retains full git history (using `git mv`).

## What stays (36 live modules reachable from runtime/)

These are the real spine. Several are the watermark / settle / admission
primitives that align with PR #649's vocabulary — they survive intact and
become the visible architecture once `cache_pre_claim_*` / `cache_stream_*` /
`*_exactness` noise is gone.

```
abort_recovery
cache_manager
cache_residency_tracker
cache_scheduler_status
cache_truth
comparative_evidence_ledger
comparative_evidence_record
comparative_evidence_schema
context_concurrency
gemma4_mtp_drafter
host_pressure
memory_actuator
memory_budget
memory_pressure_contract
memory_pressure_eviction_policy
model_inventory
model_lineage
model_load_admission
model_profile
model_release_candidate_ledger
model_release_candidate_record
model_release_candidate_schema
model_residency_policy
nonresident_loadability_lineage
nonresident_model_admission_policy
orchestration_status
reasoning_trace_policy
reclaim_barrier_event
recovery_supervisor_contract
request_context_length_truth
runtime_health
runtime_model_visibility
runtime_monitor_test_console
scheduler_admission_contract
serving
termination_recovery_policy
```

## Dead modules grouped (157 total)

| Family | Count | LOC |
|---|---:|---:|
| `cache_stream_*` | 84 | 17,589 |
| `evidence_ledger_*` | 3 | 4,370 |
| `cache_pre_claim_*` | 27 | 3,140 |
| `cache_request_*` | 3 | 2,202 |
| `multi_model_*` | 7 | 1,047 |
| `other` | 5 | 787 |
| `ad-hoc / probes` | 4 | 732 |
| `cache_scheduler_*` | 5 | 642 |
| `repeatability_*` | 2 | 608 |
| `cache_pre_gate_*` | 4 | 498 |
| `cache_cohort_*` | 2 | 304 |
| `cache_continuous_*` | 2 | 269 |
| `cache_child_*` | 2 | 260 |
| `cache_closure_*` | 1 | 255 |
| `cache_repeatability_*` | 1 | 237 |
| `cache_counter_*` | 2 | 218 |
| `cache_batching_*` | 1 | 114 |
| `cache_runtime_*` | 1 | 98 |
| `cache_turboquant_*` | 1 | 98 |

## Edge cases — confirmed dead but worth flagging

- `training.py` (227 LOC) — 'training artifact registration'. Per project
  charter `training` is explicitly **not_in_scope**. Archiving aligns
  scope-of-code with scope-of-charter.
- `prefix_cache_feasibility_probe.py` — one of only 4 files in the entire
  package that imports `mlx_lm`, but it's a probe that reports whether
  mlx_lm's prefix-cache primitives are importable. Not consumed by runtime.
  When we implement prefix cache in Stage 4+, the probe gets thrown away
  and replaced with real code.
- `multi_model_pinning_control.py` / `multi_model_ttl_policy_control.py` —
  names suggest features, but content is the same dataclass+builder pattern
  returning `control_absent` / `unsupported`. No runtime consumer.
- `comparative_evidence_runner.py` — runs a benchmark report. Distinct from
  live `comparative_evidence_ledger.py` (which runtime/ does import). The
  runner is replaceable by the new external bench script planned for Stage 6.

## Detailed dead module list

<details><summary>All 157 modules</summary>

```
owlmlx/cache_admission_hook_safety_contract.py  (103 LOC)
owlmlx/cache_batching_mechanism_subgap.py  (114 LOC)
owlmlx/cache_child_exchange_aggregated_dispatch_exactness.py  (146 LOC)
owlmlx/cache_child_exchange_aggregated_dispatch_harness.py  (114 LOC)
owlmlx/cache_closure_rung.py  (255 LOC)
owlmlx/cache_cohort_to_child_exchange_handoff_exactness.py  (155 LOC)
owlmlx/cache_cohort_to_child_exchange_handoff_harness.py  (149 LOC)
owlmlx/cache_continuous_batching_branch_reduction.py  (160 LOC)
owlmlx/cache_continuous_batching_feasibility.py  (109 LOC)
owlmlx/cache_counter_feasibility.py  (104 LOC)
owlmlx/cache_counter_gap.py  (114 LOC)
owlmlx/cache_pre_claim_admission_carrier_branch_reselection.py  (117 LOC)
owlmlx/cache_pre_claim_admission_carrier_construction.py  (113 LOC)
owlmlx/cache_pre_claim_admission_carrier_encoding_exactness.py  (111 LOC)
owlmlx/cache_pre_claim_admission_carrier_field_exactness.py  (109 LOC)
owlmlx/cache_pre_claim_admission_carrier_locality_access_exactness.py  (112 LOC)
owlmlx/cache_pre_claim_admission_carrier_locality_exactness.py  (111 LOC)
owlmlx/cache_pre_claim_admission_carrier_locality_isolation_exactness.py  (113 LOC)
owlmlx/cache_pre_claim_admission_carrier_locality_lifetime_coupling.py  (122 LOC)
owlmlx/cache_pre_claim_admission_carrier_reclaim_reset_exactness.py  (125 LOC)
owlmlx/cache_pre_claim_admission_contract.py  (105 LOC)
owlmlx/cache_pre_claim_inert_state_semantics.py  (149 LOC)
owlmlx/cache_pre_claim_marker_clear_observer_boundary.py  (124 LOC)
owlmlx/cache_pre_claim_marker_encoding_carrier_exactness.py  (113 LOC)
owlmlx/cache_pre_claim_marker_immutability_boundary.py  (110 LOC)
owlmlx/cache_pre_claim_marker_lifetime.py  (120 LOC)
owlmlx/cache_pre_claim_marker_locality_access_exactness.py  (111 LOC)
owlmlx/cache_pre_claim_marker_locality_isolation_exactness.py  (111 LOC)
owlmlx/cache_pre_claim_marker_locality_lifetime_coupling.py  (120 LOC)
owlmlx/cache_pre_claim_marker_payload_shape_exactness.py  (110 LOC)
owlmlx/cache_pre_claim_marker_reader_writer_ownership.py  (122 LOC)
owlmlx/cache_pre_claim_marker_reclaim_reset_exactness.py  (120 LOC)
owlmlx/cache_pre_claim_marker_state_carrier.py  (116 LOC)
owlmlx/cache_pre_claim_marker_storage_locality_exactness.py  (115 LOC)
owlmlx/cache_pre_claim_marker_trigger_inputs.py  (118 LOC)
owlmlx/cache_pre_claim_marker_visibility.py  (119 LOC)
owlmlx/cache_pre_claim_metadata_ticket_ownership.py  (114 LOC)
owlmlx/cache_pre_claim_staging_seam_exactness.py  (110 LOC)
owlmlx/cache_pre_gate_admission_hook_exactness.py  (148 LOC)
owlmlx/cache_pre_gate_admission_hook_harness.py  (84 LOC)
owlmlx/cache_pre_gate_admission_window_seam.py  (143 LOC)
owlmlx/cache_pre_gate_cohort_window_feasibility.py  (123 LOC)
owlmlx/cache_repeatability_evidence.py  (237 LOC)
owlmlx/cache_request_aggregation_active_seam.py  (1890 LOC)
owlmlx/cache_request_aggregation_window_exactness.py  (170 LOC)
owlmlx/cache_request_aggregation_window_reentry.py  (142 LOC)
owlmlx/cache_residency_evidence.py  (194 LOC)
owlmlx/cache_runtime_observation_harness.py  (98 LOC)
owlmlx/cache_scheduler_branch_selection.py  (112 LOC)
owlmlx/cache_scheduler_floor_gap.py  (107 LOC)
owlmlx/cache_scheduler_implementation_backlog.py  (99 LOC)
owlmlx/cache_scheduler_turboquant_branch_reselection.py  (133 LOC)
owlmlx/cache_scheduler_turboquant_split.py  (191 LOC)
owlmlx/cache_stream_backend_terminal_action_discriminant_exactness.py  (170 LOC)
owlmlx/cache_stream_backend_terminal_action_discriminant_harness.py  (235 LOC)
owlmlx/cache_stream_backend_terminal_event_exactness.py  (152 LOC)
owlmlx/cache_stream_backend_terminal_event_harness.py  (174 LOC)
owlmlx/cache_stream_backend_terminal_notice_action_discriminant_exactness.py  (170 LOC)
owlmlx/cache_stream_backend_terminal_notice_action_discriminant_harness.py  (239 LOC)
owlmlx/cache_stream_backend_terminal_notice_action_stem_exactness.py  (172 LOC)
owlmlx/cache_stream_backend_terminal_notice_action_stem_harness.py  (236 LOC)
owlmlx/cache_stream_backend_terminal_notice_capture_exactness.py  (166 LOC)
owlmlx/cache_stream_backend_terminal_notice_capture_harness.py  (235 LOC)
owlmlx/cache_stream_backend_terminal_notice_leading_discriminator_discriminant_exactness.py  (189 LOC)
owlmlx/cache_stream_backend_terminal_notice_leading_discriminator_discriminant_harness.py  (281 LOC)
owlmlx/cache_stream_backend_terminal_notice_leading_discriminator_exactness.py  (175 LOC)
owlmlx/cache_stream_backend_terminal_notice_leading_discriminator_harness.py  (260 LOC)
owlmlx/cache_stream_backend_terminal_notice_leading_discriminator_marker_discriminant_exactness.py  (193 LOC)
owlmlx/cache_stream_backend_terminal_notice_leading_discriminator_marker_discriminant_harness.py  (283 LOC)
owlmlx/cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_exactness.py  (194 LOC)
owlmlx/cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_first_unique_boundary_exactness.py  (182 LOC)
owlmlx/cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_first_unique_boundary_harness.py  (95 LOC)
owlmlx/cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_harness.py  (303 LOC)
owlmlx/cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_earlier_boundary_exactness.py  (194 LOC)
owlmlx/cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_earlier_boundary_harness.py  (311 LOC)
owlmlx/cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_exactness.py  (192 LOC)
owlmlx/cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_first_unique_boundary_exactness.py  (182 LOC)
owlmlx/cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_first_unique_boundary_harness.py  (95 LOC)
owlmlx/cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_harness.py  (300 LOC)
owlmlx/cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_prefix_exactness.py  (194 LOC)
owlmlx/cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_prefix_harness.py  (295 LOC)
owlmlx/cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_stem_exactness.py  (194 LOC)
owlmlx/cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_stem_harness.py  (315 LOC)
owlmlx/cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_discriminant_exactness.py  (194 LOC)
owlmlx/cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_discriminant_harness.py  (275 LOC)
owlmlx/cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_exactness.py  (194 LOC)
owlmlx/cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_first_unique_boundary_exactness.py  (182 LOC)
owlmlx/cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_first_unique_boundary_harness.py  (97 LOC)
owlmlx/cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_harness.py  (279 LOC)
owlmlx/cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_prefix_exactness.py  (194 LOC)
owlmlx/cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_prefix_harness.py  (275 LOC)
owlmlx/cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_stem_exactness.py  (194 LOC)
owlmlx/cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_stem_harness.py  (273 LOC)
owlmlx/cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_discriminant_exactness.py  (194 LOC)
owlmlx/cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_discriminant_harness.py  (287 LOC)
owlmlx/cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_exactness.py  (194 LOC)
owlmlx/cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_first_unique_boundary_exactness.py  (184 LOC)
owlmlx/cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_first_unique_boundary_harness.py  (97 LOC)
owlmlx/cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_harness.py  (295 LOC)
owlmlx/cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_prefix_exactness.py  (194 LOC)
owlmlx/cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_prefix_harness.py  (287 LOC)
owlmlx/cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_stem_exactness.py  (194 LOC)
owlmlx/cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_stem_harness.py  (285 LOC)
owlmlx/cache_stream_backend_terminal_notice_leading_discriminator_marker_exactness.py  (187 LOC)
owlmlx/cache_stream_backend_terminal_notice_leading_discriminator_marker_first_unique_boundary_exactness.py  (182 LOC)
owlmlx/cache_stream_backend_terminal_notice_leading_discriminator_marker_first_unique_boundary_harness.py  (92 LOC)
owlmlx/cache_stream_backend_terminal_notice_leading_discriminator_marker_harness.py  (278 LOC)
owlmlx/cache_stream_backend_terminal_notice_leading_discriminator_marker_prefix_exactness.py  (191 LOC)
owlmlx/cache_stream_backend_terminal_notice_leading_discriminator_marker_prefix_harness.py  (281 LOC)
owlmlx/cache_stream_backend_terminal_notice_leading_discriminator_marker_stem_exactness.py  (194 LOC)
owlmlx/cache_stream_backend_terminal_notice_leading_discriminator_marker_stem_harness.py  (283 LOC)
owlmlx/cache_stream_backend_terminal_notice_leading_discriminator_prefix_exactness.py  (181 LOC)
owlmlx/cache_stream_backend_terminal_notice_leading_discriminator_prefix_harness.py  (275 LOC)
owlmlx/cache_stream_backend_terminal_notice_leading_discriminator_stem_exactness.py  (183 LOC)
owlmlx/cache_stream_backend_terminal_notice_leading_discriminator_stem_harness.py  (277 LOC)
owlmlx/cache_stream_backend_terminal_notice_marker_discriminant_exactness.py  (174 LOC)
owlmlx/cache_stream_backend_terminal_notice_marker_discriminant_harness.py  (243 LOC)
owlmlx/cache_stream_backend_terminal_notice_marker_exactness.py  (170 LOC)
owlmlx/cache_stream_backend_terminal_notice_marker_harness.py  (236 LOC)
owlmlx/cache_stream_backend_terminal_notice_marker_key_lead_exactness.py  (167 LOC)
owlmlx/cache_stream_backend_terminal_notice_marker_key_lead_harness.py  (235 LOC)
owlmlx/cache_stream_backend_terminal_notice_marker_prefix_exactness.py  (168 LOC)
owlmlx/cache_stream_backend_terminal_notice_marker_prefix_harness.py  (236 LOC)
owlmlx/cache_stream_backend_terminal_notice_marker_stem_exactness.py  (173 LOC)
owlmlx/cache_stream_backend_terminal_notice_marker_stem_harness.py  (239 LOC)
owlmlx/cache_stream_backend_terminal_notice_prefix_exactness.py  (172 LOC)
owlmlx/cache_stream_backend_terminal_notice_prefix_harness.py  (237 LOC)
owlmlx/cache_stream_backend_terminal_payload_capture_exactness.py  (166 LOC)
owlmlx/cache_stream_backend_terminal_payload_capture_harness.py  (200 LOC)
owlmlx/cache_stream_backend_terminal_payload_commit_exactness.py  (161 LOC)
owlmlx/cache_stream_backend_terminal_payload_commit_harness.py  (200 LOC)
owlmlx/cache_stream_backend_terminal_record_capture_exactness.py  (168 LOC)
owlmlx/cache_stream_backend_terminal_record_capture_harness.py  (218 LOC)
owlmlx/cache_stream_backend_terminal_record_prefix_exactness.py  (170 LOC)
owlmlx/cache_stream_backend_terminal_record_prefix_harness.py  (226 LOC)
owlmlx/cache_stream_hold_dependency_exactness.py  (151 LOC)
owlmlx/cache_stream_hold_dependency_harness.py  (131 LOC)
owlmlx/cache_structural_ingress_seam.py  (129 LOC)
owlmlx/cache_turboquant_preconditions_gap.py  (98 LOC)
owlmlx/comparative_evidence_runner.py  (1130 LOC)
owlmlx/customer_runtime_evidence.py  (3046 LOC)
owlmlx/dominant_gap_reselection.py  (203 LOC)
owlmlx/heavy_weight_repeatability_status.py  (265 LOC)
owlmlx/multi_model_eviction_history_governance.py  (110 LOC)
owlmlx/multi_model_governance_controls.py  (196 LOC)
owlmlx/multi_model_governance_policy_gap.py  (155 LOC)
owlmlx/multi_model_governance_status.py  (203 LOC)
owlmlx/multi_model_governance_transition_ledger.py  (143 LOC)
owlmlx/multi_model_pinning_control.py  (122 LOC)
owlmlx/multi_model_ttl_policy_control.py  (118 LOC)
owlmlx/prefix_cache_feasibility_probe.py  (142 LOC)
owlmlx/repeatability_harness.py  (445 LOC)
owlmlx/repeatability_statistics.py  (163 LOC)
owlmlx/runtime_status.py  (171 LOC)
owlmlx/serving_status.py  (119 LOC)
owlmlx/training.py  (216 LOC)
owlmlx/turboquant_readiness.py  (171 LOC)
```

</details>

## Commit plan

Five commits, each independently revertable:

1. `archive(spec): cache_stream_* family (84 modules, ~17.5K LOC)`
2. `archive(spec): cache_pre_claim_/cache_pre_gate_/cohort/child/etc. families`
3. `archive(spec): multi_model_/training/probes/runners`
4. `archive(spec): corresponding tests + scripts`
5. `chore: trim __init__.py + add CONTRIBUTING anti-regression rule + exclude archive/ from packaging`

Tests will be run after each commit; the goal is **no live test regressions**.
Test count will drop from 1501 → expected ≈ 400-500 (the 158 archived test files
contain the bulk of the 1501 parametrized cases that drive the spec layer).
