# owlmlx Model RC A2 Qwen3.6-35B-A3B Live Record Handoff

Repo: `/Users/yeemio/AI/gitrep/owlmlx`

Date: 2026-05-05

Outcome:

`owlmlx_model_release_candidate_a2_qwen36_35b_a3b_live_record_introduced`

## 1. Verdict

`Qwen3.6-35B-A3B` now has a non-dry-run
`owlmlx.model_release_candidate_record`.

Record verdict:

```text
needs_optimization
```

This is intentionally not `pass` because OwlOps observation and same-host
reference runtime comparison remain open. The short generation also returned a
length-truncated reasoning trace, so the record proves runtime operation and
measurement capture, not answer quality.

## 2. Live Run

Runtime:

```text
http://127.0.0.1:8066
```

Model:

```text
Qwen3.6-35B-A3B
```

Artifact path:

```text
/Users/yeemio/AI/Agent/models/Qwen3.6-35B-A3B
```

Evidence directory:

```text
files/evidence/owlmlx/model-release-candidates/20260505T073902Z-qwen36-35b-a3b
```

Operation sequence:

```text
load -> stream generate -> unload -> reload -> stream generate -> unload
```

Result:

```text
repeat_count = 2
failure_count = 0
load_result.status = pass
generation_result.status = pass
unload_result.status = pass
reload_result.status = pass
```

## 3. Metrics

Measured:

```text
first_token_latency_ms = 3315.486
tokens_per_second = 14.666
wall_clock_ms = 37299.247
peak_resident_set_bytes = 54570254336
memory_headroom_bytes = 82868699136
output_sanity_label = reasoning_trace_truncated
```

Blockers preserved in the record:

```text
owlops_observation_pending
reference_runtime_comparison_missing
short_generation_quality_inconclusive
```

## 4. Coordination And HTTP Surface

The live run acquired the required exclusive lock before model load:

```text
/tmp/owlmlx-model-rc-heavy.lock
```

Per coordinator override, this lane did not remount or restart `8066` after
the run. The current mounted HTTP latest/history surface therefore still shows
the A1 `Qwen3.6-27B` ledger until the coordinator performs the later
cumulative merge/remount.

Captured files:

```text
http-latest-current-mounted-ledger.json
http-history-current-mounted-ledger.json
local-ledger-latest.json
local-ledger-history.json
```

Post-run runtime state:

```text
active_model_id = null
model_count = 0
readiness = degraded
```

## 5. Verification

```text
pytest -q tests/test_model_release_candidate_surface.py
17 passed

pytest -q tests/test_runtime_technical_preview_server.py
4 passed

pytest -q tests/test_runtime_server.py -k "model_release_candidate or runtime_status"
1 passed, 40 deselected

python3 -m py_compile \
  owlmlx/model_release_candidate_schema.py \
  owlmlx/model_release_candidate_record.py \
  owlmlx/model_release_candidate_ledger.py \
  scripts/runtime_model_release_candidate.py \
  owlmlx/runtime/server.py \
  owlmlx/runtime/technical_preview.py \
  scripts/runtime_technical_preview_server.py
OK

git diff --check
clean
```

Stale process check:

```text
8066 remained listening.
8001 remained listening and was not killed.
8009 remained listening and was not killed.
No loaded owlmlx model remained after A2 completion.
```

## 6. Remaining Gaps

- Coordinator still needs to merge/remount the cumulative Model RC ledger when
  B1 no longer needs the A1-only latest/history view.
- OwlOps still needs to consume/render the A2 record.
- Same-host reference comparison for this model remains missing.
- The next memory-exclusive mainline lane is `gemma-4-31B-it`; DeepSeek remains
  separate experimental pressure work.
