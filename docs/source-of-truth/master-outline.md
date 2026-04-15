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

The current next exact scheduler subgap is:

- `request_aggregation_window`

The current next exact ingress blocker is:

- `missing_pre_gate_admission_window`

The current next exact runtime-owned boundary question is:

- can owlmlx expose a bounded pre-gate admission hook without breaking the
  validated serial safety boundary after whole-request gate claim?
