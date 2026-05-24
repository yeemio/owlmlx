# owlmlx Master Outline

> Status: authoritative outline
> Updated: 2026-05-23（§5 加 Wave G-5 banner 标记 `phase45-*` 项目脱离 canonical reading sequence；§8 Dominant Question 重置；§1–§4 / §6 / §7 维持 2026-05-12 历史口径）

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

Chinese runtime-spine blueprint: `runtime-spine-architecture-blueprint.zh.md`.

Current release-channel split: `public-release-standard.md`.

Current coordination note for that gate:
`owlcoda-learning-loop-coordination.md`.

Learning artifact v0 decision for the future downstream consumer-readiness gate:
`learning-artifact-v0-decision.md`.

Session-scoped native KV cache experiment:
`session-kv-cache-experimental.md`.

Plan-grade architect docs（独立目录 `docs/architect/` · 不入本索引 · 详见
`docs/architect/README.md`）：`01-mainline-roadmap.md`、`02-state-vs-market-gap.md`、
`03-real-accomplishments.md`、`04-architecture-canvas.md`、`05-alignment-audit.md`
+ `design/` 子目录 8 份 gate spec。

> **2026-05-23 Wave G-5 banner**：下方 numbered list 第 **50–85、87–128** 项
> 共 78 份 `phase45-*` 前缀文档是 wave-45 cache / scheduler / pre-claim /
> stream-backend 分解契约。它们**保留在此 numbered list 中以维持向后兼容**，
> 但已**脱离 canonical reading sequence** —— 阅读优先级是第 **1–49 + 86 +
> 129–145** 项（共 67 项 · 全部非 `phase45-*`）。
>
> `phase45-*` 文档的命名扩散（含 15 份 4+ 层 hyphen 嵌套递归命名）已识别为
> Wave G-4 治理目标，将在独立 round 中讨论归档 / 命名约束 / 迁移路径
> （详见 `docs/architect/05-alignment-audit.md §3.2 / §4.3 / §8`）。本次
> Wave G-5 不做归并 / 迁移 / 删除。

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
125. `phase45-stream-backend-terminal-notice-leading-discriminator-marker-earlier-runtime-owned-boundary-first-unique-boundary-exactness.md`
126. `phase45-stream-backend-terminal-notice-leading-discriminator-marker-earlier-runtime-owned-boundary-earlier-boundary-exactness.md`
127. `phase45-stream-backend-terminal-notice-leading-discriminator-marker-earlier-runtime-owned-boundary-earlier-boundary-first-unique-boundary-exactness.md`
128. `phase45-stream-backend-terminal-notice-leading-discriminator-marker-earlier-runtime-owned-boundary-earlier-earlier-boundary-exactness.md`
129. `delivery-discipline.md`
130. `single-host-orchestration-architecture.md`
131. `release-readiness-backlog.md`
132. `release-readiness-execution-plan.md`
133. `comparative-evidence-harness-contract.md`
134. `comparative-evidence-schema-stub.md`
135. `native-mlx-backend-capability-matrix.md`
136. `release-floor-3-1-cache-scheduler-capability-audit.md`
137. `reclaim-barrier-event.md`
138. `termination-recovery-policy.md`
139. `public-surface.md`
140. `model-release-candidate-program.md`
141. `deepseek-v4-flash-adapter-optimization-candidate.md`
142. `peer-reference-mechanism-audit-for-model-profiles.md`
143. `peer-reference-vendor-provenance-audit.md`
144. `mlx-lm-generation-baseline-triage.md`
145. `model-load-admission.md`

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

