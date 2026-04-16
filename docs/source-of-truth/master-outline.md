# owlmlx Master Outline

> Status: authoritative outline
> Updated: 2026-04-15

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
72. `phase45-admission-hook-safety-contract.md`
73. `phase45-pre-claim-marker-state-carrier.md`
74. `phase45-pre-claim-marker-clear-observer-boundary.md`
75. `phase45-pre-claim-marker-immutability-boundary.md`
76. `phase45-pre-claim-marker-payload-shape-exactness.md`
77. `phase45-pre-claim-marker-encoding-carrier-exactness.md`
78. `phase45-pre-claim-marker-storage-locality-exactness.md`
79. `phase45-pre-claim-marker-locality-access-exactness.md`
80. `phase45-pre-claim-marker-locality-isolation-exactness.md`
81. `phase45-cache-structural-ingress-seam.md`

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

- this host is **not** a candidate for deeper replacement-grade runtime
  validation

The current gating program priority is:

- establish one supported-host execution baseline

The current locally reducible dominant gap is:

- `cache_scheduler_depth`

The current heavy-weight answer is now frozen:

- `owlmlx.heavy_weight_runtime_repeatability` exists
- current result remains `local_blocked` on this host
- the exact external blocker is now explicit

The next executable closure round is:

- one of:
  - supported-host baseline establishment on a distinct host/system image
  - local cache/scheduler closure work on the `cache_scheduler_depth` branch

The current cache checkpoint result is:

- one bounded pre-gate admission seam now exists before whole-request gate claim
- it remains a structural runtime experiment only
- it does not imply request aggregation, continuous batching, or parity

The current next exact ingress contract question is:

- what safety contract must any future bounded admission hook preserve after
  whole-request gate claim?

The current next exact admission question is:

- can owlmlx define any bounded pre-claim admission contract that stays wholly
  outside whole-request gate claim while preserving the frozen post-claim
  safety contract?

The current next exact staging question is:

- if a future pre-claim seam exists at all, what exact bounded metadata/ticket
  staging work may it own without becoming a hidden gate-claim or execution
  boundary?

The current next exact ownership question is:

- what exact ownership and lifetime can immutable request metadata and ticket
  reservation have before whole-request gate claim, without turning the
  pre-claim seam into hidden execution state?

The current next exact inert-state question is:

- if ticket reservation and immutable request metadata remain inert before gate
  claim, what exact cohort/drop semantics are still allowed to exist on that
  inert state without creating hidden execution rights?

The current next exact lifetime question is:

- if the only allowed inert semantics are drop/cancel markers, what exact
  lifetime and expiry boundary can those markers have before whole-request gate
  claim without creating hidden queue ownership?

The current next exact visibility question is:

- if inert drop/cancel markers have an exact lifetime, what exact visibility
  and discard-trigger semantics can they have before whole-request gate claim
  without becoming hidden queue ownership?

The current next exact trigger-input question is:

- if marker visibility is exact, what exact discard-trigger inputs may clear a
  pre-claim marker before gate claim without turning that trigger path into
  hidden queue ownership?

The current next exact reader/writer question is:

- if trigger inputs are exact, which runtime-owned path may author a marker,
  which may only observe it, and what exact writer ownership must remain absent
  before whole-request gate claim?

The current next exact state-carrier question is:

- if marker reader/writer ownership is exact, what exact inert state carrier
  does a marker live in before gate claim, and what carrier semantics must stay
  absent until whole-request gate claim?

The current next exact clear/observer question is:

- if the inert marker carrier is exact, which path may clear it, which path may
  only observe it, and what clearer ownership must remain unavailable before
  whole-request gate claim?

The current next exact immutability question is:

- if clearer/observer ownership is exact, may any pre-claim path mutate marker
  state beyond clear-only semantics, or must marker state remain fully inert
  until whole-request gate claim?

The current next exact payload-shape question is:

