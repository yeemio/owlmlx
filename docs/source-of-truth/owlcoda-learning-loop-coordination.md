# OwlCoda Learning Loop Coordination

> Status: authoritative coordination note
> Created: 2026-05-12
> Scope: coordinator decision after Stage 3.2 Track A and Stage 3.3 Track B
> were paused pending mainline direction

## 1. Coordinator Decision

The public release mainline is no longer `A/B` as originally named.

Current disposition:

| Track | Status | Coordinator ruling |
|---|---|---|
| Stage 3.2 Track A — independence cleanup | complete | Closed. It corrected the architecture map and should not reopen unless a doc regression reintroduces migration framing. |
| Stage 3.3 Track B — cache / residency / eviction activation | paused but valid | Keep as a parallel runtime-foundation lane. It is useful for long-running local learning reliability, but it is not the public release gate by itself. |
| New mainline — OwlCoda npm local-model learning loop | active dominant gap | This is now the public release gate and should receive coordinator attention first. |

## 2. Why B Does Not Lead The Public Release Gate

Track B improves `owlmlx`'s own runtime depth:

```text
load decision -> residency -> pressure -> eviction -> release ledger -> status
```

That remains valuable, especially for long-running local learning sessions. But
it does not prove the new public story:

```text
OwlCoda npm package -> owlmlx local model -> self-training data accumulation
-> learning/adaptation -> runtime truth registration -> OwlCoda re-consumption
```

Therefore:

- Track B may continue in parallel if an executor is available.
- Track B must not claim public-release progress except as a supporting
  reliability prerequisite.
- The main coordinator lane must first define and prove the OwlCoda learning
  loop contract.

## 3. New Dominant Gap

`owlcoda_learning_loop_contract_gap`

The missing piece is not another benchmark, route, or public-surface document.
The missing piece is an end-to-end contract that names:

1. what OwlCoda npm captures as training data;
2. what provenance must be attached;
3. how that data enters a learning/adaptation step;
4. how the learned artifact/state is registered in `owlmlx`;
5. how OwlCoda consumes the updated local-model path again;
6. what evidence proves the loop ran without hidden manual bridges.

## 4. Immediate Work Split

Two lanes can run in parallel because their write surfaces do not overlap.

### Lane C0 — Contract And Evidence Map

Owner: coordinator / owlmlx.

Write surface:

- `docs/source-of-truth/`
- `files/execution-prompts/owlmlx/`

No runtime code on the first pass.

Goal:

- freeze the cross-repo learning-loop contract;
- define required evidence records;
- map existing `owlmlx` truth surfaces that can carry the result;
- identify missing runtime surfaces without implementing them yet.

### Lane C1 — OwlCoda npm Discovery

Owner: OwlCoda executor.

Write surface:

- OwlCoda repo only.

First pass should be read-only unless the executor finds a trivial docs-only
handoff need.

Goal:

- confirm the npm package invocation path;
- identify where local-model calls are made;
- identify where interaction transcripts or task data can be captured;
- identify existing storage or provenance hooks;
- report the smallest end-to-end smoke path.

### Lane B — Cache / Residency / Eviction

Owner: owlmlx runtime executor.

Write surface:

- `owlmlx/cache_manager.py`
- `owlmlx/memory_pressure_eviction_policy.py`
- `owlmlx/model_residency_policy.py`
- `owlmlx/runtime/kernel.py`
- focused tests

Goal remains:

- implement deterministic eviction loop.

Constraint:

- report it as `runtime-foundation support for long-running learning`, not as
  public release closure.

## 5. Merge Order

Recommended order:

1. C0 contract first.
2. C1 discovery can run in parallel and report back.
3. B may run in parallel but merges only after C0 confirms no conflict with
   learning-loop runtime truth needs.
4. After C0 + C1, open C2: first end-to-end learning-loop smoke.

## 6. Current Public Release Gate

Public release remains parked until `public-release-standard.md` §3-§4 passes.

Allowed current public-facing status:

```text
internal runtime milestone; public release parked behind OwlCoda npm
local-model learning-loop proof
```

Forbidden:

```text
public release ready
developer preview release
OwlCoda learning loop complete
cache eviction closure equals public release closure
```

## 7. Final Coordinator Verdict

```text
owlcoda_learning_loop_contract_gap_selected
```