> Updated 2026-05-24 · 之前的 dominant gap `memory_discipline_baseline_missing`
> （2026-04 ~ 2026-05-12 口径）已被以下证据闭合：
>
> - **PR #649 alignment**（Stage 2 · 2026-05-12 commit `6141d134`：reclaim
>   barrier stats surface · `MemoryWatermark` · `SettleBarrierEvent`）
> - **B-1a**（Gemma 4-31B-it 通过 · warm p50 TTFT 1542.972 ms → 687.102 ms ·
>   2.246× · `20260516T151100Z`）
> - **B-1b**（cache-on no-regress N=20 · 20/20 warm hits · `failed_reclaim=0` ·
>   `20260517T013342Z`）
> - **B-1c §1**（current-Mac 路径 `interrupted_no_swap_rehearsal=passed` ·
>   累积 ≈24.69h clean native segments · `20260521T064658Z`）
>
> 因此 dominant question 在 2026-05-23 重置；2026-05-24 的 Qwen-only
> no-swap probe 把 §2 drift blocker 从 swap-boundary 问题收窄为
> prompt/session growth allocator policy 问题。

### 8.1 Current Top-Level Question

**owlmlx 如何闭合 §VI 4-gate native backend promote-path —— 特别是 G2
(Reclaim Verified) —— 而不破坏 PR #649 memory discipline，同时让 Campaign F
(speculative path safety) 具备并行起跑条件？**

### 8.2 Current Dominant Gaps（两条并发）

- **`session_kv_drift_under_swap_workload`**：B-1c §2 boundary-safe 4h
  segment（`20260522T164506Z`）跑出 cache 全 clean / swap boundary clean /
  watermark GREEN / reclaim stats clean，但 `active_memory` 在 sample 685
  之后漂 **352 MB > 200 MB budget**。2026-05-24 Qwen-only no-swap probe
  (`20260524T113306Z`) 在 `swap_count=0`、cache drop/expiration/reject 全 0
  的情况下复现同一 352 MB drift，说明 blocker 已从 swap boundary 收窄到
  prompt/session growth allocator policy。下一步决定 G2 是否需要 runtime
  code-grade 修复（settle-on-session-boundary / bounded prompt-growth window /
  allocator high-watermark accounting）还是 drift budget rationale 修订。

- **`native_backend_promote_path_g2_closure`**：§VI 4-gate 中 G1（Cache
  Parity）已通过 B-1a 闭合；G2（Reclaim Verified）通过 B-1b + B-1c §1
  达到约 60%，§2 漂移是当前活跃工作面；G3（Structured-Output Invariance）
  + G4（Speculative Path Landing）未启动，但 **G3 不阻塞于 G2**——Campaign
  F-1（`speculative_execution_status` 状态契约）可独立起跑。

### 8.3 Frozen Heavy-Weight Answer（保持自 2026-05-12 口径 · 仍然成立）

- `owlmlx.heavy_weight_runtime_repeatability` exists
- current result is `supported_host_repeatability_visible` on this host
- the original Kimi heavy boundary remains frozen exactly at `122.0G > 116.0G`
- one budget-fit heavy boundary on
  `/Users/yeemio/AI/Agent/models/gemma-4-31B-it` has entered successfully at
  `62.0G <= 116.0G`
- repeated heavy-weight proof is now visible on that selected path via two
  successful repeat runs under default `~/.owlmlx` truth

### 8.4 Next Executable Closure Rounds（双轨并行）

- **Track 1 · B-1c §2 allocator-policy closure**: Qwen-only no-swap
  boundary-safe probe 已完成（`20260524T113306Z`）并复现 drift；下一 round
  是 runtime/allocator policy 归因：修 settle / prompt-growth window /
  high-watermark accounting，或明确修订 drift budget rationale。完成前不恢复
  §2 aggregate segment
- **Track 2 · Campaign F-1 state contract**: 建立 runtime-owned
  `speculative_execution_status` 状态契约（per
  `docs/architect/01-mainline-roadmap.md §V Campaign F · F1`）· 不依赖
  G2 closure · 可与 Track 1 并行起跑

### 8.5 历史 Phase 45 注脚

Historical Phase 45 cache/governance seam details remain in their individual
`phase45-*` source-of-truth files. They are **not** the current selector for
the next runtime round; **see §5 Wave G-5 banner** for their脱离 canonical
reading sequence 状态。
