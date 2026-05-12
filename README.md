# owlmlx

A memory-discipline-first MLX serving runtime for Apple Silicon. Single
worker by design. Watermark + settle barrier on every load path.

```python
from owlmlx import MemoryWatermark, WatermarkAction, pre_load_check

verdict = pre_load_check("model-id", runtime_status=current_status)
# verdict.decision ∈ {admit_and_load, defer, reject, unknown}
```

## What this is

`owlmlx` is the MLX runtime we wanted when [oMLX#649][pr649] showed that
Apple Silicon's unified memory needs a different shape of discipline than
multi-host servers were designed for. Two primitives are central:

- **MemoryWatermark** — four-level projected utilization classification
  (`GREEN < 65 % < YELLOW < 80 % < RED < 90 % < FATAL`) consulted before
  every model load. Pressure-aware eviction picks LRU victims when YELLOW
  or higher; FATAL refuses the load rather than oversubscribing.
- **Settle barrier** — after every model unload, poll
  `mx.get_active_memory()` until the observed reclaim equals the expected
  unload size. The contract is *verified reclaim*, not estimated unload.
  Without this, repeated model switching accumulates Metal buffer pressure
  silently until the system swaps.

[pr649]: https://github.com/jundot/omlx/pull/649

`owlmlx` runs **one generation at a time** (`MAX_GENERATION_CONCURRENCY = 1`).
This is not a temporary limitation. MLX's Metal thread model is unsafe under
concurrent generation on the default stream; a FIFO admission gate trades
throughput for crash-freeness on a single-host Apple Silicon box. Multi-host
batching and continuous batching are explicitly out of scope — projects like
`oMLX` and `vMLX` cover that surface.

The pre-gate cohort hook is also conservative by default: its admission window
is `0 ms` unless `OWLMLX_COHORT_WINDOW_MS` or an explicit test gate enables a
non-zero window. This prevents a single-worker request from paying a dead
cohort wait on the TTFT path while keeping the old aggregated child-exchange
probe available for controlled experiments.

## What this is for

A single Mac Studio / Mac Pro running an inference service for a small team
or a backing service. The deployment shape is:

- One host, unified memory
- 1–10 simultaneous users behind a request queue
- Models swapped in/out during the day; the swap path must not leak memory
- Long uptime expected; restart-safe lifecycle and abort recovery are
  first-class

If your shape is a fleet, continuous batching, or multi-tenant cluster,
look at oMLX or vMLX instead. They have features `owlmlx` doesn't and
won't.

## What ships now

| Surface | Status |
|---|---|
| OpenAI-compatible HTTP (`/v1/chat/completions`, `/v1/completions`, `/v1/embeddings`) | supported |
| Anthropic-compatible HTTP (`/v1/messages`) | supported |
| Memory watermark + settle barrier | supported |
| Pressure-aware LRU eviction | supported |
| Abort recovery (substrate state verified before resuming) | supported |
| Runtime-owned observability (`/v1/runtime/monitor/snapshot`, `/history`, `/metrics`) | supported |
| Native MLX backend (in-process, bypassing `mlx_lm`) | experimental |
| Native session KV cache (`X-Owlmlx-Session-Id`, default off) | experimental |
| Subprocess backend (`mlx_lm` in a separate process) | supported |
| Continuous batching / paged KV cache / implicit prefix matching / multimodal / speculative | **not in scope** |

Short-prompt TPS on `Mac17,6` (`max_tokens=64`, `temperature=0`):

| Model | owlmlx | Reference | Reference runtime |
|---|---|---|---|
| Qwen3.6-27B | 5.45 | 2.81 | oMLX |
| Qwen3.6-35B-A3B | 3.53 | 2.44 | oMLX |
| Gemma 4 | 3.75 | 3.83 | vMLX |

Short-prompt only. These measurements are runtime engineering evidence, not
OwlCoda product-readiness proof. `owlmlx` owns a runtime engineering release
channel; the OwlCoda npm local-learning loop remains the downstream consumer
readiness gate. See `docs/source-of-truth/public-release-standard.md`.

Experimental native session KV cache TTFT evidence (`Qwen3.6-27B-4bit`,
4k system prompt, append-only multi-turn stream, `max_tokens=2`):

| Mode | Warm p50 TTFT | Evidence |
|---|---:|---|
| cache disabled | 4026.099 ms | `files/evidence/owlmlx/bench/session-kv-cache/20260512T123316Z-owlmlx-native-session-kv-ttft-n4.jsonl` |
| cache enabled | 543.389 ms | same run, 3 warm hits / 0 drops |

This is still `experimental`: native backend only, default off, explicit
`X-Owlmlx-Session-Id`, append-only reuse for non-trimmable upstream caches.

## Quick start

```bash
uv sync --extra runtime
uv run pytest             # 1005 cases, ~38 s
uv run python -m uvicorn 'owlmlx.runtime.server:create_app' --factory --port 8082
curl http://127.0.0.1:8082/v1/runtime/monitor/snapshot
```

Project Python is **3.11.15** (pinned via `.python-version`). `pytest`
emits a loud warning if run outside `.venv/`.

## Where to look next

- `docs/source-of-truth/public-release-standard.md` — current release-channel
  split: owlmlx engineering release vs OwlCoda consumer readiness
- `docs/source-of-truth/public-developer-preview-readiness.md` — historical
  developer-preview evidence for the runtime engineering channel
- `docs/source-of-truth/public-surface.md` — frozen public boundary
- `docs/source-of-truth/system-architecture.md` — runtime kernel design
- `docs/source-of-truth/memory-pressure-contract.md` — watermark contract
- `docs/source-of-truth/reclaim-barrier-event.md` — settle barrier contract
  (file name retained for git history; the contract is `SettleBarrierEvent`)
- `docs/source-of-truth/nonresident-model-admission-policy.md` — `pre_load_check`
- `AGENTS.md` — repository navigation + anti-regression rules for
  LLM-assisted contributors

## Development status

Internal runtime milestone as of 2026-05-12. Public Python surface and HTTP
routes are stable enough for the runtime engineering channel, while OwlCoda
product readiness remains parked behind the npm local-model learning-loop
gate. Internal kernel still under active refinement. Stage 1
refactor (2026-05-11) archived 151 spec-as-code modules; Stage 2 (in
progress) aligns landmark vocabulary with [PR #649][pr649]. See
`CHANGELOG.md` (when present) or recent `release(...)` / `refactor(...)`
commits.
