# owlmlx Replacement-Grade Stability Gaps

> Status: authoritative
> Updated: 2026-04-13

## 1. Purpose

This document freezes the current replacement-grade stability gap between
`owlmlx` and the local reference runtimes `oMLX` / `vMLX`.

Its purpose is not to claim parity. Its purpose is to stop the `owlmlx` loop
from drifting into narrower specimen or shell concerns while the runtime still
falls short of reference-system stability.

## 2. Honest Top-Level Verdict

`owlmlx` is now a real runtime with real serving seams, real compatibility
entrypoints, and real Owl consumer cutover proof.

`owlmlx` is **not yet** in the same stability class as `oMLX` or `vMLX`.

That means:

- it is no longer honest to call `owlmlx` just a toy
- it is also not honest to present it as customer-ready

The current honest label is:

**early formal runtime, below reference-grade stability**

## 3. Reference Systems Actually Prove More

What `oMLX` and `vMLX` already demonstrate that matters here:

- host-stable local execution on real serving machines
- deeper cache and scheduler behavior than one truth surface or one control
  action
- more mature multi-model lifecycle behavior
- repeatable heavy-weight serving behavior on actual runtime paths
- stronger customer-facing confidence through longer-running operational proof

This is why parity cannot be inferred from `owlmlx` having:

- OpenAI / Anthropic entrypoints
- restart/status contracts
- cutover proofs
- blocker reports

Those are necessary runtime assets. They are not yet sufficient stability.

## 4. Frozen Replacement-Grade Gaps

### 4.1 `host_stable_execution`

Reference systems prove:

- usable local execution baselines exist on real hosts
- serving can proceed without being blocked at import time

`owlmlx` currently has:

- machine-owned blocker truth
- specimen gate
- host forensics
- first-smoke locality decision

`owlmlx` still lacks:

- one verified-safe MLX baseline on a supported host for heavy-weight runtime

Why it blocks customer-grade claims:

- no runtime can claim `oMLX` / `vMLX`-class stability while its primary host
  path remains blocked at the import layer

### 4.2 `cache_scheduler_depth`

Reference systems prove:

- real cache reuse and scheduler depth in live runtime behavior
- cache systems are more than descriptive truth

`owlmlx` currently has:

- cache truth contract
- queue-based single-worker scheduler truth
- runtime-owned cache/scheduler depth status
- runtime-owned cache residency/reuse evidence surface
- runtime-owned cache repeatability evidence surface
- runtime-owned TurboQuant readiness surface
- runtime-owned cache closure rung
- runtime-owned cache counter-gap freeze
- runtime-owned cache counter-feasibility freeze
- runtime-path repeated-serving observations through persistent-child backend bookkeeping
- some operator/control-plane surfaces above it

`owlmlx` still lacks:

- replacement-grade cache/scheduler closure inside the runtime line itself
- deeper scheduler behavior beyond the now-frozen serial floor
- explicit scheduler implementation beyond:
  - `queue_discipline = serial`
  - `max_concurrent = 1`
  - wait-counter visibility
- TurboQuant preconditions beyond the now-frozen exact missing set:
  - `bits_in_cache_key`
  - `invalidates_on_config_toggle`
  - `runtime_verified`

Why it blocks customer-grade claims:

- customer stability requires not just visibility of cache policy, but runtime
  behavior that meaningfully approaches the reference systems

### 4.3 `multi_model_lifecycle_governance`

Reference systems prove:

- stronger model residency, eviction, and lifecycle behavior
- multi-model serving as a governed runtime path, not just a theoretical
  contract

`owlmlx` currently has:

- load/unload/restart semantics
- inventory and budget truth
- runtime-owned multi-model governance status
- runtime-owned multi-model governance controls
- runtime-owned multi-model governance transition ledger
- runtime-owned governance transition observations on the active kernel path
- runtime-owned governance policy-gap freeze

`owlmlx` still lacks:

- pinning
- TTL policy
- eviction-history governance
- deeper replacement-grade multi-model lifecycle depth beyond visible active/default and restart semantics

