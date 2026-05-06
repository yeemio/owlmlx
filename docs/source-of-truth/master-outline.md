# owlmlx Master Outline

> Status: authoritative outline
> Updated: 2026-05-05

## 1. What `owlmlx` Is

`owlmlx` is our own runtime source of truth.

It is the project boundary where our Apple Silicon runtime direction becomes a
first-class system rather than a collection of patches attached to another
runtime.

## 2. What `owlmlx` Is Not

- Not a renamed `oMLX`
- Not a `vMLX` clone
- Not a desktop shell project
- Not the entire current desktop product shell repository
- Not a claim that every runtime path is already mature

## 3. Why `owlmlx` Must Exist

`owlmlx` exists because our runtime goals already exceed the scope of upstream
patching:

- Multi-model switching with explicit memory governance
- Switch-safe behavior under pressure and restart conditions
- Runtime truth exposure to upper layers
- Background-heavy serving paths for large-weight models

These are runtime-level goals, not temporary integration work.

## 4. Current Top-Level Product Truth

- `owlmlx` is our own runtime
- `owlmlx` is intended to replace `oMLX`
- `oMLX` and `vMLX` are borrowable reference systems, not identity sources
- The first mature runtime path is `large-weight runtime path`
- `Kimi` is the first validated specimen on that path
- `Gemma` is the production mainline model (training substrate verified, pilot PASS)
- the current desktop product shell repository sits above `owlmlx`

## 5. Core Documents

