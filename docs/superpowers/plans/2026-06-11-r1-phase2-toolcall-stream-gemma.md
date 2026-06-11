# R1 Phase-2 Tool-Call Completion (E1 + C1) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Anthropic `/v1/messages` streaming surfaces structured `tool_use` (E1), and gemma vlm-loaded sessions get a working tool parser (C1) — closing the two confirmed gaps blocking OwlCoda agentic traffic on owlmlx.

**Architecture:** E1 mirrors the in-repo OpenAI SSE pattern (tools present → internal non-streaming generate → emit results as SSE) inside `anthropic_sse_source`. C1 attaches the upstream gemma4 tool parser (`parse_tool_call` + `<|tool_call>`/`<tool_call|>` markers) to mlx_vlm-loaded session tokenizers at load time, feeding the existing `_parse_native_tool_calls` machinery.

**Tech Stack:** FastAPI routes (`owlmlx/runtime/server_routes_openai.py`), native backend (`owlmlx/runtime/mlx_native_backend.py`), pytest + FastAPI TestClient with stub backends. Spec: `docs/architect/design/R1-phase2-toolcall-stream-gemma-spec.md`.

**Hard rules (repeat to every worker):** TDD (failing test first, paste FAIL output, then implement, paste PASS). Never touch `uv.lock`, `owlmlx/speculative/`, or pre-existing dirty working-tree files. `owlmlx/runtime/mlx_native_backend.py` IS pre-existing-dirty — Task 2 includes a selective-staging recipe; follow it exactly. Capability language stays *experimental*; promotes nothing. No push.

