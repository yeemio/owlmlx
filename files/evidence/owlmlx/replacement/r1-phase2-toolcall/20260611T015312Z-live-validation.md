# R1 Phase-2 Live Validation — 20260611T015312Z

owlmlx commit: 3d3ad66b (branch r1-phase2-toolcall-stream-gemma)
Server: fresh isolated :8067 launched from this checkout (restarted after the
tool-shape fix — never validated against a stale process). Models loaded/unloaded
via API; :8066 untouched except API unloads of lab leftovers.

| Check | Surface | Model | Verdict |
|---|---|---|---|
| L1-auto | OpenAI /v1/chat/completions, tool_choice=auto | gemma-4-12B-it | **passed** — tool_calls PRESENT (write, args parse), no tool_parser_missing |
| L1-required | OpenAI /v1/chat/completions, tool_choice=required | gemma-4-12B-it | **passed** |
| L2 | Anthropic /v1/messages stream:true | gemma-4-12B-it | **passed** (after live-found tool-shape fix) — tool_use block, input_json_delta parses, stop_reason=tool_use, no degeneration |
| L3 | Anthropic /v1/messages stream:true | Qwen3.6-27B | **passed** — same bar as L2 |

Raw transcripts: 20260611T015312Z-L1-auto.json, 20260611T015312Z-L1-required.json,
20260611T015312Z-L2-anthropic-stream.sse (pre-fix FAILED run, retained honestly),
20260611T015312Z-L2-anthropic-stream-rerun.sse, 20260611T015312Z-L3-qwen-anthropic-stream.sse.

Live-found defect (fixed in-branch): /v1/messages passed Anthropic-shaped tool
defs verbatim to the backend → garbage template declaration → degenerate
repetition on gemma (same signature as the OwlCoda lab failures). Fixed by
boundary conversion (tools + tool_choice); see commit history.

Bounds (honest): experimental; single-prompt smoke per check, not sustained,
not concurrency-tested; promotes nothing; replacement verdict unchanged
(not yet replaceable). The vlm-engine load plumbing these runs exercised is
pre-existing UNCOMMITTED working-tree code (separate integrity issue, flagged).