1. `master-outline.md`
2. `ARCHITECTURE-TRUTH.md`
3. `product-definition.md`
4. `system-architecture.md`
5. `repository-boundaries.md`
6. `runtime-capability-matrix.md`
7. `runtime-kernel-mvp.md`
8. `runtime2-benchmark-baseline.md`
9. `runtime1-environment-diagnostics.md`
10. `runtime3-serving-surface.md`
11. `runtime3-benchmark-and-streaming.md`
12. `runtime4-transport-and-migration.md`
13. `runtime-contracts.md`
14. `runtime-status-schema.md`
15. `runtime-governance.md`
16. `hazardous-operations.md`
17. `rename-strategy.md`
18. `contract-mapping.md`
19. `runtime-contract-adoption-plan.md`
20. `extraction-inventory.md`
21. `autonomous-loop-discipline.md`
22. `large-weight-path-truth.md`
23. `roadmap.md`
24. `gemma-high-fidelity-role.md`
25. `training-substrate-contract.md`
26. `artifact-layout-contract.md`
27. `training-to-serving-contract.md`
28. `capability-absorption-inventory.md`
29. `ownership-boundary.md`
30. `model-line-placement.md`
31. `first-absorption-target.md`
32. `convergence-posture.md`
33. `hypura-overflow-path-reference.md`
34. `model-lineage-schema.md`
35. `cache-truth-contract.md`
36. `runtime6-anthropic-entrypoint.md`
37. `runtime7-owlcc-cutover-verification.md`
38. `runtime8-owlcoda-cutover-verification.md`
39. `runtime9-source-first-and-replacement-verdict.md`
40. `runtime10-replacement-hardening-and-parity.md`
41. `runtime11-degraded-routing-and-replacement-closure.md`
42. `runtime12-replacement-readiness-verdict.md`
43. `stabilization1-upstream-contract-freeze.md`
44. `stabilization2-mlx-environment-readiness.md`
45. `stabilization2-large-weight-specimen-gate.md`
46. `stabilization2-mlx-import-blocker.md`
47. `stabilization2-mlx-host-forensics.md`
48. `stabilization3-verified-baseline-resolution.md`
49. `replacement-grade-stability-gaps.md`
50. `phase45-host-stable-execution-status.md`
51. `phase45-cache-scheduler-status.md`
52. `phase45-cache-residency-evidence.md`
53. `phase45-cache-repeatability-evidence.md`
54. `phase45-turboquant-readiness.md`
55. `phase45-cache-closure-rung.md`
56. `phase45-multi-model-governance-status.md`
57. `phase45-multi-model-governance-controls.md`
58. `phase45-multi-model-governance-transition-ledger.md`
59. `phase45-multi-model-governance-policy-gap.md`
60. `phase45-heavy-weight-repeatability-status.md`
61. `phase45-customer-runtime-evidence-ledger.md`
62. `phase45-cache-scheduler-floor-gap.md`
63. `phase45-cache-scheduler-implementation-backlog.md`
64. `phase45-cache-turboquant-preconditions-gap.md`
65. `phase45-dominant-gap-reselection.md`
66. `phase45-cache-scheduler-branch-selection.md`
67. `phase45-cache-continuous-batching-feasibility.md`
68. `phase45-cache-batching-mechanism-subgap.md`
69. `phase45-request-aggregation-window-exactness.md`
70. `phase45-pre-gate-cohort-window-feasibility.md`
71. `phase45-pre-gate-admission-hook-exactness.md`
72. `phase45-cache-pre-gate-admission-window-seam.md`
73. `phase45-admission-hook-safety-contract.md`
74. `phase45-pre-claim-marker-state-carrier.md`
75. `phase45-pre-claim-marker-clear-observer-boundary.md`
76. `phase45-pre-claim-marker-immutability-boundary.md`
77. `phase45-pre-claim-marker-payload-shape-exactness.md`
78. `phase45-pre-claim-marker-encoding-carrier-exactness.md`
79. `phase45-pre-claim-marker-storage-locality-exactness.md`
80. `phase45-pre-claim-marker-locality-access-exactness.md`
81. `phase45-pre-claim-marker-locality-isolation-exactness.md`
82. `phase45-cache-structural-ingress-seam.md`
83. `phase45-multi-model-pinning-control.md`
84. `phase45-multi-model-ttl-policy-control.md`
85. `phase45-multi-model-eviction-history-governance.md`
86. `reference-runtime-comparison-matrix.md`
87. `phase45-current-host-heavy-boundary-budget-blocker.md`
88. `phase45-request-aggregation-active-seam.md`
89. `phase45-child-exchange-aggregated-dispatch-exactness.md`
90. `phase45-cohort-to-child-exchange-handoff-exactness.md`
91. `phase45-stream-hold-dependency-exactness.md`
92. `phase45-stream-backend-terminal-event-exactness.md`
93. `phase45-stream-backend-terminal-payload-commit-exactness.md`
94. `phase45-stream-backend-terminal-payload-capture-exactness.md`
95. `phase45-stream-backend-terminal-record-capture-exactness.md`
96. `phase45-stream-backend-terminal-record-prefix-exactness.md`
97. `phase45-stream-backend-terminal-action-discriminant-exactness.md`
98. `phase45-stream-backend-terminal-notice-capture-exactness.md`
99. `phase45-stream-backend-terminal-notice-prefix-exactness.md`
100. `phase45-stream-backend-terminal-notice-action-discriminant-exactness.md`
101. `phase45-stream-backend-terminal-notice-action-stem-exactness.md`
102. `phase45-stream-backend-terminal-notice-marker-exactness.md`
103. `phase45-stream-backend-terminal-notice-marker-prefix-exactness.md`
104. `phase45-stream-backend-terminal-notice-marker-stem-exactness.md`
105. `phase45-stream-backend-terminal-notice-marker-discriminant-exactness.md`
106. `phase45-stream-backend-terminal-notice-marker-key-lead-exactness.md`
107. `phase45-stream-backend-terminal-notice-leading-discriminator-exactness.md`
108. `phase45-stream-backend-terminal-notice-leading-discriminator-prefix-exactness.md`
109. `phase45-stream-backend-terminal-notice-leading-discriminator-stem-exactness.md`
110. `phase45-stream-backend-terminal-notice-leading-discriminator-discriminant-exactness.md`
111. `phase45-stream-backend-terminal-notice-leading-discriminator-marker-exactness.md`
112. `phase45-stream-backend-terminal-notice-leading-discriminator-marker-prefix-exactness.md`
113. `phase45-stream-backend-terminal-notice-leading-discriminator-marker-stem-exactness.md`
114. `phase45-stream-backend-terminal-notice-leading-discriminator-marker-discriminant-exactness.md`
115. `phase45-stream-backend-terminal-notice-leading-discriminator-marker-first-unique-boundary-exactness.md`
116. `phase45-stream-backend-terminal-notice-leading-discriminator-marker-earlier-runtime-owned-discriminator-exactness.md`
117. `phase45-stream-backend-terminal-notice-leading-discriminator-marker-earlier-runtime-owned-discriminator-stem-exactness.md`
118. `phase45-stream-backend-terminal-notice-leading-discriminator-marker-earlier-runtime-owned-discriminator-discriminant-exactness.md`
119. `phase45-stream-backend-terminal-notice-leading-discriminator-marker-earlier-runtime-owned-discriminator-first-unique-boundary-exactness.md`
120. `phase45-stream-backend-terminal-notice-leading-discriminator-marker-earlier-runtime-owned-leading-discriminator-exactness.md`
121. `phase45-stream-backend-terminal-notice-leading-discriminator-marker-earlier-runtime-owned-leading-discriminator-prefix-exactness.md`
122. `phase45-stream-backend-terminal-notice-leading-discriminator-marker-earlier-runtime-owned-boundary-exactness.md`
123. `phase45-stream-backend-terminal-notice-leading-discriminator-marker-earlier-runtime-owned-boundary-prefix-exactness.md`
124. `phase45-stream-backend-terminal-notice-leading-discriminator-marker-earlier-runtime-owned-boundary-stem-exactness.md`
125. `delivery-discipline.md`
126. `single-host-orchestration-architecture.md`
127. `release-readiness-backlog.md`
128. `release-readiness-execution-plan.md`
129. `comparative-evidence-harness-contract.md`
130. `comparative-evidence-schema-stub.md`
131. `release-floor-3-1-cache-scheduler-capability-audit.md`
132. `reclaim-barrier-event.md`
133. `termination-recovery-policy.md`
134. `public-surface.md`
135. `model-release-candidate-program.md`
136. `deepseek-v4-flash-adapter-optimization-candidate.md`
137. `peer-reference-mechanism-audit-for-model-profiles.md`
138. `peer-reference-vendor-provenance-audit.md`
139. `mlx-lm-generation-baseline-triage.md`
140. `model-load-admission.md`