Why it blocks customer-grade claims:

- customer-grade local runtime is not defined by one-model happy paths alone

### 4.4 `heavy_weight_runtime_repeatability`

Reference systems prove:

- repeatable heavy-weight runtime serving, not just staging or one-off smokes

`owlmlx` currently has:

- specimen completeness gate
- first-smoke gate
- locality decision
- some historical local smokes on other models
- runtime-owned heavy-weight repeatability status

`owlmlx` still lacks:

- repeatable heavy-weight runtime proof on a supported host for the current
  path under active development

Why it blocks customer-grade claims:

- customer trust comes from repeatable runtime behavior, not specimen readiness

### 4.5 `customer_runtime_evidence`

Reference systems prove:

- a body of operational evidence that supports stronger user-facing promises

`owlmlx` currently has:

- formal contracts
- verified tests
- migration seams
- cutover proofs
- runtime-owned customer evidence ledger

`owlmlx` still lacks:

- enough runtime evidence to honestly advance beyond early formal runtime

Why it blocks customer-grade claims:

- stable contracts and cutover proofs are necessary, but still below the
  evidence threshold of a customer-facing runtime

## 5. What This Resets

This document resets one important truth drift:

- the main `owlmlx` goal is **not** "run MiniMax first smoke on this machine"
- the main `owlmlx` goal is **replacement-grade stability alignment**

MiniMax first smoke remains a valid subproblem. It is not the top-level goal.

## 6. Current Dominant Gap

`host_stable_execution` remains a real replacement-grade gap, but the current
host answer is now frozen through `owlmlx.host_stable_execution`.

That means the next locally reducible dominant gap is now:

`cache_scheduler_depth`

Reason:

- the current host is already classified as unsuitable for deeper replacement-grade validation
- continuing to restate the same blocked host truth would not shrink the gap inventory
- cache/scheduler depth was one of the clearest remaining differences versus
  `oMLX` / `vMLX`, and it now has a frozen runtime-owned closure rung
- the exact remaining cache blocker is now explicit:
  - direct runtime-owned `reuse_counter` is now visible on the active runtime path
  - `residency_counter` and `eviction_counter` are now frozen as not-runtime-owned on the current path
  - the scheduler branch is now frozen exactly as `owlmlx.cache_scheduler_floor_gap`
    with:
    - `queue_discipline = serial`
    - `max_concurrent = 1`
    - `scheduler_depth = serial_single_worker`
  - the scheduler-grade remaining work is now frozen exactly as
    `owlmlx.cache_scheduler_implementation_backlog`:
    - `ticketed_fifo` queue policy is now explicit and runtime-owned
    - `continuous_batching`
    - `multi_worker_scheduler_depth`
  - the next scheduler branch is now frozen exactly as
    `owlmlx.cache_scheduler_branch_selection`:
    - `continuous_batching` is the next locally reducible branch
    - `multi_worker_scheduler_depth` stays secondary until concurrency safety
      is revalidated
  - the TurboQuant branch is now frozen exactly as
    `owlmlx.cache_turboquant_preconditions_gap`:
    - `bits_in_cache_key`
    - `invalidates_on_config_toggle`
    - `runtime_verified`
- `multi_model_lifecycle_governance` now has a runtime-owned status surface,
  controls surface, transition ledger, active-kernel governance observations,
  and a governance policy-gap freeze
- its remaining absent controls are now frozen more narrowly as policy-grade
  gaps (`pinning`, `TTL`, `eviction-history governance`) rather than the next
  dominant observation/integration gap
- `heavy_weight_runtime_repeatability` now has a runtime-owned status surface
  too, and the current remaining blocker is exact:
  - a supported host/system image is still required for repeated heavy-weight proof
- `customer_runtime_evidence` already has a runtime-owned evidence ledger, and
  governance can now be frozen more narrowly as a policy-grade residual blocker
  rather than an observation-grade gap
- the next locally reducible dominant gap is therefore
  `cache_scheduler_depth`
- that dominant-gap choice is now also frozen as
  `owlmlx.dominant_gap_reselection`