**Verified upstream facts (do not re-derive):**
- `mlx_lm.tool_parsers.gemma4` exposes `parse_tool_call(text, _=None)`, `tool_call_start == "<|tool_call>"`, `tool_call_end == "<tool_call|>"`.
- `mlx_vlm.tool_parsers` also contains a `gemma4` module (probe its symbols in Task 2 Step 1; prefer it when it exposes the same three symbols, else fall back to mlx_lm's).
- `_parse_native_tool_calls(tokenizer, text, tools=...)` (mlx_native_backend.py:463) needs exactly: callable `tokenizer.tool_parser` (called as `tool_parser(tool_text, tools)`), `tokenizer.tool_call_start`, `tokenizer.tool_call_end`. When `tool_parser` is absent it sets `detail["tool_parser_missing"]=True`.
- Real backend convention: success → `detail["tool_calls"]` + `finish_reason="tool_calls"`. Route helper `_anthropic_tool_use_blocks_from_detail(detail)` (added in `41b8c752`) normalizes all conventions into Anthropic tool_use blocks.
- OpenAI SSE precedent: `sse_source` at server_routes_openai.py:849-:899 — `if payload.tools and payload.tool_choice != "none": result = await runtime.generate_messages(...)` then emits chunks. E1 copies this control flow.

---

### Task 1: E1 — Anthropic SSE tools branch

**Files:**
- Modify: `owlmlx/runtime/server_routes_openai.py` (inside `anthropic_sse_source`, the generator starting ~line 1250s after `41b8c752`; locate with `grep -n "anthropic_sse_source" `)
- Test: `tests/test_server_routes_openai.py` (this file is currently CLEAN — committed in `41b8c752`; append tests)

- [ ] **Step 1: Write 4 failing tests** (append to `tests/test_server_routes_openai.py`; reuse the file's existing stub-backend/TestClient harness — copy the construction used by `test_anthropic_messages_surfaces_real_backend_tool_calls_convention` and adapt)

```python
def _collect_sse_events(response_text: str) -> list[dict]:
    events = []
    for line in response_text.splitlines():
        if line.startswith("data: "):
            try:
                events.append(json.loads(line[len("data: "):]))
            except json.JSONDecodeError:
                pass
    return events


def test_anthropic_stream_with_tools_emits_tool_use_blocks() -> None:
    # Backend returns the REAL convention: finish_reason="tool_calls" + detail["tool_calls"]
    backend = _StubBackend(  # use/extend this file's existing stub pattern
        text="",
        finish_reason="tool_calls",
        detail={"tool_calls": [{
            "id": "call_1", "type": "function",
            "function": {"name": "write",
                         "arguments": "{\"path\": \"a.js\", \"content\": \"x\"}"},
        }]},
    )
    client = _client_for_backend(backend)  # existing helper/pattern in this file
    response = client.post("/v1/messages", json={
        "model": "stub-model", "stream": True, "max_tokens": 64,
        "messages": [{"role": "user", "content": "write a.js"}],
        "tools": [{"name": "write", "description": "w",
                   "input_schema": {"type": "object", "properties": {}}}],
    })
    events = _collect_sse_events(response.text)
    starts = [e for e in events if e.get("type") == "content_block_start"
              and e.get("content_block", {}).get("type") == "tool_use"]
    assert len(starts) == 1
    assert starts[0]["content_block"]["name"] == "write"
    deltas = [e for e in events if e.get("type") == "content_block_delta"
              and e.get("delta", {}).get("type") == "input_json_delta"]
    joined = "".join(d["delta"]["partial_json"] for d in deltas)
    assert json.loads(joined) == {"path": "a.js", "content": "x"}
    message_deltas = [e for e in events if e.get("type") == "message_delta"]
    assert message_deltas and message_deltas[-1]["delta"]["stop_reason"] == "tool_use"


def test_anthropic_stream_with_tools_text_only_falls_back_to_end_turn() -> None:
    backend = _StubBackend(text="plain answer", finish_reason="stop", detail={})
    client = _client_for_backend(backend)
    response = client.post("/v1/messages", json={
        "model": "stub-model", "stream": True, "max_tokens": 64,
        "messages": [{"role": "user", "content": "hi"}],
        "tools": [{"name": "write", "description": "w",
                   "input_schema": {"type": "object", "properties": {}}}],
    })
    events = _collect_sse_events(response.text)
    text = "".join(e["delta"]["text"] for e in events
                   if e.get("type") == "content_block_delta"
                   and e.get("delta", {}).get("type") == "text_delta")
    assert text == "plain answer"
    message_deltas = [e for e in events if e.get("type") == "message_delta"]
    assert message_deltas[-1]["delta"]["stop_reason"] == "end_turn"


def test_anthropic_stream_without_tools_keeps_streaming_path() -> None:
    # No tools → the existing token-by-token streaming branch must be used.
    # Use the file's existing streaming stub (the one test_anthropic_messages_stream_*
    # uses) and assert behavior is unchanged: text deltas arrive and stop_reason end_turn.
    ...  # adapt from existing streaming test in this file; assert no tool_use events


def test_anthropic_stream_with_tools_generate_failure_emits_error() -> None:
    backend = _StubBackend(ok=False, message="boom",
                           error_code=RuntimeErrorCode.backend_error)
    client = _client_for_backend(backend)
    response = client.post("/v1/messages", json={
        "model": "stub-model", "stream": True, "max_tokens": 64,
        "messages": [{"role": "user", "content": "hi"}],
        "tools": [{"name": "write", "description": "w",
                   "input_schema": {"type": "object", "properties": {}}}],
    })
    events = _collect_sse_events(response.text)
    assert any(e.get("type") == "error" or "error" in e for e in events)
```

(The `...` in test 3 means: copy the existing no-tools streaming test in this file and add `assert not [e for e in events if e.get("content_block", {}).get("type") == "tool_use"]` — write it out fully in the actual test file.)

- [ ] **Step 2: Run, verify all 4 FAIL**

Run: `cd /Users/yeemio/AI/gitrep/owlmlx && .venv/bin/python -m pytest tests/test_server_routes_openai.py -q -k anthropic_stream`
Expected: 4 failed (tool_use events absent / error event absent).

- [ ] **Step 3: Implement E1** in `anthropic_sse_source`. At the very top of the generator (before `message_start` is yielded by the existing path), add the tools branch:

```python
        async def anthropic_sse_source():
            tool_choice_type = (
                payload.tool_choice.get("type")
                if isinstance(payload.tool_choice, dict)
                else payload.tool_choice
            )
            if payload.tools and tool_choice_type != "none":
                result = await runtime.generate_messages(
                    turns, model_id=target_model, **params
                )
                if not result.ok:
                    yield (
                        "event: error\n"
                        f"data: {json.dumps({'type': 'error', 'error': {'type': 'api_error', 'message': result.message}})}\n\n"
                    )
                    return
                visible_text, _policy_payload = _openai_visible_text_for_policy(
                    result.text,
                    finish_reason=result.finish_reason,
                    policy=reasoning_policy,  # reuse the profile-driven policy var
                                              # already computed for this route in 41b8c752;
                                              # if it is only computed in the non-stream
                                              # branch, hoist that computation above both.
                )
                tool_blocks = _anthropic_tool_use_blocks_from_detail(result.detail)
                stop_reason = "tool_use" if tool_blocks else "end_turn"
                yield (
                    "event: message_start\n"
                    f"data: {json.dumps({'type': 'message_start', 'message': _anthropic_message_dict(message_id=message_id, model=target_model or 'unknown', text='', stop_reason=None, input_tokens=result.prompt_tokens or input_tokens, output_tokens=0)})}\n\n"
                )
                block_index = 0
                if visible_text and visible_text.strip():
                    yield (
                        "event: content_block_start\n"
                        f"data: {json.dumps({'type': 'content_block_start', 'index': block_index, 'content_block': {'type': 'text', 'text': ''}})}\n\n"
                    )
                    yield (
                        "event: content_block_delta\n"
                        f"data: {json.dumps({'type': 'content_block_delta', 'index': block_index, 'delta': {'type': 'text_delta', 'text': visible_text}})}\n\n"
                    )
                    yield (
                        "event: content_block_stop\n"
                        f"data: {json.dumps({'type': 'content_block_stop', 'index': block_index})}\n\n"
                    )
                    block_index += 1
                for block in tool_blocks:
                    yield (
                        "event: content_block_start\n"
                        f"data: {json.dumps({'type': 'content_block_start', 'index': block_index, 'content_block': {'type': 'tool_use', 'id': block.get('id'), 'name': block.get('name'), 'input': {}}})}\n\n"
                    )
                    yield (
                        "event: content_block_delta\n"
                        f"data: {json.dumps({'type': 'content_block_delta', 'index': block_index, 'delta': {'type': 'input_json_delta', 'partial_json': json.dumps(block.get('input') or {})}})}\n\n"
                    )
                    yield (
                        "event: content_block_stop\n"
                        f"data: {json.dumps({'type': 'content_block_stop', 'index': block_index})}\n\n"
                    )
                    block_index += 1
                yield (
                    "event: message_delta\n"
                    f"data: {json.dumps({'type': 'message_delta', 'delta': {'stop_reason': stop_reason, 'stop_sequence': None}, 'usage': {'output_tokens': result.completion_tokens or 0}})}\n\n"
                )
                yield (
                    "event: message_stop\n"
                    f"data: {json.dumps({'type': 'message_stop'})}\n\n"
                )
                return
            # ... existing no-tools streaming path continues unchanged below ...
```

Match the exact event-dict shapes already used elsewhere in this generator (the existing `message_start`/`content_block_delta` yields) — keep `event:`-line prefixes consistent with what the existing code does (if the existing code emits bare `data:` lines without `event:` lines, do the same; the tests above only parse `data:` lines so either form passes).

- [ ] **Step 4: Run, verify all 4 PASS + no regressions**

Run: `.venv/bin/python -m pytest tests/test_server_routes_openai.py -q`
Expected: all pass (existing 26 + new 4).

- [ ] **Step 5: Commit** (both files are clean-scoped; normal staging)

```bash
git add owlmlx/runtime/server_routes_openai.py tests/test_server_routes_openai.py
git commit -m "feat(r1-phase2): Anthropic SSE surfaces tool_use via non-stream generate (E1)

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 2: C1 — gemma tool parser attach for vlm-loaded sessions

**Files:**
- Modify: `owlmlx/runtime/mlx_native_backend.py` (PRE-EXISTING-DIRTY — see Step 6 staging recipe)
- Test: Create `tests/test_gemma_vlm_tool_parser_attach.py` (new file; do NOT add to tests/test_mlx_native_backend.py, it is pre-existing-dirty)

- [ ] **Step 1: Probe parser sources, pin preference**

Run: `.venv/bin/python -c "import mlx_vlm.tool_parsers.gemma4 as g; print(callable(getattr(g,'parse_tool_call',None)), getattr(g,'tool_call_start',None), getattr(g,'tool_call_end',None))"`
If it prints `True <|tool_call> <tool_call|>` → preference order is `mlx_vlm.tool_parsers.gemma4` then `mlx_lm.tool_parsers.gemma4`. If symbols differ/missing → preference is mlx_lm first. Record the observed output in the commit message.

- [ ] **Step 2: Write failing tests** (`tests/test_gemma_vlm_tool_parser_attach.py`)

```python
"""C1: gemma4 tool parser attach for vlm-loaded sessions (R1 Phase-2 spec §2)."""
from __future__ import annotations

from owlmlx.runtime.mlx_native_backend import (
    _attach_gemma_vlm_tool_parser,
    _parse_native_tool_calls,
)


class _BareTokenizer:
    """Mimics an mlx_vlm processor: no tool_parser attributes at all."""


def test_attach_installs_parser_and_markers_for_gemma4() -> None:
    tok = _BareTokenizer()
    attached = _attach_gemma_vlm_tool_parser(tok, model_id="gemma-4-12B-it")
    assert attached is True
    assert callable(tok.tool_parser)
    assert tok.tool_call_start == "<|tool_call>"
    assert tok.tool_call_end == "<tool_call|>"


def test_attached_parser_feeds_parse_native_tool_calls() -> None:
    tok = _BareTokenizer()
    _attach_gemma_vlm_tool_parser(tok, model_id="gemma-4-12B-it")
    text = (
        'before <|tool_call>call:write{content:<|"|>x<|"|>,'
        'path:<|"|>a.js<|"|>}<tool_call|> after'
    )
    tools = [{"type": "function", "function": {
        "name": "write", "description": "w",
        "parameters": {"type": "object", "properties": {
            "path": {"type": "string"}, "content": {"type": "string"}},
            "required": ["path", "content"]}}}]
    parsed = _parse_native_tool_calls(tok, text, tools=tools)
    assert parsed.tool_calls, f"expected tool_calls, detail={parsed.detail}"
    assert parsed.tool_calls[0]["function"]["name"] == "write"
    assert not parsed.detail.get("tool_parser_missing")


def test_attach_skips_non_gemma_models() -> None:
    tok = _BareTokenizer()
    attached = _attach_gemma_vlm_tool_parser(tok, model_id="Qwen3.6-27B")
    assert attached is False
    assert not hasattr(tok, "tool_parser")


def test_attach_preserves_existing_parser() -> None:
    tok = _BareTokenizer()
    sentinel = lambda text, tools=None: []  # noqa: E731
    tok.tool_parser = sentinel
    attached = _attach_gemma_vlm_tool_parser(tok, model_id="gemma-4-12B-it")
    assert attached is False
    assert tok.tool_parser is sentinel
```

NOTE: if the gemma4 `parse_tool_call(tool_text, _)` expects the tool_text WITHOUT the start/end markers (check `_extract_tool_call_texts` in mlx_native_backend.py — it strips markers before calling the parser), adjust the second test's expectation accordingly after reading that function; the assertion on `parsed.tool_calls[0]["function"]["name"]` must hold either way.

- [ ] **Step 3: Run, verify FAIL**

Run: `.venv/bin/python -m pytest tests/test_gemma_vlm_tool_parser_attach.py -q`
Expected: ImportError (`_attach_gemma_vlm_tool_parser` not defined).

- [ ] **Step 4: Implement** in `owlmlx/runtime/mlx_native_backend.py`. Add near `_parse_native_tool_calls`:

```python
_GEMMA_VLM_PARSER_SOURCES: tuple[str, ...] = (
    "mlx_vlm.tool_parsers.gemma4",   # engine-matched first (per Task-2 Step-1 probe)
    "mlx_lm.tool_parsers.gemma4",
)


def _attach_gemma_vlm_tool_parser(tokenizer: Any, *, model_id: str) -> bool:
    """Attach the upstream gemma4 tool parser to a vlm-loaded tokenizer.

    mlx_vlm processors expose no ``tool_parser``/``tool_call_start``/
    ``tool_call_end``, so ``_parse_native_tool_calls`` honestly reports
    ``tool_parser_missing`` (R1 Phase-2 spec §1-C). Returns True only when a
    parser was newly attached. Never raises: attach failure leaves the
    diagnostics truthful.
    """
    if callable(getattr(tokenizer, "tool_parser", None)):
        return False
    haystack = model_id.lower()
    if "gemma" not in haystack:
        return False
    for module_name in _GEMMA_VLM_PARSER_SOURCES:
        try:
            module = importlib.import_module(module_name)
        except Exception:
            continue
        parse_tool_call = getattr(module, "parse_tool_call", None)
        start = getattr(module, "tool_call_start", None)
        end = getattr(module, "tool_call_end", None)
        if not callable(parse_tool_call) or not start or not end:
            continue
        try:
            tokenizer.tool_parser = parse_tool_call
            tokenizer.tool_call_start = start
            tokenizer.tool_call_end = end
        except Exception:
            return False
        return True
    return False
```

(`importlib` is already imported at the top of this file — verify; add if absent.)

Then wire the call site: in the load path, right after a successful **mlx_vlm-engine** load assigns the session tokenizer/processor (locate with `grep -n 'engine == "mlx_vlm"' owlmlx/runtime/mlx_native_backend.py` inside `_load_on_worker`/`load`), add:

```python
        if engine == "mlx_vlm":
            _attach_gemma_vlm_tool_parser(tokenizer, model_id=model_id)
```

(adapt the variable names to the surrounding code — the tokenizer object must be the SAME object later passed to `_parse_native_tool_calls`; verify by reading how `session.tokenizer` is constructed and used at the `generate` call site, line ~1683.)

- [ ] **Step 5: Run, verify PASS + backend suite green**

Run: `.venv/bin/python -m pytest tests/test_gemma_vlm_tool_parser_attach.py tests/test_mlx_native_backend.py -q`
Expected: new 4 pass; pre-existing backend tests still pass.

- [ ] **Step 6: Selective-stage commit (the file is pre-existing-dirty — commit ONLY your hunks)**

```bash
cd /Users/yeemio/AI/gitrep/owlmlx
cp owlmlx/runtime/mlx_native_backend.py /tmp/native_backend_backup.py
git diff -- owlmlx/runtime/mlx_native_backend.py > /tmp/native_all.patch
# Identify PRE-EXISTING hunks: every hunk in /tmp/native_all.patch that is NOT
# (a) the _attach_gemma_vlm_tool_parser helper block, (b) the engine=="mlx_vlm"
# call-site lines, or (c) an importlib import line you added.
# Extract those pre-existing hunks into /tmp/native_pre.patch (awk hunk filter or
# manual split of the patch file), then:
git apply -R /tmp/native_pre.patch                     # temporarily remove pre-existing edits
.venv/bin/python -m pytest tests/test_gemma_vlm_tool_parser_attach.py -q   # still green
git add owlmlx/runtime/mlx_native_backend.py tests/test_gemma_vlm_tool_parser_attach.py
git commit -m "feat(r1-phase2): attach upstream gemma4 tool parser to vlm-loaded sessions (C1)

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
git apply /tmp/native_pre.patch                        # restore pre-existing dirty edits
git diff --stat -- owlmlx/runtime/mlx_native_backend.py   # confirm dirty edits restored
```

If `git apply -R` or the restore fails with context errors: restore from the backup copy (`cp /tmp/native_backend_backup.py owlmlx/runtime/mlx_native_backend.py`), then STOP and report instead of improvising.

---

### Task 3: Regression net + live validation + evidence

**Files:**
- Create: `files/evidence/owlmlx/replacement/r1-phase2-toolcall/<UTC>-live-validation.md` (+ raw JSON transcripts alongside)
- No code changes in this task.

- [ ] **Step 1: Full regression net**

Run: `.venv/bin/python -m pytest tests/test_server_routes_openai.py tests/test_gemma_vlm_tool_parser_attach.py tests/test_mlx_native_backend.py tests/test_runtime_native_preview_server.py tests/test_runtime_technical_preview_server.py -q`
Expected: all pass, no regressions. Paste the summary line.

- [ ] **Step 2: Memory + port preflight (the stale-process lesson — never validate against an old process)**

```bash
top -l 1 -n 0 | grep PhysMem
curl -s http://127.0.0.1:8066/healthz | python3 -c "import sys,json;d=json.load(sys.stdin);print(d.get('model_count'),d.get('active_model_id'))"
lsof -iTCP:8067 -sTCP:LISTEN || echo "8067 free"
```
Need ≈26 GB free for gemma-12B. If :8066 currently holds models that crowd the budget, unload via `POST http://127.0.0.1:8066/v1/unload {"model_id": ...}` (it is our runtime; do NOT kill the process). Launch a FRESH isolated server from THIS branch checkout:

```bash
cd /Users/yeemio/AI/gitrep/owlmlx
nohup .venv/bin/python scripts/runtime_native_preview_server.py --host 127.0.0.1 --port 8067 > /tmp/r1p2-server.log 2>&1 &
sleep 5 && curl -s http://127.0.0.1:8067/healthz | head -c 120
```

- [ ] **Step 3: Live L1 (C — gemma parses, auto + required)**

```bash
curl -s -X POST http://127.0.0.1:8067/v1/load -H 'Content-Type: application/json' \
  -d '{"model_id":"gemma-4-12B-it","memory_gb":26.0,"warmup":false}'
# then for TC in auto required:
curl -s -X POST http://127.0.0.1:8067/v1/chat/completions -H 'Content-Type: application/json' -d '{
  "model":"gemma-4-12B-it",
  "messages":[{"role":"user","content":"Call the write tool to create solution.js containing: function add(a,b){return a+b}. Keep it tiny."}],
  "tools":[{"type":"function","function":{"name":"write","description":"Write a file.","parameters":{"type":"object","properties":{"path":{"type":"string"},"content":{"type":"string"}},"required":["path","content"]}}}],
  "tool_choice":"auto","max_tokens":512,"stream":false}'
```
PASS bar: `message.tool_calls` PRESENT with `function.name=="write"` and JSON-parseable arguments; no `tool_parser_missing` in diagnostics. Record each as passed/failed. Save raw responses.

- [ ] **Step 4: Live L2 (E — Anthropic streaming tool_use)**

```bash
curl -s -N -X POST http://127.0.0.1:8067/v1/messages -H 'Content-Type: application/json' -d '{
  "model":"gemma-4-12B-it","stream":true,"max_tokens":512,
  "messages":[{"role":"user","content":"Call the write tool to create solution.js containing: function add(a,b){return a+b}."}],
  "tools":[{"name":"write","description":"Write a file.","input_schema":{"type":"object","properties":{"path":{"type":"string"},"content":{"type":"string"}},"required":["path","content"]}}],
  "tool_choice":{"type":"auto"}}' | head -40
```
PASS bar: SSE contains `content_block_start` with `"type": "tool_use"`, `input_json_delta` whose joined `partial_json` JSON-parses, `message_delta` with `stop_reason:"tool_use"`. Save raw SSE.

- [ ] **Step 5: Live L3 (E on Qwen, budget-permitting)** — if free RAM ≥ ~50 GB, unload gemma (`POST /v1/unload`), load `Qwen3.6-27B` (`memory_gb: 48`), repeat Step 4 with that model id. Otherwise record `not_run (memory budget)`.

- [ ] **Step 6: Teardown + evidence + commit**

```bash
curl -s -X POST http://127.0.0.1:8067/v1/unload -H 'Content-Type: application/json' -d '{"model_id":"<loaded>"}'
kill %1 2>/dev/null || pkill -f "runtime_native_preview_server.py --host 127.0.0.1 --port 8067"
lsof -iTCP:8067 -sTCP:LISTEN || echo "8067 released"
```
Write `files/evidence/owlmlx/replacement/r1-phase2-toolcall/<UTC>-live-validation.md`: per-check three-state verdicts (L1-auto, L1-required, L2, L3), raw transcript paths, owlmlx commit SHA, model ids, the honest bounds line ("experimental; single-prompt smoke, not sustained; promotes nothing"). Commit evidence + this plan's checkboxes:

```bash
git add files/evidence/owlmlx/replacement/r1-phase2-toolcall/ docs/superpowers/plans/2026-06-11-r1-phase2-toolcall-stream-gemma.md
git commit -m "test(r1-phase2): live validation evidence — gemma parser + Anthropic streaming tool_use

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

## Self-Review (done at plan-write time)
- Spec coverage: E1 → Task 1; C1 → Task 2; live L1/L2/L3 + evidence + wording bounds → Task 3; DoD §4 staging rules → embedded in Task 2 Step 6 and hard rules. No gaps.
- Placeholders: Task 1 test 3 contains an explicit instruction (not a TBD) to clone an existing test; acceptable because the referenced test exists in-file post-`41b8c752`.
- Type consistency: helper name `_attach_gemma_vlm_tool_parser` used identically in Tasks 2 tests and impl; `_anthropic_tool_use_blocks_from_detail` exists since `41b8c752`.