- if marker state is fully immutable before gate claim, do any pre-claim marker
  payload fields exist at all, or must marker state collapse to pure
  presence/absence only?

The current next exact encoding question is:

- if marker payload shape collapses to pure presence/absence, what exact inert
  encoding carrier holds that bit before whole-request gate claim without
  becoming hidden queue ownership?

The current next exact storage-locality question is:

- if marker presence lives in one inert boolean slot, where is that slot stored
  relative to staged metadata/ticket units and does that storage locality stay
  free of hidden queue ownership?

The current next exact locality-access question is:

- if marker storage locality is exact, which exact pre-claim path may reach that
  adjacent inert slot and does any reachability remain free of hidden queue
  ownership?

The current next exact locality-isolation question is:

- if locality access is exact, is that adjacent inert slot isolated per staged
  request or could any shared pending-state locality still remain?

The current next exact locality-lifetime question is:

- if locality isolation is exact, how is that isolated marker slot reclaimed or
  expired relative to staged request lifetime without turning lifetime coupling
  into hidden queue ownership?

The current next exact reclaim-reset question is:

- if locality lifetime coupling is exact, what exact clean-state reset is left
  in the adjacent inert slot after reclaim before any later staged request may
  reuse that locality?

The current next exact admission-carrier question is:

- if reclaim/reset is exact, what exact bounded admission-carrier could exist
  before gate claim without turning that carrier into hidden queue ownership or
  execution-bearing state?

The current next exact admission-carrier field question is:

- if admission-carrier construction is exact, what exact fields may inhabit
  that bounded inert carrier before gate claim without turning it into hidden
  queue ownership?

The current next exact admission-carrier encoding question is:

- if admission-carrier field exactness is frozen, how are those inert fields
  encoded together before gate claim without turning the carrier into hidden
  queue ownership?

The current exact admission-carrier locality answer is:

- if admission-carrier encoding exactness is frozen, where may that bounded
  inert pre-claim record live before gate claim without turning locality into
  hidden queue ownership?

The current exact admission-carrier locality-access answer is:

- if admission-carrier locality exactness is frozen, which exact pre-claim
  paths may reach that bounded inert record before gate claim without turning
  locality access into hidden queue ownership?

The current next exact admission-carrier locality-isolation question is:

- if admission-carrier locality-access exactness is frozen, does that bounded
  inert pre-claim carrier remain isolated per staged request before gate claim
  without becoming shared pending-state locality?

The current next exact admission-carrier locality-lifetime question is:

- if admission-carrier locality-isolation exactness is frozen, how is isolated
  pre-claim carrier locality reclaimed or expired before gate claim without
  becoming retained or cross-request lifetime?

The current next exact admission-carrier reclaim-reset question is:

- if admission-carrier locality-lifetime coupling is frozen, what exact
  clean-state reset does reclaim leave on that bounded inert carrier before any
  later staged request may reuse adjacent locality?

That question is now frozen exactly as:

- `owlmlx.cache_pre_claim_admission_carrier_reclaim_reset_exactness`

The current next exact cache question is:

- whether admission-carrier reclaim/reset exactness is sufficient to reselect
  the next residual carrier sub-branch honestly

That question is now frozen exactly as:

- `owlmlx.cache_pre_claim_admission_carrier_branch_reselection`

The current next exact cache question is:

- which non-carrier cache branch should be reduced next without regressing the
  already-frozen ingress invariants

That question is now frozen exactly as:

- `owlmlx.cache_scheduler_turboquant_branch_reselection`

The current next exact cache question is:

- how the selected scheduler-depth branch should be reduced next without
  regressing already-frozen ingress invariants or inflating TurboQuant

That question is now frozen exactly as:

- `owlmlx.cache_continuous_batching_branch_reduction`

The current next exact cache question is:

- which request-aggregation exactness point is now the active cache reduction
  seam on the current path

That question is now frozen exactly as:

- `owlmlx.cache_request_aggregation_window_reentry`