## 6. Adoption Model

`owlmlx` reuses open-source runtime mechanisms wherever they are proven. It does
not require full rewrite of every execution layer. What `owlmlx` owns is
identity, principles, governance, truth contracts, and path semantics. What it
borrows freely is MLX substrate, loader machinery, and proven serving patterns.

External systems such as Hypura may be recorded as research references when
they illuminate future runtime paths. Recording a reference does not promote it
to an adopted backend or supported owlmlx capability.

The formal adoption rule is frozen in `product-definition.md` section 6.

## 7. Autonomous Loop Discipline

`owlmlx` progresses through self-directed iteration rounds. Each round
identifies a dominant gap, executes against it, verifies delivery, and decides
whether to continue. The discipline is frozen in
`autonomous-loop-discipline.md`.

## 8. Current Dominant Question

The current top-level goal is no longer specimen-first and no longer broad
replacement storytelling.

The next question is:

**How does `owlmlx` become a supported-host runtime substrate that upper layers
can trust without inflating replacement claims?**

The current host-level answer is now frozen:

- this host now has one supported candidate baseline for deeper
  replacement-grade runtime validation

The current gating program priority is:

- freeze the current post-structural cache blocker exact and hand any further
  runtime-owned leading-discriminator-marker choice back to coordinator
  without inflating readiness claims

The current dominant gap is:

- `cache_scheduler_depth`

The current heavy-weight answer is now frozen:

- `owlmlx.heavy_weight_runtime_repeatability` exists
- current result is `supported_host_repeatability_visible` on this host
- the original Kimi heavy boundary remains frozen exactly at `122.0G > 116.0G`
- one budget-fit heavy boundary on
  `/Users/yeemio/AI/Agent/models/gemma-4-31B-it` has entered successfully at
  `62.0G <= 116.0G`
- repeated heavy-weight proof is now visible on that selected path via two
  successful repeat runs under default `~/.owlmlx` truth

The next executable closure round is:

- current-host supported candidate baseline is now established
- supported-host repeated heavy-weight proof is now visible on the selected
  budget-fit path
- cache is now the next dominant locally reducible gap
- governance remains frozen
- cache has reopened beyond the old structural checkpoint and now waits at the
  backend-terminal-notice-leading-discriminator-marker-earlier-runtime-owned-boundary-stem seam,
  while fuller earlier-runtime-owned-boundary prefix detection plus fuller
  earlier-runtime-owned-boundary detection remain preserved as secondary
  truth, current marker-discriminant detection remains frozen as the first
  honest unique boundary on the current runtime-owned marker-first record,
  the newer earlier-runtime-owned discriminator discriminant and
  newer earlier-runtime-owned leading-discriminator discriminant remain
  frozen as the first honest unique boundaries on their newer runtime-owned
  records, and old marker-key lead stays preserved as secondary truth

The current cache checkpoint result is:

- one real pre-gate request-aggregation / cohort window is now visible before
  whole-request gate claim
- the old structural and pre-gate window checkpoints remain preserved exact
- one non-stream child exchange now already carries multiple requests in one
  exchange
- the active cache truth now points at
  `owlmlx.cache_request_aggregation_active_seam`
- the current exact cache blocker is
  `backend_stream_exchange_holds_serial_boundary_until_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_stem_detection`
- the newer earlier-runtime-owned leading-discriminator discriminant remains
  frozen as the first honest unique boundary on the newer earlier-runtime-
  owned leading-discriminator record
