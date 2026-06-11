# R1 Phase-2 — Tool-Call Completion: Anthropic Streaming (E1) + Gemma Parser Attach (C1)

> design-grade · 2026-06-10 · follows R1 (tool-calling) + the `/v1/messages` A/B fix (`41b8c752`) · **promotes nothing**; capability language stays *experimental* until live evidence lands.

## 1. Problem (all evidence-backed, this week)

OwlCoda (reference consumer) drives models exclusively through **Anthropic `/v1/messages`, streaming**. Two confirmed gaps block end-to-end agentic traffic on owlmlx — the same traffic R4 Phase B (B2 soak) needs:

- **E — streaming drops tool calls.** The backend stream path emits only `token`/`done` events; tool-call parsing happens only in non-streaming `generate`. The Anthropic SSE route therefore never surfaces `tool_use`. (The non-streaming branch was fixed in `41b8c752`; streaming was deliberately left.)
- **C — gemma has no parser.** `gemma-4-12B-it` (`gemma4_unified`) loads via the mlx_vlm engine; its processor/tokenizer exposes no `tool_parser`/`tool_call_start`/`tool_call_end`, so `_parse_native_tool_calls` honestly reports `tool_parser_missing: true` and never parses — **even for `tool_choice: required`, even when the model emits a complete well-formed `<|tool_call>call:NAME{...}<tool_call|>`** (live-verified 2026-06-09 on :8066).

Out of scope (explicitly): true incremental streaming of tool calls (E2 — future optimization); any consumer-repo change; D (gemma degenerate repetition — re-evaluate after C lands); OpenAI-route changes.

## 2. Design

### E1 — Anthropic SSE mirrors the OpenAI route's tools pattern (route-level)

Precedent in-repo: the OpenAI SSE route (`sse_source`, `server_routes_openai.py:850`) already short-circuits when `payload.tools and tool_choice != "none"` — it awaits the **non-streaming** `runtime.generate_messages(...)` and emits the result as SSE chunks. E1 applies the identical pattern to `anthropic_sse_source`:

1. Top of `anthropic_sse_source`: if `payload.tools` is non-empty and `tool_choice` is not the none-shape (Anthropic dict form, e.g. `{"type":"none"}`), await non-streaming `runtime.generate_messages(turns, ...)`.
2. Emit a valid Anthropic SSE sequence:
   - `message_start`
   - optional text block (`content_block_start` type=text + `content_block_delta` text_delta + `content_block_stop`) **only when the policy-cleaned visible text is non-empty** (reuse `_openai_visible_text_for_policy`),
   - one block per tool call (from `_anthropic_tool_use_blocks_from_detail(result.detail)` — already normalizes real `tool_calls` / legacy `tool_uses` conventions): `content_block_start` with `{type:"tool_use", id, name, input:{}}` + `content_block_delta` `input_json_delta` carrying the full arguments JSON as `partial_json` + `content_block_stop`,
   - `message_delta` with `stop_reason="tool_use"` (or `"end_turn"` when no tool blocks) + usage, then `message_stop`.
3. Generate failure → SSE error event then terminate (mirror the OpenAI route's error chunk).
4. No tools → the existing true-streaming path is untouched (including the A/B buffered text cleanup).

Accepted trade-off (same as the OpenAI route already accepted): with tools present, first byte arrives after full generation. A tool-call consumer needs the complete call body anyway.

### C1 — attach an upstream gemma4 tool parser to vlm-loaded sessions (backend-level)

`_parse_native_tool_calls` (mlx_native_backend.py:463) already does everything given three tokenizer attributes. mlx_lm-loaded tokenizers carry them; mlx_vlm-loaded processors do not. Fix at load time:

1. After a successful mlx_vlm-engine load, if the session tokenizer lacks a callable `tool_parser` **and** the model family is gemma4 (reuse `_infer_tool_choice_forcing_family` / profile match), attach `tool_parser`, `tool_call_start`, `tool_call_end` from the upstream gemma4 parser.
2. Parser source: prefer the module that actually exposes a gemma4 parser at runtime — candidates are `mlx_lm.tool_parsers.gemma4` and `mlx_vlm.tool_parsers` (both packages present in the venv). The implementer must probe both, pick a deterministic preference order, and pin it with a unit test. No owlmlx-side reimplementation of the format.
3. Attach failure (import error, missing symbols) → log + leave attributes absent; `tool_parser_missing: true` diagnostics keep telling the truth. Never crash a load over parser attach.
4. Forcing grammar note: `_tool_choice_forcing_family` already knows the gemma4 EBNF; once the parser is attached, `required` forcing + parsing compose without further change.

## 3. Tests

**Unit (TDD, stub backends, no model load):**
- E1-T1: Anthropic SSE + tools, backend returns real convention (`finish_reason="tool_calls"`, `detail["tool_calls"]`) → SSE contains `content_block_start` type=tool_use with correct name/id, `input_json_delta` whose `partial_json` parses to the arguments, `message_delta.stop_reason=="tool_use"`.
- E1-T2: Anthropic SSE + tools, backend returns plain text → text-only SSE, `stop_reason=="end_turn"`, reasoning-trace markers stripped.
- E1-T3: no tools → existing streaming behavior unchanged (regression net).
- E1-T4: generate failure with tools → SSE error event, stream terminates.
- C1-T1: fake vlm session w/o `tool_parser`, gemma4 family → after attach hook, the three attributes are present and `_parse_native_tool_calls` extracts a gemma-format call.
- C1-T2: attach failure path → no crash, `tool_parser_missing` diagnostic preserved.
- C1-T3: non-gemma vlm session → no attach attempted.

**Live (user-cleared cost: gemma-4-12B-it ≈24 GB, minutes; run right after implementation):**
- L1 (C): OpenAI `/v1/chat/completions`, gemma-12B, `tool_choice` auto + required → `tool_calls` PRESENT, arguments parse, no `tool_parser_missing`.
- L2 (E): Anthropic `/v1/messages` `stream:true` + tools, gemma-12B → tool_use SSE per E1.
- L3 (E, second family): same as L2 on a Qwen model if loadable within budget; otherwise record as not-run.
- Evidence → `files/evidence/owlmlx/replacement/r1-phase2-toolcall/` (request/response transcripts + verdict file). Honest three-state verdict per check: `passed` / `failed` / `not_run`.

## 4. Definition of Done
1. All unit tests pass; full serving-route + native-backend regression net passes (no regressions).
2. Live L1+L2 `passed` with evidence on disk (L3 best-effort).
3. Capability wording: tool calling over Anthropic streaming + gemma = **experimental**; supported claimed nowhere; replacement verdict untouched (`not yet replaceable`); §1a gate untouched.
4. No changes to consumer repos, uv.lock, owlmlx/speculative/, or pre-existing dirty working-tree files.
