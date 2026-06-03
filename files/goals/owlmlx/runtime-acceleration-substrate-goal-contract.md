# Goal Contract

## Goal ID

`owlmlx-runtime-acceleration-substrate-b1c2-b2`

## Title

Turn the B-1c section-2 + B-2 no-header prefix-cache lane into a verified
runtime acceleration substrate without overclaiming DS4/MTP or speculative
serving.

## Success Definition

- B-1c section 2 has executable four-axis evidence for load, switch,
  throughput, and cache-breadth/concurrency pressure, with local threshold
  evidence distinguished from canonical 24-swap graduation evidence.
- B-2 no-header prefix-cache validation remains native-streaming,
  default-off, and route-level, with OpenAI/Anthropic cached-token metadata
  emitted only from real runtime cache events.
- Source-of-truth documents, prompt archives, tests, and evidence agree that
  session KV / automatic prefix cache remains `experimental` until the full
  promotion gate passes.
- DS4 / MTP / speculative surfaces remain truthfully labeled: DS4 is
  technical-preview `partial`, DS4 MTP is unavailable until D3 changes, and
  speculative methods remain unpromoted.

## Blocked Definition

- Blocked if B-1c section-2 runner cannot measure throughput decay from
  generation events without changing the runtime generation contract.
- Blocked if cache-breadth pressure cannot be observed without fabricating
  session-cache counters or merging unrelated prompts.
- Blocked if native route-level verification is unavailable because no local
  model/backend path can run the next required slice.
- Blocked if upstream MLX cache semantics prevent safe rollback/trim and no
  clean fallback path can be recorded.

## Hard Rules

- Do not promote session KV cache, automatic prefix cache, speculative decoding,
  or DS4 MTP to `supported`.
- Do not treat `X-Owlmlx-Session-Id` as the mainstream consumer contract.
- Do not create banned spec-as-code modules under `owlmlx/`.
- Prefer extending existing bench/runtime surfaces that are already consumed by
  tests or operator scripts.
- Leave unrelated dirty files untouched.
- Duration is a reported byproduct for B-1c section 2, not the pass gate.

## Out of Scope

- Paged KV cache.
- Continuous batching.
- Subprocess/default-serving cache-handle transport.
- DS4 MTP implementation before a new D3 checkpoint inspection finds usable
  MTP weights.
- EAGLE / P-EAGLE / draft-model serving implementation.
- OwlCoda-side product integration.

## Current Truth

- B-1c section 2 has clean load/switch evidence, including high-frequency
  forced-swap canaries and resident-cache byte accounting.
- The current B-1c section-2 runner can measure all four axes. The short
  `20260602T095334Z` native threshold smoke passed load, switch, throughput,
  and cache-breadth/concurrency at 3 swaps with 18 throughput samples and
  6 cache-breadth entries, but
  `canonical_gate.canonical_switch_requirement_met=false` and
  `graduates.soak_plus_swap_stability=false`.
- Two operator-paused 24-swap fast-count attempts (`20260602T095953Z` and
  `20260602T100243Z`) are diagnostic partial ledgers only because they have no
  matching rollup and do not satisfy `--require-canonical`.
- The `20260603T012641Z` canonical-threshold attempt produced a blocked
  interrupted rollup after renewed external LoRA contention was detected. It
  reached 20/24 swaps, observed cache eviction pressure, and kept drops /
  expirations / rejects at 0, but it is not canonical: `interrupted=true`,
  `canonical_switch_requirement_met=false`, and throughput decay
  `0.31106123332617563` exceeded the configured `0.30` ceiling.
- The `20260603T031832Z` clean canonical-threshold run passed 24/24 swaps,
  all four configured axes, and cache-eviction pressure. Independent
  `session_kv_soak_audit.py --require-canonical --require-cache-eviction`
  reports `canonical_acceptance_status=canonical_passed`, with drops /
  expirations / rejects all 0 and `session_kv_supported=false`.
- B-2.3 has a narrow no-header automatic prefix slice behind
  `OWLMLX_SESSION_CACHE_AUTO_PREFIX_ENABLED=1`.
- Real route evidence on 2026-06-02 passed on Qwen27, Qwen35, and Gemma31 for
  no-header OpenAI SSE and Anthropic SSE cached/read token metadata.
- `scripts/runtime_native_preview_server.py` now provides the opt-in native
  preview route needed for live cache validation.
- F-1 speculative status surface is `experimental`; no speculative method is
  promoted.
- DeepSeek-V4-Flash-2bit-DQ is technical-preview `partial`; D3 still records
  `mtp_weights_absent_or_stripped`.

## Remaining Gaps

- B-1c section 2 fast-count canonical evidence is now present, but source-of-
  truth must keep the claim ceiling clear: this is not continuous 24h evidence
  and not a standalone Session KV `supported` promotion.
- B-2 route-level validation needs to remain tied to real backend metadata,
  default-off policy, and resident-cache budget evidence.
- Source-of-truth docs need to pivot the dominant gap from B-1c evidence
  collection to B-2 route-level / policy closure without changing the
  capability ceiling.

## Dominant Next Gap

`B-2-post-B-1c-route-level-policy-closure`

The next round should treat `20260603T031832Z` as the accepted B-1c §2
fast-count canonical evidence and move to B-2 no-header prefix-cache
route-level / policy closure. It should revalidate the existing Qwen27/Qwen35/
Gemma31 compat-route ledgers with the offline B-2 audits, refresh B-2 source-of-
truth so it is no longer blocked on B-1c §2, and keep automatic prefix cache
`experimental`, default-off, and native-streaming only.
