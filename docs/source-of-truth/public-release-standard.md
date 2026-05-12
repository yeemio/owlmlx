# owlmlx Release Standard

> Status: authoritative release-channel split
> Created: 2026-05-12
> Updated: 2026-05-12
> Scope: release authority for `owlmlx` after the runtime-spine refactor and
> OwlCoda packaging boundary correction

## 1. One-Line Standard

`owlmlx` owns a runtime engineering release channel. OwlCoda owns the
downstream product acceptance gate that proves an npm package can consume
`owlmlx` for a local-model learning loop.

The OwlCoda loop is required before claiming OwlCoda-backed public product
readiness. It is not a blocker for an `owlmlx` runtime engineering release.

## 2. Release Channels

| Channel | Owner | Release authority | Current status |
|---|---|---|---|
| Runtime engineering release | `owlmlx` | runtime-owned tests, benchmarks, HTTP contracts, memory discipline, stability evidence | active channel |
| Consumer readiness / OwlCoda integration | coordinated `owlmlx` + OwlCoda | OwlCoda npm end-to-end local-model learning loop | downstream gate |
| Public marketing release | product / brand layer | product-ready narrative plus consumer proof | parked |

## 3. Runtime Engineering Release Criteria

An `owlmlx` runtime engineering release may proceed when runtime-owned evidence
supports the claimed version scope:

- supported HTTP routes remain contract-stable
- supported backend paths pass focused and release-relevant tests
- memory pressure, load admission, unload/reclaim, and status truth remain
  honest
- benchmark claims are scoped to measured workloads and raw evidence
- unsupported capabilities stay labelled `not in scope`, `experimental`, or
  `partial`
- no runtime claim depends on OwlCoda UI, package behavior, or marketing copy

This channel may publish scoped runtime versions such as `0.x` without waiting
for OwlCoda.

## 4. OwlCoda Consumer Readiness Gate

The downstream consumer proof remains:

```text
OwlCoda npm package
  -> local model served through owlmlx
  -> user/task interaction produces training data
  -> training-data accumulation is persisted with provenance
  -> LoRA adapter or explicit no-op learning verdict consumes that data
  -> resulting artifact or verdict is registered into owlmlx truth surfaces
  -> OwlCoda consumes the updated local-model path again
```

This loop must be real. It cannot be replaced by:

- a static demo transcript
- an offline-only script with no OwlCoda package path
- a runtime-only benchmark
- a standalone training run that is not registered back into `owlmlx`
- an OwlOps dashboard display without the learning loop

## 5. Relationship To Existing Public Docs

The older "public developer preview" threshold remains historical evidence,
not the only release authority.

The following are valid runtime engineering evidence:

- closed historical release floors
- `public-surface.md` supported HTTP routes
- `public-claim-matrix.md` scoped allowed claims
- measured benchmark and model-release-candidate evidence
- live runtime monitor/status contracts

They do not prove OwlCoda product readiness. They can support an `owlmlx`
runtime engineering release when the version scope is explicit.

## 6. Allowed Claims Before OwlCoda Proof

Allowed with scope:

- "runtime engineering release"
- "technical-preview runtime surface"
- "internal runtime milestone"
- "local MLX runtime surface"
- "OwlCoda integration target"

Forbidden without the downstream proof:

- "OwlCoda learning loop complete"
- "OwlCoda-backed public product release ready"
- "production-ready"
- "replacement-grade public runtime"
- "cache eviction closure equals product release closure"

## 7. Final Ruling

`owlmlx` release authority is no longer delegated to OwlCoda. OwlCoda remains a
downstream consumer and product acceptance gate.
