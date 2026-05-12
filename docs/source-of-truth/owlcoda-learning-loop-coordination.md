# OwlCoda Learning Loop Coordination

> Status: corrected coordination note
> Created: 2026-05-12
> Scope: coordinator decision after Stage 3.2 Track A and Stage 3.3 Track B
> were paused pending mainline direction

## 1. Coordinator Correction

The previous wording in this note incorrectly promoted the OwlCoda learning loop
from a downstream public-release consumption gate into the current `owlmlx`
mainline. That was wrong.

Corrected decision:

```text
owlmlx mainline remains owlmlx runtime capability.
OwlCoda is a downstream consumer of owlmlx.
The OwlCoda learning loop is the future downstream consumer-readiness gate,
not the immediate owlmlx implementation mainline and not the sole authority for
owlmlx runtime engineering releases.
```

The release-channel split in `public-release-standard.md` remains valid, but it
does not mean `owlmlx` should immediately switch to OwlCoda integration work.
`owlmlx` first has to reach the runtime capability floor that makes that
downstream loop meaningful.

Current disposition:

| Track | Status | Coordinator ruling |
|---|---|---|
| Stage 3.2 Track A — independence cleanup | complete | Closed. It corrected the architecture map and should not reopen unless a doc regression reintroduces migration framing. |
| Stage 3.3 Track B — cache / residency / eviction activation | resume as current owlmlx mainline | This is an owlmlx-owned runtime capability lane and should proceed before OwlCoda integration work. |
| OwlCoda npm local-model learning loop | future downstream consumer-readiness gate | Park until owlmlx runtime prerequisites are strong enough to be consumed. Do not dispatch OwlCoda work as the current owlmlx mainline. |

## 2. Why B Leads The Current owlmlx Mainline

Track B improves `owlmlx`'s own runtime depth:

```text
load decision -> residency -> pressure -> eviction -> release ledger -> status
```

That is exactly the right current `owlmlx` mainline because the future OwlCoda
learning loop needs long-running local-model stability. It still does not prove
the public story by itself:

```text
OwlCoda npm package -> owlmlx local model -> self-training data accumulation
-> learning/adaptation -> runtime truth registration -> OwlCoda re-consumption
```

Therefore:

- Track B should resume as the current owlmlx runtime lane.
- Track B may support a runtime engineering release, but must not claim
  OwlCoda product-readiness progress except as a reliability prerequisite.
- OwlCoda discovery should wait until the `owlmlx` side has the runtime floor
  required for consumption.

## 3. Current Dominant Gap

`owlmlx_runtime_consumption_prerequisite_gap`

The missing piece is not OwlCoda UI or npm package behavior. The missing piece
is the `owlmlx` runtime floor that makes future OwlCoda consumption safe:

1. deterministic residency / eviction behavior;
2. honest memory-pressure and release evidence;
3. stable model lineage / artifact registration semantics;
4. repeatable local-model serving under the intended long-running workflow;
5. no hidden OwlCoda product-readiness claim from intermediate runtime
   evidence.

## 4. Immediate Work Split

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

### Research Agents

For research-only tasks, the coordinator may open parallel agents directly.
Those agents may inspect candidate contracts, repo surfaces, or prior evidence,
but they must not change implementation files unless a follow-up execution round
is explicitly authorized.

The first research questions should remain `owlmlx`-centered:

1. Which existing owlmlx model-lineage / artifact-layout / training-to-serving
   contracts already support future learning-loop registration?
2. What runtime truth is still missing before an OwlCoda consumer can safely
   rely on local-model learning state?
3. Which part of Track B is actually required before downstream consumption?

## 5. Merge Order

Recommended order:

1. Resume Track B on its own branch.
2. Run optional research agents to map owlmlx training/artifact/lineage surfaces.
3. Close B or identify its blockers.
4. Only then reopen OwlCoda-facing discovery.

## 6. Current Release-Channel Split

Runtime engineering release authority lives in `owlmlx` and is defined by
`public-release-standard.md` §3.

The OwlCoda learning-loop proof remains downstream consumer readiness. It does
not change the current `owlmlx` mainline.

Allowed current public-facing status:

```text
runtime engineering milestone; OwlCoda product readiness parked behind npm
local-model learning-loop proof
```

Forbidden:

```text
OwlCoda product release ready
developer preview release
OwlCoda learning loop complete
cache eviction closure equals public release closure
```

## 7. Final Coordinator Verdict

```text
owlmlx_runtime_mainline_restored_track_b_resumes
```
