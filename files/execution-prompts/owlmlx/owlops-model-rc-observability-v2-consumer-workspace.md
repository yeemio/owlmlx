# OwlOps Model RC Observability v2 Consumer Workspace

> Status: outbound execution prompt
> Updated: 2026-05-05
> Source repo: `/Users/yeemio/AI/gitrep/owlmlx`
> Target repo: `/Users/yeemio/AI/gitrep/owlops`
> Dependency: owlmlx `owlmlx.model_release_candidate_record` optional
> observability v2 fields

## 1. Mission

Update OwlOps so the Model RC workspace becomes an optimization radar instead
of a result-only board.

OwlOps must consume the runtime-owned observability v2 fields from owlmlx
Model RC `history.records` and render bottleneck categories literally:

- load timing
- reload timing
- unload timing
- queue wait
- TTFT
- post-first-token decode speed
- end-to-end throughput
- resident/test mode
- prompt/template provenance
- quality caveats
- memory peak source

OwlOps must not compute these fields locally when owlmlx does not provide
them.

## 2. Upstream Contract

Read from the existing owlmlx surfaces:

- `GET /v1/runtime/model-release-candidates`
- `GET /v1/runtime/model-release-candidates/history`

Use `history.records` as the matrix source. Do not treat `latest` as the full
mainline verdict, because `latest` may be an experimental DeepSeek record.

New optional fields to normalize when present:

- `load_time_ms`
- `reload_time_ms`
- `unload_time_ms`
- `queue_wait_ms`
- `ttft_ms`
- `decode_tokens_per_second`
- `end_to_end_tokens_per_second`
- `resident_mode`
- `prompt_template_id`
- `quality_caveats`
- `memory_peak_source`

Legacy rows without these fields remain valid. Render missing v2 fields as
`upstream_missing`, not as zero and not as inferred.

## 3. Required UX

In the Model RC workspace:

- keep the existing verdict and blocker rendering
- add a per-model bottleneck row or panel with `load_time_ms`, `ttft_ms`,
  `decode_tokens_per_second`, `end_to_end_tokens_per_second`, `queue_wait_ms`,
  `peak_resident_set_bytes`, and `memory_peak_source`
- visually distinguish end-to-end throughput includes TTFT while decode
  throughput excludes TTFT
- show `quality_caveats` as caveats, not model-quality verdicts
- show `resident_mode` and `prompt_template_id` near the metrics so operators
  can tell whether a run was load/unload RC testing or resident serving
- keep DeepSeek `experimental_only` separate from mainline candidate rows

The goal is to let an operator answer:

- is this model slow because load is slow?
- is it slow because TTFT is high?
- is decode speed actually fine after first token?
- is queueing involved?
- is memory measurement coming from process RSS or another source?
- is the observed issue a prompt/template caveat rather than a runtime speed
  bottleneck?

## 4. Hard Rules

- Do not compute `decode_tokens_per_second` locally from old v1 rows.
- Do not convert missing v2 fields into `0`.
- Do not upgrade any model verdict to `pass`.
- Do not claim release-ready, parity, replacement, equivalent,
  production-grade, beats, wins, or matches.
- Do not make OwlOps the source of runtime truth.
- Do not touch owlmlx, OwlCoda, or `/Users/yeemio/AI/Agent`.
- Do not start model loads from OwlOps in this round; this is read-side
  consumption and rendering only.

## 5. Suggested Implementation Area

Expected OwlOps files to inspect and likely modify:

- `OwlOps/EmbeddedServices/OwlmlxAdapter.swift`
- `OwlOps/EmbeddedServices/ModelReleaseCandidateWorkspaceBuilder.swift`
- `OwlOps/Sources/Views/ModelReleaseCandidateView.swift`
- `OwlOps/Sources/Views/InspectorView.swift`
- `OwlOps/Sources/Resources/zh-Hans.lproj/Localizable.strings`
- `OwlOps/Tests/ModelReleaseCandidateWorkspaceBuilderTests.swift`
- `docs/source-of-truth/owlops-model-rc-b1-consumer-workspace.md`

Keep the write set narrow. If the actual project structure has shifted,
follow the existing Model RC workspace implementation rather than creating a
parallel workspace.

## 6. Verification

Run focused checks first:

```bash
swift build
swift test --filter ModelReleaseCandidateWorkspaceBuilderTests
swift test --filter AppState
```

If the repo has known SwiftPM testing-helper tail behavior, report it
honestly. Do not call a full suite clean unless it actually exits cleanly.

Also run a live read-side probe against owlmlx if `127.0.0.1:8066` is up:

```bash
curl -sS http://127.0.0.1:8066/v1/runtime/model-release-candidates/history
```

The probe should show four records in current owlmlx state:

- `Qwen3.6-27B`
- `Qwen3.6-35B-A3B`
- `gemma-4-31B-it`
- `DeepSeek-V4-Flash-2bit-DQ`

Rows may not yet have v2 fields until owlmlx records are regenerated after the
observability v2 runner change. OwlOps must still render legacy rows safely.

## 7. Acceptance Criteria

This round is closed only when:

- OwlOps normalizes all v2 fields when present
- legacy v1 rows without v2 fields remain renderable
- missing v2 fields are visibly labeled as upstream missing or unavailable
- the UI distinguishes decode throughput from end-to-end throughput
- DeepSeek remains `experimental_only`
- tests cover v2-present and v2-missing rows
- no local inference or verdict upgrade is introduced

## 8. Report Format

Return:

- outcome label
- changed files
- tests and live probes
- screenshot or text evidence of how v2-present and v2-missing rows render
- explicit statement that OwlOps did not compute runtime metrics locally
- blockers / deferred scope
