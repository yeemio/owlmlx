# Runtime-3 Serving Surface

> Status: authoritative
> Updated: 2026-04-11
> Scope: Runtime-3 control surface, serialized serving truth, and handoff to streaming/comparison proof

## 1. Purpose

This document freezes the first Runtime-3 capabilities that sit above the
Runtime-2 backend internals:

- explicit runtime restart surface
- honest serialized concurrent serving validation
- runtime streaming and comparison closure recorded separately in
  `runtime3-benchmark-and-streaming.md`

## 2. Runtime Surface

Runtime-3 adds two explicit runtime-control surfaces:

| Surface | Path | Meaning |
|---|---|---|
| full runtime snapshot | `GET /v1/runtime/status` | complete kernel-derived runtime status |
| explicit restart | `POST /v1/runtime/restart` | restart one currently loaded model through `RuntimeKernel.restart_model()` |

These surfaces sit above backend internals. They make Runtime-2 restart and
health truth visible through the HTTP layer instead of hiding them inside
`MlxLmSubprocessBackend`.

## 3. Serialized Concurrent Serving Validation

Script:

`scripts/runtime3_serialized_concurrency_check.py`

Model:

- `/Users/yeemio/AI/Agent/models/gpt-oss-20b-MXFP4-Q4`

Environment:

- `/Users/yeemio/AI/gitrep/owlmlx/.runtime1-mlx/bin/python`

Command shape:

```bash
env PYTHONPATH=/Users/yeemio/AI/gitrep/owlmlx \
  /Users/yeemio/AI/gitrep/owlmlx/.runtime1-mlx/bin/python \
  scripts/runtime3_serialized_concurrency_check.py \
  --python /Users/yeemio/AI/gitrep/owlmlx/.runtime1-mlx/bin/python \
  --model /Users/yeemio/AI/Agent/models/gpt-oss-20b-MXFP4-Q4 \
  --memory-gb 16 \
  --prompt "Reply with exactly OK." \
  --max-tokens 8 \
  --concurrency 2
```

Result:

| Metric | Value |
|---|---|
| `load_time_s` | `1.5023` |
| `same_child_pid` | `true` |
| `all_serialized` | `true` |
| `total_served` | `2` |
| `total_queued` | `2` |
| `queue_discipline` | `serial` |
| request #1 `execution_time_s` | `0.2541` |
| request #2 `execution_time_s` | `0.1407` |

## 4. Interpretation

This validates that Runtime-3 does not break the serving-path safety rule that
came from the large-weight path:

- one persistent child session can serve repeated requests
- concurrent requests still pass through `GenerationGate`
- serialized serving remains the runtime truth

The `was_queued` field is not the authoritative signal for this proof because
short requests can still record `0.0` wait time at this scale. The authoritative
signals are:

- `max_concurrent == 1`
- `queue_discipline == serial`
- `total_served == total_queued == concurrency`
- same child `pid` for the concurrent requests

## 5. Non-Claims

This document does not claim:

- serialized serving has been validated at higher concurrency levels
- multi-model concurrent serving policy is complete
- production transport semantics are finished