- a second backend stream can already start before the first iterator consumer
  receives the first stream's terminal event
- a second backend stream can already start before the first terminal payload
  is committed to the first stream queue
- a second backend stream can already start before the first terminal payload
  is decoded and captured
- a second backend stream request can already enter the live backend exchange
  before the first terminal record is fully captured
- a second backend stream request can already enter the live backend exchange
  before the first stream fully matches its terminal-record prefix on child
  stdout
- a second backend stream request can already enter the live backend exchange
  before the first terminal done payload reaches its action discriminant on
  child stdout
- a second backend stream request can already enter the live backend exchange
  before the first terminal-notice record is fully captured
- a second backend stream request can already enter the live backend exchange
  before child stdout fully matches the first terminal-notice prefix
- a second backend stream request can already enter the live backend exchange
  before the first terminal-notice action stem is reached
- a second backend stream request can already enter the live backend exchange
  before child stdout reaches the fuller earlier runtime-owned discriminator
  prefix on the newer discriminator record
- a second backend stream request can already enter the live backend exchange
  before the first explicit terminal-notice marker field is reached
- a second backend stream request can already enter the live backend exchange
  before the first terminal-notice marker key is fully matched
- a second backend stream request can already enter the live backend exchange
  before the first terminal-notice marker stem is reached
- a second backend stream request can already enter the live backend exchange
  before the first terminal-notice marker discriminant is reached
- owlmlx now also owns one runtime-owned terminal-notice leading-discriminator
  record ahead of the old marker-key-lead seam
- a second backend stream request can already enter the live backend exchange
  before the first terminal-notice marker-key lead on the old notice record is
  reached
- a second backend stream request can already enter the live backend exchange
  before child stdout fully matches that runtime-owned leading-discriminator
  action
- a second backend stream request can already enter the live backend exchange
  before child stdout reaches that runtime-owned leading-discriminator prefix
- a second backend stream request can already enter the live backend exchange
  before child stdout reaches that runtime-owned leading-discriminator stem
- a second backend stream request can already enter the live backend exchange
  before child stdout reaches that runtime-owned leading-discriminator
  discriminant
- a second backend stream request can already enter the live backend exchange
  before child stdout reaches the earlier runtime-owned leading-discriminator
  stem on that newer leading-discriminator record
- a second backend stream request can already enter the live backend exchange
  before child stdout reaches the earlier runtime-owned leading-discriminator
  discriminant on that newer leading-discriminator record
- owlmlx now also owns one earlier runtime-owned `terminal_notice_lead` marker
  on that same leading-discriminator record
- the current runtime-owned leading-discriminator marker-discriminant boundary
  remains frozen as the first honest unique boundary on the current
  marker-first record
- owlmlx now also owns one new earlier runtime-owned terminal-notice
  discriminator record ahead of that current marker-discriminant seam
- owlmlx now also owns one new earlier runtime-owned boundary record ahead of
  that newer runtime-owned leading-discriminator record
- a second backend stream request can already enter the live backend exchange
  once child stdout reaches that new earlier runtime-owned boundary stem and
  before child stdout reaches fuller earlier-runtime-owned-boundary prefix
  detection on that same internal record
- the current exact cache blocker is
  `backend_stream_exchange_holds_serial_boundary_until_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_stem_detection`
- marker-key lead remains preserved as the first unique boundary on the old
  terminal-notice record
- it still does not imply continuous batching, parity, or replacement-ready

The current governance fallback result is:

- one real runtime-owned policy control now exists:
  - `owlmlx.multi_model_pinning_control`
- a second real runtime-owned policy control now exists:
  - `owlmlx.multi_model_ttl_policy_control`
- a third real runtime-owned policy control now exists:
  - `owlmlx.multi_model_eviction_history_governance`
- pinning blocks unload on the runtime-owned path
- pin retention across restart is visible
- TTL expiry sweep is visible on the runtime-owned path
- eviction-history governance is visible on the runtime-owned path
- the local governance fallback branch is now policy-closed

The current next governance policy question is:

- no longer another local policy-control round on this host
- governance now waits behind stronger baseline validation on the current host

The current restart condition is:

- freeze the repeated-proof result in a fresh coordinator checkpoint
- do not reopen cache/governance without a fresh coordinator choice
- do not substitute isolated `/tmp` registry truth for the default
  `~/.owlmlx` registry verdict
- Phase 45 no longer stops at `budget_fit_heavy_boundary_entered`; it now holds
  `supported_host_repeatability_visible` on the selected budget-fit path
