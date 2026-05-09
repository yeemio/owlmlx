# owlmlx Single-Host Orchestration Architecture

> Status: authoritative
> Updated: 2026-04-23
> Scope: runtime-only architecture for single-host resource orchestration above
> engine execution and below the product shell

## 1. Purpose

This document starts the architecture-level design for the missing
single-host orchestration layer inside `owlmlx`.

The question it answers is:

**What runtime-owned orchestration responsibilities belong above raw engine
execution on one host, and how should `owlmlx` own them without pretending the
current runtime already has full local-scheduler parity?**

This is not a cluster-scheduler document. It is the single-machine equivalent
of the resource-coordination duties that a larger serving stack would normally
delegate outward.

## 2. Why This Layer Exists

`owlmlx` already operates in a regime where "just run the engine" is not
enough:

- model switching affects unified memory pressure
- multiple sessions compete for one serialized serving path
- benchmark and serving workloads can interfere with each other
- stream lifetime can block scheduler progress on the active path
- recoverability after unload, restart, expiry, or reclaim matters to runtime
  truth

On a single Apple Silicon host, these conflicts accumulate on one machine:

- CPU
- Metal execution
- unified memory
- loaded model weights
- KV/cache state
- long-lived session state

That means `owlmlx` needs a runtime-owned orchestration layer, not just a
larger framework name.

## 3. Boundary

This layer belongs to the `owlmlx core runtime`.

It owns:

- admission control before execution begins
- request scheduling policy
- model residency policy
- memory-pressure response on the runtime-owned path
- cache residency / reclaim policy integration
- failure isolation and recovery policy
- orchestration truth surfaces for upper layers

It does not own:

- desktop UX
- dashboard narratives
- cluster scheduling
- multi-node placement
- cloud autoscaling
- product-level pricing, tenancy, or subscription logic

The shell above `owlmlx` may call these policies and display their truth, but
it must not become the only truth source for them.

## 4. Current Honest Baseline

`owlmlx` has already started this work, but only partially.

What exists today:

- a real serialized post-claim execution boundary via `GenerationGate`
- explicit `ticketed_fifo` queue policy and `max_concurrent = 1`
- one bounded pre-gate admission / cohort window on the active cache path
- runtime-owned model inventory, active/default selection, and restartability
- runtime-owned pinning, TTL policy, and eviction-history governance
- runtime-owned visibility and status surfaces for upper-layer consumers

What does not exist yet:

- full continuous batching
- multi-worker scheduler depth
- policy-complete latency / throughput / fairness scheduling
- pressure-aware model placement across competing workloads
- complete cache-residency and reclaim orchestration parity
- failure-domain isolation strong enough to call the layer replacement-grade

So the honest starting label for this layer is:

- `partial`

## 5. Architectural Position

The single-host orchestration layer sits:

1. above raw backend execution and child exchange
2. above simple load/unload primitives
3. above the current serialized execution gate as a policy owner
4. below desktop routing and operator UI

It is not a replacement for `GenerationGate`.

`GenerationGate` is the current safe execution floor. The orchestration layer
decides:

- what may approach that floor
- when it may approach it
- which model should remain resident
- which model should be reclaimed first
- what to do when the host is under pressure

until stronger concurrency safety is revalidated.

## 6. Required Modules

The architecture should be understood as six cooperating runtime-owned modules.

### 6.1 Admission Control

Responsibilities:

- classify incoming work before execution claim
- reject or defer work that cannot fit current runtime policy
- distinguish interactive, streaming, benchmark, and maintenance traffic
- preserve post-claim safety invariants on the active path

Current floor:

- bounded pre-gate admission window
- whole-request gate claim remains the validated safety boundary

### 6.2 Request Scheduler

Responsibilities:

- choose queue discipline and fairness rules
- define whether short interactive work may preempt or bypass bulk work
- prevent starvation under long-running requests
- coordinate stream-hold behavior with future batching mechanisms

Current floor:

- serialized `ticketed_fifo` single-worker scheduling

### 6.3 Residency Manager

Responsibilities:

- decide which models stay resident
- decide which models load on demand
- govern pinning, TTL, and unload eligibility
- expose active/default and resident-model truth

Current floor:

- runtime-owned inventory
- active/default selection
- pinning
- explicit TTL policy and expiry sweep
- visible eviction-history events

### 6.4 Memory And Cache Governor

Responsibilities:

- track memory pressure using runtime-owned truth
- mediate between model weights, KV/cache state, and concurrent work
- decide reclaim, eviction, or restart barriers when cleanup is incomplete
- prevent hidden cache drift from being narrated as health

Current floor:

- memory budget truth
- cache/scheduler depth truth
- partial cache residency/reuse evidence surfaces

### 6.5 Recovery Supervisor

Responsibilities:

- define what happens after failed unload, failed reclaim, or restart
- isolate a polluted worker or child session
- preserve active-model truth across recovery
- fail closed when runtime truth is weaker than runtime demand

Current floor:

- restartability visibility
- restart action surface
- repeated transition and governance observations

### 6.6 Orchestration Truth Surfaces

Responsibilities:

- expose runtime-owned policy and state to upper layers
- keep "supported", "partial", and "experimental" labels honest
- prevent shell-only narratives from redefining runtime behavior

Current floor:

- `/v1/runtime/status`
- cache scheduler and governance surfaces
- model visibility contract

## 7. Non-Negotiable Invariants

Any future orchestration work must preserve these rules unless a later runtime
round explicitly revalidates and replaces them:

1. host safety comes before throughput
2. post-claim serial safety is the current validated floor
3. policy decisions must be runtime-owned, not hidden in shell routing
4. model-lifecycle truth must remain inspectable
5. failure handling must fail closed rather than fabricate readiness

On the active serving path today, that means:

- no hidden bypass of whole-request gate claim
- no fake claim that continuous batching already exists
- no fake claim that multi-worker depth is already safe
- no silent promotion from visibility-only truth to replacement-grade closure

## 8. What This Layer Is Not

It is not:

- Kubernetes on a laptop
- a desktop product feature bundle
- a claim that one queue plus one lock is enough
- a claim that current `owlmlx` already owns full local-runtime orchestration

It is the runtime-owned place where `owlmlx` should eventually answer:

- which request runs next
- which model stays loaded
- which workload gets sacrificed first under pressure
- how long streams may hold shared execution boundaries
- what recovery action is mandatory after failed reclaim or worker pollution

## 9. Immediate Design Program

The next architecture-level work should freeze four contracts before broader
implementation:

1. `scheduler_admission_contract`
   - request classes, admission signals, and reject/defer rules
2. `model_residency_policy`
   - resident/default/pinned/ttl/evictable state machine
3. `memory_pressure_contract`
   - reclaim, unload, restart-barrier, and fail-closed semantics
4. `orchestration_status_surface`
   - one runtime-owned surface that summarizes scheduler, residency, pressure,
     and recovery posture without inflating readiness

## 10. Reference Inputs

External systems may help `owlmlx` think more clearly about orchestration, but
they do not define `owlmlx` identity or architecture.

For this layer, `HAMI` is a useful reference input because it makes one point
very obvious:

- scheduling is its own system responsibility

That insight matters even more on a single host once multiple models, multiple
sessions, and long-running workloads begin to compete for one machine.

What `owlmlx` may borrow from that reference:

- duty decomposition between admission, scheduling, placement/residency, and
  recovery
- explicit policy language instead of ad-hoc queue behavior
- stable contracts between policy decision and execution layer

What `owlmlx` does not adopt from that reference:

- Kubernetes-shaped control planes
- multi-node placement assumptions
- CUDA-hook or device-plugin implementation patterns
- cluster identity, terminology, or deployment form

So the role of `HAMI` here is:

- to sharpen the question
- not to provide the finished local-runtime answer

## 11. Honest Current Conclusion

`owlmlx` has already entered the orchestration problem.

It has not solved it yet.

The current runtime owns a safe serial execution floor plus several real
governance controls, but it does not yet own the full single-host orchestration
layer required for durable multi-model, multi-session, long-running local
serving.
